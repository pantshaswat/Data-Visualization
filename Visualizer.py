import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from classifier import classify_dataframe
from chart_utils import (
    COLOR_THEMES, 
    create_single_column_chart, 
    create_two_column_chart
)
from ai_interpreter import ChartInterpreter

# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="AI-Powered CSV Visualizer", layout="wide")

st.title("🤖 CSV Visualizer with AI Interpretation")
st.markdown("Upload your CSV and get intelligent insights about your data visualizations!")

# Initialize session state for dataset description
if 'dataset_description' not in st.session_state:
    st.session_state.dataset_description = ""

# Sidebar configuration
st.sidebar.header("⚙️ Settings")

# Load API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize AI interpreter with API key from .env
ai_interpreter = None
if GEMINI_API_KEY:
    try:
        ai_interpreter = ChartInterpreter(GEMINI_API_KEY)
        st.sidebar.success("✅ AI Interpreter ready!")
    except Exception as e:
        st.sidebar.error(f"❌ Error initializing AI: {str(e)}")
else:
    st.sidebar.error("❌ GEMINI_API_KEY not found in environment variables")
    st.sidebar.info("💡 Create a .env file with: GEMINI_API_KEY=your_api_key_here")

# Chart settings
st.sidebar.subheader("🎨 Chart Settings")
selected_theme = st.sidebar.selectbox(
    "Choose Color Theme",
    options=list(COLOR_THEMES.keys()),
    index=0,
    help="Select a color theme for your charts"
)

color_palette = COLOR_THEMES[selected_theme]

# AI settings
if ai_interpreter:
    st.sidebar.subheader("🧠 AI Settings")
    include_image_analysis = st.sidebar.checkbox(
        "Include chart image in analysis", 
        value=True,
        help="Send chart image to AI for visual analysis (more detailed but slower)"
    )
    auto_interpret = st.sidebar.checkbox(
        "Auto-interpret charts", 
        value=False,
        help="Automatically generate AI interpretation when chart is created"
    )

