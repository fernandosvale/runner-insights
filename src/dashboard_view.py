"""Módulo de renderização do Dashboard Visual Chamativo (HTML/CSS/JS integrado)."""

import json
from pathlib import Path

import pandas as pd

TEMPLATE_PATH = Path(__file__).parent / "templates" / "dashboard.html"


def gerar_html_dashboard(df: pd.DataFrame | None = None) -> str:
    """Carrega o template HTML e injeta os registros do DataFrame como JSON.

    Parameters
    ----------
    df : Optional[pd.DataFrame]
        DataFrame tratado contendo as corridas.

    Returns
    -------
    str
        Código HTML completo pronto para ser injetado via st.components.v1.html.
    """
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template do dashboard não encontrado em {TEMPLATE_PATH}")

    template_html = TEMPLATE_PATH.read_text(encoding="utf-8")

    if df is not None and not df.empty:
        # Garante que NaNs sejam convertidos em null/None para JSON válido
        registros = df.where(pd.notnull(df), None).to_dict(orient="records")
        dados_json = json.dumps(registros, ensure_ascii=False)
    else:
        dados_json = "[]"

    return template_html.replace("__INITIAL_DATA_PLACEHOLDER__", dados_json)
