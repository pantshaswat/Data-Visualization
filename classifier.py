# classifier.py

import pandas as pd

def classify_column(series):
    unique_vals = series.dropna().unique()
    if pd.api.types.is_numeric_dtype(series):
        if set(unique_vals).issubset({0, 1}):
            return "Categorical"
        elif (series.dropna().apply(lambda x: isinstance(x, (int, float)) and float(x).is_integer())).all():
            if series.nunique() < 20:
                return "Numeric (Discrete)"
            else:
                return "Numeric (Continuous)"
        else:
            return "Numeric (Continuous)"
    else:
        return "Categorical"

def classify_dataframe(df):
    return {col: classify_column(df[col]) for col in df.columns}
