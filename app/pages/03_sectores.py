# ============================================================
# pages/03_sectores.py — Análisis por Sectores
# H2: Diferencias sectoriales en la percepción de la IA
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from theme import setup_theme

# ── Rutas ─────────────────────────────────────────────────────
ROOT     = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data" / "processed"
YT_PATH  = DATA_DIR / "youtube_sentiment_v2.parquet"

# ── Tema ──────────────────────────────────────────────────────
T = setup_theme()

ORDER = ["positive", "neutral", "negative"]
LABEL_ES = {
    "positive": "Positivo",
    "neutral": "Neutral",
    "negative": "Negativo",
}
SENTIMENT_COLORS = {
    "positive": T["positive"],
    "neutral":  T["neutral"],
    "negative": T["negative"],
}

# ── Carga ─────────────────────────────────────────────────────
@st.cache_data(show_spinner="Cargando datos…")
def load_yt():
    df = pd.read_parquet(YT_PATH)
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df = df[df["date"].notna()].copy()
    df["comment_month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["year"] = df["date"].dt.year
    df["fase"] = np.where(df["year"] <= 2022, "Pre-ChatGPT", "Post-ChatGPT")
    return df

try:
    yt = load_yt()
except FileNotFoundError as e:
    st.error(f"Parquet no encontrado.\n\n`{e}`")
    st.stop()

# ── Subsets ───────────────────────────────────────────────────
edu = yt[yt["sector_education"] == True].copy()
emp = yt[yt["sector_employment"] == True].copy()

# ── Helpers ───────────────────────────────────────────────────
def set_mpl_style():
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({
        "figure.facecolor": T["bg"] if "bg" in T else "#0b1020",
        "axes.facecolor": T["surface"],
        "axes.edgecolor": T["border"],
        "axes.labelcolor": T["text"],
        "xtick.color": T["text"],
        "ytick.color": T["text"],
        "text.color": T["text"],
        "grid.color": T["border"],
        "grid.alpha": 0.35,
        "font.size": 11,
        "axes.titleweight": "bold",
    })

def sentiment_pct(df):
    return (
        df["sentiment_label"]
        .value_counts(normalize=True)
        .reindex(ORDER, fill_value=0)
        * 100
    )

def monthly_sentiment(df_sector, min_comments=50, smooth_window=3):
    monthly = (
        df_sector.groupby(["comment_month", "sentiment_label"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["positive", "neutral", "negative"], fill_value=0)
    )
    total = monthly.sum(axis=1)
    monthly = monthly[total >= min_comments].copy()
    monthly_pct = monthly.div(monthly.sum(axis=1), axis=0) * 100
    monthly_pct.index = pd.to_datetime(monthly_pct.index)
    monthly_smooth = monthly_pct.rolling(
        window=smooth_window, center=True, min_periods=2
    ).mean()
    return monthly_smooth

MILESTONES = [
    ("2021-01-01", "DALL·E", "ene 2021"),
    ("2022-11-01", "ChatGPT", "nov 2022"),
    ("2023-03-01", "GPT-4", "mar 2023"),
    ("2023-12-01", "Gemini", "dic 2023"),
    ("2024-06-01", "EU AI Act", "jun 2024"),
]

# ── Cabecera ──────────────────────────────────────────────────
st.markdown(
    f'<p style="font-family:\'DM Mono\',monospace;font-size:12px;'
    f'letter-spacing:0.15em;color:{T["accent"]};text-transform:uppercase;'
    f'margin-bottom:6px">H2 · Análisis sectorial</p>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<h1 style="font-size:clamp(24px,3vw,34px);font-weight:900;'
    f'color:{T["text"]};margin-bottom:8px;line-height:1.15">'
    f'Diferencias sectoriales en la percepción de la IA</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<p style="color:{T["muted"]};font-size:16px;margin-bottom:24px;line-height:1.7">'
    f'La conversación sobre IA no evoluciona igual en todos los ámbitos. '
    f'En empleo domina una lectura más negativa y persistente; en educación el discurso '
    f'es más equilibrado al inicio, pero se desplaza progresivamente hacia posiciones más críticas.</p>',
    unsafe_allow_html=True,
)
st.divider()

# ════════════════════════════════════════════════════════════
#  BLOQUE 1 — Distribución agregada por sector
# ════════════════════════════════════════════════════════════
st.markdown(
    f'<p style="font-family:\'Playfair Display\',serif;font-size:20px;'
    f'font-weight:700;color:{T["text"]};margin-bottom:6px">'
    f'Distribución agregada del sentimiento por sector</p>'
    f'<p style="color:{T["muted"]};font-size:14px;line-height:1.6;margin-bottom:16px">'
    f'Cada sector se compara con la distribución global del corpus mediante líneas de referencia.</p>',
    unsafe_allow_html=True,
)

set_mpl_style()

global_pct = sentiment_pct(yt)
sectores = {
    "Educación": edu,
    "Empleo": emp,
}

fig1, axes = plt.subplots(1, 2, figsize=(14, 5.8))
fig1.suptitle("Distribución de sentimiento por sector — YouTube", fontsize=15, fontweight="bold", y=1.02)

for ax, (nombre, subset) in zip(axes, sectores.items()):
    pct = sentiment_pct(subset)

    bars = ax.bar(
        ORDER,
        pct.values,
        color=[SENTIMENT_COLORS[s] for s in ORDER],
        edgecolor="white",
        linewidth=0.8
    )

    for s in ORDER:
        ax.axhline(
            global_pct[s],
            color=SENTIMENT_COLORS[s],
            linewidth=1.0,
            linestyle="--",
            alpha=0.35
        )

    for i, v in enumerate(pct.values):
        ax.text(i, v + 0.9, f"{v:.1f}%", ha="center", fontsize=10, fontweight="bold")

    ax.set_title(f"{nombre}  (n={len(subset):,})", fontsize=13)
    ax.set_ylabel("% de comentarios")
    ax.set_ylim(0, 80)
    ax.set_xticks(range(len(ORDER)))
    ax.set_xticklabels([LABEL_ES[s].lower() for s in ORDER], fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)

    ax.text(
        0.98, 0.97, "-- media global",
        transform=ax.transAxes,
        fontsize=8,
        color=T["muted"],
        ha="right",
        va="top"
    )

plt.tight_layout()
st.pyplot(fig1, use_container_width=True)

# ════════════════════════════════════════════════════════════
#  BLOQUE 2 — Evolución temporal por sector
# ════════════════════════════════════════════════════════════
st.markdown(
    f'<p style="font-family:\'Playfair Display\',serif;font-size:20px;'
    f'font-weight:700;color:{T["text"]};margin:18px 0 6px 0">'
    f'Evolución temporal del sentimiento en educación y empleo</p>'
    f'<p style="color:{T["muted"]};font-size:14px;line-height:1.6;margin-bottom:16px">'
    f'Series mensuales suavizadas con media móvil de 3 meses. '
    f'Se excluyen meses con menos de 50 comentarios para reducir ruido.</p>',
    unsafe_allow_html=True,
)

edu_m = monthly_sentiment(edu, min_comments=50, smooth_window=3)
emp_m = monthly_sentiment(emp, min_comments=50, smooth_window=3)

fig2, axes = plt.subplots(2, 1, figsize=(14, 8.5), sharex=True, sharey=True)

for ax, (nombre, dfm) in zip(axes, [("Educación", edu_m), ("Empleo", emp_m)]):
    for s in ORDER:
        ax.plot(
            dfm.index,
            dfm[s],
            label=LABEL_ES[s],
            color=SENTIMENT_COLORS[s],
            linewidth=2.1
        )

    ax.fill_between(dfm.index, dfm["negative"].values, 0,
                    color=SENTIMENT_COLORS["negative"], alpha=0.05)

    for date_str, label, short_lbl in MILESTONES:
        dt = pd.Timestamp(date_str)
        if dt >= dfm.index.min() and dt <= dfm.index.max():
            ax.axvline(dt, color=T["muted"], linestyle="--", linewidth=1.0, alpha=0.55)
            ax.text(
                dt, 93, f"{label}\n{short_lbl}",
                ha="center", va="center",
                fontsize=7.5,
                color=T["text"],
                bbox=dict(boxstyle="round,pad=0.18", fc=T["surface"], ec=T["border"], alpha=0.9)
            )

    ax.set_title(nombre, fontsize=13)
    ax.set_ylabel("% de comentarios")
    ax.set_ylim(0, 100)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)

axes[0].legend(loc="upper left", fontsize=9, frameon=True)
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig2, use_container_width=True)

