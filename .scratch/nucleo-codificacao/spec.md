# Spec: núcleo de codificação de facturas

Status: ready-for-agent

## Problem Statement

A contabilidade da AMT codifica à mão, no Business Central, cada linha de serviço das facturas de fornecedores. Para cada linha escolhe um código de item de uma de duas abas do catálogo. A aba depende de a factura ser dirigida à própria AMT (OUTLAYS) ou a outra entidade em nome de quem a AMT suporta a despesa (OUTLAYSP).

Este trabalho manual tem quatro problemas:

- **Erros com consequência fiscal.** As descrições variam de fornecedor para fornecedor e chegam em português e em inglês, por isso o código errado é um erro frequente. Cada erro obriga a uma reclassificação no fecho do mês.
- **Empresas irmãs.** Têm nomes quase iguais ao da AMT. Confundi-las encaminha a factura inteira para a aba errada.
- **Nenhuma indicação de risco.** A pessoa que codifica não sabe que linhas são duvidosas, e nada distingue uma escolha segura de um palpite.
- **Trabalho sem rasto.** Não fica registado porque se escolheu um código, o que deixa sem resposta a pergunta de um auditor.

## Solution

O sistema recebe facturas em PDF nativo no modelo das amostras, extrai-as, recusa com motivo o que não consegue ler com segurança, e faz quatro coisas:

1. **Verifica a entidade facturada** de forma totalmente determinística. O resultado é um de três: correspondência, não correspondência, ou entidade ambígua.
2. **Encaminha a factura para a aba de destino** e pede ao modelo de linguagem que escolha, para cada linha de serviço, um item **da aba inteira**. O modelo devolve sempre um índice da lista que o servidor construiu, nunca um código.
3. **Calcula a confiança** de cada linha por regra fixa e sinaliza para revisão humana o que não é seguro, sempre com um motivo legível.
4. **Regista cada decisão com o que a produziu.** O revisor aceita ou corrige códigos, resolve entidades ambíguas, e exporta o resultado em CSV ou XLSX com as nove colunas do enunciado.

Quando há escolha entre atribuir algo plausível e devolver a decisão ao humano, o sistema devolve.

## User Stories

### Carregamento e trabalhos

1. Como contabilista, quero carregar várias facturas de uma vez e receber logo um identificador de trabalho, para não ficar à espera da codificação.
2. Como contabilista, quero ver o estado de um trabalho (facturas processadas, em curso, falhadas e totais), para saber quando posso rever.
3. Como contabilista, quero que carregar duas vezes o mesmo ficheiro me devolva o trabalho existente, para não criar codificações em duplicado quando não sei se o primeiro carregamento passou.
4. Como contabilista, quero que uma factura que falhe não interrompa as restantes do lote, para que um ficheiro problemático não me bloqueie o fecho.
5. Como contabilista, quero que uma factura que falhou por indisponibilidade do modelo possa ser reprocessada sem novo carregamento, para não ter de voltar a procurar o ficheiro.
6. Como contabilista, quero que uma factura com o mesmo fornecedor e o mesmo número de outra já carregada, mas com conteúdo diferente, seja sinalizada como duplicado provável com referência à anterior, para não pagar a mesma despesa duas vezes.

### Verificação de entidade

