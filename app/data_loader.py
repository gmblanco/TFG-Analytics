from pathlib import Path
import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data" / "processed"


@st.cache_data(show_spinner=False)
def load_parquet(filename: str) -> pd.DataFrame:
    file_path = DATA_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {file_path}")
    return pd.read_parquet(file_path)


@st.cache_data(show_spinner=False)
def load_twitter_sentiment() -> pd.DataFrame:
    return load_parquet("tweets_ai_sentiment_hf.parquet")


@st.cache_data(show_spinner=False)
def load_youtube_sentiment() -> pd.DataFrame:
    candidates = [
        "youtube_sentiment_v2.parquet",
        "youtube_sentiment.parquet",
        "youtube_comments_clean.parquet",
    ]

    for filename in candidates:
        file_path = DATA_DIR / filename
        if file_path.exists():
            return pd.read_parquet(file_path)

    raise FileNotFoundError(
        "No se encontró ningún parquet de YouTube esperado en data/processed."
    )


@st.cache_data(show_spinner=False)
def get_dataset_shapes() -> dict:
    result = {}

    try:
        tw = load_twitter_sentiment()
        result["twitter_rows"] = len(tw)
        result["twitter_cols"] = list(tw.columns)
    except Exception as exc:
        result["twitter_error"] = str(exc)

    try:
        yt = load_youtube_sentiment()
        result["youtube_rows"] = len(yt)
        result["youtube_cols"] = list(yt.columns)
    except Exception as exc:
        result["youtube_error"] = str(exc)

    return result