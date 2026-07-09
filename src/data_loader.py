import pandas as pd


def load_data(source):
    """
    Load retail data from either:
    - a Streamlit uploaded CSV/Excel file
    - a direct CSV/Excel URL

    For the Online Retail II workbook, the two expected yearly sheets
    are combined automatically when both or either are available.
    """

    if source is None:
        return None

    # ---------------------------------
    # Uploaded file
    # ---------------------------------
    if hasattr(source, "name"):
        filename = source.name.lower()

        if filename.endswith(".csv"):
            return pd.read_csv(source)

        if filename.endswith((".xlsx", ".xls")):
            return _load_excel(source)

        raise ValueError(
            "Unsupported file type. Please upload a CSV or Excel file."
        )

    # ---------------------------------
    # URL
    # ---------------------------------
    if isinstance(source, str):
        source_lower = source.lower().split("?")[0]

        if source_lower.endswith(".csv"):
            return pd.read_csv(source)

        if source_lower.endswith((".xlsx", ".xls")):
            return _load_excel(source)

        raise ValueError(
            "Unsupported URL format. Please provide a direct CSV or Excel URL."
        )

    raise TypeError("Unsupported data source.")


def _load_excel(source):
    """
    Load an Excel workbook.

    If the workbook contains the Online Retail II yearly sheets,
    they are combined into one dataframe.

    Otherwise, the first available sheet is loaded.
    """

    excel_file = pd.ExcelFile(source)

    expected_sheets = [
        "Year 2009-2010",
        "Year 2010-2011",
    ]

    available_expected_sheets = [
        sheet
        for sheet in expected_sheets
        if sheet in excel_file.sheet_names
    ]

    if available_expected_sheets:
        dataframes = [
            pd.read_excel(
                excel_file,
                sheet_name=sheet,
            )
            for sheet in available_expected_sheets
        ]

        return pd.concat(dataframes, ignore_index=True)

    return pd.read_excel(
        excel_file,
        sheet_name=excel_file.sheet_names[0],
    )
