# Requisitos

**Projecto:** Sextante, Pipeline de Codificação Automática de Linhas de Facturas de Fornecedores
**Cliente:** AMT, Advanced Maritime Transports - Transitarios Limitada
**Versão:** 0.2 · 18-11-2026 · revisto depois da sessão de grilling e da análise das amostras. Os requisitos alterados estão marcados.

---

## 0. Como ler este documento

Cada requisito tem identificador estável, enunciado verificável e, quando aplicável, a origem no enunciado do teste ou na decisão que o motivou.

| Prefixo | Área |
|---|---|
| `REQ-ING` | Ingestão e extracção |
| `REQ-ENT` | Verificação de entidade |
| `REQ-MAP` | Encaminhamento e mapeamento de item |
| `REQ-CNF` | Confiança e sinalização |
| `REQ-REV` | Revisão humana |
| `REQ-EXP` | Exportação |
| `REQ-PLT` | Plataforma e API |
| `REQ-AUD` | Auditoria e rastreabilidade |
| `NFR-*` | Requisitos não funcionais |

Regra de rastreabilidade: **todo o requisito tem pelo menos um teste marcado com o seu identificador.** A marcação é verificada por ferramenta, como descrito em `04-padroes-de-codigo.md` §3.4. Um requisito sem teste é um requisito não entregue, não um requisito implícito.

Palavras com força normativa: **deve** é obrigatório, **não deve** é proibido, **pode** é opcional.

---

## 1. Ingestão e extracção

### REQ-ING-001 · Formatos aceites

O sistema **deve** aceitar ficheiros de factura em PDF e em XLSX, e **não deve** aceitar nenhum outro formato.

O formato é determinado pelo **conteúdo real** do ficheiro, por inspecção dos primeiros bytes, e **não** pela extensão nem pelo `Content-Type` declarado no pedido, que são ambos controlados por quem carrega.

Nesta versão só é extraído o PDF nativo no modelo das amostras. Um XLSX, ou um PDF fora do modelo, é recusado nos termos de REQ-ING-009. *Revisto em 18-11-2026.*

*Origem: R9. Segurança: SEC-16.*

### REQ-ING-002 · Recusa de PDF sem camada de texto

O sistema **deve** recusar, com motivo explícito, um PDF cuja extracção devolva menos caracteres por página do que o mínimo configurado.

Um PDF digitalizado **não deve** ser aceite e codificado com o pouco texto que se conseguir extrair. A recusa é visível ao utilizador e registada no trabalho com o estado `rejected` e o motivo `pdf_without_text_layer`, e aparece na exportação nos termos de REQ-EXP-007.

*Origem: L-01. O OCR está fora de âmbito nesta versão.*

### REQ-ING-003 · Extracção de cabeçalho

Para cada factura, o sistema **deve** extrair, quando presentes no documento:

- o fornecedor emitente, com o nome e o NIF;
- o número da factura, a data e a moeda;
- o bloco da entidade facturada, com o nome, as linhas "ao cuidado de", a morada e o NIF;
- as linhas de resumo (subtotal, IVA e total);
- as observações.

Um campo ausente fica vazio e é registado como ausente. O sistema **não deve** inferir um valor para um campo que não encontrou. *Revisto em 18-11-2026.*

### REQ-ING-004 · Extracção de linhas

Para cada factura, o sistema **deve** extrair as linhas de serviço com, no mínimo, a descrição. Quando presentes, extrai também quantidade, preço unitário, percentagem de IVA e valor.

A ordem das linhas na saída **deve** ser a ordem em que aparecem no documento.

### REQ-ING-005 · Localização da entidade facturada

O sistema **deve** localizar o bloco da entidade facturada por rótulo, contra uma lista fechada de rótulos configurável, que inclui no mínimo `Bill To`, `Billed To`, `Cliente`, `Facturar a` e `Exmo`.

A entidade facturada é **a primeira linha** do bloco. Uma linha começada por "c/o" ou "a/c" é registada como "ao cuidado de" e **não deve** ser tratada como entidade facturada.

Se nenhum bloco for localizado, a entidade fica ambígua com o motivo `entity_label_not_found`, nos termos de REQ-ENT-004. O sistema **não deve** usar o primeiro nome de empresa que encontrar no documento como entidade facturada. *Revisto em 18-11-2026.*

*Origem: D-3.6, D-3.15. É o erro mais caro possível: uma entidade errada encaminha toda a factura para a aba errada.*

### REQ-ING-006 · Classificação do tipo de linha

Antes de qualquer codificação, o sistema **deve** classificar cada linha extraída num dos tipos `service`, `tax` ou `discount`. O que não é reconhecido como `tax` ou `discount` é `service`.

