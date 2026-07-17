import pandas as pd
import streamlit as st


# ============================================================
# DATA PREPARATION
# ============================================================

@st.cache_data(max_entries=4)
def prepare_data(df):
    """
    Add calculated fields required by the dashboard.
    """

    df = df.copy()

    required_columns = [
        "Quantity",
        "Price",
        "InvoiceDate",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns for analysis: "
            f"{missing_columns}"
        )

    df["TotalPrice"] = (
        df["Quantity"] * df["Price"]
    )

    df["InvoiceDate"] = pd.to_datetime(
        df["InvoiceDate"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["InvoiceDate"]
    )

    df["InvoiceMonth"] = (
        df["InvoiceDate"]
        .dt.to_period("M")
        .astype(str)
    )

    return df


# ============================================================
# FILTER OPTIONS
# ============================================================

@st.cache_data(max_entries=8)
def get_unique_countries(df):
    return sorted(
        df["Country"]
        .dropna()
        .unique()
    )


@st.cache_data(max_entries=8)
def get_unique_months(df):
    return sorted(
        df["InvoiceMonth"]
        .dropna()
        .unique()
    )


@st.cache_data(max_entries=8)
def get_top_products(df):
    """
    Return the top 50 products ranked by revenue.
    """

    return (
        df.dropna(subset=["Description"])
        .groupby("Description")["TotalPrice"]
        .sum()
        .sort_values(ascending=False)
        .head(50)
        .index
        .tolist()
    )


# ============================================================
# KPI CALCULATIONS
# ============================================================

@st.cache_data(max_entries=8)
def calculate_kpis(df):
    """
    Calculate the main executive dashboard KPIs.
    """

    total_revenue = (
        df["TotalPrice"].sum()
    )

    total_orders = (
        df["Invoice"].nunique()
    )

    total_customers = (
        df["Customer ID"].nunique()
    )

    total_items = (
        df["Quantity"].sum()
    )

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
        "average_order_value": (
            average_order_value
        ),
    }


# ============================================================
# PREVIOUS PERIOD
# ============================================================

def get_previous_period_df(
    df,
    selected_months,
):
    """
    Return rows for the period immediately preceding the
    selected period, using the same number of months.

    Example:
        Selected:
            2011-08
            2011-09

        Previous:
            2011-06
            2011-07
    """

    if not selected_months:
        return df.iloc[0:0]

    all_months = sorted(
        df["InvoiceMonth"]
        .dropna()
        .unique()
    )

    number_of_months = len(
        selected_months
    )

    earliest_selected = min(
        selected_months
    )

    if earliest_selected not in all_months:
        return df.iloc[0:0]

    selected_index = all_months.index(
        earliest_selected
    )

    start_index = max(
        0,
        selected_index - number_of_months,
    )

    previous_months = all_months[
        start_index:selected_index
    ]

    if not previous_months:
        return df.iloc[0:0]

    return df[
        df["InvoiceMonth"].isin(
            previous_months
        )
    ]


# ============================================================
# KPI DELTAS
# ============================================================

@st.cache_data(max_entries=8)
def calculate_kpis_with_delta(
    current_df,
    previous_df,
):
    """
    Calculate current KPIs and percentage changes against
    the previous comparison period.

    A delta is None when no valid previous-period comparison
    is available.
    """

    current = calculate_kpis(
        current_df
    )

    if previous_df.empty:
        return (
            current,
            {
                key: None
                for key in current
            },
        )

    previous = calculate_kpis(
        previous_df
    )

    deltas = {}

    for key in current:
        previous_value = previous.get(
            key,
            0,
        )

        if previous_value != 0:
            deltas[key] = (
                (
                    current[key]
                    - previous_value
                )
                / previous_value
                * 100
            )
        else:
            deltas[key] = None

    return current, deltas
