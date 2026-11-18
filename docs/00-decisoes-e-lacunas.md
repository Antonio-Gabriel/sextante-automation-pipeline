# Decisões de Arquitectura e Lacunas por Resolver

**Projecto:** Sextante, Pipeline de Codificação Automática de Linhas de Facturas de Fornecedores
**Cliente:** AMT, Advanced Maritime Transports - Transitarios Limitada
**Origem:** Teste técnico "Automated Supplier Invoice Line-Item Encoding Pipeline"
**Stack:** Python 3.12 com FastAPI · React 18 com TypeScript · SQLite · Claude
**Versão:** 0.2 · 18-11-2026
**Estado:** rascunho para validação. Revisto em 18-11-2026, depois da sessão de grilling e da análise das amostras: ver §3.15 a §3.18, as lacunas L-13 a L-16 e o registo do §5

---

## 1. Como ler este documento

Este documento tem duas partes. A secção 3 lista as **decisões tomadas** e porquê, para que não sejam rediscutidas a meio da construção. A secção 4 lista as **lacunas**, ou seja, o que não é possível decidir sem informação que não está no enunciado. Cada lacuna traz uma sugestão concreta, para que a ausência de resposta não bloqueie o trabalho.

Regra de trabalho: nenhuma lacuna fica aberta sem decisão por omissão registada. Se a resposta não chegar, aplica-se a sugestão, e a decisão passa a constar da secção 3.

Convenção de identificadores usada em todos os documentos:

| Prefixo | Significado |
|---|---|
| `D-n.n` | Decisão de arquitectura tomada, na subsecção §3.n deste documento |
| `L-nn` | Lacuna por resolver |
| `REQ-<AREA>-nnn` | Requisito de engenharia, em `01-requisitos.md` |
| `NFR-<AREA>-nnn` | Requisito não funcional, em `01-requisitos.md` |
| `SEC-nn` | Invariante de segurança, em `03-seguranca.md` |

---

## 2. Sobre o nome

**Sextante.** Instrumento de navegação que fixa a posição de uma embarcação a partir da observação de um astro. O pipeline faz o equivalente: a partir da observação de uma descrição livre, fixa a posição exacta dessa linha no catálogo de itens. O nome funciona em português e em inglês, assenta no domínio marítimo do cliente, e é específico o suficiente para que uma busca no repositório devolva código deste projecto e não ruído.

Convenções derivadas do nome, fixadas agora para não divergirem depois:

| Artefacto | Valor |
|---|---|
| Repositório | `sextante` |
| Pacote Python | `sextante` |
| Prefixo de variáveis de ambiente | `SEXTANTE_` |
| Prefixo de variáveis públicas do frontend | `VITE_SEXTANTE_` |
| Base de dados | `sextante.db` |
| Rede Docker interna | `sextante-internal` |
| Nome dos eventos de log | `snake_case` em Inglês, sem prefixo |

---

## 3. Decisões tomadas

### 3.1 Restrições que não são negociáveis

Vêm do enunciado do teste e das decisões já tomadas em conversa. Alterá-las é alterar o âmbito.

| # | Restrição | Origem |
|---|---|---|
| R1 | O código de item devolvido é o valor **exacto** da coluna `No.` (Coluna A) do catálogo | Enunciado, secção 2, passo 2 |
| R2 | A ordem dos três passos é **estrita**: verificação de entidade, encaminhamento e mapeamento, confiança e excepções | Enunciado, secção 2 |
| R3 | A regra de recurso `O00999` aplica-se **apenas** a OUTLAYSP | Enunciado, secção 2, passo 2 |
| R4 | Facturas emitidas a clientes terceiros, companhias de navegação ou empresas irmãs contam como **não correspondentes**, ainda que o nome seja parecido | Enunciado, secção 2, passo 1 |
| R5 | Diferenças menores de maiúsculas, pontuação e sufixo societário (`Limitada` e `Lda.`) **não** quebram a correspondência | Enunciado, secção 2, passo 1 |
| R6 | A saída tem as nove colunas especificadas, com esses nomes exactos | Enunciado, secção 3 |
| R7 | Os prompts de sistema são entregues, **sem chaves de API** | Enunciado, secção 3 |
| R8 | O `README.md` explica onde foi usada IA e onde foi usada lógica determinística, e porquê | Enunciado, secção 3 |
| R9 | Facturas chegam em **PDF ou XLSX**. Nenhum outro formato é aceite nesta versão | Decisão do projecto |
| R10 | O modelo de linguagem é o **Claude**, pela API da Anthropic | Decisão do projecto |
| R11 | A persistência é **SQLite** | Decisão do projecto |
| R12 | Todo o código, identificadores, comentários e logs em **Inglês**. Todo o texto de interface em **Português** | Decisão da equipa |
| R13 | O modelo de linguagem **nunca** devolve um código de item livre. Escolhe de uma lista de candidatos fornecida pelo servidor, e a escolha é validada contra o catálogo antes de ser persistida | Decisão de segurança, `03-seguranca.md` SEC-14 |

A restrição R13 é a mais fácil de violar sem dar por isso, e é a que separa este desenho de um que aceita o que o modelo devolver. Ver a secção 3.7.

### 3.2 Estilo arquitectural

**Monólito modular, um processo.** Um serviço FastAPI dividido em módulos com fronteira explícita, cada um com as suas camadas `api`, `application`, `domain` e `infrastructure`. A comunicação entre módulos faz-se por contratos publicados, nunca por acesso directo ao modelo interno de outro módulo.

Porquê e não microsserviços: o domínio é pequeno e fortemente sequencial, a operação é de uma equipa de contabilidade, e o protótipo tem de arrancar com um comando. Microsserviços acrescentariam orquestração e consistência eventual onde não há ganho nenhum.

**Frontend: React com Vite, uma aplicação.** Camadas simples, `pages`, `features`, `entities`, `shared`, com dependência descendente. Não se adopta Feature-Sliced Design completo porque a aplicação tem cinco ecrãs e a cerimónia não se paga.

**Trabalho pesado: processo em segundo plano, no mesmo processo.** Ver a secção 3.4.

### 3.3 Volume e dimensionamento

O enunciado fala de 5.000 facturas por mês. Em dias úteis são cerca de 250 por dia, o que não justifica infraestrutura de escala. Mas o número que dimensiona o sistema não é esse:

| Grandeza | Valor assumido | Consequência |
|---|---|---|
| Facturas por mês | 5.000 | Irrelevante por si só |
| Linhas por factura | 6 a 10 | 30.000 a 50.000 linhas por mês |
| Chamadas ao modelo por factura | 1, em lote de linhas | 5.000 chamadas por mês, não 50.000 |
| Pico diário | 2.000 facturas no fecho do mês | É isto que dimensiona |
| Duração de uma chamada ao modelo | 2 a 5 segundos | 2.000 facturas em série levam horas |

A conclusão é que o gargalo é a latência do modelo em dia de pico, não o volume mensal. Daí a decisão da secção 3.4 e a decisão de agrupar as linhas de uma factura numa só chamada, em 3.7.

### 3.4 Assincronia sem fila

Decisão: **tabela de trabalhos em SQLite, consumida por um trabalhador assíncrono no mesmo processo.** Sem RabbitMQ, sem Celery, sem Redis.

