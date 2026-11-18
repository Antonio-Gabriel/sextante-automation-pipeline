# 01: Limites de taxa por endpoint

**What to build:** Quem chamar a API depressa demais recebe `429` com `Retry-After`, nos limites da tabela de SEC-12: carregamento, reprocessamento, exportação, correcção de linha e API geral. A limitação com mais do que uma instância fica provada, e não suposta.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Os limites de SEC-12 aplicados por endpoint, com a chave da sessão ou da API como identidade
- [ ] Acima do limite, `429` com `Retry-After` e a mensagem de erro habitual em Português
- [ ] `/api/health` fica fora dos limites
- [ ] Um teste documentado como falhando com duas instâncias, porque o contador vive em memória do processo
- [ ] Os limites são configuráveis, com os valores de SEC-12 por omissão
- [ ] O `README.md` lista os limites e diz que, com mais do que uma instância, é preciso um contador partilhado
- [ ] Testes pela API acima e abaixo de cada limite
