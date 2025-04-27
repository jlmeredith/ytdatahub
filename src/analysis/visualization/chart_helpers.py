"""
Common chart configuration helpers for Plotly visualizations.
"""
import plotly.graph_objects as go
import plotly.express as px

def configure_time_series_layout(fig, title, height=500, show_rangeslider=True):
    """
    Configure a time series plot layout with common settings.
    
    Args:
        fig: Plotly figure object
        title: Chart title
        height: Chart height in pixels
        show_rangeslider: Whether to show a range slider for the x-axis
        
    Returns:
        The configured figure
    """
    fig.update_layout(
        title=title,
        template="plotly_white",
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        selectdirection="h",
        height=height,
        xaxis_title="Date",
        yaxis_title="Count",
        plot_bgcolor="rgba(240,242,246,0.3)",
        autosize=True
    )
    
    if show_rangeslider:
        fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
    
    return fig

def configure_bar_chart_layout(fig, title, x_title, y_title, height=400):
    """
    Configure a bar chart layout with common settings.
    
    Args:
        fig: Plotly figure object
        title: Chart title
        x_title: X-axis title
        y_title: Y-axis title
        height: Chart height in pixels
        
    Returns:
        The configured figure
    """
    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        template="plotly_white",
        height=height,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="rgba(240,242,246,0.3)"
    )
    
    return fig

def add_percentage_annotations(fig, df, x_col, y_col, total=None):
    """
    Add percentage annotations to a bar chart.
    
    Args:
        fig: Plotly figure object
        df: DataFrame with data
        x_col: Column name for x-axis values
        y_col: Column name for y-axis values
        total: Total value for percentage calculation (if None, sum of y_col is used)
        
    Returns:
        The figure with annotations added
    """
    if total is None:
        total = df[y_col].sum()
    
    for i, row in df.iterrows():
        percentage = (row[y_col] / total * 100)
        if not pd.isna(percentage) and percentage > 0:
            fig.add_annotation(
                x=row[x_col],
                y=row[y_col],
                text=f"{percentage:.1f}%",
                showarrow=False,
                yshift=10
            )
    
    return fig

def get_plotly_config(responsive=True, display_mode_bar=True, scroll_zoom=True):
    """
    Get a standard configuration dictionary for Plotly charts.
    
    Args:
        responsive: Whether to make the chart responsive
        display_mode_bar: Whether to display the mode bar
        scroll_zoom: Whether to enable scroll zoom
        
    Returns:
        Dictionary with Plotly configuration
    """
    return {
        'responsive': responsive,
        'displayModeBar': display_mode_bar,
        'scrollZoom': scroll_zoom,
        'modeBarButtonsToRemove': ['lasso2d', 'select2d']
    }