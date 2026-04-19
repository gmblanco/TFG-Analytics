from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_loader import load_twitter_opinion, load_youtube_sentiment
from theme import COLORS, PLOTLY_BASE_LAYOUT, get_theme_tokens

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Constants ─────────────────────────────────────────────────────────────────

_CHATGPT_DATE = "2022-11-01"

_TW_MILESTONES = [
    ("2020-06-01", "GPT-3"),
    ("2021-01-01", "DALL·E"),
]

_YT_MILESTONES = [
    ("2020-06-01", "GPT-3"),
    ("2021-01-01", "DALL·E"),
    ("2022-11-01", "ChatGPT"),
    ("2023-03-01", "GPT-4"),
    ("2023-12-01", "Gemini"),
    ("2024-06-01", "EU AI Act"),
]

_SENT_LINES = [
    ("negative", COLORS["negative"], "Negativo"),
    ("neutral", COLORS["neutral"], "Neutral"),
    ("positive", COLORS["positive"], "Positivo"),
]

_PHASE_ORDER = [
    "Periodo pre-ChatGPT (2020–2022)",
    "Era Generative AI (2023–2026)",
]


# ── Data helpers ──────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _tw_annual() -> pd.DataFrame:
    tw = load_twitter_opinion().copy()
    tw["year"] = tw["date"].dt.year
    grp = tw.groupby(["year", "sentiment_label_hf"]).size().unstack(fill_value=0)
    pct = grp.div(grp.sum(axis=1), axis=0) * 100
    return pct.reset_index()


@st.cache_data(show_spinner=False)
def _tw_monthly() -> pd.DataFrame:
    tw = load_twitter_opinion().copy()
    tw["month"] = tw["date"].dt.to_period("M")
    grp = tw.groupby(["month", "sentiment_label_hf"]).size().unstack(fill_value=0)

    counts = grp.sum(axis=1)
    pct = grp.div(counts, axis=0) * 100
    pct = pct[counts >= 50]

    smooth = pct.rolling(window=3, center=True, min_periods=2).mean()
    smooth.index = smooth.index.to_timestamp()

    return smooth.reset_index().rename(columns={"month": "date"})


@st.cache_data(show_spinner=False)
def _yt_monthly() -> pd.DataFrame:
    yt = load_youtube_sentiment().copy()
    yt["month"] = yt["date"].dt.to_period("M")
    grp = yt.groupby(["month", "sentiment_label"]).size().unstack(fill_value=0)

    counts = grp.sum(axis=1)
    pct = grp.div(counts, axis=0) * 100
    pct = pct[counts >= 50]

    smooth = pct.rolling(window=3, center=True, min_periods=2).mean()
    smooth.index = smooth.index.to_timestamp()

    return smooth.reset_index().rename(columns={"month": "date"})


@st.cache_data(show_spinner=False)
def _yt_prepost() -> pd.DataFrame:
    yt = load_youtube_sentiment().copy()
    cutoff = pd.Timestamp(_CHATGPT_DATE)

    if yt["date"].dt.tz is not None:
        cutoff = cutoff.tz_localize("UTC")

    yt["fase"] = (yt["date"] >= cutoff).map(
        {
            False: "Periodo pre-ChatGPT (2020–2022)",
            True: "Era Generative AI (2023–2026)",
        }
    )

    grp = yt.groupby(["fase", "sentiment_label"]).size().unstack(fill_value=0)
    pct = (grp.div(grp.sum(axis=1), axis=0) * 100).reset_index()

    pct["fase"] = pd.Categorical(pct["fase"], categories=_PHASE_ORDER, ordered=True)
    pct = pct.sort_values("fase").reset_index(drop=True)

    return pct


# ── UI / CSS helpers ──────────────────────────────────────────────────────────

