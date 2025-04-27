"""
UI utilities for loading HTML templates and CSS files.
This module centralizes loading of UI resources to keep them separate from application logic.
"""
import re
import streamlit as st
from pathlib import Path
import json
import os

# Template cache to avoid reloading templates
_template_cache = {}

def load_html_template(template_name):
    """Load an HTML template from the templates directory.
    
    Args:
        template_name: Name of the template file without path
        
    Returns:
        str: The HTML content of the template
    """
    # Check cache first for better performance
    if template_name in _template_cache:
        return _template_cache[template_name]
    
    template_path = Path(__file__).parent.parent.parent / 'static' / 'templates' / template_name
    
    if not template_path.exists():
        st.error(f"Template {template_name} not found at {template_path}")
        return ""
    
    with open(template_path) as f:
        template_content = f.read()
        _template_cache[template_name] = template_content
        return template_content

def clear_template_cache():
    """Clear the template cache to force reload of templates."""
    global _template_cache
    _template_cache = {}

def render_template(template_name, context=None):
    """Render an HTML template with the provided context.
    
    Args:
        template_name: Name of the template file
        context: Dictionary of variables to replace in the template
        
    Returns:
        str: The rendered HTML content
    """
    template_content = load_html_template(template_name)
    
    if not context:
        return template_content
    
    # Simple template variable replacement
    for key, value in context.items():
        placeholder = f"{{{{ {key} }}}}"
        template_content = template_content.replace(placeholder, str(value))
    
    # Process conditional blocks (simple if statements)
    # Format: <!-- if condition_variable --> content <!-- endif -->
    pattern = r'<!-- if (\w+) -->(.*?)<!-- endif -->'
    
    def replace_conditional(match):
        condition_var = match.group(1)
        content = match.group(2)
        
        # Check if the condition variable exists and is truthy
        if condition_var in context and context[condition_var]:
            return content
        return ""
    
    template_content = re.sub(pattern, replace_conditional, template_content, flags=re.DOTALL)
    
    # Process loops (simple foreach loops)
    # Format: <!-- foreach item in items --> content with {{item}} <!-- endforeach -->
    loop_pattern = r'<!-- foreach (\w+) in (\w+) -->(.*?)<!-- endforeach -->'
    
    def replace_loop(match):
        item_var = match.group(1)
        collection_var = match.group(2)
        loop_content_template = match.group(3)
        
        # Check if the collection variable exists
        if collection_var not in context or not isinstance(context[collection_var], (list, tuple)):
            return ""
        
        # Build the result by repeating the loop content for each item
        result = []
        for item in context[collection_var]:
            # Create a copy of the loop content and replace the item variable
            content = loop_content_template.replace(f"{{{{ {item_var} }}}}", str(item))
            
            # If item is a dictionary, replace its attribute placeholders too
            if isinstance(item, dict):
                for key, value in item.items():
                    placeholder = f"{{{{ {item_var}.{key} }}}}"
                    content = content.replace(placeholder, str(value))
            
            result.append(content)
        
        return ''.join(result)
    
    template_content = re.sub(loop_pattern, replace_loop, template_content, flags=re.DOTALL)
    
    return template_content

def render_template_as_markdown(template_name, context=None):
    """Render an HTML template and display it as markdown in Streamlit.
    
    Args:
        template_name: Name of the template file
        context: Dictionary of variables to replace in the template
    """
    html_content = render_template(template_name, context)
    st.markdown(html_content, unsafe_allow_html=True)

def include_template(template_name, context=None):
    """Include a template within another template.
    
    Args:
        template_name: Name of the template file to include
        context: Dictionary of variables to replace in the template
        
    Returns:
        str: The rendered HTML content of the included template
    """
    return render_template(template_name, context)

def load_css_file(css_name="styles.css"):
    """Load CSS from a file and inject it into Streamlit.
    
    Args:
        css_name: Name of the CSS file in the css directory
    """
    css_path = Path(__file__).parent.parent.parent / 'static' / 'css' / css_name
    
    if not css_path.exists():
        st.error(f"CSS file {css_name} not found at {css_path}")
        return
    
    with open(css_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def apply_security_headers():
    """Apply security headers using a template instead of inline HTML."""
    html_content = load_html_template("security_headers.html")
    st.markdown(html_content, unsafe_allow_html=True)

def create_template(template_name, content):
    """Create a new template file.
    
    Args:
        template_name: Name of the template file to create
        content: HTML content of the template
        
    Returns:
        bool: True if the template was created successfully
    """
    template_path = Path(__file__).parent.parent.parent / 'static' / 'templates' / template_name
    
    # Create directory if it doesn't exist
    os.makedirs(template_path.parent, exist_ok=True)
    
    try:
        with open(template_path, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        st.error(f"Error creating template {template_name}: {e}")
        return False