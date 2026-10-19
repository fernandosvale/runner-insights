import os

import pandas as pd
import plotly.express as px  # Biblioteca para gráficos interativos
import streamlit as st

from src.utils import calcular_metricas_estatisticas, formatar_minutos_para_pace
from styles import aplicar_tema
from styles.design_tokens import COLORS
from styles.plotly_theme import COR_MEDIA, COR_MEDIANA, CORES_CATEGORIA, registrar_tema_plotly

# Configuração inicial da página do Streamlit
st.set_page_config(
    page_title="RunnerInsights - Performance de Corrida",
    page_icon=":material/directions_run:",
    layout="wide"
)

# Identidade visual (DESIGN_SYSTEM.md): tema global + template Plotly
aplicar_tema()
registrar_tema_plotly()


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
    st.error("Arquivo de dados tratados não encontrado! Rode `python -m src.pipeline` primeiro.", icon=":material/error:")
else:
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros de Pesquisa")

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
    st.sidebar.caption("O sexo é uma **estimativa** feita pelo primeiro nome, não um dado oficial.")

    # Aplicando os filtros encadeados no DataFrame
    df_filtrado = df.copy()

    if prova_selecionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado['nome_prova'] == prova_selecionada]

    if distancia_selecionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado['distancia_prova'] == distancia_selecionada]

    if sexo_codigo_selecionado != "Todos" and 'sexo' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['sexo'] == sexo_codigo_selecionado]

    # --- CORPO PRINCIPAL DO DASHBOARD ---
    st.title("RunnerInsights")
    st.subheader("Análise de Performance de Corridas de Rua em Fortaleza")
    st.markdown("---")

    # VERIFICAÇÃO SE EXISTEM DADOS COM OS FILTROS SELECIONADOS
    if not df_filtrado.empty:
        # Aviso: comparar pace entre distâncias diferentes distorce a análise
        if df_filtrado['distancia_prova'].nunique() > 1:
            st.info("Os resultados misturam distâncias diferentes. Selecione uma distância para uma comparação de pace justa.")

        # 2. Cartões de Métricas (KPIs) com Média, Mediana e Extremos
        tempos_validos = df_filtrado['tempo_total_minutos'].dropna()
        paces_validos = df_filtrado['pace_decimal'].dropna() if 'pace_decimal' in df_filtrado.columns else pd.Series(dtype=float)
        stats_pace = calcular_metricas_estatisticas(paces_validos)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(label="Atletas Coletados", value=f"{len(df_filtrado)}")

        with col2:
            if not tempos_validos.empty:
                linha_campeao = df_filtrado.loc[tempos_validos.idxmin()]
                st.metric(
                    label="Melhor Tempo",
                    value=str(linha_campeao['tempo_bruto']),
                    help=f"Conquistado por: {linha_campeao['nome_atleta']} ({linha_campeao.get('distancia_prova', '')})",
                )
            else:
                st.metric(label="Melhor Tempo", value="--:--")

        with col3:
            if stats_pace:
                pace_mediano_formatado = formatar_minutos_para_pace(stats_pace["mediana"]) or "--:--"
                st.metric(
                    label="Pace Mediano (P50)",
                    value=f"{pace_mediano_formatado} min/km",
                    help="Ritmo central do grupo: metade dos atletas correu acima e metade abaixo deste pace.",
                )
            else:
                st.metric(label="Pace Mediano (P50)", value="--:--")

        with col4:
            if stats_pace:
                pace_medio_formatado = formatar_minutos_para_pace(stats_pace["media"]) or "--:--"
                st.metric(
                    label="Pace Médio do Grupo",
                    value=f"{pace_medio_formatado} min/km",
                    help=f"Média geral (desvio padrão: ± {stats_pace['desvio_padrao']:.2f} min/km).",
                )
            else:
                st.metric(label="Pace Médio do Grupo", value="--:--")

        # Seção Expansível com Percentis Estatísticos
        if stats_pace:
            with st.expander("Estatísticas Detalhadas de Performance (Percentis P10 a P90)", expanded=False, icon=":material/query_stats:"):
                col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
                col_p1.metric(
                    "Top 10% (P10)",
                    f"{formatar_minutos_para_pace(stats_pace['p10'])} min/km",
                    help="Ritmo do pelotão de elite",
                )
                col_p2.metric(
                    "Top 25% (P25)",
                    f"{formatar_minutos_para_pace(stats_pace['p25'])} min/km",
                    help="1º Quartil (top 25% mais rápidos)",
                )
                col_p3.metric(
                    "Mediana (P50)",
                    f"{formatar_minutos_para_pace(stats_pace['mediana'])} min/km",
                    help="Pelotão intermediário central",
                )
                col_p4.metric(
                    "Pelotão 75% (P75)",
                    f"{formatar_minutos_para_pace(stats_pace['p75'])} min/km",
                    help="3º Quartil",
                )
                col_p5.metric(
                    "Pelotão 90% (P90)",
                    f"{formatar_minutos_para_pace(stats_pace['p90'])} min/km",
                    help="Faixa de conclusão confortável",
                )

        st.markdown("---")

        # 3. SEÇÃO DE GRÁFICOS VISUAIS INTERATIVOS
        st.write("### Análises Visuais de Performance")

        df_graficos = df_filtrado.copy()
        if 'sexo' in df_graficos.columns:
            nomes_sexo = {'M': 'Masculino', 'F': 'Feminino', 'N/I': 'Não identificado'}
            df_graficos['Categoria'] = df_graficos['sexo'].map(nomes_sexo).fillna('Não identificado')

        col_grafico1, col_grafico2 = st.columns(2)

        # Gráfico 1: Proporção por Categoria (Sexo estimado)
        with col_grafico1:
            if 'Categoria' in df_graficos.columns and len(df_graficos['Categoria'].dropna()) > 0:
                df_grafico_sexo = df_graficos['Categoria'].value_counts().reset_index()
                df_grafico_sexo.columns = ['Categoria', 'Quantidade']

                fig_sexo = px.pie(
                    df_grafico_sexo,
                    names='Categoria',
                    values='Quantidade',
                    title="Participação por Categoria (estimada)",
                    hole=0.4,
                    color='Categoria',
                    color_discrete_map=CORES_CATEGORIA,
                )
                st.plotly_chart(fig_sexo, use_container_width=True)

        # Gráfico 2: Distribuição do Pace com marcas de Média e Mediana
        with col_grafico2:
            if stats_pace:
                fig_pace = px.histogram(
                    df_filtrado,
                    x='pace_decimal',
                    nbins=15,
                    title="Distribuição de Frequência do Pace (min/km)",
                    labels={'pace_decimal': 'Pace Decimal (minutos/km)'},
                    color_discrete_sequence=[COLORS["accent-primary"]],
                )
                fig_pace.add_vline(
                    x=stats_pace["mediana"],
                    line_dash="dash",
                    line_color=COR_MEDIANA,
                    annotation_text=f"Mediana: {formatar_minutos_para_pace(stats_pace['mediana'])}",
                )
                fig_pace.add_vline(
                    x=stats_pace["media"],
                    line_dash="dot",
                    line_color=COR_MEDIA,
                    annotation_text=f"Média: {formatar_minutos_para_pace(stats_pace['media'])}",
                )
                fig_pace.update_layout(yaxis_title="Quantidade de Atletas")
                st.plotly_chart(fig_pace, use_container_width=True)

        # Linha 2 de Gráficos: Boxplot de Pace por Categoria e Comparativo de Provas
        col_grafico3, col_grafico4 = st.columns(2)

        with col_grafico3:
            if 'Categoria' in df_graficos.columns and stats_pace:
                fig_box_sexo = px.box(
                    df_graficos,
                    x='Categoria',
                    y='pace_decimal',
                    color='Categoria',
                    points="outliers",
                    title="Dispersão do Pace por Categoria (min/km)",
                    labels={'pace_decimal': 'Pace (min/km)', 'Categoria': 'Categoria Estimada'},
                    color_discrete_map=CORES_CATEGORIA,
                )
                fig_box_sexo.update_layout(showlegend=False)
                st.plotly_chart(fig_box_sexo, use_container_width=True)

        with col_grafico4:
            if stats_pace:
                if df_filtrado['nome_prova'].nunique() > 1:
                    fig_box_prova = px.box(
                        df_filtrado,
                        x='nome_prova',
                        y='pace_decimal',
                        color='nome_prova',
                        title="Comparativo de Ritmo (Pace) entre Provas",
                        labels={'pace_decimal': 'Pace (min/km)', 'nome_prova': 'Prova'},
                    )
                    fig_box_prova.update_layout(showlegend=False, xaxis_tickangle=-30)
                    st.plotly_chart(fig_box_prova, use_container_width=True)
                else:
                    # Quando uma única prova está filtrada, mostra comparação de Pace Médio e Mediano por Categoria
                    df_resumo_cat = df_graficos.groupby('Categoria')['pace_decimal'].agg(['mean', 'median']).reset_index()
                    df_resumo_cat = df_resumo_cat.melt(
                        id_vars=['Categoria'],
                        value_vars=['median', 'mean'],
                        var_name='Métrica',
                        value_name='Pace',
                    )
                    df_resumo_cat['Métrica'] = df_resumo_cat['Métrica'].map({'median': 'Mediana', 'mean': 'Média'})

                    fig_bar_cat = px.bar(
                        df_resumo_cat,
                        x='Categoria',
                        y='Pace',
                        color='Métrica',
                        barmode='group',
                        title="Pace Médio vs Mediano por Categoria",
                        labels={'Pace': 'Pace (min/km)'},
                        color_discrete_map={'Mediana': COR_MEDIANA, 'Média': COR_MEDIA},
                    )
                    st.plotly_chart(fig_bar_cat, use_container_width=True)

        st.markdown("---")

        # 4. Tabela de Dados Filtrada
        st.write("### Resultados Detalhados")

        colunas_exibicao = ['nome_prova', 'nome_atleta', 'sexo', 'tempo_bruto', 'numero_peito', 'distancia_prova', 'pace_min_km']
        colunas_presentes = [col for col in colunas_exibicao if col in df_filtrado.columns]

        st.dataframe(df_filtrado[colunas_presentes], use_container_width=True)

    else:
        # TRATAMENTO DE RETORNO VAZIO AMIGÁVEL
        st.warning("**Nenhum registro encontrado para os filtros selecionados.**", icon=":material/search_off:")
        st.info(
            "Tente alterar os filtros na barra lateral (por exemplo, selecionar 'Todas' "
            "as distâncias ou categorias) para visualizar os dados."
        )