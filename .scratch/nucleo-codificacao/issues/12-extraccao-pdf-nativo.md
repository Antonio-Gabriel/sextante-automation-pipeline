# 12: Extracção de PDF nativo no modelo das amostras

**What to build:** Um contabilista carrega facturas em PDF no modelo das amostras e o sistema extrai-as correctamente. A extracção tem de lidar com quatro particularidades: colunas lado a lado no cabeçalho, nome do fornecedor sobreposto na faixa de topo, descrições partidas a meio da palavra e valores no formato `1,206.00`.

Dois tipos de PDF são recusados com motivo visível, e nunca codificados:

- **PDF digitalizado sem texto**, como INV-011: motivo `pdf_without_text_layer`.
- **Documento que não é uma factura no modelo**, como a nota de liquidação da AGT (INV-012): motivo `unsupported_document_type`.

**Blocked by:** 02

**Status:** resolved

- [x] O tipo do ficheiro é determinado pelos primeiros bytes, e não pela extensão nem pelo `Content-Type`
- [x] O nome do fornecedor é lido da região da faixa de topo e não sai entrelaçado com "INVOICE / FACTURA" (casos INV-004 e INV-007)
- [x] Os blocos FROM e BILL TO são separados pelas coordenadas das palavras
- [x] O nome da entidade facturada é a primeira linha do bloco BILL TO; as linhas "c/o" e "a/c" ficam como "ao cuidado de"; o NIF de cada bloco é extraído
- [x] O número, a data e a moeda são extraídos do cabeçalho e da coluna de valor
- [x] Uma linha de continuação junta-se à anterior: sem espaço numa quebra a meio da palavra ("Tic" + "ket" dá "Ticket"), com espaço numa quebra num espaço
- [x] A quantidade, o preço unitário, a percentagem de IVA e o valor são interpretados no formato `1,206.00`
- [x] Subtotal, IVA e total são extraídos como linhas de resumo, e as observações como texto
- [x] Todo o texto é normalizado para NFC e sem caracteres de controlo antes de ser persistido
- [x] Um campo ausente fica vazio e registado como ausente, nunca inferido
- [x] Um PDF com menos texto por página do que o mínimo configurado é recusado com `pdf_without_text_layer`
- [x] Um documento sem a estrutura do modelo é recusado com `unsupported_document_type`
- [x] Os testes usam réplicas sintéticas geradas por script e identificadas como sintéticas, que reproduzem as quatro particularidades. Nenhuma amostra real entra no repositório
- [x] O `pdfplumber` (MIT) é a única dependência nova, com a licença verificada

## Comments

Resolved on 2026-11-18 (CHG-0030). The layout is read from word coordinates: the supplier name is the largest font of the top band, FROM and BILL TO are split at the x of the "BILL TO" label, and table cells go to the column whose heading ends nearest, since they are right-aligned. A continuation row is joined from the raw characters, so a leading space tells a break on a space from a break mid-word. All 12 samples extract as the golden proposal expects (ticket 13), checked locally; the tests use synthetic replicas written by hand as PDF objects, with no PDF library. XLSX stays refused with `extractor_not_configured` (D-3.6). A truncated or unreadable PDF is refused as `unsupported_document_type`, not failed, because reading it again gives the same result.

Review fixes on 2026-11-18 (CHG-0032): the minimum of text holds for every page, not on average; a missing field is also recorded in the audit trail (`extraction_fields_missing`), by name; the synthetic fixtures no longer carry identifiers, names or descriptions taken from the samples.
