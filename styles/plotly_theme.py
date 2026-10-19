"""Tema Plotly do RunnerInsights (ver DESIGN_SYSTEM.md, seção 9)."""
import plotly.graph_objects as go
import plotly.io as pio

from styles.design_tokens import CATEGORICAL, COLORS

NOME_TEMPLATE = "runnerinsights"

# Cores semânticas das categorias de sexo estimado (verde neon reservado à série prioritária)
CORES_CATEGORIA = {
    "Masculino": "#38BDF8",
    "Feminino": "#F472B6",
    "Não identificado": "#A3A3A3",
}

COR_MEDIANA = COLORS["warning"]
COR_MEDIA = COLORS["info"]

_FONTE = "Inter, Arial, sans-serif"


def registrar_tema_plotly() -> None:
    """Registra e define o template padrão dos gráficos Plotly."""
    eixo = {
        "gridcolor": COLORS["border"],
        "gridwidth": 1,
        "zerolinecolor": COLORS["border"],
        "linecolor": COLORS["border"],
        "tickfont": {"color": COLORS["text-secondary"]},
        "title": {"font": {"color": COLORS["text-secondary"]}},
    }
    template = go.layout.Template()
    template.layout = go.Layout(
        paper_bgcolor=COLORS["bg-primary"],
        plot_bgcolor=COLORS["surface"],
        font={"family": _FONTE, "color": COLORS["text-primary"], "size": 13},
        title={"font": {"family": "Barlow Condensed, Arial Narrow, sans-serif", "size": 22, "color": COLORS["text-primary"]}},
        colorway=CATEGORICAL,
        xaxis=eixo,
        yaxis=eixo,
        legend={"font": {"color": COLORS["text-secondary"]}, "bgcolor": "rgba(0,0,0,0)"},
        hoverlabel={
            "bgcolor": COLORS["surface-hover"],
            "bordercolor": COLORS["border-strong"],
            "font": {"family": "JetBrains Mono, Consolas, monospace", "color": COLORS["text-primary"]},
        },
        margin={"l": 48, "r": 24, "t": 64, "b": 48},
    )
    pio.templates[NOME_TEMPLATE] = template
    pio.templates.default = NOME_TEMPLATE
