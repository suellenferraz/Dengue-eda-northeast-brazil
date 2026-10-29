# 02. Banco de dados e dicionário

Postgres local, banco `dengue-eda`, schema `public`. Acesso pelo arquivo `.env` na raiz (modelo em `.env.example`;
variáveis `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`), lido por `src/config.py` (`BANCO`).

## 1. Tabelas
| Tabela | Camada | Linhas | Criada por |
|---|---|---|---|
| `sinan_dengue` | bruta | 32.512.002 | `src/carga/dengue/carga_dengue.py` |
| `sinan_dengue_carga` | controle | 27 | `src/carga/dengue/carga_dengue.py` |
| `populacao_ne` | bruta | 44.850 | `src/carga/ibge/carga_ibge.py` |
| `estado` | apoio | 27 | `src/carga/ibge/carga_ibge.py` |
| `municipio` | apoio | 5.571 | `src/carga/ibge/carga_ibge.py` |
| `populacao_municipio_ano` | tratada | 48.421 | `src/carga/ibge/carga_ibge.py` |
| `notificacao_dengue_ne` | tratada | 5.598.410 | `src/limpeza/dengue/limpeza_dengue.py` |

Relações (todas pelo código do município de 7 dígitos):
```
estado (uf_cod) ◄── municipio (cod_mun7, cod_mun6) ◄── populacao_municipio_ano (cod_mun7, ano)
                                                   ◄── notificacao_dengue_ne (cod_mun7, cod_mun7_notificacao)
```
Incidência = casos (`notificacao_dengue_ne`) ÷ população (`populacao_municipio_ano`), mesmo município e ano, × 100.000.

## 2. Camada bruta e controle

### `sinan_dengue`
- Uma linha por notificação, Brasil, 2000 a 2026, a partir do CSV anual (opção B). ~7,9 GB.
- `ano_arquivo` (smallint, ano do CSV) + as 196 colunas dos CSVs, em minúsculas, **todas texto**, sem conversão.
  Coluna que não existe num período da ficha fica nula nele.
- Particionada por `ano_arquivo` (`sinan_dengue_2000` ... `sinan_dengue_2026`).
- Única alteração: bytes nulos (0x00) removidos (1 em todo o conjunto, `dt_obito` de um registro de 2008).

### `sinan_dengue_carga`
| Coluna | Tipo | Descrição |
|---|---|---|
| `ano_arquivo` | smallint | ano carregado (chave primária) |
| `arquivo` | text | CSV de origem |
| `linhas` | bigint | linhas carregadas |
| `bytes_nulos` | integer | bytes 0x00 removidos |
| `carregado_em` | timestamptz | data da carga |

### `populacao_ne`
| Coluna | Tipo | Descrição |
|---|---|---|
| `cod_mun7` | char(7) | código IBGE do município (chave primária com `ano`) |
| `cod_mun6` | char(6) | código sem dígito verificador |
| `uf_cod` | smallint | código IBGE da UF (21 a 29) |
| `municipio` | text | nome mais recente |
| `ano` | smallint | 2000 a 2026, sem 2007 e 2023 |
| `populacao` | integer | habitantes; nulo quando o SIDRA não tem o valor (16) |
| `fonte` | text | `censo_2000_2010`, `censo_2022` ou `estimativa_6579` |

## 3. Camadas de apoio e tratada

### `estado`
| Coluna | Tipo | Descrição |
|---|---|---|
| `uf_cod` | smallint | código IBGE da UF (chave primária) |
| `sigla` | char(2) | sigla (única) |
| `nome` | text | nome |
| `regiao_sigla`, `regiao` | char(2), text | N, NE, SE, S, CO |

### `municipio`
| Coluna | Tipo | Descrição |
|---|---|---|
| `cod_mun7` | char(7) | código IBGE (chave primária) |
| `cod_mun6` | char(6) | sem dígito verificador (único); junção com o SINAN |
| `nome` | text | nome atual |
| `uf_cod` | smallint | chave estrangeira para `estado` |
| `microrregiao`, `mesorregiao` | text | divisão antiga; nula para municípios criados depois de 2017 |
| `regiao_imediata`, `regiao_intermediaria` | text | divisão atual (desde 2017) |

### `populacao_municipio_ano` (use nas análises)
| Coluna | Tipo | Descrição |
|---|---|---|
| `cod_mun7` | char(7) | chave estrangeira para `municipio`; chave primária com `ano` |
| `ano` | smallint | 2000 a 2026, sem buracos na série de cada município |
| `populacao` | integer | habitantes |
| `fonte` | text | `censo_2000_2010`, `censo_2022`, `estimativa_6579` ou `interpolada` |

2007 e 2023 = média do ano anterior e do seguinte (`interpolada`). Municípios criados depois de 2000 começam no primeiro
ano com população (7 municípios; ex.: Nazária/PI a partir de 2008).

### `notificacao_dengue_ne` (use nas análises)
Uma linha por notificação de **residente do Nordeste** (código de residência com par em `municipio`, UF 21 a 29),
a partir de `sinan_dengue`. Inclui residentes notificados fora do Nordeste. Exclui códigos sem par no IBGE
("município ignorado", 167) e notificações sem município de residência.

