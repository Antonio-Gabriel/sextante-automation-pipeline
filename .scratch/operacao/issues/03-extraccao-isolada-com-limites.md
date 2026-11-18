# 03: Extracção de PDF isolada com limites

**What to build:** A leitura de um PDF corre num processo à parte, com limite de memória e de tempo. Um ficheiro construído para expandir na descompressão, ou que demora demais a ler, é recusado com um motivo visível, e o trabalhador continua a processar as outras facturas.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] A extracção corre num processo separado, com limite de memória e de tempo configuráveis
- [x] Ultrapassar um limite recusa o documento como não suportado, nunca derruba o trabalhador
- [x] Os resultados da extracção de um PDF válido são os mesmos de antes
- [x] O log regista o limite atingido, sem conteúdo do ficheiro
- [x] O `README.md` explica os limites e como os ajustar
- [x] Testes com um PDF sintético que expande na descompressão e com um que excede o tempo

Resolved on 2026-11-19 (CHG-0053): each PDF is read in a child process started from a forkserver, with an address-space limit and a time limit, off the event loop. Over a limit the document is refused as `unsupported_document_type` and the log records the limit. Defaults 512 MiB and 30 s.

Review fixes on 2026-11-19 (CHG-0054): closed sets for the limit and the child messages; a silent child death counts as memory only when it was SIGKILL, any other fails the invoice; CPU time limit in the child; memory limit fails closed on Linux and is declared unavailable elsewhere; process context built on first use; parity tests for refusals; Linux-only tests skip elsewhere; fixtures share one document builder.