# ════════════════════════════════════════════════════════════
#  BLOQUE 3 — Pre vs Post ChatGPT
# ════════════════════════════════════════════════════════════
st.markdown(
    f'<p style="font-family:\'Playfair Display\',serif;font-size:20px;'
    f'font-weight:700;color:{T["text"]};margin:18px 0 6px 0">'
    f'Comparación pre- y post-ChatGPT por sector</p>'
    f'<p style="color:{T["muted"]};font-size:14px;line-height:1.6;margin-bottom:16px">'
    f'La composición del sentimiento se compara antes y después de noviembre de 2022.</p>',
    unsafe_allow_html=True,
)

phase_rows = []
for sector_name, subset in [("Educación", edu), ("Empleo", emp)]:
    for fase in ["Pre-ChatGPT", "Post-ChatGPT"]:
        sub = subset[subset["fase"] == fase]
        pct = sentiment_pct(sub)
        phase_rows.append({
            "grupo": f"{sector_name} · {fase}",
            "positive": pct["positive"],
            "neutral": pct["neutral"],
            "negative": pct["negative"],
        })

phase_df = pd.DataFrame(phase_rows)

fig3, ax = plt.subplots(figsize=(11.5, 4.8))
y = np.arange(len(phase_df))
left = np.zeros(len(phase_df))

