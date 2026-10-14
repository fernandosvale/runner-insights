import hashlib
import logging
import os
import re
import sys

import pandas as pd

from src.utils import formatar_minutos_para_pace

logger = logging.getLogger(__name__)


def carregar_dados_brutos():
    """Busca o arquivo CSV bruto na pasta data/raw de forma segura."""
    pasta_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caminho_csv = os.path.join(pasta_raiz, "data", "raw", "corridas_fortaleza_bruto.csv")

    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"O arquivo bruto não foi encontrado em: {caminho_csv}. Rode o scraper primeiro!")

    logger.info("Carregando dados brutos de: %s", caminho_csv)
    return pd.read_csv(caminho_csv)


def converter_tempo_para_minutos(tempo_str):
    """Converte uma string 'HH:MM:SS' para minutos totais em float."""
    try:
        if pd.isna(tempo_str) or not isinstance(tempo_str, str):
            return None

        partes = tempo_str.split(':')
        if len(partes) == 3:
            horas, minutos, segundos = map(int, partes)
            return horas * 60 + minutos + segundos / 60.0
        elif len(partes) == 2:
            minutos, segundos = map(int, partes)
            return minutos + segundos / 60.0
        return None
    except Exception:
        return None


def extrair_distancia_numerica(distancia_str):
    """Extrai apenas o valor numérico da distância (ex: '5K' -> 5.0, '21K' -> 21.0)."""
    try:
        if pd.isna(distancia_str) or not isinstance(distancia_str, str):
            return None

        # Encontra os números (incluindo decimais se houver, ex: 5.5K)
        numeros = re.findall(r'[\d\.]+', distancia_str)
        if numeros:
            return float(numeros[0])
        return None
    except Exception:
        return None


def anonimizar_nome(nome_completo):
    """Reduz o nome a 'Primeiro S.' (LGPD: evita expor o nome completo)."""
    if not isinstance(nome_completo, str) or not nome_completo.strip():
        return "Anônimo"
    partes = nome_completo.strip().title().split()
    if len(partes) == 1:
        return partes[0]
    return f"{partes[0]} {partes[-1][0]}."


def gerar_id_atleta(nome_completo, url_corrida):
    """Gera um identificador estável (hash) sem expor o nome."""
    base = f"{nome_completo}|{url_corrida}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()[:10]


def inferir_sexo_pelo_nome(nome_completo):
    """
    Infere o sexo (M/F) com base no primeiro nome do atleta.
    Usa terminações comuns do português e uma lista de nomes frequentes.
    Retorna 'N/I' quando o nome é ambíguo (estimativa, não dado oficial).
    """
    if not isinstance(nome_completo, str) or not nome_completo.strip():
        return "N/I"  # Não Identificado

    # Isola o primeiro nome e coloca em maiúsculas
    primeiro_nome = nome_completo.strip().split()[0].upper()

    # Nomes masculinos comuns que terminam com 'A' ou outras vogais
    excecoes_masculinas = {
        "LUCA", "LUCAS", "GABRIEL", "RAFAEL", "DANIEL", "MATEUS", "MATHEUS",
        "JOSÉ", "JOSE", "ALEXANDRE", "ANDRÉ", "ANDRE", "FELIPE", "JORGE",
        "JONAS", "ELIAS", "ISAAC", "JOSHUA", "MURILO", "OTÁVIO", "OTAVIO",
        "GUILHERME", "JOSUÉ", "JOSUE", "NICOLA", "MOISÉS", "MOISES"
    }

    # Nomes femininos comuns que não terminam com 'A'
    excecoes_femininas = {
        "BEATRIZ", "ALICE", "CAROL", "RAQUEL", "ESTER", "ESTHER", "INGRID",
        "KAREN", "MIRIAM", "RUTE", "RUTH", "SUELI", "LIZ", "IRIS", "AINE",
        "ISABEL", "ALINE", "MICHELE", "SIMONE", "JANETE", "DENISE", "ELIANE",
        "MARISOL", "MABEL", "NAIR", "IVONE", "SOLANGE", "LUCIENE", "ROSE"
    }

    if primeiro_nome in excecoes_masculinas:
        return "M"
    if primeiro_nome in excecoes_femininas:
        return "F"

    # Regra geral da língua portuguesa
    if primeiro_nome.endswith('A'):
        return "F"

    # Terminações predominantemente masculinas; as demais (E, I, Y...) são ambíguas
    if primeiro_nome[-1] in "OSRLNMDKTCXZHUPBGFVJW":
        return "M"

    return "N/I"


