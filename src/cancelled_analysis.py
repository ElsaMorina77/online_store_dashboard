import pandas as pd
import streamlit as st
import plotly.express as px


def render_cancelled_dashboard(df_cancel_source):
    st.markdown("---")
    st.header("Cancellation Performance Overview")

    st.info(
        "The cancellation analysis complements the overall sales dashboard by evaluating "
        "cancelled transactions alongside sales performance. While cancellations account "
        "for a relatively small share of overall revenue, they are concentrated within a "
        "limited number of products and markets."
    )

    df = df_cancel_source.copy()

    df["StockCode"] = df["StockCode"].astype(str)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Revenue"] = df["Quantity"] * df["Price"]
    df["IsCancelled"] = df["Invoice"].astype(str).str.startswith("C")
    df["Month"] = df["InvoiceDate"].dt.to_period("M").astype(str)

    non_products = ["M", "AMAZONFEE", "B", "ADJUST", "POST", "DOT", "84016"]

    # Cleaned sales data, aligned with Elsa's main dashboard logic
    sales_df = df[
        (~df["IsCancelled"])
        & (df["Price"] > 0)
        & (df["Quantity"] > 0)
        & (df["Quantity"] <= 10000)
    ].copy()

    sales_df = sales_df.drop_duplicates()
    sales_df = sales_df[~sales_df["StockCode"].isin(non_products)]

    # Cancelled transactions from original dataset
    cancelled = df[df["IsCancelled"]].copy()
    cancelled["Cancelled Revenue"] = cancelled["Revenue"].abs()

    total_sales_orders = sales_df["Invoice"].nunique()
    cancelled_orders = cancelled["Invoice"].nunique()

    cancellation_rate = (
        cancelled_orders / (total_sales_orders + cancelled_orders) * 100
        if (total_sales_orders + cancelled_orders)
        else 0
    )

    net_sales_revenue = sales_df["Revenue"].sum()
    cancelled_revenue = cancelled["Cancelled Revenue"].sum()

    cancelled_revenue_share = (
        cancelled_revenue / (net_sales_revenue + cancelled_revenue) * 100
        if (net_sales_revenue + cancelled_revenue)
        else 0
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales Orders", f"{total_sales_orders:,}")
    col2.metric("Cancelled Orders", f"{cancelled_orders:,}")
    col3.metric("Cancellation Rate", f"{cancellation_rate:.2f}%")

    col4, col5, col6 = st.columns(3)
    col4.metric("Net Sales Revenue", f"${net_sales_revenue:,.2f}")
    col5.metric("Cancelled Revenue", f"${cancelled_revenue:,.2f}")
    col6.metric("Cancelled Revenue Share", f"{cancelled_revenue_share:.2f}%")

    monthly_sales = (
        sales_df.groupby("Month")["Invoice"]
        .nunique()
        .reset_index(name="Sales Orders")
    )

    monthly_cancelled = (
        cancelled.groupby("Month")["Invoice"]
        .nunique()
        .reset_index(name="Cancelled Orders")
    )

    monthly = monthly_sales.merge(monthly_cancelled, on="Month", how="outer")
    monthly[["Sales Orders", "Cancelled Orders"]] = monthly[
        ["Sales Orders", "Cancelled Orders"]
    ].fillna(0)

    monthly["Cancellation Rate (%)"] = (
        monthly["Cancelled Orders"]
        / (monthly["Sales Orders"] + monthly["Cancelled Orders"])
        * 100
    )

    monthly = monthly.sort_values("Month")

    fig_month = px.line(
        monthly,
        x="Month",
        y="Cancellation Rate (%)",
        markers=True,
        title="Monthly Cancellation Rate",
    )

    fig_month.update_layout(
        xaxis_title="Month",
        yaxis_title="Cancellation Rate (%)",
    )

    st.plotly_chart(fig_month, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        product_impact = (
            cancelled.groupby("Description")["Cancelled Revenue"]
            .sum()
            .reset_index()
            .sort_values("Cancelled Revenue", ascending=False)
            .head(10)
            .sort_values("Cancelled Revenue")
        )

        fig_products = px.bar(
            product_impact,
            x="Cancelled Revenue",
            y="Description",
            orientation="h",
            title="Top Products by Cancelled Revenue",
            labels={
                "Cancelled Revenue": "Cancelled Revenue ($)",
                "Description": "Product",
            },
        )

        st.plotly_chart(fig_products, use_container_width=True)

    with col_b:
        country_sales = (
            sales_df.groupby("Country")["Invoice"]
            .nunique()
            .reset_index(name="Sales Orders")
        )

        country_cancelled = (
            cancelled.groupby("Country")["Invoice"]
            .nunique()
            .reset_index(name="Cancelled Orders")
        )

        country_rate = country_sales.merge(country_cancelled, on="Country", how="outer")
        country_rate[["Sales Orders", "Cancelled Orders"]] = country_rate[
            ["Sales Orders", "Cancelled Orders"]
        ].fillna(0)

        country_rate["Total Activity"] = (
            country_rate["Sales Orders"] + country_rate["Cancelled Orders"]
        )

        country_rate = country_rate[country_rate["Total Activity"] >= 100]

        country_rate["Cancellation Rate (%)"] = (
            country_rate["Cancelled Orders"]
            / country_rate["Total Activity"]
            * 100
        )

        country_rate = (
            country_rate.sort_values("Cancellation Rate (%)", ascending=False)
            .head(10)
            .sort_values("Cancellation Rate (%)")
        )

        fig_country = px.bar(
            country_rate,
            x="Cancellation Rate (%)",
            y="Country",
            orientation="h",
            title="Countries with Highest Cancellation Rate",
        )

        st.plotly_chart(fig_country, use_container_width=True)

    st.success(
        "Key Insight: Although cancellations represent a relatively small proportion of "
        "total revenue, a limited number of products and countries account for most "
        "cancelled revenue. Focusing operational improvements on these areas is likely "
        "to deliver the greatest reduction in financial losses."
    )

    st.warning(
        "Final Recommendation: Prioritize investigation of the products with the highest "
        "cancelled revenue and the countries with the highest cancellation rate. This will "
        "help identify whether cancellations are linked to product quality, stock accuracy, "
        "customer expectations, delivery issues, or operational processes."
    )