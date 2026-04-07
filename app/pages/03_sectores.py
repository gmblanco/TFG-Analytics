from pathlib import Path
from pydoc_data.topics import topics

import plotly.graph_objects as go
import streamlit as st

from data_loader import load_youtube_sentiment
from theme import COLORS, PLOTLY_BASE_LAYOUT, get_theme_tokens

BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────────────────────
# Pre-computed topic data · notebook 09 · embedding-based (all-MiniLM-L6-v2)
# Filter: sector_*=True ∩ sentiment ∈ {pos, neg} ∩ n_palabras_clean ≥ 8
# ─────────────────────────────────────────────────────────────────────────────

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
            "<strong>Educación — tensión genuina:</strong> "
            "\"AI tutoring tool\" es el único topic con mayoría positiva (68.5%). "
            "Sin embargo, \"School policy\" (89% neg), \"Academic dishonesty\" (89% neg) "
            "y \"Critical thinking\" (86% neg) revelan un miedo profundo al impacto "
            "institucional. La esperanza es puntual; el miedo es sistémico."
        ),
    },
    "employment": {
        "topics": _EMP_TOPICS,
        "insight": (
            "<strong>Empleo — negatividad dominante:</strong> "
            "\"Job displacement\" concentra 2.281 comentarios negativos (93% del topic). "
            "Incluso topics aparentemente esperanzadores como \"New AI jobs\" tienen 64% "
            "de negatividad: la percepción de nueva creación de empleo es escéptica. "
            "Solo \"Human-AI collaboration\" (33% positivo) muestra algo de optimismo real."
        ),
    },
}


# ── Data ──────────────────────────────────────────────────────────────────────

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


# ── CSS ───────────────────────────────────────────────────────────────────────

def _inject_sectores_css() -> None:
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

        /* Neutral KPI (not in global CSS) */
        .kpi-neu::before { background: var(--neu) !important; }
        .kpi-val-neu     { color: var(--neu) !important; }

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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_dark_theme(bg_value: str) -> bool:
    bg_lower = str(bg_value).lower()
    dark_candidates = {
        "#000", "#000000", "#09090b", "#0b0f19", "#0f1117", "#111827", "#0e1117",
    }
    return bg_lower in dark_candidates or "rgb(0" in bg_lower


def _kpi(label: str, value: str, detail: str, cls: str) -> str:
    suffix = cls.split()[0][4:]
    return (
        f'<div class="kpi-card {cls}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value kpi-val-{suffix}">{value}</div>'
        f'<div class="kpi-detail">{detail}</div>'
        f'</div>'
    )


# ── Charts ────────────────────────────────────────────────────────────────────

def _fears_chart(topics: list[dict]) -> go.Figure:
    tokens = get_theme_tokens()
    bg      = tokens.get("bg", "#ffffff")
    muted   = tokens.get("muted", "#667085")
    text2   = tokens.get("text2", "#667085")
    border2 = tokens.get("border2", "rgba(148,163,184,0.35)")
    is_dark = _is_dark_theme(bg)

    hover_bg   = "rgba(255,255,255,0.98)" if not is_dark else "rgba(17,24,39,0.98)"
    hover_font = "#111827" if not is_dark else "#F9FAFB"
    grid_color = "rgba(148,163,184,0.16)" if not is_dark else "rgba(148,163,184,0.10)"

    sorted_t = sorted(topics, key=lambda x: x["neg"])
    labels   = [t["label"] for t in sorted_t]
    neg_vals = [t["neg"] for t in sorted_t]
    pct_negs = [t["pct_neg"] for t in sorted_t]
    max_val  = max(neg_vals)

    fig = go.Figure(go.Bar(
        y=labels,
        x=neg_vals,
        orientation="h",
        marker=dict(color=COLORS["negative"], line=dict(width=0)),
        text=[f"{n:,}" for n in neg_vals],
        textposition="outside",
        textfont=dict(
            family="Geist Mono, monospace",
            size=11,
            color=COLORS["negative"]
        ),
        cliponaxis=False,
        customdata=pct_negs,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Comentarios negativos: %{x:,}<br>"
            "Peso negativo dentro del topic: %{customdata:.1f}%"
            "<extra></extra>"
        ),
    ))

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        height=320,
        showlegend=False,
        margin=dict(l=28, r=70, t=8, b=16),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=hover_bg,
            bordercolor=border2,
            font=dict(color=hover_font, family="Geist, sans-serif", size=13),
        ),
        xaxis=dict(
            title=None,
            showgrid=True,
            gridcolor=grid_color,
            zeroline=False,
            fixedrange=True,
            range=[0, max_val * 1.35],
            tickfont=dict(family="Geist Mono, monospace", size=10, color=muted),
        ),
        yaxis=dict(
            title=None,
            showgrid=False,
            zeroline=False,
            automargin=True,
            fixedrange=True,
            ticklabelstandoff=18,
            tickfont=dict(family="Geist, sans-serif", size=14, color=text2),
        ),
    )
    fig.update_layout(**layout)
    return fig