7. Como contabilista, quero que uma factura dirigida à AMT seja reconhecida apesar de diferenças de maiúsculas, pontuação, hífen, espaços, acentos ou forma do sufixo (`Limitada`, `Lda`, `Lda.`, `Ltda`), para não ter de rever facturas correctas.
8. Como contabilista, quero que uma entidade da lista de exclusão seja sempre tratada como não correspondência, por muito parecido que seja o nome, para que uma empresa irmã nunca vá para OUTLAYS.
9. Como contabilista, quero que um nome parecido com o da AMT mas não igual seja tratado como entidade ambígua, para que uma empresa irmã que ninguém listou ainda não seja aceite por engano.
10. Como contabilista, quero que uma factura sem rótulo de entidade facturada seja tratada como entidade ambígua, para que o sistema não adivinhe a quem a factura se dirige.
11. Como contabilista, quero que uma factura com mais do que uma entidade facturada seja tratada como entidade ambígua, para que o sistema não escolha a primeira que encontrar.
12. Como contabilista, quero que uma factura com entidade ambígua não seja codificada, para que nenhuma linha receba `O00999` por omissão.
13. Como contabilista, quero ver em cada linha da saída o nome da entidade facturada tal como aparece no documento, para julgar a verificação sem abrir a factura.
14. Como contabilista, quero que uma factura dirigida a uma entidade claramente diferente da AMT seja encaminhada para OUTLAYSP, para que as despesas por conta de terceiros fiquem na aba certa.

### Tipos de linha

15. Como contabilista, quero que as linhas de IVA e de desconto apareçam na saída sem código, com a indicação do tipo e sem ir para revisão, para que a fila de revisão não fique cheia de casos fáceis.
16. Como contabilista, quero que subtotais e totais não apareçam como linhas da saída, porque não são linhas da factura.
17. Como auditor, quero que as linhas de resumo fiquem no registo de auditoria, para poder confirmar que a extracção leu a factura inteira.
18. Como contabilista, quero que as linhas apareçam na saída pela ordem do documento, para as conferir lado a lado com a factura.

### Codificação

19. Como contabilista, quero que cada linha de serviço receba um código de item exactamente igual ao da coluna `No.` do catálogo, para o poder colar no Business Central sem reformatar.
20. Como contabilista, quero que o código venha sempre da aba de destino da factura, para que a regra de encaminhamento nunca seja contornada.
21. Como contabilista, quero que o modelo veja a aba de destino inteira, com descrições em português e em inglês, para que uma linha em inglês encontre o item certo mesmo quando o catálogo o descreve em português.
22. Como contabilista, quero que o modelo veja as linhas vizinhas da mesma factura, para que abreviaturas como "THC" sejam interpretadas no contexto.
23. Como contabilista, quero que uma linha de OUTLAYSP sem item adequado receba `O00999`, como manda o enunciado.
24. Como contabilista, quero que uma linha de OUTLAYS sem item adequado fique sem código e sinalizada com `no_match_in_outlays`, para não receber um código errado com aparência de certo.
25. Como contabilista, quero que a escolha de um item genérico como `O00052 Outras Despesas` fique sempre com confiança `LOW` e sinalizada, para que não funcione como recurso escondido em OUTLAYS.
26. Como contabilista, quero ver na saída a descrição em português do item atribuído, para julgar a atribuição sem abrir o catálogo.
27. Como responsável pela segurança, quero que o modelo só possa devolver um índice da lista construída pelo servidor, validado contra a lista e contra a aba de destino, para que texto escrito numa factura não consiga dirigir a atribuição de códigos.
28. Como contabilista, quero que uma resposta inválida do modelo deixe a linha sem código, com `LOW` e sinalizada, em vez de receber um código improvisado.

### Confiança e sinalização

29. Como contabilista, quero que a confiança de cada linha seja `HIGH`, `MEDIUM` ou `LOW` por uma regra fixa e reproduzível, para que a mesma linha tenha sempre a mesma classificação.
30. Como contabilista, quero que uma linha só seja `HIGH` quando o modelo e a semelhança lexical concordam com margem, para que o `HIGH` signifique realmente "não precisa de revisão".
31. Como contabilista, quero que toda a linha `LOW` seja sinalizada, para não ter de procurar os casos duvidosos.
32. Como contabilista, quero que uma linha em que o item escolhido e outro estejam lexicalmente muito próximos seja sinalizada como itens em conflito, para rever as escolhas genuinamente difíceis.
33. Como contabilista, quero que cada sinalização traga um motivo de um conjunto fechado, com texto em português, para perceber de imediato porque a linha está na fila.
34. Como avaliador, quero que os limiares de confiança estejam declarados como provisórios e que não se publique nenhuma métrica de precisão sem conjunto de referência, para não ler afirmações como se fossem medições.

