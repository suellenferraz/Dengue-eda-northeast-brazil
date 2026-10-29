---
name: coleta
description: Coleta das fontes do projeto (notificações de dengue do SINAN por CSV anual ou API, população e localidades do IBGE). Use ao mexer em src/coleta/, nos notebooks 01_coleta_dengue e 03_coleta_ibge, ou em arquivos de data/raw/.
---

# Coleta

Referência das fontes (URLs, parâmetros, formatos, comportamento verificado): `.claude/specs/01_fontes.md`.

## Scripts
| Script | Comando | Saída |
|---|---|---|
| `src/coleta/dengue/coleta_dengue_csv.py` | `--anos INI FIM [--refazer]`; `--comparar` (colunas por ano) | `data/raw/dengue_csv/ano=AAAA/DENGBR{aa}.csv(.zip)` |
| `src/coleta/dengue/coleta_dengue_api.py` | `--anos INI FIM [--max-paginas N]`; `--probe` | `data/raw/dengue_api/ano=AAAA/dengue.jsonl` |
| `src/coleta/ibge/coleta_ibge.py` | sem argumentos | `data/raw/ibge/populacao_municipios_ne.csv`, `data/raw/ibge/{UF}/{municipio}.csv` |

## Regras
- Notebooks de coleta (01, 03) baixam os arquivos quando executados (o CSV e o IBGE pulam o que já existe; a coleta
  completa da API fica desligada, porque leva dias). Notebooks de análise e limpeza (05 em diante) leem só do banco.
- O dado bruto vai para `data/raw/` como veio da fonte, sem filtro e sem limpeza; `data/` não é versionado.
- Dengue: coleta do **Brasil inteiro** (o recorte do Nordeste é feito na limpeza, por residência).
- Toda coleta é retomável ou pula o que já existe; arquivo em andamento usa `.part` e só é renomeado no fim.
- API: `offset` conta registros; erro temporário (429, 5xx, timeout) tem 6 tentativas com espera; o progresso fica em
  `dengue.estado.json` (offset e bytes do `.part`). Nunca rode dois processos no mesmo ano.
- Teste mudanças com um piloto (`--anos 2026 2026`, e na API `--max-paginas 3`) antes da coleta completa.
- Se a fonte se comportar diferente de `01_fontes.md`, teste de novo e atualize a spec.

## Estilo de código (`src/`)
Sem texto no topo do arquivo nem títulos de seção; imports juntos; uma linha em branco entre funções; docstring curta em
toda função; identificadores em português sem acento; caminhos e período em `src/config.py`.
