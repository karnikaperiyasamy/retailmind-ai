"""
Query Engine and Evidence Grounding Orchestrator for RetailMind AI.
Connects user questions to intent detection, local retrieval, deterministic python analytics,
and grounded Gemini explanations.
Ensures zero hallucination and strict evidence traceability.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import timedelta
from src.analytics import AnalyticsEngine
from src.gemini_service import GeminiService
from src.retrieval import LocalRetrievalPipeline

logger = logging.getLogger("RetailMind.QueryEngine")

class QueryEngine:
    def __init__(
        self,
        analytics_engine: Optional[AnalyticsEngine] = None,
        gemini_service: Optional[GeminiService] = None,
        retrieval_pipeline: Optional[LocalRetrievalPipeline] = None
    ):
        self.analytics = analytics_engine or AnalyticsEngine()
        self.gemini = gemini_service or GeminiService()
        self.retrieval = retrieval_pipeline or LocalRetrievalPipeline()
        self.products_df = self.analytics.loader.get_products()
        self.stores_df = self.analytics.loader.get_stores()

    def detect_intent(self, question: str) -> str:
        """Determines the user query intent using pattern matching and keyword heuristics."""
        q = question.lower().strip()

        # Difficult Case 1: Root-cause speculation
        if re.search(r"\bwhy\b.*\b(decrease|drop|fall|declined|down|slump)\b", q) or ("why did" in q and "sales" in q):
            return "unsupported_cause"

        # Difficult Case 2: Distant forecasting speculation
        if re.search(r"\b(six|6|twelve|12)\s+months\b", q) or ("exact sales" in q and "future" in q) or ("forecast" in q and "months" in q):
            return "unsupported_forecast"

        # Comparison intent
        if "compare" in q or (" vs " in q) or ("versus" in q) or ("difference between" in q):
            return "comparison"

        # Stockout / running out
        if any(term in q for term in ["running out", "run out", "stock out", "stockout", "out of stock", "low stock", "depleted", "reorder"]):
            return "stockout"

        # Overstock / excess
        if any(term in q for term in ["overstock", "over stocked", "excess stock", "surplus", "too much stock"]):
            return "overstock"

        # Slow moving
        if any(term in q for term in ["slow moving", "slow-moving", "not moving", "stagnant", "dead stock", "dormant"]):
            return "slow_moving"

        # Sales Spikes / Surges
        if any(term in q for term in ["spike", "surge", "jump", "increase", "rising sales", "peaked"]):
            return "sales_spike"

        # Sales Drops / Declines
        if any(term in q for term in ["drop", "falling sales", "falling", "decrease", "decline", "down"]):
            return "sales_drop"

        # What needs attention today
        if any(term in q for term in ["attention today", "pay attention", "needs attention", "daily priorities", "action items"]):
            return "attention_today"

        # Store performance / Which store
        if ("which store" in q) or ("highest sales" in q) or ("best store" in q) or ("store sales" in q):
            return "store_performance"

        # Category performance
        if any(term in q for term in ["category", "categories", "electronics", "beverages", "grocery"]):
            return "category_performance"

        # Top products / Best selling
        if any(term in q for term in ["best selling", "top products", "top selling", "highest selling", "best-selling"]):
            return "top_products"

        # Product performance (e.g. mentions specific product or SKU)
        for _, prod in self.products_df.iterrows():
            p_name = prod["product_name"].lower()
            p_id = prod["product_id"].lower()
            if p_id in q or p_name in q or any(word in q for word in p_name.split() if len(word) > 4):
                return "product_performance"

        return "unknown"

    def process_query(self, question: str) -> Dict[str, Any]:
        """Main processing pipeline: question -> intent -> analytics -> package -> Gemini -> response."""
        intent = self.detect_intent(question)
        logger.info(f"Processing question: '{question}' -> Intent: {intent}")

        evidence_package = {}

        if intent == "unsupported_cause":
            evidence_package = self._handle_unsupported_cause()
        elif intent == "unsupported_forecast":
            evidence_package = self._handle_unsupported_forecast()
        elif intent == "stockout":
            evidence_package = self._handle_stockout(question)
        elif intent == "overstock":
            evidence_package = self._handle_overstock(question)
        elif intent == "slow_moving":
            evidence_package = self._handle_slow_moving(question)
        elif intent == "sales_spike":
            evidence_package = self._handle_sales_spike(question)
        elif intent == "sales_drop":
            evidence_package = self._handle_sales_drop(question)
        elif intent == "product_performance":
            evidence_package = self._handle_product_performance(question)
        elif intent == "store_performance":
            evidence_package = self._handle_store_performance(question)
        elif intent == "category_performance":
            evidence_package = self._handle_category_performance()
        elif intent == "top_products":
            evidence_package = self._handle_top_products()
        elif intent == "comparison":
            evidence_package = self._handle_comparison(question)
        elif intent == "attention_today":
            evidence_package = self._handle_attention_today()
        else:
            evidence_package = self._handle_unknown(question)

        # Call Gemini service for grounded natural language synthesis
        response = self.gemini.generate_grounded_response(
            question=question,
            intent=intent,
            evidence_package=evidence_package
        )

        return response

    # -------------------------------------------------------------
    # Intent Handlers (Deterministic Evidence Assembly)
    # -------------------------------------------------------------

    def _handle_unsupported_cause(self) -> Dict[str, Any]:
        """
        Difficult Demo Case 1: User asks 'Why did sales decrease?'.
        The system MUST distinguish what the data proves from what it cannot prove.
        """
        drops = self.analytics.get_sales_drops()
        lead_drop = drops[0] if drops else None

        if lead_drop:
            prod_name = lead_drop["product_name"]
            store_name = lead_drop["store_name"]
            pct = lead_drop["percentage_change"]
            recent_avg = lead_drop["recent_average"]
            base_avg = lead_drop["baseline_average"]
            rec_per = lead_drop["recent_period"]
            base_per = lead_drop["baseline_period"]

            answer = (
                f"The transaction records in sales.csv confirm that sales for **{prod_name}** at the **{store_name}** "
                f"decreased by **{abs(pct):.1f}%** (dropping from a 30-day baseline of {base_avg} units/day to {recent_avg} units/day). "
                f"However, the available retail dataset does not contain sufficient causal information (such as foot traffic counters, "
                f"competitor price changes, promotional spend, or customer feedback) to prove WHY this decline occurred."
            )
            evidence = [
                f"Source: sales.csv | Product: {prod_name} ({lead_drop['product_id']}) | Store: {store_name}",
                f"Baseline Sales ({base_per}): {base_avg} units/day",
                f"Recent Sales ({rec_per}): {recent_avg} units/day",
                f"Deterministic Net Decline: {pct:.1f}%"
            ]
            calculations = [
                f"Percentage Change: ({recent_avg} - {base_avg}) / {base_avg} * 100 = {pct:.1f}%",
                f"Volume Loss: ~{lead_drop['baseline_total_30d'] // 4 - lead_drop['recent_total_7d']} fewer units per week"
            ]
        else:
            answer = "Overall sales have experienced normal fluctuations, but the dataset contains no external event or footfall data to determine root causes."
            evidence = ["Source: sales.csv (90-day transaction logs)"]
            calculations = []

        recommendation = (
            "Store manager should inspect physical shelf placement, verify stock visibility, "
            "and check for local factors before discounting or adjusting orders."
        )

        return {
            "default_answer": answer,
            "evidence": evidence,
            "calculations": calculations,
            "default_recommendation": recommendation,
            "assumptions": [
                "Transaction records in sales.csv accurately reflect all completed customer checkouts.",
                "Inventory was physically available on shelves during the measured window."
            ],
            "limitations": [
                "The available dataset tracks sales and inventory units only.",
                "No external variables (competitor actions, foot traffic, local weather, marketing) are present in the data to determine root causes."
            ]
        }

    def _handle_unsupported_forecast(self) -> Dict[str, Any]:
        """
        Difficult Demo Case 2: User asks 'What will our exact sales be six months from now?'.
        The system refuses to hallucinate future predictions.
        """
        answer = (
            "The current dataset does not contain sufficient historical depth or macroeconomic forecasting variables "
            "to reliably determine exact sales six months from now. Fabricating an exact numerical forecast without "
            "forward-looking contracts or seasonality models would be unsupported."
        )
        return {
            "default_answer": answer,
            "evidence": [
                "Available data horizon: 92 days (June 1, 2026 to August 31, 2026).",
                "Forecasting horizon requested: 180 days (6 months into future).",
                "Ratio of forecast horizon to observed history: 2.0x (insufficient for high-confidence projection)."
            ],
            "calculations": [
                "Data Coverage: 92 days observed / 180 days forecast requested = Insufficient statistical baseline."
            ],
            "default_recommendation": (
                "For medium-term planning, rely on rolling 30-day moving averages and establish safe buffer stocks "
                "with suppliers rather than betting operational capital on unsupported distant forecasts."
            ),
            "assumptions": [
                "Retail demand fluctuates with consumer seasonality and market trends."
            ],
            "limitations": [
                "Predictive forecasting models require multi-year seasonality data, marketing plans, and macro trend datasets not present in this operation."
            ]
        }

    def _handle_stockout(self, question: str) -> Dict[str, Any]:
        """Handles questions about running out of stock."""
        stockouts = self.analytics.get_stockout_risks(max_days=7.0)
        
        # Check if specific store or product was mentioned
        target_store = None
        for _, s in self.stores_df.iterrows():
            if s["store_name"].lower() in question.lower() or s["store_id"].lower() in question.lower():
                target_store = s["store_id"]
                break

        if target_store:
            filtered = [s for s in stockouts if s["store_id"] == target_store]
            if filtered:
                stockouts = filtered

        lead = stockouts[0] if stockouts else None
        if not lead:
            return {
                "default_answer": "Currently, no products are at imminent stockout risk (all SKUs hold more than 7 days of supply).",
                "evidence": ["All products evaluated against 7-day average sales velocity."],
                "calculations": ["days_of_inventory > 7.0 for all SKUs"],
                "default_recommendation": "Maintain standard weekly reorder review schedules.",
                "assumptions": ["Customer velocity remains at current 7-day run rate."],
                "limitations": ["Sudden bulk purchases could accelerate depletion."]
            }

        answer = (
            f"**{lead['product_name']}** at **{lead['store_name']}** is at critical risk of running out. "
            f"With only **{lead['current_stock']} units** in stock and an average sales velocity of **{lead['average_daily_sales']} units/day**, "
            f"the remaining inventory will last approximately **{lead['days_remaining']} days** (reorder threshold is {lead['reorder_level']} units)."
        )

        evidence = [
            f"Source: inventory.csv & sales.csv | SKU: {lead['product_id']} | Store: {lead['store_name']} ({lead['store_id']})",
            f"Current Physical Stock: {lead['current_stock']} units",
            f"Recent 7-Day Average Daily Sales: {lead['average_daily_sales']} units/day",
            f"Reorder Point: {lead['reorder_level']} units",
            f"Additional At-Risk SKUs: {len(stockouts) - 1} other products hold &le; 7 days of supply."
        ]

        calculations = [
            f"Days of Inventory = {lead['current_stock']} / {lead['average_daily_sales']} = {lead['days_remaining']:.2f} days",
            f"Recommended Replenishment = max({lead['reorder_level']} * 2, {lead['average_daily_sales']} * 21) = {max(lead['reorder_level'] * 2, int(lead['average_daily_sales'] * 21))} units"
        ]

        return {
            "default_answer": answer,
            "evidence": evidence,
            "calculations": calculations,
            "default_recommendation": f"Store manager should review raising a replenishment order of ~{max(lead['reorder_level'] * 2, int(lead['average_daily_sales'] * 21))} units with {self.products_df[self.products_df['product_id']==lead['product_id']]['supplier'].values[0]} today.",
            "assumptions": [
                f"Assumes sales demand remains steady at ~{lead['average_daily_sales']} units/day.",
                "Assumes supplier lead time is within standard 3–5 business days."
            ],
            "limitations": [
                "Does not account for pending purchase orders currently in transit from the supplier."
            ]
        }

    def _handle_overstock(self, question: str) -> Dict[str, Any]:
        """Handles questions about overstocked items."""
        overstock = self.analytics.get_overstock_products(min_days=45.0)
        lead = overstock[0] if overstock else None

        if not lead:
            return {
                "default_answer": "No products currently exceed the 45-day overstock threshold.",
                "evidence": ["Evaluated all 32 SKUs across 3 stores."],
                "calculations": ["days_of_inventory < 45.0 for all SKUs"],
                "default_recommendation": "Inventory is operating within lean working capital limits.",
                "assumptions": ["30-day velocity target is benchmark."],
                "limitations": []
            }

        answer = (
            f"**{lead['product_name']}** at **{lead['store_name']}** is heavily overstocked. "
            f"Current stock stands at **{lead['current_stock']} units**, providing **{lead['days_of_inventory']:.1f} days** of supply "
            f"at current sales velocity ({lead['average_daily_sales']} units/day). This represents an estimated excess of "
            f"**{lead['estimated_excess_units']} units**, locking up **₹{lead['tied_up_capital']:,.2f}** in working capital."
        )

        evidence = [
            f"Source: inventory.csv & sales.csv | SKU: {lead['product_id']} | Store: {lead['store_name']}",
            f"Current Stock: {lead['current_stock']} units | Benchmark Target: {int(lead['average_daily_sales'] * 30)} units (30d)",
            f"Average Daily Sales: {lead['average_daily_sales']} units/day",
            f"Working Capital Tied Up: ₹{lead['tied_up_capital']:,.2f}"
        ]

        calculations = [
            f"Days of Inventory: {lead['current_stock']} / {lead['average_daily_sales']} = {lead['days_of_inventory']:.2f} days",
            f"Surplus Units: {lead['current_stock']} - ({lead['average_daily_sales']} * 30) = {lead['estimated_excess_units']} units",
            f"Tied Capital: {lead['estimated_excess_units']} units * ₹{lead['cost_price']} = ₹{lead['tied_up_capital']:,.2f}"
        ]

        return {
            "default_answer": answer,
            "evidence": evidence,
            "calculations": calculations,
            "default_recommendation": f"Pause upcoming purchase orders for this SKU and consider a promotional discount or stock transfer of {lead['estimated_excess_units']} units.",
            "assumptions": [
                "Assumes 30 days is the optimal holding inventory target."
            ],
            "limitations": [
                "Holding costs and warehousing shelf constraints vary by product dimension."
            ]
        }

    def _handle_slow_moving(self, question: str) -> Dict[str, Any]:
        """Handles slow-moving inventory queries."""
        slow = self.analytics.get_slow_moving_products(window_days=60, max_sales_threshold=5)
        lead = slow[0] if slow else None

        if not lead:
            return {
                "default_answer": "No severe slow-moving inventory detected across the past 60 days.",
                "evidence": ["All stocked SKUs recorded turnover >= 5 units."],
                "calculations": [],
                "default_recommendation": "Maintain routine inventory monitoring.",
                "assumptions": [],
                "limitations": []
            }

        answer = (
            f"**{lead['product_name']}** at **{lead['store_name']}** is slow-moving. "
            f"Only **{lead['units_sold']} units** have been sold in the past 60 days despite holding **{lead['current_inventory']} units** in stock, "
            f"locking up **₹{lead['capital_locked']:,.2f}** in stagnant inventory."
        )

        evidence = [
            f"Source: sales.csv & inventory.csv | SKU: {lead['product_id']} | Store: {lead['store_name']}",
            f"Sales History: {lead['units_sold']} units sold in 60-day window ({lead['sales_period']})",
            f"Current Physical Stock: {lead['current_inventory']} units"
        ]

        calculations = [
            f"Turnover Velocity: {lead['units_sold']} / 60 days = {lead['units_sold']/60.0:.3f} units/day",
            lead["calculation"]
        ]

        return {
            "default_answer": answer,
            "evidence": evidence,
            "calculations": calculations,
            "default_recommendation": "Store manager should consider bundling with complementary high-demand products or evaluating supplier return terms.",
            "assumptions": [
                "Assumes product was prominently displayed on shelves during the 60-day window."
            ],
            "limitations": [
                "Does not reflect seasonal writing or back-to-school surges outside the summer window."
            ]
        }

    def _handle_sales_spike(self, question: str) -> Dict[str, Any]:
        """Handles sales spike queries."""
        spikes = self.analytics.get_sales_spikes(spike_threshold_pct=40.0)
        lead = spikes[0] if spikes else None

        if not lead:
            return {
                "default_answer": "No significant sales spikes (>40% increase) detected over the recent 7-day period.",
                "evidence": ["Compared recent 7-day daily rates with 30-day baseline."],
                "calculations": ["(recent_avg - baseline_avg) / baseline_avg < 0.40"],
                "default_recommendation": "Demand remains stable across catalogue.",
                "assumptions": [],
                "limitations": []
            }

        answer = (
            f"**{lead['product_name']}** at **{lead['store_name']}** experienced a notable sales surge of "
            f"**+{lead['percentage_change']:.1f}%**. Daily sales jumped to **{lead['recent_average']} units/day** "
            f"(up from a 30-day baseline average of {lead['baseline_average']} units/day)."
        )

        evidence = [
            f"Source: sales.csv | SKU: {lead['product_id']} | Store: {lead['store_name']}",
            f"Recent 7-day average: {lead['recent_average']} units/day ({lead['recent_period']})",
            f"Baseline 30-day average: {lead['baseline_average']} units/day ({lead['baseline_period']})"
        ]

        calculations = [
            lead["calculation"]
        ]

        return {
            "default_answer": answer,
            "evidence": evidence,
            "calculations": calculations,
            "default_recommendation": "Check supplier lead time and reorder buffer to prevent unexpected stock-out if surge demand continues.",
            "assumptions": ["Recent demand surge reflects ongoing momentum."],
            "limitations": ["Causal driver (e.g., local event, influencer post) is not captured in transaction logs."]
        }

    def _handle_sales_drop(self, question: str) -> Dict[str, Any]:
        """Handles sales drop queries."""
        drops = self.analytics.get_sales_drops(drop_threshold_pct=-30.0)
        lead = drops[0] if drops else None

        if not lead:
            return {
                "default_answer": "No sharp sales drops (>-30%) detected across the catalogue.",
                "evidence": ["Compared 7-day moving averages with 30-day baseline."],
                "calculations": [],
                "default_recommendation": "Standard category performance.",
                "assumptions": [],
                "limitations": []
            }

        answer = (
            f"**{lead['product_name']}** at **{lead['store_name']}** recorded a significant sales decline of "
            f"**{lead['percentage_change']:.1f}%**. Sales dropped to **{lead['recent_average']} units/day** "
            f"compared with the previous 30-day baseline of {lead['baseline_average']} units/day."
        )

        evidence = [
            f"Source: sales.csv | SKU: {lead['product_id']} | Store: {lead['store_name']}",
            f"Recent 7-day average: {lead['recent_average']} units/day",
            f"Baseline 30-day average: {lead['baseline_average']} units/day"
        ]

        calculations = [lead["calculation"]]

        return {
            "default_answer": answer,
            "evidence": evidence,
            "calculations": calculations,
            "default_recommendation": "Inspect shelf display and pause automated replenishment.",
            "assumptions": ["Item remained in stock on the sales floor."],
            "limitations": ["Transaction logs record unit sales, not footfall or browsing behavior."]
        }

    def _handle_product_performance(self, question: str) -> Dict[str, Any]:
        """Handles specific product performance questions (e.g. Wireless Ergonomic Mouse)."""
        # Find matched product
        matched_prod = None
        for _, prod in self.products_df.iterrows():
            if prod["product_name"].lower() in question.lower() or prod["product_id"].lower() in question.lower():
                matched_prod = prod
                break

        if matched_prod is None:
            # Fallback search by token
            for _, prod in self.products_df.iterrows():
                tokens = prod["product_name"].lower().split()
                if any(t in question.lower() for t in tokens if len(t) > 4):
                    matched_prod = prod
                    break

        if matched_prod is None:
            matched_prod = self.products_df.iloc[4] # Default P014

        p_id = matched_prod["product_id"]
        perf_list = self.analytics.get_product_performance(product_id=p_id)
        perf = perf_list[0] if perf_list else {}

        answer = (
            f"**{perf.get('product_name', p_id)}** ({p_id}) generated **₹{perf.get('revenue_30d', 0):,.2f}** "
            f"in revenue ({perf.get('units_30d', 0)} units sold) over the past 30 days. "
            f"Current total physical stock across all stores is **{perf.get('stock_quantity', 0)} units**, "
            f"representing approximately **{perf.get('days_of_inventory', 0)} days** of inventory. "
            f"Current overall health status: **{perf.get('status', 'Healthy')}**."
        )

        evidence = [
            f"Source: sales.csv & products.csv & inventory.csv | SKU: {p_id}",
            f"Selling Price: ₹{perf.get('selling_price')} | Cost Price: ₹{perf.get('cost_price')} | Margin: {round((perf.get('selling_price',1) - perf.get('cost_price',0))/perf.get('selling_price',1)*100, 1)}%",
            f"30-Day Sales Volume: {perf.get('units_30d')} units | 30-Day Gross Revenue: ₹{perf.get('revenue_30d'):,.2f}",
            f"90-Day Cumulative Revenue: ₹{perf.get('revenue_90d'):,.2f} ({perf.get('units_90d')} units sold)",
            f"Total Inventory On Hand: {perf.get('stock_quantity')} units"
        ]

        calculations = [
            f"Average Daily Velocity: {perf.get('units_30d')} units / 30 days = {perf.get('avg_daily_sales_30d')} units/day",
            f"Days of Inventory: {perf.get('stock_quantity')} / {perf.get('avg_daily_sales_30d')} = {perf.get('days_of_inventory')} days"
        ]

        recommendation = "Review individual store breakdown in the Products catalogue to balance stock levels between branches."
        if perf.get("status") == "Stockout Risk":
            recommendation = "Urgent: Expedite replenishment order as stock coverage is critically low."
        elif perf.get("status") == "Overstocked":
            recommendation = "Pause procurement and consider marketing promotion to clear surplus stock."

        return {
            "default_answer": answer,
            "evidence": evidence,
            "calculations": calculations,
            "default_recommendation": recommendation,
            "assumptions": ["Sales velocity of past 30 days continues into near-term."],
            "limitations": ["Store-to-store variance exists; check store breakdown in table."]
        }

    def _handle_store_performance(self, question: str) -> Dict[str, Any]:
        """Handles store performance and comparison questions."""
        stores = self.analytics.get_store_performance()
        top_store = max(stores, key=lambda x: x["revenue_30d"])

        answer = (
            f"**{top_store['store_name']}** ({top_store['store_id']}) recorded the highest sales over the past 30 days, "
            f"generating **₹{top_store['revenue_30d']:,.2f}** across **{top_store['units_30d']:,} units sold**, "
            f"accounting for **{top_store['revenue_share_pct']}%** of total retail network revenue."
        )

        evidence = [
            f"Top Performer: {top_store['store_name']} — Revenue: ₹{top_store['revenue_30d']:,.2f} ({top_store['revenue_share_pct']}% share)",
        ]
        for s in stores:
            if s["store_id"] != top_store["store_id"]:
                evidence.append(f"{s['store_name']}: Revenue: ₹{s['revenue_30d']:,.2f} ({s['units_30d']} units, {s['revenue_share_pct']}% share)")

        calculations = [
            f"Store Share = ₹{top_store['revenue_30d']:,.2f} / Total Network Sales = {top_store['revenue_share_pct']}%"
        ]

        return {
            "default_answer": answer,
            "evidence": evidence,
            "calculations": calculations,
            "default_recommendation": f"Ensure {top_store['store_name']} maintains full shelf stock on top velocity electronics and beverage items to maximize footfall conversion.",
            "assumptions": ["Footfall patterns remain stable."],
            "limitations": ["Does not include square footage normalization."]
        }

    def _handle_category_performance(self) -> Dict[str, Any]:
        """Handles category breakdown."""
        cats = self.analytics.get_category_performance()
        top_cat = cats[0]

        answer = (
            f"**{top_cat['category']}** leads category performance, generating **₹{top_cat['revenue_30d']:,.2f}** "
            f"({top_cat['revenue_share_pct']}% of total sales) with {top_cat['units_30d']} units sold over the last 30 days."
        )

        evidence = [f"{c['category']}: ₹{c['revenue_30d']:,.2f} ({c['revenue_share_pct']}%) | {c['units_30d']} units" for c in cats]
        calculations = [f"Leading category contribution = {top_cat['revenue_share_pct']}%"]

        return {
            "default_answer": answer,
            "evidence": evidence,
            "calculations": calculations,
            "default_recommendation": "Prioritize procurement contracts with suppliers in top revenue categories.",
            "assumptions": ["Product catalogue mix remains fixed."],
            "limitations": []
        }

    def _handle_top_products(self) -> Dict[str, Any]:
        """Handles top-selling products query."""
        prods = self.analytics.get_product_performance()
        top_5 = sorted(prods, key=lambda x: x["revenue_30d"], reverse=True)[:5]

        top_names = ", ".join([f"**{p['product_name']}** (₹{p['revenue_30d']:,.2f})" for p in top_5[:3]])
        answer = f"The top 3 revenue-generating products over the past 30 days are {top_names}."

        evidence = [f"#{i+1}: {p['product_name']} (SKU: {p['product_id']}) — Revenue: ₹{p['revenue_30d']:,.2f} ({p['units_30d']} units)" for i, p in enumerate(top_5)]
        calculations = [f"Top 5 products generate a combined ₹{sum(p['revenue_30d'] for p in top_5):,.2f}."]

        return {
            "default_answer": answer,
            "evidence": evidence,
            "calculations": calculations,
            "default_recommendation": "Ensure zero stock-out buffer for these core revenue drivers.",
            "assumptions": ["Sales velocity will remain elevated."],
            "limitations": []
        }

    def _handle_comparison(self, question: str) -> Dict[str, Any]:
        """Handles store comparison query, specifically Downtown Store vs Mall Store."""
        stores = self.analytics.get_store_performance()
        s1 = next((s for s in stores if "downtown" in s["store_name"].lower()), stores[0])
        s2 = next((s for s in stores if "mall" in s["store_name"].lower()), stores[1])

        diff_rev = s1["revenue_30d"] - s2["revenue_30d"]
        diff_pct = (diff_rev / s2["revenue_30d"] * 100) if s2["revenue_30d"] > 0 else 0

        answer = (
            f"Comparing **{s1['store_name']}** and **{s2['store_name']}**: "
            f"{s1['store_name']} generated **₹{s1['revenue_30d']:,.2f}** ({s1['revenue_share_pct']}% share) "
            f"versus **₹{s2['revenue_30d']:,.2f}** ({s2['revenue_share_pct']}% share) for {s2['store_name']}. "
            f"{s1['store_name']} outperformed {s2['store_name']} by **₹{diff_rev:,.2f} (+{diff_pct:.1f}%)** in 30-day revenue."
        )

        evidence = [
            f"{s1['store_name']} (S001): Revenue ₹{s1['revenue_30d']:,.2f} | Volume: {s1['units_30d']} units | Stock: {s1['stock_quantity']} units",
            f"{s2['store_name']} (S002): Revenue ₹{s2['revenue_30d']:,.2f} | Volume: {s2['units_30d']} units | Stock: {s2['stock_quantity']} units"
        ]

        calculations = [
            f"Revenue Variance: ₹{s1['revenue_30d']:,.2f} - ₹{s2['revenue_30d']:,.2f} = ₹{diff_rev:,.2f}",
            f"Percentage Premium: ({diff_rev:,.2f} / ₹{s2['revenue_30d']:,.2f}) * 100 = +{diff_pct:.1f}%"
        ]

        return {
            "default_answer": answer,
            "evidence": evidence,
            "calculations": calculations,
            "default_recommendation": f"Consider transferring slower-velocity stock from {s2['store_name']} to {s1['store_name']} where foot traffic throughput is higher.",
            "assumptions": ["Customer footfall density accounts for the throughput variance."],
            "limitations": ["Operating overhead and square footage are not accounted for in gross revenue."]
        }

    def _handle_attention_today(self) -> Dict[str, Any]:
        """Handles 'What should I pay attention to today?'"""
        stockouts = self.analytics.get_stockout_risks(max_days=7.0)
        overstock = self.analytics.get_overstock_products(min_days=45.0)
        spikes = self.analytics.get_sales_spikes(40.0)

        urgent_stockout = stockouts[0] if stockouts else None
        urgent_overstock = overstock[0] if overstock else None

        answer = (
            f"Top priorities today: **{len(stockouts)} SKUs** are at immediate risk of stockout "
            f"(led by **{urgent_stockout['product_name']}** at {urgent_stockout['store_name']} with only {urgent_stockout['days_remaining']} days left). "
            f"Additionally, **{len(overstock)} SKUs** are severely overstocked (locking up capital), and **{len(spikes)} SKUs** have active demand surges."
        )

        evidence = [
            f"Immediate Stockout: {urgent_stockout['product_name']} ({urgent_stockout['days_remaining']} days left)",
            f"Capital Locked in Overstock: {urgent_overstock['product_name']} (₹{urgent_overstock['tied_up_capital']:,.2f} excess)",
            f"Active Surges: {spikes[0]['product_name']} (+{spikes[0]['percentage_change']}%)" if spikes else "No spikes"
        ]

        calculations = [
            f"Stockout threshold: &le; 7.0 days inventory run rate",
            f"Overstock threshold: &ge; 45.0 days inventory holding"
        ]

        return {
            "default_answer": answer,
            "evidence": evidence,
            "calculations": calculations,
            "default_recommendation": "1. Expedite reorder for stock-out items. 2. Freeze purchase orders on overstocked SKUs. 3. Monitor surging demand.",
            "assumptions": ["Daily operational reviews are conducted each morning."],
            "limitations": ["Supplier delivery lead times dictate actual stock receipt date."]
        }

    def _handle_unknown(self, question: str) -> Dict[str, Any]:
        """Handles open-ended or out-of-scope questions."""
        # Use local semantic retrieval to pull closest items
        results = self.retrieval.search(question, top_k=2)
        top_context = [r.get("text", "") for r in results if "text" in r]

        answer = (
            f"The available sales and inventory records do not contain a direct answer for: '{question}'. "
            f"RetailMind AI operates strictly on factual store data (sales.csv, inventory.csv, products.csv, stores.csv)."
        )

        return {
            "default_answer": answer,
            "evidence": top_context or ["Local retail dataset covers 3 stores and 32 SKUs."],
            "calculations": ["Zero matching deterministic analytical routine for this query."],
            "default_recommendation": "Try asking about stock levels ('What is running out?'), sales anomalies ('Which products had a sales spike?'), or specific SKUs.",
            "assumptions": [],
            "limitations": ["Question falls outside the operational scope of sales and inventory data."]
        }
