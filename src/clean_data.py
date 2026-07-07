import streamlit as st


@st.cache_data
def clean_data(df):
    df = df.copy()

    # Make StockCode consistent (fix Streamlit Arrow error)
    if "StockCode" in df.columns:
        df["StockCode"] = df["StockCode"].astype(str)

    df = df.drop_duplicates()

    df = df[df["Price"] > 0]
    df = df[df["Quantity"] > 0]
    df = df[df["Quantity"] <= 10000]

    non_products = ["M", "AMAZONFEE", "B", "ADJUST", "POST", "DOT", "84016"]
    df = df[~df["StockCode"].isin(non_products)]

    return df