import os

import pandas as pd
import plotly.express as px
import streamlit as st

from src.utils import calcular_metricas_estatisticas, formatar_minutos_para_pace, gerar_ticks_pace
from styles import aplicar_tema
from styles.design_tokens import COLORS
from styles.plotly_theme import COR_MEDIA, COR_MEDIANA, CORES_CATEGORIA, registrar_tema_plotly

# Configuração da página
st.set_page_config(page_title="RunnerInsights - Inteligência Esportiva", page_icon=":material/directions_run:", layout="wide")

# Identidade visual oficial
aplicar_tema()
registrar_tema_plotly()


@st.cache_data
def carregar_dados_tratados():
    """Carrega os dados limpos do arquivo CSV processado."""
    pasta_raiz = os.path.dirname(os.path.abspath(__file__))
    caminho_csv = os.path.join(pasta_raiz, "data", "processed", "corridas_fortaleza_limpo.csv")

    if not os.path.exists(caminho_csv):
        return None

    return pd.read_csv(caminho_csv)


df = carregar_dados_tratados()

if df is None:
    st.error("Arquivo de dados tratados não encontrado! Execute `python -m src.pipeline` para processar a base.", icon=":material/error:")
else:
    # ----------------------------------------------------
    # BARRA LATERAL: FILTROS E CONTEXTO
    # ----------------------------------------------------
    st.sidebar.header("Filtros de Pesquisa")

    # Filtro 1: Prova
    lista_provas = sorted(df["nome_prova"].dropna().unique())
    prova_selecionada = st.sidebar.selectbox("Selecione a Prova / Evento:", ["Todas"] + lista_provas, key="filtro_prova")

    # Filtro 2: Distância
    lista_distancias = sorted(df["distancia_prova"].dropna().unique())
    distancia_selecionada = st.sidebar.selectbox("Selecione a Distância:", ["Todas"] + lista_distancias, key="filtro_distancia")

    # Filtro 3: Categoria / Sexo estimado
    opcoes_sexo = {"Todas as categorias": "Todos", "Masculino": "M", "Feminino": "F", "Não identificado": "N/I"}
    sexo_rotulo_selecionado = st.sidebar.selectbox("Categoria (estimada):", list(opcoes_sexo.keys()), key="filtro_sexo")
    sexo_codigo_selecionado = opcoes_sexo[sexo_rotulo_selecionado]

    st.sidebar.caption("O sexo é uma **estimativa probabilística** baseada no primeiro nome do atleta, não um dado cadastral oficial.")

    # Aplicação encadeada dos filtros
    df_filtrado = df.copy()

    if prova_selecionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado["nome_prova"] == prova_selecionada]

    if distancia_selecionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado["distancia_prova"] == distancia_selecionada]

    if sexo_codigo_selecionado != "Todos" and "sexo" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["sexo"] == sexo_codigo_selecionado]

    # Resumo contextual de filtros ativos na sidebar
    filtros_ativos = []
    if prova_selecionada != "Todas":
        filtros_ativos.append(f"Prova: {prova_selecionada}")
    if distancia_selecionada != "Todas":
        filtros_ativos.append(f"Distância: {distancia_selecionada}")
    if sexo_codigo_selecionado != "Todos":
        filtros_ativos.append(f"Categoria: {sexo_rotulo_selecionado}")

    if filtros_ativos:
        st.sidebar.divider()
        st.sidebar.caption("**Filtros ativos:** " + " • ".join(filtros_ativos))
        if st.sidebar.button("Limpar todos os filtros", icon=":material/filter_alt_off:"):
            st.session_state["filtro_prova"] = "Todas"
            st.session_state["filtro_distancia"] = "Todas"
            st.session_state["filtro_sexo"] = "Todas as categorias"
            st.rerun()

    # ----------------------------------------------------
    # CABEÇALHO PRINCIPAL
    # ----------------------------------------------------
    st.title("RunnerInsights")
    st.caption("Engenharia de Dados e Inteligência Esportiva • Resultados de Corridas de Rua em Fortaleza")
    st.divider()

    if df_filtrado.empty:
        # Estado vazio amigável e explicativo
        st.warning("**Nenhum resultado encontrado para os filtros selecionados.**", icon=":material/search_off:")
        st.info(
            "Tente ajustar os filtros na barra lateral (por exemplo, selecionar 'Todas' as "
            "categorias ou distâncias) para visualizar os dados."
        )
    else:
        # Contexto de alerta se houver mistura de distâncias
        distancias_unicas = df_filtrado["distancia_prova"].nunique()
        if distancias_unicas > 1:
            st.warning(
                "Você selecionou provas de distâncias diferentes. O ritmo (pace) varia sensivelmente com a distância; "
                "portanto, compare os tempos e paces com cautela.",
                icon=":material/info:",
            )

        # ----------------------------------------------------
        # SEÇÃO 1: O PANORAMA DAS CORRIDAS
        # ----------------------------------------------------
        st.subheader("1. Visão geral dos resultados")
        st.caption("Explore os tempos e ritmos registrados nas corridas incluídas no recorte atual.")

        tempos_validos = df_filtrado["tempo_total_minutos"].dropna()
        paces_validos = df_filtrado["pace_decimal"].dropna() if "pace_decimal" in df_filtrado.columns else pd.Series(dtype=float)
        stats_pace = calcular_metricas_estatisticas(paces_validos)
        num_provas = df_filtrado["nome_prova"].nunique()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Resultados Analisados",
                value=f"{len(df_filtrado):,}".replace(",", "."),
                help="Número de resultados de conclusão incluídos nos filtros ativos.",
            )

        with col2:
            if not tempos_validos.empty:
                idx_campeao = tempos_validos.idxmin()
                linha_campeao = df_filtrado.loc[idx_campeao]
                desc_campeao = (
                    f"Menor tempo total entre os válidos: {linha_campeao['nome_atleta']} "
                    f"({linha_campeao.get('distancia_prova', '')}) na prova {linha_campeao['nome_prova']}"
                )
                st.metric(
                    label="Melhor Tempo",
                    value=str(linha_campeao["tempo_bruto"]),
                    help=desc_campeao,
                )
            else:
                st.metric(label="Melhor Tempo", value="--:--")

        with col3:
            if stats_pace:
                pace_mediano_formatado = formatar_minutos_para_pace(stats_pace["mediana"]) or "--:--"
                st.metric(
                    label="Pace Mediano (P50)",
                    value=f"{pace_mediano_formatado} min/km",
                    help="Ritmo central: 50% dos resultados foram mais rápidos e 50% mais lentos do que este pace.",
                )
            else:
                st.metric(label="Pace Mediano (P50)", value="--:--")

        with col4:
            st.metric(
                label="Provas Incluídas",
                value=f"{num_provas}",
                help="Quantidade de eventos/etapas de corrida presentes no conjunto selecionado.",
            )

        # Expander de percentis estatísticos
        if stats_pace:
            with st.expander("Entenda a distribuição dos ritmos (Percentis P10 a P90)", expanded=False, icon=":material/query_stats:"):
                st.caption(
                    "No pace (min/km), **valores menores representam velocidades maiores**. "
                    "Por isso, o percentil P10 indica o pelotão mais veloz."
                )
                col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
                col_p1.metric(
                    "P10 (Mais rápidos)",
                    f"{formatar_minutos_para_pace(stats_pace['p10'])} min/km",
                    help="Percentil 10: apenas 10% dos atletas registraram ritmos mais velozes.",
                )
                col_p2.metric(
                    "P25 (1º Quartil)",
                    f"{formatar_minutos_para_pace(stats_pace['p25'])} min/km",
                    help="Primeiro quartil: faixa de pace que delimita os 25% mais rápidos.",
                )
                col_p3.metric(
                    "P50 (Mediana)",
                    f"{formatar_minutos_para_pace(stats_pace['mediana'])} min/km",
                    help="Mediana: ritmo exato do meio do pelotão.",
                )
                col_p4.metric(
                    "P75 (3º Quartil)",
                    f"{formatar_minutos_para_pace(stats_pace['p75'])} min/km",
                    help="Terceiro quartil: ritmo que supera 75% dos participantes.",
                )
                col_p5.metric(
                    "P90 (Pelotão Conclusão)",
                    f"{formatar_minutos_para_pace(stats_pace['p90'])} min/km",
                    help="Percentil 90: ritmo de conclusão confortável do grupo.",
                )

        st.divider()

        # Preparação do DataFrame enriquecido com categorias e formatação
        df_graficos = df_filtrado.copy()
        if "sexo" in df_graficos.columns:
            nomes_sexo = {"M": "Masculino", "F": "Feminino", "N/I": "Não identificado"}
            df_graficos["Categoria"] = df_graficos["sexo"].map(nomes_sexo).fillna("Não identificado")

        # ----------------------------------------------------
        # SEÇÃO 2: COMO É O RITMO DOS CORREDORES?
        # ----------------------------------------------------
        st.subheader("2. Como os ritmos se distribuem?")
        st.caption("Veja em quais faixas de pace se concentram os resultados dos concluintes.")

        if stats_pace:
            min_p = float(df_graficos["pace_decimal"].min())
            max_p = float(df_graficos["pace_decimal"].max())
            tickvals_p, ticktext_p = gerar_ticks_pace(min_p, max_p, step_segundos=30)

            fig_pace = px.histogram(
                df_graficos,
                x="pace_decimal",
                nbins=12,
                title="Distribuição de Frequência do Pace",
                labels={"pace_decimal": "Pace (min/km)"},
                color_discrete_sequence=[COLORS["accent-primary"]],
            )

            # Rótulos das referências centrais
            p_mediana = formatar_minutos_para_pace(stats_pace["mediana"])
            p_media = formatar_minutos_para_pace(stats_pace["media"])

            fig_pace.add_vline(
                x=stats_pace["mediana"],
                line_dash="dash",
                line_color=COR_MEDIANA,
                annotation_text=f"Mediana: {p_mediana} min/km",
                annotation_position="top left",
                annotation_font_color=COR_MEDIANA,
            )
            fig_pace.add_vline(
                x=stats_pace["media"],
                line_dash="dot",
                line_color=COR_MEDIA,
                annotation_text=f"Média: {p_media} min/km",
                annotation_position="top right",
                annotation_font_color=COR_MEDIA,
            )

            fig_pace.update_layout(
                yaxis_title="Quantidade de Resultados",
                xaxis_title="Pace (min/km)",
                xaxis=dict(tickmode="array", tickvals=tickvals_p, ticktext=ticktext_p),
                hovermode="x unified",
            )
            fig_pace.update_traces(hovertemplate="Quantidade: %{y}<extra></extra>")

            st.plotly_chart(fig_pace, use_container_width=True)

            st.info(
                f"**Interpretação:** A **mediana ({p_mediana} min/km)** reflete o ritmo típico central, menos vulnerável a extremos. "
                f"A **média ({p_media} min/km)** pondera todos os tempos (desvio padrão: ± {stats_pace['desvio_padrao']:.2f} min/km). "
                "Lembre-se: no pace, valores menores representam velocidades maiores.",
                icon=":material/lightbulb:",
            )

        st.divider()

        # ----------------------------------------------------
        # SEÇÃO 3: COMO OS GRUPOS SE COMPARAM?
        # ----------------------------------------------------
        st.subheader("3. Como os grupos e provas se comparam?")
        st.caption("Analise a variação do ritmo central e da dispersão entre categorias e eventos.")

        col_comp1, col_comp2 = st.columns(2)

        # Gráfico A: Boxplot por Categoria estimada
        with col_comp1:
            if "Categoria" in df_graficos.columns and stats_pace:
                # Contagem N por categoria para exibir no eixo
                contagens = df_graficos["Categoria"].value_counts().to_dict()
                df_graficos["Categoria_Rotulo"] = df_graficos["Categoria"].apply(lambda c: f"{c}<br>(N={contagens.get(c, 0)})")

                fig_box_cat = px.box(
                    df_graficos,
                    x="Categoria_Rotulo",
                    y="pace_decimal",
                    color="Categoria",
                    points="outliers",
                    title="Dispersão do Ritmo por Categoria Estimada",
                    labels={"pace_decimal": "Pace (min/km)", "Categoria_Rotulo": "Categoria Estimada"},
                    color_discrete_map=CORES_CATEGORIA,
                )

                min_cat = float(df_graficos["pace_decimal"].min())
                max_cat = float(df_graficos["pace_decimal"].max())
                t_vals, t_texts = gerar_ticks_pace(min_cat, max_cat, step_segundos=30)

                fig_box_cat.update_layout(
                    showlegend=False,
                    xaxis_title="Categoria (N = amostra)",
                    yaxis_title="Pace (min/km)",
                    yaxis=dict(tickmode="array", tickvals=t_vals, ticktext=t_texts),
                )
                st.plotly_chart(fig_box_cat, use_container_width=True)
                st.caption(
                    "A linha interna indica a **mediana**. A caixa contém os **50% centrais** dos resultados (P25 a P75). "
                    "Pontos isolados representam registros atípicos (outliers). Categorias estimadas via primeiro nome."
                )

        # Gráfico B: Comparação entre Provas
        with col_comp2:
            if stats_pace:
                if df_filtrado["nome_prova"].nunique() > 1:
                    # Ordenar provas por ritmo mediano (da mais veloz/menor pace para a mais lenta)
                    ordem_provas = df_filtrado.groupby("nome_prova")["pace_decimal"].median().sort_values(ascending=True).index.tolist()

                    # Nomes com quantidade
                    contagem_provas = df_filtrado["nome_prova"].value_counts().to_dict()
                    df_graficos["Prova_Rotulo"] = df_graficos["nome_prova"].apply(
                        lambda p: f"{p[:28]}... (N={contagem_provas.get(p, 0)})" if len(p) > 28 else f"{p} (N={contagem_provas.get(p, 0)})"
                    )
                    ordem_rotulos = [
                        f"{p[:28]}... (N={contagem_provas.get(p, 0)})" if len(p) > 28 else f"{p} (N={contagem_provas.get(p, 0)})"
                        for p in ordem_provas
                    ]

                    fig_box_prova = px.box(
                        df_graficos,
                        x="Prova_Rotulo",
                        y="pace_decimal",
                        category_orders={"Prova_Rotulo": ordem_rotulos},
                        title="Comparativo de Ritmo entre Provas (ordenado por mediana)",
                        labels={"pace_decimal": "Pace (min/km)", "Prova_Rotulo": "Prova"},
                        color_discrete_sequence=[COLORS["accent-primary"]],
                    )

                    min_pr = float(df_filtrado["pace_decimal"].min())
                    max_pr = float(df_filtrado["pace_decimal"].max())
                    tp_vals, tp_texts = gerar_ticks_pace(min_pr, max_pr, step_segundos=30)

                    fig_box_prova.update_layout(
                        showlegend=False,
                        xaxis_tickangle=-30,
                        xaxis_title="Provas (ordenadas da menor para a maior mediana)",
                        yaxis_title="Pace (min/km)",
                        yaxis=dict(tickmode="array", tickvals=tp_vals, ticktext=tp_texts),
                    )
                    st.plotly_chart(fig_box_prova, use_container_width=True)
                    st.caption(
                        "Eventos ordenados pela mediana do pace. Diferenças podem refletir altimetria, clima e perfil de participantes."
                    )
                else:
                    # Quando uma única prova está selecionada: Resumo comparativo Média vs Mediana por Categoria
                    df_resumo_cat = df_graficos.groupby("Categoria")["pace_decimal"].agg(["mean", "median", "count"]).reset_index()
                    df_melted = df_resumo_cat.melt(
                        id_vars=["Categoria", "count"], value_vars=["median", "mean"], var_name="Métrica", value_name="PaceDecimal"
                    )
                    df_melted["Métrica"] = df_melted["Métrica"].map({"median": "Mediana", "mean": "Média"})
                    df_melted["PaceFormatado"] = df_melted["PaceDecimal"].apply(formatar_minutos_para_pace) + " min/km"
                    df_melted["Rotulo_Cat"] = df_melted.apply(lambda r: f"{r['Categoria']}<br>(N={r['count']})", axis=1)

                    fig_bar_cat = px.bar(
                        df_melted,
                        x="Rotulo_Cat",
                        y="PaceDecimal",
                        color="Métrica",
                        barmode="group",
                        text="PaceFormatado",
                        title=f"Média vs Mediana nesta Prova ({prova_selecionada[:30]}...)",
                        labels={"PaceDecimal": "Pace (min/km)", "Rotulo_Cat": "Categoria"},
                        color_discrete_map={"Mediana": COR_MEDIANA, "Média": COR_MEDIA},
                    )

                    min_b = float(df_melted["PaceDecimal"].min()) * 0.85
                    max_b = float(df_melted["PaceDecimal"].max()) * 1.15
                    tb_vals, tb_texts = gerar_ticks_pace(min_b, max_b, step_segundos=30)

                    fig_bar_cat.update_layout(
                        yaxis_title="Pace (min/km)", yaxis=dict(tickmode="array", tickvals=tb_vals, ticktext=tb_texts)
                    )
                    fig_bar_cat.update_traces(textposition="outside")
                    st.plotly_chart(fig_bar_cat, use_container_width=True)
                    st.caption("Diferenças perceptíveis entre a média e a mediana revelam assimetria na distribuição dos tempos da prova.")

        st.divider()

        # ----------------------------------------------------
        # SEÇÃO 4: COMO OS RESULTADOS ESTÃO DISTRIBUÍDOS?
        # ----------------------------------------------------
        st.subheader("4. Distribuição dos resultados por categoria")
        st.caption("Veja como os registros coletados se dividem entre as classificações disponíveis.")

        col_cat1, col_cat2 = st.columns([1.2, 1])

        with col_cat1:
            if "Categoria" in df_graficos.columns:
                df_cat_count = df_graficos["Categoria"].value_counts().reset_index()
                df_cat_count.columns = ["Categoria", "Quantidade"]
                total_cat = df_cat_count["Quantidade"].sum()
                df_cat_count["Percentual"] = (df_cat_count["Quantidade"] / total_cat * 100).round(1)
                df_cat_count["Rotulo_Texto"] = df_cat_count.apply(lambda r: f"{r['Quantidade']} ({r['Percentual']}%)", axis=1)

                fig_bar_comp = px.bar(
                    df_cat_count,
                    x="Quantidade",
                    y="Categoria",
                    orientation="h",
                    text="Rotulo_Texto",
                    color="Categoria",
                    color_discrete_map=CORES_CATEGORIA,
                    title=f"Proporção por Categoria Estimada (Total N={total_cat})",
                )
                fig_bar_comp.update_layout(
                    showlegend=False,
                    xaxis_title="Quantidade de Registros",
                    yaxis_title="",
                )
                fig_bar_comp.update_traces(textposition="auto")
                st.plotly_chart(fig_bar_comp, use_container_width=True)

        with col_cat2:
            st.markdown(
                """
                **Observações metodológicas:**
                - **Classificação:** As categorias foram inferidas utilizando o primeiro nome dos corredores através de regras
                  fonéticas em português e dicionários de nomes.
                - **Transparência:** A categoria **Não identificado** contempla nomes unissex, ambíguos ou abreviações onde não é
                  prudente afirmar uma classificação.
                - **Amostra:** A contagem representa *registros de conclusão*, e não necessariamente indivíduos únicos distintos.
                """
            )

        st.divider()

        # ----------------------------------------------------
        # SEÇÃO 5: TABELA DE RESULTADOS INDIVIDUAIS
        # ----------------------------------------------------
        st.subheader("5. Explore os resultados individuais")
        st.caption("Consulte os tempos, distâncias e ritmos calculados para cada atleta no recorte selecionado.")

        colunas_exibicao = ["nome_prova", "nome_atleta", "sexo", "tempo_bruto", "numero_peito", "distancia_prova", "pace_min_km"]
        colunas_presentes = [col for col in colunas_exibicao if col in df_filtrado.columns]

        df_tabela = df_filtrado[colunas_presentes].copy()
        nomes_colunas_amigaveis = {
            "nome_prova": "Prova",
            "nome_atleta": "Atleta (LGPD)",
            "sexo": "Categoria",
            "tempo_bruto": "Tempo Líquido/Bruto",
            "numero_peito": "N° Peito",
            "distancia_prova": "Distância",
            "pace_min_km": "Pace (MM:SS min/km)",
        }
        df_tabela = df_tabela.rename(columns=nomes_colunas_amigaveis)

        st.dataframe(
            df_tabela.sort_values(by=["Pace (MM:SS min/km)", "Tempo Líquido/Bruto"], ascending=True),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        # ----------------------------------------------------
        # SEÇÃO 6: SOBRE OS DADOS E METODOLOGIA
        # ----------------------------------------------------
        with st.expander("Sobre os dados e metodologia de Engenharia de Dados", expanded=False, icon=":material/info:"):
            st.markdown(
                f"""
                ### Arquitetura e Pipeline Técnico
                - **Fonte primária:** Resultados oficiais de corridas em Fortaleza disponibilizados no portal O2 Corre.
                - **Coleta Automatizada (Scraper):** Desenvolvida com **Playwright** e retry exponencial com **Tenacity**,
                  garantindo resiliência a timeouts e paginações dinâmicas.
                - **Camada de Transformação (Pandas):**
                  - Conversão de strings de tempo (`HH:MM:SS`) em minutos decimais e distâncias (`5K`) em quilômetros numéricos.
                  - Cálculo de pace: `tempo_total_minutos / distancia_km`, com formatação precisa de segundos
                    (`0.2 min * 60 = 12s -> 03:12 min/km`).
                - **Privacidade & LGPD:** Nomes reduzidos (`Primeiro S.`) e identificadores únicos anônimos via SHA-256 (`id_atleta`).
                - **Volume nesta sessão:** **{len(df)}** registros na base local, abrangendo **{df["nome_prova"].nunique()}**
                  etapas de eventos esportivos.
                """
            )
