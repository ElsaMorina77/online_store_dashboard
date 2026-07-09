import io

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


# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Online Store Executive Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Online Store Executive Dashboard")

st.caption(
    "Interactive analysis of sales performance, "
    "customers, products, markets, and cancellations."
)


# ============================================================
# CACHED DATA FUNCTIONS
# ============================================================

@st.cache_data(show_spinner=False)
def load_uploaded_file(
    file_bytes: bytes,
    file_name: str,
) -> pd.DataFrame:
    """
    Load an uploaded CSV or Excel file from cached bytes.

    Passing bytes instead of the Streamlit UploadedFile object
    gives Streamlit a stable value that can be hashed and cached.
    """

    file_object = io.BytesIO(file_bytes)

    # Some existing load_data() implementations use .name
    # to determine the file extension.
    file_object.name = file_name

    return load_data(file_object)


@st.cache_data(show_spinner=False)
def load_url_data(url: str) -> pd.DataFrame:
    """
    Load data from a URL and cache the result.
    """

    return load_data(url)


@st.cache_data(show_spinner=False)
def prepare_dashboard_data(
    raw_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare both:
    1. Clean sales data.
    2. Original transaction data for cancellation analysis.

    This entire preprocessing stage is cached.
    """

    # Keep original transactions because clean_data()
    # removes cancellations with negative quantities.
    df_original = raw_df.copy()

    # Main sales dataframe
    df_sales = clean_data(raw_df.copy())
    df_sales = prepare_data(df_sales)

    # Raw transaction dataframe prepared for
    # cancellation analysis.
    df_cancel_source = prepare_data(
        df_original
    )

    return df_sales, df_cancel_source


@st.cache_data(show_spinner=False)
def filter_by_countries(
    df: pd.DataFrame,
    selected_countries: tuple,
) -> pd.DataFrame:
    """
    Filter dataframe by selected countries.
    """

    if not selected_countries:
        return df.iloc[0:0]

    return df[
        df["Country"].isin(selected_countries)
    ]


@st.cache_data(show_spinner=False)
def filter_by_months(
    df: pd.DataFrame,
    selected_months: tuple,
) -> pd.DataFrame:
    """
    Filter dataframe by selected months.
    """

    if not selected_months:
        return df.iloc[0:0]

    return df[
        df["InvoiceMonth"].isin(selected_months)
    ]


@st.cache_data(show_spinner=False)
def filter_by_products(
    df: pd.DataFrame,
    selected_products: tuple,
) -> pd.DataFrame:
    """
    Filter dataframe by selected products.
    """

    if not selected_products:
        return df

    return df[
        df["Description"].isin(
            selected_products
        )
    ]


@st.cache_data(show_spinner=False)
def create_csv_download(
    df: pd.DataFrame,
) -> bytes:
    """
    Convert filtered dataframe to CSV only when needed.
    """

    return df.to_csv(
        index=False
    ).encode("utf-8")


# ============================================================
# 1. DATA INPUT
# ============================================================

df = None

option = st.sidebar.radio(
    "Data Source",
    [
        "Upload File",
        "URL",
    ],
)


try:

    if option == "Upload File":

        file = st.file_uploader(
            "Upload CSV or Excel",
            type=[
                "csv",
                "xlsx",
                "xls",
            ],
        )

        if file is not None:

            with st.spinner(
                "Loading data..."
            ):

                file_bytes = file.getvalue()

                df = load_uploaded_file(
                    file_bytes=file_bytes,
                    file_name=file.name,
                )

    elif option == "URL":

        url = st.text_input(
            "Enter direct CSV or Excel URL"
        )

        if url:

            with st.spinner(
                "Loading data from URL..."
            ):

                df = load_url_data(url)


except Exception as error:

    st.error(
        f"Could not load the data: {error}"
    )

    st.stop()


# ============================================================
# 2. STOP IF NO DATA
# ============================================================

if df is None:

    st.info(
        "Please upload a CSV/Excel file "
        "or provide a direct data URL."
    )

    st.stop()


# ============================================================
# 3. PREPARE DATA
# ============================================================

try:

    with st.spinner(
        "Preparing dashboard data..."
    ):

        df_sales, df_cancel_source = (
            prepare_dashboard_data(df)
        )


except Exception as error:

    st.error(
        f"Could not prepare the data: {error}"
    )

    st.stop()


# ============================================================
# 4. FILTERS
# ============================================================

st.sidebar.header("Filters")


# ---------------------------------
# Country filter
# ---------------------------------

selected_countries = []

if "Country" in df_sales.columns:

    country_options = get_unique_countries(
        df_sales
    )

    selected_countries = (
        st.sidebar.multiselect(
            "Select Country",
            options=country_options,
            default=country_options,
        )
    )

    selected_countries_tuple = tuple(
        selected_countries
    )

    df_sales = filter_by_countries(
        df_sales,
        selected_countries_tuple,
    )

    df_cancel_source = (
        filter_by_countries(
            df_cancel_source,
            selected_countries_tuple,
        )
    )


# Keep a sales copy after country filtering but
# before month filtering for previous-period KPI deltas.
df_before_month_filter = df_sales.copy()


# ---------------------------------
# Month filter
# ---------------------------------

selected_months = []

if "InvoiceMonth" in df_sales.columns:

    month_options = get_unique_months(
        df_sales
    )

    selected_months = (
        st.sidebar.multiselect(
            "Select Month",
            options=month_options,
            default=month_options,
        )
    )

    selected_months_tuple = tuple(
        selected_months
    )

    df_sales = filter_by_months(
        df_sales,
        selected_months_tuple,
    )

    df_cancel_source = filter_by_months(
        df_cancel_source,
        selected_months_tuple,
    )


# ---------------------------------
# Product filter
# ---------------------------------

selected_products = []

if (
    "Description" in df_sales.columns
    and not df_sales.empty
):

    product_options = get_top_products(
        df_sales
    )

    selected_products = (
        st.sidebar.multiselect(
            "Select Top Products",
            options=product_options,
        )
    )

    if selected_products:

        selected_products_tuple = tuple(
            selected_products
        )

        df_sales = filter_by_products(
            df_sales,
            selected_products_tuple,
        )

        df_before_month_filter = (
            filter_by_products(
                df_before_month_filter,
                selected_products_tuple,
            )
        )

        df_cancel_source = (
            filter_by_products(
                df_cancel_source,
                selected_products_tuple,
            )
        )


# ============================================================
# 5. STOP IF FILTERS RETURN NO SALES DATA
# ============================================================

if df_sales.empty:

    st.warning(
        "No sales data matches the selected filters."
    )

    st.stop()


# ============================================================
# 6. DATA STATUS
# ============================================================

st.caption(
    f"Displaying {len(df_sales):,} sales rows "
    f"from {len(df):,} original transaction rows."
)


# ============================================================
# 7. KPI DASHBOARD
# ============================================================

previous_df = get_previous_period_df(
    df_before_month_filter,
    selected_months,
)

kpis, deltas = calculate_kpis_with_delta(
    df_sales,
    previous_df,
)


st.subheader(
    "Key Performance Indicators"
)


render_kpi_cards(
    [
        {
            "label": "Total Revenue",
            "value": (
                f"£{kpis['total_revenue']:,.2f}"
            ),
            "icon": "💷",
            "accent": "#6366f1",
            "delta": deltas[
                "total_revenue"
            ],
        },
        {
            "label": "Total Orders",
            "value": (
                f"{kpis['total_orders']:,}"
            ),
            "icon": "🛒",
            "accent": "#22c55e",
            "delta": deltas[
                "total_orders"
            ],
        },
        {
            "label": "Customers",
            "value": (
                f"{kpis['total_customers']:,}"
            ),
            "icon": "👥",
            "accent": "#f59e0b",
            "delta": deltas[
                "total_customers"
            ],
        },
        {
            "label": "Average Order Value",
            "value": (
                f"£{kpis['average_order_value']:,.2f}"
            ),
            "icon": "💳",
            "accent": "#ec4899",
            "delta": deltas[
                "average_order_value"
            ],
        },
    ]
)


# ============================================================
# 8. SALES ANALYTICS
# ============================================================

render_charts(df_sales)


# ============================================================
# 9. CANCELLATION ANALYTICS
# ============================================================

if not df_cancel_source.empty:
    render_cancelled_dashboard(df_cancel_source)
else:
    st.info("No cancellation data matches the selected filters.")


# ============================================================
# 10. RAW DATA
# ============================================================

st.divider()


with st.expander(
    "View Filtered Sales Data"
):

    # Only render the first 1,000 rows in the browser.
    # Rendering a huge dataframe can make Streamlit slow.
    preview_limit = 1000

    preview_df = df_sales.head(
        preview_limit
    )

    st.dataframe(
        preview_df,
        use_container_width=True,
    )

    if len(df_sales) > preview_limit:

        st.caption(
            f"Showing the first "
            f"{preview_limit:,} of "
            f"{len(df_sales):,} rows "
            f"for better performance."
        )

    # The complete filtered dataframe is still
    # available for download.
    csv_data = create_csv_download(
        df_sales
    )

    st.download_button(
        label=(
            "⬇ Download filtered "
            "sales data as CSV"
        ),
        data=csv_data,
        file_name=(
            "filtered_sales_data.csv"
        ),
        mime="text/csv",
        key=(
            "download_filtered_sales_data"
        ),
    )
