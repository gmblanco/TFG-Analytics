from pathlib import Path
from pydoc_data.topics import topics

import plotly.graph_objects as go
import streamlit as st

from data_loader import load_youtube_sentiment
from theme import COLORS, PLOTLY_BASE_LAYOUT, get_theme_tokens

BASE_DIR = Path(__file__).resolve().parent.parent

# Topics pre-calculados en notebook 09 (all-MiniLM-L6-v2, umbral 0.30)
# Filtro: sector_*=True, sentiment ∈ {pos, neg}, n_palabras_clean ≥ 8

_EDU_TOPICS = [
    {"label": "School policy",       "neg": 953,  "pos": 118, "total": 1071, "pct_neg": 89.0, "pct_pos": 11.0},
    {"label": "Academic dishonesty", "neg": 480,  "pos":  57, "total":  537, "pct_neg": 89.4, "pct_pos": 10.6},
    {"label": "Critical thinking",   "neg": 432,  "pos":  73, "total":  505, "pct_neg": 85.5, "pct_pos": 14.5},
    {"label": "Teacher replacement", "neg": 899,  "pos": 332, "total": 1231, "pct_neg": 73.0, "pct_pos": 27.0},
    {"label": "Workforce prep.",     "neg": 379,  "pos": 175, "total":  554, "pct_neg": 68.4, "pct_pos": 31.6},
    {"label": "AI access & equity",  "neg": 256,  "pos": 164, "total":  420, "pct_neg": 61.0, "pct_pos": 39.0},
    {"label": "AI tutoring tool",    "neg": 307,  "pos": 668, "total":  975, "pct_neg": 31.5, "pct_pos": 68.5},
]

_EMP_TOPICS = [
    {"label": "Job displacement",    "neg": 2281, "pos": 161, "total": 2442, "pct_neg": 93.4, "pct_pos":  6.6},
    {"label": "Economic inequality", "neg":  786, "pos":  67, "total":  853, "pct_neg": 92.1, "pct_pos":  7.9},
    {"label": "Specific job threat", "neg":  922, "pos": 198, "total": 1120, "pct_neg": 82.3, "pct_pos": 17.7},
    {"label": "Reskilling & adapt.", "neg":  302, "pos": 105, "total":  407, "pct_neg": 74.2, "pct_pos": 25.8},
    {"label": "AI productivity",     "neg":  507, "pos": 181, "total":  688, "pct_neg": 73.7, "pct_pos": 26.3},
    {"label": "Human-AI collab.",    "neg":  506, "pos": 247, "total":  753, "pct_neg": 67.2, "pct_pos": 32.8},
    {"label": "New AI jobs",         "neg":  594, "pos": 336, "total":  930, "pct_neg": 63.9, "pct_pos": 36.1},
]

_SECTOR_META = {
    "education": {
        "topics": _EDU_TOPICS,
        "insight": (
            "<div style='line-height:1.45;'>"
            "<div style='font-weight:700; font-size:1.08rem; color:#d97706; margin-bottom:10px;'>Educación</div>"
            "<strong style='color:#111827;'>AI tutoring tool</strong> es el único topic en el que predominan los comentarios positivos (68.5%). "
            "En cambio, temas como <strong style='color:#111827;'>School policy</strong> (89% negativo), "
            "<strong style='color:#111827;'>Academic dishonesty</strong> (89% negativo) y "
            "<strong style='color:#111827;'>Critical thinking</strong> (86% negativo) concentran una percepción mucho más crítica."
            "<br>"
            "Por tanto, los resultados muestran que en educación la IA genera preocupación en el plano institucional, "
            "aunque también se reconoce su utilidad como apoyo al aprendizaje."
            "</div>"
        ),
    },
    "employment": {
        "topics": _EMP_TOPICS,
        "insight": (
            "<div style='line-height:1.45;'>"
            "<div style='font-weight:700; font-size:1.08rem; color:#d97706; margin-bottom:10px;'>Empleo</div>"
            "<strong style='color:#111827;'>Job displacement</strong> es el topic con mayor volumen de comentarios negativos, con 2.281 registros "
            "y un 93% de negatividad dentro del propio tema. "
            "Además, incluso topics que en principio podrían asociarse a oportunidades, como "
            "<strong style='color:#111827;'>New AI jobs</strong>, mantienen un tono mayoritariamente negativo (64%)."
            "<br>"
            "Esto sugiere que, en el ámbito laboral, la IA se percibe sobre todo como una amenaza más que como una oportunidad."
            "</div>"
        ),
    },
}


