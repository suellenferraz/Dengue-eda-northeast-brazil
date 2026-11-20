---
name: limpeza
description: Análise de qualidade do bruto e criação das tabelas tratadas (notificacao_dengue_ne). Use ao mexer em src/limpeza/, em src/dicionario.py, nos notebooks 05_analise e 06_limpeza, ao interpretar ou decodificar campos do SINAN (classificação, idade, critério, evolução), ao definir caso provável ou confirmado, ou ao escrever a seção de qualidade dos dados.
---

# Limpeza

Regras, colunas e códigos do SINAN: `.claude/specs/02_banco.md` (seções 3 e 4). Decisões: `.claude/specs/03_decisoes.md`.

## Arquivos
| Arquivo | Papel |
|---|---|
| `notebooks/05_analise.ipynb` | estuda o bruto (só consultas): ligação com o IBGE, duplicadas, classificação, validação coluna a coluna |
| `src/limpeza/dengue/limpeza_dengue.py` | cria `notificacao_dengue_ne` em SQL numa transação (`criar()`) |
| `notebooks/06_limpeza.ipynb` | regras, criação, conferência e comparação histórica para Bahia em 2024 |
| `src/dicionario.py` | perfil de colunas (`perfil_colunas`, `salvar_markdown`); conta `"nan"` e vazio como nulos |

## Regras
- A limpeza nunca altera o bruto: gera tabela nova, recriada do zero a cada execução.
- Volume grande fica no banco (SQL); pandas só para conferência e gráficos.
- Para mudar uma regra: medir antes no `05_analise`, alterar o SQL em `limpeza_dengue.py`, atualizar a tabela de regras
  em `02_banco.md` e conferir no `06_limpeza` quantas linhas a regra afetou.
- Campos com nome diferente nas fichas (até 2006 / desde 2007): `nu_idade`/`nu_idade_n`, `con_classi`/`classi_fin`,
  `con_criter`/`criterio`, `con_evoluc`/`evolucao`. Sempre unificar antes de usar.
- Idade: remover o `.0` (2008, 2012, 2016–2019) antes de decodificar; sem isso, 1,66 milhão de idades se perdem.
- Classificação: caso provável exclui os códigos 5 e 13 e inclui os vazios e o código 0. Caso confirmado usa os códigos 1–4 ou 10–12.
- Antes de usar uma variável, confira o % de nulos por ano: vários campos são vazios nos anos antigos.
- Fontes oficiais da classificação final e verificações restantes estão registradas em `02_banco.md` e `03_decisoes.md`.

## Verificação
- Linhas da tratada = residentes do Nordeste no bruto − excluídos previstos (hoje 167).
- Contagens de cada regra batem com o `05_analise`.
- Na comparação externa de Bahia em 2024, registre a fonte e a data da extração.
