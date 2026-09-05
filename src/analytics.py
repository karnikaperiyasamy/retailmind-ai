"""
Deterministic Retail Analytics Engine for RetailMind AI.
Performs strictly verified Python/pandas computations for sales, inventory,
stock-out warnings, overstocks, slow-moving items, and anomalies.
Zero LLM hallucination - all math is deterministic and verifiable.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import timedelta
from src.data_loader import DataLoader

class AnalyticsEngine:
    def __init__(self, data_loader: Optional[DataLoader] = None):
        self.loader = data_loader or DataLoader.get_instance()
        self.latest_date = self.loader.get_latest_date()

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Calculates executive KPI cards for the retail operation."""
        sales_df = self.loader.get_sales()
        inv_df = self.loader.get_inventory()
        products_df = self.loader.get_products()

        # Last 30 days total sales and units
        thirty_days_ago = self.latest_date - timedelta(days=29)
        recent_sales = sales_df[sales_df["date"] >= thirty_days_ago]

        total_revenue_30d = float(recent_sales["revenue"].sum())
        total_units_sold_30d = int(recent_sales["quantity_sold"].sum())

        # Current total stock on latest date
        latest_inv = inv_df[inv_df["date"] == self.latest_date]
        total_current_stock = int(latest_inv["stock_quantity"].sum())

        # Inventory valuation
        inv_with_cost = latest_inv.merge(products_df[["product_id", "cost_price", "selling_price"]], on="product_id", how="left")
        total_inventory_cost_valuation = float((inv_with_cost["stock_quantity"] * inv_with_cost["cost_price"]).sum())
        total_inventory_retail_valuation = float((inv_with_cost["stock_quantity"] * inv_with_cost["selling_price"]).sum())

        # Risks and alerts
        stockout_risks = self.get_stockout_risks()
        overstocked_items = self.get_overstock_products()
        spikes = self.get_sales_spikes()
        drops = self.get_sales_drops()

        total_alerts = len(stockout_risks) + len(overstocked_items) + len(spikes) + len(drops)

        # Average profit margin
        recent_sales_with_cost = recent_sales.merge(products_df[["product_id", "cost_price"]], on="product_id", how="left")
        total_cogs = float((recent_sales_with_cost["quantity_sold"] * recent_sales_with_cost["cost_price"]).sum())
        gross_profit = total_revenue_30d - total_cogs
        gross_margin_pct = round((gross_profit / total_revenue_30d * 100), 1) if total_revenue_30d > 0 else 0.0

        return {
            "period": f"{thirty_days_ago.strftime('%Y-%m-%d')} to {self.latest_date.strftime('%Y-%m-%d')}",
            "total_sales_30d": round(total_revenue_30d, 2),
            "total_units_sold_30d": total_units_sold_30d,
            "total_current_stock": total_current_stock,
            "inventory_cost_valuation": round(total_inventory_cost_valuation, 2),
            "inventory_retail_valuation": round(total_inventory_retail_valuation, 2),
            "gross_margin_pct": gross_margin_pct,
            "stockout_risks_count": len(stockout_risks),
            "overstocked_count": len(overstocked_items),
            "sales_alerts_count": total_alerts,
            "stores_count": len(self.loader.get_stores()),
            "products_count": len(products_df)
        }

    def _get_daily_rates_and_stock(self, days_window: int = 7) -> pd.DataFrame:
        """Helper to merge current stock with recent average daily sales per store and product."""
        sales_df = self.loader.get_sales()
        inv_df = self.loader.get_inventory()
        products_df = self.loader.get_products()
        stores_df = self.loader.get_stores()

        window_start = self.latest_date - timedelta(days=days_window - 1)
        window_sales = sales_df[(sales_df["date"] >= window_start) & (sales_df["date"] <= self.latest_date)]

        # Aggregate total sold in window
        sales_agg = window_sales.groupby(["store_id", "product_id"])["quantity_sold"].sum().reset_index()
        sales_agg["average_daily_sales"] = (sales_agg["quantity_sold"] / days_window).round(2)

        # Get latest inventory
        latest_inv = inv_df[inv_df["date"] == self.latest_date][["store_id", "product_id", "stock_quantity"]]

        # Combine all products and stores
        full_grid = []
        for s_id in stores_df["store_id"]:
            for p_id in products_df["product_id"]:
                full_grid.append({"store_id": s_id, "product_id": p_id})
        df_grid = pd.DataFrame(full_grid)

        merged = df_grid.merge(latest_inv, on=["store_id", "product_id"], how="left")
        merged["stock_quantity"] = merged["stock_quantity"].fillna(0).astype(int)

        merged = merged.merge(sales_agg[["store_id", "product_id", "average_daily_sales", "quantity_sold"]], on=["store_id", "product_id"], how="left")
        merged["average_daily_sales"] = merged["average_daily_sales"].fillna(0.0)
        merged["quantity_sold_window"] = merged["quantity_sold"].fillna(0).astype(int)
        merged.drop(columns=["quantity_sold"], inplace=True)

        # Add product and store metadata
        merged = merged.merge(products_df, on="product_id", how="left")
        merged = merged.merge(stores_df, on="store_id", how="left")

        # Calculate days of inventory safely (avoid divide by zero)
        def calc_doi(row):
            ads = row["average_daily_sales"]
            stock = row["stock_quantity"]
            if ads > 0:
                return round(stock / ads, 2)
            elif stock > 0:
                return 999.0  # Stock present but zero recent sales
            else:
                return 0.0    # No stock and no sales

        merged["days_of_inventory"] = merged.apply(calc_doi, axis=1)
        return merged

    def get_stockout_risks(self, max_days: float = 7.0) -> List[Dict[str, Any]]:
        """
        Identifies products with <= 7.0 days of inventory remaining.
        Formula: days_of_inventory = current_stock / average_daily_sales
        """
        df = self._get_daily_rates_and_stock(days_window=7)
        # Filter for active velocity (average_daily_sales > 0) and days_of_inventory <= max_days
        risks = df[(df["average_daily_sales"] > 0) & (df["days_of_inventory"] <= max_days)].sort_values("days_of_inventory")

        results = []
        for _, row in risks.iterrows():
            curr_stock = int(row["stock_quantity"])
            ads = float(row["average_daily_sales"])
            doi = float(row["days_of_inventory"])
            reorder = int(row["reorder_level"])
            prod_name = str(row["product_name"])
            store_name = str(row["store_name"])
            p_id = str(row["product_id"])
            s_id = str(row["store_id"])

            # Recommended restock units
            recommended_reorder = max(reorder * 2, int(ads * 21))  # target 3 weeks supply

            results.append({
                "product_id": p_id,
                "product_name": prod_name,
                "category": row["category"],
                "store_id": s_id,
                "store_name": store_name,
                "current_stock": curr_stock,
                "average_daily_sales": ads,
                "days_remaining": doi,
                "reorder_level": reorder,
                "supporting_period": f"Recent 7 days ({ (self.latest_date - timedelta(days=6)).strftime('%Y-%m-%d') } to { self.latest_date.strftime('%Y-%m-%d') })",
                "reason": f"Current stock ({curr_stock} units) covers only {doi} days of sales at the current velocity ({ads} units/day). Reorder threshold is {reorder} units.",
                "action": f"Initiate replenishment order of {recommended_reorder} units with supplier {row['supplier']}.",
                "data_summary": {
                    "source": "sales.csv & inventory.csv",
                    "current_stock": curr_stock,
                    "avg_daily_sales_7d": ads,
                    "reorder_level": reorder
                },
                "calculation": f"{curr_stock} / {ads} = {doi:.2f} days of inventory",
                "assumption": f"Assuming near-term customer demand remains at ~{ads} units/day without promotional disruption.",
                "recommendation": f"Store manager should review order of {recommended_reorder} units before stock runs out in ~{doi:.1f} days."
            })
        return results

    def get_overstock_products(self, min_days: float = 45.0) -> List[Dict[str, Any]]:
        """
        Identifies products with >= 45 days of inventory.
        """
        df = self._get_daily_rates_and_stock(days_window=7)
        # Filter for products with stock > 0, average_daily_sales > 0, and days_of_inventory >= min_days
        overstocked = df[(df["stock_quantity"] > 0) & (df["average_daily_sales"] > 0) & (df["days_of_inventory"] >= min_days)].sort_values("days_of_inventory", ascending=False)

        results = []
        for _, row in overstocked.iterrows():
            curr_stock = int(row["stock_quantity"])
            ads = float(row["average_daily_sales"])
            doi = float(row["days_of_inventory"])
            cost = float(row["cost_price"])
            price = float(row["selling_price"])

            # 30 days is standard healthy stock
            target_stock = int(ads * 30)
            excess_units = max(0, curr_stock - target_stock)
            tied_up_capital = round(excess_units * cost, 2)

            results.append({
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "category": row["category"],
                "store_id": row["store_id"],
                "store_name": row["store_name"],
                "current_stock": curr_stock,
                "average_daily_sales": ads,
                "days_of_inventory": doi,
                "estimated_excess_units": excess_units,
                "tied_up_capital": tied_up_capital,
                "cost_price": cost,
                "selling_price": price,
                "supporting_period": f"Recent 7 days ({ (self.latest_date - timedelta(days=6)).strftime('%Y-%m-%d') } to { self.latest_date.strftime('%Y-%m-%d') })",
                "reason": f"Inventory level of {curr_stock} units provides {doi:.1f} days of supply at current sales rate of {ads} units/day, exceeding healthy threshold (30 days).",
                "action": f"Evaluate promotional discount or transfer {excess_units} units to higher-velocity branch locations.",
                "data_summary": {
                    "source": "inventory.csv & sales.csv",
                    "current_stock": curr_stock,
                    "avg_daily_sales": ads,
                    "target_30d_stock": target_stock,
                    "excess_units": excess_units,
                    "capital_tied_up": tied_up_capital
                },
                "calculation": f"{curr_stock} / {ads} = {doi:.2f} days; Excess: {curr_stock} - {target_stock} = {excess_units} units (₹{tied_up_capital:,.2f})",
                "assumption": "Assumes standard inventory target of 30 days sales velocity.",
                "recommendation": f"Pause procurement and consider marketing promotion or inter-store inventory transfer for {excess_units} surplus units."
            })
        return results

    def get_slow_moving_products(self, window_days: int = 60, max_sales_threshold: int = 5) -> List[Dict[str, Any]]:
        """
        Identifies products with very low sales (< 5 units over 60 days) while holding stock (> 10 units).
        """
        sales_df = self.loader.get_sales()
        inv_df = self.loader.get_inventory()
        products_df = self.loader.get_products()
        stores_df = self.loader.get_stores()

        start_date = self.latest_date - timedelta(days=window_days - 1)
        period_sales = sales_df[(sales_df["date"] >= start_date) & (sales_df["date"] <= self.latest_date)]

        sales_sum = period_sales.groupby(["store_id", "product_id"])["quantity_sold"].sum().reset_index()

        latest_inv = inv_df[inv_df["date"] == self.latest_date][["store_id", "product_id", "stock_quantity"]]

        merged = latest_inv.merge(sales_sum, on=["store_id", "product_id"], how="left")
        merged["quantity_sold"] = merged["quantity_sold"].fillna(0).astype(int)
        merged = merged.merge(products_df, on="product_id", how="left")
        merged = merged.merge(stores_df, on="store_id", how="left")

        # Criteria: held stock >= 15 units and units sold <= max_sales_threshold
        slow = merged[(merged["stock_quantity"] >= 15) & (merged["quantity_sold"] <= max_sales_threshold)].sort_values("quantity_sold")

        results = []
        for _, row in slow.iterrows():
            units_sold = int(row["quantity_sold"])
            curr_stock = int(row["stock_quantity"])
            cost = float(row["cost_price"])
            capital_locked = round(curr_stock * cost, 2)
            velocity_per_month = round(units_sold / (window_days / 30), 2)

            results.append({
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "category": row["category"],
                "store_id": row["store_id"],
                "store_name": row["store_name"],
                "units_sold": units_sold,
                "current_inventory": curr_stock,
                "capital_locked": capital_locked,
                "sales_period": f"{start_date.strftime('%Y-%m-%d')} to {self.latest_date.strftime('%Y-%m-%d')} ({window_days} days)",
                "relationship": f"{units_sold} units sold vs {curr_stock} units in stock ({velocity_per_month} units/month).",
                "reason": f"Minimal velocity over {window_days} days indicates poor turnover and dead inventory risk.",
                "data_summary": {
                    "source": "sales.csv & inventory.csv",
                    "units_sold": units_sold,
                    "current_stock": curr_stock,
                    "window_days": window_days
                },
                "calculation": f"Velocity: {units_sold} / {window_days} days = {units_sold/window_days:.3f} units/day. Capital locked: {curr_stock} * ₹{cost} = ₹{capital_locked:,.2f}",
                "assumption": "Assumes item has been in stock on sales floor throughout the window.",
                "recommendation": f"Assess markdown clearance or bundling with complementary items to recover ₹{capital_locked:,.2f} in locked working capital."
            })
        return results

    def get_sales_spikes(self, spike_threshold_pct: float = 40.0) -> List[Dict[str, Any]]:
        """
        Compares recent 7-day average sales with the previous 30-day baseline (days -37 to -7).
        Flags meaningful increases >= 40%.
        """
        sales_df = self.loader.get_sales()
        products_df = self.loader.get_products()
        stores_df = self.loader.get_stores()

        recent_start = self.latest_date - timedelta(days=6)
        baseline_end = recent_start - timedelta(days=1)
        baseline_start = baseline_end - timedelta(days=29)

        recent_df = sales_df[(sales_df["date"] >= recent_start) & (sales_df["date"] <= self.latest_date)]
        baseline_df = sales_df[(sales_df["date"] >= baseline_start) & (sales_df["date"] <= baseline_end)]

        recent_agg = recent_df.groupby(["store_id", "product_id"])["quantity_sold"].agg(["sum", "mean"]).reset_index()
        recent_agg.rename(columns={"sum": "recent_total", "mean": "recent_avg"}, inplace=True)

        baseline_agg = baseline_df.groupby(["store_id", "product_id"])["quantity_sold"].agg(["sum", "mean"]).reset_index()
        baseline_agg.rename(columns={"sum": "baseline_total", "mean": "baseline_avg"}, inplace=True)

        merged = recent_agg.merge(baseline_agg, on=["store_id", "product_id"], how="inner")
        # Ensure minimum volume to avoid noise
        merged = merged[merged["baseline_avg"] >= 1.0]

        merged["pct_change"] = ((merged["recent_avg"] - merged["baseline_avg"]) / merged["baseline_avg"] * 100).round(1)

        spikes = merged[merged["pct_change"] >= spike_threshold_pct].sort_values("pct_change", ascending=False)
        spikes = spikes.merge(products_df, on="product_id", how="left").merge(stores_df, on="store_id", how="left")

        results = []
        for _, row in spikes.iterrows():
            results.append({
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "category": row["category"],
                "store_id": row["store_id"],
                "store_name": row["store_name"],
                "recent_average": round(float(row["recent_avg"]), 2),
                "baseline_average": round(float(row["baseline_avg"]), 2),
                "recent_total_7d": int(row["recent_total"]),
                "baseline_total_30d": int(row["baseline_total"]),
                "percentage_change": float(row["pct_change"]),
                "recent_period": f"{recent_start.strftime('%Y-%m-%d')} to {self.latest_date.strftime('%Y-%m-%d')} (7d)",
                "baseline_period": f"{baseline_start.strftime('%Y-%m-%d')} to {baseline_end.strftime('%Y-%m-%d')} (30d)",
                "data_summary": {
                    "source": "sales.csv",
                    "recent_daily_avg": round(float(row["recent_avg"]), 2),
                    "baseline_daily_avg": round(float(row["baseline_avg"]), 2),
                    "increase_pct": float(row["pct_change"])
                },
                "calculation": f"({row['recent_avg']:.2f} - {row['baseline_avg']:.2f}) / {row['baseline_avg']:.2f} * 100 = +{row['pct_change']:.1f}%",
                "assumption": "Recent sales rate reflects an ongoing demand spike.",
                "recommendation": f"Monitor inventory closely and secure supplier replenishment to avoid unexpected stockout from sustained spike."
            })
        return results

    def get_sales_drops(self, drop_threshold_pct: float = -30.0) -> List[Dict[str, Any]]:
        """
        Compares recent 7-day average sales with previous 30-day baseline.
        Flags meaningful decreases <= -30%.
        """
        sales_df = self.loader.get_sales()
        products_df = self.loader.get_products()
        stores_df = self.loader.get_stores()

        recent_start = self.latest_date - timedelta(days=6)
        baseline_end = recent_start - timedelta(days=1)
        baseline_start = baseline_end - timedelta(days=29)

        recent_df = sales_df[(sales_df["date"] >= recent_start) & (sales_df["date"] <= self.latest_date)]
        baseline_df = sales_df[(sales_df["date"] >= baseline_start) & (sales_df["date"] <= baseline_end)]

        recent_agg = recent_df.groupby(["store_id", "product_id"])["quantity_sold"].agg(["sum", "mean"]).reset_index()
        recent_agg.rename(columns={"sum": "recent_total", "mean": "recent_avg"}, inplace=True)

        baseline_agg = baseline_df.groupby(["store_id", "product_id"])["quantity_sold"].agg(["sum", "mean"]).reset_index()
        baseline_agg.rename(columns={"sum": "baseline_total", "mean": "baseline_avg"}, inplace=True)

        merged = recent_agg.merge(baseline_agg, on=["store_id", "product_id"], how="inner")
        merged = merged[merged["baseline_avg"] >= 1.5]  # Meaningful baseline

        merged["pct_change"] = ((merged["recent_avg"] - merged["baseline_avg"]) / merged["baseline_avg"] * 100).round(1)

        drops = merged[merged["pct_change"] <= drop_threshold_pct].sort_values("pct_change")
        drops = drops.merge(products_df, on="product_id", how="left").merge(stores_df, on="store_id", how="left")

        results = []
        for _, row in drops.iterrows():
            results.append({
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "category": row["category"],
                "store_id": row["store_id"],
                "store_name": row["store_name"],
                "recent_average": round(float(row["recent_avg"]), 2),
                "baseline_average": round(float(row["baseline_avg"]), 2),
                "recent_total_7d": int(row["recent_total"]),
                "baseline_total_30d": int(row["baseline_total"]),
                "percentage_change": float(row["pct_change"]),
                "recent_period": f"{recent_start.strftime('%Y-%m-%d')} to {self.latest_date.strftime('%Y-%m-%d')} (7d)",
                "baseline_period": f"{baseline_start.strftime('%Y-%m-%d')} to {baseline_end.strftime('%Y-%m-%d')} (30d)",
                "data_summary": {
                    "source": "sales.csv",
                    "recent_daily_avg": round(float(row["recent_avg"]), 2),
                    "baseline_daily_avg": round(float(row["baseline_avg"]), 2),
                    "drop_pct": float(row["pct_change"])
                },
                "calculation": f"({row['recent_avg']:.2f} - {row['baseline_avg']:.2f}) / {row['baseline_avg']:.2f} * 100 = {row['pct_change']:.1f}%",
                "assumption": "Assumes shelf availability was maintained during this period.",
                "recommendation": f"Verify on-shelf display placement, check for defective stock, and hold pending reorders."
            })
        return results

    def get_product_performance(self, product_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns 30-day and 90-day sales, revenue, profit, and stock health for one or all products."""
        sales_df = self.loader.get_sales()
        inv_df = self.loader.get_inventory()
        products_df = self.loader.get_products()

        thirty_days_ago = self.latest_date - timedelta(days=29)
        sales_30d = sales_df[sales_df["date"] >= thirty_days_ago]

        agg_30d = sales_30d.groupby("product_id").agg({
            "quantity_sold": "sum",
            "revenue": "sum"
        }).reset_index().rename(columns={"quantity_sold": "units_30d", "revenue": "revenue_30d"})

        # 90d total
        agg_90d = sales_df.groupby("product_id").agg({
            "quantity_sold": "sum",
            "revenue": "sum"
        }).reset_index().rename(columns={"quantity_sold": "units_90d", "revenue": "revenue_90d"})

        # Latest stock across all stores
        latest_inv = inv_df[inv_df["date"] == self.latest_date].groupby("product_id")["stock_quantity"].sum().reset_index()

        perf = products_df.merge(agg_30d, on="product_id", how="left").merge(agg_90d, on="product_id", how="left").merge(latest_inv, on="product_id", how="left")
        perf["units_30d"] = perf["units_30d"].fillna(0).astype(int)
        perf["revenue_30d"] = perf["revenue_30d"].fillna(0.0).round(2)
        perf["units_90d"] = perf["units_90d"].fillna(0).astype(int)
        perf["revenue_90d"] = perf["revenue_90d"].fillna(0.0).round(2)
        perf["stock_quantity"] = perf["stock_quantity"].fillna(0).astype(int)

        perf["avg_daily_sales_30d"] = (perf["units_30d"] / 30.0).round(2)
        perf["days_of_inventory"] = perf.apply(
            lambda r: round(r["stock_quantity"] / r["avg_daily_sales_30d"], 1) if r["avg_daily_sales_30d"] > 0 else (999.0 if r["stock_quantity"] > 0 else 0.0),
            axis=1
        )

        # Status badge
        def determine_status(r):
            if r["days_of_inventory"] <= 7.0 and r["avg_daily_sales_30d"] > 0:
                return "Stockout Risk"
            elif r["days_of_inventory"] >= 45.0 and r["stock_quantity"] > 0:
                return "Overstocked"
            elif r["units_90d"] <= 10 and r["stock_quantity"] > 20:
                return "Slow Moving"
            else:
                return "Healthy"

        perf["status"] = perf.apply(determine_status, axis=1)

        if product_id:
            perf = perf[perf["product_id"].str.upper() == product_id.upper()]

        return perf.to_dict(orient="records")

    def get_store_performance(self, store_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns 30-day performance per store with inventory and revenue comparisons."""
        sales_df = self.loader.get_sales()
        inv_df = self.loader.get_inventory()
        stores_df = self.loader.get_stores()
        products_df = self.loader.get_products()

        thirty_days_ago = self.latest_date - timedelta(days=29)
        sales_30d = sales_df[sales_df["date"] >= thirty_days_ago]

        store_sales = sales_30d.groupby("store_id").agg({
            "revenue": "sum",
            "quantity_sold": "sum"
        }).reset_index().rename(columns={"revenue": "revenue_30d", "quantity_sold": "units_30d"})

        latest_inv = inv_df[inv_df["date"] == self.latest_date].groupby("store_id")["stock_quantity"].sum().reset_index()

        perf = stores_df.merge(store_sales, on="store_id", how="left").merge(latest_inv, on="store_id", how="left")
        perf["revenue_30d"] = perf["revenue_30d"].fillna(0.0).round(2)
        perf["units_30d"] = perf["units_30d"].fillna(0).astype(int)
        perf["stock_quantity"] = perf["stock_quantity"].fillna(0).astype(int)

        # Share of sales
        total_rev = perf["revenue_30d"].sum()
        perf["revenue_share_pct"] = (perf["revenue_30d"] / total_rev * 100).round(1) if total_rev > 0 else 0.0

        if store_id:
            perf = perf[perf["store_id"].str.upper() == store_id.upper()]

        return perf.to_dict(orient="records")

    def get_category_performance(self) -> List[Dict[str, Any]]:
        """Returns sales, revenue, and stock breakdown grouped by category."""
        sales_df = self.loader.get_sales()
        inv_df = self.loader.get_inventory()
        products_df = self.loader.get_products()

        thirty_days_ago = self.latest_date - timedelta(days=29)
        sales_30d = sales_df[sales_df["date"] >= thirty_days_ago].merge(products_df[["product_id", "category"]], on="product_id", how="left")

        cat_sales = sales_30d.groupby("category").agg({
            "revenue": "sum",
            "quantity_sold": "sum"
        }).reset_index().rename(columns={"revenue": "revenue_30d", "quantity_sold": "units_30d"})

        latest_inv = inv_df[inv_df["date"] == self.latest_date].merge(products_df[["product_id", "category"]], on="product_id", how="left")
        cat_inv = latest_inv.groupby("category")["stock_quantity"].sum().reset_index()

        merged = cat_sales.merge(cat_inv, on="category", how="left")
        merged["revenue_30d"] = merged["revenue_30d"].round(2)
        total_rev = merged["revenue_30d"].sum()
        merged["revenue_share_pct"] = (merged["revenue_30d"] / total_rev * 100).round(1) if total_rev > 0 else 0.0

        return merged.sort_values("revenue_30d", ascending=False).to_dict(orient="records")

    def get_sales_trends(self, days: int = 90) -> List[Dict[str, Any]]:
        """Daily sales trend over the specified window (total across stores or grouped)."""
        sales_df = self.loader.get_sales()
        start_date = self.latest_date - timedelta(days=days - 1)
        period_df = sales_df[sales_df["date"] >= start_date]

        daily = period_df.groupby("date").agg({
            "revenue": "sum",
            "quantity_sold": "sum"
        }).reset_index().sort_values("date")

        daily["date_str"] = daily["date"].dt.strftime("%Y-%m-%d")
        daily["revenue"] = daily["revenue"].round(2)
        return daily[["date_str", "revenue", "quantity_sold"]].to_dict(orient="records")

    def get_inventory_status(self) -> Dict[str, Any]:
        """Aggregate breakdown of inventory health."""
        products = self.get_product_performance()
        total_items = len(products)
        stockouts = [p for p in products if p["status"] == "Stockout Risk"]
        overstocked = [p for p in products if p["status"] == "Overstocked"]
        slow = [p for p in products if p["status"] == "Slow Moving"]
        healthy = [p for p in products if p["status"] == "Healthy"]

        return {
            "total_products": total_items,
            "stockout_count": len(stockouts),
            "overstocked_count": len(overstocked),
            "slow_moving_count": len(slow),
            "healthy_count": len(healthy),
            "stockout_items": stockouts,
            "overstocked_items": overstocked,
            "slow_moving_items": slow
        }

    def get_reorder_recommendations(self) -> List[Dict[str, Any]]:
        """Provides prioritized restocking proposals based on stock-out risks and reorder thresholds."""
        stockouts = self.get_stockout_risks()
        products_df = self.loader.get_products()
        recs = []
        for item in stockouts:
            recs.append({
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "store_id": item["store_id"],
                "store_name": item["store_name"],
                "current_stock": item["current_stock"],
                "days_remaining": item["days_remaining"],
                "action": item["action"],
                "calculation": item["calculation"],
                "recommendation": item["recommendation"],
                "data_summary": item["data_summary"]
            })
        return recs

    def get_product_comparison(self, product_id_1: str, product_id_2: str) -> Dict[str, Any]:
        """Direct side-by-side comparison between two products."""
        p1_list = self.get_product_performance(product_id_1)
        p2_list = self.get_product_performance(product_id_2)

        p1 = p1_list[0] if p1_list else None
        p2 = p2_list[0] if p2_list else None

        return {
            "product_1": p1,
            "product_2": p2,
            "found_both": (p1 is not None and p2 is not None)
        }
