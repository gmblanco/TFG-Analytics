from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"


def main() -> None:
    st.markdown(
        """
        <div class="page-wrap">
            <div class="section-tag">Herramientas · Explorador</div>
            <h1 class="section-title">Explorador de comentarios</h1>
            <p class="section-subtitle">
                Busca y filtra por plataforma, sentimiento, sector y período.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info("Página en construcción")


if __name__ == "__main__":
    main()
