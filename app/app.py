import streamlit as st
from pathlib import Path

from theme import init_page_config, inject_global_css, init_theme_state, render_sidebar_header


BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"


def main() -> None:
    init_page_config()
    init_theme_state()
    inject_global_css(ASSETS_DIR / "style.css")
    render_sidebar_header()

    st.markdown(
        """
        <div class="home-shell">
            <div class="section-tag">TFG · Dashboard</div>
            <h1 class="section-title">Percepción pública de la IA</h1>
            <p class="section-subtitle">
                Base de la aplicación cargada correctamente. Usa el menú lateral para navegar
                entre páginas y construir el dashboard paso a paso.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "La estructura base ya está lista. Ahora construiremos cada página para replicar el mockup."
    )


if __name__ == "__main__":
    main()