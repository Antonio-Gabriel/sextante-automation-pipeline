# 08: Revisão de linhas

**What to build:** Um revisor filtra a fila de linhas, abre uma linha e vê todos os itens da aba de destino, ordenados por score lexical e com a escolha do modelo marcada. Pode aceitar a linha, ou corrigir o código escolhendo um item **só** dessa aba. Pode também deixar uma nota. Cada acção fica na auditoria sem apagar o registo anterior.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] Os resultados podem ser filtrados por confiança, aba de destino, sinalização e factura
- [ ] A paginação tem um limite máximo imposto pelo servidor, e o truncamento é indicado
- [ ] O endpoint de candidatos devolve a aba de destino inteira, ordenada por score, com a escolha do modelo marcada
- [ ] A correcção aceita só códigos da aba de destino da linha, validados no servidor; é recusada para linhas sem aba de destino
- [ ] A aceitação passa a linha de `pending` para `accepted`, e a correcção passa-a para `corrected`
- [ ] A nota tem um comprimento máximo declarado
- [ ] Cada acção gera um evento de auditoria (`line_accepted` ou `line_corrected`) com o valor anterior, o novo, o autor (vindo da configuração) e o momento, só com inserções
- [ ] `POST` e `PATCH` exigem `Idempotency-Key`
- [ ] Os contratos de entrada rejeitam campos extra e nunca aceitam campos de controlo (aba de destino, confiança, digest)
