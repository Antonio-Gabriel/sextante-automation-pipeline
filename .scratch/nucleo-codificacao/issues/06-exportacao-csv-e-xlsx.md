# 06: Exportação em CSV e XLSX

**What to build:** Um contabilista exporta um trabalho em CSV ou em XLSX e recebe as nove colunas do enunciado, por ordem e com os nomes exactos, com os valores revistos em vigor.

O ficheiro inclui:

- **as linhas de facturas ambíguas**, com a aba de destino vazia;
- **as facturas recusadas**, com uma linha que traz o motivo da recusa em `Notes_or_Flags`.

O identificador da factura combina o fornecedor e o número da factura.

**Blocked by:** 03, 04

**Status:** ready-for-agent

- [ ] As colunas são, por esta ordem: `Invoice_ID`, `Billed_Entity_Detected`, `Exact_Entity_Match`, `Target_Sheet`, `Line_Description`, `Assigned_Item_No`, `Matched_Catalog_Description`, `Confidence`, `Notes_or_Flags`
- [ ] A exportação é gerada a partir do estado persistido e reflecte as revisões em vigor
- [ ] O CSV é UTF-8 com BOM, com separador configurável e vírgula por omissão
- [ ] Toda a célula que comece por `=`, `+`, `-`, `@`, tabulação ou retorno de carro é prefixada com apóstrofo, em CSV e em XLSX
- [ ] O fornecedor é identificado pelo NIF quando extraído, e pelo nome normalizado quando não
- [ ] `Invoice_ID` é `<fornecedor>/<número>`, ou `<fornecedor>/<digest curto>` quando falta o número, e nunca um contador
- [ ] `Matched_Catalog_Description` é a descrição PT do catálogo, sem espaços nas pontas
- [ ] `Notes_or_Flags` junta os motivos de sinalização em português, as notas de tipo de linha, as linhas "ao cuidado de" e a nota de revisão
- [ ] Uma recusa simulada pelo `FakeInvoiceExtractor` aparece na exportação com o motivo
- [ ] Os testes pela API verificam as colunas, a ordem, o BOM, a neutralização e o reflexo de uma correcção
