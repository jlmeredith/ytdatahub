"""
Template rendering utilities for data collection UI.
"""
import streamlit as st
import jinja2
import os
from src.utils.debug_utils import debug_log

def render_template_as_markdown(template_file, context):
    """
    Render a Jinja2 template as Markdown in Streamlit.
    
    Args:
        template_file (str): Path to the template file
        context (dict): Context variables for the template
    """
    try:
        # Get the templates directory
        template_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
        
        # Create Jinja2 environment
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Load the template
        template = env.get_template(template_file)
        
        # Render the template with context
        rendered = template.render(**context)
        
        # Display in Streamlit
        st.markdown(rendered)
        return True
        
    except Exception as e:
        debug_log(f"Error rendering template {template_file}: {str(e)}", e)
        st.error(f"Error rendering template: {str(e)}")
        return False