### Revisão

35. Como revisor, quero filtrar as linhas por confiança, por aba de destino, por sinalização e por factura, para trabalhar a fila por prioridade.
36. Como revisor, quero ver, para uma linha, todos os itens da aba de destino ordenados pela semelhança lexical, com o respectivo score e a escolha do modelo, para decidir em segundos.
37. Como revisor, quero corrigir o código de uma linha escolhendo um item da aba de destino dessa linha, e só dessa aba, para que a revisão não contorne o encaminhamento.
38. Como revisor, quero aceitar uma linha sinalizada sem a alterar, para a tirar da fila.
39. Como revisor, quero deixar uma nota em cada linha, com um comprimento máximo, para explicar a minha decisão a quem vier depois.
40. Como revisor, quero resolver a entidade de uma factura ambígua como correspondência ou não correspondência, com nota obrigatória, para que a factura passe a ser codificada.
41. Como revisor, quero que a factura cuja entidade resolvi seja codificada a partir do texto já extraído, sem novo carregamento.
42. Como revisor, quero que as linhas de uma factura cuja entidade resolvi possam chegar a `HIGH`, porque a entidade foi decidida por uma pessoa.
43. Como responsável pela configuração, quero que resolver uma entidade **não** altere a lista de exclusão, para que essa lista só mude por decisão explícita.
44. Como revisor, quero que cada linha tenha um estado de revisão (`pending`, `accepted` ou `corrected`), e que as linhas sinalizadas comecem em `pending` e as restantes em `accepted`.

### Exportação

45. Como contabilista, quero exportar os resultados em CSV e em XLSX, com as nove colunas do enunciado, por essa ordem e com esses nomes.
46. Como contabilista, quero que a exportação mostre os valores revistos em vigor, e não os do último processamento.
47. Como contabilista, quero que o CSV abra correctamente no Excel em configuração portuguesa, em UTF-8 com BOM, para que os acentos não apareçam corrompidos.
48. Como responsável pela segurança, quero que qualquer célula exportada que comece por `=`, `+`, `-`, `@`, tabulação ou retorno de carro seja neutralizada com apóstrofo, para que uma descrição de factura não execute uma fórmula na máquina de quem abre o ficheiro.
49. Como contabilista, quero que o identificador da factura combine fornecedor e número da factura, para que facturas de fornecedores diferentes com o mesmo número não se misturem.
50. Como contabilista, quero que uma factura sem número tenha como identificador um digest curto do ficheiro, e nunca um contador, para que o identificador seja estável entre reprocessamentos.
51. Como contabilista, quero que as linhas de uma factura com entidade ambígua apareçam na exportação, com aba de destino vazia e sinalização, para não perder facturas por rever.

### Auditoria e operação

52. Como auditor, quero, para cada linha codificada:
    - a descrição original e a normalizada;
    - a aba de destino;
    - os scores lexicais;
    - a escolha do modelo;
    - o modelo e a versão do prompt;
    - o digest do catálogo;
    - a confiança e a regra que a produziu;
    - o momento da codificação.

    Assim posso explicar qualquer código atribuído.
53. Como auditor, quero que cada correcção, aceitação e resolução de entidade gere um registo novo, com o valor anterior, o novo, o autor e o momento, sem alterar registos antigos.
54. Como responsável pelo orçamento, quero os tokens de entrada e de saída registados por factura e acumulados por trabalho, para medir o custo real.
55. Como responsável pela segurança, quero que os logs não contenham descrições, nomes de fornecedor, valores nem o corpo dos prompts, só identificadores, scores e classificações.
56. Como operador, quero que a aplicação recuse arrancar com o catálogo inválido, sem chave da API ou sem caminho do catálogo, com uma mensagem que diga o que falta.
57. Como operador, quero ver no arranque avisos sobre caracteres invisíveis e descrições em inglês vazias no catálogo, sem que isso impeça o arranque.
58. Como operador, quero que as falhas transitórias do modelo sejam repetidas com recuo exponencial até um máximo configurável, e que as respostas inválidas não sejam repetidas.

