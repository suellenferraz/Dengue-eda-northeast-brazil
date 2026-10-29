from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path
import psycopg
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # pasta src/
from coleta.dengue import coleta_dengue_csv as dengue_csv  # noqa: E402
from config import ANO_FIM_COLETA, ANO_INICIO, BANCO  # noqa: E402

TABELA = "sinan_dengue"            # uma linha por notificacao, uma particao por ano
CONTROLE = "sinan_dengue_carga"    # uma linha por ano carregado

def colunas_todos_os_anos(anos: range) -> list[str]:
    """Junta as colunas dos CSVs de todos os anos, em minusculas."""
    colunas: list[str] = []
    for ano in anos:
        for c in dengue_csv.colunas_ano(ano):
            if c.lower() not in colunas:
                colunas.append(c.lower())
    return colunas

def criar_tabelas(con: psycopg.Connection, colunas: list[str]) -> None:
    """Cria sinan_dengue e sinan_dengue_carga, se ainda nao existirem."""
    definicao = sql.SQL(", ").join(sql.SQL("{} text").format(sql.Identifier(c)) for c in colunas)
    con.execute(sql.SQL(
        "CREATE TABLE IF NOT EXISTS {} (ano_arquivo smallint NOT NULL, {}) PARTITION BY LIST (ano_arquivo)"
    ).format(sql.Identifier(TABELA), definicao))
    con.execute(sql.SQL("""
        CREATE TABLE IF NOT EXISTS {} (
            ano_arquivo  smallint    PRIMARY KEY,
            arquivo      text        NOT NULL,
            linhas       bigint      NOT NULL,
            bytes_nulos  integer     NOT NULL DEFAULT 0,
            carregado_em timestamptz NOT NULL DEFAULT now()
        )""").format(sql.Identifier(CONTROLE)))

def anos_carregados(con: psycopg.Connection) -> dict[int, int]:
    """Anos ja carregados e o numero de linhas de cada um."""
    consulta = sql.SQL("SELECT ano_arquivo, linhas FROM {}").format(sql.Identifier(CONTROLE))
    return dict(con.execute(consulta).fetchall())

def carregar_ano(con: psycopg.Connection, ano: int) -> int:
    """Carrega um ano (substitui o que havia); devolve o numero de linhas.

    Tudo numa transacao: se der erro, o ano fica como estava. Bytes nulos (0x00) sao removidos,
    porque o Postgres nao aceita esse caractere em texto.
    """
    csv = dengue_csv.DESTINO / f"ano={ano}" / f"DENGBR{ano % 100:02d}.csv"
    particao = sql.Identifier(f"{TABELA}_{ano}")
    colunas = sql.SQL(", ").join(sql.Identifier(c.lower()) for c in dengue_csv.colunas_ano(ano))
    copiar = sql.SQL("COPY {} ({}) FROM STDIN (FORMAT csv, HEADER true)").format(particao, colunas)

    with con.transaction():
        con.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {} PARTITION OF {} FOR VALUES IN ({})").format(
            particao, sql.Identifier(TABELA), sql.Literal(ano)))
        con.execute(sql.SQL("ALTER TABLE {} ALTER COLUMN ano_arquivo SET DEFAULT {}").format(particao, sql.Literal(ano)))
        con.execute(sql.SQL("TRUNCATE {}").format(particao))

        nulos = 0
        with con.cursor() as cur:
            with cur.copy(copiar) as copia, open(csv, "rb") as f:
                while bloco := f.read(1 << 22):
                    nulos += bloco.count(b"\x00")
                    copia.write(bloco.replace(b"\x00", b""))
            linhas = cur.rowcount

        con.execute(sql.SQL("""
            INSERT INTO {} (ano_arquivo, arquivo, linhas, bytes_nulos) VALUES (%s, %s, %s, %s)
            ON CONFLICT (ano_arquivo) DO UPDATE
            SET arquivo = EXCLUDED.arquivo, linhas = EXCLUDED.linhas,
                bytes_nulos = EXCLUDED.bytes_nulos, carregado_em = now()""").format(sql.Identifier(CONTROLE)),
            (ano, csv.name, linhas, nulos))

    con.execute(sql.SQL("ANALYZE {}").format(particao))
    return linhas

def carregar(anos: range, refazer: bool = False) -> None:
    """Carrega os anos pedidos, pulando os ja carregados (a menos que refazer=True)."""
    # autocommit: cada ano e gravado (ou desfeito) na sua propria transacao, em carregar_ano
    with psycopg.connect(**BANCO, autocommit=True) as con:
        existe = con.execute("SELECT to_regclass(%s)", (CONTROLE,)).fetchone()[0]
        feitos = anos_carregados(con) if existe else {}
        pendentes = [ano for ano in anos if refazer or ano not in feitos]
        for ano in anos:
            if ano not in pendentes:
                print(f"ano={ano}: ja carregado ({feitos[ano]:,} linhas)", flush=True)
        if not pendentes:
            return
        # so le os CSVs (cabecalhos) quando ha ano para carregar
        criar_tabelas(con, colunas_todos_os_anos(range(ANO_INICIO, ANO_FIM_COLETA + 1)))
        for ano in pendentes:
            t0 = time.time()
            linhas = carregar_ano(con, ano)
            print(f"ano={ano}: {linhas:,} linhas ({time.time() - t0:.0f}s)", flush=True)

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--anos", nargs=2, type=int, default=[ANO_INICIO, ANO_FIM_COLETA], metavar=("INI", "FIM"))
    ap.add_argument("--refazer", action="store_true", help="carrega de novo anos ja carregados")
    a = ap.parse_args()
    carregar(range(a.anos[0], a.anos[1] + 1), refazer=a.refazer)

if __name__ == "__main__":
    main()
