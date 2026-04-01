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
    "muted_dark": "#71717a",
    "bg_light": "#f0f0ed",
    "surface_light": "#f7f7f5",
    "surface2_light": "#eaeae7",
    "border_light": "#ddddd9",
    "border2_light": "#ccccc8",
    "text_light": "#0a0a0a",
    "text2_light": "#3f3f46",
    "muted_light": "#71717a",
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
    st.set_page_config(
        page_title="Percepción Pública de la IA",
        page_icon="A",
        layout="wide",
        initial_sidebar_state="expanded",
    )


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


def inject_global_css(css_path: Path) -> None:
    tokens = get_theme_tokens()
    css = css_path.read_text(encoding="utf-8")

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
        --neg: {COLORS["negative"]};
        --neu: {COLORS["neutral"]};
        --pos: {COLORS["positive"]};
        --tw: {COLORS["twitter"]};
        --yt: {COLORS["youtube"]};
    }}
    </style>
    """

    st.markdown(token_css, unsafe_allow_html=True)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_sidebar_header() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="logo-tag">TFG · 2025-2026</div>
                <div class="logo-title">Percepción de la IA</div>
                <div class="logo-sub">Twitter & YouTube · NLP</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if "theme_mode_toggle" not in st.session_state:
            st.session_state.theme_mode_toggle = get_theme_mode() == "dark"

        st.toggle(
            "Modo oscuro",
            key="theme_mode_toggle",
            on_change=_on_theme_toggle,
        )