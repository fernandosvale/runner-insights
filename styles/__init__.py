"""Identidade visual do RunnerInsights (ver DESIGN_SYSTEM.md)."""
from pathlib import Path

import streamlit as st

from styles.design_tokens import css_variables

_THEME_CSS = Path(__file__).with_name("theme.css")


def aplicar_tema() -> None:
    """Injeta tokens + theme.css na página atual do Streamlit."""
    css = _THEME_CSS.read_text(encoding="utf-8")
    st.markdown(f"<style>\n{css_variables()}\n{css}\n</style>", unsafe_allow_html=True)
