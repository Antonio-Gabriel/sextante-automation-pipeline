# 02: Tecto de chamadas ao modelo no trabalhador

**What to build:** Quando o trabalhador atinge um número máximo de chamadas ao modelo numa janela de tempo, as facturas seguintes esperam na fila em vez de serem recusadas ou perdidas, e são codificadas quando a janela abre de novo. É o limite que protege o orçamento, como SEC-12 pede.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] O tecto e a janela são configuráveis, com valores por omissão declarados
- [ ] Acima do tecto, a factura fica `queued` e é codificada depois; nenhuma factura passa a `failed` por causa do tecto
- [ ] O estado do trabalho mostra que há facturas à espera do tecto
- [ ] O log regista quando o tecto atrasa trabalho, sem conteúdo de facturas
- [ ] O `README.md` explica o tecto e como o ajustar
- [ ] Testes com o `FakeItemClassifier` e um relógio controlado, que provam que o tecto atrasa e não perde trabalho
