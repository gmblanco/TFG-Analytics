"""
generate_explorer_csv.py
========================
Script offline que lee los parquets de Twitter y YouTube,
aplica toda la lógica de curación/filtrado/scoring del Explorer,
limpia el HTML de los comentarios de YouTube y genera un CSV
con exactamente 4 columnas:

    platform, sentiment, sector, message

Ejecutar desde la carpeta app/:
    python generate_explorer_csv.py

Genera:  data/processed/explorer_comments.csv
"""
from __future__ import annotations

import hashlib
import html
import re
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd

# ─── rutas ───────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data" / "processed"
OUTPUT_PATH = DATA_DIR / "explorer_comments.csv"

MAX_COMMENTS = 100


# =========================================================
#  HTML STRIPPING (nuclear approach)
# =========================================================

class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._pieces: list[str] = []

    def handle_data(self, data: str):
        self._pieces.append(data)

    def handle_entityref(self, name: str):
        self._pieces.append(f"&{name};")

    def handle_charref(self, name: str):
        self._pieces.append(f"&#{name};")

    def error(self, message):
        pass

    def get_text(self) -> str:
        return " ".join(self._pieces)


def strip_html(text: str) -> str:
    """Elimina TODO el HTML de un string."""
    if pd.isna(text) or text is None:
        return ""
    text = str(text)

    # Desescapar entidades HTML repetidamente
    for _ in range(5):
        new = html.unescape(text)
        if new == text:
            break
        text = new

    # Limpiar escapes literales
    text = (
        text.replace("\\n", " ")
            .replace("\\t", " ")
            .replace('\\"', '"')
            .replace("\\/", "/")
    )

    # Si contiene algo que parezca HTML, usar el parser
    if "<" in text and ">" in text:
        # Intentar extraer contenido de comment-text primero
        m = re.search(
            r'class=["\']comment-text["\'][^>]*>(.*)',
            text, flags=re.IGNORECASE | re.DOTALL,
        )
        if m:
            text = m.group(1)

        try:
            extractor = _HTMLTextExtractor()
            extractor.feed(text)
            text = extractor.get_text()
        except Exception:
            text = re.sub(r'<[^>]*>', '', text)

    # Limpieza final
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# =========================================================
#  COLUMN HELPERS
# =========================================================

def _first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower_map:
            return lower_map[c.lower()]
    return None


def _norm_sentiment(x) -> str:
    if pd.isna(x):
        return "Neutral"
    val = str(x).strip().lower()
    m = {
        "positive": "Positivo", "positivo": "Positivo", "pos": "Positivo",
        "negative": "Negativo", "negativo": "Negativo", "neg": "Negativo",
        "neutral": "Neutral", "neutro": "Neutral", "neu": "Neutral",
    }
    return m.get(val, str(x).strip().title())


def _norm_sector(x) -> str:
    if pd.isna(x):
        return ""
    val = str(x).strip()
    if not val:
        return ""
    lower = val.lower()
    if lower in {"other", "otro", "otros"}:
        return ""
    m = {
        "education": "Educación", "empleo": "Empleo", "employment": "Empleo",
        "healthcare": "Salud", "health": "Salud", "finance": "Finanzas",
        "ethics": "Ética", "regulation": "Regulación", "technology": "Tecnología",
    }
    return m.get(lower, val.title())


def _map_yt_sector(row: pd.Series) -> str:
    topic = str(row.get("topic", "")).strip().lower()
    if topic == "education":
        return "Educación"
    if topic == "employment":
        return "Empleo"
    if topic == "both":
        return "Educación"
    return ""


# =========================================================
#  NORMALIZE DataFrames
# =========================================================

def normalize_twitter(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["platform", "message", "sentiment", "sector"])

    if "language" in df.columns:
        df = df[df["language"].str.lower().eq("en")].copy()
    if df.empty:
        return pd.DataFrame(columns=["platform", "message", "sentiment", "sector"])

    text_col = _first_col(df, ["tweet_clean_filt", "tweet_clean", "tweet", "text", "content", "comment"])
    sent_col = _first_col(df, ["sentiment_label_hf", "sentiment", "label"])
    sect_col = _first_col(df, ["sector", "topic_sector", "category"])

    return pd.DataFrame({
        "platform": "Twitter",
        "message": df[text_col].apply(strip_html) if text_col else "",
        "sentiment": df[sent_col].apply(_norm_sentiment) if sent_col else "Neutral",
        "sector": df[sect_col].apply(_norm_sector) if sect_col else "",
    })


