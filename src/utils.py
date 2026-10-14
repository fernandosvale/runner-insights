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


def calcular_metricas_estatisticas(series: pd.Series) -> dict[str, float]:
    """Calcula média, mediana e percentis (P10, P25, P50, P75, P90) de uma série numérica."""
    validos = series.dropna()
    if validos.empty:
        return {}

    return {
        "media": float(validos.mean()),
        "mediana": float(validos.median()),
        "desvio_padrao": float(validos.std()) if len(validos) > 1 else 0.0,
        "min": float(validos.min()),
        "p10": float(validos.quantile(0.10)),
        "p25": float(validos.quantile(0.25)),
        "p50": float(validos.median()),
        "p75": float(validos.quantile(0.75)),
        "p90": float(validos.quantile(0.90)),
        "max": float(validos.max()),
    }
