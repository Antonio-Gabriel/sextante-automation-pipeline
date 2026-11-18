# 09: Resolução de entidade

**What to build:** Um revisor abre uma factura com entidade ambígua, decide que é correspondência ou não correspondência e escreve uma nota obrigatória. A factura é então codificada a partir do texto já extraído. As suas linhas seguem a regra normal de confiança e podem chegar a `HIGH`.

A lista de exclusão não muda.

**Blocked by:** 03, 04, 07

**Status:** ready-for-agent

- [ ] `POST /api/invoices/{invoice_id}/entity-resolution` aceita `MATCH` ou `NO_MATCH` e uma nota obrigatória com comprimento máximo
- [ ] O pedido é recusado para facturas que não estejam `AMBIGUOUS`
- [ ] É exigida `Idempotency-Key`; repetir o pedido não codifica a factura duas vezes
- [ ] É gerado um evento de auditoria `entity_resolved`, com o resultado anterior, o novo, o autor e o momento
- [ ] A factura é posta na fila e codificada a partir do texto extraído, contra a aba correspondente à resolução
- [ ] A resolução humana não limita a confiança das linhas
- [ ] A lista de exclusão e a configuração ficam inalteradas
