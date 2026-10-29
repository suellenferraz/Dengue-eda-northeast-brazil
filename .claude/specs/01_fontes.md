# 01. Fontes de dados

| Dado | Fonte | Método | Script | Saída |
|---|---|---|---|---|
| Notificações de dengue (opção B, **usada**) | OpenDataSUS, CSV anual | download de dados abertos | `src/coleta/dengue/coleta_dengue_csv.py` | `data/raw/dengue_csv/ano=AAAA/` |
| Notificações de dengue (opção A, alternativa) | API Dados Abertos | consumo de API REST | `src/coleta/dengue/coleta_dengue_api.py` | `data/raw/dengue_api/ano=AAAA/` |
| População por município | IBGE, API SIDRA | consumo de API REST | `src/coleta/ibge/coleta_ibge.py` | `data/raw/ibge/` |
| Estados e municípios | IBGE, API de Localidades | consumo de API REST | `src/carga/ibge/carga_ibge.py` | tabelas `estado`, `municipio` |

## 1. Notificações de dengue (SINAN, Ministério da Saúde)
Conjunto "Arboviroses - Dengue": https://dados.gov.br/dados/conjuntos-dados/arboviroses-dengue
(a página é montada por JavaScript; os arquivos ficam no armazenamento do OpenDataSUS).

### 1.1 Opção B: CSV anual (usada)
| Item | Valor |
|---|---|
| URL | `https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Dengue/csv/DENGBR{aa}.csv.zip` (aa = 00 a 26) |
| Cobertura | Brasil, 2000 a 2026, um ZIP com um CSV por ano |
| Tamanho | ~900 MB compactados; 8,5 GB extraídos (2024: 1,8 GB) |
| Formato | CSV, separador `,`, UTF-8, cabeçalho na 1ª linha, colunas em MAIÚSCULAS, valores como texto, quebra de linha CRLF |
| Ausentes | célula vazia |
| Atualização (verificada em 29/10/2026) | 2000–2016 em 01/10/2026; 2017–2026 em 24/10/2026 |
| Coleta | `python src/coleta/dengue/coleta_dengue_csv.py --anos 2000 2026`; anos já baixados são pulados (`--refazer` baixa de novo) |

Colunas por período da ficha do SINAN (196 colunas distintas; 27 em todos os anos):

| Anos | Colunas | Mudança |
|---|---|---|
| 2000–2006 | 107 | ficha antiga: `NU_IDADE`, `CON_CLASSI`, `CON_CRITER`, `CON_EVOLUC`, `DENGUE`, sinais clínicos (`FEBRE`, `CEFALEIA`...) |
| 2007–2008 | 63 | SINAN Net: saem 80 colunas, entram 36 (`NU_IDADE_N`, `CLASSI_FIN`, `CRITERIO`, `EVOLUCAO`, `TP_NOT`...) |
| 2009–2013 | 66 | entram `DT_NS1`, `RESUL_NS1`, `TP_SISTEMA` |
| 2014–2015 | 121 | classificação OMS 2009: entram 55 (`ALRM_*`, `GRAV_*`, comorbidades, `ANO_NASC`) |
| 2016–2019 | 119 | `DT_NASC` substitui `ANO_NASC`; saem `DT_DIGITA`, `MIGRADO_W` |
| 2020–2026 | 121 | voltam `ANO_NASC`, `DT_DIGITA`, `MIGRADO_W`; sai `DT_NASC` |

Sempre presentes (entre outras): `NU_ANO`, `ID_MUNICIP`, `ID_MN_RESI`, `SG_UF`, `DT_NOTIFIC`, `DT_SIN_PRI`, `CS_SEXO`.
Equivalências entre as fichas e códigos: `02_banco.md`, seção 4.

### 1.2 Opção A: API Dados Abertos (alternativa)
| Item | Valor |
|---|---|
| Endpoint | `GET https://apidadosabertos.saude.gov.br/arboviroses/dengue` |
| Documentação | https://apidadosabertos.saude.gov.br/v1/ (seção "Agravo Arboviroses") |
| Resposta | `{"dengue": [ {...}, ... ]}`; fim dos dados = lista vazia |
| Registro | ~196 campos (as colunas de todas as fichas; as que não existem no período vêm vazias), minúsculas, texto, ~3,7 KB em JSON |
| Ausentes | `"nan"` (anos recentes) ou `null` (anos antigos) |
| Situação | coleta interrompida (2000–2012 completos; demais parciais); nunca carregada no banco; arquivos apagados em 29/10/2026 |