## Implementation Decisions

### Módulos

O projecto é um monólito modular com os módulos `ingestion`, `catalog`, `matching`, `review` e `export`, mais a camada transversal `platform`. O desenho de camadas e as fronteiras verificadas por import-linter são os do documento de arquitectura.

Nesta spec, `ingestion` recebe a factura extraída **através da porta `InvoiceExtractor`, que aqui não se implementa**. A extracção real é outra spec.

### Extracção de PDF nativo

*Emenda de 18-11-2026, a partir das amostras.*

A extracção cobre apenas o modelo das amostras: PDF nativo com faixa de topo, blocos "FROM / FORNECEDOR" e "BILL TO / CLIENTE" lado a lado, tabela de linhas e resumo por baixo. O XLSX continua fora do âmbito, porque não há nenhuma amostra.

A porta `InvoiceExtractor` devolve um de dois resultados: uma **factura extraída** ou uma **recusa com motivo**.

**Factura extraída:**

- **Fornecedor:** o nome, tirado da faixa de topo, e o NIF, tirado do bloco FROM.
- **Factura:** o número, a data e a moeda.
- **Bloco da entidade facturada:**
  - nome, que é **a primeira linha do bloco**;
  - linhas "ao cuidado de" ("c/o" ou "a/c");
  - morada;
  - NIF.
- **Linhas:** descrição, quantidade, preço unitário, percentagem de IVA e valor.
- **Linhas de resumo:** subtotal, IVA e total.
- **Observações.**

Pontos de leitura que as amostras tornam obrigatórios:

- **Colunas pelas coordenadas.** Os blocos FROM e BILL TO são separados pelas coordenadas das palavras, e não pelo texto corrido, que mistura as duas colunas na mesma linha.
- **Faixa de topo por região.** O nome do fornecedor é recortado por região, porque nalgumas facturas sobrepõe-se ao texto "INVOICE / FACTURA" e o texto corrido sai entrelaçado.
- **Descrições partidas.** Uma linha de continuação, sem números, junta-se à linha anterior. Uma quebra a meio da palavra junta-se sem espaço ("Tic" + "ket" dá "Ticket"). Uma quebra num espaço conserva um espaço ("@" + " 100.50").
- **Números.** Os valores lêem-se no formato `1,206.00`, com a moeda indicada no cabeçalho da coluna de valor.

**Recusas, visíveis no estado do trabalho e na exportação:**

| Motivo | Quando |
|---|---|
| `pdf_without_text_layer` | O PDF tem menos texto por página do que o mínimo configurado (é digitalizado) |
| `unsupported_document_type` | O documento não segue o modelo de factura, por exemplo uma nota de liquidação aduaneira |

As amostras **não** entram no repositório. Os testes usam réplicas sintéticas geradas por script e identificadas como sintéticas. Essas réplicas reproduzem as particularidades acima: colunas lado a lado, sobreposição na faixa de topo e quebras a meio da palavra.

### Verificação de entidade

É uma função de domínio pura. Recebe:

- o nome da entidade facturada (a primeira linha do bloco) e o NIF dela, ou a indicação de que não há bloco, ou de que há mais do que um;
- o nome e o NIF da entidade alvo, vindos da configuração;
- a lista de exclusão.

As linhas "ao cuidado de" **nunca** entram na verificação. Ficam registadas e aparecem na nota da linha.

Devolve `MATCH`, `NO_MATCH` ou `AMBIGUOUS`, e neste último caso um motivo.

Ordem de avaliação:

1. **Nenhum bloco de entidade facturada:** `AMBIGUOUS` com `entity_label_not_found`.
2. **Mais do que um bloco de entidade facturada:** `AMBIGUOUS` com `multiple_billed_entities`.
3. **Nome na lista de exclusão**, por igualdade sobre o nome normalizado: `NO_MATCH`.
4. **NIF extraído e diferente do NIF da entidade alvo:**
   - nome normalizado igual ao alvo: `AMBIGUOUS` com `entity_nif_mismatch`;
   - nome diferente: seguem-se as regras 6 e 7, mas **nunca** dá `MATCH`.
