import pandas as pd
import plotly.express as px
import streamlit as st


CURRENCY_SYMBOL = "£"


NON_PRODUCT_STOCK_CODES = {
    "M",
    "AMAZONFEE",
    "B",
    "ADJUST",
    "POST",
    "DOT",
    "84016",
}


# ============================================================
# DATA PREPARATION
# ============================================================

def _prepare_cancellation_data(
    df_cancel_source: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Separate valid completed sales and cancelled transactions.

    A transaction is considered cancelled when its invoice
    number begins with 'C'.

    This function runs only once each time
    render_cancelled_dashboard() is called.
    """

    if df_cancel_source.empty:

        return (
            pd.DataFrame(),
            pd.DataFrame(),
        )

    df = df_cancel_source.copy()

    # --------------------------------------------------------
    # Standardise important columns
    # --------------------------------------------------------

    df["StockCode"] = (
        df["StockCode"]
        .astype(str)
        .str.strip()
    )

    df["Invoice"] = (
        df["Invoice"]
        .astype(str)
        .str.strip()
    )

    df["InvoiceDate"] = (
        pd.to_datetime(
            df["InvoiceDate"],
            errors="coerce",
        )
    )

    df["Quantity"] = pd.to_numeric(
        df["Quantity"],
        errors="coerce",
    )

    df["Price"] = pd.to_numeric(
        df["Price"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Remove unusable rows
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "InvoiceDate",
            "Quantity",
            "Price",
        ]
    )

    if df.empty:

        return (
            pd.DataFrame(),
            pd.DataFrame(),
        )

    # --------------------------------------------------------
    # Create calculation columns
    # --------------------------------------------------------

    df["Revenue"] = (
        df["Quantity"]
        * df["Price"]
    )

    df["IsCancelled"] = (
        df["Invoice"]
        .str.upper()
        .str.startswith("C")
    )

    df["Month"] = (
        df["InvoiceDate"]
        .dt.to_period("M")
        .astype(str)
    )

    # --------------------------------------------------------
    # Remove non-product codes once
    # --------------------------------------------------------

    df = df[
        ~df["StockCode"].isin(
            NON_PRODUCT_STOCK_CODES
        )
    ]

    # --------------------------------------------------------
    # VALID COMPLETED SALES
    # --------------------------------------------------------

    sales_mask = (
        (~df["IsCancelled"])
        & (df["Price"] > 0)
        & (df["Quantity"] > 0)
        & (df["Quantity"] <= 10000)
    )

    sales_df = (
        df.loc[
            sales_mask
        ]
        .drop_duplicates()
        .copy()
    )

    # --------------------------------------------------------
    # CANCELLED TRANSACTIONS
    # --------------------------------------------------------

    cancelled = (
        df.loc[
            df["IsCancelled"]
        ]
        .copy()
    )

    if not cancelled.empty:

        cancelled[
            "Cancelled Revenue"
        ] = (
            cancelled[
                "Revenue"
            ].abs()
        )

    return (
        sales_df,
        cancelled,
    )


# ============================================================
# CSV HELPER
# ============================================================

def _dataframe_to_csv(
    df: pd.DataFrame,
) -> bytes:
    """
    Convert dataframe to downloadable CSV bytes.
    """

    return df.to_csv(
        index=False
    ).encode("utf-8")


# ============================================================
# DOWNLOADABLE CHART
# ============================================================

def _show_downloadable_chart(
    fig,
    chart_data: pd.DataFrame,
    chart_key: str,
    csv_filename: str,
):
    """
    Display Plotly chart with PNG and CSV download support.
    """

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "responsive": True,
            "toImageButtonOptions": {
                "format": "png",
                "filename": chart_key,
                "height": 700,
                "width": 1200,
                "scale": 2,
            },
        },
    )

    st.download_button(
        label=(
            "⬇ Download chart data as CSV"
        ),
        data=_dataframe_to_csv(
            chart_data
        ),
        file_name=csv_filename,
        mime="text/csv",
        key=f"download_{chart_key}",
        use_container_width=True,
    )


# ============================================================
# KPI CALCULATIONS
# ============================================================

def _calculate_cancellation_kpis(
    sales_df: pd.DataFrame,
    cancelled: pd.DataFrame,
) -> dict:
    """
    Calculate cancellation dashboard KPIs.
    """

    total_sales_orders = (
        sales_df[
            "Invoice"
        ].nunique()
        if not sales_df.empty
        else 0
    )

    cancelled_orders = (
        cancelled[
            "Invoice"
        ].nunique()
        if not cancelled.empty
        else 0
    )

    total_activity = (
        total_sales_orders
        + cancelled_orders
    )

    cancellation_activity_rate = (
        cancelled_orders
        / total_activity
        * 100
        if total_activity > 0
        else 0
    )

    net_sales_revenue = (
        sales_df[
            "Revenue"
        ].sum()
        if not sales_df.empty
        else 0
    )

    cancelled_revenue = (
        cancelled[
            "Cancelled Revenue"
        ].sum()
        if not cancelled.empty
        else 0
    )

    total_transaction_value = (
        net_sales_revenue
        + cancelled_revenue
    )

    cancelled_revenue_share = (
        cancelled_revenue
        / total_transaction_value
        * 100
        if total_transaction_value > 0
        else 0
    )

    return {
        "total_sales_orders": (
            total_sales_orders
        ),
        "cancelled_orders": (
            cancelled_orders
        ),
        "cancellation_activity_rate": (
            cancellation_activity_rate
        ),
        "net_sales_revenue": (
            net_sales_revenue
        ),
        "cancelled_revenue": (
            cancelled_revenue
        ),
        "cancelled_revenue_share": (
            cancelled_revenue_share
        ),
    }


# ============================================================
# MONTHLY CANCELLATION RATE DATA
# ============================================================

def _build_monthly_cancellation_data(
    sales_df: pd.DataFrame,
    cancelled: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build monthly sales/cancellation summary.
    """

    if sales_df.empty:

        monthly_sales = pd.DataFrame(
            columns=[
                "Month",
                "Sales Orders",
            ]
        )

    else:

        monthly_sales = (
            sales_df.groupby(
                "Month",
                observed=True,
                as_index=False,
            )
            .agg(
                **{
                    "Sales Orders": (
                        "Invoice",
                        "nunique",
                    )
                }
            )
        )

    if cancelled.empty:

        monthly_cancelled = pd.DataFrame(
            columns=[
                "Month",
                "Cancelled Orders",
            ]
        )

    else:

        monthly_cancelled = (
            cancelled.groupby(
                "Month",
                observed=True,
                as_index=False,
            )
            .agg(
                **{
                    "Cancelled Orders": (
                        "Invoice",
                        "nunique",
                    )
                }
            )
        )

    monthly = monthly_sales.merge(
        monthly_cancelled,
        on="Month",
        how="outer",
    )

    if monthly.empty:

        return monthly

    count_columns = [
        "Sales Orders",
        "Cancelled Orders",
    ]

    monthly[count_columns] = (
        monthly[
            count_columns
        ]
        .fillna(0)
        .astype(int)
    )

    monthly["Total Activity"] = (
        monthly["Sales Orders"]
        + monthly["Cancelled Orders"]
    )

    monthly[
        "Cancellation Activity Rate (%)"
    ] = (
        monthly["Cancelled Orders"]
        / monthly[
            "Total Activity"
        ].replace(
            0,
            pd.NA,
        )
        * 100
    ).fillna(0)

    return monthly.sort_values(
        "Month"
    )


# ============================================================
# MONTHLY CANCELLATION RATE CHART
# ============================================================

def render_monthly_cancellation_rate(
    monthly: pd.DataFrame,
):

    st.subheader(
        "Monthly Cancellation Activity Rate"
    )

    if monthly.empty:

        st.info(
            "No monthly cancellation data "
            "is available."
        )

        return

    fig = px.line(
        monthly,
        x="Month",
        y=(
            "Cancellation Activity Rate (%)"
        ),
        markers=True,
        labels={
            (
                "Cancellation Activity Rate (%)"
            ): (
                "Cancellation Activity Rate (%)"
            ),
        },
    )

    fig.update_layout(
        title=(
            "Are cancellation transactions "
            "becoming more frequent?"
        ),
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Cancellation activity rate: "
            "%{y:.2f}%"
            "<extra></extra>"
        )
    )

    _show_downloadable_chart(
        fig=fig,
        chart_data=monthly,
        chart_key=(
            "monthly_cancellation_activity_rate"
        ),
        csv_filename=(
            "monthly_cancellation_activity_rate.csv"
        ),
    )


