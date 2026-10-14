import logging
import time

import pandas as pd
from playwright.sync_api import sync_playwright

from src import config

logger = logging.getLogger(__name__)


def mapear_corridas_exclusivas_fortaleza(page) -> list[dict]:
    """Pesquisa o termo configurado, expande o histórico e retorna as corridas válidas (nome + URL)."""
    links_corridas: list[dict] = []
    urls_vistas: set[str] = set()

    logger.info("Acessando a página inicial de resultados: %s", config.URL_BASE_RESULTADOS)
    page.goto(config.URL_BASE_RESULTADOS)
    page.wait_for_timeout(3000)

    logger.info("Localizando o campo de busca...")
    campo_busca = page.get_by_placeholder("Pesquisar Evento")
    campo_busca.click()
    campo_busca.fill(config.TERMO_BUSCA)
    campo_busca.press("Enter")

    logger.info("Filtro aplicado. Aguardando os resultados carregarem...")
    page.wait_for_timeout(4000)

    logger.info("Expandindo o histórico filtrado...")
    for _ in range(config.MAX_CLIQUES_VER_MAIS):
        try:
            botao_ver_mais = page.get_by_text("Ver mais")
            if not botao_ver_mais.is_visible():
                break
            botao_ver_mais.click()
            page.wait_for_timeout(2000)
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
    Entra na página de uma corrida específica com tratamento de instabilidade de rede (Retry)
    e extrai os dados de TODOS os atletas.
    """
    logger.info("Iniciando extração da corrida: %s (%s)", nome_prova, url_corrida)

    # Lógica de Re-tentativa (Retry) para proteger contra quedas de Wi-Fi / ERR_NETWORK_CHANGED
    sucesso_carregamento = False
    for tentativa in range(1, config.MAX_TENTATIVAS_REDE + 1):
        try:
            page.goto(url_corrida, timeout=30000)
            sucesso_carregamento = True
            break
        except Exception as e:
            logger.warning("Oscilação de rede (tentativa %d/%d): %s", tentativa, config.MAX_TENTATIVAS_REDE, e)
            time.sleep(3)

    if not sucesso_carregamento:
        logger.error("Não foi possível carregar a URL após %d tentativas. Pulando prova: %s",
                     config.MAX_TENTATIVAS_REDE, nome_prova)
        return []

    # Aguarda a tabela de atletas ser renderizada na tela
    try:
        page.wait_for_selector(".css-wo7zn5", timeout=10000)
    except Exception:
        logger.warning("Tabela de atletas não carregou nesta URL ou prova sem resultados registrados.")
        return []

    todos_atletas: list[dict] = []
    pagina_atual = 1

    while pagina_atual <= limite_paginas:
        logger.info("Coletando dados da página %d...", pagina_atual)
        page.wait_for_timeout(1500)  # Pausa de estabilização do DOM

        cartoes_atletas = page.locator(".css-wo7zn5").all()

        if not cartoes_atletas:
            logger.info("Nenhum atleta encontrado nesta página. Encerrando esta corrida.")
            break

        for cartao in cartoes_atletas:
            try:
                paragrafos = cartao.locator("p").all_text_contents()

                if len(paragrafos) >= 3:
                    todos_atletas.append({
                        "url_corrida": url_corrida,
                        "nome_prova": nome_prova,
                        "nome_atleta": paragrafos[0].strip(),
                        "tempo_bruto": paragrafos[1].strip(),
                        "detalhes_atleta": paragrafos[2].strip()
                    })
            except Exception as e:
                logger.debug("Cartão de atleta ignorado: %s", e)
                continue

        # Lógica de Paginação Precisão Chakra UI
        try:
            botao_proximo = page.locator("button:has(img[alt='Próximo'])")

            if botao_proximo.is_visible():
                attr_disabled = botao_proximo.get_attribute("disabled")
                class_disabled = "disabled" in (botao_proximo.get_attribute("class") or "")
                is_disabled = attr_disabled is not None or class_disabled

                if not is_disabled:
                    botao_proximo.scroll_into_view_if_needed()
                    page.wait_for_timeout(500)

                    botao_proximo.click()
                    pagina_atual += 1
                    page.wait_for_timeout(2500)  # Aguarda renderização da nova página
                else:
                    logger.info("Última página da prova (%d página(s) extraída(s)).", pagina_atual)
                    break
            else:
                logger.info("Botão 'Próximo' não visível. Fim dos resultados na página %d.", pagina_atual)
                break

        except Exception as e:
            logger.warning("Paginação encerrada na página %d. Detalhe: %s", pagina_atual, e)
            break

    return todos_atletas


def executar_pipeline_coleta() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.SCRAPER_HEADLESS, args=["--start-maximized"])
        try:
            page = browser.new_page(no_viewport=True)

            # Passo 1: Mapear todas as corridas válidas
            corridas = mapear_corridas_exclusivas_fortaleza(page)

            # Passo 2: Iterar por todas as corridas e capturar todas as páginas de cada uma
            lista_final_atletas: list[dict] = []
            for corrida in corridas:
                lista_final_atletas.extend(
                    extrair_atletas_da_corrida(page, corrida["url"], corrida["nome_prova"])
                )
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