5. **Nome normalizado igual ao nome alvo normalizado** (NIF igual ou ausente): `MATCH`.
6. **Semelhança abaixo do limiar baixo:** `NO_MATCH`.
7. **Em todos os outros casos:** `AMBIGUOUS` com `entity_similar_not_equal`.

Um NIF igual ao da entidade alvo nunca basta, sozinho, para dar `MATCH`.

A normalização trata maiúsculas, pontuação, hífen, espaços repetidos, acentos e as formas do sufixo `limitada`, `lda` e `ltda`. A semelhança usa uma métrica que não dá 100 quando um nome está contido no outro (`token_sort_ratio` ou `ratio`, nunca `token_set_ratio`).

O modelo de linguagem não participa: a porta `EntityTiebreaker` e o prompt de desempate deixam de existir. A lista de exclusão é um ficheiro de configuração com estrutura definida e, por agora, vazio (L-04). Nada do seu conteúdo é inventado.

### Encaminhamento

| Resultado da verificação | Aba de destino |
|---|---|
| `MATCH` | OUTLAYS |
| `NO_MATCH` | OUTLAYSP |
| `AMBIGUOUS` | Nenhuma. A factura não é codificada |

Para uma factura ambígua, a aba de destino fica vazia na exportação. É um desvio declarado ao formato de saída, em aberto com o avaliador.

### Tipos de linha

A classificação é determinística, por padrão sobre a descrição normalizada e por posição na tabela. Os tipos são `service`, `tax` e `discount`, e o que não casa com nenhum padrão é `service`.

O padrão de `tax` reconhece **só o IVA do fornecedor**: "IVA", "VAT" e "Imposto sobre o Valor Acrescentado". Nunca reconhece "taxa" ou "imposto" sozinhos. Uma linha como "Taxa de pilotagem" é um serviço, e um direito aduaneiro também.

A percentagem de IVA de cada linha é guardada como atributo da linha. Nas amostras, o IVA aparece sempre como coluna e como linha de resumo, e nunca como linha da tabela.

As linhas de resumo (subtotal e total) **não** são linhas de factura: não são persistidas como linhas e ficam só no registo de auditoria da factura.

As linhas `tax` e `discount` ficam:

- sem código;
- com confiança `HIGH`;
- com a nota `line_type_tax` ou `line_type_discount`;
- com estado de revisão `accepted`;
- sem sinalização.

### Catálogo

O catálogo é lido uma vez no arranque, com `openpyxl` em modo `read_only` e `data_only`. As duas abas, OUTLAYS e OUTLAYSP, têm estas colunas: `No.` (A), `Description` (B, PT), `Description 2` (C, EN) e outras sem uso nesta spec.

**Validações no arranque que impedem o arranque:**

- as duas abas existem;
- a coluna A existe em ambas;
- os códigos não estão vazios e são únicos dentro de cada aba;
- `O00999` existe em OUTLAYSP;
- nenhuma aba excede o limite de itens enviados ao modelo (100, em `docs/03-seguranca.md` §9.1).

**Avisos no arranque que não impedem o arranque:**

- caracteres invisíveis;
- descrição em inglês vazia.

Cada item é guardado com dois conjuntos de valores:

- **Valores de apresentação:** o código exacto e a descrição PT sem espaços nas pontas.
- **Valores de comparação:** as descrições PT e EN normalizadas, em NFKC, sem caracteres invisíveis e com os espaços colapsados.

O catálogo é identificado pelo digest SHA-256 do ficheiro, registado em cada linha codificada. Os itens genéricos (inicialmente `O00052`) são uma lista de configuração, e não estão escritos no código.

### Pontuação lexical