| Hipótese | Vantagem | Razão da rejeição |
|---|---|---|
| Processamento síncrono no pedido HTTP | Zero infraestrutura | Um lote de 300 facturas estoura o tempo de espera do cliente e de qualquer proxy à frente. Inaceitável |
| Celery com RabbitMQ ou Redis | Maturidade, retries, dead-letter | Dois contentores e um corretor para uma carga de 250 trabalhos por dia. Custo operacional sem retorno |
| `arq` ou `TaskIQ` sobre Redis | Nativamente assíncrono, leve | Continua a exigir Redis |
| **Tabela `job` em SQLite com trabalhador em processo** | Transaccional com os dados, zero componentes novos, visível por `SELECT` | Escolhida. Não sobrevive a múltiplas réplicas da API, o que nesta escala não é requisito |

O que isto dá, e que o processamento síncrono não dá:

- O carregamento devolve um identificador de trabalho de imediato, com estado `queued`.
- O frontend acompanha o progresso por sondagem, linha a linha.
- Uma falha numa factura não derruba o lote. O trabalho continua e a factura fica em `failed` com o motivo.
- Repetição com recuo exponencial, até três tentativas, para falhas transitórias do modelo.

O que isto **não** dá, e tem de ficar escrito: se a API escalar para mais do que um processo, dois trabalhadores competem pela mesma tabela. A mitigação é um `UPDATE ... WHERE status = 'queued'` com reivindicação atómica e `rowcount` verificado, que funciona em SQLite com WAL mas não substitui uma fila a sério. Quando o volume justificar mais do que um processo, a decisão é revista, e o caminho natural é `procrastinate` sobre PostgreSQL, pela mesma razão que leva à secção 3.5.

### 3.5 Persistência

Decisão: **SQLite 3 com WAL, acedido por SQLAlchemy 2 em modo assíncrono, através de `aiosqlite`.**

| Opção | Avaliação |
|---|---|
| **SQLite com WAL** | Escolhida. Zero infraestrutura, ficheiro único, transaccional, suficiente para a escala declarada |
| PostgreSQL | Correcto para produção, excessivo para o protótipo. É o caminho de migração previsto |
| Ficheiros CSV e JSON no disco | Sem transacções, sem restrições de unicidade, sem consultas. Inviável para idempotência e auditoria |
| Sem persistência, só memória | Elimina revisão humana, auditoria e idempotência, que são três dos entregáveis implícitos |

Condições de uso do SQLite que não são opcionais:

- `PRAGMA journal_mode=WAL`, para leitura concorrente com escrita.
- `PRAGMA foreign_keys=ON`. Está desligado por omissão no SQLite, o que é uma armadilha conhecida.
- `PRAGMA busy_timeout=5000`, para que uma escrita concorrente espere em vez de falhar.
- Um único escritor por vez. A camada de aplicação serializa as escritas do trabalhador.
- O esquema é criado e evoluído por **Alembic**, não por `CREATE TABLE IF NOT EXISTS` espalhado pelo código. Mesmo num protótipo, a migração é o que permite mudar de ideias sem perder os dados de revisão já feitos.

**O desenho é portável de propósito.** Nenhuma consulta usa sintaxe específica do SQLite. Todas as datas são guardadas em UTC, em texto ISO 8601, porque o SQLite não tem tipo de data e a conversão implícita é fonte de erro. A migração para PostgreSQL deve ser uma mudança de URL de ligação e uma migração de dados, não uma reescrita.

### 3.6 Extracção de facturas

Decisão: porta `InvoiceExtractor`, escolhida pelo **tipo real do conteúdo** e nunca pela extensão. A porta devolve uma factura extraída ou uma recusa com motivo. *Revisto em 18-11-2026.*

| Formato | Biblioteca | Licença | Nota |
|---|---|---|---|
| PDF nativo no modelo das amostras | `pdfplumber` | MIT | Implementado nesta versão. Texto com coordenadas, o que permite separar colunas e recortar regiões |
| XLSX | `openpyxl` | MIT | **Não implementado nesta versão**, por não haver nenhuma amostra. Recusado com `unsupported_document_type`, por REQ-ING-001 e REQ-ING-009 (decidido em 18-11-2026). Quando for, leitura em `read_only` e `data_only` |
| PDF digitalizado | não implementado | | Recusado com `pdf_without_text_layer`. Porta `OpticalCharacterRecognizer` declarada. Ver L-01 |
| Outro documento, como a nota de liquidação aduaneira da AGT | não implementado | | Recusado com `unsupported_document_type`. Ver L-14 |

O `pandas` entra na manipulação tabular depois da extracção e na geração da saída, não na leitura do ficheiro carregado. Ler um ficheiro desconhecido com `pandas.read_excel` esconde a validação de tipo que a secção SEC-16 de `03-seguranca.md` exige.

O que as amostras obrigam a extracção de PDF a fazer:

- **Separar colunas por coordenadas.** Os blocos "FROM / FORNECEDOR" e "BILL TO / CLIENTE" estão lado a lado, e o texto corrido mistura-os na mesma linha.
- **Recortar a faixa de topo por região.** O nome do fornecedor está na faixa de topo, não no bloco FROM, e nalgumas facturas sobrepõe-se a "INVOICE / FACTURA", o que entrelaça o texto corrido.
- **Juntar descrições partidas.** Uma linha de continuação, sem números, junta-se à anterior: sem espaço numa quebra a meio da palavra, com espaço numa quebra num espaço.
- **Ler valores no formato `1,206.00`**, com a moeda tirada do cabeçalho da coluna de valor.

A entidade facturada é **a primeira linha** do bloco da entidade facturada. Uma linha "c/o" ou "a/c" é registada como "ao cuidado de" e nunca entra na verificação de entidade (3.15). Se nenhum bloco for encontrado, a entidade fica ambígua e a factura vai para revisão. **Nunca adivinhar a entidade.** Adivinhar errado no passo 1 encaminha toda a factura para a aba errada, o que é o erro mais caro que este sistema pode cometer.

### 3.7 Fronteira entre lógica determinística e modelo de linguagem

Esta é a decisão central do projecto e a pergunta que o enunciado faz explicitamente. O princípio é: **o modelo só é chamado onde a ambiguidade é linguística. Tudo o que é regra fica em código.**

