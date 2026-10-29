from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path
import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # pasta src/
from config import BANCO  # noqa: E402

TABELA = """
CREATE TABLE notificacao_dengue_ne (
    id                    bigint   GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cod_mun7              char(7)  NOT NULL REFERENCES municipio (cod_mun7),  -- residencia
    cod_mun7_notificacao  char(7)  REFERENCES municipio (cod_mun7),
    ano                   smallint NOT NULL,                                 -- ano da notificacao
    dt_notificacao        date,
    dt_sintomas           date,
    mes_sintomas          smallint,
    sexo                  char(1),                                           -- M ou F
    idade_anos            smallint,
    classificacao         text,
    criterio              text,
    evolucao              text,
    caso_provavel         boolean  NOT NULL,                                 -- tudo menos descartado (5)
    caso_confirmado       boolean  NOT NULL,                                 -- 1 a 4 ou 10 a 12
    possivel_duplicata    boolean  NOT NULL,
    ano_arquivo           smallint NOT NULL
)
"""

# Regras documentadas em .claude/specs/02_banco.md (tabela notificacao_dengue_ne).
PREENCHER = r"""
INSERT INTO notificacao_dengue_ne (
    cod_mun7, cod_mun7_notificacao, ano, dt_notificacao, dt_sintomas, mes_sintomas, sexo, idade_anos,
    classificacao, criterio, evolucao, caso_provavel, caso_confirmado, possivel_duplicata, ano_arquivo)
WITH base AS (
    SELECT m.cod_mun7,
           mn.cod_mun7 AS cod_mun7_notificacao,
           CASE WHEN s.nu_ano ~ '^\d{4}$' AND s.nu_ano::int BETWEEN 1999 AND 2026
                THEN s.nu_ano::smallint ELSE s.ano_arquivo END AS ano,
           CASE WHEN pg_input_is_valid(s.dt_notific, 'date') THEN s.dt_notific::date END AS dt_notificacao,
           CASE WHEN pg_input_is_valid(s.dt_sin_pri, 'date') THEN s.dt_sin_pri::date END AS dt_sin_bruta,
           CASE WHEN s.cs_sexo IN ('M', 'F') THEN s.cs_sexo END AS sexo,
           regexp_replace(coalesce(s.nu_idade_n, s.nu_idade), '\.0$', '') AS idade_cod,
           coalesce(s.classi_fin, s.con_classi) AS classificacao,
           coalesce(s.criterio, s.con_criter) AS criterio,
           coalesce(s.evolucao, s.con_evoluc) AS evolucao,
           row_number() OVER (
               PARTITION BY s.ano_arquivo, s.id_municip, s.id_unidade, s.dt_notific, s.dt_sin_pri, s.cs_sexo,
                            coalesce(s.nu_idade_n, s.nu_idade), s.id_mn_resi
               ORDER BY s.dt_digita NULLS LAST) AS ordem_no_grupo,
           s.ano_arquivo
    FROM sinan_dengue s
    JOIN municipio m       ON m.cod_mun6 = left(s.id_mn_resi, 6) AND m.uf_cod BETWEEN 21 AND 29
    LEFT JOIN municipio mn ON mn.cod_mun6 = left(s.id_municip, 6)
)
SELECT cod_mun7, cod_mun7_notificacao, ano, dt_notificacao,
       sintomas.dt_sintomas,
       extract(month FROM sintomas.dt_sintomas)::smallint,
       sexo,
       CASE WHEN idade_cod ~ '^[A4]\d{3}$' AND substr(idade_cod, 2)::int <= 110 THEN substr(idade_cod, 2)::smallint
            WHEN idade_cod ~ '^[MD321]\d{3}$' THEN 0 END,
       classificacao, criterio, evolucao,
       classificacao IS DISTINCT FROM '5',
       coalesce(classificacao IN ('1', '2', '3', '4', '10', '11', '12'), false),
       ordem_no_grupo > 1,
       ano_arquivo
FROM base,
LATERAL (SELECT CASE WHEN dt_notificacao IS NULL
                       OR dt_sin_bruta BETWEEN dt_notificacao - 365 AND dt_notificacao
                     THEN dt_sin_bruta END AS dt_sintomas) sintomas
"""

def criar() -> int:
    """Recria notificacao_dengue_ne a partir de sinan_dengue numa unica transacao; devolve o numero de linhas."""
    with psycopg.connect(**BANCO) as con, con.transaction():
        con.execute("DROP TABLE IF EXISTS notificacao_dengue_ne")
        con.execute(TABELA)
        linhas = con.execute(PREENCHER).rowcount
        con.execute("CREATE INDEX ON notificacao_dengue_ne (ano)")
        con.execute("CREATE INDEX ON notificacao_dengue_ne (cod_mun7)")
    with psycopg.connect(**BANCO, autocommit=True) as con:
        con.execute("ANALYZE notificacao_dengue_ne")
    return linhas

def main() -> None:
    argparse.ArgumentParser(description="Cria a tabela tratada notificacao_dengue_ne.").parse_args()
    t0 = time.time()
    print(f"notificacao_dengue_ne: {criar():,} linhas ({time.time() - t0:.0f}s)")

if __name__ == "__main__":
    main()
