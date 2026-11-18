# 04: Retenção e purga dos dados (L-11)

**What to build:** Os dados de facturas não ficam guardados para sempre. O ficheiro original, o texto extraído e os registos de auditoria têm prazos de retenção configuráveis, e uma tarefa periódica apaga o que passou do prazo, deixando na auditoria o que foi apagado e quando, sem o conteúdo.

**Blocked by:** None (can start immediately)

**Status:** needs-info

- [ ] Prazos configuráveis para o ficheiro original, o texto extraído e a auditoria
- [ ] Uma tarefa periódica apaga o que passou do prazo; a auditoria só de inserção (SEC-04) é tratada à parte, por decisão explícita
- [ ] Apagar o texto extraído impede o reprocessamento dessa factura, e o pedido de reprocessamento diz porquê
- [ ] O `README.md` documenta os prazos e o que se perde quando passam
- [ ] Testes com um relógio controlado

## Comments

Status needs-info: os prazos dependem da resposta da AMT a L-11 (com apoio jurídico). A sugestão registada em `docs/00-decisoes-e-lacunas.md` serve de ponto de partida, mas não se aplica por omissão.
