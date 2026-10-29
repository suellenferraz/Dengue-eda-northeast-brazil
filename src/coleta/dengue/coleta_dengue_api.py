from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # pasta src/
from config import ANO_FIM_COLETA, ANO_INICIO, DATA_RAW  # noqa: E402

URL = "https://apidadosabertos.saude.gov.br/arboviroses/dengue"
PARAM_ANO = "nu_ano"
PAGE_SIZE = 1000   # maximo aceito pela API
PAUSA_S = 0.2      # pausa entre requisicoes
DESTINO = DATA_RAW / "dengue_api"

def _sessao() -> requests.Session:
    """Sessao HTTP com os cabecalhos da coleta."""
    s = requests.Session()
    s.headers.update({"Accept": "application/json", "User-Agent": "eda-dengue-ne/0.1"})
    return s

def buscar_pagina(sessao: requests.Session, params: dict, tentativas: int = 6) -> list[dict]:
    """GET com retry/backoff para erros temporarios (429, 5xx, timeout). Devolve a lista de registros."""
    ultimo_erro = None
    for i in range(tentativas):
        try:
            r = sessao.get(URL, params=params, timeout=60)
            if r.status_code == 200:
                return r.json()["dengue"]
            if r.status_code not in (429, 500, 502, 503, 504):
                raise RuntimeError(f"HTTP {r.status_code} em {r.url}: {r.text[:200]}")
            ultimo_erro = f"HTTP {r.status_code}"
        except (requests.ConnectionError, requests.Timeout, ValueError) as e:
            ultimo_erro = repr(e)
        time.sleep(min(2 ** i, 30))
    raise RuntimeError(f"Falha apos {tentativas} tentativas ({ultimo_erro}) params={params}")

def probe(page_size: int = 5) -> list[dict]:
    """Busca poucos registros e mostra latencia, campos e um exemplo."""
    t0 = time.time()
    regs = buscar_pagina(_sessao(), {"limit": page_size, "offset": 0})
    print(f"URL: {URL} | latencia: {time.time() - t0:.2f}s | registros: {len(regs)}")
    if regs:
        print("Campos:", sorted(regs[0]))
        print("Exemplo:", json.dumps(regs[0], ensure_ascii=False)[:600])
    return regs

def testar_filtro(param: str, valor, campo_resposta: str, page_size: int = 20) -> float:
    """Fracao dos registros com `campo_resposta == valor` ao filtrar por `param=valor` (~1.0 = filtro funciona)."""
    regs = buscar_pagina(_sessao(), {"limit": page_size, "offset": 0, param: valor})
    if not regs:
        print(f"{param}={valor}: nenhum registro retornado")
        return 0.0
    ok = sum(str(r.get(campo_resposta)) == str(valor) for r in regs)
    print(f"{param}={valor}: {ok}/{len(regs)} registros com {campo_resposta}=={valor} ({ok / len(regs):.0%})")
    return ok / len(regs)

def estimar_requisicoes(n_linhas: int, page_size: int = PAGE_SIZE, seg_por_req: float = 0.5) -> str:
    """Estima requisicoes e horas para baixar n_linhas registros."""
    n_req = -(-n_linhas // page_size)
    horas = n_req * (seg_por_req + PAUSA_S) / 3600
    return f"{n_linhas:,} linhas -> {n_req:,} requisicoes -> ~{horas:.1f} h (seg/req={seg_por_req})"

def coletar_particao(sessao, ano: int, page_size: int = PAGE_SIZE,
                     pausa: float = PAUSA_S, max_paginas: int | None = None) -> Path:
    """Baixa um ano inteiro. Retomavel.

    Depois de cada pagina gravada, o estado guarda o offset e o tamanho do .part. Ao retomar,
    o .part e cortado nesse tamanho, descartando uma pagina gravada pela metade.
    """
    pasta = DESTINO / f"ano={ano}"
    pasta.mkdir(parents=True, exist_ok=True)
    final = pasta / "dengue.jsonl"
    parcial = pasta / "dengue.part"
    estado = pasta / "dengue.estado.json"
    if final.exists():
        return final

    offset, tamanho = 0, 0
    if estado.exists() and parcial.exists():
        e = json.loads(estado.read_text())
        offset, tamanho = e["offset"], e["bytes"]

    with open(parcial, "ab") as f:
        f.truncate(tamanho)
        for _ in range(max_paginas or sys.maxsize):
            regs = buscar_pagina(sessao, {"limit": page_size, "offset": offset, PARAM_ANO: ano})
            if not regs:
                break
            f.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in regs).encode("utf-8"))
            f.flush()
            offset += len(regs)
            estado.write_text(json.dumps({"offset": offset, "bytes": f.tell()}))
            time.sleep(pausa)
        else:
            print(f"[parcial] ano={ano}: {offset:,} registros (limitado por max_paginas)")
            return parcial

    parcial.rename(final)
    estado.unlink(missing_ok=True)
    return final

def contar_linhas(caminho: Path) -> int:
    """Numero de linhas de um arquivo."""
    with open(caminho, encoding="utf-8") as f:
        return sum(1 for _ in f)

def coletar(anos: range, **kw) -> None:
    """Coleta os anos pedidos, um de cada vez."""
    sessao = _sessao()
    for n, ano in enumerate(anos, start=1):
        t0 = time.time()
        caminho = coletar_particao(sessao, ano, **kw)
        print(f"[{n}/{len(anos)}] ano={ano}: {contar_linhas(caminho):,} linhas ({time.time() - t0:.0f}s)")

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe", action="store_true", help="so diagnostica a API e sai")
    ap.add_argument("--anos", nargs=2, type=int, default=[ANO_INICIO, ANO_FIM_COLETA], metavar=("INI", "FIM"))
    ap.add_argument("--pausa", type=float, default=PAUSA_S)
    ap.add_argument("--max-paginas", type=int, default=None, help="limite para testes")
    a = ap.parse_args()

    if a.probe:
        probe()
        return
    coletar(range(a.anos[0], a.anos[1] + 1), pausa=a.pausa, max_paginas=a.max_paginas)

if __name__ == "__main__":
    main()