def normalize_youtube(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["platform", "message", "sentiment", "sector"])

    text_candidates = ["comment", "text", "content", "comment_clean", "text_clean", "comment_text"]
    sent_col = _first_col(df, ["sentiment_label", "sentiment_label_hf", "sentiment", "label"])
    sect_col = _first_col(df, ["sector", "topic_sector", "category"])

    if sect_col:
        sector_series = df[sect_col].apply(_norm_sector)
    elif "topic" in df.columns:
        sector_series = df.apply(_map_yt_sector, axis=1)
    else:
        sector_series = ""

    def pick_text(row):
        for col in text_candidates:
            if col in row.index:
                cleaned = strip_html(row[col])
                if cleaned:
                    return cleaned
        return ""

    return pd.DataFrame({
        "platform": "YouTube",
        "message": df.apply(pick_text, axis=1),
        "sentiment": df[sent_col].apply(_norm_sentiment) if sent_col else "Neutral",
        "sector": sector_series,
    })


# =========================================================
#  CURATION — misma lógica que el explorer original
# =========================================================

AI_SPECIFIC_PATTERNS = [
    r"\bartificial intelligence\b", r"\bmachine learning\b", r"\bdeep learning\b",
    r"\bgenerative ai\b", r"\bgenai\b", r"\bchatgpt\b", r"\bgpt[- ]?[34]?\b",
    r"\bllm[s]?\b", r"\blarge language model\b", r"\bneural network[s]?\b",
    r"\bai model[s]?\b", r"\bdeepfake[s]?\b",
]
AI_SPECIFIC_RE = re.compile("|".join(AI_SPECIFIC_PATTERNS), re.IGNORECASE)

AI_CONTEXT_WORDS = re.compile(
    r"\b(robot[s]?|automat\w+|algorithm[s]?|data science|natural language|nlp|"
    r"superintelligence|autonomous|computer vision|facial recognition|"
    r"job[s]?\b|worker[s]?\b|replac\w+|school|student[s]?|teacher[s]?|"
    r"bias|ethic[s]?|regulat\w+|privacy|surveillance|healthcare|diagnos\w+)\b",
    re.IGNORECASE,
)
AI_BARE = re.compile(r"\bai\b", re.IGNORECASE)

SPAM_RE = re.compile(
    r"\b(click here|subscribe|follow me|link in bio|buy now|promo|giveaway|"
    r"join now|dm me|check out my|use code|discount)\b", re.IGNORECASE,
)

LOW_VALUE_RE = re.compile(
    r"\b(poemoftheday|100daysofcode|marketresearch|financialastrology|"
    r"breakingnews|breaking news)\b|"
    r"^rt\s+\w+|"
    r"\bhas passed away.*future tweets\b|"
    r"\bwill now be conducted by artificial intelligence\b|"
    r"\bjoin us for\b|\bregister now\b|\bfree webinar\b|\blearn more at\b",
    re.IGNORECASE,
)

OPINION_WORDS = re.compile(
    r"\b(because|should|shouldn't|think[s]?|believe[s]?|feel[s]?\b|"
    r"worried|concern\w*|hope[s]?\b|fear[s]?\b|afraid|important|"
    r"disagree|agree\b|unfortunately|hopefully|honestly|"
    r"danger\w*|benefit[s]?|problem\w*|challenge[s]?|opportunity|"
    r"impact\w*|risk[s]?)\b", re.IGNORECASE,
)

EN_FUNCTION_WORDS = re.compile(
    r"\b(the|is|are|was|were|this|that|with|have|has|had|not|from|they|"
    r"will|would|could|should|can|but|for|you|your|their|its|our|we|it|"
    r"be|been|being|do|does|did|all|when|what|how|who|if|as|so|just|"
    r"than|more|about|there|into|him|her|his|she|he|an|of|to|a)\b",
    re.IGNORECASE,
)

