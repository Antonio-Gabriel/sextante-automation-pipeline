# 10: Duplicado provável

**What to build:** Um contabilista carrega uma factura que tem o mesmo fornecedor e o mesmo número de outra já carregada, mas um ficheiro diferente, por exemplo reexportado. A factura é codificada na mesma e as suas linhas ficam sinalizadas como duplicado provável, com referência à factura anterior.

**Blocked by:** 06

**Status:** resolved

- [x] Há um índice não único sobre (fornecedor, número da factura)
- [x] O mesmo fornecedor e o mesmo número com digest diferente dá a sinalização `possible_duplicate`, com o identificador da factura anterior
- [x] O mesmo digest continua a devolver o trabalho existente, sem sinalização (idempotência)
- [x] O carregamento nunca é bloqueado por suspeita de duplicado
- [x] Uma factura sem número nunca é considerada duplicado provável

## Comments

Resolved on 2026-11-18 (CHG-0027). The supplier is its NIF when extracted, its folded name otherwise, the same key the export's Invoice_ID uses. Only an invoice uploaded before counts, so two copies never point at each other. Every line of the copy gets `possible_duplicate`, which sends it to review without changing its confidence; the results show `possible_duplicate_of` with the earlier invoice's identifier, and the audit records `possible_duplicate_detected`. The export carries the flag text, not the earlier identifier: both copies have the same Invoice_ID, so it would not tell them apart. Headers stored before migration 0007 have no supplier key and are never matched.
