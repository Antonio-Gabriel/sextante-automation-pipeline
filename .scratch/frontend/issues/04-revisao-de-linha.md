# 04: Revisão de linha

**What to build:** Uma pessoa abre uma linha e vê todos os itens da aba de destino dessa linha, ordenados por score, com a escolha do modelo marcada. Pode aceitar a linha, corrigir o código escolhendo um item da mesma aba, e deixar uma nota. Vê também o histórico das codificações da linha, com a revisão feita a cada uma, incluindo as anteriores a uma recodificação.

**Blocked by:** 03 (Ecrã de resultados com filtros)

**Status:** resolved

- [x] Os candidatos mostram o score, a posição e a escolha do modelo
- [x] O selector de correcção só oferece itens da aba de destino da linha; a validação continua a ser do servidor
- [x] Uma linha sem aba de destino não oferece correcção e explica que a entidade da factura tem de ser resolvida
- [x] Aceitar só é oferecido a uma linha pendente
- [x] A nota respeita o comprimento máximo e mostra quanto falta
- [x] Cada acção gera a sua `Idempotency-Key` antes do primeiro envio, e o botão fica desactivado durante o envio, por SEC-19
- [x] O histórico mostra cada codificação, em vigor ou substituída, com a versão do prompt, o digest do catálogo e a revisão
- [x] O `README.md` descreve a revisão de uma linha
- [x] Testes do componente para aceitar, corrigir, a recusa do servidor e o envio repetido

## Comments

Resolved on 2026-11-19 (CHG-0063), after ticket 05: the line's job and description come from the invoice endpoint and the invoice's results.