| Passo | Mecanismo | Porquê |
|---|---|---|
| Normalização de texto | Determinístico. NFC, minúsculas, remoção de pontuação e de sufixo societário | É uma transformação, não um juízo |
| Lista de exclusão de entidades | Determinístico. Correspondência exacta sobre nome normalizado | R4 exige recusa estrita. Um modelo que "acha" que uma empresa irmã é a AMT viola uma regra contratual |
| Correspondência de entidade | Determinístico. Igualdade do nome normalizado, veto pelo NIF, e semelhança abaixo do limiar baixo para a não correspondência | R5 é tolerância ortográfica, que a normalização resolve. Ver 3.15 |
| Entidade ambígua | **Humano**, por resolução de entidade | R4 é recusa estrita. Um modelo que desempata está a decidir que uma empresa é a AMT. O desempate pelo Claude foi retirado em 18-11-2026 |
| Encaminhamento para OUTLAYS ou OUTLAYSP | Determinístico. `if` sobre o resultado do passo 1. Entidade ambígua não tem aba | É a regra do enunciado, literalmente |
| Classificação do tipo de linha | Determinístico. Padrão que reconhece só o IVA do fornecedor | Ver 3.17 |
| Pontuação lexical | Determinístico. `rapidfuzz` sobre as descrições PT e EN de **todos** os itens da aba de destino, guardando o máximo das duas | Sinal de confiança, não filtro. Ver 3.16 |
| Escolha do item | **Claude**, sobre a aba de destino inteira | Comparar "Taxa de movimentação de contentor" com oito descrições de catálogo em dois idiomas é exactamente o que um modelo faz melhor do que uma métrica de distância |
| Recurso para `O00999` | Determinístico. Só se o encaminhamento foi OUTLAYSP e o modelo declarou que nenhum candidato serve | R3 limita o recurso a uma aba. A verificação dessa condição é código |
| Classificação de confiança | Determinístico. Regra sobre o score de recuperação, o intervalo até ao segundo candidato, e a concordância do modelo | Ver 3.8 |
| Sinalização para revisão | Determinístico. Regra sobre a confiança e sobre as condições do passo 3 | É política, não juízo |

**Agrupamento das chamadas.** Uma factura é uma chamada ao modelo, com todas as suas linhas de serviço e a lista de itens da aba de destino, enviada uma vez. Não uma chamada por linha. Reduz as chamadas mensais de cerca de 50.000 para cerca de 5.000, e dá ao modelo o contexto das linhas vizinhas, que ajuda em descrições abreviadas.

**Configuração da chamada.** *Revista em 18-11-2026 por 3.22.* `temperature=0`, saída estruturada por ferramenta com esquema declarado, e `max_tokens` dimensionado ao número de linhas. A resposta é validada por Pydantic antes de qualquer uso. Uma resposta que não cumpra o esquema é tratada como falha de linha, não como motivo para improvisar.

### 3.8 Confiança derivada, não auto-declarada

Decisão: a confiança **não** é pedida ao modelo. É calculada.

A razão é de calibração. Modelos de linguagem são maus avaliadores da sua própria certeza: pedir `HIGH`, `MEDIUM` ou `LOW` devolve uma distribuição quase sempre optimista, e sobretudo não reproduzível, porque a mesma linha pode receber classificações diferentes em execuções diferentes. Num sistema cujo propósito é decidir o que vai para revisão humana, uma confiança não calibrada é pior do que nenhuma: enche a fila de revisão com casos fáceis e deixa passar os difíceis.

A regra, em `matching/confidence.py`, com os limiares em constantes `Final` num só ficheiro:

| Classificação | Condição |
|---|---|
| `HIGH` | O modelo escolheu um item, esse item é o topo lexical, o score dele está acima do limiar alto, e a distância ao segundo está acima do mínimo |
| `MEDIUM` | O modelo escolheu um item válido e não se cumpre o resto da condição `HIGH` |
| `LOW` | Recurso para `O00999`, o modelo declarou que nenhum item serve, a resposta do modelo falhou validação, ou o item escolhido é genérico (3.16) |

Toda a linha `LOW` é sinalizada para revisão. A sinalização `conflicting_candidates` dispara quando o item escolhido é um dos dois primeiros lexicais e os dois estão a menos da distância mínima, para não sinalizar linhas em que o modelo escolheu claramente um terceiro item.

Uma factura com entidade ambígua não chega a esta regra: não é codificada, e as suas linhas saem sem aba de destino, sem código, com `LOW` e sinalizadas (3.15). Depois da resolução de entidade por um humano, as linhas seguem esta regra sem limite, e podem chegar a `HIGH`. *Revisto em 18-11-2026.*

Os limiares nascem calibrados contra o conjunto dourado das facturas de amostra, assim que este existir. Até lá, ficam em valores declarados no documento de requisitos como provisórios, e isso é dito no `README.md`.

### 3.9 Catálogo

Decisão: carregado uma vez no arranque, mantido em memória, **versionado pelo digest do ficheiro**.

- Leitura por `openpyxl`, as duas abas, com validação de que a coluna A existe e tem valores não vazios e únicos.
- Colunas conhecidas desde 18-11-2026: `No.` (A), `Description` (B, português) e `Description 2` (C, inglês). OUTLAYS tem 44 itens e OUTLAYSP tem 20, com códigos únicos e nenhum código em comum entre abas. O prefixo do código **não** identifica a aba.
- Cada item tem valores de apresentação e valores de comparação. Os de apresentação são o código exacto e a descrição PT sem espaços nas pontas, que é a exportada. Os de comparação são as descrições PT e EN em NFKC, sem caracteres invisíveis e com os espaços colapsados. O catálogo não é corrigido em código, nem quando as duas descrições se contradizem (L-05).
- O arranque falha se `O00999` não existir em OUTLAYSP, e avisa, sem falhar, sobre caracteres invisíveis e descrições EN vazias.
- A pontuação lexical é feita por aba, separadamente. OUTLAYS e OUTLAYSP nunca se misturam, porque isso derrotaria o passo 2.
- O digest SHA-256 do ficheiro de catálogo é guardado em cada resultado codificado. Sem isso, um resultado de ontem não é reproduzível quando o catálogo mudar, e numa codificação com impacto fiscal a reprodutibilidade é a diferença entre explicar e adivinhar.
- Recarregar o catálogo é uma operação explícita, com novo digest, que **não** recodifica resultados anteriores.

### 3.10 Idempotência

Decisão: **o digest SHA-256 do conteúdo do ficheiro é a chave de idempotência.**

Carregar duas vezes a mesma factura não cria dois trabalhos nem duas codificações. A restrição única está na tabela, não numa verificação prévia em código, porque verificar e depois escrever é uma condição de corrida que dois carregamentos simultâneos ganham os dois.

A resposta a um carregamento repetido é o trabalho existente, com o seu estado, e não um erro. Um carregamento repetido é um comportamento normal de quem não sabe se o primeiro passou.

O `Invoice_ID` da saída é `<fornecedor>/<número da factura>`. O fornecedor é identificado pelo NIF quando extraído, e pelo nome normalizado quando não. Um digest curto substitui o número quando este falta. Nunca é um contador, que não sobrevive a reprocessamentos. O fornecedor entra porque dois fornecedores emitem com facilidade o mesmo número.

A idempotência por digest só apanha o mesmo ficheiro. Uma factura com o mesmo fornecedor e o mesmo número de outra, mas com digest diferente, é codificada na mesma e sinalizada como **duplicado provável**, com referência à anterior. Bloquear seria adivinhar, porque uma nota de crédito pode reutilizar o número. Ver L-15. *Revisto em 18-11-2026.*

### 3.11 Trilho de auditoria

Decisão: cada decisão fica registada com o que a produziu. Não é refinamento, é entregável.

Para cada linha codificada, guarda-se: a descrição original, o texto normalizado, a aba de destino, os scores lexicais de todos os itens da aba de destino, a escolha do modelo, o identificador do modelo e a versão do prompt, o digest do catálogo, a classificação de confiança e a regra que a produziu, e o momento da codificação. Quando houver revisão humana, guarda-se o valor anterior, o novo, quem alterou e quando.

