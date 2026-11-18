# 10: Duplicado provável

**What to build:** Um contabilista carrega uma factura que tem o mesmo fornecedor e o mesmo número de outra já carregada, mas um ficheiro diferente, por exemplo reexportado. A factura é codificada na mesma e as suas linhas ficam sinalizadas como duplicado provável, com referência à factura anterior.

**Blocked by:** 06

**Status:** ready-for-agent

- [ ] Há um índice não único sobre (fornecedor, número da factura)
- [ ] O mesmo fornecedor e o mesmo número com digest diferente dá a sinalização `possible_duplicate`, com o identificador da factura anterior
- [ ] O mesmo digest continua a devolver o trabalho existente, sem sinalização (idempotência)
- [ ] O carregamento nunca é bloqueado por suspeita de duplicado
- [ ] Uma factura sem número nunca é considerada duplicado provável
