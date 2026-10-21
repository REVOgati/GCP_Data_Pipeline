from datetime import datetime, timedelta
import os
import random
from google.cloud import bigquery
from google.oauth2 import service_account
import numpy as np
import pandas as pd

# ==============================================================================
# 1. CONFIGURATION & AUTHENTICATION SETUP
# ==============================================================================
SERVICE_ACCOUNT_FILE = "fwg-key.json"  # Path Service Account JSON key
GCP_PROJECT_ID = "fresh-water-grocery-company"  # GCP Project ID
DATASET_ID = "fwg_raw"  # Raw landing dataset created in BigQuery

# Number of records to generate for simulation
NUM_PRODUCTS = 30
NUM_ORDERS = 600
NUM_CUSTOMERS = 120

# Initialize BigQuery Client using Service Account Credentials
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE
)
client = bigquery.Client(credentials=credentials, project=GCP_PROJECT_ID)


# ==============================================================================
# 2. DATA GENERATION LOGIC (fwg E-GROCERY SIMULATION)
# ==============================================================================

# A. PRODUCTS TABLE
# Covers perishable goods, catch-weight items (e.g. fresh meat/vegetables sold by weight),
# and standard packaged shelf goods.
product_categories = {
    "Fresh Produce": {
        "perishable": True,
        "catch_weight": True,
        "avg_price": 250,
        "shelf_life": 7,
    },
    "Dairy & Eggs": {
        "perishable": True,
        "catch_weight": False,
        "avg_price": 180,
        "shelf_life": 14,
    },
    "Meat & Seafood": {
        "perishable": True,
        "catch_weight": True,
        "avg_price": 850,
        "shelf_life": 5,
    },
    "Bakery": {
        "perishable": True,
        "catch_weight": False,
        "avg_price": 220,
        "shelf_life": 4,
    },
    "Pantry & Groceries": {
        "perishable": False,
        "catch_weight": False,
        "avg_price": 400,
        "shelf_life": 180,
    },
    "Beverages": {
        "perishable": False,
        "catch_weight": False,
        "avg_price": 300,
        "shelf_life": 90,
    },
}

products_list = []
product_names = [
    ("Fresh Organic Spinach 250g", "Fresh Produce"),
    ("Hass Avocados (Pack of 3)", "Fresh Produce"),
    ("Red Tomatoes (1kg)", "Fresh Produce"),
    ("Organic Bananas (1kg)", "Fresh Produce"),
    ("Whole Chicken (Approx 1.2kg)", "Meat & Seafood"),
    ("Prime Beef Steak (500g)", "Meat & Seafood"),
    ("Fresh Tilapia Fillet (400g)", "Meat & Seafood"),
    ("Whole Fresh Milk 1L", "Dairy & Eggs"),
    ("Greek Yogurt Plain 500g", "Dairy & Eggs"),
    ("Free Range Eggs (12 Pack)", "Dairy & Eggs"),
    ("Artisanal Sourdough Loaf", "Bakery"),
    ("Whole Wheat Bread 400g", "Bakery"),
    ("Extra Virgin Olive Oil 500ml", "Pantry & Groceries"),
    ("Organic White Rice 2kg", "Pantry & Groceries"),
    ("Fresh Cold-Pressed Orange Juice 1L", "Beverages"),
]

for i, (p_name, category) in enumerate(product_names, start=101):
    meta = product_categories[category]
    cost = round(meta["avg_price"] * random.uniform(0.65, 0.78), 2)
    price = round(meta["avg_price"] * random.uniform(0.95, 1.15), 2)

    products_list.append({
        "product_id": f"PRD-{i}",
        "product_name": p_name,
        "category": category,
        "unit_cost_kes": cost,
        "unit_price_kes": price,
        "is_perishable": meta["perishable"],
        "is_catch_weight": meta["catch_weight"],
        "shelf_life_days": meta["shelf_life"],
    })

df_products = pd.DataFrame(products_list)


# B. ORDERS TABLE
# Models express fulfillment (45 min SLA) vs scheduled deliveries (2-hour delivery windows)
start_date = datetime.now() - timedelta(days=30)
orders_list = []
order_statuses = [
    "delivered",
    "delivered",
    "delivered",
    "delivered",
    "delivered",
    "cancelled",
]
slot_types = ["express", "scheduled"]

for i in range(1001, 1001 + NUM_ORDERS):
    order_time = start_date + timedelta(
        days=random.randint(0, 29),
        hours=random.randint(7, 20),
        minutes=random.randint(0, 59),
    )
    customer_id = f"CUST-{random.randint(1000, 1000 + NUM_CUSTOMERS)}"
    slot_type = random.choice(slot_types)
    status = random.choice(order_statuses)

    if slot_type == "scheduled":
        # Scheduled window starts 2 to 6 hours after order time
        sched_start = order_time.replace(
            minute=0, second=0
        ) + timedelta(hours=random.randint(2, 6))
        sched_end = sched_start + timedelta(hours=2)
    else:
        # Express delivery target: within 45 minutes
        sched_start = order_time
        sched_end = order_time + timedelta(minutes=45)

    delivery_fee = 150.00 if slot_type == "express" else 250.00

    orders_list.append({
        "order_id": f"ORD-{i}",
        "customer_id": customer_id,
        "order_timestamp": order_time,
        "delivery_slot_type": slot_type,
        "scheduled_delivery_start": sched_start,
        "scheduled_delivery_end": sched_end,
        "delivery_status": status,
        "payment_status": (
            "paid"
            if status == "delivered"
            else random.choice(["refunded", "failed"])
        ),
        "delivery_fee_kes": delivery_fee,
    })