O tipo `tax` reconhece **só** o IVA do fornecedor ("IVA", "VAT", "Imposto sobre o Valor Acrescentado"), e **não deve** reconhecer "taxa" ou "imposto" sozinhos.

Só as linhas `service` seguem para codificação. As linhas `tax` e `discount` aparecem na saída com `Assigned_Item_No` vazio, confiança `HIGH`, a nota `line_type_tax` ou `line_type_discount`, o estado de revisão `accepted` e **sem** sinalização.

O subtotal e o total **não** são linhas da factura. **Não devem** aparecer na saída e ficam registados na auditoria da factura.

A classificação é determinística, por padrão sobre a descrição normalizada e por posição na tabela. *Revisto em 18-11-2026.*

*Origem: L-06, D-3.17. Sem isto, "IVA 14%" recebe um código de serviço com confiança artificialmente alta. Sinalizar as linhas de IVA encheria a fila de revisão com casos fáceis.*

### REQ-ING-007 · Idempotência do carregamento

Carregar duas vezes o mesmo ficheiro **deve** devolver o trabalho existente, com o seu estado, e **não deve** criar um segundo trabalho nem uma segunda codificação.

A chave é o digest SHA-256 do conteúdo. A unicidade é imposta por restrição na tabela, dentro da transacção de escrita, e **não** por verificação prévia em código.

*Origem: D-3.10. Verificar e depois escrever é uma condição de corrida que dois carregamentos simultâneos ganham os dois.*

### REQ-ING-008 · Normalização de texto

Todo o texto extraído **deve** ser normalizado para NFC e despojado de caracteres de controlo antes de ser validado, persistido ou comparado.

*Origem: texto em português tem mais do que uma representação Unicode possível para a mesma palavra acentuada. Sem normalização, a comparação de descrições falha de forma invisível.*

### REQ-ING-009 · Recusa de documento não suportado

O sistema **deve** recusar, com o motivo `unsupported_document_type`, um documento que não siga o modelo de factura suportado, incluindo as notas de liquidação aduaneira da AGT.

A recusa fica registada no trabalho com o estado `rejected` e aparece na exportação nos termos de REQ-EXP-007. O documento **não deve** ser codificado. *Revisto em 18-11-2026.*

*Origem: L-14, D-3.6.*

### REQ-ING-010 · Leitura do modelo das amostras

Na extracção de PDF, o sistema **deve**:

- separar os blocos do fornecedor e da entidade facturada pelas coordenadas das palavras, e não pelo texto corrido;
- ler o nome do fornecedor da região da faixa de topo;
- juntar uma linha de continuação de descrição à linha anterior, sem espaço numa quebra a meio da palavra e com espaço numa quebra num espaço;
- interpretar os valores no formato `1,206.00`, com a moeda do cabeçalho da coluna de valor.

*Revisto em 18-11-2026.*

*Origem: D-3.6. As amostras têm colunas lado a lado, sobreposição na faixa de topo e descrições partidas a meio da palavra.*

### REQ-ING-011 · Duplicado provável

Uma factura com o mesmo fornecedor e o mesmo número de outra já carregada, mas com digest diferente, **deve** ser codificada e sinalizada com `possible_duplicate`, com referência à anterior.

O carregamento **não deve** ser bloqueado por suspeita de duplicado. Uma factura sem número nunca é duplicado provável. *Revisto em 18-11-2026.*

*Origem: D-3.10, L-15. Uma nota de crédito pode reutilizar o número da factura.*

---

## 2. Verificação de entidade

### REQ-ENT-001 · Entidade alvo

O sistema **deve** verificar se a entidade facturada é `Advanced Maritime Transports - Transitarios Limitada`.

O nome alvo e o NIF da entidade alvo vivem em configuração, não em literal no código. *Revisto em 18-11-2026.*

*Origem: enunciado, passo 1.*

### REQ-ENT-002 · Tolerância a variações menores

A verificação **deve** considerar correspondentes nomes que difiram do alvo apenas em: maiúsculas e minúsculas, pontuação, espaços repetidos, presença ou ausência de hífen, acentos, e forma do sufixo societário, incluindo `Limitada`, `Lda`, `Lda.` e `Ltda`.

A correspondência é a **igualdade** do nome normalizado com o nome alvo normalizado. A semelhança aproximada serve só para decidir a não correspondência, abaixo do limiar baixo, e **não deve** usar uma métrica que dê o valor máximo quando um nome está contido no outro, como `token_set_ratio`. *Revisto em 18-11-2026.*

*Origem: R5, D-3.15.*

### REQ-ENT-003 · Recusa estrita de terceiros

