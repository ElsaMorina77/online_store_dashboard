import pandas as pd
import streamlit as st

@st.cache_data
def prepare_data(df):
    df = df.copy()

    df["TotalPrice"] = df["Quantity"] * df["Price"]
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["InvoiceMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)

    return df


@st.cache_data
def get_unique_countries(df):
    return sorted(df["Country"].dropna().unique())


@st.cache_data
def get_unique_months(df):
    return sorted(df["InvoiceMonth"].dropna().unique())


@st.cache_data
def get_top_products(df):
    return df["Description"].dropna().value_counts().index[:50].tolist()

#Kpi's down here:
@st.cache_data
def calculate_kpis(df):
    total_revenue = df["TotalPrice"].sum()

    total_orders = df["Invoice"].nunique()

    total_customers = df["Customer ID"].nunique()

    total_items = df["Quantity"].sum()

    average_order_value = (
        total_revenue / total_orders
        if total_orders != 0
        else 0
    )

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "total_items": total_items,
        "average_order_value": average_order_value
    }


def get_previous_period_df(df, selected_months):
    """
    Given a dataframe (already filtered by Country/Product but NOT by month)
    and the list of currently selected months (e.g. ['2011-08', '2011-09']),
    return the rows belonging to the immediately preceding period of the
    same length.

    Example: if selected_months = ['2011-08', '2011-09'] (2 months),
    this returns data for ['2011-06', '2011-07'].
    """
    if not selected_months:
        return df.iloc[0:0]

    all_months = sorted(df["InvoiceMonth"].dropna().unique())
    n = len(selected_months)

    earliest_selected = min(selected_months)
    idx = all_months.index(earliest_selected)

    start = max(0, idx - n)
    previous_months = all_months[start:idx]

    if not previous_months:
        return df.iloc[0:0]

    return df[df["InvoiceMonth"].isin(previous_months)]


@st.cache_data
def calculate_kpis_with_delta(current_df, previous_df):
    """
    Returns (current_kpis, deltas) where deltas is a dict of
    {kpi_name: percent_change_or_None}.
    percent_change is None when there's no previous-period data to compare
    against (e.g. you're looking at the very first month in the dataset).
    """
    current = calculate_kpis(current_df)

    if previous_df.empty:
        return current, {k: None for k in current}

    previous = calculate_kpis(previous_df)

    deltas = {}
    for key in current:
        prev_val = previous.get(key, 0)
        if prev_val:
            deltas[key] = ((current[key] - prev_val) / prev_val) * 100
        else:
            deltas[key] = None

    return current, deltas