"""
Data loader module for RetailMind AI.
Loads, validates, and caches retail datasets (stores, products, sales, inventory).
"""

import os
import pandas as pd
from typing import Dict, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

class DataLoader:
    _instance: Optional['DataLoader'] = None

    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self.stores_df: Optional[pd.DataFrame] = None
        self.products_df: Optional[pd.DataFrame] = None
        self.sales_df: Optional[pd.DataFrame] = None
        self.inventory_df: Optional[pd.DataFrame] = None
        self.load_all()

    @classmethod
    def get_instance(cls, data_dir: str = DATA_DIR) -> 'DataLoader':
        if cls._instance is None:
            cls._instance = cls(data_dir)
        return cls._instance

    def load_all(self):
        """Loads and parses all 4 CSV files into memory with appropriate types."""
        stores_path = os.path.join(self.data_dir, "stores.csv")
        products_path = os.path.join(self.data_dir, "products.csv")
        sales_path = os.path.join(self.data_dir, "sales.csv")
        inventory_path = os.path.join(self.data_dir, "inventory.csv")

        if not os.path.exists(stores_path):
            raise FileNotFoundError(f"Stores data missing at {stores_path}")
        if not os.path.exists(products_path):
            raise FileNotFoundError(f"Products data missing at {products_path}")
        if not os.path.exists(sales_path):
            raise FileNotFoundError(f"Sales data missing at {sales_path}")
        if not os.path.exists(inventory_path):
            raise FileNotFoundError(f"Inventory data missing at {inventory_path}")

        self.stores_df = pd.read_csv(stores_path)
        self.products_df = pd.read_csv(products_path)
        self.sales_df = pd.read_csv(sales_path)
        self.inventory_df = pd.read_csv(inventory_path)

        # Validate required columns defensively
        required_product_cols = {"product_id", "product_name", "category", "selling_price", "cost_price", "reorder_level", "supplier"}
        required_store_cols = {"store_id", "store_name", "location"}
        required_sales_cols = {"date", "store_id", "product_id", "quantity_sold", "revenue"}
        required_inv_cols = {"date", "store_id", "product_id", "stock_quantity"}

        if not required_product_cols.issubset(self.products_df.columns):
            missing = required_product_cols - set(self.products_df.columns)
            raise ValueError(f"products.csv missing required columns: {missing}")
        if not required_store_cols.issubset(self.stores_df.columns):
            missing = required_store_cols - set(self.stores_df.columns)
            raise ValueError(f"stores.csv missing required columns: {missing}")
        if not required_sales_cols.issubset(self.sales_df.columns):
            missing = required_sales_cols - set(self.sales_df.columns)
            raise ValueError(f"sales.csv missing required columns: {missing}")
        if not required_inv_cols.issubset(self.inventory_df.columns):
            missing = required_inv_cols - set(self.inventory_df.columns)
            raise ValueError(f"inventory.csv missing required columns: {missing}")

        # Convert date columns to datetime for fast time-series queries
        self.sales_df["date"] = pd.to_datetime(self.sales_df["date"])
        self.inventory_df["date"] = pd.to_datetime(self.inventory_df["date"])

        # Defensive numeric conversions
        self.products_df["selling_price"] = pd.to_numeric(self.products_df["selling_price"], errors="coerce").fillna(0.0)
        self.products_df["cost_price"] = pd.to_numeric(self.products_df["cost_price"], errors="coerce").fillna(0.0)
        self.products_df["reorder_level"] = pd.to_numeric(self.products_df["reorder_level"], errors="coerce").fillna(0).astype(int)

        self.sales_df["quantity_sold"] = pd.to_numeric(self.sales_df["quantity_sold"], errors="coerce").fillna(0).astype(int)
        self.sales_df["revenue"] = pd.to_numeric(self.sales_df["revenue"], errors="coerce").fillna(0.0)

        self.inventory_df["stock_quantity"] = pd.to_numeric(self.inventory_df["stock_quantity"], errors="coerce").fillna(0).astype(int)

        # Create quick lookup dicts
        self.store_map = self.stores_df.set_index("store_id").to_dict(orient="index")
        self.product_map = self.products_df.set_index("product_id").to_dict(orient="index")

    def get_stores(self) -> pd.DataFrame:
        return self.stores_df.copy()

    def get_products(self) -> pd.DataFrame:
        return self.products_df.copy()

    def get_sales(self) -> pd.DataFrame:
        return self.sales_df.copy()

    def get_inventory(self) -> pd.DataFrame:
        return self.inventory_df.copy()

    def get_latest_date(self) -> pd.Timestamp:
        return self.sales_df["date"].max()

    def get_date_range(self) -> tuple[pd.Timestamp, pd.Timestamp]:
        return self.sales_df["date"].min(), self.sales_df["date"].max()
