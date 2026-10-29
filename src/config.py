import os
from pathlib import Path
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[1]
DATA_RAW = RAIZ / "data" / "raw"
DATA_PROCESSED = RAIZ / "data" / "processed"

ANO_INICIO = 2000
ANO_FIM = 2025          # periodo da analise
ANO_FIM_COLETA = 2026   # a coleta inclui 2026 (parcial, sujeito a revisao)

# Codigo IBGE de UF (2 primeiros digitos do codigo de municipio) por sigla.
UFS_NORDESTE = {
    "MA": 21, "PI": 22, "CE": 23, "RN": 24, "PB": 25,
    "PE": 26, "AL": 27, "SE": 28, "BA": 29,
}

# Numero de municipios do Nordeste (IBGE, 2022). Usado como checagem de cobertura.
N_MUNICIPIOS_NE = 1794

# Banco Postgres que recebe as cargas. Os dados de acesso ficam no .env (modelo em .env.example).
load_dotenv(RAIZ / ".env")

def _variavel(nome: str, padrao: str | None = None) -> str:
    """Le uma variavel do .env (ou do ambiente); sem padrao, ela e obrigatoria."""
    valor = os.getenv(nome, padrao)
    if valor is None:
        raise RuntimeError(f"Defina {nome} no arquivo .env (veja .env.example)")
    return valor

BANCO = {
    "host": _variavel("PGHOST", "localhost"),
    "port": int(_variavel("PGPORT", "5432")),
    "dbname": _variavel("PGDATABASE", "dengue-eda"),
    "user": _variavel("PGUSER"),
    "password": _variavel("PGPASSWORD"),
}

for _p in (DATA_RAW, DATA_PROCESSED):
    _p.mkdir(parents=True, exist_ok=True)
