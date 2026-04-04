from __future__ import annotations

import html
import re
from pathlib import Path

import pandas as pd
import streamlit as st

from theme import get_theme_tokens


BASE_DIR = Path(__file__).resolve().parent.parent
# Buscar el CSV en múltiples ubicaciones posibles
_CANDIDATE_PATHS = [
    BASE_DIR / "data" / "processed" / "explorer_comments.csv",            # app/data/processed/
    BASE_DIR.parent / "data" / "processed" / "explorer_comments.csv",     # TFG-Analytics/data/processed/
]
CSV_PATH = next((p for p in _CANDIDATE_PATHS if p.exists()), _CANDIDATE_PATHS[-1])
MAX_EXPLORER_COMMENTS = 100


# =========================================================
# LOAD DATA — simple CSV read, instantáneo
# =========================================================

@st.cache_data(show_spinner=False, ttl=60)
def load_explorer_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        st.error(
            f"No se encontró el archivo de comentarios curados.\n\n"
            f"Ejecuta primero: `python generate_explorer_csv.py`\n\n"
            f"Ruta esperada: `{CSV_PATH}`"
        )
        return pd.DataFrame()

    df = pd.read_csv(CSV_PATH, encoding="utf-8")

    # Asegurar columnas esperadas
    for col in ["platform", "sentiment", "sector", "message"]:
        if col not in df.columns:
            st.error(f"Falta la columna '{col}' en el CSV.")
            return pd.DataFrame()

    # Normalizar vacíos
    df["sector"] = df["sector"].fillna("").astype(str).str.strip()
    df["message"] = df["message"].fillna("").astype(str).str.strip()
    df["sentiment"] = df["sentiment"].fillna("Neutral").astype(str).str.strip()
    df["platform"] = df["platform"].fillna("").astype(str).str.strip()

    # Descartar filas sin mensaje
    df = df[df["message"] != ""].copy()

    return df.reset_index(drop=True)


# =========================================================
# FILTERS
# =========================================================

def apply_user_filters(df: pd.DataFrame) -> pd.DataFrame:
    c1, c2, c3, c4 = st.columns([1.7, 1.0, 1.0, 1.0])

    keyword = c1.text_input(
        "Buscar por keyword",
        placeholder="Ej. job, teacher, ChatGPT, replace...",
    )

    sources = ["Todos"] + sorted(df["platform"].dropna().unique().tolist())
    source_sel = c2.selectbox("Fuente", sources, index=0)

    sentiments = ["Todos"] + sorted(df["sentiment"].dropna().unique().tolist())
    sentiment_sel = c3.selectbox("Sentimiento", sentiments, index=0)

    sectors_raw = [x for x in df["sector"].unique().tolist() if x.strip() != ""]
    sectors = ["Todos"] + sorted(sectors_raw)
    sector_sel = c4.selectbox("Sector", sectors, index=0)

    out = df.copy()

    if keyword:
        pat = re.escape(keyword.strip())
        out = out[out["message"].str.contains(pat, case=False, na=False)].copy()

    if source_sel != "Todos":
        out = out[out["platform"] == source_sel].copy()

    if sentiment_sel != "Todos":
        out = out[out["sentiment"] == sentiment_sel].copy()

    if sector_sel != "Todos":
        out = out[out["sector"] == sector_sel].copy()

    return out


# =========================================================
# UI — CSS
# =========================================================

