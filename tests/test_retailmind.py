"""
Automated Test Suite for RetailMind AI.
Tests dataset integrity, deterministic analytics, zero-division safeguards,
local embedding retrieval, query intent routing, evidence grounding,
refusal of ungrounded speculation, and Flask REST endpoints.
"""

import unittest
import json
import numpy as np
import pandas as pd
from app import app
from src.data_loader import DataLoader
from src.analytics import AnalyticsEngine
from src.retrieval import LocalRetrievalPipeline
from src.query_engine import QueryEngine

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        self.loader = DataLoader.get_instance()

    def test_datasets_loaded(self):
        self.assertIsNotNone(self.loader.stores_df)
        self.assertIsNotNone(self.loader.products_df)
        self.assertIsNotNone(self.loader.sales_df)
        self.assertIsNotNone(self.loader.inventory_df)

    def test_record_counts(self):
        self.assertEqual(len(self.loader.stores_df), 3)
        self.assertGreaterEqual(len(self.loader.products_df), 30)
        self.assertGreaterEqual(len(self.loader.sales_df), 8000)
        self.assertGreaterEqual(len(self.loader.inventory_df), 8000)

    def test_required_columns(self):
        prod_cols = {"product_id", "product_name", "category", "selling_price", "cost_price", "reorder_level", "supplier"}
        self.assertTrue(prod_cols.issubset(self.loader.products_df.columns))

        store_cols = {"store_id", "store_name", "location"}
        self.assertTrue(store_cols.issubset(self.loader.stores_df.columns))

        sales_cols = {"date", "store_id", "product_id", "quantity_sold", "revenue"}
        self.assertTrue(sales_cols.issubset(self.loader.sales_df.columns))

        inv_cols = {"date", "store_id", "product_id", "stock_quantity"}
        self.assertTrue(inv_cols.issubset(self.loader.inventory_df.columns))

class TestDeterministicAnalytics(unittest.TestCase):
    def setUp(self):
        self.engine = AnalyticsEngine()

    def test_dashboard_metrics(self):
        metrics = self.engine.get_dashboard_metrics()
        self.assertIn("total_sales_30d", metrics)
        self.assertIn("total_units_sold_30d", metrics)
        self.assertIn("total_current_stock", metrics)
        self.assertIn("gross_margin_pct", metrics)
        self.assertGreater(metrics["total_sales_30d"], 0)
        self.assertGreater(metrics["total_units_sold_30d"], 0)

    def test_stockout_risks(self):
        stockouts = self.engine.get_stockout_risks(max_days=7.0)
        self.assertIsInstance(stockouts, list)
        self.assertGreater(len(stockouts), 0)
        for s in stockouts:
            self.assertLessEqual(s["days_remaining"], 7.0)
            self.assertIn("calculation", s)
            self.assertIn("recommendation", s)
            self.assertIn("reorder_level", s)

    def test_overstock_products(self):
        overstock = self.engine.get_overstock_products(min_days=45.0)
        self.assertIsInstance(overstock, list)
        self.assertGreater(len(overstock), 0)
        for o in overstock:
            self.assertGreaterEqual(o["days_of_inventory"], 45.0)
            self.assertIn("estimated_excess_units", o)
            self.assertIn("tied_up_capital", o)

    def test_slow_moving_products(self):
        slow = self.engine.get_slow_moving_products(window_days=60, max_sales_threshold=5)
        self.assertIsInstance(slow, list)
        self.assertGreater(len(slow), 0)
        for sl in slow:
            self.assertLessEqual(sl["units_sold"], 5)
            self.assertGreaterEqual(sl["current_inventory"], 15)

    def test_sales_spikes_and_drops(self):
        spikes = self.engine.get_sales_spikes(spike_threshold_pct=40.0)
        drops = self.engine.get_sales_drops(drop_threshold_pct=-30.0)
        self.assertIsInstance(spikes, list)
        self.assertIsInstance(drops, list)
        for sp in spikes:
            self.assertGreaterEqual(sp["percentage_change"], 40.0)
        for d in drops:
            self.assertLessEqual(d["percentage_change"], -30.0)

    def test_safe_division_by_zero(self):
        # Verify engine does not crash when sales rate or stock is zero
        df = self.engine._get_daily_rates_and_stock(days_window=7)
        self.assertFalse(df["days_of_inventory"].isna().any())
        self.assertFalse(np.isinf(df["days_of_inventory"]).any())