O sistema **não deve** considerar correspondente nenhuma entidade constante da lista de exclusão, qualquer que seja a sua semelhança com o nome alvo.

A lista de exclusão vive em `config/entity_denylist.yaml`, cobre empresas irmãs, companhias de navegação e clientes conhecidos, e é avaliada **antes** de qualquer correspondência aproximada.

*Origem: R4. Uma empresa irmã de um transitário tem tipicamente nome quase idêntico, e correspondência aproximada sozinha vai casar. Falso negativo custa uma revisão; falso positivo custa uma reclassificação fiscal.*

### REQ-ENT-004 · Entidade ambígua

A entidade **deve** ser marcada como ambígua, com o motivo indicado, quando:

| Condição | Motivo |
|---|---|
| Nenhum bloco de entidade facturada foi localizado, nos termos de REQ-ING-005 | `entity_label_not_found` |
| Mais do que um bloco de entidade facturada foi localizado na mesma factura | `multiple_billed_entities` |
| O nome normalizado é igual ao alvo, mas o NIF extraído é diferente | `entity_nif_mismatch` |
| O nome não é igual ao alvo depois de normalizado, não consta da lista de exclusão, e a semelhança não está abaixo do limiar baixo | `entity_similar_not_equal` |

Uma factura com entidade ambígua **não deve** ser codificada. As suas linhas saem com `Exact_Entity_Match = NO`, `Target_Sheet` vazio, sem código, com confiança `LOW` e sinalizadas. *Revisto em 18-11-2026.*

*Origem: L-04, L-09, L-13, D-3.15. O último caso é o que apanha a empresa irmã que ninguém listou ainda.*

### REQ-ENT-005 · Verificação sem modelo de linguagem

A verificação de entidade **não deve** invocar o modelo de linguagem, em nenhum caso. A entidade ambígua é resolvida por um humano, nos termos de REQ-REV-006. *Revisto em 18-11-2026.* Substitui o desempate pelo modelo da versão 0.1.

*Origem: D-3.15. R4 é recusa estrita. Um desempate pelo modelo seria o modelo a decidir que uma empresa é a AMT.*

### REQ-ENT-006 · Registo da entidade detectada

O sistema **deve** registar o nome da entidade tal como foi extraído do documento, sem normalização, na coluna `Billed_Entity_Detected` da saída, e o resultado da verificação em `Exact_Entity_Match`, com os valores `YES` ou `NO`.

Quando a entidade for ambígua, `Exact_Entity_Match` é `NO` e `Notes_or_Flags` indica o motivo. As linhas "ao cuidado de" aparecem em `Notes_or_Flags` e não em `Billed_Entity_Detected`.

### REQ-ENT-007 · Veto pelo NIF

Quando o NIF da entidade facturada for extraído e for diferente do NIF da entidade alvo, a verificação **não deve** devolver correspondência.

Um NIF igual ao da entidade alvo **não deve** bastar, sozinho, para devolver correspondência. *Revisto em 18-11-2026.*

*Origem: L-04, D-3.15. INV-010 mostra uma empresa irmã com a morada da AMT e um NIF quase igual.*

### REQ-ENT-008 · Ao cuidado de

As linhas "ao cuidado de" do bloco da entidade facturada **não devem** entrar na verificação de entidade. *Revisto em 18-11-2026.*

*Origem: D-3.15. Em INV-002, uma factura do cliente entregue "c/o" a AMT é uma despesa por conta do cliente.*

*Origem: R6.*

---

## 3. Encaminhamento e mapeamento de item

### REQ-MAP-001 · Encaminhamento da aba

Se a verificação de entidade devolver correspondência, cada linha **deve** ser codificada contra a aba `OUTLAYS`. Se devolver não correspondência, contra a aba `OUTLAYSP`. Se a entidade for ambígua, a factura não tem aba de destino e não é codificada, nos termos de REQ-ENT-004. *Revisto em 18-11-2026.*

O encaminhamento é determinístico, derivado directamente do resultado do passo anterior, e **não deve** ser decidido pelo modelo de linguagem.

*Origem: R2, enunciado, passo 2.*

### REQ-MAP-002 · Isolamento das abas na recuperação

A pontuação lexical e a lista enviada ao modelo **devem** ser construídas separadamente por aba, e **não devem** conter itens da outra aba.

*Origem: misturar as abas derrotaria o passo 2 do enunciado.*

### REQ-MAP-003 · Código exacto

O valor atribuído em `Assigned_Item_No` **deve** ser o valor exacto da coluna `No.`, Coluna A, do item escolhido, sem reformatação, sem preenchimento de zeros e sem alteração de maiúsculas.

*Origem: R1.*

### REQ-MAP-004 · Pontuação lexical