A razão é dupla. Em contexto fiscal, "o sistema atribuiu este código" não é resposta a um auditor. E em contexto de melhoria, cada correcção humana é um exemplo rotulado, que é o material de que se precisa para afinar limiares ou construir exemplos no prompt.

Os registos de auditoria são **apenas inseridos**. Nunca actualizados nem eliminados pela aplicação. Uma correcção é um novo registo, não uma alteração do anterior.

### 3.12 Revisão humana

Decisão: o frontend inclui ecrã de revisão. O enunciado pede para sinalizar casos para revisão humana, e entregar isso apenas como uma coluna num CSV é meio caminho.

Âmbito deliberadamente curto, porque o esforço tem de ir para a qualidade do mapeamento e não para a interface:

| Entra | Fica fora |
|---|---|
| Carregamento, com acompanhamento do progresso | Autenticação e perfis, ver L-07 |
| Tabela de resultados, com filtro por confiança e por aba | Painéis e gráficos |
| Edição do código de item atribuído, com escolha a partir do catálogo | Edição das descrições extraídas |
| Nota de revisão por linha | Discussão ou aprovação em várias etapas |
| Aceitação de uma linha sinalizada sem a alterar | |
| Resolução de entidade de uma factura ambígua, com nota obrigatória | Alteração da lista de exclusão pela interface |
| Botão de exportação para CSV e XLSX | Agendamento de exportações |

### 3.13 Exportação

Decisão: as nove colunas de R6, por essa ordem e com esses nomes, em CSV e em XLSX, geradas a partir do estado persistido e não do resultado em memória do último trabalho.

O CSV é escrito com **neutralização de injecção de fórmula**: qualquer célula que comece por `=`, `+`, `-`, `@`, tabulação ou retorno de carro é prefixada com apóstrofo. Uma descrição de factura é conteúdo de origem externa, e um ficheiro que a contém vai ser aberto no Excel por alguém da contabilidade. Ver `03-seguranca.md` SEC-17.

A exportação reflecte as revisões humanas. As colunas `Assigned_Item_No` e `Notes_or_Flags` mostram o valor em vigor; a auditoria guarda o percurso.

### 3.14 Licenças das dependências

Nenhuma dependência com modelo de subscrição no código do projecto. Lista branca em `01-requisitos.md`, NFR-LIC-001. A excepção é o acesso à API da Anthropic, que é um serviço pago e está declarado como tal, não uma dependência de código.

Verificação de licença antes de acrescentar qualquer dependência, como nas regras transversais do `CLAUDE.md`.

### 3.15 Verificação de entidade sem modelo

Decisão: a verificação de entidade é **totalmente determinística**. *Revisto em 18-11-2026.*

Recebe o nome da entidade facturada (a primeira linha do bloco) e o NIF dela, o nome e o NIF da entidade alvo, vindos de configuração, e a lista de exclusão. Avalia por esta ordem:

1. Nenhum bloco de entidade facturada: `AMBIGUOUS`, motivo `entity_label_not_found`.
2. Mais do que um bloco: `AMBIGUOUS`, motivo `multiple_billed_entities`.
3. Nome na lista de exclusão, por igualdade sobre o nome normalizado: `NO_MATCH`.
4. NIF extraído e diferente do NIF da entidade alvo: nunca `MATCH`. Com o nome normalizado igual ao alvo, `AMBIGUOUS` com o motivo `entity_nif_mismatch`. Com o nome diferente, seguem-se as regras 6 e 7.
5. Nome normalizado igual ao nome alvo normalizado: `MATCH`.
6. Semelhança abaixo do limiar baixo: `NO_MATCH`.
7. Todos os outros casos: `AMBIGUOUS`, motivo `entity_similar_not_equal`.

A normalização trata maiúsculas, pontuação, hífen, espaços, acentos e as formas do sufixo `limitada`, `lda` e `ltda`. A semelhança usa `token_sort_ratio` ou `ratio`, **nunca** `token_set_ratio`, que dá 100 quando um nome está contido no outro e não distingue a AMT de uma irmã chamada "Advanced Maritime Transports Moçambique". Um NIF igual ao da AMT nunca basta, sozinho, para dar `MATCH`.

As linhas "ao cuidado de" nunca entram na verificação. Em INV-002, "Operadora Sintética de Petróleo Angola, c/o Advanced Maritime Transports" é `NO_MATCH` e vai para OUTLAYSP.

Uma factura `AMBIGUOUS` **não é codificada**. As linhas saem com `Exact_Entity_Match = NO`, `Target_Sheet` vazio, sem código, com `LOW` e sinalizadas. O `Target_Sheet` vazio é um desvio declarado ao formato de saída (L-13). Encaminhar para OUTLAYSP por "não ser correspondência" aplicaria `O00999` por omissão a facturas que podem ser da AMT.

Um revisor desbloqueia a factura com a **resolução de entidade**: escolhe `MATCH` ou `NO_MATCH` e escreve uma nota obrigatória. A resolução fica na auditoria e a factura é codificada a partir do texto extraído. A resolução não altera a lista de exclusão, que é configuração e só muda por decisão explícita.

O desempate pelo Claude, que existia na versão 0.1, foi retirado. Com a regra 7, toda a zona cinzenta já ia para o humano, e um desempate pelo modelo seria o modelo a decidir que uma empresa é a AMT, o que R4 proíbe.

### 3.16 O modelo vê a aba de destino inteira

Decisão: a lista enviada ao modelo é **a aba de destino inteira**, por ordem fixa do catálogo, com índice, código, descrição PT e descrição EN. Deixa de haver recuperação dos oito melhores candidatos. *Revisto em 18-11-2026.*

Com 44 e 20 itens, a recuperação resolvia um problema que não existe e criava outro. A semelhança lexical entre idiomas falha: "Passagem aérea" não se parece com "Bilhete Avião". Se o item certo não entra nos oito, o modelo não o pode escolher, e o erro é invisível.

R13 mantém-se intacta. A lista é construída pelo servidor, o modelo devolve um índice ou `none`, e o índice é validado contra a lista e contra a aba antes de ter efeito.

O score lexical é o máximo entre a comparação com a descrição PT e com a descrição EN, calculado para todos os itens da aba e persistido. Deixa de filtrar e passa a ser só sinal: entra na confiança (3.8) e no ecrã de revisão, que mostra a aba inteira ordenada por score.

**Itens genéricos.** `O00052 Outras Despesas` é um item válido de OUTLAYS, mas escolhê-lo livremente seria um recurso escondido, que contornaria L-08. Os itens genéricos ficam numa lista de configuração, inicialmente só com `O00052`, e escolher um deles dá sempre `LOW` com o motivo `generic_catalog_item`.

### 3.17 Tipos de linha

Decisão: os tipos de linha são `service`, `tax` e `discount`. O que não é reconhecido como `tax` ou `discount` é `service`. *Revisto em 18-11-2026.*

