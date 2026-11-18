# 05: Tipos de linha

**What to build:** Um contabilista vê as linhas de IVA e de desconto na saída sem código, com a indicação do tipo, já aceites e fora da fila de revisão. Os subtotais e totais não aparecem como linhas, mas ficam no registo de auditoria da factura.

Tudo o que não for reconhecido como IVA ou desconto é tratado como serviço e é codificado.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] A classificação é determinística, por padrão sobre a descrição normalizada e por posição na tabela
- [ ] O padrão de `tax` reconhece só o IVA ("IVA", "VAT", "Imposto sobre o Valor Acrescentado"), e nunca "taxa" ou "imposto" sozinhos
- [ ] "Taxa de pilotagem sintética" (INV-003) e um direito aduaneiro são classificados como serviço
- [ ] As linhas `tax` e `discount` saem sem código, com `HIGH`, nota `line_type_tax` ou `line_type_discount`, estado `accepted` e sem sinalização
- [ ] As linhas de resumo não são persistidas como linhas, e o evento `summary_rows_extracted` fica na auditoria da factura
- [ ] A percentagem de IVA de cada linha é guardada como atributo da linha
- [ ] As linhas `tax` e `discount` não são enviadas ao classificador
