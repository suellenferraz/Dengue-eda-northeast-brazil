# Dengue no Nordeste do Brasil: análise exploratória (2000 a 2025)

Projeto da 2ª unidade de IMD1151 (Ciência de Dados, 2026.2).

**Título:** Incidência e distribuição espaço-temporal da dengue na Região Nordeste do Brasil: uma análise exploratória entre 2000 e 2025.

## Perguntas de pesquisa
1. Como a incidência evoluiu por estado e quais anos foram epidêmicos no Nordeste?
2. Existe sazonalidade mensal consistente, e ela difere entre estados (litoral vs. semiárido)?
3. Quais municípios têm incidência atípica em relação ao seu estado, considerando o porte populacional?
4. A distribuição por faixa etária e sexo muda entre anos epidêmicos e não epidêmicos?

## Fontes de dados
| Fonte | Uso | Acesso |
|---|---|---|
| SINAN/Dengue, API Dados Abertos do Ministério da Saúde | notificações | https://apidadosabertos.saude.gov.br/v1/ |
| IBGE, API SIDRA (estimativas e Censos) | população por município | https://sidra.ibge.gov.br |

## Estrutura
```
README.md
requirements.txt
notebooks/01_coleta.ipynb      # CP1
src/config.py                  # caminhos, período, UFs
src/coleta_dengue_api.py       # coleta paginada e retomável
src/coleta_ibge.py             # população por município
src/dicionario.py              # gera o esqueleto do dicionário a partir dos dados
docs/dicionario_dados.md
docs/uso_ia.md                 # registro obrigatório do uso de IA generativa
data/                          # NÃO versionado (ver .gitignore)
```

## Como executar
```bash
python -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows
pip install -r requirements.txt

python src/coleta_dengue_api.py --probe              # diagnostica a API
python src/coleta_ibge.py                            # baixa população
python src/coleta_dengue_api.py --anos 2023 2023 --ufs RN --max-paginas 3   # piloto
python src/coleta_dengue_api.py --anos 2000 2025     # coleta completa (retomável)
jupyter lab                                          # notebooks/01_coleta.ipynb
```

## Plano B se a API não for viável
Se o diagnóstico mostrar página pequena (ex.: 20 registros) e milhões de linhas, a coleta via API para
2000 a 2025 pode levar dias. Alternativa: microdados do SINAN no DATASUS (arquivos `.dbc` por ano, nacionais),
lidos com a biblioteca PySUS e filtrados para UF 21 a 29. A API continua valendo como fonte para validar totais
e para anos recentes. Decidam em grupo e registrem a decisão no relatório (seção de metodologia).

## Decisões de análise a registrar (afetam todos os gráficos)
- Caso confirmado vs. notificado (excluir descartados?).
- Data de referência: primeiros sintomas ou notificação.
- Município de residência vs. de notificação.
- Denominador: qual tabela populacional por ano; como tratar anos de Censo e interpolação.
- Anos recentes (2025) sujeitos a revisão.
