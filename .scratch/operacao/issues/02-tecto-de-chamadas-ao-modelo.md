# 02: Tecto de chamadas ao modelo no trabalhador

**What to build:** Quando o trabalhador atinge um número máximo de chamadas ao modelo numa janela de tempo, as facturas seguintes esperam na fila em vez de serem recusadas ou perdidas, e são codificadas quando a janela abre de novo. É o limite que protege o orçamento, como SEC-12 pede.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] O tecto e a janela são configuráveis, com valores por omissão declarados
- [x] Acima do tecto, a factura fica `queued` e é codificada depois; nenhuma factura passa a `failed` por causa do tecto
- [x] O estado do trabalho mostra que há facturas à espera do tecto
- [x] O log regista quando o tecto atrasa trabalho, sem conteúdo de facturas
- [x] O `README.md` explica o tecto e como o ajustar
- [x] Testes com o `FakeItemClassifier` e um relógio controlado, que provam que o tecto atrasa e não perde trabalho

Resolved on 2026-11-19 (CHG-0051): the worker counts every model call, retries included, in fixed windows; over the ceiling it waits before the next invoice, which stays `queued`, and the job shows `waiting_model`. Default 200 calls per hour, provisional.

Review fixes on 2026-11-19 (CHG-0052): the wait now happens at the model call, so retries mark the job and invoices without a model call never wait; job status changes are conditional, so a reprocessing during a wait is coded; at startup the jobs a stopped process left claimed are queued again; window maths shared with the rate limits; unit tests for the ceiling.