def render_css() -> None:
    tokens = get_theme_tokens()
    card = tokens.get("surface", tokens.get("card", "#111827"))
    text = tokens.get("text", "#f8fafc")
    text2 = tokens.get("text2", tokens.get("muted", "#94a3b8"))
    border = tokens.get("border", "rgba(148,163,184,0.18)")

    st.markdown(
        f"""
        <style>
        .kpi-card {{
            background: {card};
            border: 1px solid {border};
            border-radius: 18px;
            padding: 18px 18px 16px 18px;
            min-height: 120px;
            margin-bottom: 14px;
        }}

        .kpi-label {{
            color: {text2};
            font-size: 0.78rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}

        .kpi-value {{
            color: {text};
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.1;
            margin-bottom: 6px;
        }}

        .kpi-sub {{
            color: {text2};
            font-size: 0.95rem;
        }}

        .exp-card {{
            background: {card};
            border: 1px solid {border};
            border-radius: 18px;
            padding: 18px 18px 16px 18px;
            margin-bottom: 14px;
        }}

        .badge-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 12px;
        }}

        .badge-left {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            align-items: center;
        }}

        .badge {{
            display: inline-block;
            padding: 5px 11px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 600;
            border: 1px solid rgba(255,255,255,0.12);
        }}

        .badge-twitter {{
            background: rgba(59,130,246,0.12);
            color: #60a5fa;
            border-color: rgba(59,130,246,0.28);
        }}

        .badge-youtube {{
            background: rgba(239,68,68,0.12);
            color: #f87171;
            border-color: rgba(239,68,68,0.28);
        }}

        .badge-positive {{
            background: rgba(34,197,94,0.12);
            color: #4ade80;
            border-color: rgba(34,197,94,0.28);
        }}

        .badge-neutral {{
            background: rgba(148,163,184,0.14);
            color: #cbd5e1;
            border-color: rgba(148,163,184,0.24);
        }}

        .badge-negative {{
            background: rgba(239,68,68,0.12);
            color: #f87171;
            border-color: rgba(239,68,68,0.28);
        }}

        .badge-sector {{
            background: rgba(245,158,11,0.12);
            color: #fbbf24;
            border-color: rgba(245,158,11,0.26);
        }}

        .comment-text {{
            color: {text};
            font-size: 1.02rem;
            line-height: 1.75;
            margin-top: 6px;
            word-break: break-word;
        }}

        .section-sub {{
            color: {text2};
            margin-bottom: 12px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# UI — KPIs
# =========================================================

def render_kpis(df: pd.DataFrame) -> None:
    total = len(df)

    if total == 0:
        neg_pct = neu_pct = pos_pct = 0.0
        tw_count = yt_count = 0
    else:
        neg_pct = 100 * (df["sentiment"] == "Negativo").mean()
        neu_pct = 100 * (df["sentiment"] == "Neutral").mean()
        pos_pct = 100 * (df["sentiment"] == "Positivo").mean()
        tw_count = int((df["platform"] == "Twitter").sum())
        yt_count = int((df["platform"] == "YouTube").sum())

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Comentarios</div>
                <div class="kpi-value">{total:,}</div>
                <div class="kpi-sub">Twitter {tw_count:,} · YouTube {yt_count:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Negativos</div>
                <div class="kpi-value">{neg_pct:.1f}%</div>
                <div class="kpi-sub">{int((df["sentiment"] == "Negativo").sum()) if total else 0:,} comentarios</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Neutrales</div>
                <div class="kpi-value">{neu_pct:.1f}%</div>
                <div class="kpi-sub">{int((df["sentiment"] == "Neutral").sum()) if total else 0:,} comentarios</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Positivos</div>
                <div class="kpi-value">{pos_pct:.1f}%</div>
                <div class="kpi-sub">{int((df["sentiment"] == "Positivo").sum()) if total else 0:,} comentarios</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# UI — Comment cards
# =========================================================

def _truncate(text: str, n: int = 420) -> str:
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def render_comment_card(row: pd.Series) -> None:
    platform = str(row.get("platform", ""))
    sentiment = str(row.get("sentiment", "Neutral"))
    sector = str(row.get("sector", "")).strip()
    message = str(row.get("message", ""))

    # Badge de plataforma
    src_cls = "badge-twitter" if platform == "Twitter" else "badge-youtube"
    source_badge = f"<span class='badge {src_cls}'>{html.escape(platform)}</span>"

    # Badge de sentimiento
    sent_map = {
        "Positivo": "badge-positive",
        "Neutral": "badge-neutral",
        "Negativo": "badge-negative",
    }
    sent_cls = sent_map.get(sentiment, "badge-neutral")
    sent_badge = f"<span class='badge {sent_cls}'>{html.escape(sentiment)}</span>"

    # Badge de sector (opcional)
    sector_badge = ""
    if sector:
        sector_badge = f"<span class='badge badge-sector'>{html.escape(sector)}</span>"

    badges = f"{source_badge}\n{sent_badge}"
    if sector_badge:
        badges += f"\n{sector_badge}"

    # Texto — html.escape garantiza que no se renderice ningún HTML
    text = html.escape(_truncate(message, 420))

    st.markdown(
        f"""
        <div class="exp-card">
            <div class="badge-row">
                <div class="badge-left">
                    {badges}
                </div>
            </div>
            <div class="comment-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# PAGE
# =========================================================

def main() -> None:
    render_css()
    df = load_explorer_data()

    if df.empty:
        st.warning("No se han podido cargar datos para el Explorer.")
        return

    st.title("Explorer")
    st.markdown("---")

    filtered = apply_user_filters(df)
    render_kpis(filtered)

    st.markdown("### Comentarios")
    st.caption(f"{len(filtered):,} resultados")

    if filtered.empty:
        st.info("No hay comentarios disponibles con los filtros actuales.")
        return

    for _, row in filtered.head(MAX_EXPLORER_COMMENTS).iterrows():
        render_comment_card(row)


if __name__ == "__main__":
    main()