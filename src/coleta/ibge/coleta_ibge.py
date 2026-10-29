from __future__ import annotations
import argparse
import re
import sys
import time
from pathlib import Path
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # pasta src/
from config import DATA_RAW, N_MUNICIPIOS_NE, UFS_NORDESTE  # noqa: E402

SIDRA = "https://apisidra.ibge.gov.br/values"
DESTINO = DATA_RAW / "ibge"

TABELAS = [
    dict(nome="censo_2000_2010", tabela=200, variavel=93, periodos="2000,2010", extra="/c1/0/c2/0", prioridade=1),
    dict(nome="censo_2022", tabela=4714, variavel=93, periodos="2022", extra="", prioridade=1),
    dict(nome="estimativa_6579", tabela=6579, variavel=9324, periodos="all", extra="", prioridade=2),
]

def montar_url(tab: dict, cods_uf: list[int]) -> str:
    """Endereco da consulta ao SIDRA para uma tabela e UFs."""
    cods = ",".join(str(c) for c in cods_uf)
    return (f"{SIDRA}/t/{tab['tabela']}/n6/in n3 {cods}/v/{tab['variavel']}"
            f"/p/{tab['periodos']}{tab['extra']}")

def parsear_sidra(payload: list[dict], fonte: str, prioridade: int) -> pd.DataFrame:
    """Converte a resposta do SIDRA (1a linha = cabecalho) em DataFrame longo."""
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError(f"Resposta inesperada do SIDRA ({fonte}): {str(payload)[:300]}")
    cab, linhas = payload[0], payload[1:]
    col_mun = next(k for k, v in cab.items() if k.startswith("D") and k.endswith("C")
                   and str(v).lower().startswith("munic"))
    col_ano = next(k for k, v in cab.items() if k.startswith("D") and k.endswith("C")
                   and str(v).lower().startswith("ano"))
    col_nome = col_mun[:-1] + "N"   # D1C -> D1N, ex.: "Natal (RN)" ou "Natal - RN"
    df = pd.DataFrame({
        "cod_mun7": [str(l[col_mun]) for l in linhas],
        "municipio": [re.sub(r"( - [A-Z]{2}| \([A-Z]{2}\))$", "", str(l[col_nome])) for l in linhas],
        "ano": [int(l[col_ano]) for l in linhas],
        "populacao": pd.to_numeric([l["V"] for l in linhas], errors="coerce"),
    })
    df["fonte"] = fonte
    df["prioridade"] = prioridade
    return df

def baixar_tabela(tab: dict, cods_uf: list[int]) -> pd.DataFrame:
    """Baixa uma tabela do SIDRA, com novas tentativas em erro temporario."""
    url = montar_url(tab, cods_uf)
    for i in range(5):
        r = requests.get(url, timeout=120)
        if r.status_code == 200:
            return parsear_sidra(r.json(), tab["nome"], tab["prioridade"])
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** i)
            continue
        raise RuntimeError(f"HTTP {r.status_code} em {url}: {r.text[:200]}")
    raise RuntimeError(f"Falha ao baixar {url}")

def consolidar(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Une as fontes. Se (municipio, ano) aparece em mais de uma, vale a de menor prioridade (Censo)."""
    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["cod_mun7", "ano", "prioridade"]).drop_duplicates(["cod_mun7", "ano"], keep="first")
    df["cod_mun6"] = df["cod_mun7"].str[:6]
    df["uf_cod"] = df["cod_mun7"].str[:2].astype(int)
    # nome mais recente (alguns municipios mudaram de nome ao longo da serie)
    df["municipio"] = df.groupby("cod_mun7")["municipio"].transform("last")
    return df[["cod_mun7", "cod_mun6", "uf_cod", "municipio", "ano", "populacao", "fonte"]].reset_index(drop=True)

def salvar_por_municipio(df: pd.DataFrame) -> None:
    """Grava um CSV por municipio em DESTINO/{UF}/{municipio}.csv, com todos os anos."""
    sigla = {cod: uf for uf, cod in UFS_NORDESTE.items()}
    for (uf_cod, nome), grupo in df.groupby(["uf_cod", "municipio"]):
        pasta = DESTINO / sigla[uf_cod]
        pasta.mkdir(parents=True, exist_ok=True)
        grupo[["cod_mun7", "cod_mun6", "ano", "populacao", "fonte"]].to_csv(pasta / f"{nome}.csv", index=False)

def cobertura(df: pd.DataFrame) -> pd.DataFrame:
    """Municipios com populacao valida por ano. O esperado e N_MUNICIPIOS_NE em cada ano."""
    return (df.dropna(subset=["populacao"]).groupby("ano")["cod_mun7"].nunique()
            .rename("municipios").to_frame())

def main() -> None:
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    DESTINO.mkdir(parents=True, exist_ok=True)
    cods = list(UFS_NORDESTE.values())
    frames = []
    for tab in TABELAS:
        print(f"Baixando {tab['nome']} (tabela {tab['tabela']})...")
        # uma UF por vez evita estourar o limite de valores por requisicao do SIDRA
        partes = [baixar_tabela(tab, [c]) for c in cods]
        df = pd.concat(partes, ignore_index=True)
        print(f"  {len(df):,} linhas, anos {sorted(df['ano'].unique())}")
        frames.append(df)

    pop = consolidar(frames)
    saida = DESTINO / "populacao_municipios_ne.csv"
    pop.to_csv(saida, index=False)
    salvar_por_municipio(pop)

    cob = cobertura(pop)
    print(f"\nSalvo: {saida} ({len(pop):,} linhas)")
    print(f"Cobertura (esperado {N_MUNICIPIOS_NE} municipios por ano):")
    print(cob.to_string())
    faltando = cob[cob["municipios"] < N_MUNICIPIOS_NE]
    if len(faltando):
        print("\nAVISO: anos com cobertura incompleta:", list(faltando.index))
        print("Trate no notebook de limpeza (interpolacao entre censos/estimativas).")

if __name__ == "__main__":
    main()