Para cada linha a codificar, o sistema **deve** calcular o score de semelhança lexical de **todos** os itens da aba de destino. O score de cada item é o máximo entre a comparação com a descrição PT e com a descrição EN.

Os scores são persistidos e são entrada da classificação de confiança e do ecrã de revisão. **Não** filtram a lista enviada ao modelo. *Revisto em 18-11-2026.*

*Origem: D-3.16. Com 44 e 20 itens, filtrar por semelhança lexical faz o item certo desaparecer quando a linha e o catálogo estão em idiomas diferentes.*

### REQ-MAP-005 · Escolha entre candidatos

A escolha do item **deve** ser feita pelo modelo de linguagem, que recebe a descrição da linha, o contexto das linhas vizinhas da mesma factura, e a lista de itens da **aba de destino inteira**, por ordem fixa do catálogo, com índice, código, descrição PT e descrição EN. *Revisto em 18-11-2026.*

O modelo **deve** devolver o **índice** do candidato escolhido na lista fornecida, ou a indicação de que nenhum serve. O modelo **não deve** devolver um código de item em texto livre.

O índice devolvido **deve** ser validado contra o comprimento da lista, e o código correspondente validado contra o catálogo, antes de ser persistido.

*Origem: R13, SEC-14. É o controlo que impede que conteúdo de uma factura dirija a atribuição de códigos.*

### REQ-MAP-006 · Agrupamento das chamadas

As linhas de serviço de uma factura **devem** ser enviadas ao modelo numa só chamada, com a lista de itens da aba de destino enviada uma vez.

*Origem: D-3.7. Reduz as chamadas mensais de cerca de 50.000 para cerca de 5.000 e dá ao modelo o contexto das linhas vizinhas.*

### REQ-MAP-007 · Determinismo da chamada

A chamada ao modelo **deve** usar saída estruturada com esquema declarado e `max_tokens` dimensionado ao número de linhas. *Revisto em 18-11-2026:* `temperature=0` foi retirado, porque a API deixou de aceitar parâmetros de amostragem; ver 00-decisoes-e-lacunas.md §3.22.

A resposta **deve** ser validada contra o esquema antes de qualquer uso. Uma resposta inválida é tratada como falha da linha, com confiança `LOW` e sinalização, e **não** como motivo para o sistema improvisar um código.

### REQ-MAP-008 · Regra de recurso em OUTLAYSP

Se o encaminhamento foi para `OUTLAYSP` e o modelo declarou que nenhum candidato serve, o sistema **deve** atribuir o código `O00999`.

A verificação de que o encaminhamento foi `OUTLAYSP` é feita em código, e o recurso **não deve** ser aplicado a linhas encaminhadas para `OUTLAYS`.

*Origem: R3, enunciado, passo 2, regra de recurso.*

### REQ-MAP-009 · Ausência de correspondência em OUTLAYS

Se o encaminhamento foi para `OUTLAYS` e nenhum candidato serve, o sistema **deve** deixar `Assigned_Item_No` vazio, atribuir confiança `LOW`, e sinalizar a linha com o motivo `no_match_in_outlays`.

O sistema **não deve**, neste caso, atribuir `O00999`, nem o melhor candidato disponível.

*Origem: L-08. O enunciado não define este caso. A escolha é devolver a lacuna ao humano, nunca preenchê-la por omissão.*

### REQ-MAP-010 · Descrição do item correspondido

O sistema **deve** registar em `Matched_Catalog_Description` a descrição PT (coluna B) do item do catálogo que foi atribuído, tal como consta do catálogo, sem espaços nas pontas. *Revisto em 18-11-2026.*

Quando não houve atribuição, o campo fica vazio.

*Origem: R6. É o campo que permite a um revisor julgar a atribuição sem abrir o catálogo.*

### REQ-MAP-011 · Versão do catálogo

Cada linha codificada **deve** registar o digest SHA-256 do ficheiro de catálogo usado.

*Origem: D-3.9. Sem isto, um resultado de ontem não é reproduzível quando o catálogo mudar.*

### REQ-MAP-012 · Validação do catálogo no arranque

No arranque, o sistema **deve** validar que o ficheiro de catálogo contém as abas `OUTLAYS` e `OUTLAYSP`, que a coluna A existe em ambas, que os seus valores são não vazios e únicos dentro de cada aba, e que `O00999` existe em `OUTLAYSP`.

O sistema **deve** registar um aviso, sem recusar o arranque, quando uma descrição contiver caracteres invisíveis ou uma descrição EN estiver vazia. *Revisto em 18-11-2026.*

Falhando qualquer destas condições, a aplicação **deve** recusar arrancar, com mensagem que nomeia a aba e a condição violada.

