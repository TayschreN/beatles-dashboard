# -*- coding: utf-8 -*-
"""
Beatles Catalog Analytics — Dashboard interativo em Dash
Projeto de portfólio · Análise exploratória de 310 faixas dos Beatles (1958-1980)

Como rodar:
    pip install -r requirements.txt
    python app.py
Depois abra http://127.0.0.1:8050 no navegador.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from dash import Dash, dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc

# ----------------------------------------------------------------------------
# 1) DADOS — carregamento e engenharia de features
#    (mesma lógica de classificação usada no notebook original beatles_eda.ipynb)
# ----------------------------------------------------------------------------

df = pd.read_csv("data/beatles_songs.csv")

YEAR_MIN, YEAR_MAX = int(df["Year"].min()), int(df["Year"].max())
TOTAL_FAIXAS = len(df)


def classificar_compositor(s):
    s = str(s)
    tem_lennon = "Lennon" in s
    tem_mccartney = "McCartney" in s
    tem_harrison = "Harrison" in s
    tem_starkey = "Starkey" in s
    outros_nomes = [
        "Berry", "Goffin", "Perkins", "Charles", "Williams", "Leiber",
        "Traditional", "Allison", "Yellen", "Thompson", "Scott", "Russell",
    ]
    e_cover = any(nome in s for nome in outros_nomes)

    if e_cover and not (tem_lennon or tem_mccartney or tem_harrison or tem_starkey):
        return "Cover / outro autor"
    if tem_lennon and tem_mccartney and not tem_harrison and not tem_starkey:
        return "Lennon-McCartney (dupla)"
    if tem_lennon and not tem_mccartney and not tem_harrison and not tem_starkey:
        return "Lennon (solo)"
    if tem_mccartney and not tem_lennon and not tem_harrison and not tem_starkey:
        return "McCartney (solo)"
    if tem_harrison and not tem_lennon and not tem_mccartney and not tem_starkey:
        return "Harrison (solo)"
    if tem_starkey and not tem_lennon and not tem_mccartney and not tem_harrison:
        return "Starkey (solo)"
    return "Outra combinação / banda toda"


def classificar_vocal(s):
    if pd.isna(s) or str(s).strip() == "":
        return "Instrumental / não informado"
    s = str(s)
    flags = {
        "Lennon": "Lennon" in s,
        "McCartney": "McCartney" in s,
        "Harrison": "Harrison" in s,
        "Starkey": "Starkey" in s,
    }
    ativos = [k for k, v in flags.items() if v]
    if len(ativos) == 1:
        return ativos[0]
    if len(ativos) > 1:
        return "Vocal conjunto"
    return "Outro / convidado"


# limpeza leve dos rótulos de gênero (o dataset bruto tem duplicatas de
# capitalização e artefatos de raspagem, ex: "Acid Rock[", "Hard rock")
_GENERO_CANONICO = {
    "acid rock[": "Acid Rock", "heavy metal[": "Heavy Metal",
    "country rock": "Country Rock", "hard rock": "Hard Rock",
    "rock and roll": "Rock and Roll", "rock & roll": "Rock and Roll",
    "psychedelic folk": "Psychedelic Folk", "psychedelic pop": "Psychedelic Pop",
    "jangle pop": "Jangle Pop", "experimental pop": "Experimental Pop",
    "folk blues": "Folk Blues", "children's": "Children's Music",
    "children's music": "Children's Music", "folkpop/rock": "Folk Pop/Rock",
    "pop rock": "Pop Rock",
}


def limpar_genero(g):
    g = g.strip().rstrip("[]").strip()
    return _GENERO_CANONICO.get(g.lower(), g)


df["compositor_cat"] = df["Songwriter"].apply(classificar_compositor)
df["vocal_cat"] = df["Lead.vocal"].apply(classificar_vocal)
df["entrou_top50"] = df["Top.50.Billboard"] > 0
df["duration_min"] = df["Duration"] / 60
df["genre_list"] = (
    df["Genre"].fillna("").apply(lambda x: [limpar_genero(g) for g in x.split(",") if g.strip()])
)

GENEROS_DISPONIVEIS = sorted({g for lst in df["genre_list"] for g in lst})
COMPOSITORES_DISPONIVEIS = sorted(df["compositor_cat"].unique())
VOCAL_ORDEM = ["Lennon", "McCartney", "Harrison", "Starkey", "Vocal conjunto",
                "Outro / convidado", "Instrumental / não informado"]
VOCAIS_DISPONIVEIS = [v for v in VOCAL_ORDEM if v in df["vocal_cat"].unique()]
ALBUNS_DISPONIVEIS = df["Album.debut"].value_counts().index.tolist()

# ----------------------------------------------------------------------------
# 2) ESTILO — identidade visual "fita analógica / estúdio de gravação"
#    Paleta e tipografia compartilhadas com assets/style.css — qualquer
#    alteração de cor deve ser espelhada nos dois lugares.
# ----------------------------------------------------------------------------

COLORS = {
    "bg": "#0e1015",
    "card": "#1a1d26",
    "card_alt": "#21252f72",
    "border": "rgba(255,255,255,0.08)",
    "text": "#f3ede2",
    "muted": "#938ea0",
    "navy": "#3d5a73",
    "red": "#c23b3b",
    "green": "#7a9b76",
    "purple": "#9b6bb3",
    "gold": "#e0a458",
    "blue": "#5b8fb0",
    "gray": "#6b6f7a",
}

COMPOSITOR_COLORS = {
    "Lennon-McCartney (dupla)": COLORS["blue"],
    "Lennon (solo)": COLORS["navy"],
    "McCartney (solo)": COLORS["red"],
    "Harrison (solo)": COLORS["green"],
    "Starkey (solo)": COLORS["purple"],
    "Cover / outro autor": COLORS["gray"],
    "Outra combinação / banda toda": COLORS["gold"],
}

VOCAL_COLORS = {
    "Lennon": COLORS["navy"],
    "McCartney": COLORS["red"],
    "Harrison": COLORS["green"],
    "Starkey": COLORS["purple"],
    "Vocal conjunto": COLORS["blue"],
    "Outro / convidado": COLORS["gold"],
    "Instrumental / não informado": COLORS["gray"],
}

pio.templates["beatles_dark"] = go.layout.Template(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLORS["text"], size=12.5),
        title=dict(font=dict(size=15, family="Fraunces, serif", color=COLORS["text"]), x=0.02, xanchor="left"),
        colorway=[COLORS["gold"], COLORS["red"], COLORS["blue"], COLORS["green"], COLORS["purple"], COLORS["navy"]],
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)", linecolor="rgba(255,255,255,0.15)", automargin=True),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)", linecolor="rgba(255,255,255,0.15)", automargin=True),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=24, r=32, t=56, b=40),
        hoverlabel=dict(bgcolor=COLORS["card"], font_size=12.5, font_family="Inter, sans-serif", bordercolor=COLORS["border"]),
    )
)
pio.templates.default = "beatles_dark"

# Modebar com apenas o botão de download (demais ícones de zoom/pan removidos
# para manter a interface limpa). O PNG exportado sai com o tamanho renderizado
# na tela — já inclui título, eixos e legenda.
GRAPH_CONFIG_BASE = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d",
        "autoScale2d", "resetScale2d", "hoverClosestCartesian",
        "hoverCompareCartesian", "toggleSpikelines",
    ],
    "responsive": True,
}


def graph_card(graph_id, height=380, download_name="grafico"):
    """Envolve o dcc.Graph num card com altura CSS explícita.
    Sem isso, com responsive=True o Plotly mede a altura do container pai;
    se o pai não tiver altura definida, mede 0px e o gráfico nunca aparece."""
    config = {
        **GRAPH_CONFIG_BASE,
        "toImageButtonOptions": {"format": "png", "filename": download_name, "scale": 2},
    }
    return html.Div(
        dcc.Loading(
            dcc.Graph(id=graph_id, config=config, style={"height": f"{height}px", "width": "100%"}),
            color=COLORS["gold"], type="dot",
        ),
        className="chart-card",
    )


def style_fig(fig, height=380, showlegend=None):
    if showlegend is not None:
        fig.update_layout(showlegend=showlegend)
    fig.update_layout(height=height, template="beatles_dark")
    return fig


def empty_fig(msg="Nenhuma faixa encontrada para esse filtro"):
    fig = go.Figure()
    fig.add_annotation(text=msg, showarrow=False, font=dict(size=13, color=COLORS["muted"]))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return style_fig(fig, height=380)


def format_duration(seconds):
    if seconds is None or pd.isna(seconds):
        return "–"
    m = int(seconds // 60)
    s = int(round(seconds % 60))
    if s == 60:
        m += 1
        s = 0
    return f"{m}:{s:02d}"


# ----------------------------------------------------------------------------
# 3) FILTRAGEM
# ----------------------------------------------------------------------------

def aplicar_filtros(year_range, compositores, vocais, generos, albuns, somente_hits):
    dff = df
    mask = (dff["Year"] >= year_range[0]) & (dff["Year"] <= year_range[1])
    if compositores:
        mask &= dff["compositor_cat"].isin(compositores)
    if vocais:
        mask &= dff["vocal_cat"].isin(vocais)
    if generos:
        gens = set(generos)
        mask &= dff["genre_list"].apply(lambda lst: not gens.isdisjoint(lst))
    if albuns:
        mask &= dff["Album.debut"].isin(albuns)
    if somente_hits:
        mask &= dff["entrou_top50"]
    return dff[mask]


# ----------------------------------------------------------------------------
# 4) FIGURAS — 8 gráficos interativos
# ----------------------------------------------------------------------------

def fig_faixas_por_ano(dff):
    if dff.empty:
        return empty_fig()
    s = dff.groupby("Year").size().reset_index(name="Faixas")
    fig = px.bar(s, x="Year", y="Faixas", color_discrete_sequence=[COLORS["gold"]])
    fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y} faixas<extra></extra>", marker_line_width=0)
    fig.update_layout(title="① Faixas compostas por ano", xaxis_title=None, yaxis_title="Nº de faixas")
    return style_fig(fig)


def fig_duracao_por_ano(dff):
    if dff.empty:
        return empty_fig()
    s = dff.groupby("Year")["duration_min"].mean().reset_index()
    fig = px.area(s, x="Year", y="duration_min", color_discrete_sequence=[COLORS["gold"]], markers=True)
    fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y:.2f} min<extra></extra>", line=dict(width=2.5), fillgradient=dict(type="vertical", colorscale=[(0, "rgba(224,164,88,0.35)"), (1, "rgba(224,164,88,0)")]))
    fig.update_layout(title="② Duração média das faixas, por ano", xaxis_title=None, yaxis_title="Minutos")
    return style_fig(fig)


def fig_compositor(dff):
    if dff.empty:
        return empty_fig()
    s = dff["compositor_cat"].value_counts().reset_index()
    s.columns = ["Categoria", "Faixas"]
    fig = px.pie(s, names="Categoria", values="Faixas", hole=0.55, color="Categoria",
                 color_discrete_map=COMPOSITOR_COLORS)
    fig.update_traces(textinfo="percent", hovertemplate="<b>%{label}</b><br>%{value} faixas (%{percent})<extra></extra>",
                       marker=dict(line=dict(color=COLORS["bg"], width=2)))
    fig.update_layout(title="③ Quem compôs: divisão por categoria de autor",
                       legend=dict(orientation="h", yanchor="bottom", y=-0.34, x=0.5, xanchor="center", font=dict(size=10.5)),
                       margin=dict(l=24, r=32, t=56, b=76))
    return style_fig(fig, height=430)


def fig_vocal(dff):
    if dff.empty:
        return empty_fig()
    counts = dff["vocal_cat"].value_counts()
    counts = counts.reindex([o for o in VOCAL_ORDEM if o in counts.index])
    fig = px.bar(x=counts.values, y=counts.index, orientation="h", color=counts.index,
                 color_discrete_map=VOCAL_COLORS, text=counts.values)
    fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x} faixas<extra></extra>", textposition="outside", cliponaxis=False)
    fig.update_layout(title="④ Vocal principal, por Beatle", xaxis_title="Nº de faixas", yaxis_title=None, showlegend=False)
    return style_fig(fig)


def fig_taxa_hit(dff):
    if dff.empty:
        return empty_fig()
    grp = dff.groupby("compositor_cat")["entrou_top50"].agg(["mean", "count"])
    grp = grp[grp["count"] >= 5]
    if grp.empty:
        return empty_fig("Poucas faixas nesse recorte (mín. 5 por categoria)")
    grp["pct"] = (grp["mean"] * 100).round(1)
    grp = grp.sort_values("pct")
    fig = px.bar(grp, x="pct", y=grp.index, orientation="h", color=grp.index,
                 color_discrete_map=COMPOSITOR_COLORS, text=grp["pct"].map(lambda v: f"{v:.1f}%"))
    fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x:.1f}%% entrou no Top 50<extra></extra>", textposition="outside", cliponaxis=False)
    fig.update_layout(title="⑤ Taxa de entrada no Top 50 Billboard, por autor", xaxis_title="% das faixas", yaxis_title=None, showlegend=False)
    return style_fig(fig)


def fig_diversidade(dff):
    if dff.empty:
        return empty_fig()
    tmp = dff.explode("genre_list")
    tmp = tmp[tmp["genre_list"].notna() & (tmp["genre_list"] != "Pop/Rock") & (tmp["genre_list"] != "")]
    if tmp.empty:
        return empty_fig()
    s = tmp.groupby("Year")["genre_list"].nunique().reset_index(name="Subgêneros")
    fig = px.area(s, x="Year", y="Subgêneros", color_discrete_sequence=[COLORS["purple"]], markers=True)
    fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y} subgêneros distintos<extra></extra>", line=dict(width=2.5), fillgradient=dict(type="vertical", colorscale=[(0, "rgba(155,107,179,0.35)"), (1, "rgba(155,107,179,0)")]))
    fig.update_layout(title="⑥ Diversidade de subgêneros por ano (exclui \"Pop/Rock\")", xaxis_title=None, yaxis_title="Nº de subgêneros")
    return style_fig(fig)


def fig_duracao_hits(dff):
    if dff.empty or dff["entrou_top50"].sum() == 0 or (~dff["entrou_top50"]).sum() == 0:
        return empty_fig("Precisa de faixas nos dois grupos (Top 50 e fora) para comparar")
    tmp = dff.copy()
    tmp["Grupo"] = tmp["entrou_top50"].map({True: "Entrou no Top 50", False: "Fora do Top 50"})
    fig = px.box(tmp, x="Grupo", y="duration_min", color="Grupo", points="outliers",
                 color_discrete_map={"Entrou no Top 50": COLORS["gold"], "Fora do Top 50": COLORS["navy"]},
                 hover_data={"Title": True, "Grupo": False})
    fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>%{y:.2f} min<extra></extra>")
    fig.update_layout(title="⑦ Duração: faixas Top 50 vs. faixas fora da parada", xaxis_title=None, yaxis_title="Minutos", showlegend=False)
    return style_fig(fig)


def fig_evergreen(dff):
    if dff.empty or dff["Other.releases"].max() == 0:
        return empty_fig("Sem relançamentos registrados nesse recorte")
    top = dff.nlargest(10, "Other.releases")[["Title", "Other.releases"]].sort_values("Other.releases")
    fig = px.bar(top, x="Other.releases", y="Title", orientation="h", color_discrete_sequence=[COLORS["gold"]], text="Other.releases")
    fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x} relançamentos<extra></extra>", textposition="outside", cliponaxis=False)
    fig.update_layout(title="⑧ Top 10 faixas mais \"evergreen\" (relançamentos)", xaxis_title="Nº de outros relançamentos", yaxis_title=None)
    return style_fig(fig, height=430)


# ----------------------------------------------------------------------------
# 5) INSIGHTS (texto fixo — refletem o catálogo completo, base do storytelling)
# ----------------------------------------------------------------------------

INSIGHTS = [
    ("bi-trophy", COLORS["gold"], "McCartney bate Lennon em volume solo",
     "68 faixas de McCartney (solo) contra 65 de Lennon (solo) — contraria a percepção popular de Lennon como o mais prolífico."),
    ("bi-clock-history", COLORS["red"], "Faixas foram ficando mais longas",
     "Duração média sobe de ~2,3 min (1962-63) para ~3,0 min (1968-69), refletindo a virada de singles de rádio para álbuns conceituais."),
    ("bi-mic", COLORS["navy"], "Quem canta não é quem mais compõe",
     "Lennon lidera nos vocais principais (99 faixas) — inverte o resultado de composição, onde McCartney vence."),
    ("bi-graph-up-arrow", COLORS["blue"], "Hits do Top 50 são mais longos, não mais curtos",
     "Contraria a hipótese de que rádio recompensava só faixas curtas: a duração média dos hits é maior que a das faixas fora da parada."),
    ("bi-palette", COLORS["purple"], "Explosão de gêneros a partir de 1965",
     "O nº de subgêneros distintos por ano dispara em meados dos anos 60 — evidência quantitativa da fase de expansão estilística da banda."),
    ("bi-person-arms-up", COLORS["green"], "Harrison sai da sombra no fim da carreira",
     "Praticamente não compõe em 1962-64 (2 faixas) e cresce fortemente em 1968-69 (13 faixas) — o \"Beatle quieto\" ganha espaço."),
    ("bi-pen", COLORS["gray"], "\"Lennon-McCartney\" virou cada vez mais formalidade",
     "A fração de composições genuinamente conjuntas cai de ~46% (1962-63) para ~23% (1967-69) — o crédito compartilhado não refletia mais coautoria constante."),
    ("bi-calendar-event", COLORS["gold"], "1963: o ano mais prolífico",
     "66 faixas compostas em um único ano — o auge da Beatlemania britânica, antes da invasão dos EUA em 1964."),
]

# ----------------------------------------------------------------------------
# 6) APP
# ----------------------------------------------------------------------------

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css",
        "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap",
    ],
    title="Beatles Catalog Analytics",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server


def kpi_card(icon, value_id, label, accent):
    return dbc.Col(
        html.Div(
            [
                html.Div(html.I(className=f"bi {icon}"), className="kpi-icon", style={"color": accent}),
                html.Div(
                    [
                        html.Div(id=value_id, className="kpi-value"),
                        html.Div(label, className="kpi-label"),
                    ]
                ),
            ],
            className="kpi-card",
            style={"borderTop": f"2px solid {accent}"},
        ),
        xs=6, md=4, lg=2,
    )


def filtro_bloco(titulo, children):
    return html.Div([html.Div(titulo, className="filtro-titulo"), children], className="filtro-bloco")


sidebar = html.Div(
    [
        html.Div(
            [
                html.I(className="bi bi-sliders me-2"),
                html.Span("Filtros"),
            ],
            className="sidebar-title",
        ),
        filtro_bloco(
            "Intervalo de anos",
            dcc.RangeSlider(
                id="f-year", min=YEAR_MIN, max=YEAR_MAX, step=1,
                value=[YEAR_MIN, YEAR_MAX], allowCross=False,
                marks={y: str(y) for y in [1958, 1963, 1966, 1969, 1977, 1980]},
                tooltip={"placement": "bottom", "always_visible": False},
                className="dark-slider",
            ),
        ),
        filtro_bloco(
            "Compositor",
            dcc.Dropdown(id="f-compositor", options=COMPOSITORES_DISPONIVEIS, multi=True,
                         placeholder="Todos", className="dark-dropdown"),
        ),
        filtro_bloco(
            "Vocal principal",
            dcc.Dropdown(id="f-vocal", options=VOCAIS_DISPONIVEIS, multi=True,
                         placeholder="Todos", className="dark-dropdown"),
        ),
        filtro_bloco(
            "Gênero",
            dcc.Dropdown(id="f-genero", options=GENEROS_DISPONIVEIS, multi=True,
                         placeholder="Todos", className="dark-dropdown"),
        ),
        filtro_bloco(
            "Álbum de estreia",
            dcc.Dropdown(id="f-album", options=ALBUNS_DISPONIVEIS, multi=True,
                         placeholder="Todos", className="dark-dropdown"),
        ),
        html.Div(
            dbc.Switch(id="f-hits", label="Somente faixas Top 50 Billboard", value=False, className="hits-switch"),
            className="filtro-bloco",
        ),
        dbc.Button([html.I(className="bi bi-arrow-counterclockwise me-2"), "Limpar filtros"],
                   id="btn-reset", color="secondary", outline=True, size="sm", className="w-100 mt-2"),
        html.Hr(style={"borderColor": COLORS["border"]}),
        html.Div(id="filtro-resumo", className="filtro-resumo"),
    ],
    className="sidebar",
)

header = html.Div(
    [
        html.Div(
            [
                html.Div("🎸", className="header-emoji"),
                html.Div(
                    [
                        html.H1("Beatles Catalog Analytics", className="header-title"),
                        html.P(f"Análise exploratória interativa · {TOTAL_FAIXAS} faixas · {YEAR_MIN}–{YEAR_MAX}",
                               className="header-subtitle"),
                    ]
                ),
            ],
            className="header-left",
        ),
        html.Div(
            [
                html.A([html.I(className="bi bi-github me-1"), "GitHub"], href="https://github.com/TayschreN",
                       target="_blank", className="header-link"),
                html.A([html.I(className="bi bi-linkedin me-1"), "LinkedIn"], href="https://linkedin.com/in/gabrielfranca123",
                       target="_blank", className="header-link"),
            ],
            className="header-right",
        ),
    ],
    className="header",
)

kpi_row = dbc.Row(
    [
        kpi_card("bi-music-note-list", "kpi-total", "Faixas no recorte", COLORS["gold"]),
        kpi_card("bi-stopwatch", "kpi-duracao", "Duração média", COLORS["blue"]),
        kpi_card("bi-star", "kpi-top50", "Entraram no Top 50", COLORS["red"]),
        kpi_card("bi-arrow-repeat", "kpi-relancamentos", "Relançamentos (méd.)", COLORS["purple"]),
        kpi_card("bi-calendar3", "kpi-ano", "Ano mais prolífico", COLORS["green"]),
        kpi_card("bi-feather", "kpi-compositor", "Autor mais presente", COLORS["navy"]),
    ],
    className="g-3 kpi-row",
)

charts_grid = html.Div(
    [
        dbc.Row([
            dbc.Col(graph_card("g1", 380, "faixas_compostas_por_ano"), md=6, className="chart-col"),
            dbc.Col(graph_card("g2", 380, "duracao_media_por_ano"), md=6, className="chart-col"),
        ], className="g-3"),
        dbc.Row([
            dbc.Col(graph_card("g3", 430, "composicao_por_autor"), md=6, className="chart-col"),
            dbc.Col(graph_card("g4", 380, "vocal_principal_por_beatle"), md=6, className="chart-col"),
        ], className="g-3"),
        dbc.Row([
            dbc.Col(graph_card("g5", 380, "taxa_top50_por_autor"), md=6, className="chart-col"),
            dbc.Col(graph_card("g6", 380, "diversidade_subgeneros_por_ano"), md=6, className="chart-col"),
        ], className="g-3"),
        dbc.Row([
            dbc.Col(graph_card("g7", 380, "duracao_top50_vs_fora"), md=6, className="chart-col"),
            dbc.Col(graph_card("g8", 430, "top10_faixas_evergreen"), md=6, className="chart-col"),
        ], className="g-3"),
    ]
)

insights_section = html.Div(
    [
        html.Div([html.I(className="bi bi-lightbulb me-2"), "Insights do catálogo completo"], className="section-title"),
        html.P("Achados fixos, calculados sobre as 310 faixas do catálogo — servem de contexto enquanto você explora os filtros acima.",
               className="section-subtitle"),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.I(className=f"bi {icon}", style={"color": accent}),
                            html.Div([html.Div(titulo, className="insight-titulo"), html.Div(texto, className="insight-texto")]),
                        ],
                        className="insight-card",
                        style={"borderLeft": f"3px solid {accent}"},
                    ),
                    md=6, lg=3, className="mb-3",
                )
                for icon, accent, titulo, texto in INSIGHTS
            ],
            className="g-3",
        ),
        html.P(
            [
                html.I(className="bi bi-info-circle me-2"),
                "Limitações: \"Year\" reflete o ano de composição, não de lançamento; não há dados diretos de vendas/streams, "
                "apenas proxies (relançamentos e posição no Top 50 Billboard dos EUA).",
            ],
            className="disclaimer",
        ),
    ],
    className="insights-section",
)

footer = html.Div(
    [
        html.Span("Fonte dos dados: "),
        html.A("inteligentni/Class-05-Feature-engineering", href="https://github.com/inteligentni/Class-05-Feature-engineering", target="_blank"),
        html.Span(" · Dashboard construído com Dash + Plotly · Projeto de portfólio de Gabriel Silva"),
    ],
    className="footer",
)

app.layout = dbc.Container(
    [
        header,
        dbc.Row(
            [
                dbc.Col(sidebar, lg=2, md=12, className="sidebar-col"),
                dbc.Col(
                    [
                        html.Div(id="alert-vazio"),
                        kpi_row,
                        charts_grid,
                        insights_section,
                    ],
                    lg=10, md=12,
                ),
            ],
            className="g-4",
        ),
        footer,
    ],
    fluid=True,
    className="app-container",
)

# ----------------------------------------------------------------------------
# 7) CALLBACKS
# ----------------------------------------------------------------------------

FILTER_INPUTS = [
    Input("f-year", "value"),
    Input("f-compositor", "value"),
    Input("f-vocal", "value"),
    Input("f-genero", "value"),
    Input("f-album", "value"),
    Input("f-hits", "value"),
]


@app.callback(
    Output("kpi-total", "children"),
    Output("kpi-duracao", "children"),
    Output("kpi-top50", "children"),
    Output("kpi-relancamentos", "children"),
    Output("kpi-ano", "children"),
    Output("kpi-compositor", "children"),
    Output("g1", "figure"),
    Output("g2", "figure"),
    Output("g3", "figure"),
    Output("g4", "figure"),
    Output("g5", "figure"),
    Output("g6", "figure"),
    Output("g7", "figure"),
    Output("g8", "figure"),
    Output("filtro-resumo", "children"),
    Output("alert-vazio", "children"),
    FILTER_INPUTS,
)
def atualizar_dashboard(year_range, compositores, vocais, generos, albuns, somente_hits):
    dff = aplicar_filtros(year_range, compositores, vocais, generos, albuns, somente_hits)

    total = len(dff)
    if total == 0:
        alerta = dbc.Alert(
            [html.I(className="bi bi-exclamation-triangle me-2"), "Nenhuma faixa corresponde aos filtros selecionados. Tente ampliar o recorte."],
            color="warning", className="mb-3",
        )
        kpis = ("0", "–", "–", "–", "–", "–")
    else:
        alerta = None
        duracao_media = format_duration(dff["Duration"].mean())
        pct_top50 = f"{dff['entrou_top50'].mean() * 100:.0f}%"
        media_relanc = f"{dff['Other.releases'].mean():.1f}"
        ano_top = str(dff.groupby('Year').size().idxmax())
        compositor_top = dff['compositor_cat'].value_counts().idxmax()
        kpis = (f"{total}", duracao_media, pct_top50, media_relanc, ano_top, compositor_top)

    resumo = f"Mostrando {total} de {TOTAL_FAIXAS} faixas"

    figs = (
        fig_faixas_por_ano(dff),
        fig_duracao_por_ano(dff),
        fig_compositor(dff),
        fig_vocal(dff),
        fig_taxa_hit(dff),
        fig_diversidade(dff),
        fig_duracao_hits(dff),
        fig_evergreen(dff),
    )

    return kpis + figs + (resumo, alerta)


@app.callback(
    Output("f-year", "value"),
    Output("f-compositor", "value"),
    Output("f-vocal", "value"),
    Output("f-genero", "value"),
    Output("f-album", "value"),
    Output("f-hits", "value"),
    Input("btn-reset", "n_clicks"),
    prevent_initial_call=True,
)
def resetar_filtros(n_clicks):
    return [YEAR_MIN, YEAR_MAX], None, None, None, None, False


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)