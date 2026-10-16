"""Gera o esqueleto do dicionario de dados a partir de um DataFrame real.

Os tipos, % de nulos e exemplos saem dos dados. As descricoes vem do dicionario
padrao SINAN abaixo quando o campo e conhecido; o resto fica "PREENCHER".
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# Descricoes do layout padrao da ficha de dengue do SINAN. CONFIRMAR contra os campos
# reais da API: nomes podem vir em minusculas ou diferir. Codigos de CLASSI_FIN
# mudaram entre versoes da ficha, entao verifique o dicionario oficial por periodo.
DESCRICOES_SINAN = {
    "NU_NOTIFIC": "Numero da notificacao",
    "TP_NOT": "Tipo de notificacao",
    "ID_AGRAVO": "Codigo CID-10 do agravo",
    "DT_NOTIFIC": "Data da notificacao",
    "SEM_NOT": "Semana epidemiologica da notificacao",
    "NU_ANO": "Ano da notificacao",
    "SG_UF_NOT": "UF de notificacao",
    "ID_MUNICIP": "Municipio de notificacao (codigo IBGE, 6 digitos)",
    "DT_SIN_PRI": "Data dos primeiros sintomas",
    "SEM_PRI": "Semana epidemiologica dos primeiros sintomas",
    "NU_IDADE_N": "Idade codificada (1o digito: 1 hora, 2 dia, 3 mes, 4 ano; demais: valor)",
    "CS_SEXO": "Sexo (M, F, I)",
    "CS_GESTANT": "Gestante (trimestre ou nao)",
    "CS_RACA": "Raca/cor",
    "CS_ESCOL_N": "Escolaridade",
    "SG_UF": "UF de residencia",
    "ID_MN_RESI": "Municipio de residencia (codigo IBGE, 6 digitos)",
    "CLASSI_FIN": "Classificacao final do caso (codigos variam por versao da ficha)",
    "CRITERIO": "Criterio de confirmacao (laboratorial, clinico-epidemiologico)",
    "EVOLUCAO": "Evolucao do caso (cura, obito pelo agravo, obito por outra causa)",
    "DT_OBITO": "Data do obito",
    "HOSPITALIZ": "Houve hospitalizacao",
}


def perfil_colunas(df: pd.DataFrame, n_exemplos: int = 3) -> pd.DataFrame:
    linhas = []
    for col in df.columns:
        s = df[col]
        exemplos = s.dropna().astype(str).unique()[:n_exemplos]
        linhas.append({
            "variavel": col,
            "tipo_pandas": str(s.dtype),
            "pct_nulos": round(100 * s.isna().mean(), 2),
            "n_unicos": s.nunique(dropna=True),
            "exemplos": ", ".join(exemplos),
            "descricao": DESCRICOES_SINAN.get(str(col).upper(), "PREENCHER"),
        })
    return pd.DataFrame(linhas)


def salvar_markdown(perfil: pd.DataFrame, caminho: Path, titulo: str, fonte: str) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    cab = ["variavel", "tipo_pandas", "pct_nulos", "n_unicos", "exemplos", "descricao"]
    linhas = [f"## {titulo}", "", f"Fonte: {fonte}", "",
              "| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for _, r in perfil.iterrows():
        linhas.append("| " + " | ".join(str(r[c]).replace("|", "/") for c in cab) + " |")
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
