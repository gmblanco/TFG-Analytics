from pathlib import Path
import streamlit as st


COLORS = {
    "bg_dark": "#09090b",
    "surface_dark": "#111114",
    "surface2_dark": "#18181b",
    "border_dark": "#27272a",
    "border2_dark": "#3f3f46",
    "text_dark": "#fafafa",
    "text2_dark": "#d4d4d8",
    "muted_dark": "#a1a1aa",
    "bg_light": "#f0f0ed",
    "surface_light": "#ffffff",
    "surface2_light": "#eaeae7",
    "border_light": "#ddddd9",
    "border2_light": "#ccccc8",
    "text_light": "#0a0a0a",
    "text2_light": "#27272a",
    "muted_light": "#52525b",
    "accent": "#f59e0b",
    "accent2": "#fbbf24",
    "negative": "#ef4444",
    "neutral": "#94a3b8",
    "positive": "#22c55e",
    "twitter": "#60a5fa",
    "youtube": "#f87171",
}

SENTIMENT_ORDER = ["negative", "neutral", "positive"]
SENTIMENT_LABELS_ES = {
    "negative": "Negativo",
    "neutral": "Neutral",
    "positive": "Positivo",
}
PLATFORM_LABELS_ES = {
    "twitter": "Twitter",
    "youtube": "YouTube",
}
SECTOR_LABELS_ES = {
    "education": "Educación",
    "employment": "Empleo",
}

PLOTLY_BASE_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "margin": {"l": 20, "r": 20, "t": 30, "b": 20},
    "legend": {
        "orientation": "h",
        "yanchor": "bottom",
        "y": -0.25,
        "xanchor": "center",
        "x": 0.5,
    },
}


def init_page_config() -> None:
    try:
        st.set_page_config(
            page_title="Percepción Pública de la IA",
            page_icon="A",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    except Exception:
        pass  # ya fue llamado por app.py vía st.navigation


def init_theme_state() -> None:
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "dark"


def get_theme_mode() -> str:
    return st.session_state.get("theme_mode", "dark")


def toggle_theme() -> None:
    st.session_state.theme_mode = "light" if get_theme_mode() == "dark" else "dark"


def _on_theme_toggle() -> None:
    st.session_state.theme_mode = "dark" if st.session_state.theme_mode_toggle else "light"


def get_theme_tokens() -> dict:
    mode = get_theme_mode()

    if mode == "dark":
        return {
            "bg": COLORS["bg_dark"],
            "surface": COLORS["surface_dark"],
            "surface2": COLORS["surface2_dark"],
            "border": COLORS["border_dark"],
            "border2": COLORS["border2_dark"],
            "text": COLORS["text_dark"],
            "text2": COLORS["text2_dark"],
            "muted": COLORS["muted_dark"],
        }

    return {
        "bg": COLORS["bg_light"],
        "surface": COLORS["surface_light"],
        "surface2": COLORS["surface2_light"],
        "border": COLORS["border_light"],
        "border2": COLORS["border2_light"],
        "text": COLORS["text_light"],
        "text2": COLORS["text2_light"],
        "muted": COLORS["muted_light"],
    }


@st.cache_data(show_spinner=False)
def _read_css(path_str: str) -> str:
    return Path(path_str).read_text(encoding="utf-8")


def inject_global_css(css_path: Path) -> None:
    mode = get_theme_mode()
    tokens = get_theme_tokens()
    css = _read_css(str(css_path))

    token_css = f"""
    <style>
    :root {{
        --bg: {tokens["bg"]};
        --surface: {tokens["surface"]};
        --surface2: {tokens["surface2"]};
        --border: {tokens["border"]};
        --border2: {tokens["border2"]};
        --text: {tokens["text"]};
        --text2: {tokens["text2"]};
        --muted: {tokens["muted"]};
        --accent: {COLORS["accent"]};
        --accent2: {COLORS["accent2"]};
        --tag-color: {"#e53935" if mode == "light" else COLORS["accent"]};
        --insight-bg: {"rgba(245,158,11,0.10)" if mode == "light" else "rgba(245,158,11,0.05)"};
        --insight-border: {"rgba(245,158,11,0.32)" if mode == "light" else "rgba(245,158,11,0.16)"};
        --neg: {COLORS["negative"]};
        --neu: {COLORS["neutral"]};
        --pos: {COLORS["positive"]};
        --tw: {COLORS["twitter"]};
        --yt: {COLORS["youtube"]};
    }}
    </style>
    """

    st.markdown(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        unsafe_allow_html=True,
    )
    st.markdown(token_css, unsafe_allow_html=True)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    collapsed_rail = """
<div id="sb-collapsed-rail" style="position:fixed;top:0;left:0;width:56px;height:100vh;
z-index:99998;pointer-events:none;display:none;"></div>
<script>
(function(){
    var rail = document.getElementById('sb-collapsed-rail');
    function applyTheme(){
        var s = getComputedStyle(document.documentElement);
        rail.style.background = s.getPropertyValue('--surface').trim() || '#f7f7f5';
        rail.style.borderRight = '1px solid ' + (s.getPropertyValue('--border').trim() || '#ddddd9');
    }
    function update(){
        var sidebar = document.querySelector('section[data-testid="stSidebar"]');
        var collapsed = sidebar ? sidebar.getBoundingClientRect().right < 50 : false;
        rail.style.display = collapsed ? 'block' : 'none';
        if(collapsed) applyTheme();
        var btn = document.querySelector('button[data-testid="stSidebarCollapsedControl"]');
        if(btn && collapsed){
            btn.style.setProperty('position','fixed','important');
            btn.style.setProperty('left','7px','important');
            btn.style.setProperty('top','12px','important');
            btn.style.setProperty('width','42px','important');
            btn.style.setProperty('height','42px','important');
            btn.style.setProperty('z-index','999999','important');
        }
    }
    new MutationObserver(update).observe(document.body,{childList:true,subtree:true,attributes:true});
    setInterval(update, 200);
    update();
})();
</script>"""
    st.markdown(collapsed_rail, unsafe_allow_html=True)


def render_sidebar_brand() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="logo-tag">TFG · 2025-2026</div>
                <div class="logo-title">PERCEPCIÓN PÚBLICA DE LA IA</div>
                <div class="logo-sub">Twitter & YouTube · NLP</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_sidebar_toggle() -> None:
    with st.sidebar:
        if "theme_mode_toggle" not in st.session_state:
            st.session_state.theme_mode_toggle = get_theme_mode() == "dark"

        st.toggle(
            "Modo oscuro",
            key="theme_mode_toggle",
            on_change=_on_theme_toggle,
        )


def render_sidebar_header() -> None:
    render_sidebar_brand()
    render_sidebar_toggle()