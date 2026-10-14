"""Funções utilitárias compartilhadas entre o pipeline e o dashboard."""
import pandas as pd


def formatar_minutos_para_pace(minutos_decimais):
    """Converte minutos decimais para o formato de ritmo 'MM:SS'. Retorna None se inválido."""
    if minutos_decimais is None or pd.isna(minutos_decimais) or minutos_decimais <= 0:
        return None

    minutos = int(minutos_decimais)
    segundos = int(round((minutos_decimais - minutos) * 60))

    # Trata arredondamento que passa de 59 segundos
    if segundos == 60:
        minutos += 1
        segundos = 0

    return f"{minutos:02d}:{segundos:02d}"
