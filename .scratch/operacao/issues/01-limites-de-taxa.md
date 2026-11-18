# 01: Limites de taxa por endpoint

**What to build:** Quem chamar a API depressa demais recebe `429` com `Retry-After`, nos limites da tabela de SEC-12: carregamento, reprocessamento, exportação, correcção de linha e API geral. A limitação com mais do que uma instância fica provada, e não suposta.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] Os limites de SEC-12 aplicados por endpoint, com a chave da sessão ou da API como identidade
- [x] Acima do limite, `429` com `Retry-After` e a mensagem de erro habitual em Português
- [x] `/api/health` fica fora dos limites
- [x] Um teste documentado como falhando com duas instâncias, porque o contador vive em memória do processo
- [x] Os limites são configuráveis, com os valores de SEC-12 por omissão
- [x] O `README.md` lista os limites e diz que, com mais do que uma instância, é preciso um contador partilhado
- [x] Testes pela API acima e abaixo de cada limite

## Comments

Resolved on 2026-11-19 (CHG-0049). Fixed windows on a monotonic clock, separate from the business clock, per caller: the API key's digest, or the client address without a key. Every `/api` call counts against the general limit; upload, reprocessing, export and correction also against their own. The key check runs first, so a refused credential never uses a quota. The two-instance limitation is a strict xfail test that fails on the expected assertion.

Review fixes on 2026-11-19 (CHG-0050): closed set of rules, costly endpoints named by route function, nothing counted when any limit refuses, memory bounded per caller, `Retry-After` through a hook on the domain error, entity resolution and acceptance under the costly limits, and tests for the defaults and for a repeated Idempotency-Key.
