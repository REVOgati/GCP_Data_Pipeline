# Fresh Water Grocery E-Commerce Data Platform (GCP + BigQuery + dbt)

An end-to-end, production-grade analytics engineering platform built for **Fresh Water Grocery** . This platform ingests operational data across orders, catch-weight perishable products, rider dispatches, and inventory batches into **Google Cloud Platform (BigQuery)**, transforms raw data using **dbt (data build tool)** and **GoogleSQL**, enforces data quality assertions, and exposes governed models for **Power BI** and **AI Assistants (LLMs)**.

---

## 🏗️ Platform Architecture

```text
[ Synthetic Data Generator ] (Python)
          │
          ▼
[ BigQuery Raw Layer ] ──► `Fresh Water Grocery_raw` (Landing Tables)
          │
          ▼
[ dbt Transformation Layer ]
   ├── Staging Layer (`stg_`)   ──► Clean datatypes, standardized naming, deduplication
   ├── Intermediate Layer (`int_`) ──► Catch-weight logic, rider dispatch SLA metrics
   └── Marts Layer (`dim_`, `fact_`) ──► Governed Star Schemas (Partitioned & Clustered)
          │
          ├──► [ Business Intelligence ] ──► Power BI Dashboards
          └──► [ Governed AI Layer ]     ──► LLM Assistant (Semantic Metadata + SQL)
```

---

## 📂 Repository Structure

```text
GCP_Data_Pipeline/
├── scripts/
│   └── generate_and_ingest_Fresh Water Grocery.py  # Python script generating synthetic raw data
├── dbt_Fresh Water Grocery/                        # dbt Core / Dataform transformations
│   ├── models/
│   │   ├── staging/                       # Staging models (stg_orders, stg_products, etc.)
│   │   ├── intermediate/                  # Intermediate business logic
│   │   └── marts/                         # Production dimensional models (facts & dims)
│   ├── tests/                             # Custom SQL & generic data tests
│   └── dbt_project.yml
├── .gitignore                              # Ignores service accounts, .env, and venvs
├── requirements.txt                        # Pinned Python dependencies
└── README.md                               # Repository documentation
```

---

## 🚀 Phase 1: Environment Setup & Raw Data Ingestion (Completed)

This phase establishes the Google Cloud connection and ingests realistic e-grocery operational data into BigQuery.

### 1. Key Business Domains Modeled
* **Orders & Slots**: Captures express delivery (45-minute SLA) vs. scheduled delivery (2-hour time windows).
* **Catch-Weight Items**: Handles fresh produce and meats sold by weight variance (e.g., ordered 1.0 kg, delivered 0.96 kg).
* **Perishable Inventory**: Tracks batch manufacture dates, expiry dates, and spoilage/waste flags.
* **Delivery Performance**: Logs rider dispatches, arrival times, customer handoffs, and SLA compliance.

### 2. Prerequisites
* **Python 3.11+**
* **Google Cloud Platform (GCP)** account with an active BigQuery Sandbox or Project.
* **Service Account JSON Key** with `BigQuery Admin` (or Data Editor/Job User) permissions.

### 3. Local Installation & Ingestion Execution

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/GCP_Data_Pipeline.git
cd GCP_Data_Pipeline

# 2. Create and activate virtual environment
python -m venv .myvenv
source .myvenv/Scripts/activate   # On Windows Git Bash

# 3. Install required dependencies
pip install google-cloud-bigquery "numpy<2.0.0" "pandas<3.0.0" "pyarrow<16.0.0" db-dtypes google-auth

# 4. Save environment specs
pip freeze > requirements.txt

# 5. Place your service account key in the project root as `Fresh Water Grocery-key.json`

