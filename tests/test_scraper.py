from unittest.mock import MagicMock

import pytest

from src.scraper import (
    extrair_dados_cartao,
    navegar_com_retry,
    verificar_botao_proximo_habilitado,
    verificar_conformidade_robots_txt,
)


def test_extrair_dados_cartao_valido():
    paragrafos = ["  João Silva  ", "  00:25:30 ", "  N° 100 - 5K  "]
    resultado = extrair_dados_cartao(paragrafos, "https://exemplo.com/1", "Corrida Teste")

    assert resultado is not None
    assert resultado["nome_atleta"] == "João Silva"
    assert resultado["tempo_bruto"] == "00:25:30"
    assert resultado["detalhes_atleta"] == "N° 100 - 5K"
    assert resultado["url_corrida"] == "https://exemplo.com/1"
    assert resultado["nome_prova"] == "Corrida Teste"


def test_extrair_dados_cartao_incompleto_retorna_none():
    assert extrair_dados_cartao(["João", "00:25:30"], "https://exemplo.com", "Prova") is None
    assert extrair_dados_cartao([], "https://exemplo.com", "Prova") is None


def test_verificar_conformidade_robots_txt():
    assert verificar_conformidade_robots_txt() is True


def test_verificar_botao_proximo_habilitado():
    botao = MagicMock()
    botao.is_visible.return_value = True
    botao.is_enabled.return_value = True
    botao.get_attribute.return_value = None

    assert verificar_botao_proximo_habilitado(botao) is True


def test_verificar_botao_proximo_invisivel_ou_desabilitado():
    botao_invisivel = MagicMock()
    botao_invisivel.is_visible.return_value = False
    assert verificar_botao_proximo_habilitado(botao_invisivel) is False

    botao_desabilitado = MagicMock()
    botao_desabilitado.is_visible.return_value = True
    botao_desabilitado.is_enabled.return_value = False
    assert verificar_botao_proximo_habilitado(botao_desabilitado) is False


def test_verificar_botao_proximo_com_atributos_disabled():
    # Atributo disabled presente
    botao_attr = MagicMock()
    botao_attr.is_visible.return_value = True
    botao_attr.is_enabled.return_value = True
    botao_attr.get_attribute.side_effect = lambda attr: "" if attr == "disabled" else None
    assert verificar_botao_proximo_habilitado(botao_attr) is False

    # aria-disabled = true
    botao_aria = MagicMock()
    botao_aria.is_visible.return_value = True
    botao_aria.is_enabled.return_value = True
    botao_aria.get_attribute.side_effect = lambda attr: "true" if attr == "aria-disabled" else None
    assert verificar_botao_proximo_habilitado(botao_aria) is False

    # classe contendo disabled
    botao_classe = MagicMock()
    botao_classe.is_visible.return_value = True
    botao_classe.is_enabled.return_value = True
    botao_classe.get_attribute.side_effect = lambda attr: "btn disabled-state" if attr == "class" else None
    assert verificar_botao_proximo_habilitado(botao_classe) is False


def test_navegar_com_retry_sucesso_apos_falha_transiente():
    page = MagicMock()
    # Falha na primeira chamada, tem sucesso na segunda
    page.goto.side_effect = [RuntimeError("Oscilação de rede"), None]

    navegar_com_retry(page, "https://exemplo.com/resultado")
    assert page.goto.call_count == 2


def test_navegar_com_retry_esgota_tentativas():
    page = MagicMock()
    page.goto.side_effect = RuntimeError("Falha persistente")

    with pytest.raises(RuntimeError):
        navegar_com_retry(page, "https://exemplo.com/resultado")

    assert page.goto.call_count >= 3
