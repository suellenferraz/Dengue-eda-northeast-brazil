from __future__ import annotations
from pathlib import Path
import pandas as pd

# Valores que o SINAN usa para "sem informacao": contam como nulos no perfil.
AUSENTES = {"", "nan", "NaN", "None", "null"}

# Descricoes dos campos da ficha de dengue do SINAN (nomes em maiusculas; a busca ignora maiusculas).
# A ficha mudou em 2007: alguns campos trocaram de nome (ficha antiga -> nova). Os codigos de
# CLASSI_FIN tambem mudaram em 2014; confirme no dicionario oficial antes de usar.
DESCRICOES_SINAN = {
    "ANO_ARQUIVO": "Ano do arquivo de origem (coluna criada na carga)",
    "NU_NOTIFIC": "Numero da notificacao",
    "TP_NOT": "Tipo de notificacao",
    "ID_AGRAVO": "Codigo CID-10 do agravo (A90 = dengue)",
    "DT_NOTIFIC": "Data da notificacao",
    "SEM_NOT": "Semana epidemiologica da notificacao",
    "NU_ANO": "Ano da notificacao",
    "SG_UF_NOT": "UF de notificacao (sigla nos anos antigos, codigo IBGE nos recentes)",
    "ID_MUNICIP": "Municipio de notificacao (codigo IBGE: 7 digitos ate 2006, 6 depois)",
    "DT_SIN_PRI": "Data dos primeiros sintomas",
    "SEM_PRI": "Semana epidemiologica dos primeiros sintomas",
    "NU_IDADE": "Idade, ficha ate 2006 (letra = unidade, ex.: A046 = 46 anos)",
    "NU_IDADE_N": "Idade, ficha desde 2007 (1o digito = unidade: 1 hora, 2 dia, 3 mes, 4 ano; ex.: 4046 = 46 anos)",
    "ANO_NASC": "Ano de nascimento",
    "DT_NASC": "Data de nascimento (2016 a 2019)",
    "CS_SEXO": "Sexo (M, F, I = ignorado)",
    "CS_GESTANT": "Gestante (trimestre ou nao)",
    "CS_RACA": "Raca/cor",
    "CS_ESCOL_N": "Escolaridade",
    "SG_UF": "UF de residencia (sigla nos anos antigos, codigo IBGE nos recentes)",
    "ID_MN_RESI": "Municipio de residencia (codigo IBGE: 7 digitos ate 2006, 6 depois)",
    "CON_CLASSI": "Classificacao final, ficha ate 2006 (equivale a CLASSI_FIN)",
    "CLASSI_FIN": "Classificacao final, ficha desde 2007 (codigos mudaram em 2014)",
    "CON_CRITER": "Criterio de confirmacao, ficha ate 2006 (equivale a CRITERIO)",
    "CRITERIO": "Criterio de confirmacao (1 laboratorial, 2 clinico-epidemiologico)",
    "CON_EVOLUC": "Evolucao do caso, ficha ate 2006 (equivale a EVOLUCAO)",
    "EVOLUCAO": "Evolucao do caso (cura, obito pelo agravo, obito por outra causa)",
    "DT_OBITO": "Data do obito",
    "HOSPITALIZ": "Houve hospitalizacao (1 sim, 2 nao, 9 ignorado)",
    "SOROTIPO": "Sorotipo do virus (1 a 4)",
}

def descricao(coluna: str) -> str:
    """Descricao conhecida do campo, ou PREENCHER."""
    return DESCRICOES_SINAN.get(str(coluna).upper(), "PREENCHER")

def perfil_colunas(df: pd.DataFrame, n_exemplos: int = 3) -> pd.DataFrame:
    """Tipo, % de nulos, valores unicos, exemplos e descricao de cada coluna (valores de AUSENTES contam como nulos)."""
    linhas = []
    for col in df.columns:
        s = df[col]
        validos = s[s.notna() & ~s.astype(str).str.strip().isin(AUSENTES)]
        linhas.append({
            "variavel": col,
            "tipo_pandas": str(s.dtype),
            "pct_nulos": round(100 * (1 - len(validos) / len(s)), 2) if len(s) else 0.0,
            "n_unicos": validos.nunique(),
            "exemplos": ", ".join(validos.astype(str).drop_duplicates().head(n_exemplos)),
            "descricao": descricao(col),
        })
    return pd.DataFrame(linhas)

def salvar_markdown(perfil: pd.DataFrame, caminho: Path, titulo: str, fonte: str) -> None:
    """Grava o perfil como tabela Markdown."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    cab = ["variavel", "tipo_pandas", "pct_nulos", "n_unicos", "exemplos", "descricao"]
    celula = lambda v: str(v).replace("|", "/").replace("\n", " ")
    linhas = [f"## {titulo}", "", f"Fonte: {fonte}", "",
              "| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    linhas += ["| " + " | ".join(celula(r[c]) for c in cab) + " |" for _, r in perfil.iterrows()]
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
