import pandas as pd
import pandera.errors
import pytest

from src.validation import validar_dados_tratados


def _linha(**sobrescrever):
    base = {
        "nome_prova": "Corrida A",
        "nome_atleta": "Maria S.",
        "id_atleta": "abc123",
        "sexo": "F",
        "tempo_total_minutos": 25.0,
        "distancia_km": 5.0,
        "pace_decimal": 5.0,
    }
    base.update(sobrescrever)
    return base


def test_dados_validos_passam():
    df = pd.DataFrame([_linha()])
    assert len(validar_dados_tratados(df)) == 1


def test_pace_implausivel_falha():
    df = pd.DataFrame([_linha(pace_decimal=0.5)])
    with pytest.raises(pandera.errors.SchemaErrors):
        validar_dados_tratados(df)


def test_sexo_invalido_falha():
    df = pd.DataFrame([_linha(sexo="X")])
    with pytest.raises(pandera.errors.SchemaErrors):
        validar_dados_tratados(df)


def test_valores_nulos_permitidos_em_metricas():
    df = pd.DataFrame([_linha(tempo_total_minutos=None, pace_decimal=None)])
    assert len(validar_dados_tratados(df)) == 1
