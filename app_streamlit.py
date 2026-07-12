import streamlit as st
import streamlit.components.v1 as components
import os

# Streamlit Page Configuration
st.set_page_config(
    page_title="Cyber Pathfinder & Grid Duel",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Streamlit Custom CSS to remove standard margins and padding for a cleaner embedded look
st.markdown("""
    <style>
        /* Hide Streamlit header and footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Reduce padding around main container */
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }
        
        /* Styling info text */
        .streamlit-info-text {
            font-family: 'Space Grotesk', sans-serif;
            color: #9ca3af;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 0.5rem;
        }
        .streamlit-info-text a {
            color: #06b6d4;
            text-decoration: none;
        }
    </style>
""", unsafe_allow_html=True)

# Small native header inside Streamlit
st.markdown("""
    <div class="streamlit-info-text">
        <span>🤖 <strong>Cyber Pathfinder & Grid Duel</strong> &mdash; Streamlit Cloud Mode</span>
        <span>Runs 100% serverless on client side</span>
    </div>
""", unsafe_allow_html=True)

# Load and inline CSS & JS to create a self-contained HTML page
# This eliminates the need for an external Flask server, making it fully compatible with Streamlit Community Cloud.
@st.cache_data
def get_self_contained_html():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path settings
    html_path = os.path.join(base_dir, "templates", "index.html")
    css_path = os.path.join(base_dir, "static", "css", "style.css")
    js_path = os.path.join(base_dir, "static", "js", "main.js")
    
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        with open(js_path, "r", encoding="utf-8") as f:
            js_content = f.read()
            
        # Inline stylesheet replacement
        css_tag = f"<style>\n{css_content}\n</style>"
        html_content = html_content.replace(
            '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/style.css\') }}">',
            css_tag
        )
        
        # Inline script replacement
        js_tag = f"<script>\n{js_content}\n</script>"
        html_content = html_content.replace(
            '<script src="{{ url_for(\'static\', filename=\'js/main.js\') }}"></script>',
            js_tag
        )
        
        return html_content
    except Exception as e:
        return f"<h3>Error loading application files: {e}</h3>"

# Render the self-contained app inside Streamlit components.html
html_markup = get_self_contained_html()
components.html(html_markup, height=920, scrolling=True)
