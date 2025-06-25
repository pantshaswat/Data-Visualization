import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import base64
import io
from PIL import Image
import streamlit as st

class ChartInterpreter:
    def __init__(self, api_key):
        """Initialize the Gemini AI interpreter"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_dataset_context(self, df, column_types, user_description=None):
        """Generate context about the dataset for better AI interpretation"""
        context = f"""
Dataset Overview:
- Total rows: {len(df)}
- Total columns: {len(df.columns)}
- Column names: {list(df.columns)}
"""
        
        if user_description:
            context += f"- Dataset Description (provided by user): {user_description}\n"
        
        context += "\nColumn Information:\n"
        for col, col_type in column_types.items():
            context += f"- {col}: {col_type}"
            if col_type in ["Numeric (Continuous)", "Numeric (Discrete)"]:
                context += f" (range: {df[col].min():.2f} to {df[col].max():.2f})"
            elif col_type == "Categorical":
                unique_count = df[col].nunique()
                context += f" ({unique_count} unique values)"
                if unique_count <= 10:
                    context += f" - values: {list(df[col].unique())}"
            context += "\n"
        
        # Add basic statistics
        context += f"\nDataset Statistics:\n"
        context += f"- Missing values: {df.isnull().sum().sum()}\n"
        
        # Sample data
        context += f"\nSample Data (first 3 rows):\n"
        context += df.head(3).to_string()
        
        return context
    
    def fig_to_image(self, fig):
        """Convert plotly figure to image"""
        # Convert plotly figure to image
        img_bytes = pio.to_image(fig, format="png", width=800, height=600)
        img = Image.open(io.BytesIO(img_bytes))
        return img
    
    def create_chart_prompt(self, chart_type, selected_columns, dataset_context, chart_data_summary=None):
        """Create a comprehensive prompt for chart interpretation"""
        
        prompt = f"""
You are an expert data analyst. Please analyze and interpret the following chart based on the provided context.

{dataset_context}

Chart Information:
- Chart Type: {chart_type}
- Columns Visualized: {selected_columns}
- Additional Data Summary: {chart_data_summary if chart_data_summary else 'Not provided'}

Please provide a comprehensive interpretation that includes:

1. **Data Patterns & Trends**: What patterns, trends, or relationships do you observe in the data?

2. **Key Insights**: What are the most important insights this visualization reveals?

3. **Statistical Observations**: Comment on distribution, outliers, correlations, or other statistical aspects.

4. **Domain-Specific Implications**: Based on the dataset description, what might these findings mean in the specific context of this data?

5. **Data Quality Notes**: Any observations about data quality, missing values, or potential issues?

6. **Recommendations**: Suggest follow-up analyses or actions based on these findings and the dataset context.

Please be specific, analytical, and provide actionable insights. Focus on what the data tells us in the context of the described domain rather than just describing what the chart looks like.
"""
        return prompt
    
    def get_chart_data_summary(self, df, selected_columns, chart_type, column_types):
        """Generate additional data summary for specific chart context"""
        summary = ""
        
        if len(selected_columns) == 1:
            col = selected_columns[0]
            col_type = column_types.get(col, "Unknown")
            
            if col_type == "Categorical":
                value_counts = df[col].value_counts()
                summary += f"Value distribution for {col}:\n"
                summary += value_counts.head(10).to_string()
                if len(value_counts) > 10:
                    summary += f"\n... and {len(value_counts) - 10} more categories"
            else:
                summary += f"Statistical summary for {col}:\n"
                summary += df[col].describe().to_string()
                
        elif len(selected_columns) == 2:
            col1, col2 = selected_columns
            summary += f"Relationship analysis between {col1} and {col2}:\n"
            
            # Correlation if both numeric
            if (column_types.get(col1) in ["Numeric (Continuous)", "Numeric (Discrete)"] and 
                column_types.get(col2) in ["Numeric (Continuous)", "Numeric (Discrete)"]):
                correlation = df[col1].corr(df[col2])
                summary += f"Correlation coefficient: {correlation:.3f}\n"
            
            # Basic summary for each column
            for col in selected_columns:
                if column_types.get(col) == "Categorical":
                    summary += f"\n{col} unique values: {df[col].nunique()}"
                else:
                    summary += f"\n{col} range: {df[col].min():.2f} to {df[col].max():.2f}"
        
        return summary
    
    def interpret_chart(self, fig, df, selected_columns, chart_type, column_types, user_description=None, include_image=True):
        """Main function to interpret a chart using Gemini AI"""
        try:
            # Generate dataset context with user description
            dataset_context = self.generate_dataset_context(df, column_types, user_description)
            
            # Get chart-specific data summary
            chart_data_summary = self.get_chart_data_summary(df, selected_columns, chart_type, column_types)
            
            # Create the prompt
            prompt = self.create_chart_prompt(chart_type, selected_columns, dataset_context, chart_data_summary)
            
            if include_image:
                # Convert chart to image and include in analysis
                chart_image = self.fig_to_image(fig)
                
                # Send both image and text to Gemini
                response = self.model.generate_content([
                    prompt,
                    chart_image
                ])
            else:
                # Text-only analysis
                response = self.model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            return f"Error generating interpretation: {str(e)}"
    
    def get_chart_recommendations(self, df, column_types, user_description=None):
        """Suggest additional charts or analyses based on the dataset"""
        try:
            dataset_context = self.generate_dataset_context(df, column_types, user_description)
            
            prompt = f"""
Based on the following dataset, suggest 3-5 additional visualizations or analyses that would provide valuable insights:

{dataset_context}

Please suggest:
1. Specific chart types and column combinations
2. Why each visualization would be useful
3. What insights it might reveal in the context of this specific dataset

Format your response as a bulleted list with brief explanations.
"""
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"Error generating recommendations: {str(e)}"