df_orders = pd.DataFrame(orders_list)


# C. ORDER ITEMS TABLE
# Captures individual line items, including catch-weight adjustments
# (e.g., customer orders 1.0kg beef, actual picking weight was 0.96kg)
order_items_list = []
item_id_counter = 50001

for _, order in df_orders.iterrows():
    # Pick 1 to 5 random products per order
    num_items = random.randint(1, 5)
    selected_products = df_products.sample(n=num_items)

    for _, product in selected_products.iterrows():
        ordered_qty = float(random.randint(1, 3))
        unit_price = product["unit_price_kes"]

        # Simulate catch-weight variance (e.g. actual delivered weight for fresh produce/meat)
        if product["is_catch_weight"]:
            actual_weight = round(ordered_qty * random.uniform(0.88, 1.08), 2)
            line_total = round(actual_weight * unit_price, 2)
        else:
            actual_weight = ordered_qty
            line_total = round(ordered_qty * unit_price, 2)

        order_items_list.append({
            "order_item_id": f"ITEM-{item_id_counter}",
            "order_id": order["order_id"],
            "product_id": product["product_id"],
            "ordered_quantity": ordered_qty,
            "actual_delivered_weight_kg": actual_weight,
            "unit_price_kes": unit_price,
            "line_total_kes": line_total,
        })
        item_id_counter += 1

df_order_items = pd.DataFrame(order_items_list)


# D. DELIVERIES TABLE
# Tracks rider dispatches, timestamps, distance, and SLA compliance metrics
deliveries_list = []
riders = [f"RIDER-00{k}" for k in range(1, 9)]

for _, order in df_orders.iterrows():
    if order["delivery_status"] == "delivered":
        dispatch_time = order["order_timestamp"] + timedelta(
            minutes=random.randint(5, 15)
        )
        arrival_time = dispatch_time + timedelta(
            minutes=random.randint(10, 25)
        )

        # Simulate SLA compliance: 85% delivered on time, 15% delayed by Nairobi traffic/weather
        if random.random() < 0.85:
            delivered_time = order["scheduled_delivery_start"] + timedelta(
                minutes=random.randint(10, 40)
            )
        else:
            delivered_time = order["scheduled_delivery_end"] + timedelta(
                minutes=random.randint(15, 50)
            )

        deliveries_list.append({
            "delivery_id": f"DEL-{order['order_id'].split('-')[1]}",
            "order_id": order["order_id"],
            "rider_id": random.choice(riders),
            "warehouse_dispatch_time": dispatch_time,
            "rider_arrival_time": arrival_time,
            "customer_delivered_time": delivered_time,
            "delivery_distance_km": round(random.uniform(1.5, 14.0), 2),
            "cancellation_reason": None,
        })
    elif order["delivery_status"] == "cancelled":
        deliveries_list.append({
            "delivery_id": f"DEL-{order['order_id'].split('-')[1]}",
            "order_id": order["order_id"],
            "rider_id": None,
            "warehouse_dispatch_time": None,
            "rider_arrival_time": None,
            "customer_delivered_time": None,
            "delivery_distance_km": None,
            "cancellation_reason": random.choice([
                "Customer cancelled",
                "Item out of stock",
                "Rider unavailable",
            ]),
        })

df_deliveries = pd.DataFrame(deliveries_list)


# E. INVENTORY TABLE
# Batch-level stock tracking for freshness, spoilage, and expiry monitoring
inventory_list = []
batch_counter = 8000

for _, product in df_products.iterrows():
    # Create 2 active batches per product in stock
    for _ in range(2):
        mfg_date = datetime.now() - timedelta(
            days=random.randint(1, product["shelf_life_days"])
        )
        exp_date = mfg_date + timedelta(days=product["shelf_life_days"])
        qty_on_hand = random.randint(10, 150)

        # Flag stock as waste if past expiry date
        is_waste = exp_date < datetime.now()

        inventory_list.append({
            "inventory_id": f"INV-{batch_counter}",
            "product_id": product["product_id"],
            "warehouse_id": "WH-NAIROBI-MAIN",
            "batch_number": f"BATCH-2026-{batch_counter}",
            "manufacture_date": mfg_date.date(),
            "expiry_date": exp_date.date(),
            "stock_quantity_units": qty_on_hand,
            "is_waste_flag": is_waste,
        })
        batch_counter += 1

df_inventory = pd.DataFrame(inventory_list)


# ==============================================================================
# 3. BIGQUERY INGESTION LOGIC
# ==============================================================================

tables_to_load = {
    "raw_products": df_products,
    "raw_orders": df_orders,
    "raw_order_items": df_order_items,
    "raw_deliveries": df_deliveries,
    "raw_inventory": df_inventory,
}

print(f"--- Starting Ingestion to BigQuery Dataset: {DATASET_ID} ---")

# Configure load job to overwrite existing tables during raw ingestion setup
job_config = bigquery.LoadJobConfig(
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    autodetect=True,  # Automatically detect schema from DataFrame datatypes
)

for table_name, df in tables_to_load.items():
    table_ref = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    try:
        job = client.load_table_from_dataframe(
            df, table_ref, job_config=job_config
        )
        job.result()  # Wait for BigQuery load job to finish execution
        print(f"✓ Successfully loaded {len(df)} rows into {table_name}")
    except Exception as e:
        print(f"✗ Failed to load {table_name}: {str(e)}")

print("--- BigQuery Raw Data Ingestion Complete! ---")