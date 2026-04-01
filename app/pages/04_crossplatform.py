from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"


def main() -> None:
    st.markdown(
        """
        <div class="page-wrap">
            <div class="section-tag">04 · Comparativa cross-platform · H3</div>
            <h1 class="section-title">Twitter vs YouTube</h1>
            <p class="section-subtitle">
                ¿Influye la plataforma en cómo se percibe la IA? Comparación directa entre
                dos formatos de opinión pública digital. Período solapado: 2020–2021.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info("Página en construcción")


if __name__ == "__main__":
    main()