*Origem: arrancar com um catálogo inválido produz codificação errada em silêncio.*

### REQ-MAP-013 · Item genérico

Quando o modelo escolher um item da lista de itens genéricos, a linha **deve** receber confiança `LOW` e a sinalização `generic_catalog_item`.

A lista de itens genéricos vive em configuração, e contém inicialmente `O00052`. *Revisto em 18-11-2026.*

*Origem: D-3.16, L-08. Escolher livremente "Outras Despesas" seria um recurso escondido em OUTLAYS.*

---

## 4. Confiança e sinalização

### REQ-CNF-001 · Confiança calculada, não pedida

A classificação de confiança **deve** ser calculada por regra determinística sobre os scores de recuperação e a decisão do modelo, e **não deve** ser pedida ao modelo de linguagem.

*Origem: D-3.8. Modelos de linguagem são maus avaliadores da sua própria certeza, e a classificação que devolvem não é reproduzível entre execuções.*

### REQ-CNF-002 · Classificações

A classificação é um de três valores, `HIGH`, `MEDIUM` ou `LOW`, atribuído segundo a tabela de D-3.8, com os limiares em constantes num só ficheiro. A resolução humana da entidade não limita a classificação. *Revisto em 18-11-2026.*

### REQ-CNF-003 · Sinalização obrigatória

O sistema **deve** sinalizar para revisão humana toda a linha que cumpra qualquer destas condições:

- confiança `LOW`;
- entidade ambígua;
- recurso aplicado para `O00999`;
- item escolhido que é um dos dois primeiros lexicais, estando os dois a menos da distância mínima entre si (`conflicting_candidates`);
- resposta do modelo que falhou validação;
- item genérico escolhido;
- factura sinalizada como duplicado provável.

As linhas `tax` e `discount` **não** são sinalizadas por causa do tipo. *Revisto em 18-11-2026.*

*Origem: enunciado, passo 3.*

### REQ-CNF-004 · Motivos legíveis

Cada sinalização **deve** registar um motivo de um conjunto fechado de códigos, acompanhado de texto em Português para apresentação.

O conjunto de códigos vive num `StrEnum`, nunca em cadeias livres espalhadas pelo código.

### REQ-CNF-005 · Limiares declarados como provisórios

Enquanto não existir conjunto dourado, nos termos de L-02, os limiares de confiança **devem** ser declarados como provisórios no `README.md`, com o valor em uso.

O sistema **não deve** publicar métricas de precisão enquanto não houver conjunto dourado contra o qual medir.

*Origem: L-02. Um número sem medição é uma afirmação.*

---

## 5. Revisão humana

### REQ-REV-001 · Listagem revisável

O sistema **deve** apresentar os resultados codificados em tabela, com filtro por confiança, por aba de destino, por estado de sinalização e por factura.

### REQ-REV-002 · Alteração do código atribuído

Um revisor **deve** poder alterar o `Assigned_Item_No` de uma linha, escolhendo de entre os itens da aba de destino dessa linha.

O sistema **não deve** permitir atribuir um código que não exista na aba de destino, nem alterar o código de uma linha sem aba de destino. A validação é feita no servidor.

*Origem: a aba de destino é o resultado do passo 2, e permitir contorná-la na revisão anularia a regra.*

### REQ-REV-003 · Nota de revisão

Um revisor **deve** poder registar uma nota em texto por linha, com comprimento máximo declarado.

### REQ-REV-004 · Registo da revisão

Toda a alteração feita por um revisor **deve** gerar um registo de auditoria com o valor anterior, o novo valor, o autor e o momento.

A alteração **não deve** sobrescrever o registo de codificação original.

*Origem: D-3.11, REQ-AUD-002.*

### REQ-REV-005 · Estado de revisão

Cada linha **deve** ter um estado de revisão de um conjunto fechado: `pending`, `accepted`, `corrected`.

Uma linha sinalizada nasce `pending`. Uma linha não sinalizada nasce `accepted`.

### REQ-REV-006 · Resolução de entidade

Um revisor **deve** poder resolver a entidade de uma factura ambígua, escolhendo correspondência ou não correspondência, com nota obrigatória de comprimento máximo declarado.

A resolução **deve** gerar um registo de auditoria e pôr a factura na fila de codificação a partir do texto já extraído. **Não deve** alterar a lista de exclusão. O pedido **deve** ser recusado para facturas que não estejam ambíguas. *Revisto em 18-11-2026.*

*Origem: D-3.15. Sem esta acção, uma factura ambígua ficava parada para sempre.*

### REQ-REV-007 · Aceitação de linha

