import streamlit as st


NON_PRODUCT_STOCK_CODES = [
    "M",
    "AMAZONFEE",
    "B",
    "ADJUST",
    "POST",
    "DOT",
    "84016",
]


@st.cache_data(max_entries=4)
def clean_data(df):
    """
    Clean completed sales transactions for the main dashboard.

    Cancellation transactions with negative quantities are excluded
    here and analysed separately in the cancellation dashboard.
    """

    df = df.copy()

    required_columns = [
        "StockCode",
        "Price",
        "Quantity",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns for data cleaning: "
            f"{missing_columns}"
        )

    # Ensure consistent StockCode type.
    df["StockCode"] = (
        df["StockCode"]
        .astype(str)
        .str.strip()
    )

    # Remove exact duplicate transactions.
    df = df.drop_duplicates()

    # Keep valid completed sales only.
    df = df[
        (df["Price"] > 0)
        & (df["Quantity"] > 0)
        & (df["Quantity"] <= 10000)
    ].copy()

    # Remove administrative and non-product StockCodes.
    df = df[
        ~df["StockCode"].isin(
            NON_PRODUCT_STOCK_CODES
        )
    ]

    return df