def tratar_dados_atletas(df_bruto):
    """Aplica as transformações, limpezas e cálculos de performance com Pandas."""
    logger.info("Iniciando o tratamento dos dados...")

    # Criando uma cópia para não alterar o DataFrame original
    df = df_bruto.copy()

    # 0. Remove duplicatas (ex.: scraper executado duas vezes ou página repetida)
    antes = len(df)
    df = df.drop_duplicates(subset=['url_corrida', 'nome_atleta', 'tempo_bruto', 'detalhes_atleta'])
    if len(df) < antes:
        logger.warning("%d registros duplicados removidos.", antes - len(df))

    # 1. Extrações básicas de texto
    df['numero_peito'] = df['detalhes_atleta'].str.extract(r'N°\s*(\d+)')
    df['distancia_prova'] = df['detalhes_atleta'].str.extract(r'-\s*([\wKk\.,]+)')

    # 2. Limpezas de strings
    df['nome_atleta'] = df['nome_atleta'].str.strip()
    df['distancia_prova'] = df['distancia_prova'].str.strip().str.upper()
    df['nome_prova'] = df['nome_prova'].str.strip()

    # 3. Inferência de Sexo pelo Nome (estimativa, feita antes de anonimizar)
    df['sexo'] = df['nome_atleta'].apply(inferir_sexo_pelo_nome)

    # 4. Conversões matemáticas de tempo e quilometragem
    df['tempo_total_minutos'] = df['tempo_bruto'].apply(converter_tempo_para_minutos)
    df['distancia_km'] = df['distancia_prova'].apply(extrair_distancia_numerica)

    # 5. Cálculo de Performance: Pace Decimal e Pace Formato de Corrida (MM:SS)
    df['pace_decimal'] = df['tempo_total_minutos'] / df['distancia_km'].where(df['distancia_km'] > 0)
    df['pace_min_km'] = df['pace_decimal'].apply(formatar_minutos_para_pace)

    # 6. Anonimização (LGPD): identificador em hash + nome reduzido
    df['id_atleta'] = [gerar_id_atleta(n, u) for n, u in zip(df['nome_atleta'], df['url_corrida'])]
    df['nome_atleta'] = df['nome_atleta'].apply(anonimizar_nome)

    # Remove colunas intermediárias que não farão sentido no dashboard final
    df = df.drop(columns=['detalhes_atleta'])

    return df


def executar_pipeline_tratamento():
    # Passo 1: Ler os dados salvos pelo Scraper
    df_bruto = carregar_dados_brutos()

    # Passo 2: Aplicar os tratamentos e cálculos
    df_tratado = tratar_dados_atletas(df_bruto)
    logger.info("Amostra dos dados tratados:\n%s", df_tratado[
        ['nome_atleta', 'sexo', 'tempo_bruto', 'distancia_km', 'pace_min_km']].head())

    # Passo 3: Salvar na pasta de dados processados
    pasta_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caminho_salvamento = os.path.join(pasta_raiz, "data", "processed", "corridas_fortaleza_limpo.csv")
    os.makedirs(os.path.dirname(caminho_salvamento), exist_ok=True)

    df_tratado.to_csv(caminho_salvamento, index=False, encoding="utf-8-sig")
    logger.info("Dados tratados salvos em: %s", caminho_salvamento)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    try:
        executar_pipeline_tratamento()
    except Exception:
        logger.exception("Falha no pipeline de tratamento")
        sys.exit(1)