def _hopes_chart(topics: list[dict]) -> go.Figure:
    tokens = get_theme_tokens()
    bg      = tokens.get("bg", "#ffffff")
    muted   = tokens.get("muted", "#667085")
    text2   = tokens.get("text2", "#667085")
    border2 = tokens.get("border2", "rgba(148,163,184,0.35)")
    is_dark = _is_dark_theme(bg)

    hover_bg   = "rgba(255,255,255,0.98)" if not is_dark else "rgba(17,24,39,0.98)"
    hover_font = "#111827" if not is_dark else "#F9FAFB"
    grid_color = "rgba(148,163,184,0.16)" if not is_dark else "rgba(148,163,184,0.10)"

    sorted_t = sorted(topics, key=lambda x: x["pos"])
    labels   = [t["label"] for t in sorted_t]
    pos_vals = [t["pos"] for t in sorted_t]
    pct_poss = [t["pct_pos"] for t in sorted_t]
    max_val  = max(pos_vals)

    fig = go.Figure(go.Bar(
        y=labels,
        x=pos_vals,
        orientation="h",
        marker=dict(color=COLORS["positive"], line=dict(width=0)),
        text=[f"{n:,}" for n in pos_vals],
        textposition="outside",
        textfont=dict(
            family="Geist Mono, monospace",
            size=11,
            color=COLORS["positive"]
        ),
        cliponaxis=False,
        customdata=pct_poss,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Comentarios positivos: %{x:,}<br>"
            "Peso positivo dentro del topic: %{customdata:.1f}%"
            "<extra></extra>"
        ),
    ))

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        height=320,
        showlegend=False,
        margin=dict(l=28, r=70, t=8, b=16),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=hover_bg,
            bordercolor=border2,
            font=dict(color=hover_font, family="Geist, sans-serif", size=13),
        ),
        xaxis=dict(
            title=None,
            showgrid=True,
            gridcolor=grid_color,
            zeroline=False,
            fixedrange=True,
            range=[0, max_val * 1.35],
            tickfont=dict(family="Geist Mono, monospace", size=10, color=muted),
        ),
        yaxis=dict(
            title=None,
            showgrid=False,
            zeroline=False,
            automargin=True,
            fixedrange=True,
            ticklabelstandoff=18,
            tickfont=dict(family="Geist, sans-serif", size=14, color=text2),
        ),
    )
    fig.update_layout(**layout)
    return fig


def _composition_chart(topics: list[dict]) -> go.Figure:
    tokens = get_theme_tokens()
    bg      = tokens.get("bg", "#ffffff")
    muted   = tokens.get("muted", "#667085")
    text2   = tokens.get("text2", "#667085")
    border2 = tokens.get("border2", "rgba(148,163,184,0.35)")
    is_dark = _is_dark_theme(bg)

    hover_bg   = "rgba(255,255,255,0.98)" if not is_dark else "rgba(17,24,39,0.98)"
    hover_font = "#111827" if not is_dark else "#F9FAFB"

    sorted_t = sorted(topics, key=lambda x: x["pct_neg"])
    labels   = [t["label"] for t in sorted_t]
    neg_pcts = [t["pct_neg"] for t in sorted_t]
    pos_pcts = [t["pct_pos"] for t in sorted_t]

    neg_text = [f"{v:.0f}%" if v >= 9 else "" for v in neg_pcts]
    pos_text = [f"{v:.0f}%" if v >= 9 else "" for v in pos_pcts]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Negativo",
        y=labels,
        x=neg_pcts,
        orientation="h",
        marker=dict(
            color=COLORS["negative"],
            line=dict(width=0),
        ),
        text=neg_text,
        textposition="inside",
        insidetextanchor="end",
        textfont=dict(
            family="Geist Mono, monospace",
            size=14,
            color="white"
        ),
        texttemplate="%{text}  ",
        customdata=pos_pcts,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Negativo: %{x:.1f}%<br>"
            "Positivo: %{customdata:.1f}%"
            "<extra></extra>"
        ),
    ))

    fig.add_trace(go.Bar(
        name="Positivo",
        y=labels,
        x=pos_pcts,
        orientation="h",
        marker=dict(
            color=COLORS["positive"],
            line=dict(width=0),
        ),
        text=pos_text,
        textposition="inside",
        insidetextanchor="end",
        textfont=dict(
            family="Geist Mono, monospace",
            size=14,
            color="white"
        ),
        customdata=neg_pcts,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Positivo: %{x:.1f}%<br>"
            "Negativo: %{customdata:.1f}%"
            "<extra></extra>"
        ),
    ))
    
    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        barmode="stack",
        bargap=0.2,
        barcornerradius= 1,
        height=400,
        margin=dict(l=28, r=26, t=10, b=44),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=hover_bg,
            bordercolor=border2,
            font=dict(color=hover_font, family="Geist, sans-serif", size=13),
        ),
        xaxis=dict(
            ticksuffix="%",
            range=[0, 101],
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            tickfont=dict(
                family="Geist Mono, monospace",
                size=10,
                color=muted
            ),
        ),
        yaxis=dict(
            title=None,
            showgrid=False,
            zeroline=False,
            automargin=True,
            fixedrange=True,
            ticklabelstandoff=20,
            tickfont=dict(
                family="Geist, sans-serif",
                size=15,
                color=text2
            ),
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.12,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="Geist Mono, monospace",
                size=11,
                color=text2
            ),
            itemsizing="constant",
        ),
    )

    fig.update_layout(**layout)
    return fig