# 6. Execute raw data generation and BigQuery load
python scripts/generate_and_ingest_Fresh Water Grocery.py
```

### 4. Raw Dataset Tables in BigQuery (`Fresh Water Grocery_raw`)
* `raw_products`: 15 SKU lines across perishable, catch-weight, and packaged categories.
* `raw_orders`: 600 orders covering express vs. scheduled windows.
* `raw_order_items`: Line-item order breakdown including unit prices and catch-weight delivered amounts.
* `raw_deliveries`: Timestamps, rider IDs, distances, and delivery statuses.
* `raw_inventory`: Batch-level warehouse stock tracking and expiry statuses.

---

## 📦 Phase 2: Transformations & Data Modeling (dbt / Dataform)

### 1. Medallion Architecture Strategy

| Layer | Dataset / Schema | Objective | Key Operations |
| :--- | :--- | :--- | :--- |
| **Staging** | `Fresh Water Grocery_staging` | Standardize Raw Sources | Cast timestamps (`TIMESTAMP`), rename columns (`snake_case`), handle `NULL` values. |
| **Intermediate** | `Fresh Water Grocery_intermediate` | Business Logic Engine | Calculate actual line totals for catch-weight items; compute delivery durations via `TIMESTAMP_DIFF`. |
| **Marts** | `Fresh Water Grocery_analytics` | Production Reporting | Dimensional Star Schema (`fact_orders`, `fact_inventory`, `dim_customers`, `dim_products`). |

### 2. Dimensional Model Specifications

#### Fact Table: `fact_orders`
* **Granularity**: 1 row per order.
* **Partitioning**: Partitioned by `order_date` (`DAY`) in BigQuery for cost optimization.
* **Clustering**: Clustered by `delivery_slot_type` and `delivery_status`.
* **Key Metrics**: `gross_revenue_kes`, `delivery_fee_kes`, `is_on_time_sla`, `delivery_duration_minutes`.

#### Fact Table: `fact_inventory_daily`
* **Granularity**: 1 row per product batch per day.
* **Key Metrics**: `quantity_on_hand`, `days_to_expiry`, `is_expired_flag`, `potential_spoilage_value_kes`.

### 3. Data Quality & Assertion Framework
* **Primary Key Integrity**: Unique and Not Null tests on surrogate/natural keys (`order_id`, `product_id`).
* **Accepted Values**: `delivery_status` validated against `['delivered', 'cancelled', 'pending', 'in_transit']`.
* **Custom Assertions**: Ensure `customer_delivered_time >= warehouse_dispatch_time`.

---

## 📊 Phase 3: BI Dashboards & AI Assistant Integration

### 1. Power BI Connection
* **Connector**: Native Google BigQuery connector.
* **Storage Mode**: DirectQuery or Import on top of `Fresh Water Grocery_analytics` dimensional models.
* **Core Measures (DAX)**:
  * **OTIF SLA %**: `DIVIDE(CALCULATE(COUNT(fact_orders[order_id]), fact_orders[is_on_time_sla] = TRUE), COUNT(fact_orders[order_id]))`
  * **Net Revenue (KES)**: `SUM(fact_orders[net_revenue_kes])`

### 2. Governed LLM Assistant Integration
* Exposes curated `schema_metadata.json` generated from dbt YAML documentation to an **LLM**.
* Enables natural-language querying for Fresh Water Grocery business users (e.g., *"What was our express delivery SLA rate in Nairobi last week?"*) while preventing SQL injection and hallucinations through governed metric definitions.

---

## 🛠️ Execution Checklist for Contributor

- [x] GCP Project & Service Account Configured
- [x] Python Synthetic Generator Created
- [x] Raw Landing Tables Ingested into BigQuery (`Fresh Water Grocery_raw`)
- [ ] Initialize dbt Project (`dbt init dbt_Fresh Water Grocery`)
- [ ] Build Staging SQL Models (`stg_orders`, `stg_products`, `stg_deliveries`)
- [ ] Build Intermediate & Mart SQL Models (`fact_orders`, `dim_products`)
- [ ] Add Data Quality Tests in `schema.yml`
- [ ] Run `dbt test` & `dbt docs generate`
- [ ] Connect Power BI Dashboard & Configure Governed LLM Utility