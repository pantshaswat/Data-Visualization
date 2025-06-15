import streamlit as st
import pandas as pd
import numpy as np

# Function to classify column data type
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


# Streamlit UI
st.title("CSV Data Visualizer with Intelligent Type Inference")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("Preview of Data")
    st.dataframe(df)

    st.subheader("Inferred Column Types")

    # Classify each column
    classifications = {
        col: classify_column(df[col]) for col in df.columns
    }

    # Convert to DataFrame for display
    type_df = pd.DataFrame.from_dict(classifications, orient='index', columns=['Inferred Type'])
    type_df.index.name = 'Column'
    st.dataframe(type_df)

else:
    st.info("Please upload a CSV file to proceed.")
