"""Design tokens do RunnerInsights (fonte única de verdade para cores, tipografia e espaçamento).

Referência: DESIGN_SYSTEM.md. Usado por `styles/theme.css` (via variáveis CSS) e `styles/plotly_theme.py`.
"""

COLORS = {
    "bg-primary": "#050708",
    "bg-secondary": "#101416",
    "surface": "#171B1E",
    "surface-hover": "#202629",
    "accent-primary": "#B6F500",
    "accent-hover": "#C9FF24",
    "text-primary": "#FFFFFF",
    "text-secondary": "#A3A3A3",
    "text-muted": "#737B80",
    "border": "#30383D",
    "border-strong": "#454D52",
    # Semânticas: usar somente quando a informação exigir o significado
    "success": "#22C55E",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#38BDF8",
}

# Paleta categórica para gráficos (primeira cor = série prioritária)
CATEGORICAL = ["#B6F500", "#38BDF8", "#A78BFA", "#F59E0B", "#F472B6", "#A3A3A3"]

SPACING = {f"space-{n}": f"{n * 4}px" for n in (1, 2, 3, 4, 5, 6, 8, 10, 12)}

RADIUS = {"radius-md": "10px", "radius-lg": "12px"}

FONTS = {
    "font-display": "'Barlow Condensed', 'Arial Narrow', sans-serif",
    "font-body": "'Inter', Arial, sans-serif",
    "font-mono": "'JetBrains Mono', Consolas, monospace",
}

# Transições curtas (120–200 ms)
TRANSITION = "160ms ease"


def css_variables() -> str:
    """Gera o bloco `:root` com todos os tokens como variáveis CSS."""
    linhas = [f"  --color-{nome}: {valor};" for nome, valor in COLORS.items()]
    linhas += [f"  --{nome}: {valor};" for nome, valor in {**SPACING, **RADIUS, **FONTS}.items()]
    linhas.append(f"  --transition: {TRANSITION};")
    return ":root {\n" + "\n".join(linhas) + "\n}"