@st.cache_data(show_spinner=False)
def _sector_kpis() -> dict:
    yt = load_youtube_sentiment()
    total_yt = len(yt)
    g = yt["sentiment_label"].value_counts().to_dict()
    result: dict = {
        "global": {
            "pct_neg": g.get("negative", 0) / total_yt * 100,
            "pct_pos": g.get("positive", 0) / total_yt * 100,
            "pct_neu": g.get("neutral",  0) / total_yt * 100,
        }
    }
    for sector_key, col in [
        ("education",  "sector_education"),
        ("employment", "sector_employment"),
    ]:
        sub = yt[yt[col] == True]
        n = len(sub)
        s = sub["sentiment_label"].value_counts().to_dict()
        result[sector_key] = {
            "n":       n,
            "pct_neg": s.get("negative", 0) / n * 100,
            "pct_pos": s.get("positive", 0) / n * 100,
            "pct_neu": s.get("neutral",  0) / n * 100,
        }
    return result


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        div[data-baseweb="tab-list"] {
            gap: 0.55rem;
            border-bottom: none !important;
            box-shadow: none !important;
            margin-bottom: 1.15rem;
        }
        div[data-baseweb="tab-highlight"],
        div[data-baseweb="tab-border"] { display: none !important; }

        button[role="tab"] {
            height: 42px !important;
            padding: 0 22px !important;
            border-radius: 999px !important;
            border: 1px solid rgba(245,158,11,0.18) !important;
            background: rgba(255,255,255,0.75) !important;
            color: #6b7280 !important;
            font-size: 0.96rem !important;
            font-weight: 500 !important;
            box-shadow: none !important;
            transition: all 0.18s ease !important;
        }
        button[role="tab"]:hover {
            color: #b45309 !important;
            border-color: rgba(245,158,11,0.35) !important;
            background: rgba(245,158,11,0.05) !important;
        }
        button[role="tab"][aria-selected="true"] {
            background: linear-gradient(180deg,#f59e0b 0%,#d97706 100%) !important;
            color: #000 !important;
            border: 1px solid #d97706 !important;
            font-weight: 600 !important;
            box-shadow: 0 6px 18px rgba(217,119,6,0.18) !important;
        }
        button[role="tab"]::after,
        button[role="tab"]::before { display: none !important; }

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
        div[data-testid="stPlotlyChart"] { margin-top: 0.15rem; }

        div[data-testid="stBorderContainer"] {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            padding: 20px 20px 8px !important;
        }
        div[data-testid="stBorderContainer"] > div {
            background: transparent !important;
        }
        div[data-testid="stBorderContainer"] div[data-testid="stPlotlyChart"],
        div[data-testid="stBorderContainer"] div[data-testid="stPlotlyChart"] > div {
            background: transparent !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _is_dark_theme(bg_value: str) -> bool:
    dark_candidates = {
        "#000", "#000000", "#09090b", "#0b0f19", "#0f1117", "#111827", "#0e1117",
    }
    return str(bg_value).lower() in dark_candidates or "rgb(0" in str(bg_value).lower()


_SENTIMENT_COLORS = {
    "neg": "#EF4444",
    "pos": "#22C55E",
    "neu": "#94A3B8",
}


def _kpi_card(label: str, value: str, detail: str, cls: str) -> str:
    suffix = cls.split()[0][4:]
    accent = _SENTIMENT_COLORS.get(suffix, "#94A3B8")
    return (
        '<div style="'
        'background:var(--surface);border:1px solid var(--border);'
        'border-radius:12px;padding:12px 24px;display:flex;'
        'flex-direction:column;gap:6px;box-sizing:border-box;">'

        '<div style="font-family:Manrope,sans-serif;font-size:13px;font-weight:800;'
        'letter-spacing:0.14em;text-transform:uppercase;color:var(--text2);'
        'text-align:center;width:100%;">' + label + '</div>'

        '<div style="font-family:sans-serif;font-size:28px;font-weight:700;'
        'line-height:1.1;color:' + accent + ';text-align:center;">' + value + '</div>'

        '<div style="font-family:monospace;font-size:13px;color:var(--text2);'
        'text-align:center;margin-top:2px;">' + detail + '</div>'

        '</div>'
    )


def _chart_theme_vars() -> dict:
    tokens = get_theme_tokens()
    is_dark = _is_dark_theme(tokens.get("bg", "#ffffff"))
    return {
        "muted":      tokens.get("muted", "#667085"),
        "text2":      tokens.get("text2", "#667085"),
        "border2":    tokens.get("border2", "rgba(148,163,184,0.35)"),
        "hover_bg":   "rgba(255,255,255,0.98)" if not is_dark else "rgba(17,24,39,0.98)",
        "hover_font": "#111827" if not is_dark else "#F9FAFB",
        "grid_color": "rgba(148,163,184,0.16)" if not is_dark else "rgba(148,163,184,0.10)",
    }


def _bar_chart_negative(sector_topics: list[dict]) -> go.Figure:
    t = _chart_theme_vars()
    sorted_topics = sorted(sector_topics, key=lambda x: x["neg"])
    labels   = [item["label"]   for item in sorted_topics]
    neg_vals = [item["neg"]     for item in sorted_topics]
    pct_neg  = [item["pct_neg"] for item in sorted_topics]

    fig = go.Figure(go.Bar(
        y=labels,
        x=neg_vals,
        orientation="h",
        marker=dict(color=COLORS["negative"], line=dict(width=0)),
        text=[f"{n:,}" for n in neg_vals],
        textposition="outside",
        textfont=dict(family="Geist Mono, monospace", size=11, color=COLORS["negative"]),
        cliponaxis=False,
        customdata=pct_neg,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Comentarios negativos: %{x:,}<br>"
            "Peso dentro del topic: %{customdata:.1f}%"
            "<extra></extra>"
        ),
    ))

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        height=320, showlegend=False,
        margin=dict(l=28, r=70, t=8, b=16),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=t["hover_bg"], bordercolor=t["border2"],
            font=dict(color=t["hover_font"], family="Geist, sans-serif", size=13),
        ),
        xaxis=dict(
            title=None, showgrid=True, gridcolor=t["grid_color"],
            zeroline=False, fixedrange=True, range=[0, max(neg_vals) * 1.35],
            tickfont=dict(family="Geist Mono, monospace", size=10, color=t["muted"]),
        ),
        yaxis=dict(
            title=None, showgrid=False, zeroline=False,
            automargin=True, fixedrange=True, ticklabelstandoff=18,
            tickfont=dict(family="Geist, sans-serif", size=14, color=t["text2"]),
        ),
    )
    fig.update_layout(**layout)
    return fig


