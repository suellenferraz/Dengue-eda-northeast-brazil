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
| `src/limpeza/dengue/limpeza_dengue.py` | cria `notificacao_dengue_ne` em SQL, numa transação (`criar()`; ~2,5 min) |
| `notebooks/06_limpeza.ipynb` | regras, criação, conferência e validação com número oficial |
| `src/dicionario.py` | perfil de colunas (`perfil_colunas`, `salvar_markdown`); conta `"nan"` e vazio como nulos |

## Regras
- A limpeza nunca altera o bruto: gera tabela nova, recriada do zero a cada execução.
- Volume grande fica no banco (SQL); pandas só para conferência e gráficos.
- Para mudar uma regra: medir antes no `05_analise`, alterar o SQL em `limpeza_dengue.py`, atualizar a tabela de regras
  em `02_banco.md` e conferir no `06_limpeza` quantas linhas a regra afetou.
- Campos com nome diferente nas fichas (até 2006 / desde 2007): `nu_idade`/`nu_idade_n`, `con_classi`/`classi_fin`,
  `con_criter`/`criterio`, `con_evoluc`/`evolucao`. Sempre unificar antes de usar.
- Idade: remover o `.0` (2008, 2012, 2016–2019) antes de decodificar; sem isso, 1,66 milhão de idades se perdem.
- Classificação: caso provável = ≠ 5; confirmado = 1–4 (qualquer ano, há códigos antigos em 2016) ou 10–12.
- Antes de usar uma variável, confira o % de nulos por ano: vários campos são vazios nos anos antigos.
- Códigos do SINAN ainda não conferidos no dicionário oficial; ao confirmar, cite a fonte em `02_banco.md`.

## Verificação
- Linhas da tratada = residentes do Nordeste no bruto − excluídos previstos (hoje 167).
- Contagens de cada regra batem com o `05_analise`.
- Validação externa: um total oficial (hoje Bahia 2024, Sesab) com diferença pequena.
