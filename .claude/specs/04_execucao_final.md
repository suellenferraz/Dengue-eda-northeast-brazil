# Execução final dos notebooks

Execução em 20/11/2026 no Windows, com o banco PostgreSQL local `dengue-eda` e o Python do ambiente `.venv`. Cada notebook foi iniciado com um kernel novo. O recorte analítico da EDA é 2000–2025. A carga também contém os dados parciais de 2026.

## Versões utilizadas

| Componente | Versão |
|---|---|
| Python | 3.14.6 |
| PostgreSQL | 18.4 |
| pandas, NumPy, PyArrow | 3.1.1, 2.5.4, 26.0.1 |
| Matplotlib, seaborn | 3.11.2, 0.13.2 |
| psycopg | 3.3.8 |
| JupyterLab, ipykernel | 4.6.5, 7.4.0 |
| nbclient, nbformat | 0.11.0, 5.11.1 |
| requests, python-dotenv, tqdm | 2.34.2, 1.2.4, 4.70.1 |

## Condições

A verificação usa os 27 CSVs anuais da carga local e os arquivos do IBGE já baixados. As demonstrações opcionais da API de dengue ficam desativadas no notebook 01. Os notebooks 04 e 06 reutilizam as tabelas existentes e executam suas conferências. Em um banco vazio, essas etapas carregam o IBGE e criam a tabela tratada.

## Verificações

Os dez notebooks foram executados em sequência (01 a 10), com 100 células de código concluídas sem erro e 13 gráficos salvos. As tabelas e os principais números das conclusões foram conferidos nas saídas da nova execução.

| Notebooks | Resultado |
|---|---|
| 01–02 · Dengue | 27 de 27 CSVs encontrados. As contagens do banco coincidiram com as de cada CSV; total de 32.530.748 notificações. |
| 03–04 · IBGE | 44.850 linhas de população no arquivo e no banco. Os anos de 2007 e 2023 estão ausentes no arquivo original e são preenchidos na camada tratada. |
| 05 · Análise do bruto | Dos 5.603.997 registros com prefixo de residência do Nordeste, 5.603.830 têm par no IBGE e 167 ficam sem par. A proporção anual de possíveis duplicatas na auditoria do bruto foi de 0,69% a 3,31%. |
| 06 · Limpeza | A reconciliação confirmou as 5.603.830 linhas da tabela tratada. |
| 07 · Incidência | 12 de 26 anos em alta. Em 2024, 605,1 casos por 100 mil habitantes. Excluir possíveis duplicatas reduz a incidência anual regional entre 0,6% e 3,5%, sem mudar a faixa de nenhum ano no Nordeste. |
| 08 · Sazonalidade | 4.169.990 casos prováveis com início dos sintomas no período. Abril foi o mês de maior ocorrência no perfil médio e o mês central típico. Capital e interior usam 25 a 26 anos em comum por estado. |
| 09 · Municípios atípicos | 46.627 pares município–ano com população válida. Nenhum par sem população tinha notificações. O cenário principal identificou 1 atípico acima e 80 abaixo do esperado. |
| 10 · Idade e sexo | 84 de 234 estados-ano classificados como epidêmicos, com 3.005.119 casos prováveis (72%). V de Cramér de 0,020 para idade e de 0,010 para sexo. |

O notebook 05 passou a gerar o resumo com os resultados das consultas e a validar as datas antes de convertê-las. No 07, o limite inferior da redução associada às possíveis duplicatas foi corrigido de 0,5% para 0,6%. No 10, as diferenças por faixa etária e estado também aparecem em tabela.
