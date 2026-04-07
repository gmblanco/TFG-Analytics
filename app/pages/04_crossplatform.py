from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from theme import COLORS, PLOTLY_BASE_LAYOUT, get_theme_tokens

BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────────────────────
# Pre-computed stats · notebook 10_cross-platform.ipynb
# ─────────────────────────────────────────────────────────────────────────────

_TW_GLOBAL = {"neg": 15.5, "neu": 56.7, "pos": 27.8, "n": 123_389}
_YT_GLOBAL = {"neg": 52.9, "neu": 26.0, "pos": 21.1, "n":  62_989}

_TW_EDU    = {"neg": 12.9, "neu": 54.6, "pos": 32.5, "n":   6_632}
_YT_EDU    = {"neg": 47.7, "neu": 28.5, "pos": 23.8, "n":  10_677}

_TW_EMP    = {"neg": 17.9, "neu": 51.9, "pos": 30.2, "n":  15_499}
_YT_EMP    = {"neg": 60.9, "neu": 22.6, "pos": 16.5, "n":  10_439}

_TW_OVLP   = {"neg": 19.8, "neu": 51.9, "pos": 28.4, "n":  22_639}
_YT_OVLP   = {"neg": 38.1, "neu": 37.1, "pos": 24.8, "n":   3_041}

# Text length percentiles · notebook 10_cross-platform.ipynb · cell 5
_TW_LEN = {"median": 16.0, "mean": 19.2, "p75": 26.0, "p90": 38.0}
_YT_LEN = {"median": 25.0, "mean": 44.1, "p75": 46.0, "p90": 89.0}

_SECTOR_META = {
    "education": {
        "tw": _TW_EDU,
        "yt": _YT_EDU,
        "label": "Educación",
        "insight": (
            "<strong>Educación — la plataforma amplifica el miedo:</strong> "
            "En Twitter, educación es el sector <em>menos</em> negativo (12.9%) y el más "
            "positivo (32.5%). En YouTube la negatividad sube a 47.7%, casi 4 veces más. "
            "El formato largo de YouTube permite articular la crítica institucional —política "
            "escolar, deshonestidad académica, pérdida de pensamiento crítico— con una "
            "extensión que Twitter (mediana 16 palabras) no permite."
        ),
    },
    "employment": {
        "tw": _TW_EMP,
        "yt": _YT_EMP,
        "label": "Empleo",
        "insight": (
            "<strong>Empleo — consenso transversal sobre el miedo:</strong> "
            "Es el sector más negativo en ambas plataformas (Twitter 17.9%, YouTube 60.9%). "
            "La diferencia de 43 puntos porcentuales entre plataformas sugiere que el formato "
            "largo de YouTube permite articular el miedo al desplazamiento laboral con mayor "
            "intensidad y detalle. Incluso en Twitter —predominantemente neutral— el empleo "
            "es el sector que genera más negatividad relativa."
        ),
    },
    "overlap": {
        "tw": _TW_OVLP,
        "yt": _YT_OVLP,
        "label": "Período solapado 2020–2021",
        "insight": (
            "<strong>Mismo período, distinta señal:</strong> "
            "Durante los dos años en que ambas plataformas coinciden, Twitter registra "
            "19.8% de negatividad frente al 38.1% de YouTube. La diferencia no puede "
            "atribuirse al contexto temporal (mismo período, misma coyuntura IA). "
            "Refleja una diferencia estructural: el formato largo de YouTube filtra "
            "y amplifica la crítica de un modo que los 280 caracteres de Twitter no permiten."
        ),
    },
}


# ── CSS ───────────────────────────────────────────────────────────────────────

