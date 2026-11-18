# Sextante

Codificação de linhas de facturas de fornecedores recebidas pela AMT (Advanced Maritime Transports - Transitarios Limitada) contra o catálogo de itens de despesa. Cada termo tem o identificador de código em inglês entre parênteses.

## Factura

**Factura de fornecedor** (`invoice`):
Documento emitido por um fornecedor, em PDF ou XLSX, que chega à AMT para ser codificado.
_Evitar_: documento, ficheiro (o ficheiro é só o suporte)

**Fornecedor** (`supplier`):
Quem emite a factura.
_Evitar_: vendedor, emitente

**Identificador da factura** (`invoice_id`):
Identificador exportado de uma factura, composto pelo fornecedor e pelo número da factura.
_Evitar_: número da factura (é só uma parte do identificador)

**Documento não suportado** (`unsupported_document`):
Documento carregado que não é uma factura de fornecedor no formato aceite, como uma nota de liquidação aduaneira, ou um PDF digitalizado sem texto. É recusado com motivo e não é codificado.
_Evitar_: factura inválida

**Duplicado provável** (`possible_duplicate`):
Factura com o mesmo fornecedor e o mesmo número de outra já carregada, mas com conteúdo de ficheiro diferente.

## Linhas

**Linha de factura** (`invoice_line`):
Uma linha da tabela de uma factura que representa um serviço, um imposto ou um desconto.
_Evitar_: item, linha (sozinhos)

**Tipo de linha** (`line_type`):
Classificação de uma linha de factura: serviço (`service`), imposto (`tax`) ou desconto (`discount`). Só as linhas de serviço são codificadas.

**Linha de resumo** (`summary_row`):
Subtotal ou total impresso na tabela da factura. Não é uma linha de factura e não aparece na saída.
_Evitar_: linha de total, linha de subtotal (como linhas de factura)

## Entidade

**Entidade facturada** (`billed_entity`):
A pessoa colectiva a quem a factura é dirigida: o titular da secção "Bill To" ou "Cliente", nunca quem aparece ao cuidado de.
_Evitar_: cliente (ambíguo, ver Cliente terceiro), destinatário

**Ao cuidado de** (`care_of`):
Entidade indicada com "c/o" ou "a/c" na secção da entidade facturada, que recebe a factura em nome do titular sem ser a entidade facturada.
_Evitar_: entidade facturada secundária

**Entidade alvo** (`target_entity`):
A AMT, a única entidade cuja correspondência encaminha para OUTLAYS.

**Verificação de entidade** (`entity_check`):
Passo que compara a entidade facturada com a entidade alvo e produz correspondência, não correspondência ou entidade ambígua.

**Correspondência** (`MATCH`):
A entidade facturada é a entidade alvo, a menos de maiúsculas, pontuação, hífen, espaços, acentos e forma do sufixo societário.
_Evitar_: correspondência exacta (a coluna `Exact_Entity_Match` usa este termo, mas com esta tolerância)

**Não correspondência** (`NO_MATCH`):
A entidade facturada é, com certeza, outra que não a entidade alvo: consta da lista de exclusão ou não se parece com ela.

**Entidade ambígua** (`AMBIGUOUS`):
Não é possível afirmar correspondência nem não correspondência sem um humano: falta o rótulo de entidade, há mais do que uma entidade facturada, ou o nome é parecido com o da entidade alvo sem ser igual. Uma factura com entidade ambígua não é codificada até haver resolução de entidade.
_Evitar_: entidade indeterminada, entidade incerta, desempate

**Resolução de entidade** (`entity_resolution`):
Decisão humana que transforma uma entidade ambígua em correspondência ou não correspondência, com nota obrigatória, e que desbloqueia a codificação da factura.

**Lista de exclusão** (`entity_denylist`):
Entidades que são sempre não correspondência, por muito parecido que seja o nome: empresas irmãs, companhias de navegação e clientes conhecidos.
_Evitar_: blacklist, lista negra

**Empresa irmã** (`sister_company`):
Empresa do mesmo grupo da AMT, normalmente com nome muito parecido, que não é a entidade alvo.

**Cliente terceiro** (`third_party_client`):
Cliente da AMT em nome de quem um fornecedor pode facturar uma despesa.

## Catálogo

**Catálogo** (`catalog`):
O ficheiro mestre de itens de despesa, com duas abas, OUTLAYS e OUTLAYSP.
_Evitar_: master, lista de itens

**Aba** (`sheet`):
Uma das duas partes do catálogo, OUTLAYS ou OUTLAYSP. Cada item pertence a uma só aba.
_Evitar_: folha, separador, tab

**OUTLAYS**:
Aba das despesas facturadas à própria AMT.

**OUTLAYSP**:
Aba das despesas facturadas em nome de outra entidade (cliente, empresa irmã, companhia de navegação) e suportadas pela AMT por conta dela.

**Item do catálogo** (`catalog_item`):
Uma linha do catálogo: código de item, descrição em português e descrição em inglês.
_Evitar_: item (sozinho), produto, serviço

**Código de item** (`item_number`):
O valor exacto da coluna `No.` de um item do catálogo. O prefixo não identifica a aba.
_Evitar_: código, número de item, item

## Codificação

**Codificação** (`encoding`):
Atribuição de um código de item a uma linha de serviço, ou a decisão registada de não atribuir nenhum.
_Evitar_: mapeamento, classificação (classificação é a do tipo de linha)

**Encaminhamento** (`routing`):
Escolha da aba de destino de uma factura a partir do resultado da verificação de entidade: correspondência leva a OUTLAYS, não correspondência leva a OUTLAYSP.

**Aba de destino** (`target_sheet`):
A aba contra a qual as linhas de uma factura são codificadas. Fica vazia quando a entidade é ambígua.

**Candidatos** (`candidates`):
Os itens do catálogo da aba de destino, apresentados ao modelo para ele escolher um.

**Item genérico** (`generic_catalog_item`):
Item do catálogo que serve para qualquer despesa, como `O00052 Outras Despesas`. Escolhê-lo é válido, mas a linha fica sempre com confiança baixa e sinalizada.
_Evitar_: item por omissão, recurso de OUTLAYS

**Recurso** (`fallback`):
Atribuição de `O00999` ("Despesas faturadas com o nome do cliente") a uma linha encaminhada para OUTLAYSP sem item adequado. Não existe recurso em OUTLAYS.
_Evitar_: valor por omissão, default

## Confiança e revisão

**Confiança** (`confidence`):
Classificação `HIGH`, `MEDIUM` ou `LOW` de uma codificação, calculada por regra e nunca declarada pelo modelo.

**Sinalização** (`flag`):
Marca que envia uma linha para revisão humana, sempre com um motivo de um conjunto fechado.
_Evitar_: alerta, aviso

**Conjunto dourado** (`golden_set`):
As facturas de amostra, com a entidade, a aba de destino e o código de item esperados para cada linha, contra os quais se mede o sistema.
_Evitar_: conjunto de referência, ground truth

**Revisão** (`review`):
Decisão humana sobre uma linha sinalizada: aceitar ou corrigir o código de item.

**Estado de revisão** (`review_status`):
`pending` (sinalizada e por rever), `accepted` (aceite) ou `corrected` (código de item alterado por um revisor).
