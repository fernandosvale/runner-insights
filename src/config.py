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
TIMEOUT_NAVEGACAO_MS = int(os.getenv("RI_TIMEOUT_NAVEGACAO_MS", "30000"))
TIMEOUT_ELEMENTO_MS = int(os.getenv("RI_TIMEOUT_ELEMENTO_MS", "10000"))
DELAY_ENTRE_PAGINAS = float(os.getenv("RI_DELAY_PAGINAS", "1.0"))
DELAY_ENTRE_CORRIDAS = float(os.getenv("RI_DELAY_CORRIDAS", "1.5"))
USER_AGENT = os.getenv(
    "RI_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 (RunnerInsights/0.1; +https://github.com/fernandosvale/runner-insights)",
)


def configurar_logging(nivel: int = logging.INFO) -> None:
    """Configura o formato padrão de logs para os scripts de linha de comando."""
    logging.basicConfig(level=nivel, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