# Upload CSV
uploaded_file = st.file_uploader("📁 Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    # Load and display data
    df = pd.read_csv(uploaded_file)
    
    # Dataset description input - moved to top level for better UX
    st.markdown("---")
    st.subheader("📝 Dataset Context (Optional but Recommended)")
    st.session_state.dataset_description = st.text_area(
        "Describe your dataset to help AI provide better insights:",
        value=st.session_state.dataset_description,
        placeholder="e.g., This dataset contains sales data from an e-commerce store, including customer demographics, product categories, and purchase amounts over the last year...",
        height=80,
        help="Providing context about your dataset helps AI give more relevant and accurate interpretations.",
        key="main_dataset_description"
    )
    
    # Create tabs for better organization
    tab1, tab2 = st.tabs(["📊 Data & Visualization", "🔍 Data Analysis"])
    
    with tab1:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📋 Data Preview")
            st.dataframe(df.head(10), height=300)
            
            # Dataset info
            st.subheader("📈 Dataset Info")
            st.write(f"**Rows:** {len(df)}")
            st.write(f"**Columns:** {len(df.columns)}")
            st.write(f"**Missing values:** {df.isnull().sum().sum()}")
            
        with col2:
            # Classify columns
            column_types = classify_dataframe(df)
            
            st.subheader("🔍 Column Type Classification")
            type_df = pd.DataFrame(list(column_types.items()), columns=["Column", "Inferred Type"])
            st.dataframe(type_df, height=200)
            
            # Column selection
            st.subheader("📊 Create Visualization")
            selected_cols = st.multiselect("Select 1 or 2 columns to visualize", df.columns)
            
            if len(selected_cols) == 1:
                col = selected_cols[0]
                col_type = column_types.get(col, "Unknown")
                
                # Chart type selection
                if col_type == "Categorical":
                    chart_type = st.selectbox("Chart type", ["Bar Chart", "Line Chart", "Pie Chart"])
                else:
                    chart_type = st.selectbox("Chart type", ["Bar Chart", "Line Chart", "Box Plot", "Histogram"])
                
                # Bin settings for numeric data
                bin_width = None
                if col_type != "Categorical":
                    with st.expander("⚙️ Bin Settings", expanded=False):
                        min_val = float(df[col].min())
                        max_val = float(df[col].max())
                        data_range = max_val - min_val
                        
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
                            help=f"Data range: {min_val:.2f} to {max_val:.2f}"
                        )
                
                # Create chart
                fig = create_single_column_chart(df, col, col_type, chart_type, color_palette, bin_width)
                
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # AI Interpretation section
                    if ai_interpreter:
                        st.markdown("---")
                        
                        # Create columns for the interpretation section
                        interpret_col1, interpret_col2 = st.columns([4, 1])
                        
                        with interpret_col1:
                            st.subheader("🤖 AI Chart Interpretation")
                        
                        with interpret_col2:
                            interpret_button = st.button("🔍 Interpret Chart", type="primary", key="interpret_single")
                        
                        # Auto-interpret logic
                        should_interpret = interpret_button or auto_interpret
                        
                        if should_interpret:
                            with st.spinner("🧠 AI is analyzing your chart..."):
                                # Use the dataset description from session state
                                interpretation = ai_interpreter.interpret_chart(
                                    fig, 
                                    df, 
                                    selected_cols, 
                                    chart_type, 
                                    column_types, 
                                    st.session_state.dataset_description if st.session_state.dataset_description.strip() else None,
                                    include_image_analysis
                                )
                                st.session_state.current_interpretation = interpretation
                        
                        # Display interpretation if available
                        if hasattr(st.session_state, 'current_interpretation'):
                            st.markdown("### 📊 Analysis Results")
                            st.markdown(st.session_state.current_interpretation)
                else:
                    st.warning("⚠️ Pie charts are only suitable for categorical data. Please select a different chart type.")
            
            elif len(selected_cols) == 2:
                col1_viz, col2_viz = selected_cols
                
                # Axis selection
                st.subheader("📐 Axis Configuration")
                axis_col1, axis_col2 = st.columns(2)
                
                with axis_col1:
                    x_axis = st.selectbox("X-axis column", selected_cols, key="x_axis")
                
                with axis_col2:
                    y_axis = st.selectbox("Y-axis column", 
                                         [col for col in selected_cols if col != x_axis], 
                                         key="y_axis")
                
                chart_type = st.selectbox("Chart type", ["Scatter Plot", "Bar Chart", "Line Chart"])
                
                # Create chart
                fig = create_two_column_chart(df, x_axis, y_axis, chart_type, color_palette, column_types)
                st.plotly_chart(fig, use_container_width=True)
                
                # AI Interpretation section
                if ai_interpreter:
                    st.markdown("---")
                    
                    # Create columns for the interpretation section
                    interpret_col1, interpret_col2 = st.columns([4, 1])
                    
                    with interpret_col1:
                        st.subheader("🤖 AI Chart Interpretation")
                    
                    with interpret_col2:
                        interpret_button_2col = st.button("🔍 Interpret Chart", type="primary", key="interpret_two")
                    
                    # Auto-interpret logic
                    should_interpret_2col = interpret_button_2col or auto_interpret
                    
                    if should_interpret_2col:
                        with st.spinner("🧠 AI is analyzing your chart..."):
                            # Use the dataset description from session state
                            interpretation = ai_interpreter.interpret_chart(
                                fig, 
                                df, 
                                [x_axis, y_axis], 
                                chart_type, 
                                column_types, 
                                st.session_state.dataset_description if st.session_state.dataset_description.strip() else None,
                                include_image_analysis
                            )
                            st.session_state.current_interpretation_2col = interpretation
                    
                    # Display interpretation if available
                    if hasattr(st.session_state, 'current_interpretation_2col'):
                        st.markdown("### 📊 Analysis Results")
                        st.markdown(st.session_state.current_interpretation_2col)
                        
                        # Add option to get chart recommendations
                        # if st.button("💡 Get Chart Recommendations", key="rec_two"):
                        #     with st.spinner("🔍 Generating recommendations..."):
                        #         recommendations = ai_interpreter.get_chart_recommendations(
                        #             df, 
                        #             column_types, 
                        #             st.session_state.dataset_description if st.session_state.dataset_description.strip() else None
                        #         )
                        #         st.session_state.current_recommendations_2col = recommendations
                        
                        # Display recommendations if available
                        if hasattr(st.session_state, 'current_recommendations_2col'):
                            st.markdown("### 💡 Additional Analysis Suggestions")
                            st.markdown(st.session_state.current_recommendations_2col)
            
            else:
                st.info("ℹ️ Select 1 or 2 columns to visualize.")
    
    with tab2:
        st.subheader("📊 Detailed Data Analysis")
        
        # Data summary
        col_summary1, col_summary2 = st.columns(2)
        
        with col_summary1:
            st.subheader("📈 Numerical Columns Summary")
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                st.dataframe(df[numeric_cols].describe())
            else:
                st.write("No numerical columns found.")
        
        with col_summary2:
            st.subheader("📋 Categorical Columns Summary")
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                for col in categorical_cols[:3]:  # Show first 3 categorical columns
                    st.write(f"**{col}:**")
                    value_counts = df[col].value_counts().head(5)
                    st.dataframe(value_counts.to_frame())
            else:
                st.write("No categorical columns found.")
        
        # Missing values analysis
        st.subheader("❓ Missing Values Analysis")
        missing_data = df.isnull().sum()
        missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
        
        if len(missing_data) > 0:
            missing_df = pd.DataFrame({
                'Column': missing_data.index,
                'Missing Count': missing_data.values,
                'Missing Percentage': (missing_data.values / len(df) * 100).round(2)
            })
            st.dataframe(missing_df)
        else:
            st.success("✅ No missing values found in the dataset!")
        
        # AI-powered data insights (if available)
        # if ai_interpreter and st.session_state.dataset_description.strip():
        #     st.markdown("---")
        #     st.subheader("🤖 AI Data Overview")
        #     if st.button("🔍 Get AI Data Overview", key="data_overview"):
        #         with st.spinner("🧠 AI is analyzing your dataset..."):
        #             # Generate overall dataset insights
        #             dataset_context = ai_interpreter.generate_dataset_context(
        #                 df, column_types, st.session_state.dataset_description
        #             )
                    
        #             prompt = f"""
        #             Based on the following dataset information, provide a comprehensive overview:
                    
        #             {dataset_context}
                    
        #             Please provide:
        #             1. **Dataset Summary**: Overall assessment of the data
        #             2. **Data Quality**: Comments on completeness, potential issues
        #             3. **Key Variables**: Most important columns for analysis
        #             4. **Potential Insights**: What interesting patterns might be found
        #             5. **Analysis Recommendations**: Suggested approaches for deeper analysis
        #             """
                    
        #             overview = ai_interpreter.model.generate_content(prompt).text
        #             st.session_state.data_overview = overview
            
        #     # Display overview if available
        #     if hasattr(st.session_state, 'data_overview'):
        #         st.markdown(st.session_state.data_overview)

else:
    st.info("📁 Upload a CSV file to begin exploring your data with AI-powered insights!")
    
    # Show example without data
    st.markdown("### 🌟 Features")
    
    feature_col1, feature_col2, feature_col3 = st.columns(3)
    
    with feature_col1:
        st.markdown("""
        **📊 Smart Visualization**
        - Automatic column type detection
        - Multiple chart types
        - Customizable themes
        """)
    
    with feature_col2:
        st.markdown("""
        **🤖 AI Analysis**
        - Chart interpretation
        - Pattern recognition
        - Insight generation
        """)
    
    with feature_col3:
        st.markdown("""
        **💡 Recommendations**
        - Suggested analyses
        - Data quality insights
        - Follow-up actions
        """)