# ============================================================
# TOP CANCELLED PRODUCTS
# ============================================================

def render_top_cancelled_products(
    cancelled: pd.DataFrame,
    top_n: int = 10,
):

    st.subheader(
        f"Top {top_n} Products "
        "by Cancelled Revenue"
    )

    if cancelled.empty:

        st.info(
            "No cancelled-product data "
            "is available."
        )

        return

    product_data = cancelled.dropna(
        subset=["Description"]
    )

    if product_data.empty:

        st.info(
            "No cancelled-product data "
            "is available."
        )

        return

    product_impact = (
        product_data.groupby(
            "Description",
            observed=True,
            as_index=False,
        )
        .agg(
            CancelledRevenue=(
                "Cancelled Revenue",
                "sum",
            ),
            CancelledOrders=(
                "Invoice",
                "nunique",
            ),
        )
        .nlargest(
            top_n,
            "CancelledRevenue",
        )
    )

    if product_impact.empty:

        st.info(
            "No cancelled-product data "
            "is available."
        )

        return

    chart_data = (
        product_impact.sort_values(
            "CancelledRevenue",
            ascending=True,
        )
    )

    fig = px.bar(
        chart_data,
        x="CancelledRevenue",
        y="Description",
        orientation="h",
        labels={
            "CancelledRevenue": (
                f"Cancelled Revenue "
                f"({CURRENCY_SYMBOL})"
            ),
            "Description": "Product",
        },
    )

    fig.update_layout(
        title=(
            "Which products have the greatest "
            "financial cancellation impact?"
        ),
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>"
            f"Cancelled revenue: "
            f"{CURRENCY_SYMBOL}%{{x:,.2f}}"
            "<extra></extra>"
        )
    )

    _show_downloadable_chart(
        fig=fig,
        chart_data=product_impact,
        chart_key=(
            "top_products_by_cancelled_revenue"
        ),
        csv_filename=(
            "top_products_by_cancelled_revenue.csv"
        ),
    )


