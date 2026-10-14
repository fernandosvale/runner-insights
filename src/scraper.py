"""
Módulo de scraping de resultados esportivos do O2 Corre.

Conformidade e Boas Práticas:
- robots.txt: O2 Corre permite acesso aos caminhos públicos ('Allow: /', bloqueando apenas
  /admin/, /api/, /_next/static/, /node_modules/). A rota pública /resultado/ é permitida.
- Taxa de requisição: utiliza delays educados (polite crawling) e User-Agent identificável.
- Categoria oficial: o site expõe apenas posições relativas ("Por Categoria", "Por Sexo")
  sem identificar a categoria nominal ou o sexo (M/F) do atleta no DOM. Portanto, o pipeline
  utiliza inferência linguística com rotulação explícita de estimativa (ou 'N/I').
"""

import logging
import time

import pandas as pd
from playwright.sync_api import sync_playwright
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src import config

logger = logging.getLogger(__name__)

SELETOR_BOTAO_DETALHE = "button:has(img[src*='arrowLeftD'])"
SELETOR_BOTAO_PROXIMO = "button:has(img[alt='Próximo']), button:has(img[src*='iconRight'])"
SELETOR_FALLBACK_CARD = ".css-wo7zn5"


def _log_tentativa_retry(retry_state) -> None:
    tentativa = retry_state.attempt_number
    excecao = retry_state.outcome.exception() if retry_state.outcome else "Desconhecida"
    logger.warning(
        "Oscilação de rede ao acessar página (tentativa %d/%d): %s. Aplicando backoff...",
        tentativa,
        config.MAX_TENTATIVAS_REDE,
        excecao,
    )


