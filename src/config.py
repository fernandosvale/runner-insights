"""Configurações centrais do projeto (caminhos, scraper e logging)."""
import logging
import os
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

# Caminhos de dados
PASTA_RAW = RAIZ_PROJETO / "data" / "raw"
PASTA_PROCESSED = RAIZ_PROJETO / "data" / "processed"
CSV_BRUTO = PASTA_RAW / "corridas_fortaleza_bruto.csv"
CSV_LIMPO = PASTA_PROCESSED / "corridas_fortaleza_limpo.csv"

# Scraper (sobrescreva via variáveis de ambiente quando necessário)
URL_BASE_RESULTADOS = os.getenv("RI_URL_BASE", "https://www.o2corre.com.br/resultado/")
URL_DOMINIO = os.getenv("RI_URL_DOMINIO", "https://www.o2corre.com.br")
TERMO_BUSCA = os.getenv("RI_TERMO_BUSCA", "fortaleza")
SCRAPER_HEADLESS = os.getenv("RI_HEADLESS", "false").lower() == "true"
MAX_CLIQUES_VER_MAIS = int(os.getenv("RI_MAX_VER_MAIS", "50"))
MAX_TENTATIVAS_REDE = int(os.getenv("RI_MAX_TENTATIVAS", "3"))


def configurar_logging(nivel: int = logging.INFO) -> None:
    """Configura o formato padrão de logs para os scripts de linha de comando."""
    logging.basicConfig(level=nivel, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
