# 06: Exportação em CSV e XLSX

**What to build:** Um contabilista exporta um trabalho em CSV ou em XLSX e recebe as nove colunas do enunciado, por ordem e com os nomes exactos, com os valores revistos em vigor.

O ficheiro inclui:

- **as linhas de facturas ambíguas**, com a aba de destino vazia;
- **as facturas recusadas**, com uma linha que traz o motivo da recusa em `Notes_or_Flags`.

O identificador da factura combina o fornecedor e o número da factura.

**Blocked by:** 03, 04

**Status:** resolved

- [x] As colunas são, por esta ordem: `Invoice_ID`, `Billed_Entity_Detected`, `Exact_Entity_Match`, `Target_Sheet`, `Line_Description`, `Assigned_Item_No`, `Matched_Catalog_Description`, `Confidence`, `Notes_or_Flags`
- [x] A exportação é gerada a partir do estado persistido e reflecte as revisões em vigor
- [x] O CSV é UTF-8 com BOM, com separador configurável e vírgula por omissão
- [x] Toda a célula que comece por `=`, `+`, `-`, `@`, tabulação ou retorno de carro é prefixada com apóstrofo, em CSV e em XLSX
- [x] O fornecedor é identificado pelo NIF quando extraído, e pelo nome normalizado quando não
- [x] `Invoice_ID` é `<fornecedor>/<número>`, ou `<fornecedor>/<digest curto>` quando falta o número, e nunca um contador
- [x] `Matched_Catalog_Description` é a descrição PT do catálogo, sem espaços nas pontas
- [x] `Notes_or_Flags` junta os motivos de sinalização em português, as notas de tipo de linha, as linhas "ao cuidado de" e a nota de revisão
- [x] Uma recusa simulada pelo `FakeInvoiceExtractor` aparece na exportação com o motivo
- [x] Os testes pela API verificam as colunas, a ordem, o BOM, a neutralização e o reflexo de uma correcção *(o reflexo de uma correcção entrou com o ticket 08, CHG-0024)*

## Comments

Resolved on 2026-11-18 (CHG-0021). Review notes join Notes_or_Flags when ticket 08 adds them. A failed invoice also gets one LOW row, like a refused document, so nothing uploaded is missing from the export.

Code review on 2026-11-18 (CHG-0022):
- The test that a correction shows in the export waits for ticket 08, which adds corrections. The export already reads the persisted state (tested across a restart), so it will reflect them without change.
- The supplier identifier and the exported Invoice_ID are computed at export time from persisted fields, not stored as columns. Ticket 10 stores the supplier identifier when it needs the (supplier, number) index.
- With no supplier NIF and no supplier name, Invoice_ID is the number (or short digest) alone: the spec does not define that case, and inventing a supplier would be filling a gap by default.
