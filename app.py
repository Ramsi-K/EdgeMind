#!/usr/bin/env python3
"""
MEC Inference Routing System - Streamlit Dashboard Entry Point
"""

import sys
from pathlib import Path

import streamlit as st

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    # Import after path setup
    from dashboard.mec_dashboard import main as dashboard_main

    st.set_page_config(
        page_title="MEC Orchestration Dashboard",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    dashboard_main()
