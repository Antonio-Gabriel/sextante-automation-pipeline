# 09: Resolução de entidade

**What to build:** Um revisor abre uma factura com entidade ambígua, decide que é correspondência ou não correspondência e escreve uma nota obrigatória. A factura é então codificada a partir do texto já extraído. As suas linhas seguem a regra normal de confiança e podem chegar a `HIGH`.

A lista de exclusão não muda.

**Blocked by:** 03, 04, 07

**Status:** resolved

- [x] `POST /api/invoices/{invoice_id}/entity-resolution` aceita `MATCH` ou `NO_MATCH` e uma nota obrigatória com comprimento máximo
- [x] O pedido é recusado para facturas que não estejam `AMBIGUOUS`
- [x] É exigida `Idempotency-Key`; repetir o pedido não codifica a factura duas vezes
- [x] É gerado um evento de auditoria `entity_resolved`, com o resultado anterior, o novo, o autor e o momento
- [x] A factura é posta na fila e codificada a partir do texto extraído, contra a aba correspondente à resolução
- [x] A resolução humana não limita a confiança das linhas
- [x] A lista de exclusão e a configuração ficam inalteradas

## Comments

Resolved on 2026-11-18 (CHG-0027). The resolution is stored in its own table and replaces the entity check when the worker codes the invoice again; the lines follow the normal confidence rule. The placeholder codings of the ambiguous invoice are marked superseded, never overwritten, so every reader shows the coding in force and the earlier one stays. A second resolution, or one for an invoice that is not ambiguous, is refused with 409; the primary key on the resolution decides a race between two reviewers.

Decided on 2026-11-18 (CHG-0029, 00-decisoes-e-lacunas.md §3.21): after a reviewer's MATCH, `Exact_Entity_Match` stays `NO` and the lines carry the note `entity_confirmed_by_reviewer`.
