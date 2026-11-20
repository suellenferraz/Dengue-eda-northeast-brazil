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
- Período 2000 a 2025. Use o ano da notificação para incidência e perfil por idade e sexo e a data de início dos sintomas para sazonalidade. Use `caso_provavel` na análise principal e `caso_confirmado` para comparação.
- Mostre o efeito das possíveis duplicatas (com e sem `possivel_duplicata`) ao menos uma vez.
- Incidência = casos ÷ população do mesmo ano × 100.000; estado e região vêm de `municipio` e `estado`.
- Agregações pesadas em SQL; o resultado (pequeno) vai para pandas.
- Os notebooks geram os agregados da EDA a partir das tabelas tratadas.

## Métodos
- Faixas de incidência por 100 mil habitantes: baixa abaixo de 100, média de 100 a menos de 300, alta a partir de 300.
- Sazonalidade: extraia ano e mês de `dt_sintomas`, diferencie mês de maior ocorrência e mês central circular e pareie capital e interior pelos mesmos anos em cada estado.
- Municípios atípicos: use o funil estadual com superdispersão aditiva do notebook 09 e consulte os cenários de sensibilidade.
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
- As figuras da EDA estão nas saídas dos notebooks 07 a 10.

## Verificação
- Notebook executado do início ao fim sem erros (`jupyter nbconvert --to notebook --execute`).
- Totais conferidos contra a tratada (ex.: soma dos estados = total do Nordeste).
