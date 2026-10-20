import os

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.classic_view import renderizar_dashboard_classico
from src.dashboard_view import gerar_html_dashboard
from styles import aplicar_tema
from styles.plotly_theme import registrar_tema_plotly

# Configuração da página
st.set_page_config(
    page_title="RunnerInsights - Inteligência Esportiva",
    page_icon=":material/directions_run:",
    layout="wide",
)

# Identidade visual oficial
aplicar_tema()
registrar_tema_plotly()


@st.cache_data
def carregar_dados_tratados():
    """Carrega os dados limpos do arquivo CSV processado."""
    pasta_raiz = os.path.dirname(os.path.abspath(__file__))
    caminho_csv = os.path.join(pasta_raiz, "data", "processed", "corridas_fortaleza_limpo.csv")

    if not os.path.exists(caminho_csv):
        return None

    try:
        return pd.read_csv(caminho_csv, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(caminho_csv, encoding="latin1")


df = carregar_dados_tratados()

if df is None:
    st.error(
        "Arquivo de dados tratados não encontrado! Execute `python -m src.pipeline` para processar a base.",
        icon=":material/error:",
    )
else:
    # ----------------------------------------------------
    # SELETOR DE MODO VISUAL
    # ----------------------------------------------------
    st.sidebar.header("Experiência Visual")
    modo_visual = st.sidebar.radio(
        "Estilo do Dashboard:",
        ["Visual Chamativo (Neon)", "Visual Clássico (Streamlit)"],
        index=0,
        help="Alterne entre o novo visual chamativo em HTML/CSS neon ou o dashboard clássico em componentes Streamlit/Plotly.",
    )

    if modo_visual == "Visual Chamativo (Neon)":
        st.markdown(
            """
            <style>
            .block-container {
                padding-top: 0.5rem !important;
                padding-bottom: 0.5rem !important;
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
                max-width: 100% !important;
            }
            iframe {
                border: none !important;
                border-radius: 12px;
                width: 100% !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        html_dashboard = gerar_html_dashboard(df)
        components.html(html_dashboard, height=1950, scrolling=True)
    else:
        renderizar_dashboard_classico(df)
