# Dengue no Nordeste do Brasil (2000 a 2025)

Análise exploratória da incidência e da distribuição espaço-temporal da dengue nos estados do Nordeste, identificando
diferenças entre os estados e os períodos de maior ocorrência.
Projeto da disciplina IMD1151, Ciência de Dados, 2026.2.

## Fontes
| Dado | Fonte |
|---|---|
| Notificações de dengue (SINAN) | Ministério da Saúde: CSV anual do OpenDataSUS (https://dados.gov.br/dados/conjuntos-dados/arboviroses-dengue) ou API Dados Abertos (https://apidadosabertos.saude.gov.br/v1/) |
| População por município | IBGE, API SIDRA (https://sidra.ibge.gov.br) |
| Estados e municípios | IBGE, API de Localidades (https://servicodados.ibge.gov.br/api/docs) |

Detalhes (formatos, parâmetros, comparação entre CSV e API): `.claude/specs/01_fontes.md`.

## Pipeline
```
coleta (data/raw/)  →  carga (Postgres, camada bruta)  →  limpeza (camada tratada)  →  EDA
```

| Etapa | Notebook | Resultado |
|---|---|---|
| Coleta da dengue | `01_coleta_dengue` | CSVs anuais em `data/raw/dengue_csv/` (Brasil, 2000 a 2026) |
| Carga da dengue | `02_carga_dengue` | tabela `sinan_dengue` (bruta, 32,5 milhões de notificações) |
| Coleta do IBGE | `03_coleta_ibge` | população por município em `data/raw/ibge/` |
| Carga do IBGE | `04_carga_ibge` | tabelas `populacao_ne`, `estado`, `municipio`, `populacao_municipio_ano` |
| Análise do bruto | `05_analise` | qualidade dos dados e regras de limpeza |
| Limpeza | `06_limpeza` | tabela `notificacao_dengue_ne` (residentes do Nordeste, 5,6 milhões) |
| EDA | a fazer | incidência por estado e período |

Tabelas e colunas: `.claude/specs/02_banco.md`. Decisões de análise: `.claude/specs/03_decisoes.md`.

## Como rodar
Requisitos: Python 3.10+ e PostgreSQL com um banco criado (ex.: `dengue-eda`).

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # preencha com os dados do seu Postgres

# coleta
python src/coleta/dengue/coleta_dengue_csv.py --anos 2000 2026   # notificações (minutos, ~900 MB)
python src/coleta/ibge/coleta_ibge.py                            # população

# carga e limpeza
python src/carga/dengue/carga_dengue.py --anos 2000 2026          # sinan_dengue (~5 min)
python src/carga/ibge/carga_ibge.py                               # tabelas do IBGE
python src/limpeza/dengue/limpeza_dengue.py                       # notificacao_dengue_ne (~3 min)
```
Os mesmos passos estão nos notebooks, com explicações e conferências. Os notebooks de coleta e carga (01 a 04)
baixam e carregam os arquivos; os de análise e limpeza (05 em diante) leem só do banco. Depois da carga, os arquivos
de `data/` podem ser apagados e baixados de novo quando precisar. A coleta pela API
(`src/coleta/dengue/coleta_dengue_api.py`) é uma alternativa ao CSV: traz as mesmas notificações, mas leva dias.

## Estrutura
```
src/
  coleta/dengue/     coleta da dengue: CSV anual e API
  coleta/ibge/       coleta da população
  carga/dengue/      carga da dengue no Postgres
  carga/ibge/        carga da população, estados e municípios
  limpeza/dengue/    tabela tratada das notificações do Nordeste
  config.py          caminhos, período e conexão com o banco (lida do .env)
  dicionario.py      perfil das colunas para o dicionário de dados
notebooks/           01 a 06, na ordem do pipeline
data/                dados brutos baixados (não versionado; pode ser apagado depois da carga)
.claude/specs/       00_projeto, 01_fontes, 02_banco, 03_decisoes, 99_uso_ia
.claude/skills/      coleta, carga, limpeza, eda, registro-ia, welcome (instruções para o assistente de IA)
.env.example         modelo do arquivo de acesso ao banco
```

## Uso de IA
No Claude Code, digite `/welcome`. Com outra IA, peça para ler `.claude/specs/` e `.claude/skills/`.
Registre todo uso em `.claude/specs/99_uso_ia.md` (exigência da disciplina).