# ============================================================
# COUNTRY CANCELLATION RATE
# ============================================================

def render_country_cancellation_rate(
    sales_df: pd.DataFrame,
    cancelled: pd.DataFrame,
    top_n: int = 10,
    minimum_activity: int = 100,
):

    st.subheader(
        "Countries with Highest "
        "Cancellation Activity Rate"
    )

    if sales_df.empty:

        country_sales = pd.DataFrame(
            columns=[
                "Country",
                "Sales Orders",
            ]
        )

    else:

        country_sales = (
            sales_df.groupby(
                "Country",
                observed=True,
                as_index=False,
            )
            .agg(
                **{
                    "Sales Orders": (
                        "Invoice",
                        "nunique",
                    )
                }
            )
        )

    if cancelled.empty:

        country_cancelled = pd.DataFrame(
            columns=[
                "Country",
                "Cancelled Orders",
            ]
        )

    else:

        country_cancelled = (
            cancelled.groupby(
                "Country",
                observed=True,
                as_index=False,
            )
            .agg(
                **{
                    "Cancelled Orders": (
                        "Invoice",
                        "nunique",
                    )
                }
            )
        )

    country_rate = country_sales.merge(
        country_cancelled,
        on="Country",
        how="outer",
    )

    if country_rate.empty:

        st.info(
            "No country cancellation data "
            "is available."
        )

        return

    count_columns = [
        "Sales Orders",
        "Cancelled Orders",
    ]

    country_rate[count_columns] = (
        country_rate[
            count_columns
        ]
        .fillna(0)
        .astype(int)
    )

    country_rate[
        "Total Activity"
    ] = (
        country_rate["Sales Orders"]
        + country_rate[
            "Cancelled Orders"
        ]
    )

    # Prevent extremely small samples from
    # dominating the ranking.
    country_rate = country_rate[
        country_rate[
            "Total Activity"
        ] >= minimum_activity
    ]

    if country_rate.empty:

        st.info(
            "No countries meet the minimum "
            f"activity threshold of "
            f"{minimum_activity} transactions."
        )

        return

    country_rate[
        "Cancellation Activity Rate (%)"
    ] = (
        country_rate[
            "Cancelled Orders"
        ]
        / country_rate[
            "Total Activity"
        ].replace(
            0,
            pd.NA,
        )
        * 100
    ).fillna(0)

    country_rate = (
        country_rate.nlargest(
            top_n,
            (
                "Cancellation Activity "
                "Rate (%)"
            ),
        )
    )

    chart_data = (
        country_rate.sort_values(
            (
                "Cancellation Activity "
                "Rate (%)"
            ),
            ascending=True,
        )
    )

    fig = px.bar(
        chart_data,
        x=(
            "Cancellation Activity Rate (%)"
        ),
        y="Country",
        orientation="h",
        labels={
            (
                "Cancellation Activity Rate (%)"
            ): (
                "Cancellation Activity Rate (%)"
            ),
        },
    )

    fig.update_layout(
        title=(
            "Which sufficiently active markets "
            "have the highest cancellation activity?"
        ),
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Cancellation activity rate: "
            "%{x:.2f}%"
            "<extra></extra>"
        )
    )

    _show_downloadable_chart(
        fig=fig,
        chart_data=country_rate,
        chart_key=(
            "country_cancellation_activity_rate"
        ),
        csv_filename=(
            "country_cancellation_activity_rate.csv"
        ),
    )


