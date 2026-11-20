# 00. Projeto

**Título:** Incidência e distribuição espaço-temporal da dengue na Região Nordeste do Brasil: uma análise exploratória
entre 2000 e 2025.
**Disciplina:** IMD1151, Ciência de Dados, 2026.2 (2ª unidade).
**Tipo de trabalho:** análise exploratória de dados (EDA).

## 1. Objetivo
Analisar como a incidência de dengue variou nos estados do Nordeste brasileiro entre 2000 e 2025, identificando
diferenças entre os estados e os períodos de maior ocorrência. A análise também descreve a sazonalidade, identifica
municípios com incidência atípica e compara o perfil de idade e sexo entre anos epidêmicos e não epidêmicos.

## 2. Perguntas de pesquisa
| Pergunta | Notebook | Como responde |
|---|---|---|
| P1. Como a incidência evoluiu por estado e quais anos foram epidêmicos no Nordeste? | [07 · Incidência](../../notebooks/07_incidencia.ipynb) | Calcula casos prováveis por 100 mil habitantes por estado e ano, compara com a série do Nordeste e aplica o limiar de alta incidência. |
| P2. Existe sazonalidade mensal consistente, e como o padrão varia entre os estados e entre a capital e o interior de cada estado? | [08 · Sazonalidade](../../notebooks/08_sazonalidade.ipynb) | Usa ano e mês dos primeiros sintomas, distingue o mês de maior ocorrência do mês central circular e compara capital e interior nos mesmos anos de cada estado. |
| P3. Quais municípios têm incidência atípica em relação ao seu estado, considerando o porte populacional? | [09 · Municípios atípicos](../../notebooks/09_municipios_atipicos.ipynb) | Compara casos observados e esperados em funis estaduais, audita o denominador populacional e testa a sensibilidade da classificação. |
| P4. A distribuição por faixa etária e sexo muda entre anos epidêmicos e não epidêmicos? | [10 · Perfil por idade e sexo](../../notebooks/10_perfil_idade_sexo.ipynb) | Classifica cada estado-ano pelo limiar de incidência e compara as distribuições de idade e sexo dos casos prováveis. |

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
O pipeline documentado usa o PostgreSQL local. A publicação de agregados no Neon está prevista para o dashboard.

| Camada | Conteúdo | Exemplo |
|---|---|---|
| bruta | dado como veio da fonte, sem filtro | `sinan_dengue`, `populacao_ne` |
| apoio | referências fixas | `estado`, `municipio` |
| tratada | dado limpo, pronto para análise | `notificacao_dengue_ne`, `populacao_municipio_ano` |
| agregada | contagens e taxas calculadas para a EDA | série estadual no notebook 07 |

Detalhes das tabelas: `02_banco.md`. Fontes: `01_fontes.md`.

## 5. Andamento

Em 20/11/2026, a carga local reuniu 32.530.748 notificações brutas de 2000 a 2026 e 5.603.830 registros tratados
de residentes do Nordeste. A notificação mais recente na tabela tratada é de 31/10/2026. O recorte da EDA termina
em 2025.

| Etapa | Notebook | Script | Saída | Situação |
|---|---|---|---|---|
| Coleta dengue | `01_coleta_dengue` | `src/coleta/dengue/coleta_dengue_csv.py` | `data/raw/dengue_csv/` | CSV de 2000 a 2026 baixado para a carga local |
| Carga dengue | `02_carga_dengue` | `src/carga/dengue/carga_dengue.py` | `sinan_dengue` | feito |
| Coleta IBGE | `03_coleta_ibge` | `src/coleta/ibge/coleta_ibge.py` | `data/raw/ibge/` | feito |
| Carga IBGE | `04_carga_ibge` | `src/carga/ibge/carga_ibge.py` | `populacao_ne`, `estado`, `municipio`, `populacao_municipio_ano` | feito |
| Análise do bruto | `05_analise` | — | achados de qualidade | análise original registrada. Reexecução local interrompida por lentidão |
| Limpeza | `06_limpeza` | `src/limpeza/dengue/limpeza_dengue.py` | `notificacao_dengue_ne` | concluída por ano com a mesma regra SQL do notebook |
| Consistência da tratada | `09_municipios_atipicos` | `src/eda/eda.py` | cobertura de população e reconciliação dos totais | validada por município e ano |
| EDA (P1 a P4) | `07_incidencia`, `08_sazonalidade`, `09_municipios_atipicos`, `10_perfil_idade_sexo` | `src/eda/eda.py` | gráficos e achados | reexecutada no banco local em 20/11/2026 |
| Dashboard | — | — | tabelas agregadas no Neon | a fazer |

## 6. Limitações

- **P1 — Incidência.** As notificações dependem da detecção, do registro e da investigação, que variam entre anos e estados. Há arquivos anuais sem registros classificados como descartados e 2025 está sujeito a revisão. O limiar de 300 casos por 100 mil habitantes é a definição operacional de alta incidência nesta análise. Os denominadores de 2007 e 2023 são interpolados.
- **P2 — Sazonalidade.** Entram casos com data válida de início dos sintomas. No recorte de 2000 a 2025, a comparação entre capital e interior exige pelo menos 100 casos em cada grupo no mesmo ano. O mês central resume a distribuição circular e pode diferir do mês de maior ocorrência.
- **P3 — Municípios atípicos.** As classificações dependem do limiar e da dispersão estimada. A série acumulada pode ocultar diferenças entre anos. Taxas baixas podem refletir menor transmissão ou subnotificação. A auditoria encontrou 17 pares município–ano sem população válida e nenhum com notificações.
- **P4 — Idade e sexo.** A análise compara o perfil dos casos notificados e usa a incidência do estado-ano para formar os grupos. Campos ausentes limitam a comparação. As proporções descrevem a composição dos casos, e a análise de risco por idade e sexo exigiria denominadores populacionais específicos.
- **Escopo.** A análise é descritiva. Chuva, temperatura e saneamento são temas de trabalho futuro.

## 7. Backlog
- Chuva e temperatura: INMET (estações meteorológicas), agregadas por estado e mês.
- Saneamento: SNIS ou Censo do IBGE, por município e ano.
- Entram depois da EDA da incidência; cada fonte nova segue o mesmo pipeline (coleta, carga, limpeza).

## 8. Entregas
- CP1: coleta de 2 fontes integradas e dicionário de dados (`02_banco.md`).
- Registro obrigatório do uso de IA (`99_uso_ia.md`).
- Notebooks de limpeza e EDA, relatório final e dashboard.