| Coluna | Tipo | Origem | Regra |
|---|---|---|---|
| `id` | bigint | — | identidade (o SINAN público não tem identificador) |
| `cod_mun7` | char(7) | `id_mn_resi` | `left(id_mn_resi, 6) = municipio.cod_mun6`; chave estrangeira |
| `cod_mun7_notificacao` | char(7) | `id_municip` | idem; sem par (2) → nulo |
| `ano` | smallint | `nu_ano` | inválido (2 em 2008) → `ano_arquivo` |
| `dt_notificacao` | date | `dt_notific` | inválida → nulo |
| `dt_sintomas` | date | `dt_sin_pri` | inválida, depois da notificação ou > 365 dias antes dela → nulo |
| `mes_sintomas` | smallint | `dt_sintomas` | mês (1 a 12) |
| `sexo` | char(1) | `cs_sexo` | M ou F; `I`, `O`, vazio → nulo |
| `idade_anos` | smallint | `nu_idade` / `nu_idade_n` | remove `.0`; `A`/`4` → valor; `M`, `D`, `3`, `2`, `1` → 0; `I999`, sem unidade, > 110 → nulo |
| `classificacao` | text | `con_classi` / `classi_fin` | fichas unificadas |
| `criterio` | text | `con_criter` / `criterio` | fichas unificadas |
| `evolucao` | text | `con_evoluc` / `evolucao` | fichas unificadas |
| `caso_provavel` | boolean | `classificacao` | ≠ 5 (inclui vazio e código 0) |
| `caso_confirmado` | boolean | `classificacao` | 1–4 (qualquer ano) ou 10–12 |
| `possivel_duplicata` | boolean | várias | 2ª linha em diante de grupo igual em `ano_arquivo`, município e unidade de notificação, datas de notificação e sintomas, sexo, idade e residência |
| `ano_arquivo` | smallint | `ano_arquivo` | CSV de origem |

Índices: `ano`, `cod_mun7`. Resultado (29/10/2026): 4.302.369 prováveis; 2.965.773 confirmados; 102.941 possíveis
duplicatas; vazios: sexo 6.769, idade 10.828, data de sintomas 13.046. 1 linha com `ano` = 1999 (filtrar 2000–2025).
**Validação:** Bahia 2024 = 232.455 casos prováveis × 232.623 da Sesab (−0,07%).

## 4. Códigos do SINAN
Observados nos dados; a confirmação no dicionário oficial do SINAN está pendente.

| Campo (ficha até 2006 / desde 2007) | Códigos |
|---|---|
| `con_classi` / `classi_fin` | até 2013: 1 dengue clássico, 2 com complicações, 3 febre hemorrágica, 4 síndrome do choque; desde 2014: 10 dengue, 11 com sinais de alarme, 12 grave, 13 chikungunya; sempre: 5 descartado, 8 inconclusivo; `0` (2000–2003) não documentado |
| `con_criter` / `criterio` | 1 laboratorial, 2 clínico-epidemiológico, 3 em investigação |
| `con_evoluc` / `evolucao` | 1 cura, 2 óbito pelo agravo, 3 óbito por outras causas, 4 óbito em investigação, 9 ignorado |
| `nu_idade` (até 2006) | letra + 3 dígitos: `A` anos, `M` meses, `D` dias, `I999` ignorado (ex.: `A046` = 46 anos) |
| `nu_idade_n` (desde 2007) | dígito + 3 dígitos: `4` anos, `3` meses, `2` dias, `1` horas (ex.: `4046`); `.0` no fim em 2008, 2012, 2016–2019 |
| `cs_sexo` | M, F, I (ignorado) |
| `hospitaliz` | 1 sim, 2 não, 9 ignorado |
| `nduplic_n` | marca de duplicidade da vigilância (0, 1, 2: confirmar); vazia em 99,7% no Nordeste |

Outros formatos por período: `sg_uf` e `sg_uf_not` vêm como sigla nos anos antigos e código IBGE nos recentes;
`id_mn_resi` e `id_municip` têm 7 dígitos até 2006 e 6 depois.

## 5. Qualidade do bruto (Nordeste, `05_analise.ipynb`)
| Ponto | Achado |
|---|---|
| Código de residência × IBGE | 99,997% com par; 167 sem par ("município ignorado"); 7º dígito sempre confere |
| Sem município de residência | ~3.700 no Brasil (0,01%) |
| Notificados fora do Nordeste | 0,03% a 1,09% por ano (maior em 2023–2025) |
| `nu_ano` × `ano_arquivo` | quase sempre igual (até 1.088 diferentes em 2025) |
| `sg_uf` × município | 99,99% coerentes |
| Possíveis duplicadas | 0,7% a 3,3% por ano |
| **Descartados** | **ausentes (código 5 = 0%) em 2014, 2015 e 2022–2026**; 16% a 47% nos demais anos |
| Classificação vazia / código 0 | 9%–18% e até 10% em 2000–2006; 11.963 vazios em 2026 (ano em andamento) |
| Datas | sintomas de 0006 a 2043; 13 depois da notificação; 13.016 mais de 1 ano antes |
| Idade | decimal (`4023.0`) em 2008, 2012, 2016–2019 (1,66 milhão); ~400 sem unidade; 1.017 acima de 110; confere com `ano_nasc` em 99,98% |
| Critério / evolução | preenchidos em 68%–89% e 47%–89%, conforme o ano |
| Confirmação por estado | varia muito (2024: SE 99%, CE 97%, BA 73%, RN 41% dos prováveis) |
