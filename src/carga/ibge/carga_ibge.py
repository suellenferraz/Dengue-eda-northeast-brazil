from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pandas as pd
import psycopg
import requests
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # pasta src/
from config import BANCO, DATA_RAW  # noqa: E402

LOCALIDADES = "https://servicodados.ibge.gov.br/api/v1/localidades"
ARQUIVO_POPULACAO = DATA_RAW / "ibge" / "populacao_municipios_ne.csv"

TABELAS = """
CREATE TABLE IF NOT EXISTS populacao_ne (            -- bruta: populacao como veio do IBGE
    cod_mun7   char(7)  NOT NULL,                    -- codigo IBGE do municipio (7 digitos)
    cod_mun6   char(6)  NOT NULL,                    -- sem digito verificador: juncao com a dengue
    uf_cod     smallint NOT NULL,
    municipio  text     NOT NULL,
    ano        smallint NOT NULL,
    populacao  integer,                              -- nulo quando o SIDRA nao tem o valor
    fonte      text     NOT NULL,                    -- censo_2000_2010, censo_2022 ou estimativa_6579
    PRIMARY KEY (cod_mun7, ano)
);
CREATE TABLE IF NOT EXISTS estado (                  -- apoio: os 27 estados
    uf_cod        smallint PRIMARY KEY,
    sigla         char(2)  NOT NULL UNIQUE,
    nome          text     NOT NULL,
    regiao_sigla  char(2)  NOT NULL,                 -- N, NE, SE, S, CO
    regiao        text     NOT NULL
);
CREATE TABLE IF NOT EXISTS municipio (               -- apoio: todos os municipios do Brasil
    cod_mun7              char(7)  PRIMARY KEY,
    cod_mun6              char(6)  NOT NULL UNIQUE,
    nome                  text     NOT NULL,
    uf_cod                smallint NOT NULL REFERENCES estado (uf_cod),
    microrregiao          text,                      -- divisao antiga (ate 2017)
    mesorregiao           text,
    regiao_imediata       text     NOT NULL,         -- divisao atual (desde 2017)
    regiao_intermediaria  text     NOT NULL
);
CREATE TABLE IF NOT EXISTS populacao_municipio_ano ( -- tratada: pronta para analise
    cod_mun7   char(7)  NOT NULL REFERENCES municipio (cod_mun7),
    ano        smallint NOT NULL,
    populacao  integer  NOT NULL,
    fonte      text     NOT NULL,                    -- censo_2000_2010, censo_2022, estimativa_6579 ou interpolada
    PRIMARY KEY (cod_mun7, ano)
);
"""

TRATADA = """
INSERT INTO populacao_municipio_ano (cod_mun7, ano, populacao, fonte)
SELECT cod_mun7, ano, populacao, fonte
FROM populacao_ne
WHERE populacao IS NOT NULL;

-- 2007 e 2023 nao existem no IBGE: media do ano anterior e do seguinte
INSERT INTO populacao_municipio_ano (cod_mun7, ano, populacao, fonte)
SELECT antes.cod_mun7, antes.ano + 1, round((antes.populacao + depois.populacao) / 2.0), 'interpolada'
FROM populacao_ne antes
JOIN populacao_ne depois ON depois.cod_mun7 = antes.cod_mun7 AND depois.ano = antes.ano + 2
WHERE antes.ano + 1 IN (2007, 2023)
  AND antes.populacao IS NOT NULL AND depois.populacao IS NOT NULL;
"""

def ler_populacao() -> pd.DataFrame:
    """Le o CSV da coleta do IBGE, com a populacao como inteiro."""
    pop = pd.read_csv(ARQUIVO_POPULACAO, dtype={"cod_mun7": str, "cod_mun6": str, "municipio": str, "fonte": str})
    pop["populacao"] = pop["populacao"].astype("Int64")
    return pop

def baixar_localidades() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Baixa estados e municipios da API de Localidades do IBGE."""
    estados = requests.get(f"{LOCALIDADES}/estados", timeout=120).json()
    municipios = requests.get(f"{LOCALIDADES}/municipios", timeout=120).json()
    estado = pd.DataFrame([{
        "uf_cod": e["id"], "sigla": e["sigla"], "nome": e["nome"],
        "regiao_sigla": e["regiao"]["sigla"], "regiao": e["regiao"]["nome"],
    } for e in estados]).sort_values("uf_cod")
    municipio = pd.DataFrame([linha_municipio(m) for m in municipios]).sort_values("cod_mun7")
    return estado, municipio

def linha_municipio(m: dict) -> dict:
    """Um municipio da API como linha da tabela (sem microrregiao para os criados depois de 2017)."""
    micro, imediata = m.get("microrregiao"), m["regiao-imediata"]
    return {
        "cod_mun7": str(m["id"]), "cod_mun6": str(m["id"])[:6], "nome": m["nome"],
        "uf_cod": imediata["regiao-intermediaria"]["UF"]["id"],
        "microrregiao": micro["nome"] if micro else None,
        "mesorregiao": micro["mesorregiao"]["nome"] if micro else None,
        "regiao_imediata": imediata["nome"],
        "regiao_intermediaria": imediata["regiao-intermediaria"]["nome"],
    }

def copiar(con: psycopg.Connection, tabela: str, df: pd.DataFrame) -> None:
    """Insere um DataFrame numa tabela com COPY (valores ausentes viram nulos)."""
    colunas = sql.SQL(", ").join(sql.Identifier(c) for c in df.columns)
    with con.cursor() as cur, cur.copy(sql.SQL("COPY {} ({}) FROM STDIN").format(sql.Identifier(tabela), colunas)) as cp:
        for linha in df.astype(object).where(df.notna(), None).itertuples(index=False):
            cp.write_row(linha)

def carregar() -> None:
    """Recria o conteudo das 4 tabelas numa unica transacao: se der erro, nada muda."""
    pop = ler_populacao()
    estado, municipio = baixar_localidades()
    with psycopg.connect(**BANCO) as con, con.transaction():
        con.execute(TABELAS)
        # municipio e estado sao referenciados pela tratada: esvazia tudo junto e recarrega na ordem
        con.execute("TRUNCATE populacao_municipio_ano, municipio, estado, populacao_ne")
        copiar(con, "populacao_ne", pop)
        copiar(con, "estado", estado)
        copiar(con, "municipio", municipio)
        con.execute(TRATADA)
    print(f"populacao_ne: {len(pop):,} | estado: {len(estado)} | municipio: {len(municipio):,}")

def main() -> None:
    argparse.ArgumentParser(description="Carga dos dados do IBGE no Postgres.").parse_args()
    carregar()

if __name__ == "__main__":
    main()
