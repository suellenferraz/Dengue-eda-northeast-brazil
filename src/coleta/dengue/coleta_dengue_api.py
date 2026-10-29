"""Coleta de notificacoes de dengue via API de Dados Abertos do Ministerio da Saude.

Swagger: https://apidadosabertos.saude.gov.br/v1/  (secao "Agravo Arboviroses")

ATENCAO: os nomes de parametros abaixo (limit, offset, nu_ano, ...) sao PALPITES e
precisam ser confirmados no Swagger e com `python src/coleta_dengue_api.py --probe`.
Ajuste as constantes ou use as variaveis de ambiente indicadas.

Caracteristicas:
- paginacao por limit/offset
- uma particao por (ano, UF) gravada em JSON Lines, em data/raw/dengue_api/
- retomavel: se cair no meio, rode de novo e ele continua de onde parou
- retry com backoff para erros temporarios (429, 5xx, timeout)

Uso:
    python src/coleta_dengue_api.py --probe
    python src/coleta_dengue_api.py --anos 2023 2023 --ufs RN --max-paginas 3
    python src/coleta_dengue_api.py --anos 2000 2025
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import ANO_FIM, ANO_INICIO, DATA_RAW, UFS_NORDESTE  # noqa: E402

# ---------------------------------------------------------------------------
# CONFIGURACAO DA API (confirmar no Swagger)
# ---------------------------------------------------------------------------
BASE_URL = os.getenv("DENGUE_API_BASE", "https://apidadosabertos.saude.gov.br")
ENDPOINT = "/arboviroses/dengue"
PARAM_LIMIT = "limit"
PARAM_OFFSET = "offset"
PARAM_ANO = "nu_ano"          # parametro de filtro por ano
PARAM_UF = "sg_uf"            # parametro de filtro por UF; use None se a API nao tiver
PAGE_SIZE = int(os.getenv("DENGUE_PAGE_SIZE", "20"))   # confirmar o maximo aceito
PAUSA_S = float(os.getenv("DENGUE_PAUSA_S", "0.2"))    # pausa entre requisicoes

URL = BASE_URL.rstrip("/") + ENDPOINT
DESTINO = DATA_RAW / "dengue_api"


def _sessao() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Accept": "application/json", "User-Agent": "eda-dengue-ne/0.1"})
    return s


def get_json(sessao: requests.Session, params: dict, tentativas: int = 6):
    """GET com retry/backoff. Levanta RuntimeError se esgotar as tentativas."""
    ultimo_erro = None
    for i in range(tentativas):
        try:
            r = sessao.get(URL, params=params, timeout=60)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                ultimo_erro = f"HTTP {r.status_code}"
            else:
                raise RuntimeError(f"HTTP {r.status_code} em {r.url}: {r.text[:200]}")
        except (requests.ConnectionError, requests.Timeout, ValueError) as e:
            ultimo_erro = repr(e)
        time.sleep(min(2 ** i, 30))
    raise RuntimeError(f"Falha apos {tentativas} tentativas ({ultimo_erro}) params={params}")


def extrair_registros(payload) -> list[dict]:
    """Aceita lista direta ou dict com uma lista de registros em alguma chave."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for valor in payload.values():
            if isinstance(valor, list) and (not valor or isinstance(valor[0], dict)):
                return valor
    return []


# ---------------------------------------------------------------------------
# DIAGNOSTICO
# ---------------------------------------------------------------------------
def probe(page_size: int = 5) -> list[dict]:
    """Busca poucos registros sem filtros e mostra formato, campos e latencia."""
    sessao = _sessao()
    t0 = time.time()
    payload = get_json(sessao, {PARAM_LIMIT: page_size, PARAM_OFFSET: 0})
    dt = time.time() - t0
    regs = extrair_registros(payload)
    print(f"URL: {URL}")
    print(f"Latencia: {dt:.2f}s | tipo da resposta: {type(payload).__name__}")
    if isinstance(payload, dict):
        print("Chaves de topo:", list(payload.keys()))
    print(f"Registros recebidos: {len(regs)} (pedido: {page_size})")
    if regs:
        print("Campos:", sorted(regs[0].keys()))
        print("Exemplo:", json.dumps(regs[0], ensure_ascii=False)[:600])
    return regs


