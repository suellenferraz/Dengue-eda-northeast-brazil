# 00. Projeto

**Título:** Incidência e distribuição espaço-temporal da dengue na Região Nordeste do Brasil: uma análise exploratória
entre 2000 e 2025.
**Disciplina:** IMD1151, Ciência de Dados, 2026.2 (2ª unidade).
**Tipo de trabalho:** análise exploratória de dados (EDA).

## 1. Objetivo
Analisar como a incidência de dengue variou nos estados do Nordeste brasileiro entre 2000 e 2025, identificando
diferenças entre os estados e os períodos de maior ocorrência. Também explorar possíveis associações com fatores como
chuva, temperatura ou saneamento, conforme os dados disponíveis. A análise é exploratória: descreve padrões e relações,
sem afirmar que um fator causou o aumento da dengue.

## 2. Perguntas de pesquisa
1. Como a incidência evoluiu por estado e quais anos foram epidêmicos no Nordeste?
2. Existe sazonalidade mensal consistente, e ela difere entre estados (litoral × semiárido)?
3. Quais municípios têm incidência atípica em relação ao seu estado, considerando o porte populacional?
4. A distribuição por faixa etária e sexo muda entre anos epidêmicos e não epidêmicos?

## 3. Escopo
| Item | Definição |
|---|---|
| Região | Nordeste: MA, PI, CE, RN, PB, PE, AL, SE, BA (códigos IBGE 21 a 29), 1.794 municípios |
| Período da análise | 2000 a 2025 (`config.ANO_INICIO`, `config.ANO_FIM`); 2025 sujeito a revisão |
| Período coletado | 2000 a 2026 (`config.ANO_FIM_COLETA`); 2026 é parcial e fica fora da análise |
| Unidade de análise | município de residência × ano (e × mês, para sazonalidade) |
| Medida principal | incidência de casos prováveis por 100 mil habitantes (ver `03_decisoes.md`) |

## 4. Arquitetura
Pipeline ELT: coleta → carga do bruto no Postgres local → limpeza no banco → tabelas tratadas → EDA.
Só as tabelas agregadas necessárias ao dashboard sobem para o Postgres no Neon.

| Camada | Conteúdo | Exemplo |
|---|---|---|
| bruta | dado como veio da fonte, sem filtro | `sinan_dengue`, `populacao_ne` |
| apoio | referências fixas | `estado`, `municipio` |
| tratada | dado limpo, pronto para análise | `notificacao_dengue_ne`, `populacao_municipio_ano` |
| agregada | contagens e taxas para EDA e dashboard | `incidencia_estado_ano` (a criar) |

Detalhes das tabelas: `02_banco.md`. Fontes: `01_fontes.md`.

## 5. Andamento (29/10/2026)
Os arquivos de `data/raw/` foram apagados depois da carga (29/10/2026). Os notebooks de coleta e carga (01 a 04)
baixam e carregam de novo quando executados (CSV em minutos, IBGE em segundos); os de análise e limpeza (05 em
diante) leem só do banco.

| Etapa | Notebook | Script | Saída | Situação |
|---|---|---|---|---|
| Coleta dengue | `01_coleta_dengue` | `src/coleta/dengue/` | `data/raw/dengue_csv/`, `data/raw/dengue_api/` | feito (CSV 2000–2026); arquivos apagados após a carga |
| Carga dengue | `02_carga_dengue` | `src/carga/dengue/carga_dengue.py` | `sinan_dengue` | feito |
| Coleta IBGE | `03_coleta_ibge` | `src/coleta/ibge/coleta_ibge.py` | `data/raw/ibge/` | feito |
| Carga IBGE | `04_carga_ibge` | `src/carga/ibge/carga_ibge.py` | `populacao_ne`, `estado`, `municipio`, `populacao_municipio_ano` | feito |
| Análise do bruto | `05_analise` | — | achados de qualidade | feito |
| Limpeza | `06_limpeza` | `src/limpeza/dengue/limpeza_dengue.py` | `notificacao_dengue_ne` | feito e validado |
| Consistência da tratada | — | — | — | a fazer |
| Tabelas de incidência | — | — | `incidencia_estado_ano`, `incidencia_estado_mes` | a fazer |
| EDA | — | — | gráficos e achados | a fazer |
| Dashboard | — | — | tabelas agregadas no Neon | a fazer |

## 6. Backlog
- Chuva e temperatura: INMET (estações meteorológicas), agregadas por estado e mês.
- Saneamento: SNIS ou Censo do IBGE, por município e ano.
- Entram depois da EDA da incidência; cada fonte nova segue o mesmo pipeline (coleta, carga, limpeza).

## 7. Entregas
- CP1: coleta de 2 fontes integradas e dicionário de dados (`02_banco.md`).
- Registro obrigatório do uso de IA (`99_uso_ia.md`).
- Notebooks de limpeza e EDA, relatório final e dashboard.
