import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


CURRENCY_SYMBOL = "GBP"


@st.cache_data(
    show_spinner=False,
    max_entries=8,
)
def _monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build monthly commercial performance metrics once.
    """

    if df.empty:
        return pd.DataFrame(
            columns=[
                "InvoiceMonth",
                "Revenue",
                "Orders",
                "Customers",
                "AverageOrderValue",
                "RevenuePerCustomer",
                "Month",
            ]
        )

    summary = (
        df.groupby(
            "InvoiceMonth",
            observed=True,
            as_index=False,
        )
        .agg(
            Revenue=("TotalPrice", "sum"),
            Orders=("Invoice", "nunique"),
            Customers=("Customer ID", "nunique"),
        )
        .sort_values("InvoiceMonth")
    )

    summary["AverageOrderValue"] = (
        summary["Revenue"]
        / summary["Orders"].replace(0, pd.NA)
    ).fillna(0)
    summary["RevenuePerCustomer"] = (
        summary["Revenue"]
        / summary["Customers"].replace(0, pd.NA)
    ).fillna(0)
    summary["Month"] = summary["InvoiceMonth"].astype(str)

    return summary


@st.cache_data(
    show_spinner=False,
    max_entries=8,
)
def _product_summary(
    df: pd.DataFrame,
    top_n: int = 15,
) -> pd.DataFrame:
    """
    Summarize product performance for portfolio analysis.
    """

    if df.empty:
        return pd.DataFrame(
            columns=[
                "Description",
                "Revenue",
                "UnitsSold",
                "Orders",
            ]
        )

    product_data = df.dropna(subset=["Description"]).copy()

    if product_data.empty:
        return pd.DataFrame(
            columns=[
                "Description",
                "Revenue",
                "UnitsSold",
                "Orders",
            ]
        )

    return (
        product_data.groupby(
            "Description",
            observed=True,
            as_index=False,
        )
        .agg(
            Revenue=("TotalPrice", "sum"),
            UnitsSold=("Quantity", "sum"),
            Orders=("Invoice", "nunique"),
        )
        .nlargest(top_n, "Revenue")
    )


@st.cache_data(
    show_spinner=False,
    max_entries=8,
)
def _country_summary(
    df: pd.DataFrame,
    minimum_orders: int = 5,
) -> pd.DataFrame:
    """
    Summarize market performance by country.
    """

    if df.empty:
        return pd.DataFrame(
            columns=[
                "Country",
                "Revenue",
                "Orders",
                "Customers",
                "AverageOrderValue",
            ]
        )

    country_data = df.dropna(subset=["Country"]).copy()

    if country_data.empty:
        return pd.DataFrame(
            columns=[
                "Country",
                "Revenue",
                "Orders",
                "Customers",
                "AverageOrderValue",
            ]
        )

    summary = (
        country_data.groupby(
            "Country",
            observed=True,
            as_index=False,
        )
        .agg(
            Revenue=("TotalPrice", "sum"),
            Orders=("Invoice", "nunique"),
            Customers=("Customer ID", "nunique"),
        )
    )

    summary = summary[summary["Orders"] >= minimum_orders].copy()

    if summary.empty:
        return summary

    summary["AverageOrderValue"] = (
        summary["Revenue"]
        / summary["Orders"].replace(0, pd.NA)
    ).fillna(0)

    return summary.sort_values("Revenue", ascending=False)


@st.cache_data(
    show_spinner=False,
    max_entries=8,
)
def _customer_summary(
    df: pd.DataFrame,
    minimum_orders: int = 1,
) -> pd.DataFrame:
    """
    Summarize customer value and frequency once for customer analytics.
    """

    if df.empty or "Customer ID" not in df.columns:
        return pd.DataFrame(
            columns=[
                "Customer ID",
                "Revenue",
                "Orders",
                "UnitsSold",
                "AverageOrderValue",
            ]
        )

    customer_data = df.dropna(subset=["Customer ID"]).copy()

    if customer_data.empty:
        return pd.DataFrame(
            columns=[
                "Customer ID",
                "Revenue",
                "Orders",
                "UnitsSold",
                "AverageOrderValue",
            ]
        )

    summary = (
        customer_data.groupby(
            "Customer ID",
            observed=True,
            as_index=False,
        )
        .agg(
            Revenue=("TotalPrice", "sum"),
            Orders=("Invoice", "nunique"),
            UnitsSold=("Quantity", "sum"),
        )
    )

    summary["AverageOrderValue"] = (
        summary["Revenue"]
        / summary["Orders"].replace(0, pd.NA)
    ).fillna(0)

    return summary[summary["Orders"] >= minimum_orders].copy()


@st.cache_data(
    show_spinner=False,
    max_entries=8,
)
def _customer_segment_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build a lightweight customer segmentation table.
    """

    customers = _customer_summary(df)

    if customers.empty:
        return pd.DataFrame(
            columns=[
                "Customer ID",
                "Revenue",
                "Orders",
                "UnitsSold",
                "AverageOrderValue",
                "Segment",
            ]
        )

    revenue_median = customers["Revenue"].median()
    revenue_top_quartile = customers["Revenue"].quantile(0.75)
    order_median = customers["Orders"].median()
    order_top_quartile = customers["Orders"].quantile(0.75)

    customers = customers.copy()
    customers["Segment"] = "Occasional"

    customers.loc[
        (
            (customers["Orders"] >= order_top_quartile)
            & (customers["Revenue"] >= revenue_top_quartile)
        ),
        "Segment",
    ] = "Champions"

    customers.loc[
        (
            (customers["Orders"] >= order_median)
            & (customers["Revenue"] >= revenue_median)
            & (customers["Segment"] != "Champions")
        ),
        "Segment",
    ] = "Loyal"

    customers.loc[
        (
            (customers["Orders"] < order_median)
            & (customers["Revenue"] >= revenue_median)
        ),
        "Segment",
    ] = "High Value New"

    customers.loc[
        (
            (customers["Orders"] >= order_median)
            & (customers["Revenue"] < revenue_median)
        ),
        "Segment",
    ] = "Repeat Low Spend"

    return customers