Um revisor **deve** poder aceitar uma linha sinalizada sem lhe alterar o código, passando-a de `pending` a `accepted`, com registo de auditoria. *Revisto em 18-11-2026.*

---

## 6. Exportação

### REQ-EXP-001 · Colunas obrigatórias

A exportação **deve** conter exactamente estas nove colunas, com estes nomes e por esta ordem:

| Ordem | Coluna | Conteúdo |
|---|---|---|
| 1 | `Invoice_ID` | Identificador da factura |
| 2 | `Billed_Entity_Detected` | Entidade facturada tal como extraída |
| 3 | `Exact_Entity_Match` | `YES` ou `NO` |
| 4 | `Target_Sheet` | `OUTLAYS`, `OUTLAYSP`, ou vazio quando a entidade é ambígua (desvio declarado, L-13) |
| 5 | `Line_Description` | Descrição da linha, tal como extraída |
| 6 | `Assigned_Item_No` | Código de item atribuído, ou vazio |
| 7 | `Matched_Catalog_Description` | Descrição do item do catálogo, ou vazio |
| 8 | `Confidence` | `HIGH`, `MEDIUM` ou `LOW` |
| 9 | `Notes_or_Flags` | Motivos de sinalização e notas de revisão |

*Origem: R6, enunciado, secção 3.*

### REQ-EXP-002 · Formatos

A exportação **deve** estar disponível em CSV e em XLSX.

### REQ-EXP-003 · Neutralização de injecção de fórmula

Na exportação para CSV e para XLSX, toda a célula cujo primeiro carácter seja `=`, `+`, `-`, `@`, tabulação ou retorno de carro **deve** ser prefixada com apóstrofo.

*Origem: SEC-17. Uma descrição de factura é conteúdo de origem externa, e o ficheiro vai ser aberto no Excel por alguém da contabilidade.*

### REQ-EXP-004 · Fonte da exportação

A exportação **deve** ser gerada a partir do estado persistido, e **não** do resultado em memória do último trabalho executado.

A exportação reflecte as revisões humanas em vigor.

### REQ-EXP-005 · Codificação e separador do CSV

O CSV **deve** ser escrito em UTF-8 com BOM, com separador configurável e vírgula por omissão.

*Origem: o Excel em configuração regional portuguesa abre UTF-8 sem BOM com acentuação corrompida, o que faria a entrega parecer defeituosa por um motivo que não é o conteúdo.*

### REQ-EXP-006 · Identificador da factura

`Invoice_ID` **deve** ser `<fornecedor>/<número da factura>`. O fornecedor é identificado pelo NIF quando extraído, e pelo nome normalizado quando não. Um digest curto do ficheiro substitui o número quando este falta.

O identificador **não deve** ser um contador sequencial, que não sobrevive a reprocessamentos. *Revisto em 18-11-2026.*

*Origem: D-3.10. Dois fornecedores emitem com facilidade o mesmo número de factura.*

### REQ-EXP-007 · Documentos recusados

Um documento recusado **deve** aparecer na exportação com uma linha, `Confidence = LOW`, e o motivo da recusa em `Notes_or_Flags`. *Revisto em 18-11-2026.*

*Origem: D-3.6. Omitir o documento esconderia ao revisor que ele existiu.*

---

## 7. Plataforma e API

### REQ-PLT-001 · Carregamento assíncrono

O carregamento de ficheiros **deve** devolver um identificador de trabalho de imediato, sem esperar pela codificação.

O estado do trabalho **deve** ser consultável, com indicação de facturas processadas, em curso, falhadas e totais.

*Origem: D-3.4. Um lote de 300 facturas estoura o tempo de espera de qualquer cliente ou proxy.*

### REQ-PLT-002 · Isolamento de falha por factura

Uma falha no processamento de uma factura **não deve** interromper o trabalho.

A factura fica em estado `failed`, com o motivo registado, e o trabalho prossegue para as restantes.

### REQ-PLT-003 · Repetição de falhas transitórias

Falhas transitórias na chamada ao modelo **devem** ser repetidas com recuo exponencial, até um número máximo configurável de tentativas, com valor inicial de três.

Falhas não transitórias, incluindo resposta que falha validação de esquema, **não devem** ser repetidas.

### REQ-PLT-004 · Paginação

Toda a listagem **deve** ser paginada, com limite máximo imposto pelo servidor. Um pedido com limite acima do máximo é truncado, e o truncamento é indicado na resposta.

*Segurança: SEC-18.*

### REQ-PLT-005 · Erros opacos ao cliente

Uma falha interna **deve** devolver mensagem genérica em Português e um identificador de correlação, sem detalhe técnico.

O detalhe fica no log do servidor, associado ao mesmo identificador.

