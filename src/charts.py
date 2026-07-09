import pandas as pd
import plotly.express as px
import streamlit as st


CURRENCY_SYMBOL = "£"

st.write("CHARTS FILE:", __file__)
# ============================================================
# SHARED HELPER
# ============================================================


def _monthly_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate monthly revenue and order metrics once.
    """

    if df.empty:
        return pd.DataFrame(
            columns=[
                "InvoiceMonth",
                "Revenue",
                "Orders",
                "Month",
            ]
        )

    monthly = (
        df.groupby(
            "InvoiceMonth",
            observed=True,
            as_index=False,
        )
        .agg(
            Revenue=(
                "TotalPrice",
                "sum",
            ),
            Orders=(
                "Invoice",
                "nunique",
            ),
        )
        .sort_values(
            "InvoiceMonth"
        )
    )

    monthly["Month"] = (
        monthly["InvoiceMonth"]
        .astype(str)
    )

    return monthly


# ============================================================
# CHART 1: MONTHLY REVENUE TREND
# ============================================================

def render_revenue_trend(
    monthly: pd.DataFrame,
):
    """
    Display monthly revenue trend.
    """

    st.subheader(
        "Monthly Revenue Trend"
    )

    if monthly.empty:
        st.info(
            "No revenue data is available."
        )
        return

    chart_data = monthly[
        [
            "Month",
            "Revenue",
        ]
    ].copy()

    fig = px.line(
        chart_data,
        x="Month",
        y="Revenue",
        markers=True,
        labels={
            "Month": "Month",
            "Revenue": (
                f"Revenue ({CURRENCY_SYMBOL})"
            ),
        },
    )

    fig.update_layout(
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"
            f"Revenue: "
            f"{CURRENCY_SYMBOL}%{{y:,.2f}}"
            "<extra></extra>"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="monthly_revenue_trend",
    )


# ============================================================
# CHART 2: MONTHLY ORDERS TREND
# ============================================================

def render_orders_trend(
    monthly: pd.DataFrame,
):
    """
    Display monthly orders trend.
    """

    st.subheader(
        "Monthly Orders Trend"
    )

    if monthly.empty:
        st.info(
            "No order data is available."
        )
        return

    chart_data = monthly[
        [
            "Month",
            "Orders",
        ]
    ].copy()

    fig = px.line(
        chart_data,
        x="Month",
        y="Orders",
        markers=True,
        labels={
            "Month": "Month",
            "Orders": "Number of Orders",
        },
    )

    fig.update_layout(
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Orders: %{y:,.0f}"
            "<extra></extra>"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="monthly_orders_trend",
    )


# ============================================================
# CHART 3: TOP 10 PRODUCTS BY REVENUE
# ============================================================

def render_top_products(
    df: pd.DataFrame,
):
    """
    Display top 10 products by revenue.
    """

    st.subheader(
        "Top 10 Products by Revenue"
    )

    product_data = df.dropna(
        subset=["Description"]
    ).copy()

    if product_data.empty:
        st.info(
            "No product data is available."
        )
        return

    top_products = (
        product_data.groupby(
            "Description",
            observed=True,
            as_index=False,
        )
        .agg(
            Revenue=(
                "TotalPrice",
                "sum",
            ),
        )
        .nlargest(
            10,
            "Revenue",
        )
        .sort_values(
            "Revenue",
            ascending=True,
        )
    )

    if top_products.empty:
        st.info(
            "No product data is available."
        )
        return

    fig = px.bar(
        top_products,
        x="Revenue",
        y="Description",
        orientation="h",
        labels={
            "Revenue": (
                f"Revenue ({CURRENCY_SYMBOL})"
            ),
            "Description": "Product",
        },
    )

    fig.update_layout(
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>"
            f"Revenue: "
            f"{CURRENCY_SYMBOL}%{{x:,.2f}}"
            "<extra></extra>"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="top_10_products_by_revenue",
    )


# ============================================================
# MAIN SALES CHARTS FUNCTION
# ============================================================

def render_charts(
    df: pd.DataFrame,
):
    """
    Render exactly 3 sales charts:

    1. Monthly Revenue Trend
    2. Monthly Orders Trend
    3. Top 10 Products by Revenue
    """

    if df.empty:
        st.warning(
            "No sales data is available "
            "for the selected filters."
        )
        return

    required_columns = [
        "InvoiceMonth",
        "TotalPrice",
        "Invoice",
        "Description",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        st.warning(
            "The following columns are "
            "required for charts: "
            f"{missing_columns}"
        )
        return

    monthly = _monthly_summary(df)

    # Sales chart 1
    render_revenue_trend(monthly)

    # Sales chart 2
    render_orders_trend(monthly)

    # Sales chart 3
    render_top_products(df)