A porta `CandidateRetriever` passa a chamar-se `LexicalScorer`. Para uma descrição de linha e uma aba, devolve o score de **todos** os itens da aba. O score de cada item é o máximo entre a comparação com a descrição PT e a comparação com a descrição EN.

Os scores já não filtram a lista enviada ao modelo; servem só de sinal para a confiança e para o ecrã de revisão. São persistidos por linha, para todos os itens da aba.

### Porta `ItemClassifier`

É chamada uma vez por factura, com todas as linhas de serviço.

**Entrada:**

- o contexto da factura;
- para cada linha de serviço, a sua posição e descrição;
- a **lista de itens da aba de destino**, por ordem fixa do catálogo. Cada item leva o índice, o código, a descrição PT e a descrição EN.

**Saída, por linha:** um índice da lista, ou `none`.

**Validação da resposta**, por esquema e antes de qualquer uso:

- o índice está dentro dos limites da lista;
- o código correspondente pertence à aba de destino;
- cada linha pedida tem exactamente uma resposta.

Uma linha com resposta inválida fica sem código, com `LOW` e o motivo `model_response_invalid`.

**Configuração da chamada:**

- `temperature` 0;
- saída estruturada por ferramenta com esquema declarado;
- `max_tokens` proporcional ao número de linhas.

O prompt é versionado e a versão fica registada em cada decisão. **O texto do prompt tem de ser confirmado pelo responsável antes de entrar**, porque é código que muda o comportamento do sistema.

### Recurso e ausência de correspondência

| Aba de destino | Resultado do modelo | Efeito na linha |
|---|---|---|
| OUTLAYSP | `none` | `O00999`, confiança `LOW`, sinalização `fallback_applied` |
| OUTLAYS | `none` | Sem código, confiança `LOW`, sinalização `no_match_in_outlays` |
| Qualquer | Um item genérico | Confiança `LOW`, sinalização `generic_catalog_item` |

A verificação da aba é feita em código.

### Confiança

É uma função de domínio pura. Os limiares ficam como constantes num único lugar e são provisórios.

| Confiança | Condição |
|---|---|
| `HIGH` | O modelo escolheu um item, esse item é o topo lexical, o score dele está acima do limiar alto, e a distância ao segundo está acima do mínimo |
| `MEDIUM` | O modelo escolheu um item válido e não se cumpre o resto da condição `HIGH` |
| `LOW` | Houve recurso, o modelo devolveu `none`, a resposta foi inválida, ou o item escolhido é genérico |

A sinalização `conflicting_candidates` dispara quando o item escolhido é um dos dois primeiros lexicais **e** os dois estão a menos da distância mínima.

A resolução de entidade por um humano **não** limita a confiança.

### Sinalização

Os motivos formam um conjunto fechado, com texto em português num catálogo de tradução:

| Âmbito | Motivos |
|---|---|
| Entidade | `entity_label_not_found`, `multiple_billed_entities`, `entity_similar_not_equal`, `entity_nif_mismatch` |
| Recusa | `pdf_without_text_layer`, `unsupported_document_type` |
| Codificação | `no_match_in_outlays`, `fallback_applied`, `generic_catalog_item`, `conflicting_candidates`, `model_response_invalid` |
| Factura | `possible_duplicate` |

Uma linha sinalizada começa no estado de revisão `pending`, e uma linha não sinalizada começa em `accepted`.

### Identidade da factura

- **Unicidade do carregamento:** o digest SHA-256 do conteúdo, com uma restrição única na tabela.
- **Identificação do fornecedor:** o NIF quando é extraído, o nome normalizado quando não é.
- **Identificador exportado:** `<fornecedor>/<número da factura>`, ou `<fornecedor>/<digest curto>` quando falta o número.
- **Duplicado provável:** o mesmo fornecedor e o mesmo número com digest diferente. A factura é codificada na mesma e sinalizada com `possible_duplicate`, com referência à anterior.

### Alterações ao esquema, relativamente ao documento de arquitectura

