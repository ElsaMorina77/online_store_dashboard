# Online Store Executive Dashboard

An interactive Streamlit dashboard for analyzing online retail performance from a manager and executive perspective. The app loads transaction data from a CSV, Excel file, or direct file URL, cleans and prepares the dataset, and then presents KPI cards, sales analytics, customer insights, product performance, and cancellation analysis.

## Project Goal

The purpose of this project is to turn raw store transaction data into clear business insight. Instead of showing charts just for the sake of visualization, the dashboard is designed to answer practical management questions such as:

- Are revenue and order volume growing together?
- Which products drive the most business value?
- Which markets are performing best?
- What does the customer mix look like?
- Are repeat customers strong enough?
- Where are cancellations hurting performance?

## Why This Project Matters

Retail datasets are often large, messy, and difficult to interpret quickly. Managers usually do not want raw rows of transactions. They want a fast business summary, high-value KPIs, and a small number of focused analytics that help them make decisions.

This dashboard was built around that idea:

- preprocess the data once
- cache repeated calculations for speed
- group related analytics into preset views
- surface business metrics before technical detail

## Main Features

### 1. Flexible Data Input

The dashboard can load data from:

- uploaded CSV files
- uploaded Excel files
- direct CSV or Excel URLs

It also supports the `Online Retail II` workbook structure by combining the expected yearly sheets when they exist.

### 2. Data Cleaning and Preparation

Before analysis, the app:

- removes duplicate rows
- removes invalid prices
- removes invalid quantities
- excludes non-product stock codes
- prepares revenue and monthly fields
- keeps cancellation-related data available for separate analysis

This makes the final dashboard more reliable and easier to explain.

### 3. KPI Dashboard

The first section gives an executive summary of core business performance:

- Total Revenue
- Total Orders
- Customers
- Average Order Value

The KPI cards also compare the current selection with the previous period when possible.

### 4. Sales Analytics Explorer

Instead of forcing the user to load every graph one by one, the dashboard uses preset-based analytics views. This improves usability and keeps the application faster.

Current preset views:

- `Executive Overview`
- `Customer Intelligence`
- `Product And Market`
- `Full Suite`

These presets load related charts together so the user gets full context with fewer clicks.

### 5. Manager-Focused Analytics

The sales analytics focus on business questions, not just visuals:

- Commercial Performance Trend
- Top Products by Revenue
- Average Order Value Trend
- Monthly Order Value Mix
- Market Performance by Country
- Product Portfolio Balance
- Number of Customers by Segment
- Customer Segment Distribution
- Repeat Customer Value Map
- Manager Health Snapshot

### 6. Cancellation Analytics

The dashboard also includes an optional cancellation analysis area to help identify operational loss and quality issues.

This section includes:

- cancellation KPIs
- monthly cancellation rate trends
- top cancelled products
- countries with the highest cancellation activity
- a written cancellation insight section

## Performance Design

One of the main goals of the refactor was improving load speed and avoiding unnecessary recomputation.

The app improves performance by:

- caching data loading with `st.cache_data`
- caching preprocessing steps
- caching reusable chart summaries
- avoiding repeated heavy groupby operations where possible
- loading only the selected analytics preset instead of every chart at once
- limiting raw table rendering to the first 1,000 rows in the browser

This keeps the app responsive while still supporting deeper analysis.

## Project Structure

```text
online_store_dashboard/
├── app.py
├── requirements.txt
├── data/
│   └── online_retail_II.xlsx
└── src/
    ├── analysis.py
    ├── cache_utils.py
    ├── cancelled_analysis.py
    ├── charts.py
    ├── clean_data.py
    ├── data_loader.py
    └── kpi_cards.py
```

### File Responsibilities

- `app.py`: main Streamlit application and page flow
- `src/data_loader.py`: loading CSV and Excel data
- `src/clean_data.py`: cleaning and filtering transaction records
- `src/analysis.py`: KPI calculations, period comparisons, and helper analysis logic
- `src/charts.py`: sales analytics explorer and manager-facing visualizations
- `src/cancelled_analysis.py`: cancellation-specific dashboard and charts
- `src/kpi_cards.py`: reusable KPI card rendering

## How To Run

### 1. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Start the dashboard

```powershell
streamlit run app.py
```

## Example Workflow

1. Launch the dashboard.
2. Upload the retail dataset or provide a direct file URL.
3. Review the processing summary to understand what happened to the raw data.
4. Filter by country, month, or top products.
5. Read the KPI cards for the executive snapshot.
6. Choose an analytics preset depending on the business question.
7. Open cancellation analytics when operational risk needs review.

## Business Rationale Behind The Design

This project is not only about showing data. It is about showing the right data in the right order.

The design choices were made for clear reasons:

- KPI cards come first because executives need immediate health indicators.
- The processing summary was added to explain what happens behind the scenes and make the app more transparent.
- Revenue and order trends were merged because separate charts created redundancy.
- Full-width chart rows improve readability and make comparisons easier.
- Preset analytics views reduce repetitive user actions and better match how managers explore information.
- Customer segmentation was added because leadership often needs to know not just how much was sold, but who is driving the business.
- Cancellation analytics remain separate so the core sales view is not distorted by operational exceptions.

## Limitations

- The dashboard depends on the structure of the uploaded retail dataset.
- Some advanced metrics such as true lifetime value or long-term churn are approximations unless a richer customer history exists.
- Very large datasets may still take time during the first preprocessing run, even with caching.

## Future Improvements

- export charts and executive summaries to PDF
- add forecasting for revenue or demand
- add cohort analysis and retention trends
- support database connections instead of only file uploads
- allow role-based dashboards for executives, operations, and product teams

## Tech Stack

- Python
- Streamlit
- Pandas
- Plotly
- OpenPyXL

