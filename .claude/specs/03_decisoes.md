# 03. Decisões de análise

**Decidido** indica uma diretriz do projeto. **Aplicado** indica que a escolha consta do pipeline ou dos notebooks executados. Ao mudar uma decisão, atualize esta tabela, o código e a metodologia do relatório.

| # | Decisão | Situação | Escolha | Motivo / evidência |
|---|---|---|---|---|
| 1 | Arquitetura | decidido | ELT: bruto no Postgres local, limpeza no banco; só tabelas agregadas sobem para o Neon (dashboard) | Neon tem pouco espaço; bruto do Brasil tem ~8 GB; bruto completo permite expandir para outras regiões |
| 2 | Fonte das notificações | aplicado | CSV anual do OpenDataSUS como fonte da carga. API mantida como alternativa | 27 arquivos anuais carregados localmente. A coleta via API ficou parcial, conforme [a comparação de fontes](01_fontes.md#13-comparação-a--b-verificada-em-29102026) |
| 3 | Geografia | aplicado | município de **residência** (`id_mn_resi`) | inclui residentes notificados fora do Nordeste; 99,997% dos códigos têm par no IBGE |
| 4 | Ligação com o IBGE | aplicado | `left(id_mn_resi, 6) = municipio.cod_mun6`, depois tudo por `cod_mun7` | vale para 7 dígitos (até 2006) e 6 dígitos (desde 2007) |
| 5 | "Município ignorado" | aplicado | excluído (167 notificações) | código com UF mas sem município (ex.: `2900000`) |
| 6 | Definição de caso | aplicado (20/11/2026) | **caso provável** exclui `5` (descartado) e `13` (chikungunya), inclui vazios e `0`; **confirmado** usa 1–4 ou 10–12 (comparação) | definição do Ministério da Saúde, códigos e análise de sensibilidade em [02_banco.md](02_banco.md#definição-e-impacto-de-caso-provável) |
| 7 | Possíveis duplicatas | aplicado | manter as linhas e marcar `possivel_duplicata`. Comparar os resultados com e sem as linhas marcadas | o agrupamento é um indício em dados anonimizados. O efeito é medido nos notebooks 07 e 09 |
| 8 | Regras de limpeza (datas, sexo, idade, fichas) | aplicado | `02_banco.md`, tabela `notificacao_dengue_ne` | validadas coluna a coluna no `05_analise.ipynb`, seção 8 |
| 9 | Data de referência | aplicado | `ano` (notificação) para a série anual. Na sazonalidade, extrair ano e mês de `dt_sintomas` e aplicar o recorte de 2000 a 2025 à data dos sintomas | a mesma data determina o mês, o ano e o período da análise sazonal |
| 10 | Denominador | aplicado | `populacao_municipio_ano` do mesmo ano; 2007 e 2023 interpolados | IBGE não tem esses anos |
| 11 | Ano epidêmico | aplicado | incidência baixa abaixo de 100, média de 100 a menos de 300, alta a partir de 300 por 100 mil habitantes | classificação operacional implementada em `src/eda/eda.py` e usada no notebook 07 |
| 12 | Período da análise | aplicado | EDA de 2000 a 2025, com 2025 sujeito a revisão | a carga preserva o arquivo parcial de 2026, fora da janela analítica |
| 13 | Capital × interior (P2) | aplicado | agrupar pelo município de residência em cada estado. Comparar os anos com pelo menos 100 casos em cada grupo | o notebook 08 distingue o mês de maior ocorrência no perfil médio do mês central típico, obtido por média circular |
| 14 | Município atípico (P3) | aplicado | funil com superdispersão aditiva (Spiegelhalter 2005), com z = log((O + 0,5)/E) ÷ √(1/E + τ²). Estimar τ² por estado com winsorização de 10% em cada cauda. Alerta \|z\| > 1,96, atípico \|z\| > 3,09. Somar 2000–2025 | 81 atípicos na regra principal. Alternativas e limitações na seção de sensibilidade |
| 15 | Ano epidêmico na P4 | aplicado | classificar cada estado-ano como epidêmico a partir de 300 casos por 100 mil habitantes | o notebook 10 usa a incidência de cada estado para agrupar seus casos |

## Pendências
- Confirmar os códigos de `nduplic_n` em documentação oficial. A classificação final está documentada em [02_banco.md](02_banco.md#4-códigos-do-sinan).
- Confirmar a extração de referência para Bahia em 2024. O notebook 06 registra uma comparação histórica com número atribuído à Sesab.
- Confirmar uma licença específica para o conjunto de dengue. O campo de licença na página consultada do OpenDataSUS contém texto genérico. [Fonte e registro da consulta](01_fontes.md#1-notificações-de-dengue-sinan-ministério-da-saúde)

## Sensibilidade dos municípios atípicos (P3)

Na base local de 2000 a 2025, a regra principal (limiar 3,09 e winsorização de 10% em cada cauda) identificou 81 atípicos, 1 acima e 80 abaixo. Variando apenas o limiar para 2,58 ou 3,29, o total foi de 162 ou 61. Com winsorização de 5% ou 15%, foi de 47 ou 126. Ao excluir as possíveis duplicatas e recalcular a referência e a dispersão por estado, os 81 atípicos da análise principal permaneceram do mesmo lado e dois municípios passaram a ser atípicos abaixo. O cenário sem dispersão adicional sinalizou 1.595 municípios. O [notebook 09](../../notebooks/09_municipios_atipicos.ipynb) mantém a regra principal e registra entradas, saídas e mudanças de lado em cada cenário.