def _inject_crossplatform_css() -> None:
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

        /* ── Comparison table ─────────────────────────────────────────────── */
        .cmp-table {
            width: 100%;
            border-collapse: collapse;
            font-family: Geist, sans-serif;
            font-size: 0.93rem;
        }
        .cmp-table thead th {
            text-transform: uppercase;
            letter-spacing: 0.07em;
            font-size: 0.74rem;
            font-family: "Geist Mono", monospace;
            color: var(--muted, #a1a1aa);
            padding: 0.35rem 1rem 0.65rem;
            text-align: left;
            border-bottom: 1px solid var(--border, #27272a);
            white-space: nowrap;
        }
        .cmp-table tbody tr {
            border-bottom: 1px solid var(--border, #27272a);
        }
        .cmp-table tbody tr:last-child { border-bottom: none; }
        .cmp-table tbody tr:hover { background: rgba(255,255,255,0.025); }
        .cmp-table tbody td {
            padding: 0.66rem 1rem;
            color: var(--text2, #d4d4d8);
            font-size: 0.93rem;
        }
        .cmp-table .metric-cell {
            color: var(--text, #fafafa);
            font-weight: 500;
        }
        .val-tw       { color: var(--tw,  #60a5fa); font-weight: 600; }
        .val-yt       { color: var(--yt,  #f87171); font-weight: 600; }
        .val-yt-hi    { color: var(--yt,  #f87171); font-weight: 700; }
        .val-tw-hi    { color: var(--tw,  #60a5fa); font-weight: 700; }
        .val-diff-neg { color: var(--yt,  #f87171); font-weight: 700; }
        .val-diff-muted { color: var(--muted, #a1a1aa); }
        .val-ratio    { color: var(--text2, #d4d4d8); }
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def _is_dark_theme(bg_value: str) -> bool:
    bg_lower = str(bg_value).lower()
    dark_candidates = {
        "#000", "#000000", "#09090b", "#0b0f19", "#0f1117", "#111827", "#0e1117",
    }
    return bg_lower in dark_candidates or "rgb(0" in bg_lower


def _summary_table_html() -> str:
    """HTML for the comparative summary table (Dashboard2 style)."""
    def pp(val: float) -> str:
        sign = "+" if val >= 0 else ""
        return f"{sign}{val:.1f}&nbsp;pp"

    rows = [
        (
            "Corpus total",
            f'<span class="val-tw">{_TW_GLOBAL["n"]:,} tweets</span>',
            f'<span class="val-yt">{_YT_GLOBAL["n"]:,} comentarios</span>',
            '<span class="val-diff-muted">—</span>',
        ),
        (
            "% Negativo",
            f'{_TW_GLOBAL["neg"]:.1f}%',
            f'<span class="val-yt-hi">{_YT_GLOBAL["neg"]:.1f}%</span>',
            f'<span class="val-diff-neg">{pp(_YT_GLOBAL["neg"] - _TW_GLOBAL["neg"])}</span>',
        ),
        (
            "% Positivo",
            f'<span class="val-tw-hi">{_TW_GLOBAL["pos"]:.1f}%</span>',
            f'{_YT_GLOBAL["pos"]:.1f}%',
            f'<span class="val-diff-muted">{pp(_YT_GLOBAL["pos"] - _TW_GLOBAL["pos"])}</span>',
        ),
        (
            "% Neutral",
            f'{_TW_GLOBAL["neu"]:.1f}%',
            f'{_YT_GLOBAL["neu"]:.1f}%',
            f'<span class="val-diff-muted">{pp(_YT_GLOBAL["neu"] - _TW_GLOBAL["neu"])}</span>',
        ),
        (
            "Media palabras",
            f'{_TW_LEN["mean"]:.1f}',
            f'{_YT_LEN["mean"]:.1f}',
            '<span class="val-ratio">×2.3</span>',
        ),
        (
            "Mediana palabras",
            f'{_TW_LEN["median"]:.1f}',
            f'{_YT_LEN["median"]:.1f}',
            '<span class="val-ratio">×1.6</span>',
        ),
        (
            "Empleo: % neg",
            f'{_TW_EMP["neg"]:.1f}%',
            f'<span class="val-yt-hi">{_YT_EMP["neg"]:.1f}%</span>',
            f'<span class="val-diff-neg">{pp(_YT_EMP["neg"] - _TW_EMP["neg"])}</span>',
        ),
        (
            "Educación: % neg",
            f'{_TW_EDU["neg"]:.1f}%',
            f'<span class="val-yt-hi">{_YT_EDU["neg"]:.1f}%</span>',
            f'<span class="val-diff-neg">{pp(_YT_EDU["neg"] - _TW_EDU["neg"])}</span>',
        ),
    ]

    rows_html = "\n".join(
        f'<tr><td class="metric-cell">{r[0]}</td>'
        f"<td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>"
        for r in rows
    )

    return (
        "<table class='cmp-table'>"
        "<thead><tr>"
        "<th>MÉTRICA</th>"
        "<th>TWITTER (2017–2021)</th>"
        "<th>YOUTUBE (2020–2026)</th>"
        "<th>DIFERENCIA</th>"
        "</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        "</table>"
    )


# ── Charts ────────────────────────────────────────────────────────────────────

def _platform_profile_chart() -> go.Figure:
    """Stacked 100% bar chart: composition of each platform by sentiment."""
    tokens  = get_theme_tokens()
    bg      = tokens.get("bg", "#ffffff")
    muted   = tokens.get("muted", "#a1a1aa")
    text2   = tokens.get("text2", "#667085")
    border2 = tokens.get("border2", "rgba(148,163,184,0.35)")
    is_dark = _is_dark_theme(bg)

    hover_bg   = "rgba(255,255,255,0.98)" if not is_dark else "rgba(17,24,39,0.98)"
    hover_font = "#111827" if not is_dark else "#F9FAFB"

    platforms = ["Twitter", "YouTube"]
    neg_vals  = [_TW_GLOBAL["neg"], _YT_GLOBAL["neg"]]
    neu_vals  = [_TW_GLOBAL["neu"], _YT_GLOBAL["neu"]]
    pos_vals  = [_TW_GLOBAL["pos"], _YT_GLOBAL["pos"]]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Negativo",
        x=platforms,
        y=neg_vals,
        marker=dict(color=COLORS["negative"], line=dict(width=0)),
        text=[f"{v:.1f}%" for v in neg_vals],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(family="Geist Mono, monospace", size=13, color="white"),
        hovertemplate="<b>%{x}</b><br>Negativo: %{y:.1f}%<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="Neutral",
        x=platforms,
        y=neu_vals,
        marker=dict(color=COLORS["neutral"], line=dict(width=0)),
        text=[f"{v:.1f}%" for v in neu_vals],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(family="Geist Mono, monospace", size=13, color="white"),
        hovertemplate="<b>%{x}</b><br>Neutral: %{y:.1f}%<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="Positivo",
        x=platforms,
        y=pos_vals,
        marker=dict(color=COLORS["positive"], line=dict(width=0)),
        text=[f"{v:.1f}%" for v in pos_vals],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(family="Geist Mono, monospace", size=13, color="white"),
        hovertemplate="<b>%{x}</b><br>Positivo: %{y:.1f}%<extra></extra>",
    ))

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        barmode="stack",
        bargap=0.45,
        barcornerradius=2,
        height=380,
        margin=dict(l=20, r=20, t=20, b=44),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=hover_bg,
            bordercolor=border2,
            font=dict(color=hover_font, family="Geist, sans-serif", size=13),
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            tickfont=dict(family="Geist, sans-serif", size=15, color=text2),
        ),
        yaxis=dict(
            title=None,
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            range=[0, 101],
            ticksuffix="%",
            tickfont=dict(family="Geist Mono, monospace", size=10, color=muted),
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.12,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(family="Geist Mono, monospace", size=12, color=text2),
            itemsizing="constant",
        ),
    )
    fig.update_layout(**layout)
    return fig


def _text_length_chart() -> go.Figure:
    """Horizontal grouped bars: text length percentiles (median, mean, P75, P90)."""
    tokens  = get_theme_tokens()
    bg      = tokens.get("bg", "#ffffff")
    muted   = tokens.get("muted", "#a1a1aa")
    text2   = tokens.get("text2", "#667085")
    border2 = tokens.get("border2", "rgba(148,163,184,0.35)")
    is_dark = _is_dark_theme(bg)

    hover_bg   = "rgba(255,255,255,0.98)" if not is_dark else "rgba(17,24,39,0.98)"
    hover_font = "#111827" if not is_dark else "#F9FAFB"
    grid_color = "rgba(148,163,184,0.16)" if not is_dark else "rgba(148,163,184,0.10)"

    labels  = ["Mediana", "Media", "P75", "P90"]
    tw_vals = [_TW_LEN["median"], _TW_LEN["mean"], _TW_LEN["p75"], _TW_LEN["p90"]]
    yt_vals = [_YT_LEN["median"], _YT_LEN["mean"], _YT_LEN["p75"], _YT_LEN["p90"]]
    x_max   = max(*tw_vals, *yt_vals) * 1.22

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Twitter",
        y=labels,
        x=tw_vals,
        orientation="h",
        marker=dict(color=COLORS["twitter"], line=dict(width=0)),
        text=[f"{v:.0f}" for v in tw_vals],
        textposition="outside",
        textfont=dict(family="Geist Mono, monospace", size=11, color=COLORS["twitter"]),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Twitter: %{x:.1f} palabras<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="YouTube",
        y=labels,
        x=yt_vals,
        orientation="h",
        marker=dict(color=COLORS["youtube"], line=dict(width=0)),
        text=[f"{v:.0f}" for v in yt_vals],
        textposition="outside",
        textfont=dict(family="Geist Mono, monospace", size=11, color=COLORS["youtube"]),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>YouTube: %{x:.1f} palabras<extra></extra>",
    ))

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        barmode="group",
        bargap=0.30,
        bargroupgap=0.08,
        barcornerradius=3,
        height=380,
        margin=dict(l=28, r=50, t=10, b=44),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=hover_bg,
            bordercolor=border2,
            font=dict(color=hover_font, family="Geist, sans-serif", size=13),
        ),
        xaxis=dict(
            title="palabras",
            showgrid=True,
            gridcolor=grid_color,
            zeroline=False,
            fixedrange=True,
            range=[0, x_max],
            tickfont=dict(family="Geist Mono, monospace", size=10, color=muted),
            title_font=dict(family="Geist, sans-serif", size=11, color=muted),
        ),
        yaxis=dict(
            title=None,
            showgrid=False,
            zeroline=False,
            automargin=True,
            fixedrange=True,
            ticklabelstandoff=14,
            tickfont=dict(family="Geist, sans-serif", size=14, color=text2),
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.14,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(family="Geist Mono, monospace", size=12, color=text2),
            itemsizing="constant",
        ),
    )
    fig.update_layout(**layout)
    return fig


def _sector_neg_pos_chart(tw: dict, yt: dict, tw_label: str, yt_label: str) -> go.Figure:
    """Horizontal grouped bars: % neg & % pos for a single sector (2 rows)."""
    tokens  = get_theme_tokens()
    bg      = tokens.get("bg", "#ffffff")
    muted   = tokens.get("muted", "#a1a1aa")
    text2   = tokens.get("text2", "#667085")
    border2 = tokens.get("border2", "rgba(148,163,184,0.35)")
    is_dark = _is_dark_theme(bg)

    hover_bg   = "rgba(255,255,255,0.98)" if not is_dark else "rgba(17,24,39,0.98)"
    hover_font = "#111827" if not is_dark else "#F9FAFB"
    grid_color = "rgba(148,163,184,0.16)" if not is_dark else "rgba(148,163,184,0.10)"

    labels   = [tw_label, yt_label]
    neg_vals = [tw["neg"], yt["neg"]]
    pos_vals = [tw["pos"], yt["pos"]]
    x_max    = max(*neg_vals, *pos_vals) * 1.28

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="% Negativo",
        y=labels,
        x=neg_vals,
        orientation="h",
        marker=dict(color=COLORS["negative"], line=dict(width=0)),
        text=[f"{v:.1f}%" for v in neg_vals],
        textposition="outside",
        textfont=dict(family="Geist Mono, monospace", size=12, color=COLORS["negative"]),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Negativo: %{x:.1f}%<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="% Positivo",
        y=labels,
        x=pos_vals,
        orientation="h",
        marker=dict(color=COLORS["positive"], line=dict(width=0)),
        text=[f"{v:.1f}%" for v in pos_vals],
        textposition="outside",
        textfont=dict(family="Geist Mono, monospace", size=12, color=COLORS["positive"]),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Positivo: %{x:.1f}%<extra></extra>",
    ))

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        barmode="group",
        bargap=0.38,
        bargroupgap=0.08,
        barcornerradius=3,
        height=240,
        margin=dict(l=28, r=80, t=10, b=44),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=hover_bg,
            bordercolor=border2,
            font=dict(color=hover_font, family="Geist, sans-serif", size=13),
        ),
        xaxis=dict(
            ticksuffix="%",
            range=[0, x_max],
            showgrid=True,
            gridcolor=grid_color,
            zeroline=False,
            fixedrange=True,
            tickfont=dict(family="Geist Mono, monospace", size=10, color=muted),
        ),
        yaxis=dict(
            title=None,
            showgrid=False,
            zeroline=False,
            automargin=True,
            fixedrange=True,
            ticklabelstandoff=18,
            tickfont=dict(family="Geist, sans-serif", size=15, color=text2),
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.20,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(family="Geist Mono, monospace", size=12, color=text2),
            itemsizing="constant",
        ),
    )
    fig.update_layout(**layout)
    return fig


# ── Page ──────────────────────────────────────────────────────────────────────

def main() -> None:
    _inject_crossplatform_css()

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="page-wrap">
            <div class="section-tag">04 · COMPARATIVA CROSS-PLATFORM</div>
            <h1 class="section-title">Twitter vs YouTube</h1>
            <p class="section-subtitle">
                ¿Influye la plataforma en cómo se percibe la IA? Comparación directa entre
                dos formatos de opinión pública digital. Mismo modelo, misma IA,
                sentimientos opuestos: Twitter dominado por la neutralidad, YouTube por la negatividad.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── KPI row ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            _kpi("Twitter", f"{_TW_GLOBAL['n']:,}",
                 "tweets · 2017–2021", "kpi-tw"),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            _kpi("YouTube", f"{_YT_GLOBAL['n']:,}",
                 "comentarios · 2020–2026", "kpi-yt"),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            _kpi("Longitud mediana", "16 vs 25",
                 "palabras · Twitter vs YouTube", "kpi-accent"),
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            _kpi("Período solapado", "2020–2021",
                 f"{_TW_OVLP['n']:,} tweets · {_YT_OVLP['n']:,} comentarios",
                 "kpi-accent"),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    # ── Global charts: profile (left) + text length (right) ──────────────────
    col_profile, col_len = st.columns(2, gap="medium")

    with col_profile:
        with st.container(border=True):
            st.markdown(
                '<p class="chart-title">Perfil de sentimiento por plataforma</p>'
                f'<p class="chart-desc">Composición 100% apilada · '
                f'Twitter n={_TW_GLOBAL["n"]:,} · YouTube n={_YT_GLOBAL["n"]:,}</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                _platform_profile_chart(),
                use_container_width=True,
                config={"displayModeBar": False},
                theme=None,
            )

    with col_len:
        with st.container(border=True):
            st.markdown(
                '<p class="chart-title">Longitud del texto por plataforma</p>'
                '<p class="chart-desc">Distribución de palabras por texto · '
                'mediana, media, P75 y P90</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                _text_length_chart(),
                use_container_width=True,
                config={"displayModeBar": False},
                theme=None,
            )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Global insight ────────────────────────────────────────────────────────
    tw_neg_mult = _YT_GLOBAL["neg"] / _TW_GLOBAL["neg"]
    st.markdown(
        f"""
        <div class="insight-box">
            <strong>Hallazgo principal:</strong> La negatividad en YouTube ({_YT_GLOBAL['neg']:.1f}%)
            es {tw_neg_mult:.1f}× mayor que en Twitter ({_TW_GLOBAL['neg']:.1f}%). Twitter está
            dominado por la neutralidad ({_TW_GLOBAL['neu']:.1f}%); YouTube invierte
            completamente ese patrón. La plataforma no es un canal neutro: es un amplificador
            selectivo del sentimiento negativo sobre IA. El P90 de longitud de YouTube (89 palabras)
            duplica el de Twitter (38), explicando parcialmente por qué el formato amplifica la opinión.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    # ── Summary comparison table ──────────────────────────────────────────────
    with st.container(border=True):
        st.markdown(
            '<p class="chart-title">Tabla resumen comparativa</p>'
            '<p class="chart-desc">Métricas clave de cada plataforma · '
            'período completo y solapado</p>',
            unsafe_allow_html=True,
        )
        st.markdown(_summary_table_html(), unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    # ── Sector & overlap tabs ─────────────────────────────────────────────────
    tab_edu, tab_emp, tab_ovlp = st.tabs(["Educación", "Empleo", "Período solapado"])

    for tab, key in [
        (tab_edu,  "education"),
        (tab_emp,  "employment"),
        (tab_ovlp, "overlap"),
    ]:
        with tab:
            meta  = _SECTOR_META[key]
            tw    = meta["tw"]
            yt    = meta["yt"]
            label = meta["label"]
            delta = yt["neg"] - tw["neg"]

            # ── KPI row ───────────────────────────────────────────────────────
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(
                    _kpi("% Neg Twitter", f"{tw['neg']:.1f}%",
                         f"n={tw['n']:,} textos", "kpi-tw"),
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    _kpi("% Neg YouTube", f"{yt['neg']:.1f}%",
                         f"n={yt['n']:,} textos", "kpi-yt"),
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    _kpi("% Pos Twitter", f"{tw['pos']:.1f}%",
                         f"vs {yt['pos']:.1f}% YouTube", "kpi-tw"),
                    unsafe_allow_html=True,
                )
            with c4:
                st.markdown(
                    _kpi("Δ Negatividad", f"+{delta:.1f}pp",
                         "YouTube más negativo que Twitter", "kpi-neg"),
                    unsafe_allow_html=True,
                )

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

            # ── Neg / Pos chart ───────────────────────────────────────────────
            with st.container(border=True):
                if key == "overlap":
                    tw_lbl = "Twitter — 2020–2021"
                    yt_lbl = "YouTube — 2020–2021"
                    desc   = (
                        f"Período 2020–2021 · Twitter n={tw['n']:,} · "
                        f"YouTube n={yt['n']:,} · mismo contexto temporal"
                    )
                else:
                    tw_lbl = f"Twitter — {label}"
                    yt_lbl = f"YouTube — {label}"
                    desc   = (
                        f"Sector {label} · Twitter n={tw['n']:,} · "
                        f"YouTube n={yt['n']:,}"
                    )
                st.markdown(
                    f'<p class="chart-title">Comparativa de sentimiento — {label}</p>'
                    f'<p class="chart-desc">{desc}</p>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(
                    _sector_neg_pos_chart(tw, yt, tw_lbl, yt_lbl),
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

    # ── Method note ───────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="method-note">
            <strong>Comparabilidad metodológica:</strong> Ambas plataformas se analizan con el
            mismo modelo (<code>cardiffnlp/twitter-xlm-roberta-base-sentiment</code>). Twitter
            incluye únicamente tweets sin URL (14% del corpus total: señal de opinión directa).
            YouTube filtra comentarios con menos de 10 palabras. Las estadísticas sectoriales
            de YouTube proceden de la asignación semántica con
            <code>sector_education=True</code> / <code>sector_employment=True</code>.
            El período solapado 2020–2021 permite comparación controlada por contexto temporal,
            aunque el volumen de YouTube en ese período es reducido (n=3,041 vs 22,639 tweets).
            Percentiles de longitud calculados sobre los corpus filtrados.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
