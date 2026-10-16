# Dicionário de dados

Status: **rascunho do CP1.** A Parte A está definida pelo próprio código. A Parte B (notificações) deve ser
gerada a partir dos dados reais (`notebooks/01_coleta.ipynb`, seção 7) e revisada pelo grupo; a tabela abaixo
lista os campos esperados do layout padrão do SINAN e serve de ponto de partida. Nomes e códigos podem diferir na API.

## Parte A. População por município (IBGE/SIDRA)
Arquivo: `data/raw/ibge/populacao_municipios_ne.csv`

| Variável | Tipo | Descrição | Observações |
|---|---|---|---|
| cod_mun7 | texto | Código IBGE do município (7 dígitos) | Mantido como texto para preservar zeros |
| cod_mun6 | texto | Código IBGE sem dígito verificador (6 dígitos) | **Chave de junção** com o SINAN |
| uf_cod | inteiro | Código IBGE da UF (21 a 29) | Derivado dos 2 primeiros dígitos |
| ano | inteiro | Ano de referência | Anos de Censo vêm de tabela diferente das estimativas |
| populacao | numérico | População residente (estimada ou censitária) | Pode haver ausências; tratar na limpeza |
| fonte | texto | Tabela de origem (`estimativa_6579`, `censo_2000_2010`, `censo_2022`) | Censo tem prioridade sobre estimativa |

## Parte B. Notificações de dengue (SINAN)
Campos esperados (confirmar contra a API; use o esqueleto gerado em `docs/dicionario_dengue_auto.md`).

| Variável | Descrição | Uso no projeto |
|---|---|---|
| NU_ANO | Ano da notificação | Série temporal |
| DT_NOTIFIC / SEM_NOT | Data e semana epidemiológica da notificação | Alternativa de data de referência |
| DT_SIN_PRI / SEM_PRI | Data e semana dos primeiros sintomas | Data de referência sugerida para sazonalidade |
| SG_UF / ID_MN_RESI | UF e município de residência (6 dígitos) | Geografia e junção com IBGE |
| SG_UF_NOT / ID_MUNICIP | UF e município de notificação | Comparar com residência |
| CS_SEXO | Sexo | Pergunta 4 |
| NU_IDADE_N | Idade codificada (1º dígito = unidade) | Pergunta 4; exige decodificação |
| CLASSI_FIN | Classificação final | Definir caso confirmado (codificação muda entre versões da ficha) |
| CRITERIO | Critério de confirmação | Qualidade dos dados |
| EVOLUCAO | Evolução do caso | Letalidade, se necessário |

## Pendências
- [ ] Confirmar nomes reais dos campos na API
- [ ] Documentar códigos de CLASSI_FIN por período
- [ ] Documentar % de nulos e inconsistências encontradas (entra na seção "Qualidade dos dados" do relatório)