- **Linhas de resumo.** Subtotal e total não são linhas da factura: não aparecem na saída e ficam só na auditoria.
- **IVA e desconto.** Aparecem na saída sem código, com `HIGH` (a classificação é certa e não há código para errar), com a nota `line_type_tax` ou `line_type_discount`, aceites e **sem** sinalização. Sinalizá-las encheria a fila de revisão com casos fáceis.
- **Padrão de `tax`.** Reconhece só o IVA do fornecedor: "IVA", "VAT", "Imposto sobre o Valor Acrescentado". Nunca reconhece "taxa" ou "imposto" sozinhos. "Taxa de pilotagem" é um serviço, e um direito aduaneiro também.
- **Percentagem de IVA.** É guardada como atributo da linha.

Nas amostras, o IVA nunca aparece como linha da tabela. É uma coluna de percentagem e uma linha de resumo. A política acima existe para o caso de aparecer, e continua por confirmar com a contabilidade (L-06).

### 3.18 Amostras e conjunto dourado

Decisão: as amostras **não** entram no repositório. *Revisto em 18-11-2026.*

- O conjunto dourado lê as amostras de um caminho local configurado por variável de ambiente.
- Os testes usam réplicas sintéticas geradas por script e identificadas como sintéticas, que reproduzem as particularidades das amostras.
- Os resultados esperados (entidade, aba de destino e código de item por linha) ficam num ficheiro de configuração editável, com os códigos do catálogo actual. A proposta inicial está no ticket do conjunto dourado e espera confirmação da AMT.
- `make golden` mede, sem chamar o modelo, as etapas determinísticas: extracção, verificação de entidade, aba de destino, tipos de linha e recusas. A medição dos códigos de item com o modelo real é um comando manual e explícito, fora da suite de testes, para cumprir a regra de nenhum teste chamar a API da Anthropic.
- Nenhuma métrica de precisão é publicada antes de a AMT confirmar os resultados esperados.

### 3.19 Idempotência do carregamento

Decisão: o carregamento (`POST /api/invoices`) é o único `POST` isento de `Idempotency-Key`. *Decidido em 18-11-2026.*

- **Porquê.** O carregamento já é idempotente pelo conteúdo: o digest SHA-256 de cada ficheiro tem restrição única, e reenviar o mesmo ficheiro devolve o trabalho existente sem nova chamada ao modelo (REQ-ING-007, SEC-19, nível «Carregamento»). Uma chave HTTP por cima repetiria a mesma garantia.
- **O que fica coberto pela chave.** As escritas de revisão (`PATCH` de correcção, `POST` de aceitação) e o reprocessamento, que não têm uma identidade de conteúdo que as torne idempotentes por si.
- **Uma escrita nova** que não seja idempotente pelo conteúdo exige a chave. A isenção não se estende por analogia.

### 3.20 Reprocessamento só de facturas com falha

Decisão: nesta versão, o reprocessamento aceita só facturas `failed`. Uma factura codificada ou recusada é recusada com 409; uma já na fila fica como está. *Decidido em 18-11-2026.*

- **O que fica por fazer.** NFR-REL-002 dá como motivo recalibrar limiares ou corrigir um prompt, e SEC-19 pede que um reprocessamento escreva uma nova linha de resultado, sem alterar a anterior. Recodificar uma factura já codificada, com o histórico guardado, fica para um ticket próprio, depois do adaptador e do prompt (ticket 11), porque é a mudança de prompt que o justifica.
- **Até lá,** NFR-REL-002 está cumprido para facturas com falha: a codificação parte do texto guardado, sem nova extracção nem novo carregamento.

### 3.22 Configuração da chamada ao modelo e prompt v1

Decisão tomada pelo responsável em 18-11-2026, ao aprovar a proposta do ticket 11. Substitui a configuração de 3.7.

- **Sem `temperature`.** A API recusa `temperature`, `top_p` e `top_k` em todos os modelos desde 21-10-2026. A reprodutibilidade que importa vive em código: a confiança, as sinalizações e o recurso não dependem da amostragem (3.8).
- **Saída por esquema, não por ferramenta forçada.** Os modelos actuais recusam `tool_choice` forçado. A resposta é JSON restringido por `output_config.format`, com o esquema declarado, e continua validada no servidor antes de qualquer efeito (SEC-14).
- **Modelo.** `SEXTANTE_MODEL_ID`, por omissão `claude-sonnet-5-5`. *Revisto em 18-11-2026, por pedido do responsável:* o Sonnet substitui o `claude-opus-5-5` por custo, a metade do preço por token. Mede-se com `make golden-model` antes de se dar por adquirido que acerta o mesmo. O modelo que respondeu fica registado em cada decisão.
- **Esforço e limite.** `effort` baixo, por ser uma classificação. `max_tokens` de 2048 mais 64 por linha, porque o raciocínio, sempre ligado nestes modelos, conta para o limite.
- **Recusa de segurança.** O recurso de servidor (`fallbacks: "default"`) tenta outro modelo. Se a recusa persistir, ou a resposta vier cortada ou ilegível, todas as linhas ficam com resposta inválida, `LOW` e sinalizadas, sem nova tentativa.
- **Falhas transitórias.** Rede, tempo esgotado, 429 e 5xx são `ItemClassifierUnavailableError`, repetidas pelo caso de uso com recuo. O cliente da API não repete por si.
- **Prompt v2 e cache** (`item-choice-v2`, aprovado pelo responsável em 18-11-2026). A lista de candidatos sai de `<invoice_data>` para um segundo bloco de sistema, `<catalog_candidates>`, marcado para a cache de prompt: é igual em todas as facturas de uma aba, e as chamadas seguintes lêem-na a um décimo do preço. Só o segundo parágrafo do texto muda. O conteúdo da factura nunca entra na parte em cache. Os tokens escritos e lidos da cache ficam registados em cada chamada (migração 0008).
- **Prompt v1** (`item-choice-v1`, substituído pelo v2, guardado para as decisões que o usaram). O texto em `backend/src/sextante/prompts/item_choice_v1.txt` foi aprovado pelo responsável tal como está. Pede só um índice ou `null` por linha, trata o conteúdo da factura como dados delimitados (`<invoice_data>`, com `<` escapado) e não repete nenhuma regra que vive em código. Mudar o texto exige nova aprovação e nova versão.

### 3.21 Saída de uma resolução humana e de um duplicado provável

Decisão tomada pelo responsável em 18-11-2026.

- **`Exact_Entity_Match` depois de uma resolução `MATCH`.** Fica `NO`. A coluna diz o resultado da verificação (REQ-ENT-006), e a verificação não encontrou correspondência exacta: foi um revisor que a confirmou. As linhas levam a nota "Entidade confirmada pelo revisor.", nos resultados e em `Notes_or_Flags`. A aba de destino é OUTLAYS e a confiança segue a regra normal, como diz 3.15.
- **Referência ao duplicado na exportação.** A nota diz o nome do ficheiro e a data de carregamento da factura anterior: "Possível duplicado de INV-001.pdf, carregada a 18-11-2026." O `Invoice_ID` não serve de referência, porque é igual nas duas cópias. Nos resultados, `possible_duplicate_of` dá o identificador da anterior. A data é a do relógio do servidor, em UTC.

---

## 4. Lacunas por resolver