# ── Page ──────────────────────────────────────────────────────────────────────

def main() -> None:
    _inject_sectores_css()

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="page-wrap">
            <div class="section-tag">03 · ANÁLISIS SECTORIAL</div>
            <h1 class="section-title">Miedos y esperanzas</h1>
            <p class="section-subtitle">
                El impacto percibido de la IA no es homogéneo. El sector del empleo concentra
                los mayores miedos; el educativo revela una tensión genuina entre oportunidad
                y amenaza.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Data ─────────────────────────────────────────────────────────────────
    kpis = _sector_kpis()
    glb  = kpis["global"]

    # ── Sector tabs ───────────────────────────────────────────────────────────
    tab_edu, tab_emp = st.tabs(["Educación", "Empleo"])

    for tab, sector_key, sector_name in [
        (tab_edu, "education",  "Educación"),
        (tab_emp, "employment", "Empleo"),
    ]:
        with tab:
            kpi    = kpis[sector_key]
            meta   = _SECTOR_META[sector_key]
            topics = meta["topics"]

            total_neg = sum(t["neg"] for t in topics)
            total_pos = sum(t["pos"] for t in topics)

            # ── KPI row ──────────────────────────────────────────────────────
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(
                    _kpi("% Negativo", f"{kpi['pct_neg']:.1f}%",
                         f"vs {glb['pct_neg']:.1f}% media YouTube", "kpi-neg"),
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    _kpi("% Positivo", f"{kpi['pct_pos']:.1f}%",
                         f"vs {glb['pct_pos']:.1f}% media YouTube", "kpi-pos"),
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    _kpi("% Neutral", f"{kpi['pct_neu']:.1f}%",
                         f"vs {glb['pct_neu']:.1f}% media YouTube", "kpi-neu"),
                    unsafe_allow_html=True,
                )
            with c4:
                st.markdown(
                    _kpi("Comentarios", f"{kpi['n']:,}",
                         "del corpus YouTube", "kpi-accent"),
                    unsafe_allow_html=True,
                )

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

            # ── Fears & Hopes ─────────────────────────────────────────────────
            col_fears, col_hopes = st.columns(2, gap="medium")

            with col_fears:
                with st.container(border=True):
                    st.markdown(
                        f'<p class="chart-title">Principales miedos — {sector_name}</p>'
                        f'<p class="chart-desc">'
                        f'Topics ordenados por volumen negativo absoluto · '
                        f'total comentarios negativos: {total_neg:,}</p>',
                        unsafe_allow_html=True,
                    )
                    st.plotly_chart(
                        _fears_chart(topics),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        theme=None,
                    )

            with col_hopes:
                with st.container(border=True):
                    st.markdown(
                        f'<p class="chart-title">Principales esperanzas — {sector_name}</p>'
                        f'<p class="chart-desc">'
                        f'Topics ordenados por volumen positivo absoluto · '
                        f'total comentarios positivos: {total_pos:,}</p>',
                        unsafe_allow_html=True,
                    )
                    st.plotly_chart(
                        _hopes_chart(topics),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        theme=None,
                    )

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

            # ── Composition chart ─────────────────────────────────────────────
            with st.container(border=True):
                st.markdown(
                    f'<p class="chart-title">'
                    f'Composición de sentimiento por topic — {sector_name}</p>'
                    f'<p class="chart-desc">'
                    f'% negativo vs % positivo (excluyendo neutrales)'
                    f'ordenado por negatividad</p>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(
                    _composition_chart(topics),
                    use_container_width=True,
                    config={"displayModeBar": False},
                    theme=None,
                )
            

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

            # ── Insight ───────────────────────────────────────────────────────
            st.markdown(
                f'<div class="insight-box">{meta["insight"]}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    # ── Method note ───────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="method-note">
            <strong>Metodología de topics:</strong> Cada comentario se asigna al topic cuya
            descripción semántica maximiza la similitud coseno con su embedding (modelo
            <code>all-MiniLM-L6-v2</code>, umbral 0.30). El análisis excluye comentarios
            neutrales y textos con menos de 8 palabras para aislar señal de opinión clara.
            Los topics son exclusivos de cada sector.
            Datos: YouTube · <code>sector_education=True</code> o
            <code>sector_employment=True</code>.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
