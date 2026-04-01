from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"


def main() -> None:
    st.markdown(
        """
        <div class="page-wrap">
            <div class="section-tag">02 · Evolución temporal · H1</div>
            <h1 class="section-title">El punto de inflexión</h1>
            <p class="section-subtitle">
                Evolución mensual del sentimiento en ambas plataformas. ChatGPT marca un antes
                y un después visible en los datos.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info("Página en construcción")


if __name__ == "__main__":
    main()
