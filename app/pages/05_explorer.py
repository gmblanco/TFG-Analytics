"""
05_explorer.py — Explorador de comentarios

Verificación cualitativa: búsqueda y filtrado interactivo sobre el corpus real.
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_loader import load_twitter_opinion, load_youtube_sentiment
from theme import COLORS, PLOTLY_BASE_LAYOUT, get_theme_tokens

BASE_DIR = Path(__file__).resolve().parent.parent

_SENT_KEYS   = ["negative", "neutral", "positive"]
_SENT_LABELS = ["Negativo", "Neutral", "Positivo"]
_SENT_COLORS = [COLORS["negative"], COLORS["neutral"], COLORS["positive"]]

_MAX_CARDS = 100   # max comments shown per query


# ── CSS ───────────────────────────────────────────────────────────────────────

def _inject_explorer_css() -> None:
    st.markdown(
        """
        <style>
        /* ── Neutral KPI (not in global CSS) ─────────────────────────────── */
        .kpi-neu::before { background: var(--neu) !important; }
        .kpi-val-neu     { color: var(--neu) !important; }

        /* ── Chart containers ─────────────────────────────────────────────── */
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
        div[data-testid="stPlotlyChart"] { margin-top: 0.15rem; }

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

        /* ── Comment cards ────────────────────────────────────────────────── */
        .comment-card {
            border: 1px solid var(--border, #27272a);
            border-radius: 12px;
            padding: 14px 18px 16px;
            margin-bottom: 10px;
            background: var(--surface, #111114);
            transition: border-color 0.15s ease;
        }
        .comment-card:hover { border-color: var(--border2, #3f3f46); }

        .comment-meta {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 10px;
        }
        .badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 0.74rem;
            font-family: "Geist Mono", monospace;
            font-weight: 600;
            line-height: 1.7;
            white-space: nowrap;
        }
        .badge-tw  { background: rgba(96,165,250,0.12);  color: #60a5fa; border: 1px solid rgba(96,165,250,0.28); }
        .badge-yt  { background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.28); }
        .badge-neg { background: rgba(239,68,68,0.10);   color: #ef4444; border: 1px solid rgba(239,68,68,0.24); }
        .badge-pos { background: rgba(34,197,94,0.10);   color: #22c55e; border: 1px solid rgba(34,197,94,0.24); }
        .badge-neu { background: rgba(148,163,184,0.10); color: #94a3b8; border: 1px solid rgba(148,163,184,0.24); }
        .badge-edu { background: rgba(245,158,11,0.10);  color: #f59e0b; border: 1px solid rgba(245,158,11,0.22); }
        .badge-emp { background: rgba(139,92,246,0.10);  color: #a78bfa; border: 1px solid rgba(139,92,246,0.22); }

        .comment-date {
            font-size: 0.78rem;
            font-family: "Geist Mono", monospace;
            color: var(--muted, #a1a1aa);
            margin-left: auto;
        }
        .comment-text {
            font-size: 0.96rem;
            line-height: 1.65;
            color: var(--text2, #d4d4d8);
            margin: 0;
            word-break: break-word;
        }

        /* ── Results count bar ────────────────────────────────────────────── */
        .results-bar {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.9rem;
        }
        .results-count {
            font-family: "Geist Mono", monospace;
            font-size: 0.82rem;
            color: var(--muted, #a1a1aa);
        }
        .results-note {
            font-family: "Geist Mono", monospace;
            font-size: 0.78rem;
            color: var(--muted, #a1a1aa);
            font-style: italic;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Data ──────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _load_combined() -> pd.DataFrame:
    """Merge Twitter and YouTube into a single explorer DataFrame."""
    tw = load_twitter_opinion().copy()
    yt = load_youtube_sentiment().copy()

    # ── Twitter ──────────────────────────────────────────────────────────────
    tw_text = "tweet_clean" if "tweet_clean" in tw.columns else "tweet"
    tw_df = pd.DataFrame({
        "text":      tw[tw_text].fillna("").astype(str),
        "date":      pd.to_datetime(tw["date"], errors="coerce", utc=False),
        "sentiment": tw["sentiment_label_hf"],
        "platform":  "Twitter",
    })
    tw_df["sector_edu"] = tw["sector"].eq("education") if "sector" in tw.columns else False
    tw_df["sector_emp"] = tw["sector"].eq("employment") if "sector" in tw.columns else False

    # ── YouTube ──────────────────────────────────────────────────────────────
    yt_text = "text_clean" if "text_clean" in yt.columns else "text"
    yt_date = pd.to_datetime(yt["date"], errors="coerce", utc=True).dt.tz_convert(None)
    yt_df = pd.DataFrame({
        "text":      yt[yt_text].fillna("").astype(str),
        "date":      yt_date,
        "sentiment": yt["sentiment_label"],
        "platform":  "YouTube",
    })
    yt_df["sector_edu"] = yt["sector_education"].astype(bool) if "sector_education" in yt.columns else False
    yt_df["sector_emp"] = yt["sector_employment"].astype(bool) if "sector_employment" in yt.columns else False

    df = pd.concat([tw_df, yt_df], ignore_index=True)
    df["date_str"] = df["date"].dt.strftime("%Y-%m").fillna("—")
    return df


# ── Helpers ───────────────────────────────────────────────────────────────────

def _kpi(label: str, value: str, detail: str, cls: str) -> str:
    suffix = cls.split()[0][4:]
    return (
        f'<div class="kpi-card {cls}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value kpi-val-{suffix}">{value}</div>'
        f'<div class="kpi-detail">{detail}</div>'
        f'</div>'
    )


def _comment_card(row: pd.Series) -> str:
    plat_cls = "badge-tw" if row["platform"] == "Twitter" else "badge-yt"
    sent_map = {
        "negative": ("badge-neg", "Negativo"),
        "neutral":  ("badge-neu", "Neutral"),
        "positive": ("badge-pos", "Positivo"),
    }
    sent_cls, sent_label = sent_map.get(row["sentiment"], ("badge-neu", "—"))

    sector_badges = ""
    if row.get("sector_edu"):
        sector_badges += '<span class="badge badge-edu">Educación</span> '
    if row.get("sector_emp"):
        sector_badges += '<span class="badge badge-emp">Empleo</span> '

    text = str(row["text"])
    if len(text) > 600:
        text = text[:597] + "…"

    return (
        f'<div class="comment-card">'
        f'  <div class="comment-meta">'
        f'    <span class="badge {plat_cls}">{row["platform"]}</span>'
        f'    <span class="badge {sent_cls}">{sent_label}</span>'
        f'    {sector_badges}'
        f'    <span class="comment-date">{row["date_str"]}</span>'
        f'  </div>'
        f'  <p class="comment-text">{text}</p>'
        f'</div>'
    )


# ── Charts ────────────────────────────────────────────────────────────────────

def _sentiment_dist_chart(df: pd.DataFrame) -> go.Figure:
    """Horizontal stacked bar: neg / neu / pos for the current selection."""
    tokens = get_theme_tokens()
    counts = df["sentiment"].value_counts()
    total  = max(len(df), 1)

    fig = go.Figure()
    for key, label, color in zip(_SENT_KEYS, _SENT_LABELS, _SENT_COLORS):
        val = counts.get(key, 0)
        pct = val / total * 100
        fig.add_trace(go.Bar(
            name=label,
            x=[pct],
            y=["Selección actual"],
            orientation="h",
            marker_color=color,
            text=f"{pct:.1f}%",
            textposition="inside" if pct >= 8 else "outside",
            textfont=dict(
                size=12,
                family="Geist Mono, monospace",
                color="white" if pct >= 8 else tokens["text2"],
            ),
            hovertemplate=f"{label}: {val:,} ({pct:.1f}%)<extra></extra>",
        ))

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        height=110,
        barmode="stack",
        margin=dict(l=0, r=0, t=4, b=4),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.08,
            xanchor="center",
            x=0.5,
            font=dict(size=11, family="Geist Mono, monospace", color=tokens["text2"]),
        ),
        xaxis=dict(visible=False, range=[0, 100]),
        yaxis=dict(visible=False),
    )
    fig.update_layout(**layout)
    return fig


def _platform_breakdown_chart(df: pd.DataFrame) -> go.Figure:
    """Grouped bars: sentiment % for Twitter vs YouTube."""
    tokens = get_theme_tokens()
    is_dark = st.session_state.get("theme_mode", "dark") == "dark"
    grid_color = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.07)"

    platforms = ["Twitter", "YouTube"]
    fig = go.Figure()

    for key, label, color in zip(_SENT_KEYS, _SENT_LABELS, _SENT_COLORS):
        vals = []
        for plat in platforms:
            sub = df[df["platform"] == plat]
            n   = max(len(sub), 1)
            pct = (sub["sentiment"] == key).sum() / n * 100
            vals.append(pct)

        fig.add_trace(go.Bar(
            name=label,
            x=platforms,
            y=vals,
            marker_color=color,
            text=[f"{v:.1f}%" for v in vals],
            textposition="outside",
            textfont=dict(size=11, family="Geist Mono, monospace",
                          color=tokens["text2"]),
            hovertemplate=f"{label} — %{{x}}: %{{y:.1f}}%<extra></extra>",
        ))

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        height=240,
        barmode="group",
        margin=dict(l=0, r=0, t=8, b=8),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.08,
            xanchor="center",
            x=0.5,
            font=dict(size=11, family="Geist Mono, monospace", color=tokens["text2"]),
        ),
        xaxis=dict(
            tickfont=dict(size=13, family="Geist Mono, monospace", color=tokens["text2"]),
            linecolor=tokens["border"],
        ),
        yaxis=dict(
            ticksuffix="%",
            range=[0, 105],
            tickfont=dict(size=11, family="Geist Mono, monospace", color=tokens["muted"]),
            gridcolor=grid_color,
        ),
    )
    fig.update_layout(**layout)
    return fig


def _temporal_chart(df: pd.DataFrame) -> go.Figure:
    """Monthly negative % over time, one line per platform."""
    tokens = get_theme_tokens()
    is_dark = st.session_state.get("theme_mode", "dark") == "dark"
    grid_color = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.07)"

    plat_cfg = [("Twitter", COLORS["twitter"]), ("YouTube", COLORS["youtube"])]
    fig = go.Figure()
    has_data = False

    for plat, color in plat_cfg:
        sub = df[df["platform"] == plat].copy()
        if sub.empty:
            continue

        sub["month"] = sub["date"].dt.to_period("M")
        grp    = sub.groupby("month")["sentiment"].value_counts().unstack(fill_value=0)
        totals = grp.sum(axis=1)
        valid  = grp[totals >= 5]
        if valid.empty or len(valid) < 2:
            continue

        neg_pct = valid.get("negative", pd.Series(dtype=float)) / totals[valid.index] * 100
        neg_pct.index = neg_pct.index.to_timestamp()
        has_data = True

        fig.add_trace(go.Scatter(
            x=neg_pct.index,
            y=neg_pct.values,
            mode="lines",
            name=plat,
            line=dict(color=color, width=2.2),
            hovertemplate=f"{plat} — %{{x|%Y-%m}}: %{{y:.1f}}%<extra></extra>",
        ))

    if not has_data:
        return go.Figure()

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        height=230,
        margin=dict(l=0, r=0, t=8, b=8),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.08,
            xanchor="center",
            x=0.5,
            font=dict(size=11, family="Geist Mono, monospace", color=tokens["text2"]),
        ),
        xaxis=dict(
            tickfont=dict(size=11, family="Geist Mono, monospace", color=tokens["muted"]),
            linecolor=tokens["border"],
            gridcolor=grid_color,
        ),
        yaxis=dict(
            title="% Negativo",
            ticksuffix="%",
            range=[0, 100],
            tickfont=dict(size=11, family="Geist Mono, monospace", color=tokens["muted"]),
            gridcolor=grid_color,
            title_font=dict(size=11, family="Geist Mono, monospace", color=tokens["muted"]),
        ),
    )
    fig.update_layout(**layout)
    return fig


# ── Page ──────────────────────────────────────────────────────────────────────

def main() -> None:
    _inject_explorer_css()

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="page-wrap">
            <div class="section-tag">05 · Verificación cualitativa</div>
            <h1 class="section-title">Explorador de comentarios</h1>
            <p class="section-subtitle">
                Busca y filtra comentarios reales del corpus. Herramienta para verificar
                cualitativamente los hallazgos cuantitativos del análisis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = _load_combined()

    # ── Filter controls ───────────────────────────────────────────────────────
    col_q, col_plat, col_sent, col_sect = st.columns([3, 1.5, 1.5, 1.5])

    with col_q:
        keyword = st.text_input(
            "keyword",
            placeholder="Buscar por keyword (ej: job, teacher, ChatGPT, replace…)",
            label_visibility="collapsed",
        )
    with col_plat:
        platform = st.selectbox(
            "plataforma",
            ["Todas las plataformas", "Twitter", "YouTube"],
            label_visibility="collapsed",
        )
    with col_sent:
        sentiment = st.selectbox(
            "sentimiento",
            ["Todo sentimiento", "Negativo", "Neutral", "Positivo"],
            label_visibility="collapsed",
        )
    with col_sect:
        sector = st.selectbox(
            "sector",
            ["Todos los sectores", "Educación", "Empleo"],
            label_visibility="collapsed",
        )

    # ── Apply filters ─────────────────────────────────────────────────────────
    filtered = df.copy()

    if keyword.strip():
        filtered = filtered[
            filtered["text"].str.contains(keyword.strip(), case=False, na=False, regex=False)
        ]

    if platform != "Todas las plataformas":
        filtered = filtered[filtered["platform"] == platform]

    _sent_map = {"Negativo": "negative", "Neutral": "neutral", "Positivo": "positive"}
    if sentiment != "Todo sentimiento":
        filtered = filtered[filtered["sentiment"] == _sent_map[sentiment]]

    if sector == "Educación":
        filtered = filtered[filtered["sector_edu"] == True]
    elif sector == "Empleo":
        filtered = filtered[filtered["sector_emp"] == True]

    total = len(filtered)
    denom = max(total, 1)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    # ── KPI row ───────────────────────────────────────────────────────────────
    n_neg = int((filtered["sentiment"] == "negative").sum())
    n_neu = int((filtered["sentiment"] == "neutral").sum())
    n_pos = int((filtered["sentiment"] == "positive").sum())
    n_tw  = int((filtered["platform"] == "Twitter").sum())
    n_yt  = total - n_tw

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            _kpi("Comentarios", f"{total:,}",
                 f"Twitter {n_tw:,} · YouTube {n_yt:,}", "kpi-accent"),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            _kpi("Negativos", f"{n_neg / denom * 100:.1f}%",
                 f"{n_neg:,} comentarios", "kpi-neg"),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            _kpi("Neutrales", f"{n_neu / denom * 100:.1f}%",
                 f"{n_neu:,} comentarios", "kpi-neu"),
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            _kpi("Positivos", f"{n_pos / denom * 100:.1f}%",
                 f"{n_pos:,} comentarios", "kpi-pos"),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    if total >= 2:
        col_left, col_right = st.columns(2)

        with col_left:
            with st.container(border=True):
                st.markdown(
                    f'<p class="chart-title">Distribución de sentimiento</p>'
                    f'<p class="chart-desc">Selección actual · {total:,} comentarios</p>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(
                    _sentiment_dist_chart(filtered),
                    use_container_width=True,
                    config={"displayModeBar": False},
                    theme=None,
                )

        with col_right:
            with st.container(border=True):
                if filtered["platform"].nunique() >= 2:
                    st.markdown(
                        '<p class="chart-title">Desglose por plataforma</p>'
                        '<p class="chart-desc">Sentimiento según plataforma · selección actual</p>',
                        unsafe_allow_html=True,
                    )
                    st.plotly_chart(
                        _platform_breakdown_chart(filtered),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        theme=None,
                    )
                else:
                    fig_tmp = _temporal_chart(filtered)
                    if fig_tmp.data:
                        st.markdown(
                            '<p class="chart-title">Evolución de la negatividad</p>'
                            '<p class="chart-desc">% negativo mensual · selección actual</p>',
                            unsafe_allow_html=True,
                        )
                        st.plotly_chart(
                            fig_tmp,
                            use_container_width=True,
                            config={"displayModeBar": False},
                            theme=None,
                        )
                    else:
                        st.markdown(
                            '<p class="chart-desc" style="padding-top:1rem">Filtra '
                            'ambas plataformas para ver la comparativa.</p>',
                            unsafe_allow_html=True,
                        )

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    # ── Insight box (keyword search) ──────────────────────────────────────────
    if total > 0 and keyword.strip():
        dom_sent  = max(_SENT_KEYS, key=lambda k: (filtered["sentiment"] == k).sum())
        dom_label = dict(zip(_SENT_KEYS, _SENT_LABELS))[dom_sent]
        dom_plat  = "Twitter" if n_tw >= n_yt else "YouTube"
        st.markdown(
            f"""
            <div class="insight-box">
                <strong>Búsqueda: «{keyword.strip()}»</strong> —
                {total:,} comentarios encontrados.
                Sentimiento dominante: <strong>{dom_label}</strong> ·
                negatividad {n_neg / denom * 100:.1f}% ·
                plataforma principal: <strong>{dom_plat}</strong>.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Comment cards ─────────────────────────────────────────────────────────
    if total == 0:
        st.markdown(
            '<div class="insight-box">No se encontraron comentarios '
            'con los filtros seleccionados.</div>',
            unsafe_allow_html=True,
        )
        return

    sampled = total > _MAX_CARDS * 3
    display = (
        filtered.sample(_MAX_CARDS, random_state=42).sort_values("date", ascending=False)
        if sampled
        else filtered.sort_values("date", ascending=False).head(_MAX_CARDS)
    )

    note = " (muestra aleatoria)" if sampled else ""
    st.markdown(
        f'<div class="results-bar">'
        f'<span class="results-count">{total:,} resultado{"s" if total != 1 else ""}</span>'
        f'<span class="results-note">mostrando {len(display)}{note}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    cards_html = "\n".join(_comment_card(row) for _, row in display.iterrows())
    st.markdown(cards_html, unsafe_allow_html=True)

    # ── Method note ───────────────────────────────────────────────────────────
    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="method-note">
            <strong>Fuentes:</strong>
            Twitter (tweets de opinión sin URL · 2016–2021) ·
            YouTube (comentarios ≥10&nbsp;palabras · 2020–2026).
            Sentimiento: <code>cardiffnlp/twitter-xlm-roberta-base-sentiment</code>.
            Sectores: clasificación por keywords y embeddings (all-MiniLM-L6-v2).
            Se muestran hasta <code>100</code> comentarios ordenados por fecha.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
