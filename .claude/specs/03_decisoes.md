# 03. Decisões de análise

Situação: **decidido** (vale para o projeto), **aplicado** (já implementado no código), **proposto** (em uso, falta o
grupo confirmar), **pendente** (sem escolha). Ao mudar uma decisão, atualize esta tabela, o código e a metodologia do
relatório.

| # | Decisão | Situação | Escolha | Motivo / evidência |
|---|---|---|---|---|
| 1 | Arquitetura | decidido | ELT: bruto no Postgres local, limpeza no banco; só tabelas agregadas sobem para o Neon (dashboard) | Neon tem pouco espaço; bruto do Brasil tem ~8 GB; bruto completo permite expandir para outras regiões |
| 2 | Fonte das notificações | **pendente (grupo)** | na prática, CSV anual (opção B); API (opção A) mantida como alternativa | mesmas notificações; CSV completo em minutos, API incompleta e instável (`01_fontes.md`) |
| 3 | Geografia | aplicado | município de **residência** (`id_mn_resi`) | inclui residentes notificados fora do Nordeste; 99,997% dos códigos têm par no IBGE |
| 4 | Ligação com o IBGE | aplicado | `left(id_mn_resi, 6) = municipio.cod_mun6`, depois tudo por `cod_mun7` | vale para 7 dígitos (até 2006) e 6 dígitos (desde 2007) |
| 5 | "Município ignorado" | aplicado | excluído (167 notificações) | código com UF mas sem município (ex.: `2900000`) |
| 6 | Definição de caso | aplicado (20/11/2026) | **caso provável** exclui `5` (descartado) e `13` (chikungunya), inclui vazios e `0`; **confirmado** usa 1–4 ou 10–12 (comparação) | definição do Ministério da Saúde, códigos e análise de sensibilidade em [02_banco.md](02_banco.md#definição-e-impacto-de-caso-provável) |
| 7 | Possíveis duplicatas | proposto, aplicado | marcar (`possivel_duplicata`), não apagar; mostrar resultado com e sem elas | dados anonimizados não permitem confirmar; `nduplic_n` vazio em 99,7%; 0,7%–3,3% por ano |
| 8 | Regras de limpeza (datas, sexo, idade, fichas) | aplicado | `02_banco.md`, tabela `notificacao_dengue_ne` | validadas coluna a coluna no `05_analise.ipynb`, seção 8 |
| 9 | Data de referência | aplicado | `ano` (notificação) para a série anual. Na sazonalidade, extrair ano e mês de `dt_sintomas` e aplicar o recorte de 2000 a 2025 à data dos sintomas | a mesma data determina o mês, o ano e o período da análise sazonal |
| 10 | Denominador | aplicado | `populacao_municipio_ano` do mesmo ano; 2007 e 2023 interpolados | IBGE não tem esses anos |
| 11 | Ano epidêmico | proposto | incidência < 100 baixa, 100–299 média, ≥ 300 por 100 mil alta | classificação usada pelo Ministério da Saúde |
| 12 | Período da análise | proposto | 2000 a 2025; 2026 fora (parcial); 2025 sinalizado como sujeito a revisão | `notificacao_dengue_ne` tem 1 linha de 1999 e 2026 inteiro |
| 13 | Capital × interior (P2) | aplicado | em cada estado, comparar residentes da capital e dos demais municípios usando os mesmos anos, com pelo menos 100 casos em cada grupo por ano | o notebook `08_sazonalidade` distingue o mês de maior ocorrência no perfil médio do mês central típico, obtido por média circular |
| 14 | Município atípico (P3) | proposto | funil com superdispersão aditiva (Spiegelhalter 2005): z = log(O/E) ÷ √(1/E + τ²), τ² por estado; alerta \|z\| > 1,96, atípico \|z\| > 3,09; período 2000–2025 somado | o ajuste multiplicativo (φ de 150 a 770) marcava quase só municípios grandes; o aditivo compara todos os portes |
| 15 | Ano epidêmico na P4 | proposto | por estado-ano (incidência ≥ 300), não pelo Nordeste todo | as epidemias não são simultâneas entre estados (correlação mediana 0,41, `07_incidencia`) |

## Pendências
- Comunicar ao grupo as decisões 6 e 7 e fechar a 2.
- Confirmar os códigos do SINAN (`02_banco.md`, seção 4) no dicionário oficial.
- Confirmar no painel do Ministério da Saúde o número usado na validação (Bahia 2024), hoje vindo de notícia que cita a Sesab.

## Sensibilidade dos municípios atípicos (P3)

Na base local de 2000 a 2025, a regra principal (limiar 3,09 e winsorização de 10% em cada cauda) identificou 81 atípicos, 1 acima e 80 abaixo. Variando apenas o limiar para 2,58 ou 3,29, o total foi de 162 ou 61. Com winsorização de 5% ou 15%, foi de 47 ou 126. Ao excluir as possíveis duplicatas e recalcular a referência e a dispersão por estado, os 81 atípicos da análise principal permaneceram do mesmo lado e dois municípios passaram a ser atípicos abaixo. O cenário sem dispersão adicional sinalizou 1.595 municípios. O [notebook 09](../../notebooks/09_municipios_atipicos.ipynb) mantém a regra principal e registra entradas, saídas e mudanças de lado em cada cenário.
