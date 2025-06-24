# visualizer.py
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
        
        # Enhanced chart options for single column
        if col_type == "Categorical":
            chart_type = st.selectbox("Chart type", ["Bar Chart", "Line Chart", "Pie Chart"])
        else:
            chart_type = st.selectbox("Chart type", ["Bar Chart", "Line Chart", "Box Plot", "Histogram"])
        
        # Bin settings for numeric data (applies to all chart types)
        binned_data = None
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
            
            # Create bins with specified width
            bins = []
            current = min_val
            while current < max_val:
                bins.append(current)
                current += bin_width
            bins.append(max_val)  # Ensure we include the maximum value
            
            # Create binned data for all chart types
            hist_data = pd.cut(df[col].dropna(), bins=bins, include_lowest=True, duplicates='drop')
            binned_data = hist_data.value_counts().sort_index().reset_index()
            binned_data.columns = ['Bin', 'Count']
            binned_data['Bin_Label'] = binned_data['Bin'].apply(lambda x: f"{x.left:.2f}-{x.right:.2f}")
            binned_data['Bin_Midpoint'] = binned_data['Bin'].apply(lambda x: (x.left + x.right) / 2)
        
        if chart_type == "Bar Chart":
            if col_type == "Categorical":
                freq = df[col].value_counts().reset_index()
                freq.columns = [col, 'Count']
                fig = px.bar(freq, x=col, y='Count', title=f'Bar Chart of {col}')
            else:
                fig = px.bar(binned_data, x='Bin_Label', y='Count', 
                           title=f'Bar Chart of {col} (Bin width: {bin_width})')
                fig.update_xaxes(title=f'{col} (Range)', tickangle=45)
            st.plotly_chart(fig)
            
        elif chart_type == "Line Chart":
            if col_type == "Categorical":
                freq = df[col].value_counts().reset_index()
                freq.columns = [col, 'Count']
                fig = px.line(freq, x=col, y='Count', title=f'Line Chart of {col}')
            else:
                fig = px.line(binned_data, x='Bin_Label', y='Count', 
                            title=f'Line Chart of {col} (Bin width: {bin_width})')
                fig.update_xaxes(title=f'{col} (Range)', tickangle=45)
            st.plotly_chart(fig)
            
        elif chart_type == "Pie Chart":
            if col_type == "Categorical":
                freq = df[col].value_counts().reset_index()
                freq.columns = [col, 'Count']
                fig = px.pie(freq, values='Count', names=col, title=f'Pie Chart of {col}')
                st.plotly_chart(fig)
            else:
                st.warning("Pie charts are only suitable for categorical data. Please select a different chart type.")
                
        elif chart_type == "Box Plot":
            if col_type == "Categorical":
                fig = px.box(df, y=col, title=f'Box Plot of {col}')
            else:
                # For binned box plot, we'll show the distribution of midpoints
                expanded_data = []
                for _, row in binned_data.iterrows():
                    expanded_data.extend([row['Bin_Midpoint']] * row['Count'])
                
                binned_df = pd.DataFrame({'Binned_Values': expanded_data})
                fig = px.box(binned_df, y='Binned_Values', 
                           title=f'Box Plot of {col} (Bin width: {bin_width})')
                fig.update_yaxes(title=f'{col} (Binned)')
            st.plotly_chart(fig)
            
        elif chart_type == "Histogram":
            # Calculate number of bins based on width
            num_bins = max(1, int((max_val - min_val) / bin_width))
            
            fig = px.histogram(df, x=col, nbins=num_bins, 
                             title=f'Histogram of {col} (Bin width: {bin_width})')
            st.plotly_chart(fig)
    
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
        
        if chart_type == "Scatter Plot":
            fig = px.scatter(df, x=x_axis, y=y_axis, title=f'{chart_type}: {y_axis} vs {x_axis}')
            st.plotly_chart(fig)
            
        elif chart_type == "Bar Chart":
            # Check if we need to aggregate data
            x_type = column_types.get(x_axis, "Unknown")
            y_type = column_types.get(y_axis, "Unknown")
            
            if x_type == "Categorical" and y_type in ["Numeric (Continuous)", "Numeric (Discrete)"]:
                # Aggregate numeric data by categorical variable
                grouped = df.groupby(x_axis)[y_axis].mean().reset_index()
                fig = px.bar(grouped, x=x_axis, y=y_axis, 
                           title=f'Average {y_axis} by {x_axis}')
            elif x_type == "Categorical" and y_type == "Categorical":
                # Count occurrences for categorical vs categorical
                grouped = df.groupby([x_axis, y_axis]).size().reset_index(name='Count')
                fig = px.bar(grouped, x=x_axis, y='Count', color=y_axis,
                           title=f'Count by {x_axis} and {y_axis}')
            else:
                # Default case - direct plotting
                fig = px.bar(df, x=x_axis, y=y_axis, 
                           title=f'{chart_type}: {y_axis} vs {x_axis}')
            st.plotly_chart(fig)
            
        elif chart_type == "Line Chart":
            # Similar logic for line charts
            x_type = column_types.get(x_axis, "Unknown")
            y_type = column_types.get(y_axis, "Unknown")
            
            if x_type == "Categorical" and y_type in ["Numeric (Continuous)", "Numeric (Discrete)"]:
                grouped = df.groupby(x_axis)[y_axis].mean().reset_index()
                fig = px.line(grouped, x=x_axis, y=y_axis, 
                            title=f'Average {y_axis} by {x_axis}')
            else:
                fig = px.line(df, x=x_axis, y=y_axis, 
                            title=f'{chart_type}: {y_axis} vs {x_axis}')
            st.plotly_chart(fig)
    
    else:
        st.info("Select 1 or 2 columns to visualize.")
else:
    st.info("Upload a CSV file to begin.")