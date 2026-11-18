# 13: Conjunto dourado com as amostras

**What to build:** A equipa corre `make golden` e vê, para cada amostra, se a extracção, a entidade, a aba de destino, os tipos de linha e as recusas correspondem ao esperado.

- **As amostras** são lidas de um caminho local configurado por variável de ambiente, e nunca do repositório.
- **Os resultados esperados** ficam num ficheiro de configuração editável. Usam os códigos do catálogo actual e podem evoluir com ele.
- **A medição dos códigos de item com o modelo real** é um comando manual e explícito, fora da suite de testes.

Nenhuma métrica de precisão é publicada até a AMT confirmar os resultados esperados.

**Proposta inicial de resultados esperados** (por confirmar pela AMT):

| Amostra | Entidade | Aba | Linha | Código esperado |
|---|---|---|---|---|
| INV-001 | MATCH | OUTLAYS | Passagem aérea Sintética - Rota Teste | O00004 Bilhete Avião |
| INV-002 | NO_MATCH (cliente, c/o AMT) | OUTLAYSP | Sobrestadia sintética - Container | O00031 Sobrestadia Contentor |
| INV-003 | MATCH (LDA, sem hífen) | OUTLAYS | Taxa de pilotagem sintética | O00028 Pilotagem |
| INV-003 | | | Serviços de mergulho sintéticos | O00043 Serviços de mergulho |
| INV-004 | NO_MATCH (petrolífera cliente) | OUTLAYSP | Escolta aduaneira de carga sintética | O00017 Escolta Alfandega |
| INV-005 | MATCH | OUTLAYS | Envio sintético de documentos (BL) | O00051 Correio Express |
| INV-006 | NO_MATCH (empresa de serviços petrolíferos) | OUTLAYSP | Consulta médica sintética | O00019 Factura da Clínica |
| INV-007 | MATCH | OUTLAYS | Operações logísticas sintéticas | O00036 Sonils |
| INV-008 | NO_MATCH (empresa de engenharia) | OUTLAYSP | Reparação sintética de viatura | O00999 (recurso) |
| INV-009 | MATCH | OUTLAYS | Alojamento de 2 noites | O00020 Factura de Hotel |
| INV-009 | | | Serviço de restaurante sintético | O00021 Factura de Restaurante |
| INV-010 | NO_MATCH (empresa irmã, NIF diferente) | OUTLAYSP | Emissão sintética de certificado CNCA | O00063 Obtenção CNCA |
| INV-011 | Recusada: `pdf_without_text_layer` | | | |
| INV-012 | Recusada: `unsupported_document_type` | | | |

**Blocked by:** 03, 04, 05, 11, 12

**Status:** ready-for-agent

- [ ] Os resultados esperados ficam num ficheiro de configuração editável, inicialmente com a tabela acima
- [ ] O caminho das amostras vem de uma variável de ambiente; sem ela, `make golden` termina com uma mensagem clara
- [ ] `make golden` mede, sem chamar o modelo, a extracção, a entidade, a aba de destino, os tipos de linha e as recusas, e falha quando divergem do esperado
- [ ] Um comando manual separado mede os códigos de item com o modelo real e reporta acertos, linhas sinalizadas e custo em tokens
- [ ] O comando manual não faz parte de `make test` nem da integração contínua
- [ ] O `README.md` diz que os resultados esperados são uma proposta por confirmar e que os limiares são provisórios
- [ ] Nenhuma amostra, nem nenhum excerto de amostra, entra no repositório ou nos logs
