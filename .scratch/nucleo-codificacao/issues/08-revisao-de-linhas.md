# 08: Revisão de linhas

**What to build:** Um revisor filtra a fila de linhas, abre uma linha e vê todos os itens da aba de destino, ordenados por score lexical e com a escolha do modelo marcada. Pode aceitar a linha, ou corrigir o código escolhendo um item **só** dessa aba. Pode também deixar uma nota. Cada acção fica na auditoria sem apagar o registo anterior.

**Blocked by:** 04

**Status:** resolved

- [x] Os resultados podem ser filtrados por confiança, aba de destino, sinalização e factura
- [x] A paginação tem um limite máximo imposto pelo servidor, e o truncamento é indicado
- [x] O endpoint de candidatos devolve a aba de destino inteira, ordenada por score, com a escolha do modelo marcada
- [x] A correcção aceita só códigos da aba de destino da linha, validados no servidor; é recusada para linhas sem aba de destino
- [x] A aceitação passa a linha de `pending` para `accepted`, e a correcção passa-a para `corrected`
- [x] A nota tem um comprimento máximo declarado
- [x] Cada acção gera um evento de auditoria (`line_accepted` ou `line_corrected`) com o valor anterior, o novo, o autor (vindo da configuração) e o momento, só com inserções
- [x] `POST` e `PATCH` exigem `Idempotency-Key`
- [x] Os contratos de entrada rejeitam campos extra e nunca aceitam campos de controlo (aba de destino, confiança, digest)

## Comments

Resolved on 2026-11-18 (CHG-0024). The review state lives in its own table, `line_review`, so the coding record of `encoded_line` is never overwritten; the history is in `audit_event`, with the reviewer of `SEXTANTE_REVIEWER_ID` as author. A correction is allowed from any review state; an acceptance only from `pending`. Both are refused for a line without target sheet, which is unblocked by resolving the invoice's entity (ticket 09). Filters apply before pagination. `Idempotency-Key` is required on the review writes and on reprocessing; the upload is exempt, because the content digest already makes it idempotent (REQ-ING-007). Stored answers are kept 24 hours.

Review fixes on 2026-11-18 (CHG-0025): concurrent requests with one key act once, the 24-hour purge runs as a periodic task, audit events carry previous and new item, status and note. Open for the human: whether the upload must also require `Idempotency-Key` (SEC-19 says every POST), and rate limiting per key (SEC-19, SEC-12), which no ticket covers yet.

Decided on 2026-11-18 (CHG-0026): the upload stays exempt from `Idempotency-Key`, recorded in 00-decisoes-e-lacunas.md §3.19, SEC-19 and 02 §6.
