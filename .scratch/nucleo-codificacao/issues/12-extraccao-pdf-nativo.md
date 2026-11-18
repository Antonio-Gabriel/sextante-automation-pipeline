# 12: Extracção de PDF nativo no modelo das amostras

**What to build:** Um contabilista carrega facturas em PDF no modelo das amostras e o sistema extrai-as correctamente. A extracção tem de lidar com quatro particularidades: colunas lado a lado no cabeçalho, nome do fornecedor sobreposto na faixa de topo, descrições partidas a meio da palavra e valores no formato `1,206.00`.

Dois tipos de PDF são recusados com motivo visível, e nunca codificados:

- **PDF digitalizado sem texto**, como INV-011: motivo `pdf_without_text_layer`.
- **Documento que não é uma factura no modelo**, como a nota de liquidação da AGT (INV-012): motivo `unsupported_document_type`.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] O tipo do ficheiro é determinado pelos primeiros bytes, e não pela extensão nem pelo `Content-Type`
- [ ] O nome do fornecedor é lido da região da faixa de topo e não sai entrelaçado com "INVOICE / FACTURA" (casos INV-004 e INV-007)
- [ ] Os blocos FROM e BILL TO são separados pelas coordenadas das palavras
- [ ] O nome da entidade facturada é a primeira linha do bloco BILL TO; as linhas "c/o" e "a/c" ficam como "ao cuidado de"; o NIF de cada bloco é extraído
- [ ] O número, a data e a moeda são extraídos do cabeçalho e da coluna de valor
- [ ] Uma linha de continuação junta-se à anterior: sem espaço numa quebra a meio da palavra ("Tic" + "ket" dá "Ticket"), com espaço numa quebra num espaço
- [ ] A quantidade, o preço unitário, a percentagem de IVA e o valor são interpretados no formato `1,206.00`
- [ ] Subtotal, IVA e total são extraídos como linhas de resumo, e as observações como texto
- [ ] Todo o texto é normalizado para NFC e sem caracteres de controlo antes de ser persistido
- [ ] Um campo ausente fica vazio e registado como ausente, nunca inferido
- [ ] Um PDF com menos texto por página do que o mínimo configurado é recusado com `pdf_without_text_layer`
- [ ] Um documento sem a estrutura do modelo é recusado com `unsupported_document_type`
- [ ] Os testes usam réplicas sintéticas geradas por script e identificadas como sintéticas, que reproduzem as quatro particularidades. Nenhuma amostra real entra no repositório
- [ ] O `pdfplumber` (MIT) é a única dependência nova, com a licença verificada
