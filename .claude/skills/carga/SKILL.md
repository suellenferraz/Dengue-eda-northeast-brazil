---
name: carga
description: Carga dos dados brutos no Postgres local (dengue em sinan_dengue; população, estados e municípios do IBGE). Use ao mexer em src/carga/, em src/config.py (BANCO), no .env, nos notebooks 02_carga_dengue e 04_carga_ibge, ou ao consultar as tabelas brutas e de apoio.
---

# Carga

Tabelas, colunas e relações: `.claude/specs/02_banco.md`.

## Conexão
- Postgres local, banco `dengue-eda`. Dados de acesso no `.env` da raiz (fora do git; modelo em `.env.example`):
  `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`.
- `src/config.py` lê o `.env` (`python-dotenv`) e expõe `BANCO`; conecte com `psycopg.connect(**BANCO)`.
- Nunca escreva usuário ou senha no código, nos notebooks ou nas specs.

## Scripts
| Script | Comando | Tabelas |
|---|---|---|
| `src/carga/dengue/carga_dengue.py` | `--anos INI FIM [--refazer]` | `sinan_dengue` (particionada por ano), `sinan_dengue_carga` |
| `src/carga/ibge/carga_ibge.py` | sem argumentos | `populacao_ne`, `estado`, `municipio`, `populacao_municipio_ano` |

## Regras
- Notebooks de carga (02, 04) leem os arquivos de `data/raw/`: rode a coleta antes. A carga da dengue só lê os CSVs
  quando há ano a carregar e falha antes de mexer no banco se faltar o arquivo.
- Carga com `COPY`. Cada ano da dengue numa transação própria (conexão com `autocommit=True` e `con.transaction()`
  por ano); o IBGE inteiro numa única transação. Erro no meio não deixa resíduo.
- Rodar de novo não duplica: a dengue pula anos registrados em `sinan_dengue_carga` (`--refazer` recarrega o ano);
  o IBGE esvazia e recarrega tudo.
- Camada bruta = dado como veio (dengue: tudo texto). Única alteração permitida: remover bytes 0x00, registrada em
  `sinan_dengue_carga.bytes_nulos`.
- Conferir depois de carregar: linhas por ano no banco = linhas do CSV; para o IBGE, 0 municípios da população sem
  cadastro em `municipio`.