for s in ORDER:
    vals = phase_df[s].values
    ax.barh(
        y, vals, left=left,
        color=SENTIMENT_COLORS[s],
        edgecolor="white",
        linewidth=0.8,
        alpha=0.92,
        label=LABEL_ES[s]
    )
    for i, (v, l) in enumerate(zip(vals, left)):
        if v > 7:
            ax.text(l + v / 2, i, f"{v:.1f}%",
                    ha="center", va="center",
                    fontsize=9.5, color="white", fontweight="bold")
    left += vals

ax.axvline(50, color=T["muted"], linewidth=1.0, linestyle="--", alpha=0.35)
ax.set_yticks(y)
ax.set_yticklabels(phase_df["grupo"], fontsize=10.5)
ax.set_xlabel("% de comentarios")
ax.set_xlim(0, 100)
ax.set_title("Distribución del sentimiento por sector y periodo", fontsize=13, fontweight="bold", pad=12)
ax.legend(loc="lower right", fontsize=9, framealpha=0.85)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", alpha=0.2)
ax.set_axisbelow(True)

plt.tight_layout()
st.pyplot(fig3, use_container_width=True)

# ════════════════════════════════════════════════════════════
#  BLOQUE 4 — Canales
# ════════════════════════════════════════════════════════════
with st.expander("Ver canales más representativos por sector"):
    st.markdown(
        f'<p style="color:{T["muted"]};font-size:14px;line-height:1.6;margin-bottom:14px">'
        f'Se incluyen solo canales con suficiente volumen de comentarios para evitar interpretaciones espurias.</p>',
        unsafe_allow_html=True,
    )

    def top_channels_table(df_sector, sector_name, min_comments=80, top_n=10):
        stats = (
            df_sector.groupby("channel")["sentiment_label"]
            .value_counts(normalize=True)
            .mul(100)
            .unstack(fill_value=0)
            .reindex(columns=["negative", "neutral", "positive"], fill_value=0)
            .round(1)
        )
        counts = df_sector["channel"].value_counts().rename("Comentarios")
        stats = stats.join(counts)
        stats = stats[stats["Comentarios"] >= min_comments]
        stats = stats.sort_values(["negative", "Comentarios"], ascending=[False, False]).head(top_n)
        stats = stats.rename(columns={
            "negative": "% Negativo",
            "neutral": "% Neutral",
            "positive": "% Positivo",
        })
        st.markdown(
            f'<p style="font-family:\'Playfair Display\',serif;font-size:17px;'
            f'font-weight:700;color:{T["text"]};margin:8px 0 8px 0">{sector_name}</p>',
            unsafe_allow_html=True,
        )
        st.dataframe(stats, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        top_channels_table(edu, "Educación")
    with c2:
        top_channels_table(emp, "Empleo")

# ── Footer ────────────────────────────────────────────────────
st.divider()
st.markdown(
    f'<p style="font-family:\'DM Mono\',monospace;font-size:12px;color:{T["muted"]}">'
    f'Fuente: youtube_sentiment_v2.parquet · '
    f'Educación n={len(edu):,} · Empleo n={len(emp):,} · '
    f'Modelo: cardiffnlp/twitter-xlm-roberta-base-sentiment</p>',
    unsafe_allow_html=True,
)