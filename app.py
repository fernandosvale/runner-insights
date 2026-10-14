import os

import pandas as pd
import plotly.express as px  # Biblioteca para gráficos interativos
import streamlit as st

from src.utils import formatar_minutos_para_pace

# Configuração inicial da página do Streamlit
st.set_page_config(
    page_title="RunnerInsights - Performance de Corrida",
    page_icon="🏃‍♂️",
    layout="wide"
)


@st.cache_data
def carregar_dados_tratados():
    """Carrega os dados limpos do arquivo CSV processado (com cache entre interações)."""
    pasta_raiz = os.path.dirname(os.path.abspath(__file__))
    caminho_csv = os.path.join(pasta_raiz, "data", "processed", "corridas_fortaleza_limpo.csv")

    if not os.path.exists(caminho_csv):
        return None

    return pd.read_csv(caminho_csv)


# 1. Carregamento dos dados
df = carregar_dados_tratados()

if df is None:
    st.error("⚠️ Arquivo de dados tratados não encontrado! Rode `python -m src.pipeline` primeiro.")
else:
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🎯 Filtros de Pesquisa")

    # Filtro 1: Corrida/Prova
    lista_provas = sorted(df['nome_prova'].dropna().unique())
    prova_selecionada = st.sidebar.selectbox("Selecione a Corrida:", ["Todas"] + lista_provas)

    # Filtro 2: Distância
    lista_distancias = sorted(df['distancia_prova'].dropna().unique())
    distancia_selecionada = st.sidebar.selectbox("Selecione a Distância:", ["Todas"] + lista_distancias)

    # Filtro 3: Sexo/Categoria (estimado pelo primeiro nome)
    opcoes_sexo = {
        "Todos": "Todos",
        "Masculino": "M",
        "Feminino": "F",
        "Não identificado": "N/I"
    }
    sexo_rotulo_selecionado = st.sidebar.selectbox("Selecione a Categoria:", list(opcoes_sexo.keys()))
    sexo_codigo_selecionado = opcoes_sexo[sexo_rotulo_selecionado]
    st.sidebar.caption("ℹ️ O sexo é uma **estimativa** feita pelo primeiro nome, não um dado oficial.")

    # Aplicando os filtros encadeados no DataFrame
    df_filtrado = df.copy()

    if prova_selecionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado['nome_prova'] == prova_selecionada]

    if distancia_selecionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado['distancia_prova'] == distancia_selecionada]

    if sexo_codigo_selecionado != "Todos" and 'sexo' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['sexo'] == sexo_codigo_selecionado]

    # --- CORPO PRINCIPAL DO DASHBOARD ---
    st.title("🏃‍♂️ RunnerInsights")
    st.subheader("Análise de Performance de Corridas de Rua em Fortaleza")
    st.markdown("---")

    # VERIFICAÇÃO SE EXISTEM DADOS COM OS FILTROS SELECIONADOS
    if not df_filtrado.empty:
        # Aviso: comparar pace entre distâncias diferentes distorce a análise
        if df_filtrado['distancia_prova'].nunique() > 1:
            st.info("Os resultados misturam distâncias diferentes. Selecione uma distância para uma comparação de pace justa.")

        # 2. Cartões de Métricas (KPIs)
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(label="Atletas Coletados", value=f"{len(df_filtrado)}")

        with col2:
            # Compara o tempo numérico (minutos), não a string, para evitar erro de ordenação
            tempos_validos = df_filtrado['tempo_total_minutos'].dropna()
            if not tempos_validos.empty:
                linha_campeao = df_filtrado.loc[tempos_validos.idxmin()]
                st.metric(
                    label="Melhor Tempo",
                    value=str(linha_campeao['tempo_bruto']),
                    help=f"Conquistado por: {linha_campeao['nome_atleta']}"
                )
            else:
                st.metric(label="Melhor Tempo", value="--:--")

        with col3:
            if 'pace_decimal' in df_filtrado.columns and df_filtrado['pace_decimal'].notna().any():
                pace_medio_decimal = df_filtrado['pace_decimal'].mean()
                pace_medio_formatado = formatar_minutos_para_pace(pace_medio_decimal) or "--:--"
                st.metric(label="Pace Médio do Grupo", value=f"{pace_medio_formatado} min/km")
            else:
                st.metric(label="Pace Médio do Grupo", value="--:--")

        st.markdown("---")

        # 3. SEÇÃO DE GRÁFICOS VISUAIS INTERATIVOS
        st.write("### 📊 Análises Visuais de Performance")
        col_grafico1, col_grafico2 = st.columns(2)

        # Gráfico 1: Proporção por Categoria (Sexo estimado)
        with col_grafico1:
            if 'sexo' in df_filtrado.columns and len(df_filtrado['sexo'].dropna()) > 0:
                nomes_sexo = {'M': 'Masculino', 'F': 'Feminino', 'N/I': 'Não identificado'}
                df_grafico_sexo = df_filtrado['sexo'].map(nomes_sexo).value_counts().reset_index()
                df_grafico_sexo.columns = ['Categoria', 'Quantidade']

                fig_sexo = px.pie(
                    df_grafico_sexo,
                    names='Categoria',
                    values='Quantidade',
                    title="Participação por Categoria (estimada)",
                    hole=0.4,
                    color='Categoria',
                    color_discrete_map={
                        'Masculino': '#1f77b4',
                        'Feminino': '#e377c2',
                        'Não identificado': '#9e9e9e'
                    }
                )
                st.plotly_chart(fig_sexo, use_container_width=True)

        # Gráfico 2: Distribuição do Pace
        with col_grafico2:
            if 'pace_decimal' in df_filtrado.columns and df_filtrado['pace_decimal'].notna().any():
                fig_pace = px.histogram(
                    df_filtrado,
                    x='pace_decimal',
                    nbins=15,
                    title="Distribuição do Pace (min/km)",
                    labels={'pace_decimal': 'Pace Decimal (minutos/km)'},
                    color_discrete_sequence=['#2ca02c']
                )
                fig_pace.update_layout(yaxis_title="Quantidade de Atletas")
                st.plotly_chart(fig_pace, use_container_width=True)

        st.markdown("---")

        # 4. Tabela de Dados Filtrada
        st.write("### 📋 Resultados Detalhados")

        colunas_exibicao = ['nome_prova', 'nome_atleta', 'sexo', 'tempo_bruto', 'numero_peito', 'distancia_prova', 'pace_min_km']
        colunas_presentes = [col for col in colunas_exibicao if col in df_filtrado.columns]

        st.dataframe(df_filtrado[colunas_presentes], use_container_width=True)

    else:
        # TRATAMENTO DE RETORNO VAZIO AMIGÁVEL
        st.warning("⚠️ **Nenhum registro encontrado para os filtros selecionados.**")
        st.info("Tente alterar os filtros na barra lateral (por exemplo, selecionar 'Todas' as distâncias ou categorias) para visualizar os dados.")