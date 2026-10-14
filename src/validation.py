"""Validação de schema dos dados tratados (falha cedo se algo estiver fora do esperado)."""
import logging

import pandas as pd
import pandera.pandas as pa

logger = logging.getLogger(__name__)

# Pace plausível para corridas de rua (min/km): de ritmo de elite até caminhada lenta
PACE_MIN, PACE_MAX = 2.0, 20.0

SCHEMA_DADOS_TRATADOS = pa.DataFrameSchema(
    {
        "nome_prova": pa.Column(str, nullable=False),
        "nome_atleta": pa.Column(str, nullable=False),
        "id_atleta": pa.Column(str, nullable=False),
        "sexo": pa.Column(str, pa.Check.isin(["M", "F", "N/I"])),
        "tempo_total_minutos": pa.Column(float, pa.Check.gt(0), nullable=True),
        "distancia_km": pa.Column(float, pa.Check.gt(0), nullable=True),
        "pace_decimal": pa.Column(float, pa.Check.in_range(PACE_MIN, PACE_MAX), nullable=True),
    },
    coerce=True,
    strict=False,
)


def validar_dados_tratados(df: pd.DataFrame) -> pd.DataFrame:
    """Valida o DataFrame tratado e levanta `pandera.errors.SchemaErrors` listando todas as falhas."""
    validado = SCHEMA_DADOS_TRATADOS.validate(df, lazy=True)
    logger.info("Validação de schema concluída: %d registros válidos.", len(validado))
    return validado
