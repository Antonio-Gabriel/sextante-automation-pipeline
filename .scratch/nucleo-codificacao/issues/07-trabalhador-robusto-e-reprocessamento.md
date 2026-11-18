# 07: Trabalhador robusto e reprocessamento

**What to build:** Um contabilista carrega um lote em que uma factura falha, e as restantes são codificadas na mesma. Uma factura que falhou por indisponibilidade do modelo pode ser reprocessada a partir do texto já extraído, sem novo carregamento. O custo em tokens fica visível por factura e acumulado por trabalho.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Uma falha numa factura deixa-a em `failed`, com o motivo, e o trabalho prossegue
- [ ] As falhas transitórias do classificador são repetidas com recuo exponencial, até um máximo configurável (três por omissão)
- [ ] Uma resposta inválida não é repetida
- [ ] O estado do trabalho mostra as facturas processadas, em curso, falhadas e totais
- [ ] O endpoint de reprocessamento recodifica a partir do texto extraído persistido, sem nova extracção
- [ ] Os tokens de entrada e de saída ficam registados por factura e acumulados por trabalho
- [ ] A indisponibilidade simulada do classificador não corrompe o estado
- [ ] Os testes usam o `FakeItemClassifier` a simular falhas transitórias e permanentes