Cada lacuna tem identificador, questão, porque importa, sugestão da equipa, quem responde e data-limite. As datas são relativas ao arranque do trabalho, D+n dias.

### L-01 · Formato real das facturas: nativo ou digitalizado

**Questão.** Os PDF de factura são gerados por sistema, com camada de texto, ou são digitalizações de papel?

**Porque importa.** É a lacuna que domina todas as outras. PDF nativo é extracção determinística com `pdfplumber`, com erro próximo de zero. Digitalização obriga a OCR ou a um modelo de visão, e nesse caso a extracção passa a ser a maior fonte de erro do pipeline, muito acima do mapeamento. Toda a conversa sobre precisão de matching é secundária se o texto de entrada vier errado.

**Sugestão.** Assumir PDF nativo nesta versão. Declarar a porta `OpticalCharacterRecognizer` sem implementação, e devolver um erro explícito, não um resultado silencioso, quando um PDF não tiver camada de texto extraível. A detecção é simples: se a extracção devolver menos de um número mínimo de caracteres por página, o ficheiro é tratado como digitalizado e recusado com motivo. O que **não** se pode fazer é aceitar o ficheiro, extrair pouco texto e codificar em cima disso.

**Responde:** avaliador do teste · **Até:** antes da primeira linha de código de extracção

**Estado em 18-11-2026.** As amostras respondem em parte. INV-001 a INV-010 são PDF nativos, INV-011 é uma digitalização sem texto, e INV-012 tem imagem e texto. Há, portanto, as duas coisas. Decisão por omissão aplicada: extracção de PDF nativo no modelo das amostras, e recusa dos digitalizados com `pdf_without_text_layer`, visível no estado do trabalho e na exportação. O OCR passa a uma spec própria. Fica em aberto a proporção de facturas digitalizadas, que decide se o OCR é necessário antes de produção.

---

### L-02 · As dez facturas de amostra não foram fornecidas

**Questão.** O enunciado refere "as 10 facturas de fornecedor de exemplo abaixo", mas o documento não contém nenhuma factura, imagem ou anexo.

**Porque importa.** Sem as amostras não há conjunto dourado, e sem conjunto dourado não há forma de medir a precisão nem de calibrar os limiares da secção 3.8. Os números do `README.md` seriam afirmações, não medições. Além disso, as amostras são o que revela a estrutura real do cabeçalho, a variedade das descrições e a proporção de facturas que caem em cada aba.

**Sugestão.** Pedir as amostras. Entretanto, construir um conjunto de facturas sintéticas que cubra deliberadamente os casos limite do enunciado: entidade exacta, entidade com `Lda.` em vez de `Limitada`, entidade sem hífen, empresa irmã de nome quase igual, companhia de navegação, cliente terceiro, cabeçalho ilegível, linha vaga, linha que casa com dois itens, e linha sem correspondência em cada uma das abas. Estas facturas sintéticas ficam em `tests/fixtures/` e são identificadas como sintéticas, nunca apresentadas como amostras reais.

**Responde:** avaliador do teste · **Até:** D+1

**Estado em 18-11-2026.** Chegaram 12 amostras, INV-001 a INV-012. Cobrem quase todos os casos limite do enunciado. Decisão aplicada em 3.18: as amostras ficam fora do repositório, e os resultados esperados ficam num ficheiro de configuração editável. Ficam em aberto se INV-001 a INV-010 são sintéticas e podem entrar no repositório, e a confirmação dos resultados esperados pela AMT.

---

### L-03 · Nome e identidade do ficheiro de catálogo

**Questão.** O enunciado indica `Master item catalog.xlsx` no cabeçalho e `Items (1).xlsx` na secção 1. São o mesmo ficheiro?

**Porque importa.** Trivial de resolver, caro de assumir errado. Se forem dois ficheiros com conteúdos diferentes, metade dos códigos atribuídos estarão errados sem que nada falhe visivelmente.

**Sugestão.** Assumir que é o mesmo ficheiro e tratar o nome como irrelevante: o catálogo é identificado pelo digest do conteúdo, como decidido em 3.9, não pelo nome. A aplicação aceita o caminho por configuração e valida a estrutura das duas abas no arranque, falhando com mensagem explícita se alguma estiver ausente.

**Responde:** avaliador do teste · **Até:** D+1

**Estado em 18-11-2026.** Resolvida. O ficheiro recebido chama-se `catalog.xlsx`, um terceiro nome, o que confirma que o nome é irrelevante e que a identificação pelo digest é a certa.

---

### L-04 · Lista das empresas irmãs e companhias de navegação

**Questão.** Quais são, por nome, as empresas irmãs da AMT, as companhias de navegação e os clientes recorrentes que podem aparecer na secção "Bill To"?

**Porque importa.** É a lacuna com maior impacto na correcção. A regra R4 manda recusar estritamente empresas irmãs, e uma empresa irmã de um transitário costuma ter nome quase idêntico, por exemplo um prefixo comum com sufixo diferente. Correspondência aproximada sozinha vai casar, e o encaminhamento inteiro fica errado. Esta é a diferença entre um pipeline que parece funcionar nas amostras e um que funciona em produção.

**Sugestão.** Construir a lista de exclusão como **dado de configuração**, em `config/entity_denylist.yaml`, avaliada antes de qualquer correspondência aproximada, por nome normalizado. Começar com as entidades que aparecerem nas amostras. Acrescentar uma regra adicional: se o nome normalizado da entidade facturada tiver uma distância pequena do nome da AMT mas **não** for igual depois de remover pontuação e sufixo societário, a factura é marcada como entidade ambígua e vai para revisão, em vez de ser encaminhada por adivinhação. Falso negativo custa uma revisão. Falso positivo custa uma reclassificação fiscal.

**Responde:** AMT, área de contabilidade · **Até:** D+3

**Estado em 18-11-2026.** INV-010 é facturada a "AMT - Empresa Irmã Sintética Limitada", com a morada da AMT e um NIF quase igual ao da AMT, que só difere nos últimos dígitos. Acrescentou-se o veto pelo NIF (3.15), com o NIF da AMT em configuração (`5419990000`, tirado das amostras e por confirmar). A lista de exclusão continua sem conteúdo.

---

### L-05 · Estrutura das abas OUTLAYS e OUTLAYSP

**Questão.** Que colunas existem além de `No.` (Coluna A) e da descrição? Qual é a coluna de descrição, e existe descrição em mais de um idioma, em colunas diferentes?

**Porque importa.** Define o índice de recuperação. Se houver descrição em português e em inglês em colunas separadas, ambas entram no índice e isso melhora a cobertura bilingue de forma muito mais barata do que qualquer prompt. Se houver grupo contabilístico, unidade ou taxa de imposto, esses campos ajudam a desempatar candidatos e devem entrar no contexto dado ao modelo.

**Sugestão.** Ler as duas abas sem pressupor nomes de coluna, inferir a coluna de descrição como a primeira coluna de texto com maior cardinalidade, e registar no arranque o mapeamento inferido, para que seja visível e corrigível por configuração. Nunca inferir em silêncio.

**Responde:** AMT · **Até:** D+3

