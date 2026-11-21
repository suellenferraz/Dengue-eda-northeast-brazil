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
| EDA, P1 | `07_incidencia` | incidência por estado e ano; anos epidêmicos |
| EDA, P2 | `08_sazonalidade` | perfil por ano e mês dos sintomas, mês de maior ocorrência, mês central e comparação capital × interior nos mesmos anos |
| EDA, P3 | `09_municipios_atipicos` | municípios acima ou abaixo do esperado para o estado (funil) |
| EDA, P4 | `10_perfil_idade_sexo` | idade e sexo em anos epidêmicos e não epidêmicos |

Consulte o [mapa das perguntas e dos notebooks](.claude/specs/00_projeto.md#2-perguntas-de-pesquisa), as [limitações da análise](.claude/specs/00_projeto.md#6-limitações), o [dicionário do banco](.claude/specs/02_banco.md) e as [decisões metodológicas](.claude/specs/03_decisoes.md).

As versões do ambiente e as conferências realizadas estão no [registro da execução final](.claude/specs/04_execucao_final.md).

## Como rodar

Use Python 3.10+ e PostgreSQL 16+. A limpeza usa `pg_input_is_valid` para validar datas antes de convertê-las. O projeto requer pandas 2.1+ pelo uso de `DataFrame.map`. [Documentação do PostgreSQL 16](https://www.postgresql.org/docs/16/functions-info.html#FUNCTIONS-INFO-VALIDITY) · [Documentação do pandas 2.1](https://pandas.pydata.org/pandas-docs/version/2.1/reference/api/pandas.DataFrame.map.html)

Se a instância local já estiver configurada em `data/postgres-local/`, inicie-a na porta `5433` conforme o README dentro dessa pasta e mantenha o `.env` existente. Com as tabelas carregadas, siga direto para [os notebooks no JupyterLab](#3-execute-os-notebooks-no-jupyterlab).

### 1. Crie o banco

Com o servidor PostgreSQL em execução, rode o comando abaixo. O exemplo usa o usuário `postgres` e o banco `dengue-eda`, como em `.env.example`.

```bash
createdb -h localhost -p 5432 -U postgres dengue-eda
```

Se usar o pgAdmin, abra o Query Tool conectado ao banco `postgres` e execute `CREATE DATABASE "dengue-eda";`.

### 2. Prepare o ambiente e o `.env`

Na raiz do repositório, use os comandos do seu terminal.

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath '.env')) { Copy-Item .env.example .env }
```

**Linux ou macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
test -e .env || cp .env.example .env
```

Edite o `.env` na raiz do repositório. Informe o endereço (`PGHOST`) e a porta (`PGPORT`) do servidor, o nome do banco criado (`PGDATABASE`), o usuário com permissão para criar tabelas (`PGUSER`) e sua senha (`PGPASSWORD`).

### 3. Execute os notebooks no JupyterLab

Ainda na raiz, execute `.\.venv\Scripts\python.exe -m jupyterlab` no PowerShell ou `python -m jupyterlab` com o ambiente virtual ativado no Linux ou macOS. Abra o endereço exibido no terminal se o navegador não abrir automaticamente.

No JupyterLab, abra `notebooks/`, selecione o kernel Python do ambiente `.venv` e use **Run → Run All Cells** em cada notebook. Em um banco vazio, siga a ordem **01 → 02 → 03 → 04 → 05 → 06** da tabela do pipeline e aguarde cada notebook terminar. O `06_limpeza` cria a tabela tratada usada na EDA.

Com as tabelas tratadas de dengue e do IBGE prontas no banco, execute os notebooks principais da EDA nesta ordem:

1. [`07_incidencia.ipynb`](notebooks/07_incidencia.ipynb) — incidência por estado e ano.
2. [`08_sazonalidade.ipynb`](notebooks/08_sazonalidade.ipynb) — sazonalidade e comparação entre capital e interior.
3. [`09_municipios_atipicos.ipynb`](notebooks/09_municipios_atipicos.ipynb) — municípios com incidência fora do esperado.
4. [`10_perfil_idade_sexo.ipynb`](notebooks/10_perfil_idade_sexo.ipynb) — perfil por idade e sexo.

### Espaço em disco

- **Arquivos locais** — cerca de **9,1 GB** medidos em `data/raw/` na carga de 2000 a 2026, incluindo os ZIPs, os CSVs extraídos e os dados do IBGE.
- **PostgreSQL** — a instância local carregada ocupa cerca de **10,1 GB**. Reserve cerca de **15 GB livres** no disco do PostgreSQL para acomodar os temporários da carga e da limpeza.
- **Execução completa** — reserve cerca de **25 GB livres** se os arquivos e o PostgreSQL estiverem no mesmo disco. A estimativa inclui margem para o ambiente Python e para o espaço temporário durante a carga e a limpeza.

### Alternativa para coletar, carregar e limpar pelo terminal

Com o `.env` configurado e o ambiente virtual ativado, os comandos abaixo preparam o banco para os notebooks 07 a 10. No PowerShell, você também pode usar `.\.venv\Scripts\python.exe` no lugar de `python`.

```bash
# coleta
python src/coleta/dengue/coleta_dengue_csv.py --anos 2000 2026   # notificações
python src/coleta/ibge/coleta_ibge.py                            # população

# carga e limpeza
python src/carga/dengue/carga_dengue.py --anos 2000 2026          # sinan_dengue
python src/carga/ibge/carga_ibge.py                               # tabelas do IBGE
python src/limpeza/dengue/limpeza_dengue.py                       # notificacao_dengue_ne
```
Depois da carga, os arquivos baixados em `data/raw/` podem ser removidos e baixados de novo quando necessário. Preserve `data/postgres-local/` se tiver a instância local configurada nessa pasta. A coleta pela API
(`src/coleta/dengue/coleta_dengue_api.py`) é uma alternativa à coleta por CSV e pode levar dias.

## Estrutura
```
src/
  coleta/dengue/     coleta da dengue: CSV anual e API
  coleta/ibge/       coleta da população
  carga/dengue/      carga da dengue no Postgres
  carga/ibge/        carga da população, estados e municípios
  limpeza/dengue/    tabela tratada das notificações do Nordeste
  eda/               consultas, cores e funções comuns aos notebooks de EDA
  config.py          caminhos, período e conexão com o banco (lida do .env)
  dicionario.py      perfil das colunas para o dicionário de dados
notebooks/           01 a 10, na ordem do pipeline
data/raw/            arquivos baixados (não versionados)
data/postgres-local/ instância PostgreSQL local, quando configurada (não versionada)
.claude/specs/       00_projeto, 01_fontes, 02_banco, 03_decisoes, 99_uso_ia
.claude/skills/      coleta, carga, limpeza, eda, registro-ia, welcome (instruções para o assistente de IA)
.env.example         modelo do arquivo de acesso ao banco
```

## Uso de IA
No Claude Code, digite `/welcome`. Com outra IA, peça para ler `.claude/specs/` e `.claude/skills/`.
Registre todo uso em `.claude/specs/99_uso_ia.md` (exigência da disciplina).
