# 07: Trabalhador robusto e reprocessamento

**What to build:** Um contabilista carrega um lote em que uma factura falha, e as restantes são codificadas na mesma. Uma factura que falhou por indisponibilidade do modelo pode ser reprocessada a partir do texto já extraído, sem novo carregamento. O custo em tokens fica visível por factura e acumulado por trabalho.

**Blocked by:** 02

**Status:** resolved

- [x] Uma falha numa factura deixa-a em `failed`, com o motivo, e o trabalho prossegue
- [x] As falhas transitórias do classificador são repetidas com recuo exponencial, até um máximo configurável (três por omissão)
- [x] Uma resposta inválida não é repetida
- [x] O estado do trabalho mostra as facturas processadas, em curso, falhadas e totais
- [x] O endpoint de reprocessamento recodifica a partir do texto extraído persistido, sem nova extracção
- [x] Os tokens de entrada e de saída ficam registados por factura e acumulados por trabalho
- [x] A indisponibilidade simulada do classificador não corrompe o estado
- [x] Os testes usam o `FakeItemClassifier` a simular falhas transitórias e permanentes

## Comments

Resolved on 2026-11-18 (CHG-0023). Only `ItemClassifierUnavailableError` is retried; the Claude adapter of ticket 11 must raise it for timeouts, overload and network errors, and nothing else. Reprocessing accepts failed invoices only; an invoice already queued is left as it is, so a repeated request queues it once.

Review fixes on 2026-11-18 (CHG-0025): tokens are now shown per invoice in the job status, as the ticket text asks. Open for the human: NFR-REL-002 gives recalibration as the reason for reprocessing, and SEC-19 says a reprocessing writes a new result line; this ticket reprocesses failed invoices only, so re-coding an already coded invoice, with its history kept, is not built.

Decided on 2026-11-18 (CHG-0026): reprocessing stays limited to failed invoices in this version (00-decisoes-e-lacunas.md §3.20); re-coding with history is ticket 14, blocked by 11.
