import pandas as pd

def load_data(source):
    if hasattr(source, "name"):
        if source.name.endswith(".csv"):
            return pd.read_csv(source)

        elif source.name.endswith(".xlsx"):
            df1 = pd.read_excel(source, sheet_name="Year 2009-2010")
            df2 = pd.read_excel(source, sheet_name="Year 2010-2011")
            return pd.concat([df1, df2], ignore_index=True)

    else:
        if source.endswith(".csv"):
            return pd.read_csv(source)

        elif source.endswith(".xlsx"):
            df1 = pd.read_excel(source, sheet_name="Year 2009-2010")
            df2 = pd.read_excel(source, sheet_name="Year 2010-2011")
            return pd.concat([df1, df2], ignore_index=True)

    return None