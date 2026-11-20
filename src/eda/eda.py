from __future__ import annotations
import sys
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # pasta src/
from config import ANO_FIM, ANO_INICIO, BANCO, UFS_NORDESTE  # noqa: E402

UFS = list(UFS_NORDESTE)                      # ordem de exibição: MA, PI, CE, RN, PB, PE, AL, SE, BA
UF_SIGLA = {cod: sigla for sigla, cod in UFS_NORDESTE.items()}
CAPITAIS = {
    "2111300": "São Luís", "2211001": "Teresina", "2304400": "Fortaleza", "2408102": "Natal",
    "2507507": "João Pessoa", "2611606": "Recife", "2704302": "Maceió", "2800308": "Aracaju",
    "2927408": "Salvador",
}
CAPITAL_UF = {UF_SIGLA[int(cod[:2])]: nome for cod, nome in CAPITAIS.items()}

LIMIAR_MEDIA, LIMIAR_ALTA = 100, 300          # casos por 100 mil hab. (03_decisoes.md, decisão 11)
FAIXAS_ETARIAS = ["0–4", "5–9", "10–19", "20–39", "40–59", "60+"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
FONTE = f"Fonte: SINAN (OpenDataSUS) e IBGE. Casos prováveis, {ANO_INICIO}–{ANO_FIM}; {ANO_FIM} sujeito a revisão."

# Cores: paleta de referência da skill dataviz. Duas séries no máximo por gráfico; UFs vão em painéis.
COR = {
    "principal": "#2a78d6", "comparacao": "#eb6834", "referencia": "#8c8b86",
    "limiar": "#52514e", "texto": "#0b0b0b", "texto2": "#52514e", "grade": "#e4e3df",
}
SEQUENCIAL = mpl.colors.LinearSegmentedColormap.from_list(
    "azul", ["#f4f8fe", "#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"])
DIVERGENTE = mpl.colors.LinearSegmentedColormap.from_list(
    "azul_vermelho", ["#1c5cab", "#86b6ef", "#f0efec", "#ef9a99", "#b5302f"])


def estilo():
    """Aplica o estilo comum dos gráficos (eixos discretos, textos em português)."""
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 150, "figure.facecolor": "white",
        "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": COR["texto2"],
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": COR["grade"], "grid.linewidth": 0.8,
        "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelcolor": COR["texto2"], "xtick.color": COR["texto2"], "ytick.color": COR["texto2"],
        "lines.linewidth": 2, "legend.frameon": False, "font.size": 9,
    })


def nota(fig, texto: str = FONTE):
    """Escreve a nota de fonte e período no rodapé da figura."""
    fig.text(0.01, -0.02, texto, ha="left", va="top", fontsize=7.5, color=COR["texto2"])


