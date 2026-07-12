import streamlit as st
import threading
import time
import socket
from app import app  # Import Flask app from app.py

def is_port_in_use(port):
    """Check if a local port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def run_flask():
    """Run the Flask server on port 5000."""
    # Run with debug=False and use_reloader=False to prevent issues in background thread
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

# Start Flask in a background thread if it is not already running on port 5000
if not is_port_in_use(5000):
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    # Give the server a moment to start
    time.sleep(1.5)

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
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            max-width: 100% !important;
        }
        
        /* Styling info text */
        .streamlit-info-text {
            font-family: 'Space Grotesk', sans-serif;
            color: #9ca3af;
            font-size: 0.9rem;
            margin-bottom: 1rem;
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
        <span>🤖 <strong>Cyber Pathfinder & Grid Duel</strong> &mdash; Streamlit Mode</span>
        <span>Running on <a href="http://127.0.0.1:8501" target="_blank">http://127.0.0.1:8501</a></span>
    </div>
""", unsafe_allow_html=True)

# Embed the Flask application in an iframe
st.iframe("http://127.0.0.1:8501", height=920)
