import pandas as pd

import streamlit as st

from src.data_loader import load_data
from src.clean_data import clean_data
from src.analysis import (
    prepare_data,
    get_unique_countries,
    get_unique_months,
    get_top_products,
    calculate_kpis_with_delta,
    get_previous_period_df,
)
from src.kpi_cards import render_kpi_cards
from src.charts import render_charts
from src.cancelled_analysis import render_cancelled_dashboard



st.title("📊 Online Store Dashboard")


# -----------------------
# 1. DATA INPUT
# -----------------------

df = None

option = st.sidebar.radio(
    "Data Source",
    ["Upload File", "URL"]
)

if option == "Upload File":
    file = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx"]
    )

    if file:
        df = load_data(file)

elif option == "URL":
    url = st.text_input("Enter URL")

    if url:
        df = load_data(url)


# -----------------------
# 2. STOP IF NO DATA
# -----------------------

if df is None:
    st.info("Please upload or load data")
    st.stop()


# -----------------------
# 3. PROCESS DATA
# -----------------------

df_original = df.copy()

df = clean_data(df)
df = prepare_data(df)

df_cancel_source = df_original.copy()
df_cancel_source = prepare_data(df_cancel_source)

# -----------------------
# 4. FILTERS
# -----------------------

st.sidebar.header("🔎 Filters")


# Country filter
if "Country" in df.columns:
    countries = st.sidebar.multiselect(
        "Select Country",
        options=get_unique_countries(df),
        default=get_unique_countries(df)
    )

    df = df[df["Country"].isin(countries)]


# Save a copy here: Country/Product filters applied, but NOT the Month filter.
# This is what we use to look up the "previous period" for KPI deltas.
df_before_month_filter = df.copy()


# Month filter
months = []
if "InvoiceMonth" in df.columns:
    months = st.sidebar.multiselect(
        "Select Month",
        options=get_unique_months(df),
        default=get_unique_months(df)
    )

    df = df[df["InvoiceMonth"].isin(months)]


# Product filter
if "Description" in df.columns:
    products = st.sidebar.multiselect(
        "Select Top Products",
        options=get_top_products(df)
    )

    if products:
        df = df[df["Description"].isin(products)]
        df_before_month_filter = df_before_month_filter[
            df_before_month_filter["Description"].isin(products)
        ]


# -----------------------
# 5. KPI DASHBOARD
# -----------------------

previous_df = get_previous_period_df(df_before_month_filter, months)
kpis, deltas = calculate_kpis_with_delta(df, previous_df)

st.subheader("📈 Key Performance Indicators")

render_kpi_cards([
    {
        "label": "Total Revenue",
        "value": f"${kpis['total_revenue']:,.2f}",
        "icon": "💰",
        "accent": "#6366f1",
        "delta": deltas["total_revenue"],
    },
    {
        "label": "Total Orders",
        "value": f"{kpis['total_orders']:,}",
        "icon": "🛒",
        "accent": "#22c55e",
        "delta": deltas["total_orders"],
    },
    {
        "label": "Customers",
        "value": f"{kpis['total_customers']:,}",
        "icon": "👥",
        "accent": "#f59e0b",
        "delta": deltas["total_customers"],
    },
    {
        "label": "Items Sold",
        "value": f"{kpis['total_items']:,}",
        "icon": "📦",
        "accent": "#ec4899",
        "delta": deltas["total_items"],
    },
])

# -----------------------
# 6. CHARTS
# -----------------------
render_charts(df)

## -----------------------
# 6B. CANCELLED ORDERS ANALYSIS
# -----------------------
render_cancelled_dashboard(df_cancel_source)

# -----------------------
# 7. SHOW DATA
# -----------------------

with st.expander("View Raw Data"):
    st.dataframe(df)