| Parâmetro | Tipo | Swagger | Uso |
|---|---|---|---|
| `nu_ano` | string | ano da ocorrência | um ano por vez |
| `limit` | integer | itens por página, ≤ 1000 | 1000 |
| `offset` | integer | "número da página" | avança 1000 por página (ver abaixo) |
| `id_municip` | string | município da unidade notificadora | não usado |
| `campos` | string | campos a retornar, separados por vírgula | não usado (grava todos) |

```bash
curl 'https://apidadosabertos.saude.gov.br/arboviroses/dengue?nu_ano=2026&limit=1000&offset=0' -H 'accept: application/json'
```

Comportamento verificado na API real (28 e 29/10/2026):
- `offset` conta **registros**, não páginas (`offset=1` devolve o 2º registro).
- `limit` > 1000 não dá erro, mas devolve no máximo 1000.
- `id_municip`: 7 dígitos de 2000 a 2006, 6 de 2007 em diante; no formato errado devolve lista vazia, sem erro.
- `sg_uf` e `sg_uf_not` são ignorados: não existe filtro por UF.
- Páginas estáveis para a mesma consulta; ordem não documentada.
- Desempenho: ~1 s por página rasa; à noite ~700 registros/s; em horário comercial ~200 registros/s.
- Instabilidade: períodos de HTTP 502 e timeout de 60 s (corte do servidor), inclusive em páginas rasas.
  O script tenta 6 vezes com espera crescente; a coleta é retomável pelo offset salvo (`dengue.estado.json`).

### 1.3 Comparação A × B (verificada em 29/10/2026)
| Item | A: API | B: CSV |
|---|---|---|
| Notificações | as mesmas | as mesmas (diferença máxima −0,24% por ano em 2000–2012; 6 de 13 anos idênticos) |
| Colunas | 196 em todos os anos | só as da ficha do período (63 a 121) |
| Anos 2000–2006 | idade e classificação preenchidas nos nomes antigos (`nu_idade`, `con_classi`) | igual (`NU_IDADE`, `CON_CLASSI`); mesmo % de preenchimento |
| Tempo (2000–2026) | dias | minutos |

## 2. População (IBGE, API SIDRA)
| Item | Valor |
|---|---|
| URL | `https://apisidra.ibge.gov.br/values/t/{tabela}/n6/in n3 {uf}/v/{variavel}/p/{periodos}` |
| Recorte | municípios do Nordeste (uma UF por consulta) |
| Resposta | JSON; 1ª linha é o cabeçalho; nome do município em `D1N` como `"Natal (RN)"` ou `"Natal - RN"` |
| Coleta | `python src/coleta/ibge/coleta_ibge.py` |
| Saída | `data/raw/ibge/populacao_municipios_ne.csv` e `data/raw/ibge/{UF}/{municipio}.csv` |

| Tabela | Variável | Conteúdo | Anos |
|---|---|---|---|
| 200 (`/c1/0/c2/0`) | 93 | Censo | 2000, 2010 |
| 4714 | 93 | Censo | 2022 |
| 6579 | 9324 | Estimativa anual | 2001–2006, 2008, 2009, 2011–2021, 2024–2026 |

- Censo tem prioridade sobre estimativa no mesmo ano.
- **2007 e 2023 não existem** em nenhuma tabela (interpolados na camada tratada).
- 2000–2006 têm 1.787 a 1.793 municípios (municípios criados depois); 1.794 a partir de 2008.
- 16 valores vazios no SIDRA (municípios que ainda não existiam).
- O Censo de 2022 corrigiu estimativas superestimadas (ex.: Natal 896.708 em 2021 → 751.300 em 2022).

## 3. Estados e municípios (IBGE, API de Localidades)
| Item | Valor |
|---|---|
| URL | `https://servicodados.ibge.gov.br/api/v1/localidades/estados` e `.../localidades/municipios` |
| Cobertura | Brasil: 27 UFs, 5.571 municípios (1.794 no Nordeste) |
| Divisões regionais | antiga (microrregião, mesorregião) e atual desde 2017 (região imediata, intermediária); municípios criados depois de 2017 não têm a antiga |

## 4. Método de obtenção (não é scraping)
Nenhuma coleta é *scraping* (extrair dados do HTML de páginas feitas para pessoas). Todas usam canais oficiais feitos
para programas, o que torna a coleta documentada e reprodutível.

| | Scraping | Consumo de API | Download de dados abertos |
|---|---|---|---|
| O que se lê | HTML de uma página | JSON de um endpoint | arquivo pronto (CSV) |
| Feito para | pessoas | programas | programas e pessoas |
| Estabilidade | baixa (depende do layout) | alta (contrato documentado) | alta (link e formato fixos) |

Termos para o relatório: coleta/extração de dados (o "E" de ETL/ELT), "via API", "via download de arquivos de dados
abertos"; em inglês, *data ingestion*, *API consumption*, *open data download*.
