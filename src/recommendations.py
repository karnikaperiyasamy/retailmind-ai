"""
Recommendation and Evidence Formulation module for RetailMind AI.
Standardizes structured operational recommendations strictly adhering to the 4-part schema:
- DATA: Raw verified metrics
- CALCULATION: Explicit arithmetic step
- ASSUMPTION: Transparent operational assumptions
- RECOMMENDATION: Non-autonomous decision proposals (human-in-the-loop)
"""

from typing import Dict, Any, List

class RecommendationEngine:
    @staticmethod
    def format_stockout_recommendation(item: Dict[str, Any]) -> Dict[str, Any]:
        curr_stock = item["current_stock"]
        ads = item["average_daily_sales"]
        doi = item["days_remaining"]
        reorder = item["reorder_level"]
        store = item["store_name"]
        product = item["product_name"]

        target_restock = max(reorder * 2, int(ads * 21))

        data = {
            "Product": product,
            "Store": store,
            "Current Stock": f"{curr_stock} units",
            "Average Daily Sales (7d)": f"{ads:.2f} units/day",
            "Reorder Threshold": f"{reorder} units"
        }

        calc = f"{curr_stock} units / {ads:.2f} units/day = {doi:.2f} days of inventory"
        assumption = f"Assumes customer purchase velocity remains consistent with the past 7 days (~{ads:.2f} units/day) and supplier lead times are normal."
        rec = f"Store manager should review raising a replenishment order of approximately {target_restock} units for {product} at {store} to prevent stock-out within ~{doi:.1f} days."

        return {
            "type": "stockout_risk",
            "product_id": item["product_id"],
            "product_name": product,
            "store_id": item["store_id"],
            "store_name": store,
            "data": data,
            "calculation": calc,
            "assumption": assumption,
            "recommendation": rec,
            "human_in_the_loop_note": "Recommendation only. Store manager evaluates supplier terms and shelf space before issuing purchase order."
        }

    @staticmethod
    def format_overstock_recommendation(item: Dict[str, Any]) -> Dict[str, Any]:
        curr_stock = item["current_stock"]
        ads = item["average_daily_sales"]
        doi = item["days_of_inventory"]
        excess = item["estimated_excess_units"]
        tied_up = item["tied_up_capital"]
        store = item["store_name"]
        product = item["product_name"]

        data = {
            "Product": product,
            "Store": store,
            "Current Stock": f"{curr_stock} units",
            "Average Daily Sales (7d)": f"{ads:.2f} units/day",
            "Days of Inventory": f"{doi:.1f} days",
            "Estimated Excess (vs 30d baseline)": f"{excess} units",
            "Working Capital Tied Up": f"₹{tied_up:,.2f}"
        }

        calc = f"Days of Inventory: {curr_stock} / {ads:.2f} = {doi:.2f} days. Excess Stock: {curr_stock} - ({ads:.2f} * 30 days) = {excess} units (₹{tied_up:,.2f})"
        assumption = "Assumes healthy benchmark inventory target is 30 days of sales velocity."
        rec = f"Store manager should freeze upcoming purchase orders for this SKU and consider a promotional bundle or inter-store inventory transfer to balance working capital."

        return {
            "type": "overstock",
            "product_id": item["product_id"],
            "product_name": product,
            "store_id": item["store_id"],
            "store_name": store,
            "data": data,
            "calculation": calc,
            "assumption": assumption,
            "recommendation": rec,
            "human_in_the_loop_note": "Action requires manager sign-off. Do not automatically mark down or reallocate inventory."
        }

    @staticmethod
    def format_slow_moving_recommendation(item: Dict[str, Any]) -> Dict[str, Any]:
        units_sold = item["units_sold"]
        curr_stock = item["current_inventory"]
        capital = item["capital_locked"]
        product = item["product_name"]
        store = item["store_name"]

        data = {
            "Product": product,
            "Store": store,
            "Units Sold (Last 60 Days)": f"{units_sold} units",
            "Current Stock Holding": f"{curr_stock} units",
            "Locked Working Capital": f"₹{capital:,.2f}"
        }

        calc = f"Velocity: {units_sold} units / 60 days = {units_sold/60.0:.3f} units/day. Capital locked: {curr_stock} units * Cost = ₹{capital:,.2f}"
        assumption = "Assumes the item has been actively presented on the sales floor with adequate stock visibility."
        rec = f"Evaluate physical product placement, consider bundle merchandising with high-performing items, or review supplier return/buy-back policies."

        return {
            "type": "slow_moving",
            "product_id": item["product_id"],
            "product_name": product,
            "store_id": item["store_id"],
            "store_name": store,
            "data": data,
            "calculation": calc,
            "assumption": assumption,
            "recommendation": rec,
            "human_in_the_loop_note": "Operational decision reserved for store manager."
        }
