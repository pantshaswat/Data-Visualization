# app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from classifier import classify_dataframe

st.title("CSV Visualizer with Intelligent Column Detection")

# Upload CSV
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.subheader("Data Preview")
    st.dataframe(df)

    # Classify columns
    column_types = classify_dataframe(df)
    type_df = pd.DataFrame(list(column_types.items()), columns=["Column", "Inferred Type"])
    st.subheader("Column Type Inference")
    st.dataframe(type_df)

    # Select columns
    selected_cols = st.multiselect("Select 1 or 2 columns to visualize", df.columns)

    if len(selected_cols) == 1:
        col = selected_cols[0]
        col_type = column_types.get(col, "Unknown")

        if col_type == "Categorical":
            chart_type = st.selectbox("Chart type", ["Bar Chart", "Line Chart"])
        else:
            chart_type = st.selectbox("Chart type", ["Bar Chart", "Line Chart", "Box Plot"])

        if chart_type == "Bar Chart":
            if col_type == "Categorical":
                freq = df[col].value_counts().reset_index()
                freq.columns = [col, 'Count']
                fig = px.bar(freq, x=col, y='Count')
            else:
                fig = px.bar(df, y=col)
            st.plotly_chart(fig)

        elif chart_type == "Line Chart":
            if col_type == "Categorical":
                freq = df[col].value_counts().reset_index()
                freq.columns = [col, 'Count']
                fig = px.line(freq, x=col, y='Count')
            else:
                fig = px.line(df, y=col)
            st.plotly_chart(fig)

        elif chart_type == "Box Plot":
            fig = px.box(df, y=col)
            st.plotly_chart(fig)

    elif len(selected_cols) == 2:
        col1, col2 = selected_cols
        chart_type = st.selectbox("Chart type", ["Scatter Plot", "Bar Chart"])

        if chart_type == "Scatter Plot":
            fig = px.scatter(df, x=col1, y=col2)
            st.plotly_chart(fig)

        elif chart_type == "Bar Chart":
            grouped = df.groupby([col1, col2]).size().reset_index(name='Count')
            fig = px.bar(grouped, x=col1, y='Count', color=col2)
            st.plotly_chart(fig)

    else:
        st.info("Select 1 or 2 columns to visualize.")
else:
    st.info("Upload a CSV file to begin.")
