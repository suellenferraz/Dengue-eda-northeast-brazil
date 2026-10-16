"""Configuracao compartilhada do projeto (caminhos, periodo, UFs)."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATA_RAW = RAIZ / "data" / "raw"
DATA_PROCESSED = RAIZ / "data" / "processed"
DOCS = RAIZ / "docs"

ANO_INICIO = 2000
ANO_FIM = 2025

# Codigo IBGE de UF (2 primeiros digitos do codigo de municipio) por sigla.
UFS_NORDESTE = {
    "MA": 21, "PI": 22, "CE": 23, "RN": 24, "PB": 25,
    "PE": 26, "AL": 27, "SE": 28, "BA": 29,
}

# Numero de municipios do Nordeste (IBGE, 2022). Usado como checagem de cobertura.
N_MUNICIPIOS_NE = 1794

for _p in (DATA_RAW, DATA_PROCESSED, DOCS):
    _p.mkdir(parents=True, exist_ok=True)