SECTOR_KEYWORDS = {
    "Educación": [
        r"\beducation\b", r"\bschool\b", r"\bstudent[s]?\b", r"\bteacher[s]?\b",
        r"\blearn(?:ing)?\b", r"\bclassroom\b", r"\bessay\b", r"\buniversity\b",
        r"\bcollege\b", r"\bplagiarism\b", r"\bprofessor[s]?\b", r"\bcurriculum\b",
        r"\bhomework\b", r"\bteach(?:ing)?\b",
    ],
    "Empleo": [
        r"\bjob[s]?\b", r"\bworker[s]?\b", r"\bworkforce\b", r"\bemployment\b",
        r"\bunemployment\b", r"\blayoff[s]?\b", r"\bcareer[s]?\b", r"\bworkplace\b",
        r"\bproductivity\b", r"\breplace(?:d|ment|s)?\b", r"\bsalary\b",
        r"\bhiring\b", r"\bautomation\b", r"\bwork(?:ing)?\b",
    ],
}

SECTOR_HIGH_CONF = {
    "Educación": re.compile(
        r"\b(student[s]?|teacher[s]?|classroom|university|college|plagiarism|curriculum|professor[s]?)\b",
        re.IGNORECASE,
    ),
    "Empleo": re.compile(
        r"\b(worker[s]?|workforce|unemployment|layoff[s]?|workplace|reskill\w*)\b",
        re.IGNORECASE,
    ),
}

FINANCE_OVERRIDE = re.compile(
    r"\b(stock[s]?|trading|ticker|crypto|bitcoin|invest\w*|portfolio|"
    r"etf|dividend|earnings|forex|fund[s]?\b|ipo|nasdaq)\b", re.IGNORECASE,
)


def has_ai_relevance(text: str) -> bool:
    if AI_SPECIFIC_RE.search(text):
        return True
    if AI_BARE.search(text) and AI_CONTEXT_WORDS.search(text):
        return True
    if re.search(r"\b(robot[s]?|automat\w+|algorithm[s]?)\b", text, re.IGNORECASE):
        return True
    return False


def is_english(text: str) -> bool:
    letters = re.findall(r"[a-zA-ZàáâãäåæçèéêëìíîïðñòóôõöùúûüýþÿÀ-ÿ]", text)
    if not letters:
        return False
    ascii_letters = re.findall(r"[a-zA-Z]", text)
    if len(ascii_letters) / len(letters) < 0.70:
        return False
    return len(set(EN_FUNCTION_WORDS.findall(text.lower()))) >= 2


def sector_matches_text(sector: str, text: str) -> bool:
    if not sector or sector not in SECTOR_KEYWORDS:
        return True
    patterns = SECTOR_KEYWORDS[sector]
    matches = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    if matches < 1:
        return False
    anchor = SECTOR_HIGH_CONF.get(sector)
    if anchor and anchor.search(text):
        return True
    if matches < 2:
        return False
    if sector == "Educación" and FINANCE_OVERRIDE.search(text):
        return False
    return True


def compute_score(text: str, sector: str) -> float:
    score = 0.0
    words = re.findall(r"\b\w+\b", text.lower())
    n_words = len(words)

    if has_ai_relevance(text):
        score += 4.0
    if AI_SPECIFIC_RE.search(text):
        score += 3.0

    if 15 <= n_words <= 40:
        score += 4.0
    elif 10 <= n_words <= 60:
        score += 2.0
    else:
        score -= 3.0

    n_hash = len(re.findall(r"#\w+", text))
    n_ment = len(re.findall(r"@\w+", text))
    n_urls = len(re.findall(r"http\S+|www\.\S+", text))

    score -= 2.0 * n_hash
    score -= 1.5 * n_ment
    score -= 3.0 * n_urls

    if n_words > 0:
        rep_ratio = 1 - len(set(words)) / n_words
        score -= 10.0 * rep_ratio

    if SPAM_RE.search(text):
        score -= 5.0
    if LOW_VALUE_RE.search(text):
        score -= 3.0

    if sector and sector_matches_text(sector, text):
        score += 1.5
    if sector:
        score += 1.0

    if OPINION_WORDS.search(text):
        score += 2.0

    return score


