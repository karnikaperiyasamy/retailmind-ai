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

        # Convert date columns to datetime for fast time-series queries
        self.sales_df["date"] = pd.to_datetime(self.sales_df["date"])
        self.inventory_df["date"] = pd.to_datetime(self.inventory_df["date"])

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
