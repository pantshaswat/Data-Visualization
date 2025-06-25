# visualizer.py
import streamlit as st
import pandas as pd
from classifier import classify_dataframe
from chart_utils import (
    COLOR_THEMES, 
    create_single_column_chart, 
    create_two_column_chart
)

st.title("CSV Visualizer with Intelligent Column Detection")

# Color theme selection
st.sidebar.header("Chart Settings")

selected_theme = st.sidebar.selectbox(
    "Choose Color Theme",
    options=list(COLOR_THEMES.keys()),
    index=0,
    help="Select a color theme for your charts"
)

color_palette = COLOR_THEMES[selected_theme]

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
        
        # Enhanced chart options for single column
        if col_type == "Categorical":
            chart_type = st.selectbox("Chart type", ["Bar Chart", "Line Chart", "Pie Chart"])
        else:
            chart_type = st.selectbox("Chart type", ["Bar Chart", "Line Chart", "Box Plot", "Histogram"])
        
        # Bin settings for numeric data (applies to all chart types)
        bin_width = None
        
        if col_type != "Categorical":
            st.subheader("Bin Settings")
            min_val = float(df[col].min())
            max_val = float(df[col].max())
            data_range = max_val - min_val
            
            # Suggest a reasonable default bin width
            default_bin_width = round(data_range / 10, 2)
            if default_bin_width == 0:
                default_bin_width = 1
            
            bin_width = st.number_input(
                f"Bin width for {col}",
                min_value=0.01,
                max_value=data_range,
                value=default_bin_width,
                step=default_bin_width/10,
                format="%.2f",
                help=f"Each data point will be grouped into ranges of this width. Data range: {min_val:.2f} to {max_val:.2f}"
            )
        
        # Create chart
        fig = create_single_column_chart(df, col, col_type, chart_type, color_palette, bin_width)
        
        if fig is not None:
            st.plotly_chart(fig)
        else:
            st.warning("Pie charts are only suitable for categorical data. Please select a different chart type.")
    
    elif len(selected_cols) == 2:
        col1, col2 = selected_cols
        
        # Let user choose which column goes on which axis
        st.subheader("Axis Selection")
        axis_cols = st.columns(2)
        
        with axis_cols[0]:
            x_axis = st.selectbox("Select X-axis column", selected_cols, key="x_axis")
        
        with axis_cols[1]:
            y_axis = st.selectbox("Select Y-axis column", 
                                 [col for col in selected_cols if col != x_axis], 
                                 key="y_axis")
        
        # Chart type selection for two columns
        chart_type = st.selectbox("Chart type", ["Scatter Plot", "Bar Chart", "Line Chart"])
        
        # Create chart
        fig = create_two_column_chart(df, x_axis, y_axis, chart_type, color_palette, column_types)
        st.plotly_chart(fig)
    
    else:
        st.info("Select 1 or 2 columns to visualize.")
else:
    st.info("Upload a CSV file to begin.")