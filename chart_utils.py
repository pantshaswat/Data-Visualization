# chart_utils.py
import pandas as pd
import plotly.express as px

# Color theme definitions
COLOR_THEMES = {
    "Default": "plotly",
    "Viridis": "viridis",
    "Plasma": "plasma", 
    "Inferno": "inferno",
    "Magma": "magma",
    "Blues": "blues",
    "Reds": "reds",
    "Greens": "greens",
    "Purples": "purples",
    "Oranges": "oranges",
    "Rainbow": "rainbow",
    "Turbo": "turbo",
    "Pastel": "pastel",
    "Bold": "bold",
    "Vivid": "vivid",
    "Safe": "safe"
}

def apply_color_theme(fig, color_palette, chart_type="single"):
    """Apply color theme to figures"""
    if color_palette == "plotly":
        return fig
    elif color_palette in ["viridis", "plasma", "inferno", "magma"]:
        if chart_type == "single":
            fig.update_traces(marker_color=getattr(px.colors.sequential, color_palette.capitalize())[3])
        else:
            fig.update_traces(marker=dict(colorscale=color_palette))
    elif color_palette in ["blues", "reds", "greens", "purples", "oranges"]:
        if chart_type == "single":
            fig.update_traces(marker_color=getattr(px.colors.sequential, color_palette.capitalize())[5])
        else:
            fig.update_traces(marker=dict(colorscale=color_palette))
    elif color_palette == "rainbow":
        fig.update_traces(marker_color=px.colors.qualitative.Set3[0])
    elif color_palette == "turbo":
        fig.update_traces(marker_color=px.colors.sequential.Turbo[5])
    elif color_palette == "pastel":
        fig.update_traces(marker_color=px.colors.qualitative.Pastel1[0])
    elif color_palette == "bold":
        fig.update_traces(marker_color=px.colors.qualitative.Bold[0])
    elif color_palette == "vivid":
        fig.update_traces(marker_color=px.colors.qualitative.Vivid[0])
    elif color_palette == "safe":
        fig.update_traces(marker_color=px.colors.qualitative.Safe[0])
    
    return fig

def create_binned_data(df, col, bin_width):
    """Create binned data for numeric columns"""
    min_val = float(df[col].min())
    max_val = float(df[col].max())
    
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
    
    return binned_data

def create_single_column_chart(df, col, col_type, chart_type, color_palette, bin_width=None):
    """Create charts for single column visualization"""
    if chart_type == "Bar Chart":
        if col_type == "Categorical":
            freq = df[col].value_counts().reset_index()
            freq.columns = [col, 'Count']
            fig = px.bar(freq, x=col, y='Count', title=f'Bar Chart of {col}')
        else:
            binned_data = create_binned_data(df, col, bin_width)
            fig = px.bar(binned_data, x='Bin_Label', y='Count', 
                       title=f'Bar Chart of {col} (Bin width: {bin_width})')
            fig.update_xaxes(title=f'{col} (Range)', tickangle=45)
        
        fig = apply_color_theme(fig, color_palette, "single")
        return fig
        
    elif chart_type == "Line Chart":
        if col_type == "Categorical":
            freq = df[col].value_counts().reset_index()
            freq.columns = [col, 'Count']
            fig = px.line(freq, x=col, y='Count', title=f'Line Chart of {col}')
        else:
            binned_data = create_binned_data(df, col, bin_width)
            fig = px.line(binned_data, x='Bin_Label', y='Count', 
                        title=f'Line Chart of {col} (Bin width: {bin_width})')
            fig.update_xaxes(title=f'{col} (Range)', tickangle=45)
        
        fig = apply_color_theme(fig, color_palette, "single")
        return fig
        
    elif chart_type == "Pie Chart":
        if col_type == "Categorical":
            freq = df[col].value_counts().reset_index()
            freq.columns = [col, 'Count']
            if color_palette != "plotly":
                # Use appropriate color sequence for pie charts
                if color_palette in ["viridis", "plasma", "inferno", "magma", "blues", "reds", "greens", "purples", "oranges"]:
                    color_seq = getattr(px.colors.sequential, color_palette.capitalize())
                elif color_palette == "turbo":
                    color_seq = px.colors.sequential.Turbo
                elif color_palette == "rainbow":
                    color_seq = px.colors.qualitative.Set3
                elif color_palette == "pastel":
                    color_seq = px.colors.qualitative.Pastel1
                elif color_palette == "bold":
                    color_seq = px.colors.qualitative.Bold
                elif color_palette == "vivid":
                    color_seq = px.colors.qualitative.Vivid
                elif color_palette == "safe":
                    color_seq = px.colors.qualitative.Safe
                else:
                    color_seq = px.colors.qualitative.Set1
                
                fig = px.pie(freq, values='Count', names=col, title=f'Pie Chart of {col}',
                           color_discrete_sequence=color_seq)
            else:
                fig = px.pie(freq, values='Count', names=col, title=f'Pie Chart of {col}')
            return fig
        else:
            return None  # Pie charts not suitable for non-categorical data
            
    elif chart_type == "Box Plot":
        if col_type == "Categorical":
            fig = px.box(df, y=col, title=f'Box Plot of {col}')
        else:
            # For binned box plot, we'll show the distribution of midpoints
            binned_data = create_binned_data(df, col, bin_width)
            expanded_data = []
            for _, row in binned_data.iterrows():
                expanded_data.extend([row['Bin_Midpoint']] * row['Count'])
            
            binned_df = pd.DataFrame({'Binned_Values': expanded_data})
            fig = px.box(binned_df, y='Binned_Values', 
                       title=f'Box Plot of {col} (Bin width: {bin_width})')
            fig.update_yaxes(title=f'{col} (Binned)')
        
        fig = apply_color_theme(fig, color_palette, "single")
        return fig
        
    elif chart_type == "Histogram":
        min_val = float(df[col].min())
        max_val = float(df[col].max())
        # Calculate number of bins based on width
        num_bins = max(1, int((max_val - min_val) / bin_width))
        
        fig = px.histogram(df, x=col, nbins=num_bins, 
                         title=f'Histogram of {col} (Bin width: {bin_width})')
        fig = apply_color_theme(fig, color_palette, "single")
        return fig

