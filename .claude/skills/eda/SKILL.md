---
name: eda
description: Análise exploratória (EDA) da dengue no Nordeste, 2000 a 2025. Use ao calcular incidência, criar tabelas agregadas, investigar anos epidêmicos, sazonalidade, diferenças entre estados, municípios atípicos ou perfil por idade e sexo, ou ao fazer gráficos e tabelas para o relatório e o dashboard.
---

# EDA

Objetivo e perguntas: `.claude/specs/00_projeto.md`. Decisões: `.claude/specs/03_decisoes.md`. Tabelas: `.claude/specs/02_banco.md`.
O objetivo é descrever e explorar, sem previsão nem inferência causal. Toda conclusão vem de um número ou gráfico.
Se uma análise não ajuda a responder uma pergunta de pesquisa, pergunte antes de fazer. Decisões marcadas
**(grupo)** não são fechadas sozinho.

## Dados
- Use só as tabelas tratadas: `notificacao_dengue_ne`, `populacao_municipio_ano`, `municipio`, `estado`.
- Filtros padrão: `ano BETWEEN 2000 AND 2025`; casos = `caso_provavel` (principal) e `caso_confirmado` (comparação).
- Mostre o efeito das possíveis duplicatas (com e sem `possivel_duplicata`) ao menos uma vez.
- Incidência = casos ÷ população do mesmo ano × 100.000; estado e região vêm de `municipio` e `estado`.
- Agregações pesadas em SQL; o resultado (pequeno) vai para pandas.
- Tabelas agregadas para EDA e dashboard: `incidencia_estado_ano`, `incidencia_estado_mes` (a criar).

## Métodos
- Ano epidêmico: < 100 baixa, 100–299 média, ≥ 300 por 100 mil alta; mostre o critério no gráfico.
- Sazonalidade: `mes_sintomas`.
- Municípios atípicos: taxas de municípios pequenos são instáveis; use funnel plot ou suavização bayesiana empírica
  em relação ao estado; nunca ranqueie a taxa bruta.
- Faixas etárias: 0–4, 5–9, 10–19, 20–39, 40–59, 60+.
- 2025 sujeito a revisão: sinalize nos gráficos. Confirmação varia muito entre estados (2024: RN 41%, SE 99%);
  comparações entre estados usam caso provável.

## Notebooks
Numerados depois do `06_limpeza`, executados de cima para baixo. Cada um abre com objetivo, entradas e saídas, e fecha
com "Achados" (bullets com números). Lógica reutilizável vai para `src/`.

## Gráficos
- matplotlib/seaborn, textos em português, unidade no eixo ("casos por 100 mil hab.").
- Título com a mensagem do gráfico; fonte e período na nota.
- Cores por UF consistentes (mapa definido uma vez em `src/`).
- Escala log quando picos epidêmicos esmagam o resto, avisando no eixo.
- Figuras do relatório em `reports/figures/` (PNG, 150+ dpi), nome descritivo.

## Verificação
- Notebook executado do início ao fim sem erros (`jupyter nbconvert --to notebook --execute`).
- Totais conferidos contra a tratada (ex.: soma dos estados = total do Nordeste).
