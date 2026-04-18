import base64
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from data_loader import load_twitter_opinion, load_youtube_sentiment
from theme import (
    COLORS,
    PLOTLY_BASE_LAYOUT,
    get_theme_tokens,
)

LOGOS_DIR = Path(__file__).resolve().parent.parent / "assets" / "logos"

_SENT_COLORS = [COLORS["negative"], COLORS["neutral"], COLORS["positive"]]
_SENT_LABELS = ["Negativo", "Neutral", "Positivo"]
_SENT_KEYS   = ["negative", "neutral", "positive"]

COLOR_TW     = "#111111"
COLOR_YT     = "#FF0000"
COLOR_ACCENT = "#F59E0B"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _img_b64(path: Path):
    if path and path.exists():
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def _logo_src(path: Path):
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
) -> str:
    logo = _logo_img(logo_path, top_offset=logo_top_offset)

    text_shift = "20px" if sub_value else "0px"

    sub_html = ""
    if sub_value:
        sub_html = (
            '<div style="'
            'font-family:monospace;font-size:14px;color:#111111;margin-top:3px;text-align:left;'
            '">' + sub_value + '</div>'
        )

    return (
        '<div style="'
        'background:var(--surface);'
        'border:1px solid var(--border);'
        'border-radius:12px;'
        'padding:12px 10px;'
        'display:flex;'
        'flex-direction:column;'
        'gap:8px;'
        'box-sizing:border-box;'
        'min-height:108px;'
        '">'

        # título centrado
        '<div style="'
        'font-family:Manrope,sans-serif;'
        'font-size:13px;'
        'font-weight:800;'
        'letter-spacing:0.14em;'
        'text-transform:uppercase;'
        'color:var(--text2);'
        'text-align:center;'
        'width:100%;'
        '">' + title + '</div>'

        # fila logo izq + contenido der
        '<div style="'
        'display:flex;'
        'flex-direction:row;'
        'align-items:center;'
        'justify-content:flex-start;'
        'gap:10px;'
        'width:100%;'
        'padding-left:10px;'
        'box-sizing:border-box;'
        '">'
        + logo +
        '<div style="'
        'display:flex;'
        'flex-direction:column;'
        'justify-content:center;'
        'align-items:flex-start;'
        'min-width:0;'
        'margin-left:' + text_shift + ';'
        '">'
        '<div style="'
        'font-family:sans-serif;'
        'font-size:' + value_size + ';'
        'font-weight:700;'
        'line-height:1.1;'
        'color:' + accent + ';'
        'white-space:nowrap;text-align:left;'
        '">' + main_value + '</div>'
        + sub_html +
        '</div>'
        '</div>'

        '</div>'
    )


def _sentiment_donut(counts: dict, center: str) -> go.Figure:
    tokens = get_theme_tokens()
    vals   = [counts.get(k, 0) for k in _SENT_KEYS]
    fig = go.Figure(go.Pie(
        labels=_SENT_LABELS,
        values=vals,
        hole=0.6,
        marker=dict(colors=_SENT_COLORS, line=dict(color="rgba(0,0,0,0)", width=0)),
        textinfo="percent",
        textposition="inside",
        textfont=dict(size=14, family="Geist Mono, monospace", color="white"),
        direction="clockwise",
        sort=False,
    ))
    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        height=320,
        margin=dict(l=8, r=8, t=8, b=8),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="top", y=-0.04, xanchor="center", x=0.5,
            font=dict(size=11, family="Geist Mono, monospace", color=tokens["text2"]),
        ),
        annotations=[dict(
            text=center, x=0.5, y=0.5, showarrow=False,
            font=dict(size=18, family="Space Grotesk, sans-serif", color=tokens["text"]),
        )],
    )
    fig.update_layout(**layout)
    return fig


# ── Page ──────────────────────────────────────────────────────────────────────

