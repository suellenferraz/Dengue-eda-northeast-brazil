from __future__ import annotations
import argparse
import shutil
import sys
import time
import zipfile
from pathlib import Path
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # pasta src/
from config import ANO_FIM_COLETA, ANO_INICIO, DATA_RAW  # noqa: E402

URL = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Dengue/csv/DENGBR{aa}.csv.zip"
DESTINO = DATA_RAW / "dengue_csv"

def url_ano(ano: int) -> str:
    """Endereco do ZIP de um ano."""
    return URL.format(aa=f"{ano % 100:02d}")

def baixar(url: str, destino: Path, tentativas: int = 5) -> None:
    """Baixa em streaming para um .part e so renomeia no fim (arquivo final nunca fica pela metade)."""
    parcial = destino.with_suffix(destino.suffix + ".part")
    for i in range(tentativas):
        try:
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(parcial, "wb") as f:
                    for bloco in r.iter_content(chunk_size=1 << 20):
                        f.write(bloco)
            parcial.rename(destino)
            return
        except (requests.RequestException, OSError) as e:
            print(f"  tentativa {i + 1} falhou: {e!r}")
            time.sleep(min(2 ** i, 30))
    raise RuntimeError(f"Falha ao baixar {url}")

def coletar_ano(ano: int, refazer: bool = False) -> Path:
    """Baixa e extrai o CSV de um ano. Devolve o caminho do CSV."""
    pasta = DESTINO / f"ano={ano}"
    pasta.mkdir(parents=True, exist_ok=True)
    url = url_ano(ano)
    zip_ = pasta / url.rsplit("/", 1)[1]
    if refazer or not zip_.exists():
        baixar(url, zip_)
    with zipfile.ZipFile(zip_) as z:
        membro = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        csv = pasta / Path(membro).name
        if refazer or not csv.exists():
            with z.open(membro) as origem, open(csv, "wb") as f:
                shutil.copyfileobj(origem, f)
    return csv

def colunas_ano(ano: int) -> list[str]:
    """Cabecalho do CSV de um ano, lido direto do ZIP."""
    zip_ = DESTINO / f"ano={ano}" / url_ano(ano).rsplit("/", 1)[1]
    with zipfile.ZipFile(zip_) as z:
        membro = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(membro) as f:
            cabecalho = f.readline().decode("latin-1").strip()
    sep = ";" if cabecalho.count(";") > cabecalho.count(",") else ","
    return [c.strip().strip('"').upper() for c in cabecalho.split(sep)]

def comparar_colunas(anos: range) -> pd.DataFrame:
    """Matriz coluna x ano (True = a coluna existe naquele ano)."""
    presenca = {ano: set(colunas_ano(ano)) for ano in anos}
    todas = sorted(set().union(*presenca.values()))
    return pd.DataFrame({ano: [c in cols for c in todas] for ano, cols in presenca.items()}, index=todas)

def resumir_mudancas(matriz: pd.DataFrame) -> pd.DataFrame:
    """Para cada ano, quantas colunas tem e o que entrou/saiu em relacao ao ano anterior."""
    linhas, anterior = [], None
    for ano in matriz.columns:
        atual = set(matriz.index[matriz[ano]])
        entrou = sorted(atual - anterior) if anterior is not None else []
        saiu = sorted(anterior - atual) if anterior is not None else []
        linhas.append({"ano": ano, "colunas": len(atual), "entraram": entrou, "sairam": saiu})
        anterior = atual
    return pd.DataFrame(linhas).set_index("ano")

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--anos", nargs=2, type=int, default=[ANO_INICIO, ANO_FIM_COLETA], metavar=("INI", "FIM"))
    ap.add_argument("--refazer", action="store_true", help="baixa e extrai de novo, mesmo se ja existir")
    ap.add_argument("--comparar", action="store_true", help="so compara as colunas dos anos ja baixados")
    a = ap.parse_args()
    anos = range(a.anos[0], a.anos[1] + 1)

    if a.comparar:
        pd.set_option("display.max_colwidth", 200, "display.width", 250)
        print(resumir_mudancas(comparar_colunas(anos)).to_string())
        return
    for ano in anos:
        t0 = time.time()
        csv = coletar_ano(ano, refazer=a.refazer)
        print(f"ano={ano}: {csv.name} ({csv.stat().st_size / 1e6:,.0f} MB, {time.time() - t0:.0f}s)", flush=True)

if __name__ == "__main__":
    main()