**Estado em 18-11-2026.** Estrutura resolvida pelo ficheiro recebido (3.9). Continua em aberto o conteúdo de três pares cujas descrições PT e EN não dizem o mesmo: O00015 `Despesas` / `Storage fees`, O00027 `Pertence` / `Desconsolidation` e O00030 `Portagem` / `Airport Gate pass fee`. Também em aberto as descrições EN vazias de O00061 e O00063.

---

### L-06 · Linhas que não são serviços

**Questão.** As facturas contêm linhas de IVA, de arredondamento, de desconto, de taxa de câmbio ou de subtotal? Essas linhas devem ser codificadas, ignoradas, ou codificadas para um item próprio?

**Porque importa.** Se forem tratadas como serviços, o pipeline vai procurar no catálogo um item para "IVA 14%" e atribuir qualquer coisa com confiança artificialmente alta, porque o fuzzy vai encontrar alguma semelhança. É uma fonte de erro silencioso, que não aparece em nenhuma métrica.

**Sugestão.** Classificar o tipo de linha antes de mapear, de forma determinística, por padrão sobre a descrição normalizada e por posição na tabela: `service`, `tax`, `discount`, `subtotal`, `total`, `other`. Só `service` e `other` seguem para mapeamento. As restantes aparecem na saída com `Assigned_Item_No` vazio e `Notes_or_Flags` a indicar o tipo detectado, porque omiti-las da saída esconderia informação ao revisor. Confirmar a política com a contabilidade.

**Responde:** AMT, área de contabilidade · **Até:** D+5

**Estado em 18-11-2026.** A sugestão acima foi substituída pela decisão de 3.17. O tipo `other` e a sinalização das linhas que não são serviço foram retirados. Nas amostras, o IVA nunca aparece como linha da tabela. Continua em aberto se uma linha de IVA, desconto, arredondamento ou câmbio pode aparecer na tabela de uma factura real.

---

### L-07 · Autenticação e âmbito de acesso

**Questão.** O protótipo é usado por uma pessoa numa máquina, ou é exposto a uma equipa? Há perfis distintos entre quem carrega e quem revê?

**Porque importa.** Determina se o sistema precisa de identidade. Facturas de fornecedores contêm dados comerciais e financeiros de terceiros, e a revisão altera registos com impacto fiscal, pelo que "quem alterou" não é um campo decorativo.

**Sugestão.** Nesta versão, sem autenticação, a aplicação liga-se apenas a `127.0.0.1` e não é publicada em rede. O campo `reviewed_by` existe no esquema desde o início, preenchido com um identificador vindo de configuração, para que a introdução de autenticação não exija migração de dados nem alteração do trilho de auditoria. A ausência de autenticação fica declarada como **risco residual médio** no bloco de fecho de `03-seguranca.md`, não omitida.

**Responde:** AMT · **Até:** D+5

---

### L-08 · Ausência de correspondência em OUTLAYS

**Questão.** A regra de recurso `O00999` aplica-se apenas a OUTLAYSP, por R3. O que acontece quando uma factura é encaminhada para OUTLAYS e nenhuma descrição dessa aba se ajusta à linha?

**Porque importa.** O enunciado não define este caso, e ele vai acontecer. É a lacuna mais consequente do enunciado: deixada ao critério da implementação, produz silenciosamente um de três comportamentos muito diferentes, e dois deles são errados. Atribuir `O00999` viola R3. Atribuir o melhor candidato disponível, por fraco que seja, produz um código errado com aparência de código certo, que é exactamente o problema que o sistema existe para resolver.

**Sugestão.** Deixar `Assigned_Item_No` **vazio**, confiança `LOW`, e sinalização obrigatória para revisão humana com o motivo `no_match_in_outlays`. Uma lacuna é devolvida ao humano, nunca preenchida por omissão. Confirmar com o avaliador, porque a escolha aqui é visível na saída e revela como se interpretou a regra.

**Responde:** avaliador do teste · **Até:** D+3

**Estado em 18-11-2026.** A sugestão foi aplicada como decisão por omissão. Acrescentou-se a regra do item genérico (3.16): `O00052 Outras Despesas` pode ser escolhido, mas dá sempre `LOW` e sinalização. Pergunta acrescentada: `O00052` é o recurso pretendido para OUTLAYS?

---

### L-09 · Factura com mais do que uma entidade facturada

**Questão.** Pode uma factura ter secções facturadas a entidades diferentes, ou indicar a AMT como destinatário e um terceiro como pagador?

**Porque importa.** O passo 1 do enunciado assume uma entidade por factura. Se houver facturas mistas, o encaminhamento deixa de ser por factura e passa a ser por linha, o que altera o modelo de dados e a saída.

**Sugestão.** Assumir uma entidade por factura nesta versão. Se a extracção encontrar mais do que um candidato a entidade facturada na mesma factura, marcar como entidade ambígua e enviar a factura inteira para revisão, sem codificar. Não escolher o primeiro que aparece.

**Responde:** AMT · **Até:** D+5

**Estado em 18-11-2026.** Nenhuma amostra tem dois blocos de entidade facturada. INV-002 tem um bloco com uma linha "c/o", que é uma entidade com ao cuidado de, e não duas entidades (3.15).

---

### L-10 · Idioma e moeda

**Questão.** As facturas chegam em português e em inglês, por enunciado. Chegam também em outro idioma? Há mais do que uma moeda, e a moeda influencia a codificação?

**Porque importa.** O idioma afecta a normalização e a construção do índice de recuperação. A moeda, se influenciar a escolha de item, passa a ser entrada do mapeamento e não um campo decorativo.

**Sugestão.** Suportar português e inglês. Detectar o idioma da linha de forma determinística, por conjunto de palavras funcionais, apenas para efeitos de registo e de diagnóstico, não como entrada da decisão. Extrair a moeda e o valor para a saída e para a auditoria, mas **não** os usar na escolha de item até que alguém o confirme.

**Responde:** AMT · **Até:** D+5

**Estado em 18-11-2026.** As amostras têm duas moedas, AOA e USD, no formato `1,206.00`, e rótulos bilingues. Em INV-007 e INV-009, a percentagem de IVA da linha coincide com o grupo de IVA do item esperado (14% em Sonils, 7% em Hotel). Pode vir a ser um sinal de confiança, mas não é usado até ser confirmado (L-16).

---

### L-11 · Retenção dos dados

**Questão.** Durante quanto tempo ficam guardadas as facturas carregadas, o texto extraído e os registos de auditoria?

**Porque importa.** O sistema acumula ficheiros com dados comerciais de fornecedores e prompts que contêm esse conteúdo. Guardar indefinidamente é guardar dados de terceiros sem necessidade declarada.

**Sugestão.** Nesta versão: ficheiro original guardado enquanto o trabalho existir, texto extraído guardado para permitir reprocessamento sem novo carregamento, auditoria sem purga. Em produção, propor retenção de 24 meses para a auditoria, purga do ficheiro original após a codificação ser aceite, e exclusão do conteúdo da factura dos registos de log, que já é regra em `03-seguranca.md` SEC-15.

**Responde:** AMT, com apoio jurídico · **Até:** antes de qualquer implantação fora de máquina local

---

### L-12 · Custo por factura e orçamento do modelo

**Questão.** Existe limite de custo mensal para a utilização do modelo?