| Tabela | Alteração |
|---|---|
| `invoice_header` | Passa a guardar o resultado da verificação, o motivo de ambiguidade, a aba de destino (que pode ficar vazia), o identificador do fornecedor e o identificador exportado |
| `retrieval_candidate` | Passa a chamar-se `lexical_score`: um registo por linha e por item da aba, com o score e a posição lexical |
| `audit_event` | Ganha os tipos `entity_resolved`, `line_accepted`, `line_corrected` e `summary_rows_extracted` |

Existe um índice não único sobre (fornecedor, número da factura), para a detecção de duplicados prováveis.

### API

Os endpoints são os do documento de arquitectura, com estas alterações:

- **Novo `POST /api/invoices/{invoice_id}/entity-resolution`.**
  - Corpo: a decisão (`MATCH` ou `NO_MATCH`) e uma nota obrigatória com comprimento máximo.
  - Só é aceite para facturas `AMBIGUOUS`.
  - Gera um evento de auditoria e põe a factura na fila de codificação a partir do texto extraído.
  - Exige `Idempotency-Key`.
- **O endpoint de candidatos** passa a devolver todos os itens da aba de destino, ordenados por score lexical, com a escolha do modelo marcada.
- **A correcção de linha** aceita só códigos da aba de destino da linha, com validação no servidor. É rejeitada para linhas sem aba de destino.
- **Uma acção de aceitação de linha**, que passa o estado de `pending` para `accepted`.

### Trabalhador

É o trabalho em segundo plano, no mesmo processo, sobre a tabela de trabalhos, como no documento de decisões:

- a reivindicação de cada trabalho é atómica;
- uma falha numa factura deixa essa factura em `failed` sem parar o trabalho;
- as falhas transitórias são repetidas com recuo exponencial, até três tentativas por omissão;
- as respostas inválidas não são repetidas.

## Testing Decisions

### O que é um bom teste

Um bom teste verifica comportamento observável numa das duas fronteiras escolhidas e nunca detalhes internos. Não verifica:

- chamadas a funções privadas;
- a forma das tabelas;
- a ordem de invocações internas.

Cada teste tem a marca de rastreabilidade com o requisito ou a lacuna que cobre. Nenhum teste chama a API da Anthropic, nem de forma marcada, nem opcional. O relógio e os geradores de identificadores são injectados.

### Fronteira 1: API HTTP

Esta é a fronteira principal. Os testes percorrem o fluxo como um cliente:

1. carregamento;
2. estado do trabalho;
3. resultados;
4. candidatos;
5. correcção, aceitação e resolução de entidade;
6. exportação.

Só se substituem as portas externas:

- `FakeInvoiceExtractor` devolve facturas já extraídas, declaradas no próprio teste;
- `FakeItemClassifier` devolve índices declarados, incluindo `none`, índices fora dos limites e respostas malformadas;
- `FakeItemClassifier` simula também falhas transitórias.

O catálogo é um **catálogo sintético** com a estrutura real das colunas. Inclui `O00999`, um item genérico, um par PT/EN divergente, um item sem descrição EN e uma descrição com caracteres invisíveis. A base de dados é SQLite num ficheiro temporário.

Casos que esta fronteira tem de cobrir:

- encaminhamento para cada aba;
- recurso em OUTLAYSP;
- ausência de correspondência em OUTLAYS;
- item genérico;
- resposta inválida;
- índice fora dos limites;
- factura ambígua não codificada e depois resolvida;
- correcção fora da aba recusada;
- idempotência do carregamento;
- duplicado provável;
- linhas de IVA e de desconto;
- linhas de resumo ausentes da saída;
- as nove colunas, pela ordem certa;
- neutralização de fórmulas;
- UTF-8 com BOM;
- a exportação a reflectir as revisões;
- uma falha isolada num lote;
- repetição de falhas transitórias;
- arranque recusado com catálogo inválido.

### Fronteira 2: regras de domínio puras

São testes de tabela, sem nada montado.

**Verificação de entidade.** Os casos mínimos são:

