import time

from playwright.sync_api import sync_playwright


def testar_mapeamento_fortaleza():
    url_base = "https://www.o2corre.com.br/resultado/"
    links_corridas = []

    # Iniciamos o Playwright direto na função de teste
    with sync_playwright() as p:
        # headless=False para você ver o navegador abrindo e digitando fisicamente
        # Lança o navegador com o argumento para iniciar maximizado
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])

        # Cria a página definindo o viewport como None para que ela acompanhe o tamanho maximizado da janela
        page = browser.new_page(no_viewport=True)

        print(f"[TESTE] Acessando a página: {url_base}")
        page.goto(url_base)
        page.wait_for_timeout(3000)

        print("[TESTE] Digitando 'fortaleza' no campo de busca...")
        campo_busca = page.get_by_placeholder("Pesquisar Evento")
        campo_busca.click()
        campo_busca.fill("fortaleza")
        campo_busca.press("Enter")

        print("[TESTE] Aguardando o carregamento dos filtros...")
        page.wait_for_timeout(4000)

        print("[TESTE] Clicando no 'Ver mais' para expandir a lista...")
        while True:
            try:
                botao_ver_mais = page.get_by_text("Ver mais")
                if botao_ver_mais.is_visible():
                    botao_ver_mais.click()
                    page.wait_for_timeout(2000)
                else:
                    print("[TESTE] Todos os eventos de Fortaleza foram expandidos.")
                    break
            except Exception:
                break

        print("\n[TESTE] Extraindo e validando links capturados...")
        links_elementos = page.locator("a[href*='/resultado/']").all()

        for elemento in links_elementos:
            href = elemento.get_attribute("href")

            if href:
                # Transforma links relativos em URLs completas
                if href.startswith("/"):
                    href = f"https://www.o2corre.com.br{href}"

                # Valida se o link termina com o ID numérico da corrida
                partes_url = href.strip("/").split("/")
                if partes_url[-1].isdigit():
                    if href not in links_corridas:
                        links_corridas.append(href)
                        texto = elemento.text_content().strip() if elemento.text_content() else "Corrida"
                        print(f" -> Encontrada: {texto} | URL: {href}")

        print(f"\n[FIM DO TESTE] Total de corridas mapeadas com sucesso: {len(links_corridas)}")

        time.sleep(3)
        browser.close()


if __name__ == "__main__":
    testar_mapeamento_fortaleza()