# ============================================================
# DYNAMIC EXECUTIVE INSIGHT
# ============================================================

def render_cancellation_insight(
    kpis: dict,
    cancelled: pd.DataFrame,
):

    st.subheader(
        "Cancellation Insight"
    )

    rate = kpis[
        "cancellation_activity_rate"
    ]

    revenue_share = kpis[
        "cancelled_revenue_share"
    ]

    if revenue_share < 5:

        revenue_message = (
            "Cancelled transaction value represents "
            "a relatively small share of overall "
            "transaction value."
        )

    elif revenue_share < 15:

        revenue_message = (
            "Cancelled transaction value represents "
            "a noticeable share of overall transaction "
            "value and should be monitored closely."
        )

    else:

        revenue_message = (
            "Cancelled transaction value represents "
            "a significant share of overall transaction "
            "value and requires management attention."
        )

    if cancelled.empty:

        concentration_message = (
            "No cancelled transactions were found "
            "for the current filters."
        )

    else:

        product_data = cancelled.dropna(
            subset=["Description"]
        )

        if product_data.empty:

            concentration_message = (
                "No identified product information is "
                "available for cancellation concentration "
                "analysis."
            )

        else:

            product_impact = (
                product_data.groupby(
                    "Description",
                    observed=True,
                )[
                    "Cancelled Revenue"
                ]
                .sum()
                .nlargest(5)
            )

            top_5_value = (
                product_impact.sum()
            )

            total_cancelled_value = (
                product_data[
                    "Cancelled Revenue"
                ].sum()
            )

            top_5_share = (
                top_5_value
                / total_cancelled_value
                * 100
                if total_cancelled_value > 0
                else 0
            )

            concentration_message = (
                "The top five affected products "
                f"account for {top_5_share:.1f}% "
                "of cancelled revenue value."
            )

    st.info(
        f"""
- The cancellation activity rate is **{rate:.2f}%**.
- Cancelled revenue share is **{revenue_share:.2f}%**.
- {revenue_message}
- {concentration_message}
        """
    )

    if revenue_share >= 15:

        st.warning(
            "Recommendation: Prioritise investigation "
            "of high-impact products and markets. "
            "Review possible causes such as product "
            "quality, stock accuracy, delivery "
            "performance, and customer expectations."
        )

    elif revenue_share >= 5:

        st.warning(
            "Recommendation: Monitor cancellation "
            "trends and investigate the products and "
            "markets responsible for the greatest "
            "financial impact."
        )

    else:

        st.success(
            "Recommendation: Overall cancellation "
            "impact is currently limited, but "
            "concentrated problem areas should still "
            "be reviewed."
        )