*Segurança: SEC-15.*

### REQ-PLT-006 · Texto de interface em Português

Todo o texto apresentado ao utilizador **deve** estar em Português e viver em catálogo de tradução, não em literais espalhados pelo código.

*Origem: R12.*

### REQ-PLT-007 · Arranque que falha cedo

A aplicação **deve** recusar arrancar quando faltar qualquer configuração obrigatória, incluindo a chave de API do modelo, o caminho do catálogo, e o nome e o NIF da entidade alvo.

*Segurança: SEC-02. Falhar cedo e em voz alta é preferível a arrancar com configuração incompleta e descobrir às dez da manhã de um fecho de mês.*

### REQ-PLT-008 · Um comando para arrancar

O sistema **deve** arrancar com um único comando documentado no `README.md`, a partir de um repositório recém-clonado e de um ficheiro de configuração de exemplo.

*Origem: R8, enunciado, secção 3, instruções de instalação e execução.*

---

## 8. Auditoria e rastreabilidade

### REQ-AUD-001 · Registo da decisão

Para cada linha codificada, o sistema **deve** registar: a descrição original, o texto normalizado, a aba de destino, os scores lexicais de todos os itens da aba de destino, a escolha do modelo, o identificador do modelo, a versão do prompt, o digest do catálogo, a classificação de confiança, a regra que a produziu, e o momento da codificação.

*Origem: D-3.11. Em contexto fiscal, "o sistema atribuiu este código" não é resposta a um auditor.*

### REQ-AUD-002 · Auditoria apenas inserida

Os registos de auditoria **devem** ser apenas inseridos. A aplicação **não deve** actualizá-los nem eliminá-los.

Uma correcção é um novo registo.

### REQ-AUD-003 · Versão do prompt

Todo o prompt de sistema **deve** ter um identificador de versão, registado em cada decisão que o usou.

*Origem: alterar um prompt muda o comportamento do sistema. Sem versão, duas execuções com resultados diferentes são inexplicáveis.*

### REQ-AUD-004 · Custo por trabalho

O sistema **deve** registar os tokens de entrada e de saída consumidos por factura, e o acumulado por trabalho.

*Origem: L-12.*

### REQ-AUD-005 · Conteúdo fora dos logs

Os registos de log **não devem** conter conteúdo de factura, nomes de fornecedor, valores monetários, nem o corpo dos prompts.

Identificadores, digests, scores e classificações podem ser registados.

*Segurança: SEC-15.*

---

## 9. Requisitos não funcionais

### NFR-PRF-001 · Desempenho por factura

Uma factura com dez linhas, em PDF nativo, **deve** ser codificada em menos de 15 segundos, medidos do início do processamento ao estado final, numa máquina de desenvolvimento corrente.

### NFR-PRF-002 · Lote de pico

Um lote de 300 facturas **deve** completar sem intervenção manual e sem falha do processo, com concorrência configurável de chamadas ao modelo.

*Origem: D-3.3. O pico do fecho do mês é o que dimensiona, não o volume mensal.*

### NFR-PRF-003 · Catálogo em memória

O catálogo **deve** ser carregado uma vez no arranque e mantido em memória, não lido por cada linha.

### NFR-REL-001 · Tolerância a falha do modelo

A indisponibilidade da API do modelo **não deve** corromper estado. As facturas afectadas ficam em `failed` e podem ser reprocessadas sem novo carregamento.

### NFR-REL-002 · Reprocessamento a partir do texto extraído

O sistema **deve** permitir reprocessar uma factura a partir do texto já extraído, sem repetir a extracção nem exigir novo carregamento.

*Origem: separar extracção de codificação é o que permite recalibrar limiares ou corrigir um prompt sem voltar a pedir os ficheiros.*

### NFR-OBS-001 · Logs estruturados

Os logs **devem** ser JSON estruturado, escritos em `stdout`, com nome de evento em `snake_case` em Inglês e identificador de correlação em todos os registos.

### NFR-OBS-002 · Métricas mínimas

O sistema **deve** expor, no mínimo: contagem de facturas por estado, taxa de linhas por classificação de confiança, taxa de falha de extracção, latência das chamadas ao modelo, e custo acumulado.

*Origem: a primeira métrica a vigiar é a subida da taxa de revisão, que é o sinal de que o catálogo ou os fornecedores mudaram.*

### NFR-TST-001 · Conjunto dourado

O sistema **deve** ter um conjunto dourado formado pelas amostras, lidas de um caminho local configurado por variável de ambiente, com os resultados esperados num ficheiro de configuração editável, e um comando que mede o sistema contra ele.

As amostras **não devem** entrar no repositório. Os testes usam réplicas sintéticas, identificadas como sintéticas e nunca apresentadas como amostras reais.