@st.cache_data(
    show_spinner=False,
    max_entries=8,
)
def _segment_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count customers per segment and compute segment shares.
    """

    customers = _customer_segment_summary(df)

    if customers.empty:
        return pd.DataFrame(
            columns=[
                "Segment",
                "Customers",
                "Share",
            ]
        )

    counts = (
        customers.groupby(
            "Segment",
            observed=True,
            as_index=False,
        )
        .agg(Customers=("Customer ID", "nunique"))
        .sort_values("Customers", ascending=False)
    )

    counts["Share"] = (
        counts["Customers"]
        / counts["Customers"].sum()
        * 100
    )

    return counts


@st.cache_data(
    show_spinner=False,
    max_entries=8,
)
def _manager_health_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate executive health metrics from cached summaries.
    """

    customers = _customer_summary(df)
    monthly = _monthly_summary(df)

    if customers.empty:
        repeat_customer_rate = 0.0
        top_10_share = 0.0
        avg_customer_value = 0.0
    else:
        repeat_customer_rate = (
            customers[customers["Orders"] >= 2]["Customer ID"].nunique()
            / customers["Customer ID"].nunique()
            * 100
        )
        top_10_share = (
            customers.nlargest(10, "Revenue")["Revenue"].sum()
            / customers["Revenue"].sum()
            * 100
            if customers["Revenue"].sum() > 0
            else 0
        )
        avg_customer_value = customers["Revenue"].mean()

    if len(monthly) >= 2:
        previous_revenue = monthly.iloc[-2]["Revenue"]
        current_revenue = monthly.iloc[-1]["Revenue"]
        revenue_growth = (
            (current_revenue - previous_revenue)
            / previous_revenue
            * 100
            if previous_revenue != 0
            else 0
        )
    else:
        revenue_growth = 0.0

    return {
        "repeat_customer_rate": repeat_customer_rate,
        "top_10_share": top_10_share,
        "avg_customer_value": avg_customer_value,
        "revenue_growth": revenue_growth,
    }