def curate(df: pd.DataFrame, n: int = MAX_COMMENTS) -> pd.DataFrame:
    """Aplica filtros de calidad y devuelve los mejores n comentarios."""
    df = df.copy()

    # Filtros básicos
    df = df[df["message"].str.strip() != ""].copy()
    df = df[df["message"].apply(is_english)].copy()
    df = df[df["message"].apply(has_ai_relevance)].copy()

    # Filtros de calidad
    df["_n_words"] = df["message"].str.split().str.len()
    df = df[df["_n_words"].between(10, 80)].copy()
    df = df[~df["message"].str.contains(SPAM_RE, na=False)].copy()
    df = df[~df["message"].str.contains(r"http\S+|www\.\S+", na=False)].copy()

    # Score
    df["_score"] = df.apply(lambda r: compute_score(r["message"], r["sector"]), axis=1)
    df = df.sort_values("_score", ascending=False)

    # Diversidad: max 8 por (platform, sentiment, sector)
    selected = []
    combo_counts: dict = {}
    seen: set = set()

    for _, row in df.iterrows():
        combo = (row["platform"], row["sentiment"], row["sector"])
        fingerprint = re.sub(r"\s+", " ", row["message"].lower().strip())[:55]

        if fingerprint in seen:
            continue
        if combo_counts.get(combo, 0) >= 8:
            continue

        selected.append(row)
        combo_counts[combo] = combo_counts.get(combo, 0) + 1
        seen.add(fingerprint)

        if len(selected) >= n:
            break

    result = pd.DataFrame(selected)
    return result[["platform", "sentiment", "sector", "message"]].reset_index(drop=True)


# =========================================================
#  MAIN
# =========================================================

def main():
    print("Leyendo parquets...")

    # Twitter
    tw_path = DATA_DIR / "tweets_op_sectored.parquet"
    if tw_path.exists():
        tw = normalize_twitter(pd.read_parquet(tw_path))
        print(f"  Twitter: {len(tw)} filas normalizadas")
    else:
        tw = pd.DataFrame(columns=["platform", "message", "sentiment", "sector"])
        print("  Twitter: no encontrado")

    # YouTube
    yt = pd.DataFrame(columns=["platform", "message", "sentiment", "sector"])
    for fname in ["youtube_sentiment_v2.parquet", "youtube_sentiment.parquet", "youtube_comments_clean.parquet"]:
        p = DATA_DIR / fname
        if p.exists():
            yt = normalize_youtube(pd.read_parquet(p))
            print(f"  YouTube: {len(yt)} filas normalizadas (de {fname})")
            break
    if yt.empty:
        print("  YouTube: no encontrado")

    # Combinar
    df = pd.concat([tw, yt], ignore_index=True)
    print(f"\nTotal combinado: {len(df)} filas")

    # Verificar limpieza HTML
    has_html = df["message"].str.contains(r"<\s*/?\s*div", case=False, na=False).sum()
    print(f"Mensajes con HTML residual antes de curar: {has_html}")

    # Curar
    result = curate(df, n=MAX_COMMENTS)
    print(f"Comentarios curados: {len(result)}")

    # Verificar limpieza final
    has_html_final = result["message"].str.contains(r"<\s*/?\s*div", case=False, na=False).sum()
    print(f"Mensajes con HTML residual después de curar: {has_html_final}")

    # Stats
    print(f"\nDesglose:")
    print(f"  Twitter:  {(result['platform'] == 'Twitter').sum()}")
    print(f"  YouTube:  {(result['platform'] == 'YouTube').sum()}")
    print(f"  Positivo: {(result['sentiment'] == 'Positivo').sum()}")
    print(f"  Neutral:  {(result['sentiment'] == 'Neutral').sum()}")
    print(f"  Negativo: {(result['sentiment'] == 'Negativo').sum()}")

    # Guardar
    result.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"\n✓ Guardado en: {OUTPUT_PATH}")

    # Mostrar 3 ejemplos
    print("\n─── Ejemplos ───")
    for i, row in result.head(3).iterrows():
        print(f"  [{row['platform']}] [{row['sentiment']}] [{row['sector']}]")
        print(f"  {row['message'][:120]}...")
        print()


if __name__ == "__main__":
    main()