def create_two_column_chart(df, x_axis, y_axis, chart_type, color_palette, column_types):
    """Create charts for two column visualization"""
    if chart_type == "Scatter Plot":
        if color_palette != "plotly":
            # For scatter plots, use color sequences appropriately
            if color_palette in ["viridis", "plasma", "inferno", "magma", "blues", "reds", "greens", "purples", "oranges"]:
                fig = px.scatter(df, x=x_axis, y=y_axis, title=f'{chart_type}: {y_axis} vs {x_axis}',
                               color_discrete_sequence=getattr(px.colors.sequential, color_palette.capitalize()))
            elif color_palette == "turbo":
                fig = px.scatter(df, x=x_axis, y=y_axis, title=f'{chart_type}: {y_axis} vs {x_axis}',
                               color_discrete_sequence=px.colors.sequential.Turbo)
            elif color_palette in ["pastel", "bold", "vivid", "safe"]:
                color_map = {
                    "pastel": px.colors.qualitative.Pastel1,
                    "bold": px.colors.qualitative.Bold,
                    "vivid": px.colors.qualitative.Vivid,
                    "safe": px.colors.qualitative.Safe
                }
                fig = px.scatter(df, x=x_axis, y=y_axis, title=f'{chart_type}: {y_axis} vs {x_axis}',
                               color_discrete_sequence=color_map[color_palette])
            else:
                fig = px.scatter(df, x=x_axis, y=y_axis, title=f'{chart_type}: {y_axis} vs {x_axis}')
        else:
            fig = px.scatter(df, x=x_axis, y=y_axis, title=f'{chart_type}: {y_axis} vs {x_axis}')
        return fig
        
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
            if color_palette != "plotly":
                if color_palette in ["viridis", "plasma", "inferno", "magma", "blues", "reds", "greens", "purples", "oranges"]:
                    color_seq = getattr(px.colors.sequential, color_palette.capitalize())
                elif color_palette == "turbo":
                    color_seq = px.colors.sequential.Turbo
                elif color_palette in ["pastel", "bold", "vivid", "safe"]:
                    color_map = {
                        "pastel": px.colors.qualitative.Pastel1,
                        "bold": px.colors.qualitative.Bold,
                        "vivid": px.colors.qualitative.Vivid,
                        "safe": px.colors.qualitative.Safe
                    }
                    color_seq = color_map[color_palette]
                else:
                    color_seq = px.colors.qualitative.Set1
                
                fig = px.bar(grouped, x=x_axis, y='Count', color=y_axis,
                           title=f'Count by {x_axis} and {y_axis}',
                           color_discrete_sequence=color_seq)
            else:
                fig = px.bar(grouped, x=x_axis, y='Count', color=y_axis,
                           title=f'Count by {x_axis} and {y_axis}')
        else:
            # Default case - direct plotting
            fig = px.bar(df, x=x_axis, y=y_axis, 
                       title=f'{chart_type}: {y_axis} vs {x_axis}')
            fig = apply_color_theme(fig, color_palette, "single")
        return fig
        
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
        
        fig = apply_color_theme(fig, color_palette, "single")
        return fig