@st.cache_data(
    show_spinner=False,
    max_entries=8,
)
def _order_value_by_country(
    df: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Build order-level values for the largest countries by revenue.
    """

    required_columns = [
        "Country",
        "Invoice",
        "TotalPrice",
    ]

    if df.empty or any(
        column not in df.columns
        for column in required_columns
    ):
        return pd.DataFrame(
            columns=[
                "Country",
                "Invoice",
                "OrderValue",
            ]
        )

    valid = df.dropna(
        subset=["Country", "Invoice"]
    ).copy()

    if valid.empty:
        return pd.DataFrame(
            columns=[
                "Country",
                "Invoice",
                "OrderValue",
            ]
        )

    top_countries = (
        valid.groupby(
            "Country",
            observed=True,
        )["TotalPrice"]
        .sum()
        .nlargest(top_n)
        .index
    )

    order_values = (
        valid[valid["Country"].isin(top_countries)]
        .groupby(
            ["Country", "Invoice"],
            observed=True,
            as_index=False,
        )
        .agg(OrderValue=("TotalPrice", "sum"))
    )

    return order_values


@st.cache_data(
    show_spinner=False,
    max_entries=8,
)
def _customer_recency_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build customer-level recency and monetary metrics.
    """

    if (
        df.empty
        or "Customer ID" not in df.columns
        or "InvoiceDate" not in df.columns
    ):
        return pd.DataFrame(
            columns=[
                "Customer ID",
                "Monetary",
                "RecencyDays",
                "Orders",
            ]
        )

    valid = df.dropna(
        subset=["Customer ID", "InvoiceDate"]
    ).copy()

    if valid.empty:
        return pd.DataFrame(
            columns=[
                "Customer ID",
                "Monetary",
                "RecencyDays",
                "Orders",
            ]
        )

    reference_date = valid["InvoiceDate"].max()

    summary = (
        valid.groupby(
            "Customer ID",
            observed=True,
            as_index=False,
        )
        .agg(
            Monetary=("TotalPrice", "sum"),
            LastPurchase=("InvoiceDate", "max"),
            Orders=("Invoice", "nunique"),
        )
    )

    summary["RecencyDays"] = (
        reference_date - summary["LastPurchase"]
    ).dt.days

    return summary


@st.cache_data(
    show_spinner=False,
    max_entries=8,
)
def _country_month_revenue(
    df: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Build a country-by-month revenue matrix for the largest markets.
    """

    required_columns = [
        "Country",
        "InvoiceMonth",
        "TotalPrice",
    ]

    if df.empty or any(
        column not in df.columns
        for column in required_columns
    ):
        return pd.DataFrame(
            columns=[
                "Country",
                "InvoiceMonth",
                "Revenue",
            ]
        )

    valid = df.dropna(
        subset=["Country", "InvoiceMonth"]
    ).copy()

    if valid.empty:
        return pd.DataFrame(
            columns=[
                "Country",
                "InvoiceMonth",
                "Revenue",
            ]
        )

    top_countries = (
        valid.groupby(
            "Country",
            observed=True,
        )["TotalPrice"]
        .sum()
        .nlargest(top_n)
        .index
    )

    return (
        valid[valid["Country"].isin(top_countries)]
        .groupby(
            ["Country", "InvoiceMonth"],
            observed=True,
            as_index=False,
        )
        .agg(Revenue=("TotalPrice", "sum"))
        .sort_values(["Country", "InvoiceMonth"])
    )


def _plot_chart(fig, chart_key: str):
    """
    Render a Plotly chart with consistent defaults.
    """

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=chart_key,
        config={
            "displaylogo": False,
            "responsive": True,
        },
    )


def _render_section_intro(
    title: str,
    description: str,
):
    with st.container(border=True):
        st.subheader(title)
        st.caption(description)


def _render_manager_health_snapshot(df: pd.DataFrame):
    metrics = _manager_health_metrics(df)

    with st.container(border=True):
        st.subheader("Manager Health Snapshot")
        st.caption(
            "A compact executive check on repeat behavior, customer concentration, "
            "customer value, and the latest revenue momentum."
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(
            "Repeat Customer Rate",
            f"{metrics['repeat_customer_rate']:.1f}%",
        )
        col2.metric(
            "Top 10 Customer Share",
            f"{metrics['top_10_share']:.1f}%",
        )
        col3.metric(
            "Avg Customer Value",
            f"{CURRENCY_SYMBOL} {metrics['avg_customer_value']:,.2f}",
        )
        col4.metric(
            "Latest Revenue Growth",
            f"{metrics['revenue_growth']:.1f}%",
        )


def _render_combined_commercial_trend(df: pd.DataFrame):
    monthly = _monthly_summary(df)

    _render_section_intro(
        "Commercial Performance Trend",
        "Revenue and order volume now share one full-width view so managers can "
        "see whether demand and monetization are moving together."
    )

    if monthly.empty:
        st.info("No monthly trend data is available.")
        return

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=monthly["Month"],
            y=monthly["Orders"],
            name="Orders",
            marker_color="#94a3b8",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Orders: %{y:,.0f}<extra></extra>"
            ),
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=monthly["Month"],
            y=monthly["Revenue"],
            name="Revenue",
            mode="lines+markers",
            line=dict(color="#2563eb", width=3),
            hovertemplate=(
                "<b>%{x}</b><br>"
                f"Revenue: {CURRENCY_SYMBOL} "
                "%{y:,.2f}<extra></extra>"
            ),
        ),
        secondary_y=True,
    )

    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1, x=0),
    )
    fig.update_yaxes(title_text="Orders", secondary_y=False)
    fig.update_yaxes(
        title_text=f"Revenue ({CURRENCY_SYMBOL})",
        secondary_y=True,
    )

    _plot_chart(fig, "combined_commercial_trend")


def _render_top_products(df: pd.DataFrame):
    summary = _product_summary(df)

    _render_section_intro(
        "Top Products by Revenue",
        "A fast ranking of the products driving the most money into the business."
    )

    if summary.empty:
        st.info("No product data is available.")
        return

    chart_data = summary.sort_values("Revenue", ascending=True)

    fig = px.bar(
        chart_data,
        x="Revenue",
        y="Description",
        orientation="h",
        labels={
            "Revenue": f"Revenue ({CURRENCY_SYMBOL})",
            "Description": "Product",
        },
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>"
            f"Revenue: {CURRENCY_SYMBOL} %{{x:,.2f}}<extra></extra>"
        )
    )

    _plot_chart(fig, "top_products_by_revenue")


def _render_average_order_value_trend(df: pd.DataFrame):
    monthly = _monthly_summary(df)

    _render_section_intro(
        "Average Order Value Trend",
        "This is a direct manager signal for pricing quality, basket size, and "
        "upsell effectiveness over time."
    )

    if monthly.empty:
        st.info("No AOV trend data is available.")
        return

    fig = px.line(
        monthly,
        x="Month",
        y="AverageOrderValue",
        markers=True,
        labels={
            "Month": "Month",
            "AverageOrderValue": f"AOV ({CURRENCY_SYMBOL})",
        },
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        hovermode="x unified",
    )
    fig.update_traces(
        line=dict(color="#f97316", width=3),
        hovertemplate=(
            "<b>%{x}</b><br>"
            f"AOV: {CURRENCY_SYMBOL} %{{y:,.2f}}<extra></extra>"
        ),
    )

    _plot_chart(fig, "average_order_value_trend")


def _render_monthly_value_mix(df: pd.DataFrame):
    monthly = _monthly_summary(df)

    _render_section_intro(
        "Monthly Order Value Mix",
        "A bivariate operating view that compares order count against average "
        "order value while bubble size represents revenue."
    )

    if monthly.empty:
        st.info("No monthly mix data is available.")
        return

    fig = px.scatter(
        monthly,
        x="Orders",
        y="AverageOrderValue",
        size="Revenue",
        color="Customers",
        text="Month",
        labels={
            "Orders": "Orders",
            "AverageOrderValue": f"Average Order Value ({CURRENCY_SYMBOL})",
            "Customers": "Active Customers",
            "Revenue": f"Revenue ({CURRENCY_SYMBOL})",
        },
    )
    fig.update_traces(
        textposition="top center",
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Orders: %{x:,.0f}<br>"
            f"AOV: {CURRENCY_SYMBOL} %{{y:,.2f}}<br>"
            "Active customers: %{marker.color:,.0f}<br>"
            f"Revenue: {CURRENCY_SYMBOL} %{{marker.size:,.2f}}<extra></extra>"
        ),
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))

    _plot_chart(fig, "monthly_value_mix")


def _render_country_performance(df: pd.DataFrame):
    summary = _country_summary(df)

    _render_section_intro(
        "Market Performance by Country",
        "A multivariate market view for comparing country-level demand, revenue, "
        "customer base, and average order value."
    )

    if summary.empty:
        st.info("No country-level data meets the minimum activity threshold.")
        return

    chart_data = summary.head(20).copy()

    fig = px.scatter(
        chart_data,
        x="Orders",
        y="Revenue",
        size="Customers",
        color="AverageOrderValue",
        text="Country",
        labels={
            "Orders": "Orders",
            "Revenue": f"Revenue ({CURRENCY_SYMBOL})",
            "Customers": "Customers",
            "AverageOrderValue": f"Average Order Value ({CURRENCY_SYMBOL})",
        },
    )
    fig.update_traces(
        textposition="top center",
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Orders: %{x:,.0f}<br>"
            f"Revenue: {CURRENCY_SYMBOL} %{{y:,.2f}}<br>"
            "Customers: %{marker.size:,.0f}<br>"
            f"AOV: {CURRENCY_SYMBOL} %{{marker.color:,.2f}}<extra></extra>"
        ),
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))

    _plot_chart(fig, "country_performance_scatter")


def _render_product_portfolio(df: pd.DataFrame):
    summary = _product_summary(df, top_n=25)

    _render_section_intro(
        "Product Portfolio Balance",
        "Compare volume against revenue for leading products to see whether the "
        "catalog is driven by scale, margin, or a healthy balance of both."
    )

    if summary.empty:
        st.info("No product portfolio data is available.")
        return

    fig = px.scatter(
        summary,
        x="UnitsSold",
        y="Revenue",
        size="Orders",
        color="Revenue",
        text="Description",
        labels={
            "UnitsSold": "Units Sold",
            "Revenue": f"Revenue ({CURRENCY_SYMBOL})",
            "Orders": "Orders",
        },
    )
    fig.update_traces(
        textposition="top center",
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Units sold: %{x:,.0f}<br>"
            f"Revenue: {CURRENCY_SYMBOL} %{{y:,.2f}}<br>"
            "Orders: %{marker.size:,.0f}<extra></extra>"
        ),
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))

    _plot_chart(fig, "product_portfolio_scatter")


def _render_customer_segments_count(df: pd.DataFrame):
    segments = _segment_counts(df)

    _render_section_intro(
        "Number of Customers by Segment",
        "Customer segmentation groups the base into manager-friendly buckets so "
        "leadership can see whether growth is coming from healthy repeat demand."
    )

    if segments.empty:
        st.info("No customer segmentation data is available.")
        return

    fig = px.bar(
        segments.sort_values("Customers", ascending=False),
        x="Segment",
        y="Customers",
        color="Segment",
        labels={
            "Segment": "Customer Segment",
            "Customers": "Number of Customers",
        },
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Customers: %{y:,.0f}<extra></extra>"
        )
    )

    _plot_chart(fig, "customer_segments_count")


def _render_customer_segment_distribution(df: pd.DataFrame):
    segments = _segment_counts(df)

    _render_section_intro(
        "Customer Segment Distribution",
        "The distribution view makes it easy to judge whether the customer mix is "
        "balanced or overly dependent on low-frequency shoppers."
    )

    if segments.empty:
        st.info("No customer segment distribution data is available.")
        return

    fig = px.pie(
        segments,
        names="Segment",
        values="Customers",
        hole=0.55,
    )
    fig.update_traces(
        textinfo="percent+label",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Customers: %{value:,.0f}<br>"
            "Share: %{percent}<extra></extra>"
        ),
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))

    _plot_chart(fig, "customer_segment_distribution")


def _render_customer_value_map(df: pd.DataFrame):
    customers = _customer_segment_summary(df)

    _render_section_intro(
        "Repeat Customer Value Map",
        "Spot the customers who combine repeat buying with high value and compare "
        "them against lighter or lower-spend segments."
    )

    if customers.empty:
        st.info("No customer-level data is available for value mapping.")
        return

    chart_data = customers.nlargest(200, "Revenue").copy()
    chart_data["CustomerLabel"] = chart_data["Customer ID"].astype(str)

    fig = px.scatter(
        chart_data,
        x="Orders",
        y="Revenue",
        size="UnitsSold",
        color="Segment",
        hover_name="CustomerLabel",
        custom_data=["Segment"],
        labels={
            "Orders": "Orders",
            "Revenue": f"Revenue ({CURRENCY_SYMBOL})",
            "UnitsSold": "Units Sold",
            "Segment": "Customer Segment",
        },
    )
    fig.update_traces(
        hovertemplate=(
            "<b>Customer %{hovertext}</b><br>"
            "Orders: %{x:,.0f}<br>"
            f"Revenue: {CURRENCY_SYMBOL} %{{y:,.2f}}<br>"
            "Units sold: %{marker.size:,.0f}<br>"
            "Segment: %{customdata[0]}<extra></extra>"
        )
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))

    _plot_chart(fig, "customer_value_map")


def _render_quantity_price_scatter(df: pd.DataFrame):
    sample_size = 3000

    _render_section_intro(
        "Quantity vs Price Relationship",
        "This numeric-vs-numeric view shows whether items tend to sell as "
        "low-price bulk products or high-price low-volume products. Log scales "
        "make the skewed retail data much easier to interpret."
    )

    required_columns = [
        "Quantity",
        "Price",
        "Country",
    ]

    if any(
        column not in df.columns
        for column in required_columns
    ):
        st.info("The current dataset does not support this chart.")
        return

    chart_data = df.dropna(
        subset=["Quantity", "Price", "Country"]
    ).copy()

    chart_data = chart_data[
        (chart_data["Quantity"] > 0)
        & (chart_data["Price"] > 0)
    ]

    if chart_data.empty:
        st.info("No quantity-price data is available.")
        return

    if len(chart_data) > sample_size:
        chart_data = chart_data.sample(
            n=sample_size,
            random_state=42,
        )

    fig = px.scatter(
        chart_data,
        x="Quantity",
        y="Price",
        color="Country",
        hover_data=["Description"],
        labels={
            "Quantity": "Quantity",
            "Price": f"Unit Price ({CURRENCY_SYMBOL})",
        },
    )
    fig.update_xaxes(type="log")
    fig.update_yaxes(type="log")
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    fig.update_traces(
        hovertemplate=(
            "Quantity: %{x:,.0f}<br>"
            f"Price: {CURRENCY_SYMBOL} %{{y:,.2f}}<br>"
            "Country: %{marker.color}<extra></extra>"
        )
    )

    _plot_chart(fig, "quantity_price_scatter")


def _render_customer_orders_revenue(df: pd.DataFrame):
    customers = _customer_segment_summary(df)

    _render_section_intro(
        "Orders vs Revenue per Customer",
        "Each customer becomes one dot, making it easy to spot one-time buyers, "
        "repeat mid-tier customers, and top-right VIP accounts."
    )

    if customers.empty:
        st.info("No customer-level data is available.")
        return

    chart_data = customers.nlargest(250, "Revenue").copy()
    chart_data["CustomerLabel"] = chart_data["Customer ID"].astype(str)

    fig = px.scatter(
        chart_data,
        x="Orders",
        y="Revenue",
        size="UnitsSold",
        color="Segment",
        hover_name="CustomerLabel",
        custom_data=["AverageOrderValue", "Segment"],
        labels={
            "Orders": "Number of Orders",
            "Revenue": f"Total Revenue ({CURRENCY_SYMBOL})",
            "UnitsSold": "Units Sold",
            "Segment": "Customer Segment",
        },
    )
    fig.update_traces(
        hovertemplate=(
            "<b>Customer %{hovertext}</b><br>"
            "Orders: %{x:,.0f}<br>"
            f"Revenue: {CURRENCY_SYMBOL} %{{y:,.2f}}<br>"
            "Units sold: %{marker.size:,.0f}<br>"
            f"AOV: {CURRENCY_SYMBOL} %{{customdata[0]:,.2f}}<br>"
            "Segment: %{customdata[1]}<extra></extra>"
        )
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))

    _plot_chart(fig, "customer_orders_revenue_scatter")


def _render_customer_aov_frequency(df: pd.DataFrame):
    customers = _customer_segment_summary(df)

    _render_section_intro(
        "Average Order Value vs Order Frequency",
        "This separates customers who buy often with small baskets from those "
        "who buy rarely but spend a lot per order, which points to different "
        "marketing and retention actions."
    )

    if customers.empty:
        st.info("No customer AOV-frequency data is available.")
        return

    chart_data = customers.nlargest(250, "Revenue").copy()
    chart_data["CustomerLabel"] = chart_data["Customer ID"].astype(str)

    fig = px.scatter(
        chart_data,
        x="Orders",
        y="AverageOrderValue",
        size="Revenue",
        color="Segment",
        hover_name="CustomerLabel",
        custom_data=["Revenue", "Segment"],
        labels={
            "Orders": "Order Frequency",
            "AverageOrderValue": f"AOV ({CURRENCY_SYMBOL})",
            "Revenue": f"Revenue ({CURRENCY_SYMBOL})",
            "Segment": "Customer Segment",
        },
    )
    fig.update_traces(
        hovertemplate=(
            "<b>Customer %{hovertext}</b><br>"
            "Order frequency: %{x:,.0f}<br>"
            f"AOV: {CURRENCY_SYMBOL} %{{y:,.2f}}<br>"
            f"Revenue: {CURRENCY_SYMBOL} %{{customdata[0]:,.2f}}<br>"
            "Segment: %{customdata[1]}<extra></extra>"
        )
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))

    _plot_chart(fig, "customer_aov_frequency_scatter")


def _render_recency_monetary(df: pd.DataFrame):
    customers = _customer_recency_summary(df)

    _render_section_intro(
        "Recency vs Monetary Value",
        "This RFM-style plot highlights recently active valuable customers and "
        "valuable customers who are slipping away and may need re-engagement."
    )

    if customers.empty:
        st.info("No recency-monetary data is available.")
        return

    chart_data = customers.nlargest(250, "Monetary").copy()
    chart_data["CustomerLabel"] = chart_data["Customer ID"].astype(str)

    fig = px.scatter(
        chart_data,
        x="RecencyDays",
        y="Monetary",
        size="Orders",
        color="Orders",
        hover_name="CustomerLabel",
        labels={
            "RecencyDays": "Days Since Last Purchase",
            "Monetary": f"Total Spend ({CURRENCY_SYMBOL})",
            "Orders": "Number of Orders",
        },
    )
    fig.update_traces(
        hovertemplate=(
            "<b>Customer %{hovertext}</b><br>"
            "Days since last purchase: %{x:,.0f}<br>"
            f"Total spend: {CURRENCY_SYMBOL} %{{y:,.2f}}<br>"
            "Orders: %{marker.size:,.0f}<extra></extra>"
        )
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))

    _plot_chart(fig, "recency_monetary_scatter")


def _render_country_month_heatmap(df: pd.DataFrame):
    heatmap_data = _country_month_revenue(df)

    _render_section_intro(
        "Country by Month Revenue Heatmap",
        "A dense market-performance view that shows which countries are gaining "
        "or fading over time without needing several separate charts."
    )

    if heatmap_data.empty:
        st.info("No country-month revenue data is available.")
        return

    pivot = heatmap_data.pivot(
        index="Country",
        columns="InvoiceMonth",
        values="Revenue",
    ).fillna(0)

    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale="Blues",
        labels={
            "x": "Month",
            "y": "Country",
            "color": f"Revenue ({CURRENCY_SYMBOL})",
        },
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))

    _plot_chart(fig, "country_month_revenue_heatmap")


def _render_country_order_value_box(df: pd.DataFrame):
    chart_data = _order_value_by_country(df)

    _render_section_intro(
        "Order Value Distribution by Country",
        "This shows order-size distribution by market, helping reveal whether a "
        "country is driven by many small baskets or fewer wholesale-sized orders."
    )

    if chart_data.empty:
        st.info("No country order-value distribution data is available.")
        return

    fig = px.box(
        chart_data,
        x="Country",
        y="OrderValue",
        points="outliers",
        labels={
            "Country": "Country",
            "OrderValue": f"Order Value ({CURRENCY_SYMBOL})",
        },
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"
            f"Order value: {CURRENCY_SYMBOL} %{{y:,.2f}}<extra></extra>"
        )
    )

    _plot_chart(fig, "country_order_value_box")


PRESET_CONFIG = {
    "Executive Overview": [
        _render_manager_health_snapshot,
        _render_combined_commercial_trend,
        _render_top_products,
        _render_customer_orders_revenue,
        _render_country_month_heatmap,
        _render_country_performance,
    ],
    "Customer Intelligence": [
        _render_manager_health_snapshot,
        _render_customer_segments_count,
        _render_customer_segment_distribution,
        _render_customer_orders_revenue,
        _render_customer_aov_frequency,
        _render_recency_monetary,
        _render_average_order_value_trend,
    ],
    "Product And Market": [
        _render_combined_commercial_trend,
        _render_top_products,
        _render_product_portfolio,
        _render_quantity_price_scatter,
        _render_country_order_value_box,
        _render_country_month_heatmap,
        _render_country_performance,
    ],
    "Full Suite": [
        _render_manager_health_snapshot,
        _render_combined_commercial_trend,
        _render_top_products,
        _render_monthly_value_mix,
        _render_average_order_value_trend,
        _render_product_portfolio,
        _render_quantity_price_scatter,
        _render_country_performance,
        _render_country_order_value_box,
        _render_country_month_heatmap,
        _render_customer_segments_count,
        _render_customer_segment_distribution,
        _render_customer_orders_revenue,
        _render_customer_aov_frequency,
        _render_recency_monetary,
    ],
}


def render_charts(df: pd.DataFrame):
    """
    Render preset-based analytics with full-width chart rows.
    """

    if df.empty:
        st.warning("No sales data is available for the selected filters.")
        return

    required_columns = [
        "Invoice",
        "TotalPrice",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        st.warning(
            "The following columns are required for sales charts: "
            f"{missing_columns}"
        )
        return

    st.subheader("Sales Analytics Explorer")
    st.caption(
        "Instead of loading one chart at a time, this explorer uses smart presets. "
        "Each preset loads a related bundle of full-width analyses so the user gets "
        "context-rich insight with fewer clicks and less wasted computation."
    )

    preset = st.radio(
        "Choose an analytics view",
        options=list(PRESET_CONFIG.keys()),
        horizontal=True,
    )

    for render_function in PRESET_CONFIG[preset]:
        render_function(df)
