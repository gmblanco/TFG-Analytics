import base64
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from theme import COLORS, PLOTLY_BASE_LAYOUT, get_theme_tokens

BASE_DIR  = Path(__file__).resolve().parent.parent
LOGOS_DIR = BASE_DIR / "assets" / "logos"

_TW_GLOBAL = {"neg": 15.5, "neu": 56.7, "pos": 27.8, "n": 123_389}
_YT_GLOBAL = {"neg": 52.9, "neu": 26.0, "pos": 21.1, "n":  62_989}

_TW_EDU = {"neg": 12.9, "neu": 54.6, "pos": 32.5, "n":  6_632}
_YT_EDU = {"neg": 47.7, "neu": 28.5, "pos": 23.8, "n": 10_677}

_TW_EMP = {"neg": 17.9, "neu": 51.9, "pos": 30.2, "n": 15_499}
_YT_EMP = {"neg": 60.9, "neu": 22.6, "pos": 16.5, "n": 10_439}

_TW_LEN = {"median": 16.0, "mean": 19.2, "p75": 26.0, "p90": 38.0}
_YT_LEN = {"median": 25.0, "mean": 44.1, "p75": 46.0, "p90": 89.0}

_SECTOR_META = {
    "education": {
        "tw": _TW_EDU, "yt": _YT_EDU, "label": "Educación",
        "insight": (
            "<strong>Educación:</strong> "
            "La comparativa entre plataformas muestra diferencias claras en este sector. "
            "En Twitter, la educación presenta una distribución relativamente más positiva "
            "(32.5%) y menos negativa (12.9%). En YouTube, en cambio, la negatividad aumenta "
            "hasta el 47.7%, lo que refleja una percepción mucho más crítica. "
            "En conjunto, estos resultados sugieren que en YouTube ganan más peso preocupaciones "
            "relacionadas con el impacto institucional de la IA en el ámbito educativo."
        ),
    },
    "employment": {
        "tw": _TW_EMP, "yt": _YT_EMP, "label": "Empleo",
        "insight": (
            "<strong>Empleo:</strong> "
            "Es el sector que concentra mayor negatividad en ambas plataformas. "
            "En Twitter, el porcentaje de comentarios negativos es del 17.9%, mientras que en "
            "YouTube asciende al 60.9%. "
            "La diferencia entre plataformas muestra que el ámbito laboral es donde la percepción "
            "de la IA resulta más crítica, especialmente en YouTube, donde predominan con más fuerza "
            "las preocupaciones ligadas al desplazamiento laboral."
        ),
    },
}


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
        div[data-testid="stBorderContainer"] > div { background: transparent !important; }
        div[data-testid="stBorderContainer"] div[data-testid="stPlotlyChart"],
        div[data-testid="stBorderContainer"] div[data-testid="stPlotlyChart"] > div {
            background: transparent !important;
        }

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
        .cmp-table tbody tr { border-bottom: 1px solid var(--border, #27272a); }
        .cmp-table tbody tr:last-child { border-bottom: none; }
        .cmp-table tbody tr:hover { background: rgba(255,255,255,0.025); }
        .cmp-table tbody td {
            padding: 0.66rem 1rem;
            color: var(--text2, #d4d4d8);
            font-size: 0.93rem;
        }
        .cmp-table .metric-cell { color: var(--text, #fafafa); font-weight: 500; }
        .val-tw         { color: var(--tw,  #60a5fa); font-weight: 600; }
        .val-yt         { color: var(--yt,  #f87171); font-weight: 600; }
        .val-yt-hi      { color: var(--yt,  #f87171); font-weight: 700; }
        .val-tw-hi      { color: var(--tw,  #60a5fa); font-weight: 700; }
        .val-diff-neg   { color: var(--yt,  #f87171); font-weight: 700; }
        .val-diff-muted { color: var(--muted, #a1a1aa); }
        .val-ratio      { color: var(--text2, #d4d4d8); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _is_dark_theme(bg_value: str) -> bool:
    dark_candidates = {
        "#000", "#000000", "#09090b", "#0b0f19", "#0f1117", "#111827", "#0e1117",
    }
    return str(bg_value).lower() in dark_candidates or "rgb(0" in str(bg_value).lower()


def _img_b64(path: Path) -> str | None:
    if path and path.exists():
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def _logo_src(path: Path) -> str | None:
    b64 = _img_b64(path)
    if not b64:
        return None
    ext  = path.suffix.lstrip(".").lower()
    mime = "image/svg+xml" if ext == "svg" else "image/" + ext
    return "data:" + mime + ";base64," + b64


def _logo_img(path: Path, size: int = 38, top_offset: int = -2) -> str:
    src = _logo_src(path)
    sz  = str(size) + "px"
    if src:
        return (
            '<img src="' + src + '" style="'
            'width:' + sz + ';height:' + sz + ';'
            'object-fit:contain;display:block;flex-shrink:0;'
            'position:relative;top:' + str(top_offset) + 'px;" />'
        )
    return '<div style="width:' + sz + ';height:' + sz + ';flex-shrink:0;"></div>'


def _kpi_card(
    title: str,
    logo_path: Path,
    main_value: str,
    sub_value: str,
    accent: str,
    value_size: str = "28px",
    logo_top_offset: int = -2,
    logo_size: int = 38,
    text_shift: str | None = None,
) -> str:
    logo       = _logo_img(logo_path, size=logo_size, top_offset=logo_top_offset)
    text_shift = text_shift if text_shift is not None else ("20px" if sub_value else "0px")
    sub_html   = (
        '<div style="font-family:monospace;font-size:14px;color:#111111;'
        'margin-top:3px;text-align:left;">' + sub_value + '</div>'
    ) if sub_value else ""

    return (
        '<div style="background:var(--surface);border:1px solid var(--border);'
        'border-radius:12px;padding:12px 10px;display:flex;flex-direction:column;'
        'gap:8px;box-sizing:border-box;">'

        '<div style="font-family:Manrope,sans-serif;font-size:13px;font-weight:800;'
        'letter-spacing:0.14em;text-transform:uppercase;color:var(--text2);'
        'text-align:center;width:100%;">' + title + '</div>'

        '<div style="display:flex;flex-direction:row;align-items:center;'
        'justify-content:flex-start;gap:10px;width:100%;'
        'padding-left:10px;box-sizing:border-box;">'
        + logo +
        '<div style="display:flex;flex-direction:column;justify-content:center;'
        'align-items:flex-start;min-width:0;margin-left:' + text_shift + ';">'
        '<div style="font-family:sans-serif;font-size:' + value_size + ';font-weight:700;'
        'line-height:1.1;color:' + accent + ';white-space:nowrap;text-align:left;">'
        + main_value + '</div>'
        + sub_html +
        '</div></div></div>'
    )


def _chart_theme_vars() -> dict:
    tokens  = get_theme_tokens()
    is_dark = _is_dark_theme(tokens.get("bg", "#ffffff"))
    return {
        "muted":      tokens.get("muted", "#a1a1aa"),
        "text2":      tokens.get("text2", "#667085"),
        "border2":    tokens.get("border2", "rgba(148,163,184,0.35)"),
        "hover_bg":   "rgba(255,255,255,0.98)" if not is_dark else "rgba(17,24,39,0.98)",
        "hover_font": "#111827" if not is_dark else "#F9FAFB",
        "grid_color": "rgba(148,163,184,0.16)" if not is_dark else "rgba(148,163,184,0.10)",
    }


def _summary_table_html() -> str:
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
        "<table class='cmp-table'><thead><tr>"
        "<th>MÉTRICA</th><th>TWITTER (2017–2021)</th>"
        "<th>YOUTUBE (2020–2026)</th><th>DIFERENCIA</th>"
        f"</tr></thead><tbody>{rows_html}</tbody></table>"
    )


def _platform_profile_chart() -> go.Figure:
    t = _chart_theme_vars()
    platforms = ["Twitter", "YouTube"]

    fig = go.Figure()
    for name, vals, color in [
        ("Negativo", [_TW_GLOBAL["neg"], _YT_GLOBAL["neg"]], COLORS["negative"]),
        ("Neutral",  [_TW_GLOBAL["neu"], _YT_GLOBAL["neu"]], COLORS["neutral"]),
        ("Positivo", [_TW_GLOBAL["pos"], _YT_GLOBAL["pos"]], COLORS["positive"]),
    ]:
        fig.add_trace(go.Bar(
            name=name, x=platforms, y=vals,
            marker=dict(color=color, line=dict(width=0)),
            text=[f"{v:.1f}%" for v in vals],
            textposition="inside", insidetextanchor="middle",
            textfont=dict(family="Geist Mono, monospace", size=13, color="white"),
            hovertemplate=f"<b>%{{x}}</b><br>{name}: %{{y:.1f}}%<extra></extra>",
        ))

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        barmode="stack", bargap=0.45, barcornerradius=2,
        height=380, margin=dict(l=20, r=20, t=20, b=44),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=t["hover_bg"], bordercolor=t["border2"],
            font=dict(color=t["hover_font"], family="Geist, sans-serif", size=13),
        ),
        xaxis=dict(
            showgrid=False, zeroline=False, fixedrange=True,
            tickfont=dict(family="Geist, sans-serif", size=15, color=t["text2"]),
        ),
        yaxis=dict(
            title=None, showgrid=False, zeroline=False, fixedrange=True,
            range=[0, 101], ticksuffix="%",
            tickfont=dict(family="Geist Mono, monospace", size=10, color=t["muted"]),
        ),
        legend=dict(
            orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(family="Geist Mono, monospace", size=12, color=t["text2"]),
            itemsizing="constant",
        ),
    )
    fig.update_layout(**layout)
    return fig


def _text_length_chart() -> go.Figure:
    t = _chart_theme_vars()
    labels  = ["Mediana", "Media", "P75", "P90"]
    tw_vals = [_TW_LEN["median"], _TW_LEN["mean"], _TW_LEN["p75"], _TW_LEN["p90"]]
    yt_vals = [_YT_LEN["median"], _YT_LEN["mean"], _YT_LEN["p75"], _YT_LEN["p90"]]

    fig = go.Figure()
    for name, vals, color in [
        ("Twitter", tw_vals, COLORS["twitter"]),
        ("YouTube", yt_vals, COLORS["youtube"]),
    ]:
        fig.add_trace(go.Bar(
            name=name, y=labels, x=vals, orientation="h",
            marker=dict(color=color, line=dict(width=0)),
            text=[f"{v:.0f}" for v in vals],
            textposition="outside",
            textfont=dict(family="Geist Mono, monospace", size=11, color=color),
            cliponaxis=False,
            hovertemplate=f"<b>%{{y}}</b><br>{name}: %{{x:.1f}} palabras<extra></extra>",
        ))

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        barmode="group", bargap=0.30, bargroupgap=0.08, barcornerradius=3,
        height=380, margin=dict(l=28, r=50, t=10, b=44),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=t["hover_bg"], bordercolor=t["border2"],
            font=dict(color=t["hover_font"], family="Geist, sans-serif", size=13),
        ),
        xaxis=dict(
            title="palabras", showgrid=True, gridcolor=t["grid_color"],
            zeroline=False, fixedrange=True,
            range=[0, max(*tw_vals, *yt_vals) * 1.22],
            tickfont=dict(family="Geist Mono, monospace", size=10, color=t["muted"]),
            title_font=dict(family="Geist, sans-serif", size=11, color=t["muted"]),
        ),
        yaxis=dict(
            title=None, showgrid=False, zeroline=False,
            automargin=True, fixedrange=True, ticklabelstandoff=14,
            tickfont=dict(family="Geist, sans-serif", size=14, color=t["text2"]),
        ),
        legend=dict(
            orientation="h", yanchor="top", y=-0.14, xanchor="center", x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(family="Geist Mono, monospace", size=12, color=t["text2"]),
            itemsizing="constant",
        ),
    )
    fig.update_layout(**layout)
    return fig


def _sector_neg_pos_chart(tw: dict, yt: dict, tw_label: str, yt_label: str) -> go.Figure:
    t = _chart_theme_vars()
    labels   = [tw_label, yt_label]
    neg_vals = [tw["neg"], yt["neg"]]
    pos_vals = [tw["pos"], yt["pos"]]

    fig = go.Figure()
    for name, vals, color in [
        ("% Negativo", neg_vals, COLORS["negative"]),
        ("% Positivo", pos_vals, COLORS["positive"]),
    ]:
        fig.add_trace(go.Bar(
            name=name, y=labels, x=vals, orientation="h",
            marker=dict(color=color, line=dict(width=0)),
            text=[f"{v:.1f}%" for v in vals],
            textposition="outside",
            textfont=dict(family="Geist Mono, monospace", size=12, color=color),
            cliponaxis=False,
            hovertemplate=f"<b>%{{y}}</b><br>{name}: %{{x:.1f}}%<extra></extra>",
        ))

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        barmode="group", bargap=0.38, bargroupgap=0.08, barcornerradius=3,
        height=240, margin=dict(l=28, r=80, t=10, b=44),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=t["hover_bg"], bordercolor=t["border2"],
            font=dict(color=t["hover_font"], family="Geist, sans-serif", size=13),
        ),
        xaxis=dict(
            ticksuffix="%", range=[0, max(*neg_vals, *pos_vals) * 1.28],
            showgrid=True, gridcolor=t["grid_color"], zeroline=False, fixedrange=True,
            tickfont=dict(family="Geist Mono, monospace", size=10, color=t["muted"]),
        ),
        yaxis=dict(
            title=None, showgrid=False, zeroline=False,
            automargin=True, fixedrange=True, ticklabelstandoff=18,
            tickfont=dict(family="Geist, sans-serif", size=15, color=t["text2"]),
        ),
        legend=dict(
            orientation="h", yanchor="top", y=-0.20, xanchor="center", x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(family="Geist Mono, monospace", size=12, color=t["text2"]),
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
            <div class="section-tag">04 · COMPARATIVA CROSS-PLATFORM</div>
            <h1 class="section-title">Comparativa de sentimiento por plataforma</h1>
            <p class="section-subtitle">
                Se analizan las diferencias entre Twitter y YouTube en la distribución del sentimiento, los sectores estudiados y la longitud de los textos.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, c1, c2, c3, _ = st.columns([0.7, 1, 1, 1, 0.7])

    with c1:
        st.markdown(
            '<div style="margin-bottom:-4px;">' +
            _kpi_card(
                title="2017 – 2021",
                logo_path=LOGOS_DIR / "twitter_logo.png",
                main_value=f"{_TW_GLOBAL['n']:,}",
                sub_value="tweets",
                accent="#111111",
                value_size="30px",
                logo_top_offset=-18,
            ) + '</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div style="margin-bottom:-4px;">' +
            _kpi_card(
                title="2020 – 2026",
                logo_path=LOGOS_DIR / "youtube_logo.png",
                main_value=f"{_YT_GLOBAL['n']:,}",
                sub_value="comentarios",
                accent="#FF0000",
                value_size="30px",
                logo_top_offset=-18,
            ) + '</div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div style="margin-bottom:-4px;">' +
            _kpi_card(
                title="Longitud mediana",
                logo_path=LOGOS_DIR / "mediana.png",
                main_value="16 vs 25",
                sub_value="Twitter vs YouTube",
                accent="#F59E0B",
                value_size="26px",
                logo_top_offset=-10,
                logo_size=52,
                text_shift="0px",
            ) + '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    col_profile, col_len = st.columns(2, gap="medium")

    with col_profile:
        with st.container(border=True):
            st.markdown(
                '<p class="chart-title">Perfil de sentimiento por plataforma</p>'
                f'<p class="chart-desc">Twitter n={_TW_GLOBAL["n"]:,} | YouTube n={_YT_GLOBAL["n"]:,}</p>',
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
                '<p class="chart-desc">Distribución de palabras por texto: '
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

    tw_neg_mult = _YT_GLOBAL["neg"] / _TW_GLOBAL["neg"]
    st.markdown(
        f"""
        <div class="insight-box">
            <strong>Resultado principal:</strong> la comparativa entre plataformas muestra diferencias claras en la percepción de la IA.
            Twitter presenta una distribución dominada por la neutralidad (56,7%), mientras que en YouTube predomina la negatividad (52,9%).
            A ello se suma que los comentarios de YouTube son, en general, más extensos que los textos de Twitter, lo que puede favorecer opiniones
            más desarrolladas y críticas.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            '<p class="chart-title">Tabla resumen comparativa</p>'
            '<p class="chart-desc">Métricas clave de cada plataforma · período completo</p>',
            unsafe_allow_html=True,
        )
        st.markdown(_summary_table_html(), unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    tab_edu, tab_emp = st.tabs(["Educación", "Empleo"])

    for tab, key in [
        (tab_edu, "education"),
        (tab_emp, "employment"),
    ]:
        with tab:
            meta  = _SECTOR_META[key]
            tw    = meta["tw"]
            yt    = meta["yt"]
            label = meta["label"]

            with st.container(border=True):
                st.markdown(
                    f'<p class="chart-title">Comparativa de sentimiento - {label}</p>'
                    f'<p class="chart-desc">Twitter n={tw["n"]:,} | YouTube n={yt["n"]:,}</p>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(
                    _sector_neg_pos_chart(tw, yt, f"Twitter - {label}", f"YouTube - {label}"),
                    use_container_width=True,
                    config={"displayModeBar": False},
                    theme=None,
                )

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            st.markdown(f'<div class="insight-box">{meta["insight"]}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()