def consulta(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Executa uma consulta no Postgres local e devolve um DataFrame."""
    with psycopg.connect(**BANCO) as con:
        cur = con.execute(sql, params or {})
        return pd.DataFrame(cur.fetchall(), columns=[d.name for d in cur.description])


def painel_municipio_ano() -> pd.DataFrame:
    """Município × ano (2000–2025) com população e casos prováveis, sem duplicatas e confirmados.

    Parte da população (todos os municípios e anos), então município sem caso aparece com zero."""
    df = consulta("""
        WITH casos AS (
            SELECT cod_mun7, ano,
                   count(*) FILTER (WHERE caso_provavel)                            AS provaveis,
                   count(*) FILTER (WHERE caso_provavel AND NOT possivel_duplicata) AS provaveis_sem_dup,
                   count(*) FILTER (WHERE caso_confirmado)                          AS confirmados
            FROM notificacao_dengue_ne
            WHERE ano BETWEEN %(ini)s AND %(fim)s
            GROUP BY cod_mun7, ano)
        SELECT p.cod_mun7, m.nome, m.uf_cod, p.ano, p.populacao,
               coalesce(c.provaveis, 0)         AS provaveis,
               coalesce(c.provaveis_sem_dup, 0) AS provaveis_sem_dup,
               coalesce(c.confirmados, 0)       AS confirmados
        FROM populacao_municipio_ano p
        JOIN municipio m USING (cod_mun7)
        LEFT JOIN casos c USING (cod_mun7, ano)
        WHERE p.ano BETWEEN %(ini)s AND %(fim)s
    """, {"ini": ANO_INICIO, "fim": ANO_FIM})
    df["uf"] = pd.Categorical(df["uf_cod"].map(UF_SIGLA), categories=UFS, ordered=True)
    for c in ("populacao", "provaveis", "provaveis_sem_dup", "confirmados"):
        df[c] = df[c].astype("int64")
    return df.drop(columns="uf_cod")


def casos_mes() -> pd.DataFrame:
    """Casos prováveis por UF, capital ou interior, ano e mês dos primeiros sintomas (2000–2025)."""
    df = consulta("""
        SELECT m.uf_cod, n.cod_mun7 = ANY(%(capitais)s) AS capital,
               extract(year FROM n.dt_sintomas)::int AS ano,
               extract(month FROM n.dt_sintomas)::int AS mes, count(*) AS casos
        FROM notificacao_dengue_ne n
        JOIN municipio m USING (cod_mun7)
        WHERE n.caso_provavel
          AND n.dt_sintomas >= make_date(%(ini)s, 1, 1)
          AND n.dt_sintomas < make_date(%(fim)s + 1, 1, 1)
        GROUP BY 1, 2, 3, 4
    """, {"capitais": list(CAPITAIS), "ini": ANO_INICIO, "fim": ANO_FIM})
    df["uf"] = pd.Categorical(df["uf_cod"].map(UF_SIGLA), categories=UFS, ordered=True)
    df["grupo"] = np.where(df["capital"], "capital", "interior")
    df["casos"] = df["casos"].astype("int64")
    return df.drop(columns=["uf_cod", "capital"])


def casos_idade_sexo() -> pd.DataFrame:
    """Casos prováveis por UF, ano, faixa etária e sexo (2000–2025); idade ou sexo vazios ficam como nulo."""
    df = consulta("""
        SELECT m.uf_cod, n.ano,
               CASE WHEN n.idade_anos IS NULL THEN NULL
                    WHEN n.idade_anos < 5  THEN '0–4'
                    WHEN n.idade_anos < 10 THEN '5–9'
                    WHEN n.idade_anos < 20 THEN '10–19'
                    WHEN n.idade_anos < 40 THEN '20–39'
                    WHEN n.idade_anos < 60 THEN '40–59'
                    ELSE '60+' END AS faixa_etaria,
               n.sexo, count(*) AS casos
        FROM notificacao_dengue_ne n
        JOIN municipio m USING (cod_mun7)
        WHERE n.caso_provavel AND n.ano BETWEEN %(ini)s AND %(fim)s
        GROUP BY 1, 2, 3, 4
    """, {"ini": ANO_INICIO, "fim": ANO_FIM})
    df["uf"] = pd.Categorical(df["uf_cod"].map(UF_SIGLA), categories=UFS, ordered=True)
    df["faixa_etaria"] = pd.Categorical(df["faixa_etaria"], categories=FAIXAS_ETARIAS, ordered=True)
    df["casos"] = df["casos"].astype("int64")
    return df.drop(columns="uf_cod")


def incidencia(casos, populacao):
    """Casos por 100 mil habitantes."""
    return casos / populacao * 1e5


def faixa_incidencia(valor: float) -> str:
    """Classifica a incidência anual: baixa (< 100), média (100–299) ou alta (≥ 300 por 100 mil)."""
    if valor >= LIMIAR_ALTA:
        return "alta"
    return "média" if valor >= LIMIAR_MEDIA else "baixa"


def estatisticas_circulares(pesos) -> tuple[float, float]:
    """Mês central (média circular em [0,5; 12,5)) e concentração R (0 a 1)."""
    w = np.asarray(pesos, float)
    if w.sum() == 0:
        return np.nan, np.nan
    ang = (np.arange(1, 13) - 0.5) * 2 * np.pi / 12
    c, s = (w * np.cos(ang)).sum() / w.sum(), (w * np.sin(ang)).sum() / w.sum()
    return (np.arctan2(s, c) % (2 * np.pi)) * 12 / (2 * np.pi) + 0.5, float(np.hypot(c, s))


def media_circular(meses) -> float:
    """Média circular de meses fracionários (dezembro e janeiro ficam vizinhos)."""
    m = np.asarray(meses, float)
    m = m[~np.isnan(m)]
    ang = (m - 0.5) * 2 * np.pi / 12
    return (np.arctan2(np.sin(ang).mean(), np.cos(ang).mean()) % (2 * np.pi)) * 12 / (2 * np.pi) + 0.5


def distancia_meses(a, b):
    """Distância circular entre meses (no máximo 6)."""
    d = np.abs(np.asarray(a, float) - b)
    return np.minimum(d, 12 - d)


def nome_mes(m: float) -> str:
    """Nome abreviado do mês de um valor fracionário (ex.: 4,3 → abr; 12,7 → jan)."""
    return "—" if np.isnan(m) else MESES[(int(round(m)) - 1) % 12]


def v_de_cramer(tabela: pd.DataFrame) -> float:
    """Tamanho do efeito da associação numa tabela de contingência (0 = nenhuma, 1 = total)."""
    obs = tabela.to_numpy(float)
    esp = obs.sum(axis=1, keepdims=True) * obs.sum(axis=0, keepdims=True) / obs.sum()
    qui2 = ((obs - esp) ** 2 / esp).sum()
    return float(np.sqrt(qui2 / (obs.sum() * (min(obs.shape) - 1))))
