"""
Attention Center Service for RetailMind AI.
Aggregates, ranks, and prioritizes operational alerts across stockouts,
excess inventory, dormant stock, sales surges, and steep declines.
Ensures human-in-the-loop review guidelines are attached to every alert.
"""

from typing import Dict, List, Any
from src.analytics import AnalyticsEngine
from src.recommendations import RecommendationEngine

class AttentionCenter:
    def __init__(self, analytics_engine: AnalyticsEngine):
        self.analytics = analytics_engine

    def get_attention_feed(self) -> Dict[str, Any]:
        """Collects and prioritizes all alerts for immediate store manager attention."""
        stockouts = self.analytics.get_stockout_risks(max_days=7.0)
        overstocked = self.analytics.get_overstock_products(min_days=45.0)
        slow_moving = self.analytics.get_slow_moving_products(window_days=60, max_sales_threshold=5)
        spikes = self.analytics.get_sales_spikes(spike_threshold_pct=40.0)
        drops = self.analytics.get_sales_drops(drop_threshold_pct=-30.0)

        # Sort stockouts by urgency (lowest days remaining first)
        sorted_stockouts = sorted(stockouts, key=lambda x: x["days_remaining"])
        # Sort overstock by tied up capital (highest capital first)
        sorted_overstock = sorted(overstocked, key=lambda x: x["tied_up_capital"], reverse=True)

        return {
            "summary": {
                "stockout_count": len(stockouts),
                "overstock_count": len(overstocked),
                "slow_moving_count": len(slow_moving),
                "sales_spikes_count": len(spikes),
                "sales_drops_count": len(drops),
                "critical_urgency_count": len([s for s in stockouts if s["days_remaining"] <= 3.0]),
                "total_alerts": len(stockouts) + len(overstocked) + len(slow_moving) + len(spikes) + len(drops)
            },
            "stockouts": sorted_stockouts,
            "overstocked": sorted_overstock,
            "slow_moving": slow_moving,
            "spikes": spikes,
            "drops": drops,
            "human_in_the_loop_protocol": (
                "RetailMind AI provides evidence-backed recommendations only. "
                "Store managers must verify local shelf conditions and supplier terms "
                "prior to executing stock reorders, markdown actions, or transfers."
            )
        }