def main() -> None:

    # ── Data ──────────────────────────────────────────────────────────────────
    tw = load_twitter_opinion()
    yt = load_youtube_sentiment()

    tw_sent     = tw["sentiment_label_hf"].value_counts().to_dict()
    yt_sent     = yt["sentiment_label"].value_counts().to_dict()
    tw_total    = len(tw)
    yt_total    = len(yt)
    tw_year_min = int(tw["date"].dt.year.min())
    tw_year_max = int(tw["date"].dt.year.max())
    yt_year_max = int(yt["comment_year"].max())
    neg_yt_pct  = yt_sent.get("negative", 0) / yt_total * 100
    neu_tw_pct  = tw_sent.get("neutral",  0) / tw_total * 100

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="page-wrap">
            <div class="section-tag">01 · Visión general</div>
            <h1 class="section-title">Visión general del análisis</h1>
            <p class="section-subtitle">
                Dos plataformas, nueve años de opinión pública sobre inteligencia artificial.
                186&nbsp;378 textos analizados con el mismo modelo de NLP para garantizar comparabilidad.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── KPI row ───────────────────────────────────────────────────────────────
    _, c1, c2, c3, c4, _ = st.columns([0.22, 1, 1, 1, 1, 0.22])

    with c1:
        st.markdown(
            '<div style="margin-bottom:-4px;">' +
            _kpi_card(
                title=str(tw_year_min) + " \u2013 " + str(tw_year_max),
                logo_path=LOGOS_DIR / "twitter_logo.png",
                main_value=f"{tw_total:,}",
                sub_value="tweets sin URL",
                accent=COLOR_TW,
                value_size="30px",
                logo_top_offset=-12,
            ) + '</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div style="margin-bottom:-4px;">' +
            _kpi_card(
                title="2020 \u2013 " + str(yt_year_max),
                logo_path=LOGOS_DIR / "youtube_logo.png",
                main_value=f"{yt_total:,}",
                sub_value="comentarios",
                accent=COLOR_YT,
                value_size="30px",
                logo_top_offset=-12,
            ) + '</div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div style="margin-bottom:-4px;">' +
            _kpi_card(
                title="Modelo NLP",
                logo_path=LOGOS_DIR / "cardiffnlp_logo.png",
                main_value="XLM-RoBERTa",
                sub_value="",
                accent=COLOR_ACCENT,
                value_size="22px",
                logo_top_offset=-2,
            ) + '</div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            '<div style="margin-bottom:-4px;">' +
            _kpi_card(
                title="Periodo total",
                logo_path=LOGOS_DIR / "timeline.png",
                main_value=str(tw_year_min) + " - " + str(yt_year_max),
                sub_value="",
                accent=COLOR_ACCENT,
                value_size="26px",
                logo_top_offset=-2,
            ) + '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:0.45rem'></div>", unsafe_allow_html=True)

    # ── Donut charts ──────────────────────────────────────────────────────────
    col_tw, col_yt = st.columns(2)

    with col_tw:
        with st.container(border=True):
            st.markdown(
                '<p class="chart-title">Sentimiento global \u2014 Twitter</p>'
                '<p class="chart-desc">Solo tweets sin URL \u00b7 se\u00f1al de opini\u00f3n directa'
                ' (n=' + f"{tw_total:,}" + ')</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                _sentiment_donut(tw_sent, "Twitter"),
                use_container_width=True,
                config={"displayModeBar": False},
                theme=None,
            )
    with col_yt:
        with st.container(border=True):
            st.markdown(
                '<p class="chart-title">Sentimiento global \u2014 YouTube</p>'
                '<p class="chart-desc">Comentarios con \u226510 palabras'
                ' (n=' + f"{yt_total:,}" + ')</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                _sentiment_donut(yt_sent, "YouTube"),
                use_container_width=True,
                config={"displayModeBar": False},
                theme=None,
            )

    # ── Insight ───────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="insight-box">'
        '<strong>Hallazgo central:</strong> Twitter (pre-ChatGPT) muestra un sentimiento '
        'dominado por la neutralidad (' + f"{neu_tw_pct:.1f}" + '%), mientras YouTube (que cubre la '
        'era post-ChatGPT) invierte la proporci\u00f3n con un ' + f"{neg_yt_pct:.1f}" + '% de negatividad. '
        'El contraste revela un cambio de paradigma en la percepci\u00f3n p\u00fablica.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    # ── Hypothesis cards ──────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-tag" style="margin-bottom:14px">Hip\u00f3tesis de trabajo</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="hyp-grid">
            <div class="hyp-card">
                <h4>Evoluci&#243;n hacia la negatividad</h4>
                <p>La percepci&#243;n pasa de neutral-curiosa a dominantemente negativa. ChatGPT
                (nov 2022) act&#250;a como catalizador visible, no como causa &#250;nica.</p>
            </div>
            <div class="hyp-card">
                <h4>Diferenciaci&#243;n por sectores</h4>
                <p>Empleo concentra 60.9% de negatividad. Educaci&#243;n es genuinamente
                ambivalente: la tutor&#237;a IA genera esperanza, pero el sistema institucional
                genera miedo.</p>
            </div>
            <div class="hyp-card">
                <h4>Diferenciaci&#243;n por plataforma</h4>
                <p>Las plataformas difieren, pero no como se esperaba. YouTube no es m&#225;s
                equilibrado: la mayor extensi&#243;n amplifica la negatividad, no la mitiga.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()