class TestLocalRetrieval(unittest.TestCase):
    def setUp(self):
        self.retrieval = LocalRetrievalPipeline()

    def test_index_loaded(self):
        self.assertIsNotNone(self.retrieval.embeddings)
        self.assertGreater(len(self.retrieval.metadata), 0)

    def test_cosine_similarity_search(self):
        results = self.retrieval.search("running out of stock", top_k=3)
        self.assertEqual(len(results), 3)
        self.assertIn("similarity_score", results[0])
        self.assertGreater(results[0]["similarity_score"], 0)

class TestQueryEngineAndGrounding(unittest.TestCase):
    def setUp(self):
        self.qe = QueryEngine()

    def test_normal_demo_case_stockout(self):
        res = self.qe.process_query("What is running out?")
        self.assertEqual(res["intent"], "stockout")
        self.assertTrue(res["grounded"])
        self.assertGreater(len(res["evidence"]), 0)
        self.assertGreater(len(res["calculations"]), 0)
        self.assertIsNotNone(res["recommendation"])

    def test_difficult_demo_case_1_unsupported_cause(self):
        """User asks 'Why did sales decrease?'. Copilot must distinguish what data proves vs cannot prove."""
        res = self.qe.process_query("Why did sales decrease?")
        self.assertEqual(res["intent"], "unsupported_cause")
        self.assertTrue(res["grounded"])
        # Must explicitly acknowledge data limitations and decline to invent external causes
        answer_lower = res["answer"].lower()
        self.assertTrue(
            any(phrase in answer_lower for phrase in [
                "not contain", "insufficient", "does not", "do not", "cannot prove", "no external"
            ])
        )
        self.assertIn("limitations", res)
        self.assertGreater(len(res["limitations"]), 0)

    def test_difficult_demo_case_2_unsupported_forecast(self):
        """User asks 'What will our exact sales be six months from now?'. Must decline to guess."""
        res = self.qe.process_query("What will our exact sales be six months from now?")
        self.assertEqual(res["intent"], "unsupported_forecast")
        self.assertTrue(res["grounded"])
        answer_lower = res["answer"].lower()
        self.assertTrue("insufficient" in answer_lower or "does not contain" in answer_lower)
        self.assertIn("limitations", res)

    def test_overstock_question(self):
        res = self.qe.process_query("Which products are overstocked?")
        self.assertEqual(res["intent"], "overstock")
        self.assertTrue(res["grounded"])

    def test_slow_moving_question(self):
        res = self.qe.process_query("Which products are slow moving?")
        self.assertEqual(res["intent"], "slow_moving")
        self.assertTrue(res["grounded"])

    def test_store_comparison(self):
        res = self.qe.process_query("Compare Downtown Store and Mall Store.")
        self.assertEqual(res["intent"], "comparison")
        self.assertTrue(res["grounded"])

class TestFlaskEndpoints(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"RetailMind", response.data)

    def test_api_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "RetailMind AI")
        self.assertEqual(data["track_id"], "PS03")

    def test_api_dashboard(self):
        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("metrics", data)

    def test_api_attention(self):
        response = self.client.get("/api/attention")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("stockouts", data)
        self.assertIn("overstocked", data)

    def test_api_products(self):
        response = self.client.get("/api/products")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["count"], 30)

    def test_api_stores(self):
        response = self.client.get("/api/stores")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["count"], 3)

    def test_api_copilot_valid(self):
        payload = {"question": "What is running out?"}
        response = self.client.post("/api/copilot", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("answer", data)
        self.assertIn("evidence", data)
        self.assertIn("calculations", data)
        self.assertIn("recommendation", data)
        self.assertIn("assumptions", data)
        self.assertIn("limitations", data)
        self.assertTrue(data["grounded"])

    def test_api_copilot_empty(self):
        payload = {"question": ""}
        response = self.client.post("/api/copilot", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
