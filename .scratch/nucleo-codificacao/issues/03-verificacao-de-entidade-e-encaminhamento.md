# 03: Verificação de entidade completa e encaminhamento para OUTLAYSP

**What to build:** Um contabilista vê cada factura encaminhada de acordo com a entidade facturada:

- **A AMT**, com variações menores no nome: vai para OUTLAYS.
- **Uma entidade claramente diferente** (cliente terceiro, companhia de navegação ou empresa irmã): vai para OUTLAYSP.
- **Uma entidade que não se pode decidir sem um humano:** fica por codificar, com a aba de destino vazia e o motivo na sinalização.

A verificação é uma função de domínio pura que aplica, por ordem, as sete regras da spec: lista de exclusão, NIF, igualdade normalizada e limiar baixo.

A entidade facturada é a primeira linha do bloco. As linhas "ao cuidado de" nunca entram na verificação; ficam registadas e aparecem na nota.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] A normalização trata maiúsculas, pontuação, hífen, espaços, acentos e os sufixos `limitada`, `lda` e `ltda`
- [ ] A semelhança não usa `token_set_ratio`, e um nome contido no nome alvo não dá 100
- [ ] A lista de exclusão vem de configuração, é avaliada primeiro, e nasce com estrutura mas sem conteúdo (L-04)
- [ ] O NIF da entidade alvo vem de configuração. Um NIF extraído e diferente impede `MATCH`; com o nome igual dá `AMBIGUOUS` com `entity_nif_mismatch`
- [ ] Um NIF igual ao da entidade alvo nunca dá `MATCH` sozinho
- [ ] Nenhum modelo de linguagem é chamado na verificação
- [ ] Testes de tabela na função de domínio cobrem:
  - [ ] nome exacto
  - [ ] `LDA` em maiúsculas e sem hífen, como em INV-003
  - [ ] nome com acentos
  - [ ] cliente terceiro, como petrolífera cliente, empresa de serviços petrolíferos e empresa de engenharia
  - [ ] cliente com "c/o Advanced Maritime Transports", como em INV-002, que dá NO_MATCH
  - [ ] empresa irmã "AMT - Empresa Irmã Sintética Limitada" com NIF diferente, como em INV-010
  - [ ] empresa irmã na lista de exclusão com nome quase igual
  - [ ] irmã não listada, com o nome do alvo e um sufixo geográfico
  - [ ] nome do alvo com NIF diferente
  - [ ] nome contido no nome alvo
  - [ ] nenhum bloco
  - [ ] dois blocos
- [ ] Pela API, uma não correspondência é codificada contra OUTLAYSP
- [ ] Pela API, uma factura ambígua não chama o classificador, e as suas linhas ficam com `Exact_Entity_Match = NO`, aba de destino vazia, sem código, com `LOW` e sinalizadas
- [ ] A entidade facturada é guardada tal como foi extraída, sem normalização
