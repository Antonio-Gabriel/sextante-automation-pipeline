# 07: Listar e apagar trabalhos

**What to build:** Uma pessoa vê todos os trabalhos do servidor, do mais recente para o mais antigo, e apaga um trabalho terminado de que já não precisa, depois de confirmar num modal. O apagamento é lógico: os registos ficam, e carregar de novo um ficheiro do trabalho restaura-o com as revisões que tinha. Pedido pelo responsável em 19-11-2026, junto com melhorias de UX da tabela de resultados e do carregamento.

**Blocked by:** 02 (Carregamento com progresso), 03 (Resultados com filtros)

**Status:** resolved

- [x] `GET /api/jobs` lista os trabalhos não apagados, paginado, sem nomes de ficheiro
- [x] `DELETE /api/jobs/{job_id}` apaga um trabalho concluído ou com falha, com `Idempotency-Key` e auditoria; um trabalho na fila ou a correr é recusado com 409
- [x] Um trabalho apagado sai de todas as leituras e acções; os registos ficam
- [x] Carregar de novo um ficheiro de um trabalho apagado restaura-o, e a resposta indica-o
- [x] Página «Trabalhos» com apagamento por modal de confirmação, também no ecrã do trabalho
- [x] Tabela de resultados: a linha inteira, a descrição e um botão fixo à direita abrem a revisão
- [x] Carregamento centrado, com a lista de ficheiros, notas sobre o que o servidor faz e os últimos trabalhos
- [x] Testes do backend com `@pytest.mark.requirement` e testes de componente do frontend

## Comments

Decisions taken by the owner on 19-11-2026: restore on re-upload, only finished jobs, a «Trabalhos» page with a server list. Recorded in docs/00 §3.24 and REQ-PLT-009.
