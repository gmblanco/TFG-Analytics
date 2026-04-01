from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"


def main() -> None:
    st.markdown(
        """
        <div class="page-wrap">
            <div class="section-tag">03 · Análisis sectorial · H2</div>
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

    st.info("Página en construcción")


if __name__ == "__main__":
    main()