def testar_filtro(param: str, valor, campo_resposta: str, page_size: int = 20) -> float:
    """Pede registros com `param=valor` e devolve a fracao em que `campo_resposta == valor`.

    ~1.0 significa que o filtro funciona. Valor baixo significa que a API ignora o parametro
    (ou que o nome do campo na resposta e outro).
    """
    sessao = _sessao()
    payload = get_json(sessao, {PARAM_LIMIT: page_size, PARAM_OFFSET: 0, param: valor})
    regs = extrair_registros(payload)
    if not regs:
        print(f"{param}={valor}: nenhum registro retornado")
        return 0.0
    if campo_resposta not in regs[0]:
        print(f"Campo '{campo_resposta}' nao existe. Campos: {sorted(regs[0])}")
        return 0.0
    ok = sum(str(r.get(campo_resposta)) == str(valor) for r in regs)
    frac = ok / len(regs)
    print(f"{param}={valor}: {ok}/{len(regs)} registros com {campo_resposta}=={valor} ({frac:.0%})")
    return frac


def estimar_requisicoes(n_linhas: int, page_size: int = PAGE_SIZE, seg_por_req: float = 0.5) -> str:
    n_req = -(-n_linhas // page_size)
    horas = n_req * (seg_por_req + PAUSA_S) / 3600
    return f"{n_linhas:,} linhas -> {n_req:,} requisicoes -> ~{horas:.1f} h (seg/req={seg_por_req})"


# ---------------------------------------------------------------------------
# COLETA
# ---------------------------------------------------------------------------
def coletar_particao(sessao, ano: int, uf: str | None, page_size: int = PAGE_SIZE,
                     pausa: float = PAUSA_S, max_paginas: int | None = None) -> Path:
    """Baixa uma particao (ano, uf). Retomavel. Devolve o caminho do arquivo final."""
    nome = f"uf={uf or 'ALL'}"
    pasta = DESTINO / f"ano={ano}"
    pasta.mkdir(parents=True, exist_ok=True)
    final = pasta / f"{nome}.jsonl"
    parcial = pasta / f"{nome}.part"
    if final.exists():
        return final

    offset = 0
    if parcial.exists():
        with open(parcial, encoding="utf-8") as f:
            offset = sum(1 for _ in f)

    paginas = 0
    terminou = False
    with open(parcial, "a", encoding="utf-8") as f:
        while True:
            params = {PARAM_LIMIT: page_size, PARAM_OFFSET: offset, PARAM_ANO: ano}
            if PARAM_UF and uf:
                params[PARAM_UF] = uf
            regs = extrair_registros(get_json(sessao, params))
            if not regs:
                terminou = True
                break
            for r in regs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            offset += len(regs)
            paginas += 1
            if max_paginas and paginas >= max_paginas:
                break
            time.sleep(pausa)

    if terminou:
        parcial.rename(final)
        return final
    print(f"[parcial] ano={ano} uf={uf}: {offset} linhas (limitado por max_paginas)")
    return parcial


def coletar(anos: range, ufs: list[str], **kw) -> None:
    sessao = _sessao()
    particoes_uf = ufs if PARAM_UF else [None]
    total = len(anos) * len(particoes_uf)
    n = 0
    for ano in anos:
        for uf in particoes_uf:
            n += 1
            t0 = time.time()
            caminho = coletar_particao(sessao, ano, uf, **kw)
            linhas = sum(1 for _ in open(caminho, encoding="utf-8"))
            print(f"[{n}/{total}] ano={ano} uf={uf or 'ALL'}: {linhas:,} linhas ({time.time()-t0:.0f}s)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe", action="store_true", help="so diagnostica a API e sai")
    ap.add_argument("--anos", nargs=2, type=int, default=[ANO_INICIO, ANO_FIM], metavar=("INI", "FIM"))
    ap.add_argument("--ufs", nargs="+", default=list(UFS_NORDESTE))
    ap.add_argument("--page-size", type=int, default=PAGE_SIZE)
    ap.add_argument("--pausa", type=float, default=PAUSA_S)
    ap.add_argument("--max-paginas", type=int, default=None, help="limite para testes")
    a = ap.parse_args()

    if a.probe:
        probe()
        return
    coletar(range(a.anos[0], a.anos[1] + 1), a.ufs, page_size=a.page_size,
            pausa=a.pausa, max_paginas=a.max_paginas)


if __name__ == "__main__":
    main()
