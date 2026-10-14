import os
import time
import pandas as pd
from playwright.sync_api import sync_playwright


def mapear_corridas_exclusivas_fortaleza(page):
    url_base = "https://www.o2corre.com.br/resultado/"
    links_corridas = []

    print(f"Acessando a página inicial de resultados: {url_base}")
    page.goto(url_base)
    page.wait_for_timeout(3000)

    print("Localizando o campo de busca...")
    campo_busca = page.get_by_placeholder("Pesquisar Evento")
    campo_busca.click()
    campo_busca.fill("fortaleza")
    campo_busca.press("Enter")

    print("Filtro aplicado. Aguardando os resultados de Fortaleza carregarem...")
    page.wait_for_timeout(4000)

    print("Expandindo o histórico filtrado...")
    while True:
        try:
            botao_ver_mais = page.get_by_text("Ver mais")
            if botao_ver_mais.is_visible():
                botao_ver_mais.click()
                page.wait_for_timeout(2000)
            else:
                break
        except Exception:
            break

    print("\nMapeando os links das corridas de Fortaleza...")
    links_elementos = page.locator("a[href*='/resultado/']").all()

    for elemento in links_elementos:
        href = elemento.get_attribute("href")

        if href:
            if href.startswith("/"):
                href = f"https://www.o2corre.com.br{href}"

            partes_url = href.strip("/").split("/")
            if partes_url[-1].isdigit():
                if href not in [c['url'] for c in links_corridas]:
                    texto_prova = elemento.text_content().strip() if elemento.text_content() else "Corrida Não Identificada"

                    links_corridas.append({
                        "url": href,
                        "nome_prova": texto_prova
                    })
                    print(f"Corrida Válida Mapeada: {texto_prova}")
                    print(f"URL Completa: {href}")
                    print("-" * 50)

    print(f"Sucesso! Total de corridas de Fortaleza encontradas de forma válida: {len(links_corridas)}")
    return links_corridas


def extrair_atletas_da_corrida(page, url_corrida, nome_prova, limite_paginas=999):
    """
    Entra na página de uma corrida específica com tratamento de instabilidade de rede (Retry)
    e extrai os dados de TODOS os atletas.
    """
    print(f"\nIniciando extração da corrida: {nome_prova}")
    print(f"URL: {url_corrida}")

    # Lógica de Re-tentativa (Retry) para proteger contra quedas de Wi-Fi / ERR_NETWORK_CHANGED
    sucesso_carregamento = False
    for tentativa in range(1, 4):
        try:
            page.goto(url_corrida, timeout=30000)
            sucesso_carregamento = True
            break
        except Exception as e:
            print(f"⚠️ Oscilação de rede detectada (tentativa {tentativa}/3). Aguardando para tentar novamente...")
            time.sleep(3)

    if not sucesso_carregamento:
        print(f"❌ Não foi possível carregar a URL após 3 tentativas. Pulando prova: {nome_prova}")
        return []

    # Aguarda a tabela de atletas ser renderizada na tela
    try:
        page.wait_for_selector(".css-wo7zn5", timeout=10000)
    except Exception:
        print("Aviso: Tabela de atletas não carregou nesta URL ou prova sem resultados registrados.")
        return []

    todos_atletas = []
    pagina_atual = 1

    while pagina_atual <= limite_paginas:
        print(f"Coletando dados da página {pagina_atual}...")
        page.wait_for_timeout(1500)  # Pausa de estabilização do DOM

        cartoes_atletas = page.locator(".css-wo7zn5").all()

        if not cartoes_atletas:
            print("Nenhum atleta encontrado nesta página. Encerrando esta corrida.")
            break

        for cartao in cartoes_atletas:
            try:
                paragrafos = cartao.locator("p").all_text_contents()

                if len(paragrafos) >= 3:
                    nome = paragrafos[0].strip()
                    tempo = paragrafos[1].strip()
                    detalhes = paragrafos[2].strip()

                    todos_atletas.append({
                        "url_corrida": url_corrida,
                        "nome_prova": nome_prova,
                        "nome_atleta": nome,
                        "tempo_bruto": tempo,
                        "detalhes_atleta": detalhes
                    })
            except Exception:
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
                    print(f"Chegou na última página da prova ({pagina_atual} página(s) extraída(s)).")
                    break
            else:
                print(f"Botão 'Próximo' não visível. Fim dos resultados na página {pagina_atual}.")
                break

        except Exception as e:
            print(f"Encerrada a paginação na página {pagina_atual}. Detalhe: {e}")
            break

    return todos_atletas


def executar_pipeline_coleta():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        page = browser.new_page(no_viewport=True)

        # Passo 1: Mapear todas as corridas válidas em Fortaleza
        urls_fortaleza = mapear_corridas_exclusivas_fortaleza(page)

        lista_final_atletas = []

        # Passo 2: Iterar por todas as corridas e capturar todas as páginas de cada uma
        for corrida in urls_fortaleza:
            url = corrida["url"]
            nome_prova = corrida["nome_prova"]

            dados_corrida = extrair_atletas_da_corrida(page, url, nome_prova)
            lista_final_atletas.extend(dados_corrida)

        print("\nFinalizando a coleta completa. Gravando dados em disco...")

        # Passo 3: Salvar base bruta no CSV
        if lista_final_atletas:
            df = pd.DataFrame(lista_final_atletas)

            pasta_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            pasta_destino = os.path.join(pasta_raiz, "data", "raw")
            os.makedirs(pasta_destino, exist_ok=True)

            caminho_salvamento = os.path.join(pasta_destino, "corridas_fortaleza_bruto.csv")

            df.to_csv(caminho_salvamento, index=False, encoding="utf-8-sig")
            print(f"\n[SUCESSO COMPLETO] A base total de dados foi salva em: {caminho_salvamento}")
            print(f"Total absoluto de atletas coletados: {len(df)}")
        else:
            print("\n[AVISO] Nenhum dado foi coletado nesta execução.")

        time.sleep(2)
        browser.close()


if __name__ == "__main__":
    executar_pipeline_coleta()