def _bar_chart_positive(sector_topics: list[dict]) -> go.Figure:
    t = _chart_theme_vars()
    sorted_topics = sorted(sector_topics, key=lambda x: x["pos"])
    labels   = [item["label"]   for item in sorted_topics]
    pos_vals = [item["pos"]     for item in sorted_topics]
    pct_pos  = [item["pct_pos"] for item in sorted_topics]

    fig = go.Figure(go.Bar(
        y=labels,
        x=pos_vals,
        orientation="h",
        marker=dict(color=COLORS["positive"], line=dict(width=0)),
        text=[f"{n:,}" for n in pos_vals],
        textposition="outside",
        textfont=dict(family="Geist Mono, monospace", size=11, color=COLORS["positive"]),
        cliponaxis=False,
        customdata=pct_pos,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Comentarios positivos: %{x:,}<br>"
            "Peso dentro del topic: %{customdata:.1f}%"
            "<extra></extra>"
        ),
    ))

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        height=320, showlegend=False,
        margin=dict(l=28, r=70, t=8, b=16),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=t["hover_bg"], bordercolor=t["border2"],
            font=dict(color=t["hover_font"], family="Geist, sans-serif", size=13),
        ),
        xaxis=dict(
            title=None, showgrid=True, gridcolor=t["grid_color"],
            zeroline=False, fixedrange=True, range=[0, max(pos_vals) * 1.35],
            tickfont=dict(family="Geist Mono, monospace", size=10, color=t["muted"]),
        ),
        yaxis=dict(
            title=None, showgrid=False, zeroline=False,
            automargin=True, fixedrange=True, ticklabelstandoff=18,
            tickfont=dict(family="Geist, sans-serif", size=14, color=t["text2"]),
        ),
    )
    fig.update_layout(**layout)
    return fig


