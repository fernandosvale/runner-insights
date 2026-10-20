"""Testes unitários para a geração do HTML do Dashboard Visual."""

import pandas as pd

from src.dashboard_view import gerar_html_dashboard


def test_gerar_html_dashboard_com_dados():
    df = pd.DataFrame(
        [
            {
                "nome_prova": "Circuito das Estações - Fortaleza",
                "nome_atleta": "Corredor A.",
                "sexo": "M",
                "tempo_bruto": "00:22:15",
                "numero_peito": "123",
                "distancia_prova": "5K",
                "distancia_km": 5.0,
                "tempo_total_minutos": 22.25,
                "pace_decimal": 4.45,
                "pace_min_km": "04:27",
            }
        ]
    )
    html = gerar_html_dashboard(df)
    assert "<!DOCTYPE html>" in html
    assert "RunnerInsights" in html
    assert "Circuito das Estações - Fortaleza" in html
    assert "Corredor A." in html
    assert "__INITIAL_DATA_PLACEHOLDER__" not in html


def test_gerar_html_dashboard_vazio():
    html = gerar_html_dashboard(None)
    assert "<!DOCTYPE html>" in html
    assert "__INITIAL_DATA_PLACEHOLDER__" not in html
    assert "const INITIAL_DATA = [];" in html
