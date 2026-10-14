import time

from playwright.sync_api import sync_playwright


def rodar_demonstracao_linkedin():
    url_corrida = "https://www.o2corre.com.br/resultado/39884"

    print("🚀 Preparando o ambiente de demonstração para o LinkedIn...")

    with sync_playwright() as p:
        # Abre o navegador Chromium de forma visível
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        page = browser.new_page(no_viewport=True)

        # Acessa a página da corrida
        page.goto(url_corrida)

        # Injeta uma mensagem visual na tela para te ajudar na gravação
        page.evaluate("""() => {
            const alerta = document.createElement('div');
            alerta.style.position = 'fixed';
            alerta.style.top = '20px';
            alerta.style.left = '50%';
            alerta.style.transform = 'translateX(-50%)';
            alerta.style.backgroundColor = '#FF4500';
            alerta.style.color = 'white';
            alerta.style.padding = '15px 30px';
            alerta.style.fontSize = '18px';
            alerta.style.fontWeight = 'bold';
            alerta.style.zIndex = '99999';
            alerta.style.borderRadius = '8px';
            alerta.style.boxShadow = '0px 4px 15px rgba(0,0,0,0.3)';
            alerta.innerText = '⚠️ AGUARDANDO POSICIONAMENTO DA TELA...';
            document.body.appendChild(alerta);
            window.alertaLinkedin = alerta;
        }""")

        # Mensagem no terminal do PyCharm com instruções claras
        print("\n" + "=" * 60)
        print(" 🖥️  ORGANIZAÇÃO DA TELA ATIVADA!")
        print("=" * 60)
        print("    e pressione ENTER para começar o show!")
        print("=" * 60)

        # O script fica travado aqui esperando você interagir no terminal do PyCharm
        input("\nPressione [ENTER] para iniciar a demonstração no vídeo...")

        # Remove a mensagem de alerta da tela do navegador antes de começar
        page.evaluate("() => { window.alertaLinkedin.remove(); }")

        # ETAPA 1: Entrando na prova
        print("\n[ETAPA 1] Iniciando interação com a página da prova...")
        time.sleep(1.5)

        # ETAPA 2: Abrindo resultados (e aguardando o carregamento da tabela)
        print("\n[ETAPA 2] Analisando a tabela de atletas na tela...")
        page.wait_for_selector(".css-wo7zn5")
        time.sleep(2)

        # ETAPA 3: Capturando atletas (com efeito visual para o vídeo!)
        print("\n[ETAPA 3] Capturando dados dos atletas...")
        cartoes_atletas = page.locator(".css-wo7zn5").all()

        # Destaca visualmente os 3 primeiros atletas na tela para o vídeo
        for i, cartao in enumerate(cartoes_atletas[:3]):
            try:
                # Efeito visual: Aplica uma borda vermelha e fundo destacado no atleta que está sendo lido
                cartao.evaluate(
                    "el => { el.style.border = '3px solid #FF4500'; el.style.backgroundColor = '#FFF8DC'; }")

                paragrafos = cartao.locator("p").all_text_contents()
                if len(paragrafos) >= 3:
                    nome = paragrafos[0].strip()
                    tempo = paragrafos[1].strip()
                    detalhes = paragrafos[2].strip()
                    print(f"   ✨ Atleta {i + 1} coletado: {nome} | Tempo: {tempo} | {detalhes}")

                time.sleep(2.0)  # Pausa confortável para visualização no vídeo

                # Remove o destaque para o vídeo continuar limpo
                cartao.evaluate("el => { el.style.border = 'none'; el.style.backgroundColor = 'transparent'; }")
            except Exception:
                continue

        time.sleep(1.5)

        # ETAPA 4: Mudando de página
        print("\n[ETAPA 4] Localizando o botão 'Próximo' para mudar de página...")
        botao_proximo = page.get_by_text("Próximo")

        if botao_proximo.is_visible() and botao_proximo.is_enabled():
            # Move o mouse visualmente até o botão para dar realismo ao vídeo
            botao_proximo.hover()
            time.sleep(1.5)

            print("   👉 Clicando no botão 'Próximo'...")
            botao_proximo.click()

            # Aguarda a nova página carregar
            print("   ⏳ Nova página carregada com sucesso!")
            time.sleep(4)  # Pausa final de celebração para o vídeo
        else:
            print("   ⚠️ Botão próximo não disponível.")

        print("\n🎬 Demonstração finalizada com sucesso! O robô executou todas as etapas.")
        browser.close()


if __name__ == "__main__":
    rodar_demonstracao_linkedin()