O comando por omissão mede só as etapas determinísticas, sem chamar o modelo. A medição dos códigos de item com o modelo real é um comando manual, fora da suite de testes. *Revisto em 18-11-2026.*

*Origem: L-02, D-3.18.*

### NFR-TST-002 · Cobertura de casos limite

O conjunto de teste **deve** cobrir, no mínimo: entidade exacta, entidade com sufixo societário alternativo, entidade sem hífen, empresa irmã de nome semelhante, companhia de navegação, cliente terceiro, cabeçalho sem rótulo de entidade, linha vaga, linha com dois candidatos próximos, linha sem correspondência em `OUTLAYS`, linha sem correspondência em `OUTLAYSP`, linha de imposto, entidade com "c/o" da AMT, empresa irmã com NIF diferente, nome igual ao alvo com NIF diferente, item genérico, PDF digitalizado, e documento não suportado.

*Origem: estes são os casos que o enunciado nomeia no passo 3 e os que as regras R3, R4 e R5 criam.*

### NFR-TST-003 · Determinismo dos testes

Nenhum teste **deve** chamar a API do modelo. A porta `ItemClassifier` tem um duplo nomeado, com respostas declaradas, nos termos de `04-padroes-de-codigo.md` §3.3.

O relógio e os identificadores são injectados.

### NFR-SEC-001 · Gate de segurança

Toda a alteração que toque em input externo, identidade, dados persistidos ou rede **deve** percorrer o gate de `03-seguranca.md` §1 e terminar com o bloco de fecho de §21.

### NFR-LIC-001 · Licenças permissivas

Todas as dependências de código **devem** estar sob licença permissiva. Lista branca:

`MIT`, `BSD-2-Clause`, `BSD-3-Clause`, `Apache-2.0`, `ISC`, `PSF-2.0`, `MPL-2.0`, `Unlicense`, `CC0-1.0`.

Licenças fora da lista exigem decisão registada neste documento antes de a dependência entrar. Em particular, `GPL`, `AGPL` e `SSPL` ficam fora sem decisão prévia.

O acesso à API da Anthropic é um serviço pago, declarado como tal, e não é uma dependência de código sujeita a esta regra.

A verificação é automática no pipeline, nos termos de `03-seguranca.md` SEC-20.

### NFR-DOC-001 · README como entregável

O `README.md` **deve** conter: instruções de instalação e execução, decisões de arquitectura com a explicação de onde foi usada IA e onde foi usada lógica determinística e porquê, e a secção de prontidão para produção.

*Origem: R8, enunciado, secção 3.*

### NFR-DOC-002 · Prompts entregues sem segredos

Os prompts de sistema **devem** ser versionados no repositório, em ficheiros próprios, sem nenhuma chave de API.

*Origem: R7, SEC-02.*

---

## 10. Matriz de origem

Ligação entre as regras do enunciado e os requisitos que as implementam. Alimenta a secção de rastreabilidade do `README.md`.

| Regra do enunciado | Requisitos |
|---|---|
| Passo 1, inspeccionar "Bill To" / "Cliente" | REQ-ING-005, REQ-ENT-001 |
| Passo 1, nome exacto da entidade alvo | REQ-ENT-001 |
| Passo 1, tolerância a variações menores | REQ-ENT-002 |
| Passo 1, recusa estrita de terceiros e irmãs | REQ-ENT-003, REQ-ENT-004, REQ-ENT-005, REQ-ENT-007, REQ-ENT-008 |
| Passo 2, encaminhamento OUTLAYS | REQ-MAP-001, REQ-MAP-002 |
| Passo 2, encaminhamento OUTLAYSP | REQ-MAP-001, REQ-MAP-002 |
| Passo 2, código exacto da coluna A | REQ-MAP-003, REQ-MAP-012 |
| Passo 2, recurso `O00999` só em OUTLAYSP | REQ-MAP-008, REQ-MAP-009, REQ-MAP-013 |
| Passo 3, classificação de confiança | REQ-CNF-001, REQ-CNF-002 |
| Passo 3, sinalização de entidade ambígua | REQ-ENT-004, REQ-CNF-003 |
| Passo 3, sinalização de linha vaga | REQ-CNF-003 |
| Passo 3, sinalização de itens em conflito | REQ-CNF-003 |
| Entregável, colunas da saída | REQ-EXP-001 |
| Entregável, código e prompts sem chaves | NFR-DOC-002 |
| Entregável, README com decisões de arquitectura | NFR-DOC-001 |
| Entregável, prontidão para produção | NFR-DOC-001, `00-decisoes-e-lacunas.md` §6 |