# ============================================================
# MAIN CANCELLATION DASHBOARD
# ============================================================

def render_cancelled_dashboard(
    df_cancel_source: pd.DataFrame,
):
    """
    Render complete cancellation analytics dashboard.

    The original transaction dataset is prepared once,
    after which all cancellation visualisations reuse
    the prepared sales_df and cancelled dataframes.
    """

    st.header(
        "Cancellation Performance Overview"
    )

    st.caption(
        "This section analyses cancellation transactions "
        "separately from completed sales so operational "
        "losses and problem areas can be assessed without "
        "distorting the main sales dashboard."
    )

    if df_cancel_source.empty:

        st.info(
            "No transaction data is available "
            "for cancellation analysis."
        )

        return

    required_columns = [
        "Invoice",
        "InvoiceDate",
        "Quantity",
        "Price",
        "StockCode",
        "Description",
        "Country",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df_cancel_source.columns
    ]

    if missing_columns:

        st.warning(
            "The following columns are required "
            "for cancellation analysis: "
            f"{missing_columns}"
        )

        return

    # ========================================================
    # PREPARE DATA ONCE
    # ========================================================

    sales_df, cancelled = (
        _prepare_cancellation_data(
            df_cancel_source
        )
    )

    if (
        sales_df.empty
        and cancelled.empty
    ):

        st.info(
            "No valid completed or cancelled "
            "transactions are available after "
            "cancellation-data preparation."
        )

        return

    # ========================================================
    # CALCULATE KPIS ONCE
    # ========================================================

    kpis = _calculate_cancellation_kpis(
        sales_df,
        cancelled,
    )

    # ========================================================
    # KPI ROW 1
    # ========================================================

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Completed Sales Orders",
        f"{kpis['total_sales_orders']:,}",
    )

    col2.metric(
        "Cancelled Orders",
        f"{kpis['cancelled_orders']:,}",
    )

    col3.metric(
        "Cancellation Activity Rate",
        (
            f"{kpis['cancellation_activity_rate']:.2f}%"
        ),
    )

    # ========================================================
    # KPI ROW 2
    # ========================================================

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Net Sales Revenue",
        (
            f"{CURRENCY_SYMBOL}"
            f"{kpis['net_sales_revenue']:,.2f}"
        ),
    )

    col5.metric(
        "Cancelled Revenue Value",
        (
            f"{CURRENCY_SYMBOL}"
            f"{kpis['cancelled_revenue']:,.2f}"
        ),
    )

    col6.metric(
        "Cancelled Revenue Share",
        (
            f"{kpis['cancelled_revenue_share']:.2f}%"
        ),
    )

    # ========================================================
    # DYNAMIC INSIGHT
    # ========================================================

    render_cancellation_insight(
        kpis,
        cancelled,
    )

    st.divider()

    # ========================================================
    # MONTHLY SUMMARY — CALCULATE ONCE
    # ========================================================

    monthly = (
        _build_monthly_cancellation_data(
            sales_df,
            cancelled,
        )
    )

    render_monthly_cancellation_rate(
        monthly
    )

    # ========================================================
    # PRODUCT AND COUNTRY ANALYSIS
    # ========================================================

    col7, col8 = st.columns(2)

    with col7:

        render_top_cancelled_products(
            cancelled
        )

    with col8:

        render_country_cancellation_rate(
            sales_df,
            cancelled,
        )
