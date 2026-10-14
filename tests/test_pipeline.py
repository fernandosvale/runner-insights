import pandas as pd
import pytest

from src.pipeline import (
    anonimizar_nome,
    converter_tempo_para_minutos,
    extrair_distancia_numerica,
    gerar_id_atleta,
    inferir_sexo_pelo_nome,
    tratar_dados_atletas,
)
from src.utils import formatar_minutos_para_pace


class TestConverterTempo:
    def test_hhmmss(self):
        assert converter_tempo_para_minutos("00:16:00") == pytest.approx(16.0)

    def test_acima_de_uma_hora(self):
        assert converter_tempo_para_minutos("01:02:30") == pytest.approx(62.5)

    def test_mmss(self):
        assert converter_tempo_para_minutos("45:30") == pytest.approx(45.5)

    @pytest.mark.parametrize("entrada", [None, float("nan"), "", "abc", "1:2:3:4", 123])
    def test_entradas_invalidas(self, entrada):
        assert converter_tempo_para_minutos(entrada) is None


class TestExtrairDistancia:
    @pytest.mark.parametrize("entrada,esperado", [("5K", 5.0), ("21K", 21.0), ("5.5K", 5.5)])
    def test_valores_validos(self, entrada, esperado):
        assert extrair_distancia_numerica(entrada) == esperado

    @pytest.mark.parametrize("entrada", [None, "", "KM", 10])
    def test_entradas_invalidas(self, entrada):
        assert extrair_distancia_numerica(entrada) is None


class TestFormatarPace:
    def test_basico(self):
        assert formatar_minutos_para_pace(3.5) == "03:30"

    def test_arredondamento_60_segundos(self):
        assert formatar_minutos_para_pace(3.9999) == "04:00"

    @pytest.mark.parametrize("entrada", [None, float("nan"), 0, -1])
    def test_invalidos(self, entrada):
        assert formatar_minutos_para_pace(entrada) is None


class TestInferirSexo:
    @pytest.mark.parametrize("nome,esperado", [
        ("Maria Silva", "F"),
        ("Carlos Souza", "M"),
        ("Isabel Lima", "F"),
        ("Lucas Pereira", "M"),
        ("Joshua Alves", "M"),
        ("Alexandre Costa", "M"),
    ])
    def test_classificacao(self, nome, esperado):
        assert inferir_sexo_pelo_nome(nome) == esperado

    @pytest.mark.parametrize("nome", ["Cleudinei Santos", "Kennedy Rocha", None, "", "   "])
    def test_ambiguos_ou_invalidos(self, nome):
        assert inferir_sexo_pelo_nome(nome) == "N/I"


class TestAnonimizacao:
    def test_nome_reduzido(self):
        assert anonimizar_nome("JOÃO CARLOS DA SILVA") == "João S."

    def test_nome_unico(self):
        assert anonimizar_nome("Madonna") == "Madonna"

    def test_invalido(self):
        assert anonimizar_nome(None) == "Anônimo"

    def test_id_estavel_e_sem_nome(self):
        id_1 = gerar_id_atleta("Maria Silva", "url")
        assert id_1 == gerar_id_atleta("Maria Silva", "url")
        assert "maria" not in id_1.lower()


class TestPipelineCompleto:
    @pytest.fixture
    def df_bruto(self):
        return pd.DataFrame({
            "url_corrida": ["u1", "u1", "u1"],
            "nome_prova": [" Corrida A ", " Corrida A ", " Corrida A "],
            "nome_atleta": ["Maria Silva", "Maria Silva", "Carlos Souza"],
            "tempo_bruto": ["00:25:00", "00:25:00", "00:20:00"],
            "detalhes_atleta": ["N° 10 - 5K", "N° 10 - 5K", "N° 11 - 5K"],
        })

    def test_dedup_pace_e_anonimizacao(self, df_bruto):
        df = tratar_dados_atletas(df_bruto)

        assert len(df) == 2  # duplicata removida
        assert set(df["pace_min_km"]) == {"05:00", "04:00"}
        assert "Maria Silva" not in df["nome_atleta"].values
        assert "detalhes_atleta" not in df.columns
        assert df["nome_prova"].tolist() == ["Corrida A", "Corrida A"]