**Porque importa.** A 5.000 chamadas por mês, o custo é previsível e pequeno, mas tem de ser um número no `README.md` e não uma vaga tranquilidade. E se houver limite, isso é um requisito de desenho: muda a decisão sobre quando chamar o modelo e quando confiar apenas na recuperação determinística.

**Sugestão.** Medir o custo real por factura sobre o conjunto dourado e publicá-lo no `README.md`, com o número de tokens de entrada e de saída por factura. Acrescentar um contador de custo acumulado por trabalho na auditoria. Propor um limiar acima do qual as linhas com score de recuperação muito alto saltam a chamada ao modelo, como optimização futura e não como comportamento inicial, porque saltar o modelo sem medição é trocar correcção por custo às cegas.

**Responde:** AMT · **Até:** D+10

---

### L-13 · Aba de destino vazia em facturas com entidade ambígua

**Questão.** O formato de saída só admite `OUTLAYS` ou `OUTLAYSP` em `Target_Sheet`. Uma factura com entidade ambígua não tem aba de destino. O avaliador aceita a coluna vazia?

**Porque importa.** É um desvio visível ao formato de R6.

**Sugestão.** Coluna vazia, linhas sinalizadas, factura desbloqueada por resolução de entidade (3.15). Já aplicada.

**Responde:** avaliador do teste · **Até:** D+3

---

### L-14 · Notas de liquidação aduaneira da AGT

**Questão.** INV-012 é uma nota de liquidação da AGT. Não tem "Bill To", só "Declarant" (uma pessoa singular) e "Consignee". As linhas são direitos aduaneiros, e os números e datas usam outro formato. Estas notas entram no circuito de codificação?

**Porque importa.** Lidas pelo modelo de factura, produzem lixo. Classificadas como imposto, ficam sem código, quando os direitos aduaneiros são exactamente o que a AMT paga por conta do cliente.

**Sugestão.** Recusar com `unsupported_document_type` nesta versão. Já aplicada. Se entrarem no circuito, têm uma spec própria, com "Consignee" como entidade facturada e os direitos codificados em OUTLAYSP, provavelmente para `O00002 Alfândegas`.

**Responde:** AMT · **Até:** D+5

---

### L-15 · Notas de crédito e facturas reemitidas

**Questão.** As notas de crédito chegam pelo mesmo circuito? Como se distinguem de uma factura?

**Porque importa.** A detecção de duplicado provável (3.10) pode sinalizar uma nota de crédito legítima que reutiliza o número da factura.

**Sugestão.** Codificar e sinalizar com `possible_duplicate`, sem bloquear. Já aplicada.

**Responde:** AMT, área de contabilidade · **Até:** D+5

---

### L-16 · Percentagem de IVA como sinal de confiança

**Questão.** A coincidência entre a percentagem de IVA da linha e o grupo de IVA do item do catálogo é fiável?

**Porque importa.** Se for, é um sinal de confiança determinístico e barato, que confirma ou contradiz a escolha do modelo.

**Sugestão.** Guardar a percentagem e não a usar até haver confirmação.

**Responde:** AMT, área de contabilidade · **Até:** D+10

---

## 5. Registo de decisões por omissão

Preencher à medida que as datas-limite expiram.

| Lacuna | Data-limite | Resposta recebida | Decisão aplicada | Data |
|---|---|---|---|---|
| L-01 | antes da extracção | Parcial, pelas amostras: nativos e digitalizados | PDF nativo extraído, digitalizado recusado com `pdf_without_text_layer` (3.6) | 18-11-2026 |
| L-02 | D+1 | 12 amostras recebidas | Amostras fora do repositório, resultados esperados em configuração, por confirmar (3.18) | 18-11-2026 |
| L-03 | D+1 | Pelo ficheiro recebido | Catálogo identificado pelo digest. Resolvida | 18-11-2026 |
| L-04 | D+3 | | Lista vazia; veto pelo NIF; nome parecido sem igualdade é ambíguo (3.15) | 18-11-2026 |
| L-05 | D+3 | Estrutura, pelo ficheiro recebido | Colunas B (PT) e C (EN); pares divergentes por esclarecer (3.9) | 18-11-2026 |
| L-06 | D+5 | | Tipos `service`, `tax`, `discount`; resumo fora da saída (3.17) | 18-11-2026 |
| L-07 | D+5 | | | |
| L-08 | D+3 | | Código vazio, `LOW`, `no_match_in_outlays`; item genérico dá `LOW` (3.16) | 18-11-2026 |
| L-09 | D+5 | | Uma entidade por factura; "c/o" não conta (3.15) | 18-11-2026 |
| L-10 | D+5 | Parcial, pelas amostras: AOA e USD | Moeda e IVA registados, sem influência na escolha | 18-11-2026 |
| L-11 | pré-implantação | | | |
| L-12 | D+10 | | | |
| L-13 | D+3 | | `Target_Sheet` vazio (3.15) | 18-11-2026 |
| L-14 | D+5 | | Recusa com `unsupported_document_type` (3.6) | 18-11-2026 |
| L-15 | D+5 | | Duplicado provável sinalizado, sem bloqueio (3.10) | 18-11-2026 |
| L-16 | D+10 | | Percentagem de IVA guardada, não usada | 18-11-2026 |

---

## 6. O que mudaria para produção

Resumo das decisões que são deliberadamente de protótipo, com o caminho de evolução. Alimenta a secção "Production Readiness" do `README.md` exigida por R8.

| Decisão de protótipo | Em produção | Porquê não agora |
|---|---|---|
| SQLite com ficheiro local | PostgreSQL | O desenho já é portável. A mudança é de URL e migração de dados |
| Trabalhador em processo | `procrastinate` sobre PostgreSQL, ou Celery se o volume justificar | Não sobrevive a mais do que um processo de API |
| Sem autenticação, ligado a `127.0.0.1` | Servidor de identidade OpenID Connect, autorização por recurso | L-07 |
| Ficheiros em disco local | Armazenamento de objectos com URLs assinados e cifra por envelope | Sem réplica nem assinatura de acesso |
| Catálogo em memória, recarregado à mão | Catálogo versionado em tabela, com histórico e recarga por evento | Suficiente para um ficheiro que muda raramente |
| Sem limite de taxa real | Limite partilhado entre instâncias, em Redis ou Valkey | Um contador em memória deixa de funcionar com duas réplicas |
| Codificação apenas por carregamento manual | Ingestão por correio electrónico ou pasta vigiada, e escrita no Dynamics 365 Business Central pela sua API | Integração com o ERP está fora do âmbito do teste |
| Sem alerta | Métricas Prometheus e alerta sobre taxa de `LOW`, taxa de falha de extracção e custo acumulado | A primeira métrica a vigiar é a subida da taxa de revisão, que é o sinal de que o catálogo ou os fornecedores mudaram |
| PDF digitalizado recusado | OCR, depois de medir a proporção de facturas digitalizadas | L-01 |
| Notas de liquidação da AGT recusadas | Extracção própria, com "Consignee" como entidade facturada | L-14 |
| Limiares de confiança provisórios | Limiares calibrados e revistos periodicamente contra as correcções humanas acumuladas | Depende de L-02 |
