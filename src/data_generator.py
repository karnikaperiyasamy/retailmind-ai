"""
Synthetic Retail Data Generator for RetailMind AI
Generates realistic sales and inventory history spanning 92 days (2026-06-01 to 2026-08-31)
across 3 stores and 32 products in 6 categories.
Includes targeted scenarios: stock-out risks, overstocked items, sales spikes, sales drops, and slow movers.
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 1. Stores Data
STORES = [
    {"store_id": "S001", "store_name": "Downtown Store", "location": "Metro Central Hub, 5th Avenue"},
    {"store_id": "S002", "store_name": "Mall Store", "location": "Westside Galleria, Level 2"},
    {"store_id": "S003", "store_name": "Airport Store", "location": "International Terminal 2 Departures"}
]

# 2. Products Data (32 products across 6 categories)
PRODUCTS = [
    # Electronics
    {"product_id": "P001", "product_name": "UltraFast USB-C Cable 2m", "category": "Electronics", "selling_price": 499.0, "cost_price": 180.0, "reorder_level": 30, "supplier": "AnkerTech Logistics"},
    {"product_id": "P002", "product_name": "Compact Power Bank 10000mAh", "category": "Electronics", "selling_price": 1499.0, "cost_price": 750.0, "reorder_level": 20, "supplier": "VoltCorp Hardware"},
    {"product_id": "P003", "product_name": "Noise Cancelling Headphones", "category": "Electronics", "selling_price": 4999.0, "cost_price": 2800.0, "reorder_level": 15, "supplier": "AuraSound Ltd"},
    {"product_id": "P004", "product_name": "Bluetooth Travel Speaker", "category": "Electronics", "selling_price": 2499.0, "cost_price": 1200.0, "reorder_level": 18, "supplier": "AuraSound Ltd"},
    {"product_id": "P014", "product_name": "Wireless Ergonomic Mouse", "category": "Electronics", "selling_price": 1299.0, "cost_price": 600.0, "reorder_level": 25, "supplier": "LogiGear Supplies"},
    {"product_id": "P015", "product_name": "Mechanical Keyboard RGB", "category": "Electronics", "selling_price": 3899.0, "cost_price": 2100.0, "reorder_level": 12, "supplier": "LogiGear Supplies"},

    # Beverages
    {"product_id": "P005", "product_name": "Whole Bean Dark Roast 500g", "category": "Beverages", "selling_price": 650.0, "cost_price": 320.0, "reorder_level": 25, "supplier": "BlueTokai Coffee Estates"},
    {"product_id": "P006", "product_name": "Organic Matcha Green Tea 100g", "category": "Beverages", "selling_price": 850.0, "cost_price": 450.0, "reorder_level": 20, "supplier": "Kyoto Pure Imports"},
    {"product_id": "P007", "product_name": "Sparkling Spring Water 500ml", "category": "Beverages", "selling_price": 90.0, "cost_price": 35.0, "reorder_level": 50, "supplier": "Himalayan Waters Co"},
    {"product_id": "P008", "product_name": "Organic Cold Brew 1L", "category": "Beverages", "selling_price": 340.0, "cost_price": 160.0, "reorder_level": 60, "supplier": "BlueTokai Coffee Estates"},
    {"product_id": "P016", "product_name": "Artisan Kombucha Ginger 330ml", "category": "Beverages", "selling_price": 180.0, "cost_price": 85.0, "reorder_level": 30, "supplier": "FermentCo Botanicals"},

    # Grocery
    {"product_id": "P009", "product_name": "Roasted Almonds 250g", "category": "Grocery", "selling_price": 399.0, "cost_price": 240.0, "reorder_level": 30, "supplier": "NutriHarvest Farms"},
    {"product_id": "P010", "product_name": "Organic Wildflower Honey 500g", "category": "Grocery", "selling_price": 520.0, "cost_price": 290.0, "reorder_level": 25, "supplier": "BeeNatural Apiculture"},
    {"product_id": "P011", "product_name": "Quinoa Crunch Granola 400g", "category": "Grocery", "selling_price": 450.0, "cost_price": 230.0, "reorder_level": 25, "supplier": "NutriHarvest Farms"},
    {"product_id": "P012", "product_name": "Dark Chocolate 72% Single Origin", "category": "Grocery", "selling_price": 280.0, "cost_price": 130.0, "reorder_level": 40, "supplier": "CacaoCraft Confections"},
    {"product_id": "P017", "product_name": "Extra Virgin Olive Oil 500ml", "category": "Grocery", "selling_price": 890.0, "cost_price": 520.0, "reorder_level": 20, "supplier": "Mediterranean Gold"},

    # Personal Care
    {"product_id": "P013", "product_name": "Natural Charcoal Face Wash 150ml", "category": "Personal Care", "selling_price": 350.0, "cost_price": 150.0, "reorder_level": 30, "supplier": "EarthPure Labs"},
    {"product_id": "P018", "product_name": "Hydrating Sunscreen SPF 50 100ml", "category": "Personal Care", "selling_price": 550.0, "cost_price": 260.0, "reorder_level": 25, "supplier": "Dermacare Pharma"},
    {"product_id": "P020", "product_name": "Botanical Shampoo Bar 100g", "category": "Personal Care", "selling_price": 299.0, "cost_price": 120.0, "reorder_level": 20, "supplier": "EarthPure Labs"},
    {"product_id": "P021", "product_name": "Hand Sanitizer Spray 60ml", "category": "Personal Care", "selling_price": 99.0, "cost_price": 30.0, "reorder_level": 60, "supplier": "Dermacare Pharma"},
    {"product_id": "P022", "product_name": "Organic Lip Balm Mint 15g", "category": "Personal Care", "selling_price": 160.0, "cost_price": 60.0, "reorder_level": 35, "supplier": "EarthPure Labs"},

    # Home
    {"product_id": "P019", "product_name": "Artisan Ceramic Mug 350ml", "category": "Home", "selling_price": 450.0, "cost_price": 180.0, "reorder_level": 25, "supplier": "ClayCraft Studios"},
    {"product_id": "P023", "product_name": "Aromatherapy Soy Candle Lavender", "category": "Home", "selling_price": 599.0, "cost_price": 240.0, "reorder_level": 20, "supplier": "Lumina Scents"},
    {"product_id": "P024", "product_name": "Stainless Steel Water Bottle 750ml", "category": "Home", "selling_price": 799.0, "cost_price": 380.0, "reorder_level": 25, "supplier": "HydroSteel Living"},
    {"product_id": "P025", "product_name": "Linen Hand Towel Set of 2", "category": "Home", "selling_price": 699.0, "cost_price": 310.0, "reorder_level": 20, "supplier": "ComfortFabrics Co"},
    {"product_id": "P026", "product_name": "Bamboo Desk Organizer", "category": "Home", "selling_price": 899.0, "cost_price": 410.0, "reorder_level": 15, "supplier": "EcoDesk Solutions"},

    # Stationery
    {"product_id": "P027", "product_name": "Premium Fountain Pen Set", "category": "Stationery", "selling_price": 1899.0, "cost_price": 950.0, "reorder_level": 15, "supplier": "MontScribe Writing"},
    {"product_id": "P028", "product_name": "Hardcover Dotted Journal 200p", "category": "Stationery", "selling_price": 499.0, "cost_price": 200.0, "reorder_level": 30, "supplier": "PaperMill Goods"},
    {"product_id": "P029", "product_name": "Gel Ink Pens Pack of 5", "category": "Stationery", "selling_price": 250.0, "cost_price": 90.0, "reorder_level": 40, "supplier": "PaperMill Goods"},
    {"product_id": "P030", "product_name": "Desk Sticky Notes Pastel Pack", "category": "Stationery", "selling_price": 149.0, "cost_price": 45.0, "reorder_level": 50, "supplier": "OfficePrime Supplies"},
    {"product_id": "P031", "product_name": "Dual-Tip Pastel Highlighters (6pk)", "category": "Stationery", "selling_price": 320.0, "cost_price": 120.0, "reorder_level": 30, "supplier": "OfficePrime Supplies"},
    {"product_id": "P032", "product_name": "Leather Cardholder Wallet", "category": "Stationery", "selling_price": 850.0, "cost_price": 380.0, "reorder_level": 20, "supplier": "MontScribe Writing"}
]

def generate_datasets():
    start_date = datetime(2026, 6, 1)
    num_days = 92  # June 1 to August 31, 2026
    date_list = [start_date + timedelta(days=i) for i in range(num_days)]

    # DataFrames for stores and products
    df_stores = pd.DataFrame(STORES)
    df_products = pd.DataFrame(PRODUCTS)

    df_stores.to_csv(os.path.join(DATA_DIR, "stores.csv"), index=False)
    df_products.to_csv(os.path.join(DATA_DIR, "products.csv"), index=False)

    sales_records = []
    inventory_records = []

    # Initialize current stock levels for day 0 (June 1)
    # Target stock setup for each store and product
    current_inventory = {}
    for store in STORES:
        s_id = store["store_id"]
        current_inventory[s_id] = {}
        for prod in PRODUCTS:
            p_id = prod["product_id"]
            # Default healthy stock between 40 and 120
            base_stock = random.randint(50, 110)
            current_inventory[s_id][p_id] = base_stock

    # Set up initial intentional scenarios for specific store-product pairs:
    # 1. P014 (Wireless Mouse) at S002: starts normal, in late August demand stays up and stock gets depleted to 12
    # 2. P008 (Organic Cold Brew 1L) at S001: massive overstock received mid-August, stock stays around 420
    # 3. P003 (Noise Cancelling Headphones) at S001: spike in last 7 days (August 25-31)
    # 4. P019 (Artisan Ceramic Mug) at S002: drop in last 7 days
    # 5. P027 (Premium Fountain Pen) at S003: very slow moving (rare sales, stock 35)

    current_inventory["S003"]["P027"] = 35
    current_inventory["S001"]["P008"] = 430

    for day_idx, current_date in enumerate(date_list):
        date_str = current_date.strftime("%Y-%m-%d")
        is_weekend = current_date.weekday() >= 5
        is_recent_7_days = (num_days - day_idx) <= 7

        for store in STORES:
            s_id = store["store_id"]
            # Store traffic factor
            store_factor = 1.25 if s_id == "S001" else (1.0 if s_id == "S002" else 0.85)

            for prod in PRODUCTS:
                p_id = prod["product_id"]
                price = prod["selling_price"]
                reorder_lvl = prod["reorder_level"]

                # Base sales rate based on category and price
                if prod["category"] in ["Beverages", "Grocery"]:
                    base_rate = 5.0
                elif prod["category"] == "Personal Care":
                    base_rate = 3.5
                elif prod["category"] == "Stationery":
                    base_rate = 2.8
                elif prod["category"] == "Home":
                    base_rate = 2.5
                else: # Electronics
                    base_rate = 1.8

                # Weekend boost
                if is_weekend:
                    base_rate *= 1.35

                rate = base_rate * store_factor

                # --- Intentional Scenarios Injection ---
                # Scenario 1: P014 at S002 (Stockout risk)
                if s_id == "S002" and p_id == "P014":
                    rate = 3.2  # consistent 3.2 units/day
                    # Force inventory depletion in final week
                    if is_recent_7_days:
                        rate = 3.2
                    # Suppress replenishment in August

                # Scenario 2: P008 at S001 (Overstock)
                elif s_id == "S001" and p_id == "P008":
                    rate = 4.5  # 4.5 units/day

                # Scenario 3: P003 at S001 (Sales Spike)
                elif s_id == "S001" and p_id == "P003":
                    if is_recent_7_days:
                        rate = 8.0  # Spikes to ~8 units/day (recent avg ~8 vs baseline ~4.3)
                    else:
                        rate = 4.3

                # Scenario 4: P019 at S002 (Sales Drop)
                elif s_id == "S002" and p_id == "P019":
                    if is_recent_7_days:
                        rate = 1.4  # Drops from baseline 3.8 to 1.4 (-63%)
                    else:
                        rate = 3.8

                # Scenario 5: P027 at S003 (Slow Moving)
                elif s_id == "S003" and p_id == "P027":
                    # Only sold 2 units in total 90 days
                    rate = 0.05 if day_idx in [20, 55] else 0.0

                # Sample quantity sold (Poisson or clamped normal)
                if s_id == "S003" and p_id == "P027":
                    qty_sold = 1 if day_idx in [20, 55] else 0
                else:
                    qty_sold = int(np.random.poisson(rate))
                    qty_sold = max(0, qty_sold)

                # Cap quantity sold by available stock
                stock_avail = current_inventory[s_id][p_id]
                qty_sold = min(qty_sold, stock_avail)

                revenue = round(qty_sold * price, 2)

                # Record sales
                sales_records.append({
                    "date": date_str,
                    "store_id": s_id,
                    "product_id": p_id,
                    "quantity_sold": qty_sold,
                    "revenue": revenue
                })

                # Update stock
                new_stock = stock_avail - qty_sold

                # Normal replenishment logic (except for specific scenarios)
                if s_id == "S002" and p_id == "P014":
                    # For stockout demo, don't replenish in late August so stock ends exactly around 12
                    if day_idx == 85:
                        # set stock so that on day 91 it lands at 12
                        new_stock = 31
                elif s_id == "S001" and p_id == "P008":
                    # For overstock demo, keep high stock
                    if day_idx == 70:
                        new_stock = 480
                elif s_id == "S003" and p_id == "P027":
                    # Never replenish
                    pass
                else:
                    # Regular replenishment when below reorder level
                    if new_stock <= reorder_lvl and day_idx < 86:
                        # Restock
                        new_stock += random.randint(40, 70)

                current_inventory[s_id][p_id] = max(0, new_stock)

                # Record daily inventory snapshot
                inventory_records.append({
                    "date": date_str,
                    "store_id": s_id,
                    "product_id": p_id,
                    "stock_quantity": current_inventory[s_id][p_id]
                })

    # Ensure precise final stock numbers for the exact demo test cases on the final day (2026-08-31)
    final_inv_df = pd.DataFrame(inventory_records)
    # Fix the final day stock specifically for P014 at S002 to be exactly 12
    mask_stockout = (final_inv_df["date"] == "2026-08-31") & (final_inv_df["store_id"] == "S002") & (final_inv_df["product_id"] == "P014")
    final_inv_df.loc[mask_stockout, "stock_quantity"] = 12

    # Fix P008 at S001 on final day to be 420
    mask_overstock = (final_inv_df["date"] == "2026-08-31") & (final_inv_df["store_id"] == "S001") & (final_inv_df["product_id"] == "P008")
    final_inv_df.loc[mask_overstock, "stock_quantity"] = 420

    # Fix P027 at S003 on final day to be 35
    mask_slow = (final_inv_df["date"] == "2026-08-31") & (final_inv_df["store_id"] == "S003") & (final_inv_df["product_id"] == "P027")
    final_inv_df.loc[mask_slow, "stock_quantity"] = 35

    df_sales = pd.DataFrame(sales_records)
    df_sales.to_csv(os.path.join(DATA_DIR, "sales.csv"), index=False)
    final_inv_df.to_csv(os.path.join(DATA_DIR, "inventory.csv"), index=False)

    print(f"Generated {len(df_stores)} stores, {len(df_products)} products.")
    print(f"Generated {len(df_sales)} sales rows and {len(final_inv_df)} inventory rows.")
    print(f"Data written to {DATA_DIR}")

if __name__ == "__main__":
    generate_datasets()
