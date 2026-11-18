# 04: Revisão de linha

**What to build:** Uma pessoa abre uma linha e vê todos os itens da aba de destino dessa linha, ordenados por score, com a escolha do modelo marcada. Pode aceitar a linha, corrigir o código escolhendo um item da mesma aba, e deixar uma nota. Vê também o histórico das codificações da linha, com a revisão feita a cada uma, incluindo as anteriores a uma recodificação.

**Blocked by:** 03 (Ecrã de resultados com filtros)

**Status:** ready-for-agent

- [ ] Os candidatos mostram o score, a posição e a escolha do modelo
- [ ] O selector de correcção só oferece itens da aba de destino da linha; a validação continua a ser do servidor
- [ ] Uma linha sem aba de destino não oferece correcção e explica que a entidade da factura tem de ser resolvida
- [ ] Aceitar só é oferecido a uma linha pendente
- [ ] A nota respeita o comprimento máximo e mostra quanto falta
- [ ] Cada acção gera a sua `Idempotency-Key` antes do primeiro envio, e o botão fica desactivado durante o envio, por SEC-19
- [ ] O histórico mostra cada codificação, em vigor ou substituída, com a versão do prompt, o digest do catálogo e a revisão
- [ ] O `README.md` descreve a revisão de uma linha
- [ ] Testes do componente para aceitar, corrigir, a recusa do servidor e o envio repetido
