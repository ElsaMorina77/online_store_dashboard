import streamlit as st


def render_revenue_by_month(df):
    st.subheader("Revenue by Month")

    monthly_revenue = (
        df.groupby("InvoiceMonth")["TotalPrice"]
        .sum()
        .reset_index()
        .sort_values("InvoiceMonth")
    )

    st.line_chart(
        monthly_revenue,
        x="InvoiceMonth",
        y="TotalPrice"
    )


def render_orders_by_month(df):
    st.subheader("Orders by Month")

    monthly_orders = (
        df.groupby("InvoiceMonth")["Invoice"]
        .nunique()
        .reset_index()
        .sort_values("InvoiceMonth")
    )

    st.line_chart(
        monthly_orders,
        x="InvoiceMonth",
        y="Invoice"
    )


def render_customers_by_month(df):
    st.subheader("Customers by Month")

    monthly_customers = (
        df.groupby("InvoiceMonth")["Customer ID"]
        .nunique()
        .reset_index()
        .sort_values("InvoiceMonth")
    )

    st.line_chart(
        monthly_customers,
        x="InvoiceMonth",
        y="Customer ID"
    )


def render_average_order_value_by_month(df):
    st.subheader("Average Order Value by Month")

    monthly_aov = (
        df.groupby("InvoiceMonth")
        .agg(
            revenue=("TotalPrice", "sum"),
            orders=("Invoice", "nunique")
        )
        .reset_index()
        .sort_values("InvoiceMonth")
    )

    monthly_aov["AverageOrderValue"] = (
        monthly_aov["revenue"] / monthly_aov["orders"]
    )

    st.line_chart(
        monthly_aov,
        x="InvoiceMonth",
        y="AverageOrderValue"
    )


def render_top_products_by_revenue(df, top_n=10):
    st.subheader("Top 10 Products by Revenue")

    top_products = (
        df.groupby("Description")["TotalPrice"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )

    st.bar_chart(
        top_products,
        x="Description",
        y="TotalPrice"
    )


def render_top_countries_by_revenue(df, top_n=10):
    st.subheader("Top 10 Countries by Revenue")

    top_countries = (
        df.groupby("Country")["TotalPrice"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )

    st.bar_chart(
        top_countries,
        x="Country",
        y="TotalPrice"
    )


def render_charts(df):
    st.header("Monthly Performance Overview")

    if df.empty:
        st.info("No data available for the selected filters.")
        return

    required_columns = [
        "InvoiceMonth",
        "TotalPrice",
        "Invoice",
        "Customer ID",
        "Description",
        "Country",
    ]

    missing_columns = [
        column for column in required_columns if column not in df.columns]

    if missing_columns:
        st.warning(f"Missing columns needed for charts: {missing_columns}")
        return

    col1, col2 = st.columns(2)

    with col1:
        render_revenue_by_month(df)

    with col2:
        render_orders_by_month(df)

    col3, col4 = st.columns(2)

    with col3:
        render_customers_by_month(df)

    with col4:
        render_average_order_value_by_month(df)

    st.header("Customer & Product Performance")

    col5, col6 = st.columns(2)

    with col5:
        render_top_products_by_revenue(df)

    with col6:
        render_top_countries_by_revenue(df)
