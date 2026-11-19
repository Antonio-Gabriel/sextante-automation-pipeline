# 05: Ecrã da factura e resolução de entidade

**What to build:** Uma pessoa abre uma factura e vê o cabeçalho extraído: fornecedor, número, data, moeda, a entidade facturada detectada, o veredicto da entidade, a aba de destino, o estado, as linhas, e a referência a uma factura anterior quando é duplicado provável. Quando a entidade é ambígua, resolve-a como correspondência ou não correspondência, com nota obrigatória, e a factura volta a ser codificada.

**Blocked by:** 03 (Ecrã de resultados com filtros)

**Status:** resolved

- [x] Um endpoint novo devolve o cabeçalho de uma factura e o seu estado, com projecção explícita dos campos (SEC-18) e `404` para uma factura inexistente
- [x] O ecrã mostra o veredicto, o motivo de ambiguidade em Português, a aba de destino e o duplicado provável com a factura anterior
- [x] A resolução só é oferecida a uma factura ambígua ainda por resolver; a nota é obrigatória e tem comprimento máximo
- [x] A resolução gera a sua `Idempotency-Key` antes do primeiro envio
- [x] O `README.md` descreve o ecrã da factura e a resolução
- [x] Testes do endpoint pela API e testes do componente para a resolução

## Comments

Resolved on 2026-11-19 (CHG-0061), before ticket 04, which needs this endpoint to find a line's job and description.

Review fixes on 2026-11-19 (CHG-0062): polling after resolution, more-lines notice, one list of resolutions checked against OpenAPI, renewed key after `key_reused`, accessible errors and focus, undescribed reasons kept visible.
