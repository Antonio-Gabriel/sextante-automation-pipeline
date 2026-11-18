# 03: Extracção de PDF isolada com limites

**What to build:** A leitura de um PDF corre num processo à parte, com limite de memória e de tempo. Um ficheiro construído para expandir na descompressão, ou que demora demais a ler, é recusado com um motivo visível, e o trabalhador continua a processar as outras facturas.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] A extracção corre num processo separado, com limite de memória e de tempo configuráveis
- [ ] Ultrapassar um limite recusa o documento como não suportado, nunca derruba o trabalhador
- [ ] Os resultados da extracção de um PDF válido são os mesmos de antes
- [ ] O log regista o limite atingido, sem conteúdo do ficheiro
- [ ] O `README.md` explica os limites e como os ajustar
- [ ] Testes com um PDF sintético que expande na descompressão e com um que excede o tempo
