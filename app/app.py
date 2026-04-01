from pathlib import Path

import streamlit as st

from theme import init_page_config, init_theme_state, inject_global_css, render_sidebar_brand, render_sidebar_toggle

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

init_page_config()
init_theme_state()
inject_global_css(ASSETS_DIR / "style.css")

render_sidebar_brand()

pages = [
    st.Page("pages/01_overview.py", title="Overview"),
    st.Page("pages/02_temporal.py", title="Temporal"),
    st.Page("pages/03_sectores.py", title="Sectores"),
    st.Page("pages/04_crossplatform.py", title="Cross-platform"),
    st.Page("pages/05_explorer.py", title="Explorador"),
]

pg = st.navigation(pages)

render_sidebar_toggle()

pg.run()
