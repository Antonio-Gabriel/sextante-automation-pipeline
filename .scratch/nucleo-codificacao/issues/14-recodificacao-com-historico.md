# 14: Recodificação com histórico

**What to build:** Depois de mudar um limiar ou a versão do prompt, um responsável pede que uma factura já codificada seja codificada de novo, a partir do texto guardado, sem novo carregamento nem nova extracção. A nova codificação fica em vigor e a anterior continua consultável, com a versão do prompt e o digest do catálogo de cada uma. O pedido nunca apaga nem altera o resultado anterior.

**Blocked by:** 11 (adaptador Claude e prompt v1)

**Status:** resolved

- [x] O pedido é aceite para facturas codificadas, além das com falha, e exige `Idempotency-Key`
- [x] Cada recodificação escreve novas linhas de resultado; as anteriores ficam, marcadas como substituídas (SEC-19, «Reprocessamento»)
- [x] Os resultados e a exportação mostram só a codificação em vigor
- [x] Uma revisão humana feita sobre a codificação anterior não se perde em silêncio: o que lhe acontece é decidido antes de implementar
- [x] A recodificação gera um evento de auditoria com a versão do prompt e o digest do catálogo anteriores e novos
- [x] Os testes usam o `FakeItemClassifier`; nenhum chama a API da Anthropic

## Comments

Created on 2026-11-18 from the review of tickets 07 and 08 (00-decisoes-e-lacunas.md §3.20). Open question before implementation: whether a re-coding keeps, discards or flags the human reviews of the previous coding.

Prerequisite found in the review of tickets 09 and 10 (CHG-0028): `encoded_line` already keeps superseded codings (migration 0007), but `lexical_score` has primary key (invoice_line_id, item_number) and no link to a coding. Coding again a line that already has scores fails on that key, and the candidates endpoint could not tell current scores from earlier ones. This ticket must link scores to the coding (or supersede them) before re-coding coded invoices.

Unblocked on 2026-11-18: ticket 11 is resolved. Still needs-triage for the open question above, on what happens to the human reviews of the previous coding.

Resolved on 2026-11-18 (CHG-0043), with the owner's decision on reviews (00-decisoes-e-lacunas.md §3.23): a line a reviewer had accepted or corrected goes back to review with the flag `review_superseded`; the earlier review stays with the earlier coding and in the audit trail. Lexical scores are now keyed by coding (migration 0009), so both codings of a line keep their own. The audit event `invoice_recoded` records earlier and new prompt versions and catalog digests. A refused or ambiguous invoice is still refused with 409.