def _inject_temporal_css() -> None:
    st.markdown(
        """
        <style>
        div[data-baseweb="tab-list"] {
            gap: 0.55rem;
            border-bottom: none !important;
            box-shadow: none !important;
            margin-bottom: 1.15rem;
        }

        div[data-baseweb="tab-highlight"] {
            display: none !important;
        }

        div[data-baseweb="tab-border"] {
            display: none !important;
        }

        button[role="tab"] {
            height: 42px !important;
            padding: 0 18px !important;
            border-radius: 999px !important;
            border: 1px solid rgba(239, 68, 68, 0.18) !important;
            background: rgba(255,255,255,0.75) !important;
            color: #6b7280 !important;
            font-size: 0.96rem !important;
            font-weight: 500 !important;
            box-shadow: none !important;
            transition: all 0.18s ease !important;
        }

        button[role="tab"]:hover {
            color: #b91c1c !important;
            border-color: rgba(239, 68, 68, 0.35) !important;
            background: rgba(239, 68, 68, 0.05) !important;
        }

        button[role="tab"][aria-selected="true"] {
            background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%) !important;
            color: white !important;
            border: 1px solid #dc2626 !important;
            font-weight: 600 !important;
            box-shadow: 0 6px 18px rgba(220, 38, 38, 0.18) !important;
        }

        button[role="tab"]::after,
        button[role="tab"]::before {
            display: none !important;
        }

        .chart-title {
            margin: 0 0 0.18rem 0;
            font-size: 1.08rem;
            font-weight: 700;
            line-height: 1.3;
            color: inherit;
        }

        .chart-desc {
            margin: 0 0 0.9rem 0;
            font-size: 0.98rem;
            line-height: 1.5;
            color: var(--text2, #667085);
        }

        div[data-testid="stPlotlyChart"] {
            margin-top: 0.15rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Plot helpers ──────────────────────────────────────────────────────────────

def _is_dark_theme(bg_value: str) -> bool:
    bg_lower = str(bg_value).lower()
    dark_candidates = {
        "#000",
        "#000000",
        "#0b0f19",
        "#0f1117",
        "#111827",
        "#0e1117",
    }
    return bg_lower in dark_candidates or "rgb(0" in bg_lower


def _add_milestones_aligned(
    fig: go.Figure,
    milestones: list[tuple[str, str]],
    line_color: str,
    label_bg: str,
    label_border: str,
    label_font: str,
) -> None:
    for date_str, name in milestones:
        fig.add_vline(
            x=date_str,
            line_width=1,
            line_dash="dot",
            line_color=line_color,
            layer="above",
        )

        fig.add_annotation(
            x=date_str,
            yref="paper",
            y=1.03,
            text=name,
            showarrow=False,
            xanchor="center",
            yanchor="bottom",
            align="center",
            font=dict(
                size=10,
                color=label_font,
                family="Geist Mono, monospace",
            ),
            bgcolor=label_bg,
            bordercolor=label_border,
            borderwidth=1,
            borderpad=4,
        )


# ── Chart builders ────────────────────────────────────────────────────────────

def _hero_chart(platform: str) -> go.Figure:
    tokens = get_theme_tokens()
    is_yt = platform == "YouTube"
    df = _yt_monthly() if is_yt else _tw_monthly()
    milestones = _YT_MILESTONES if is_yt else _TW_MILESTONES

    fig = go.Figure()

    # Tokens / colores base
    bg = tokens.get("bg", "#ffffff")
    text = tokens.get("text", "#0f172a")
    text2 = tokens.get("text2", "#667085")
    muted = tokens.get("muted", "#667085")
    border = tokens.get("border", "rgba(148,163,184,0.20)")
    border2 = tokens.get("border2", "rgba(148,163,184,0.35)")
    is_dark = _is_dark_theme(bg)

    grid_color = "rgba(148,163,184,0.16)" if not is_dark else "rgba(148,163,184,0.12)"
    milestone_line = "rgba(148,163,184,0.38)" if not is_dark else "rgba(148,163,184,0.26)"

    label_bg = "rgba(255,255,255,0.96)" if not is_dark else "rgba(17,24,39,0.94)"
    label_border = "rgba(148,163,184,0.35)" if not is_dark else "rgba(148,163,184,0.22)"
    label_font = "#344054" if not is_dark else "#F3F4F6"

    hover_bg = "rgba(255,255,255,0.98)" if not is_dark else "rgba(17,24,39,0.98)"
    hover_font = "#111827" if not is_dark else "#F9FAFB"

    # Sombreado pre / post solo en YouTube
    if is_yt and len(df):
        x_min = df["date"].min()
        x_max = df["date"].max()

        fig.add_vrect(
            x0=x_min,
            x1=_CHATGPT_DATE,
            fillcolor="rgba(148,163,184,0.05)" if not is_dark else "rgba(148,163,184,0.045)",
            line_width=0,
            layer="below",
        )
        fig.add_vrect(
            x0=_CHATGPT_DATE,
            x1=x_max,
            fillcolor="rgba(239,68,68,0.045)" if not is_dark else "rgba(239,68,68,0.055)",
            line_width=0,
            layer="below",
        )

    # Líneas
    for sent_key, color, label in _SENT_LINES:
        if sent_key not in df.columns:
            continue

        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df[sent_key],
                name=label,
                mode="lines",
                line=dict(color=color, width=3),
                hovertemplate=f"{label}: %{{y:.1f}}%<extra></extra>",
            )
        )

    # Hitos alineados
    _add_milestones_aligned(
        fig=fig,
        milestones=milestones,
        line_color=milestone_line,
        label_bg=label_bg,
        label_border=label_border,
        label_font=label_font,
    )

    # Layout
    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        height=430,
        margin=dict(l=36, r=24, t=56, b=50),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=hover_bg,
            bordercolor=border2,
            font=dict(
                color=hover_font,
                family="Geist, sans-serif",
                size=13,
            ),
            align="left",
        ),
        xaxis=dict(
            title=None,
            showgrid=False,
            zeroline=False,
            tickformat="%Y",
            hoverformat="%b %Y",
            dtick="M12",
            ticklabelmode="period",
            ticks="outside",
            ticklen=0,
            tickfont=dict(
                family="Geist Mono, monospace",
                size=11,
                color=muted,
            ),
            linecolor="rgba(0,0,0,0)",
            rangeslider=dict(visible=False),
            fixedrange=True,
        ),
        yaxis=dict(
            title=None,
            ticksuffix="%",
            range=[0, 75],
            tickmode="array",
            tickvals=[0, 10, 20, 30, 40, 50, 60, 70, 75],
            showgrid=True,
            gridcolor=grid_color,
            gridwidth=1,
            zeroline=False,
            tickfont=dict(
                family="Geist Mono, monospace",
                size=11,
                color=muted,
            ),
            fixedrange=True,
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.10,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="Geist Mono, monospace",
                size=11,
                color=text2,
            ),
            itemsizing="constant",
        ),
    )

    fig.update_layout(**layout)
    return fig


def _prepost_bar_chart() -> go.Figure:
    tokens = get_theme_tokens()
    df = _yt_prepost().copy()

    bg = tokens.get("bg", "#ffffff")
    text = tokens.get("text", "#0f172a")
    text2 = tokens.get("text2", "#667085")
    muted = tokens.get("muted", "#667085")
    border2 = tokens.get("border2", "rgba(148,163,184,0.35)")
    is_dark = _is_dark_theme(bg)

    grid_color = "rgba(148,163,184,0.16)" if not is_dark else "rgba(148,163,184,0.12)"
    hover_bg = "rgba(255,255,255,0.98)" if not is_dark else "rgba(17,24,39,0.98)"
    hover_font = "#111827" if not is_dark else "#F9FAFB"

    phase_labels = {
        _PHASE_ORDER[0]: "Pre-ChatGPT\n(2020–2022)",
        _PHASE_ORDER[1]: "Era GenAI\n(2023–2026)",
    }

    df["fase_short"] = df["fase"].map(phase_labels)
    x_vals = [phase_labels[_PHASE_ORDER[0]], phase_labels[_PHASE_ORDER[1]]]

    fig = go.Figure()

    # Fondos suaves por bloque temporal
    fig.add_vrect(
        x0=-0.45,
        x1=0.45,
        fillcolor="rgba(148,163,184,0.05)" if not is_dark else "rgba(148,163,184,0.04)",
        line_width=0,
        layer="below",
    )
    fig.add_vrect(
        x0=0.55,
        x1=1.45,
        fillcolor="rgba(239,68,68,0.05)" if not is_dark else "rgba(239,68,68,0.045)",
        line_width=0,
        layer="below",
    )

    # Barras con etiquetas de valor
    for sent_key, color, label in _SENT_LINES:
        if sent_key not in df.columns:
            continue

        y_vals = df[sent_key].round(1).tolist()

        fig.add_trace(
            go.Bar(
                name=label,
                x=x_vals,
                y=y_vals,
                marker=dict(
                    color=color,
                    line=dict(
                        color="rgba(255,255,255,0.10)" if is_dark else "rgba(255,255,255,0.55)",
                        width=1,
                    ),
                ),
                text=[f"{v:.1f}%" for v in y_vals],
                textposition="outside",
                textfont=dict(
                    family="Geist Mono, monospace",
                    size=11,
                    color=color if not is_dark else "#F3F4F6",
                ),
                cliponaxis=False,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    + f"{label}: %{{y:.1f}}%"
                    + "<extra></extra>"
                ),
            )
        )

    # Etiquetas de periodo arriba
    fig.add_annotation(
        x=x_vals[0],
        y=64.5,
        text="Antes del lanzamiento",
        showarrow=False,
        font=dict(
            family="Geist, sans-serif",
            size=11,
            color=muted,
        ),
    )

    fig.add_annotation(
        x=x_vals[1],
        y=64.5,
        text="Después del lanzamiento",
        showarrow=False,
        font=dict(
            family="Geist, sans-serif",
            size=11,
            color=muted,
        ),
    )

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        height=340,
        barmode="group",
        bargap=0.28,
        bargroupgap=0.12,
        margin=dict(l=24, r=24, t=16, b=52),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="closest",
        uniformtext_minsize=10,
        uniformtext_mode="hide",
        hoverlabel=dict(
            bgcolor=hover_bg,
            bordercolor=border2,
            font=dict(
                color=hover_font,
                family="Geist, sans-serif",
                size=13,
            ),
        ),
        yaxis=dict(
            ticksuffix="%",
            range=[0, 68],
            tickmode="array",
            tickvals=[0, 10, 20, 30, 40, 50, 60],
            gridcolor=grid_color,
            zeroline=False,
            tickfont=dict(
                family="Geist Mono, monospace",
                size=11,
                color=muted,
            ),
            fixedrange=True,
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(
                family="Geist Mono, monospace",
                size=10,
                color=muted,
            ),
            fixedrange=True,
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.16,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(
                size=11,
                family="Geist Mono, monospace",
                color=text2,
            ),
            itemsizing="constant",
        ),
    )

    fig.update_layout(**layout)
    return fig


def _tw_annual_chart() -> go.Figure:
    tokens = get_theme_tokens()
    df = _tw_annual()
    fig = go.Figure()

    bg = tokens.get("bg", "#ffffff")
    text2 = tokens.get("text2", "#667085")
    muted = tokens.get("muted", "#667085")
    border2 = tokens.get("border2", "rgba(148,163,184,0.35)")
    is_dark = _is_dark_theme(bg)

    grid_color = "rgba(148,163,184,0.16)" if not is_dark else "rgba(148,163,184,0.12)"
    hover_bg = "rgba(255,255,255,0.98)" if not is_dark else "rgba(17,24,39,0.98)"
    hover_font = "#111827" if not is_dark else "#F9FAFB"

    for sent_key, color, label in _SENT_LINES:
        if sent_key not in df.columns:
            continue

        fig.add_trace(
            go.Scatter(
                x=df["year"],
                y=df[sent_key].round(1),
                name=label,
                line=dict(color=color, width=2.8),
                mode="lines+markers",
                marker=dict(
                    size=7,
                    color=bg if not is_dark else "#0b0f19",
                    line=dict(color=color, width=2.5),
                ),
                hovertemplate="<b>%{x}</b><br>" + f"{label}: %{{y:.1f}}%" + "<extra></extra>",
            )
        )

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        height=340,  # <- mismo alto que el de barras para igualar cards
        margin=dict(l=24, r=24, t=16, b=52),  # <- mismos márgenes
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=hover_bg,
            bordercolor=border2,
            font=dict(
                color=hover_font,
                family="Geist, sans-serif",
                size=13,
            ),
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickmode="linear",
            dtick=1,
            tickfont=dict(
                family="Geist Mono, monospace",
                size=11,
                color=muted,
            ),
            fixedrange=True,
        ),
        yaxis=dict(
            ticksuffix="%",
            range=[0, 68],
            tickmode="array",
            tickvals=[0, 10, 20, 30, 40, 50, 60],
            gridcolor=grid_color,
            zeroline=False,
            tickfont=dict(
                family="Geist Mono, monospace",
                size=11,
                color=muted,
            ),
            fixedrange=True,
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.16,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="Geist Mono, monospace",
                size=11,
                color=text2,
            ),
            itemsizing="constant",
        ),
    )

    fig.update_layout(**layout)
    return fig


# ── Page ──────────────────────────────────────────────────────────────────────


def main() -> None:
    _inject_temporal_css()

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="page-wrap">
            <div class="section-tag">02 · EVOLUCIÓN TEMPORAL</div>
            <h1 class="section-title">Evolución temporal del sentimiento</h1>
            <p class="section-subtitle">
                Evolución mensual del sentimiento en Twitter y YouTube a lo largo del periodo analizado.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Hero chart ───────────────────────────────────────────────────────────
    tab_tw, tab_yt = st.tabs(["Twitter", "YouTube"])

    with tab_tw:
        with st.container(border=True):
            st.markdown(
                '<p class="chart-title">Evolución del sentimiento - Twitter (2017–2021)</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                _hero_chart("Twitter"),
                use_container_width=True,
                config={"displayModeBar": False},
                theme=None,
            )

    with tab_yt:
        with st.container(border=True):
            st.markdown(
                '<p class="chart-title">Evolución del sentimiento - YouTube (2020–2026)</p>'
                '<p class="chart-desc">Media móvil suavizada · Hitos tecnológicos anotados · Sombreado pre/post ChatGPT</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                _hero_chart("YouTube"),
                use_container_width=True,
                config={"displayModeBar": False},
                theme=None,
            )

    st.markdown("<div style='height: 0.95rem;'></div>", unsafe_allow_html=True)

    # ── Secondary charts ─────────────────────────────────────────────────────
    # Twitter a la izquierda, YouTube a la derecha
    col_tw, col_yt = st.columns([1, 1], gap="large")

    with col_tw:
        with st.container(border=True):
            st.markdown(
                '<p class="chart-title">Evolución anual - Twitter (2017–2021)</p>'
                '<p class="chart-desc">Predominio de la neutralidad y aumento gradual del sentimiento negativo</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                _tw_annual_chart(),
                use_container_width=True,
                config={"displayModeBar": False},
                theme=None,
            )

    with col_yt:
        with st.container(border=True):
            st.markdown(
                '<p class="chart-title">Pre-ChatGPT vs Post-ChatGPT - YouTube</p>'
                '<p class="chart-desc">Cambio en la distribución del sentimiento</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                _prepost_bar_chart(),
                use_container_width=True,
                config={"displayModeBar": False},
                theme=None,
            )

    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # ── Insight ──────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="method-note">
            <strong>Resultado principal:</strong> los datos muestran un desplazamiento progresivo hacia la negatividad. En Twitter, esta tendencia ya se aprecia entre 2017 y 2021, mientras que en YouTube se intensifica claramente en la etapa 2022-2026.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 0.65rem;'></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()