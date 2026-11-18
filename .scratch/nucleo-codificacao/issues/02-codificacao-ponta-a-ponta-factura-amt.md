# 02: Codificação completa de uma factura da AMT (caminho feliz)

**What to build:** Um contabilista carrega uma factura e recebe logo um identificador de trabalho. O trabalhador codifica a factura, e o contabilista consulta pela API o resultado de cada linha: o código de item, a descrição do catálogo e a aba de destino.

O caso de demonstração é uma réplica sintética de INV-001, gerada por script e identificada como sintética:

1. A companhia aérea factura a AMT com o nome exacto.
2. A verificação dá correspondência, e a factura vai para OUTLAYS.
3. "Passagem aérea Sintética - Rota Teste" recebe `O00004 Bilhete Avião`.

A porta `InvoiceExtractor` fica definida com a forma real das amostras. Devolve uma de duas coisas:

- **Uma factura extraída**, com:
  - fornecedor: nome e NIF;
  - número, data e moeda;
  - bloco da entidade facturada: nome na primeira linha, linhas "ao cuidado de", morada e NIF;
  - linhas: descrição, quantidade, preço unitário, percentagem de IVA e valor;
  - linhas de resumo e observações.
- **Uma recusa com motivo.**

Neste ticket só existe o `FakeInvoiceExtractor`, que devolve facturas já interpretadas. A verificação de entidade só precisa de reconhecer a igualdade com o nome alvo; as restantes regras são do ticket 03.

**Blocked by:** 01

**Status:** resolved

- [x] O carregamento devolve um identificador de trabalho sem esperar pela codificação
- [x] Carregar o mesmo ficheiro outra vez devolve o mesmo trabalho, garantido por uma restrição única sobre o digest
- [x] O trabalhador reivindica o trabalho de forma atómica e codifica a factura
- [x] São calculados e persistidos os scores lexicais de **todos** os itens da aba de destino, para cada linha. O score é o máximo entre PT e EN
- [x] A porta `ItemClassifier` recebe a aba de destino inteira, por ordem fixa do catálogo, com índice, código, PT e EN, e devolve um índice ou `none` por linha
- [x] O índice devolvido é validado pelo esquema (tecto de 100) e depois contra o comprimento real da lista e contra a aba de destino, antes de ser persistido
- [x] O código persistido é exactamente o valor de `No.` do catálogo
- [x] A consulta dos resultados devolve as linhas pela ordem do documento
- [x] Cada linha codificada tem um registo de auditoria com: descrição original e normalizada, aba de destino, scores, escolha do modelo, identificador do modelo, versão do prompt, digest do catálogo e momento
- [x] Os logs não contêm descrições, nomes, valores nem o corpo do prompt
- [x] Os testes passam pela API HTTP, com `FakeInvoiceExtractor` e `FakeItemClassifier`, sem nenhuma chamada à API da Anthropic

## Comments

Resolved on 2026-11-18 in commits 2eff0ce (implementation) and the code review fixes that follow it, on branch feature/REQ-PLT-007-startup-catalog-validation.

Deferred on purpose, to the tickets that own them:
- invoice_header columns for the entity check result and ambiguity reason: ticket 03;
- supplier identifier, exported Invoice_ID and the (supplier, invoice number) index: tickets 06 and 10;
- confidence, flags and the O00999 fallback: ticket 04;
- HTTP Idempotency-Key header (SEC-19): ticket 08; upload idempotency by digest is in place;
- retries and reprocessing: ticket 07;
- real PDF extractor and Claude adapter: tickets 12 and 11. Until then placeholder adapters refuse with an explicit reason and never code.

SEC-16 is partial: two-step quarantine, Nginx limits and the ZIP-bomb ceiling arrive with the real extractor (ticket 12).