- nome exacto;
- `Lda.` em vez de `Limitada`;
- nome sem hífen;
- nome com acentos;
- nome em maiúsculas;
- empresa irmã na lista de exclusão com nome quase igual;
- empresa irmã não listada (nome do alvo com um sufixo geográfico);
- nome contido no nome alvo;
- companhia de navegação;
- cliente terceiro;
- nenhum nome;
- dois nomes distintos.

**Regra de confiança e de `conflicting_candidates`.** Os casos ficam nos limites de cada limiar, incluindo:

- o modelo escolhe o topo;
- o modelo escolhe o segundo;
- o modelo escolhe um item fora dos dois primeiros;
- `none` em cada aba;
- item genérico;
- resolução humana da entidade.

### Conjunto dourado

O conjunto dourado é feito das amostras, lidas de um caminho local configurado por variável de ambiente, e **nunca** do repositório.

Os resultados esperados ficam num ficheiro de configuração editável, para poderem evoluir. Para cada linha de cada amostra, o ficheiro dá a entidade, a aba de destino e o código de item esperados. Os códigos esperados são os do catálogo actual. A proposta inicial está no ticket do conjunto dourado e é confirmada pela AMT.

`make golden` mede por omissão só as etapas determinísticas, sem chamar o modelo:

- extracção;
- verificação de entidade;
- aba de destino;
- tipos de linha;
- recusas.

A medição dos códigos de item com o modelo real é um comando manual e explícito, fora da suite de testes. Nenhuma métrica de precisão é publicada antes de a AMT confirmar os resultados esperados.

### Exemplos anteriores

Não há código nem testes no repositório. Seguem-se as convenções do documento de padrões de código: duplos nomeados, a marca de requisito, e os alvos `make test`, `make golden` e `make traceability-matrix`.

## Out of Scope

- Extracção de XLSX e de PDF que não siga o modelo das amostras.
- OCR de PDF digitalizado. Estes PDF são recusados.
- Notas de liquidação aduaneira da AGT. São recusadas como documento não suportado, até a AMT confirmar se entram no circuito.
- O frontend. Esta spec entrega a API sobre a qual se constroem os ecrãs de carregamento e de revisão.
- Autenticação e perfis (L-07). A aplicação fica ligada apenas a `127.0.0.1`, e o autor da revisão vem da configuração.
- O conteúdo da lista de exclusão (L-04).
- A calibração dos limiares e a publicação de métricas de precisão (L-02).
- O encaminhamento por linha em facturas com várias entidades facturadas (L-09).
- O tratamento próprio de notas de crédito, além da sinalização de duplicado provável.
- Cache de prompt e outras optimizações de custo (L-12).
- A recarga do catálogo em tempo de execução e a recodificação de resultados antigos.
- A integração com o Business Central e a ingestão por correio electrónico.
- A retenção e purga de dados (L-11).

## Further Notes

- **Documentos de desenho.** As decisões desta spec foram passadas para `docs/` e para o `CLAUDE.md` em 18-11-2026. Isto inclui o novo limite de itens enviados ao modelo em `docs/03-seguranca.md`. Uma divergência que apareça entre a spec e os documentos deve ser assinalada, não resolvida em silêncio.
- **Decisões provisórias.** Várias decisões são provisórias e podem ser revertidas pela resposta: L-06 (tipos de linha), L-08 (OUTLAYS sem correspondência e O00052), a aba de destino vazia e o NIF do fornecedor. O desenho deve permitir mudar cada uma sem reescrita: listas e limiares em configuração ou constantes, e motivos num conjunto fechado.
- **Fronteira de segurança.** O modelo devolve apenas um índice validado, nunca um código. Nenhuma alteração desta spec enfraquece esta fronteira.
- **Gates de fecho.** Antes de declarar concluído, percorrer os gates do `CLAUDE.md`: o gate de segurança, o bloco de fecho, a lista de verificação dos padrões, e `make test`, `make golden` e `make traceability-matrix`.