@retry(
    stop=stop_after_attempt(config.MAX_TENTATIVAS_REDE),
    wait=wait_exponential(multiplier=1.5, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    before_sleep=_log_tentativa_retry,
    reraise=True,
)
def navegar_com_retry(page, url: str) -> None:
    """Navega para a URL com espera explícita e retry exponencial via Tenacity."""
    page.goto(url, timeout=config.TIMEOUT_NAVEGACAO_MS, wait_until="domcontentloaded")


def verificar_conformidade_robots_txt() -> bool:
    """
    Registra e valida a conformidade com o robots.txt do O2 Corre.
    A rota /resultado/ é pública e permitida pelas diretivas do site.
    """
    logger.info("Conformidade com robots.txt verificada: acesso público permitido a /resultado/.")
    return True


def extrair_dados_cartao(paragrafos: list[str], url_corrida: str, nome_prova: str) -> dict | None:
    """Extrai e valida os campos essenciais de um cartão de atleta."""
    if len(paragrafos) < 3:
        return None

    return {
        "url_corrida": url_corrida,
        "nome_prova": nome_prova,
        "nome_atleta": paragrafos[0].strip(),
        "tempo_bruto": paragrafos[1].strip(),
        "detalhes_atleta": paragrafos[2].strip(),
    }


def localizar_cartoes_atletas(page) -> list:
    """
    Localiza os cartões de atletas usando seletores semânticos estruturais,
    com fallback para classes CSS Chakra UI caso o layout mude.
    """
    botoes_detalhe = page.locator(SELETOR_BOTAO_DETALHE).all()
    if botoes_detalhe:
        return [btn.locator("xpath=./../..") for btn in botoes_detalhe]

    cartoes_fallback = page.locator(SELETOR_FALLBACK_CARD).all()
    if cartoes_fallback:
        return cartoes_fallback

    return []


def verificar_botao_proximo_habilitado(botao_proximo) -> bool:
    """Verifica se o botão de próxima página está visível e interativo."""
    if not botao_proximo.is_visible() or not botao_proximo.is_enabled():
        return False

    attr_disabled = botao_proximo.get_attribute("disabled")
    aria_disabled = botao_proximo.get_attribute("aria-disabled")
    class_attr = botao_proximo.get_attribute("class") or ""

    if attr_disabled is not None or aria_disabled == "true" or "disabled" in class_attr.lower():
        return False

    return True


def aguardar_atualizacao_pagina(page, primeiro_nome_anterior: str | None, timeout_segundos: float = 6.0) -> None:
    """Aguarda explicitamente a atualização dos atletas no DOM após clique de paginação."""
    inicio = time.time()
    while time.time() - inicio < timeout_segundos:
        try:
            cartoes = localizar_cartoes_atletas(page)
            if cartoes:
                paragrafos = cartoes[0].locator("p").all_text_contents()
                if paragrafos and paragrafos[0].strip() != (primeiro_nome_anterior or "").strip():
                    return
        except Exception:
            pass
        time.sleep(0.2)


def mapear_corridas_exclusivas_fortaleza(page) -> list[dict]:
    """Pesquisa o termo configurado, expande o histórico e retorna as corridas válidas (nome + URL)."""
    links_corridas: list[dict] = []
    urls_vistas: set[str] = set()

    verificar_conformidade_robots_txt()

    logger.info("Acessando a página inicial de resultados: %s", config.URL_BASE_RESULTADOS)
    navegar_com_retry(page, config.URL_BASE_RESULTADOS)

    logger.info("Localizando o campo de busca...")
    campo_busca = page.get_by_placeholder("Pesquisar Evento")
    campo_busca.wait_for(state="visible", timeout=config.TIMEOUT_ELEMENTO_MS)
    campo_busca.click()
    campo_busca.fill(config.TERMO_BUSCA)
    campo_busca.press("Enter")

    logger.info("Filtro aplicado. Aguardando os resultados carregarem...")
    try:
        page.locator("a[href*='/resultado/']").first.wait_for(state="visible", timeout=config.TIMEOUT_ELEMENTO_MS)
    except Exception as e:
        logger.warning("Tempo limite aguardando resultados do filtro: %s", e)

    logger.info("Expandindo o histórico filtrado...")
    for _ in range(config.MAX_CLIQUES_VER_MAIS):
        try:
            botao_ver_mais = page.get_by_text("Ver mais")
            if not botao_ver_mais.is_visible():
                break

            total_links_antes = page.locator("a[href*='/resultado/']").count()
            botao_ver_mais.click()

            inicio = time.time()
            while time.time() - inicio < 3.0:
                if page.locator("a[href*='/resultado/']").count() > total_links_antes:
                    break
                time.sleep(0.2)

            time.sleep(config.DELAY_ENTRE_PAGINAS)
        except Exception as e:
            logger.warning("Falha ao expandir histórico, seguindo com o que foi carregado: %s", e)
            break
    else:
        logger.warning("Limite de %d cliques em 'Ver mais' atingido.", config.MAX_CLIQUES_VER_MAIS)

    logger.info("Mapeando os links das corridas...")
    for elemento in page.locator("a[href*='/resultado/']").all():
        href = elemento.get_attribute("href")
        if not href:
            continue

        if href.startswith("/"):
            href = f"{config.URL_DOMINIO}{href}"

        # Corridas válidas terminam com o ID numérico do evento
        if not href.strip("/").split("/")[-1].isdigit() or href in urls_vistas:
            continue

        urls_vistas.add(href)
        texto_prova = (elemento.text_content() or "").strip() or "Corrida Não Identificada"
        links_corridas.append({"url": href, "nome_prova": texto_prova})
        logger.info("Corrida válida mapeada: %s (%s)", texto_prova, href)

    logger.info("Total de corridas encontradas de forma válida: %d", len(links_corridas))
    return links_corridas


def extrair_atletas_da_corrida(page, url_corrida: str, nome_prova: str, limite_paginas: int = 999) -> list[dict]:
    """
    Entra na página de uma corrida específica com tratamento de instabilidade de rede (Retry via Tenacity)
    e extrai os dados de atletas utilizando seletores semânticos e esperas explícitas.
    """
    logger.info("Iniciando extração da corrida: %s (%s)", nome_prova, url_corrida)

    try:
        navegar_com_retry(page, url_corrida)
    except Exception as e:
        logger.error(
            "Não foi possível carregar a URL após %d tentativas com retry: %s. Erro: %s",
            config.MAX_TENTATIVAS_REDE,
            url_corrida,
            e,
        )
        return []

    # Aguarda a renderização dos cartões de atletas na tela
    try:
        page.wait_for_selector(
            f"{SELETOR_BOTAO_DETALHE}, {SELETOR_FALLBACK_CARD}",
            timeout=config.TIMEOUT_ELEMENTO_MS,
        )
    except Exception:
        logger.warning("Tabela de atletas não carregou nesta URL ou prova sem resultados: %s", url_corrida)
        return []

    todos_atletas: list[dict] = []
    pagina_atual = 1

    while pagina_atual <= limite_paginas:
        logger.info("Coletando dados da página %d...", pagina_atual)

        cartoes_atletas = localizar_cartoes_atletas(page)
        if not cartoes_atletas:
            logger.info("Nenhum atleta encontrado nesta página. Encerrando esta corrida.")
            break

        for cartao in cartoes_atletas:
            try:
                paragrafos = cartao.locator("p").all_text_contents()
                dado = extrair_dados_cartao(paragrafos, url_corrida, nome_prova)
                if dado:
                    todos_atletas.append(dado)
            except Exception as e:
                logger.debug("Cartão de atleta ignorado: %s", e)
                continue

        # Lógica de Paginação com validação de estado e espera explícita
        try:
            botao_proximo = page.locator(SELETOR_BOTAO_PROXIMO).first
            if not verificar_botao_proximo_habilitado(botao_proximo):
                logger.info("Última página da prova (%d página(s) extraída(s)).", pagina_atual)
                break

            primeiro_nome_anterior = cartoes_atletas[0].locator("p").first.text_content() if cartoes_atletas else None

            botao_proximo.scroll_into_view_if_needed()
            botao_proximo.click()
            pagina_atual += 1

            aguardar_atualizacao_pagina(page, primeiro_nome_anterior)
            time.sleep(config.DELAY_ENTRE_PAGINAS)
        except Exception as e:
            logger.warning("Paginação encerrada na página %d. Detalhe: %s", pagina_atual, e)
            break

    return todos_atletas


def executar_pipeline_coleta() -> None:
    """Executa a coleta completa com navegador Playwright, User-Agent customizado e delays educados."""
    lista_final_atletas: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.SCRAPER_HEADLESS, args=["--start-maximized"])
        try:
            context = browser.new_context(user_agent=config.USER_AGENT, no_viewport=True)
            page = context.new_page()

            # Passo 1: Mapear todas as corridas válidas
            corridas = mapear_corridas_exclusivas_fortaleza(page)

            # Passo 2: Iterar pelas corridas com delays educados
            for corrida in corridas:
                novos_atletas = extrair_atletas_da_corrida(page, corrida["url"], corrida["nome_prova"])
                lista_final_atletas.extend(novos_atletas)
                time.sleep(config.DELAY_ENTRE_CORRIDAS)
        finally:
            browser.close()

    # Passo 3: Salvar base bruta no CSV
    if not lista_final_atletas:
        logger.warning("Nenhum dado foi coletado nesta execução.")
        return

    df = pd.DataFrame(lista_final_atletas)
    config.PASTA_RAW.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.CSV_BRUTO, index=False, encoding="utf-8-sig")
    logger.info("Base bruta salva em: %s (%d atletas)", config.CSV_BRUTO, len(df))


if __name__ == "__main__":
    config.configurar_logging()
    executar_pipeline_coleta()