def _bar_chart_composition(sector_topics: list[dict]) -> go.Figure:
    t = _chart_theme_vars()
    sorted_topics = sorted(sector_topics, key=lambda x: x["pct_neg"])
    labels   = [item["label"]   for item in sorted_topics]
    neg_pcts = [item["pct_neg"] for item in sorted_topics]
    pos_pcts = [item["pct_pos"] for item in sorted_topics]

    neg_labels = [f"{v:.0f}%" if v >= 9 else "" for v in neg_pcts]
    pos_labels = [f"{v:.0f}%" if v >= 9 else "" for v in pos_pcts]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Negativo",
        y=labels, x=neg_pcts, orientation="h",
        marker=dict(color=COLORS["negative"], line=dict(width=0)),
        text=neg_labels, textposition="inside", insidetextanchor="end",
        textfont=dict(family="Geist Mono, monospace", size=14, color="white"),
        texttemplate="%{text}  ",
        customdata=pos_pcts,
        hovertemplate=(
            "<b>%{y}</b><br>Negativo: %{x:.1f}%<br>Positivo: %{customdata:.1f}%<extra></extra>"
        ),
    ))

    fig.add_trace(go.Bar(
        name="Positivo",
        y=labels, x=pos_pcts, orientation="h",
        marker=dict(color=COLORS["positive"], line=dict(width=0)),
        text=pos_labels, textposition="inside", insidetextanchor="end",
        textfont=dict(family="Geist Mono, monospace", size=14, color="white"),
        customdata=neg_pcts,
        hovertemplate=(
            "<b>%{y}</b><br>Positivo: %{x:.1f}%<br>Negativo: %{customdata:.1f}%<extra></extra>"
        ),
    ))

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        barmode="stack", bargap=0.2, barcornerradius=1,
        height=400, margin=dict(l=28, r=26, t=10, b=44),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=t["hover_bg"], bordercolor=t["border2"],
            font=dict(color=t["hover_font"], family="Geist, sans-serif", size=13),
        ),
        xaxis=dict(
            ticksuffix="%", range=[0, 101], showgrid=False,
            zeroline=False, fixedrange=True,
            tickfont=dict(family="Geist Mono, monospace", size=10, color=t["muted"]),
        ),
        yaxis=dict(
            title=None, showgrid=False, zeroline=False,
            automargin=True, fixedrange=True, ticklabelstandoff=20,
            tickfont=dict(family="Geist, sans-serif", size=15, color=t["text2"]),
        ),
        legend=dict(
            orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(family="Geist Mono, monospace", size=11, color=t["text2"]),
            itemsizing="constant",
        ),
    )
    fig.update_layout(**layout)
    return fig


def main() -> None:
    _inject_css()

    st.markdown(
        """
        <div class="page-wrap">
            <div class="section-tag">03 · ANÁLISIS SECTORIAL</div>
            <h1 class="section-title">Comparativa sectorial</h1>
            <p class="section-subtitle">
                Esta sección compara cómo se percibe la IA en educación y empleo, identificando las diferencias de sentimiento y los temas que concentran mayor rechazo o valoración positiva.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    kpis        = _sector_kpis()
    global_kpis = kpis["global"]

    tab_edu, tab_emp = st.tabs(["Educación", "Empleo"])

    for tab, sector_key, sector_name in [
        (tab_edu, "education",  "Educación"),
        (tab_emp, "employment", "Empleo"),
    ]:
        with tab:
            kpi           = kpis[sector_key]
            meta          = _SECTOR_META[sector_key]
            sector_topics = meta["topics"]

            total_neg = sum(t["neg"] for t in sector_topics)
            total_pos = sum(t["pos"] for t in sector_topics)

            _, c1, c2, c3, _ = st.columns([0.6, 1, 1, 1, 0.6])
            with c1:
                st.markdown(
                    _kpi_card("% Negativo", f"{kpi['pct_neg']:.1f}%",
                              f"vs {global_kpis['pct_neg']:.1f}% media YouTube", "kpi-neg"),
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    _kpi_card("% Positivo", f"{kpi['pct_pos']:.1f}%",
                              f"vs {global_kpis['pct_pos']:.1f}% media YouTube", "kpi-pos"),
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    _kpi_card("% Neutral", f"{kpi['pct_neu']:.1f}%",
                              f"vs {global_kpis['pct_neu']:.1f}% media YouTube", "kpi-neu"),
                    unsafe_allow_html=True,
                )

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

            col_neg, col_pos = st.columns(2, gap="medium")

            with col_neg:
                with st.container(border=True):
                    st.markdown(
                        f'<p class="chart-title">Topics con más rechazo: &nbsp; &nbsp;{sector_name}</p>'
                        f'<p class="chart-desc">Total de comentarios negativos: {total_neg:,}</p>',
                        unsafe_allow_html=True,
                    )
                    st.plotly_chart(
                        _bar_chart_negative(sector_topics),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        theme=None,
                    )

            with col_pos:
                with st.container(border=True):
                    st.markdown(
                        f'<p class="chart-title">Topics con más valoración positiva: &nbsp; &nbsp;{sector_name}</p>'
                        f'<p class="chart-desc">Total de comentarios positivos: {total_pos:,}</p>',
                        unsafe_allow_html=True,
                    )
                    st.plotly_chart(
                        _bar_chart_positive(sector_topics),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        theme=None,
                    )

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown(
                    f'<p class="chart-title">Composición de sentimiento por topic: &nbsp; &nbsp;{sector_name}</p>'
                    f'<p class="chart-desc">% negativo vs % positivo (excluyendo neutrales) </p>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(
                    _bar_chart_composition(sector_topics),
                    use_container_width=True,
                    config={"displayModeBar": False},
                    theme=None,
                )

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

            st.markdown(
                f'<div class="insight-box">{meta["insight"]}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()