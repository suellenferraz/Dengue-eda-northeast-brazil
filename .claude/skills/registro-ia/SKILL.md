---
name: registro-ia
description: Registro obrigatório (exigência da disciplina) de todo uso de IA generativa no projeto. Use sempre que a IA gerar ou alterar código, notebook, texto ou análise do repositório, antes de encerrar a tarefa.
---

# Registro de uso de IA

Ao terminar uma tarefa que gerou ou alterou algo no repositório, acrescente **uma linha** na tabela de
`.claude/specs/99_uso_ia.md`, sem reescrever as existentes.

| Coluna | Conteúdo |
|---|---|
| Data | DD/MM/AAAA |
| Quem | integrante que usou a IA; se não souber, pergunte (não invente nomes) |
| Ferramenta | nome e modelo exatos (ex.: "Claude Code (Opus 5.5)") |
| Etapa | coleta, carga, limpeza, EDA pergunta N, relatório... |
| O que foi gerado | arquivos e funções, de forma específica |
| Como foi verificado | só o que foi de fato executado ou conferido; o que **não** foi verificado, escrito explicitamente |

Nunca declare uma verificação que não aconteceu.
