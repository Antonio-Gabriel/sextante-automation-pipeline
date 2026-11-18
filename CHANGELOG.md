# Registo de Alterações

Regista cada alteração à aplicação com o seu identificador, a alteração de que parte e a forma de a reverter. A obrigação de registar está no `CLAUDE.md`, na secção «Registo de alterações».

## Árvore

Cada alteração aparece por baixo daquela de que parte. A entrada mais recente de um ramo é o estado actual desse ramo.

```
CHG-0001  docs      Documentação inicial do projecto
├── CHG-0002  docs      Configuração dos skills de engenharia
└── CHG-0003  docs      Glossário e pontos em aberto da sessão de grilling
    └── CHG-0004  docs      Especificação do núcleo de codificação
        └── CHG-0005  docs      Tickets 01 a 13 e emenda pelas amostras
            └── CHG-0006  docs      Alinhamento dos documentos de desenho
                └── CHG-0007  security  Limite de itens enviados ao modelo
                    └── CHG-0008  infra     Repositório git
                        └── CHG-0009  feat      Arranque com catálogo validado
                            └── CHG-0010  fix       Correcções da revisão do ticket 01
                                └── CHG-0011  feat      Carregamento e codificação em segundo plano
                                    └── CHG-0012  fix       Correcções da revisão do ticket 02
                                        ├── CHG-0013  docs      Registo de alterações e a sua regra
                                        └── CHG-0014  infra     Graphify como memória do projecto
                                            └── CHG-0015  infra     Skill do graphify no projecto e correcção da CHG-0014
                                                └── CHG-0016  docs      Diagramas regenerados com o desenho actual
                                                    └── CHG-0017  feat      Verificação de entidade e encaminhamento para OUTLAYSP
                                                        └── CHG-0018  feat      Confiança, recurso e sinalização
                                                            └── CHG-0019  fix       Correcções da revisão dos tickets 03 e 04
                                                                └── CHG-0020  feat      Tipos de linha
                                                                    └── CHG-0021  feat      Exportação em CSV e XLSX
                                                                        └── CHG-0022  fix       Correcções da revisão dos tickets 05 e 06
                                                                            └── CHG-0023  feat      Trabalhador robusto e reprocessamento
                                                                                └── CHG-0024  feat      Revisão de linhas
                                                                                    └── CHG-0025  fix       Correcções da revisão dos tickets 07 e 08
                                                                                        └── CHG-0026  docs      Isenção do carregamento e reprocessamento só de falhas
                                                                                            └── CHG-0027  feat      Resolução de entidade e duplicado provável
                                                                                                └── CHG-0028  fix       Correcções da revisão dos tickets 09 e 10
                                                                                                    └── CHG-0029  improve   Saída da resolução humana e do duplicado provável
                                                                                                        └── CHG-0030  feat      Extracção de PDF nativo no modelo das amostras
                                                                                                            └── CHG-0031  feat      Conjunto dourado sem o modelo
                                                                                                                └── CHG-0032  fix       Correcções da revisão dos tickets 12 e 13
                                                                                                                    └── CHG-0033  docs      Histórico sem Co-Authored-By e hashes actualizados
                                                                                                                        └── CHG-0034  fix       Réplicas sem dados das amostras, XLSX recusado e padrão do conjunto dourado
                                                                                                                            └── CHG-0035  feat      Adaptador Claude do ItemClassifier e prompt v1
                                                                                                                                └── CHG-0036  feat      Medição manual dos códigos com o modelo real
                                                                                                                                    └── CHG-0037  fix       Correcções da revisão dos tickets 11 e 13
                                                                                                                                        └── CHG-0038  docs      Fornecedor e moeda no pedido ao modelo (REQ-MAP-005)
                                                                                                                                            └── CHG-0039  security  Repositório e histórico sem dados das amostras
                                                                                                                                                └── CHG-0040  infra     Catálogo no repositório, sem metadados pessoais
                                                                                                                                                    └── CHG-0041  improve   Modelo por omissão passa a Sonnet
                                                                                                                                                        └── CHG-0042  improve   Prompt v2 com cache de prompt
```

## Regras

1. **Quando registar.** Regista-se toda a alteração a:
   - código, testes ou migrações;
   - infraestrutura, dependências ou configuração da aplicação;
   - documentos que definem o comportamento da aplicação (`docs/`, `CLAUDE.md`, `GLOSSARY.md`, a spec e os tickets).
2. **Identificador.** `CHG-nnnn`, sequencial e nunca reutilizado.
3. **Alteração-pai.** É o último `CHG` do ramo em que se trabalhou. Alterações paralelas têm o mesmo pai.
4. **Imutabilidade.** Uma entrada nunca é reescrita nem apagada. Só os campos `Estado` e `Commit` podem ser actualizados.
5. **Reversão.** Uma reversão é uma entrada nova, do tipo `rollback`, cujo pai é a alteração revertida. A entrada revertida passa ao estado `revertida por CHG-nnnn`.
6. **Ordem.** As entradas ficam da mais recente para a mais antiga.
7. **Commit.** Uma alteração e a sua entrada entram no mesmo commit, com `Changelog: CHG-nnnn` na mensagem. Nesse momento o campo `Commit` fica `pendente`; o hash é preenchido no commit seguinte, como permite a regra 4.

### Tipos

| Tipo | Uso |
|---|---|
| `feat` | Funcionalidade nova |
| `improve` | Melhoria de funcionalidade existente |
| `fix` | Correcção de defeito |
| `security` | Controlo ou correcção de segurança |
| `test` | Apenas testes |
| `migration` | Esquema ou dados |
| `infra` | Contentores, dependências, configuração |
| `docs` | Documentos que definem o comportamento |
| `rollback` | Reversão de uma alteração anterior |

### Reversibilidade

| Valor | Significado |
|---|---|
| `total` | Reverter o commit repõe o estado anterior |
| `parcial` | Parte fica. O campo `Reversão` diz qual |
| `não` | Não se pode reverter. O campo `Reversão` diz a alternativa, por exemplo uma correcção posterior |

Três casos estão sempre limitados:

- **Auditoria.** Os registos de `audit_event` são só de inserção (SEC-04, REQ-AUD-002): nunca se libertam nem se alteram, e nenhuma reversão os pode apagar.
- **Migração que remove dados.** É, no máximo, `parcial`, salvo se o campo `Reversão` indicar uma salvaguarda da base de dados.
- **Pedido ao modelo.** Uma factura já enviada ao modelo não se "desenvia". Reverter o código não desfaz essa chamada.

### Modelo de entrada

```markdown
### CHG-nnnn · <título curto>

- **Data:** AAAA-MM-DD
- **Tipo:** feat
- **Pai:** CHG-nnnn
- **Estado:** activa | revertida por CHG-nnnn
- **Requisitos:** REQ-xxx-nnn, NFR-xxx-nnn, SEC-nn, D-n.n, L-nn, ou "nenhum"
- **Commit:** <hash> | pendente
- **Migração:** <revisão Alembic e revisão anterior>, ou "nenhuma"
- **Ficheiros:** <caminhos principais>
- **Reversibilidade:** total | parcial | não
- **Reversão:** <passos exactos, incluindo migração, índice e configuração>
- **Verificação:** <o que foi corrido e o que não foi verificado>

<Uma ou duas frases: o que mudou e porquê.>
```

## Alterações

### CHG-0042 · Prompt v2 com cache de prompt

- **Data:** 2026-11-18
- **Tipo:** improve
- **Pai:** CHG-0041
- **Estado:** activa
- **Requisitos:** REQ-MAP-004, REQ-MAP-005, REQ-AUD-003, REQ-AUD-004, SEC-14
- **Commit:** pendente
- **Migração:** `0008_model_call_cache_tokens` (colunas `cache_creation_input_tokens` e `cache_read_input_tokens` em `model_call`, a zero nas chamadas anteriores)
- **Ficheiros:**
  - `backend/src/sextante/prompts/item_choice_v2.txt` (novo, texto aprovado), `prompts/__init__.py` (versões)
  - `backend/src/sextante/matching/infrastructure/claude_classifier.py`, `tables.py`, `repository.py`, `matching/domain/item_choice.py`
  - `backend/migrations/versions/0008_model_call_cache_tokens.py`
  - testes: `tests/adapters/test_claude_classifier.py`, `tests/api/test_startup_database.py`, `tests/golden/`
  - `docs/00-decisoes-e-lacunas.md` (§3.22), `README.md`, ticket 11
- **Reversibilidade:** total
- **Reversão:** reverter o commit e descer a migração para `0007`. O prompt v1 continua no repositório.
- **Verificação:** 307 testes; `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos. `make golden-model` com `claude-sonnet-5-5` e o prompt v2: 12 linhas, 12 com o código esperado, 3 sinalizadas; 1 204 tokens de entrada sem cache, 4 436 escritos na cache e 17 744 lidos dela, contra 23 094 sem cache. O custo da entrada desce cerca de 63%.

**Aprovação.** O responsável aprovou o texto `item-choice-v2` e a passagem da lista de candidatos para a parte de sistema em cache, em 18-11-2026. Só o segundo parágrafo muda.

**Cache.** A lista de candidatos de uma aba é igual em todas as facturas que vão para essa aba. Passa a ser um segundo bloco de sistema, `<catalog_candidates>`, marcado com `cache_control`. A primeira chamada de cada aba escreve-a na cache, a 1,25 vezes o preço; as seguintes, nos cinco minutos, lêem-na a um décimo. O conteúdo da factura fica em `<invoice_data>`, na mensagem do utilizador, fora da parte em cache, e continua delimitado com `<` escapado. A lista de candidatos também.

**Registo.** Cada chamada guarda os tokens escritos e lidos da cache, que custam de forma diferente da entrada normal. O comando manual mostra-os.

### CHG-0041 · Modelo por omissão passa a Sonnet

- **Data:** 2026-11-18
- **Tipo:** improve
- **Pai:** CHG-0040
- **Estado:** activa
- **Requisitos:** REQ-MAP-005, REQ-AUD-003
- **Commit:** `920ad15`
- **Migração:** nenhuma
- **Ficheiros:** `backend/src/sextante/platform/settings.py`, `config/.env.example`, `README.md`, `docs/00-decisoes-e-lacunas.md` (§3.22), `backend/tests/adapters/test_claude_classifier.py`
- **Reversibilidade:** total
- **Reversão:** reverter o commit, ou definir `SEXTANTE_MODEL_ID=claude-opus-5-5`.
- **Verificação:** 306 testes. `make golden-model` com `claude-sonnet-5-5` e o prompt v1: 12 linhas, 12 com o código esperado, 3 sinalizadas, 23 094 tokens de entrada e 304 de saída, o mesmo resultado do Opus.

**Pedido do responsável.** O modelo por omissão passa de `claude-opus-5-5` a `claude-sonnet-5-5`, por custo: 2 USD por milhão de tokens de entrada e 10 de saída, contra 4 e 20. A configuração aprovada em §3.22 continua válida no Sonnet: sem parâmetros de amostragem, saída por esquema, esforço baixo e o recurso de servidor `"default"`, que é a forma que o Sonnet aceita. O modelo que respondeu continua registado em cada decisão.

### CHG-0040 · Catálogo no repositório, sem metadados pessoais

- **Data:** 2026-11-18
- **Tipo:** infra
- **Pai:** CHG-0039
- **Estado:** activa
- **Requisitos:** REQ-PLT-007, SEC-03
- **Commit:** `9dcf0d4`
- **Migração:** nenhuma
- **Ficheiros:** `sources/catalog.xlsx` (novo), `.gitignore`, `README.md`, `OPEN-ITEMS.md` (item 17)
- **Reversibilidade:** parcial
- **Reversão:** reverter o commit retira o ficheiro da versão, mas ele continua no histórico de um repositório já publicado.
- **Verificação:** as duas abas lidas com `openpyxl` são iguais às do original (45 e 21 linhas, cabeçalho incluído); o catálogo passa a validação de arranque (44 e 20 itens); nenhuma ocorrência do nome do autor nem do caminho do Windows no ficheiro.

**Pedido do responsável.** O catálogo entra no repositório, para que quem receber o projecto o possa testar. A cópia versionada não tem o autor, o último editor nem o caminho local do Windows que o original guardava nos metadados (item 17 de `OPEN-ITEMS.md`); os dados são os mesmos. O digest do catálogo muda com os metadados, por isso codificações antigas citam outro digest.

### CHG-0039 · Repositório e histórico sem dados das amostras

- **Data:** 2026-11-18
- **Tipo:** security
- **Pai:** CHG-0038
- **Estado:** activa
- **Requisitos:** D-3.18, SEC-03
- **Commit:** `dedb83a`
- **Migração:** nenhuma
- **Ficheiros:** 22 ficheiros versionados: tickets 02, 03, 12 e 13, `OPEN-ITEMS.md`, `CHANGELOG.md`, `docs/00` a `docs/02`, `config/.env.example`, testes e fixtures, e duas docstrings de exemplo do código
- **Reversibilidade:** não
- **Reversão:** a reescrita do histórico não se desfaz por um commit, e não deve: o objectivo é que nenhum commit publicado traga os dados.
- **Verificação:** 306 testes; nenhum dos valores das amostras em nenhum ficheiro versionado, nem em nenhum commit do ramo depois da reescrita. Os valores foram extraídos localmente das 12 amostras, para os procurar, e nenhum foi escrito no repositório.

**Motivo.** O repositório vai ser público. D-3.18 diz que nenhuma amostra, nem excerto de amostra, entra no repositório. Os documentos e o histórico citavam valores das amostras: nomes de fornecedores e clientes, NIFs, números de documento, moradas, descrições de linhas e observações, e os valores da nota da AGT.

**O que mudou.** Esses valores passam a valores sintéticos com a mesma estrutura, pelo mesmo mapa, na versão actual e em todos os commits do ramo, ficheiros e mensagens. O nome da AMT fica, porque é o cliente do enunciado. Os nomes dos itens do catálogo também ficam, porque o catálogo não é amostra. O NIF da AMT no repositório passa a sintético; o real fica só na configuração local.

**Hashes.** A reescrita muda os hashes de todos os commits. Os campos `Commit` e os hashes citados são actualizados no commit seguinte, como permite a regra 4.

### CHG-0038 · Fornecedor e moeda no pedido ao modelo (REQ-MAP-005)

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0037
- **Estado:** activa
- **Requisitos:** REQ-MAP-005, SEC-14
- **Commit:** `5a292e4`
- **Migração:** nenhuma
- **Ficheiros:** `docs/01-requisitos.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** o requisito passa a descrever o pedido que o adaptador já envia e que o prompt aprovado descreve; o código não muda.

**Decisão do responsável.** REQ-MAP-005 passa a listar o nome do fornecedor e a moeda entre o que o modelo recebe. Já iam no pedido, como dados delimitados, e o prompt aprovado descreve-os; o requisito não os mencionava.

### CHG-0037 · Correcções da revisão dos tickets 11 e 13

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0036
- **Estado:** activa
- **Requisitos:** REQ-MAP-005, REQ-MAP-007, REQ-PLT-003, NFR-TST-001
- **Commit:** `652577b`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/matching/application/line_coding.py` (novo: `LineCoder`), `encode_invoice.py`
  - `backend/src/sextante/matching/infrastructure/claude_classifier.py` (`create_model_client`, estados transitórios, mensagens)
  - `backend/src/sextante/main.py` (`coding_rules`, `require_generic_items_in_catalog`, classificador sem `None` intermédio), `platform/settings.py` (`ModelCallSettings`)
  - `backend/tests/golden/model_run.py`, `runner.py`; testes `tests/adapters/`, `tests/golden/`
  - tickets 11 e 13
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 306 testes; `mypy`, `ruff`, 8 contratos do `import-linter`, licenças, funções com 20 linhas ou menos. `make golden-model` contra a API real, com `claude-opus-5-5`: o pedido foi aceite e as respostas lidas; 12 linhas, 12 com o código esperado, 3 sinalizadas, 23 094 tokens de entrada e 304 de saída.

**Uma só lógica de codificação.** Decidir as linhas (chamada com repetições, validação, regra de confiança, sinalizações da factura) passa para `LineCoder`, sem persistência. `EncodeInvoice` guarda o que ele decide. O comando manual usa o mesmo `LineCoder`, as mesmas regras (`coding_rules`) e o mesmo cliente (`create_model_client`), em vez de uma cópia que já divergia nas repetições. Os parâmetros da chamada ficam em `ModelCallSettings`, partilhada pelas duas configurações.

**Adaptador.** 408 e 409 contam como transitórios, como 429 e 5xx. As mensagens de indisponível dizem o estado e a forma esperada. Um 400 não é repetido: o teste verifica um único pedido.

**Arranque.** O classificador deixa de passar por `None` e `replace`: o injectado ou o de Claude é passado directamente, e o cliente da API só é criado quando é preciso.

**Relatório manual.** O motivo de uma linha sem código (sem aba, modelo indisponível) deixa de ocupar o campo da confiança. Os tokens passam a ter um tipo próprio.

**Primeira medição real.** Contra a proposta ainda por confirmar pela AMT: 12 de 12 linhas com o código esperado; sinalizadas uma linha com o recurso O00999 e duas `MEDIUM` com candidatos próximos. Só para calibração, não para publicação (L-02).

### CHG-0036 · Medição manual dos códigos com o modelo real

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0035
- **Estado:** activa
- **Requisitos:** NFR-TST-001, D-3.18, L-02, SEC-15
- **Commit:** `0c1227e`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/tests/golden/model_run.py` (novo), `backend/tests/golden/runner.py`, `backend/Makefile` (`golden-model`)
  - `backend/src/sextante/matching/application/encode_invoice.py` (`item_choice_request` passa a público, para o comando usar o mesmo pedido)
  - testes: `tests/golden/test_golden_set.py`
  - ticket 13
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 304 testes, incluindo o relatório só com códigos e confiança; `mypy`, `ruff`, funções com 20 linhas ou menos. A primeira execução real foi recusada pela API por falta de crédito; o comando terminou com essa mensagem e código 2.

**Comando.** `make golden-model` codifica as amostras como a aplicação: o mesmo pedido, a mesma validação e a mesma regra de confiança. Reporta, por linha, o código esperado e o atribuído e a confiança, depois as linhas sinalizadas e os tokens gastos. Chama a API e custa dinheiro: só corre de propósito, fora de `make test` e da integração contínua. Um erro da API, como uma chave errada ou falta de crédito, termina com a mensagem da API e código 2. O ticket 13 fica fechado.

### CHG-0035 · Adaptador Claude do ItemClassifier e prompt v1

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0034
- **Estado:** activa
- **Requisitos:** REQ-MAP-005, REQ-MAP-007, REQ-AUD-003, REQ-AUD-004, REQ-PLT-003, SEC-14, SEC-15
- **Commit:** `d50659c`
- **Migração:** nenhuma
- **Dependência nova:** `anthropic` 1.17 (MIT), sobre `httpx2`, que já estava no projecto. `make licenses` passa.
- **Ficheiros:**
  - `backend/src/sextante/matching/infrastructure/claude_classifier.py` (novo); `unconfigured_classifier.py` retirado
  - `backend/src/sextante/prompts/` (novo: `item_choice_v1.txt`, o texto aprovado, e o carregador com a versão)
  - `backend/src/sextante/main.py`, `platform/settings.py` (`SEXTANTE_MODEL_ID`), `backend/pyproject.toml`
  - testes: `tests/adapters/test_claude_classifier.py` (novo), `tests/api/test_entity_routing.py`
  - `docs/00-decisoes-e-lacunas.md` (§3.22, e nota em §3.7), `docs/01-requisitos.md` (REQ-MAP-007), `docs/02-arquitectura.md`, spec, `config/.env.example`, `README.md`, tickets 11 e 14
- **Reversibilidade:** total
- **Reversão:** reverter o commit. Sem classificador, as facturas com linhas de serviço voltam a falhar sem código.
- **Verificação:** 304 testes. Os do adaptador respondem por um transporte HTTP em memória e verificam o pedido (prompt aprovado, esquema, esforço baixo, sem `temperature` nem ferramentas, recurso de servidor), os dados delimitados que uma descrição não consegue fechar, a leitura da resposta (índices, modelo, versão, tokens), as respostas inutilizáveis sem valor por omissão, e o mapeamento de 429, 5xx e falha de rede para indisponível. Nenhum teste chama a API. `mypy`, `ruff`, 8 contratos do `import-linter`, licenças.

**Aprovação.** O responsável aprovou a configuração da chamada e o texto do prompt `item-choice-v1` em 18-11-2026, tal como propostos. O registo está em §3.22 e no ticket 11.

**Configuração.** Sem `temperature`, que a API recusa em todos os modelos desde 21-10-2026. Resposta JSON restringida por `output_config.format`, porque os modelos actuais recusam ferramenta forçada. Modelo `SEXTANTE_MODEL_ID`, por omissão `claude-opus-5-5`. `effort` baixo. `max_tokens` de 2048 mais 64 por linha. Recurso de servidor numa recusa de segurança. O cliente não repete: a repetição é do caso de uso.

**Fronteira do modelo.** O conteúdo da factura vai como JSON dentro de `<invoice_data>`, com `<` escapado. O prompt pede só um índice ou `null` por linha e não repete nenhuma regra que vive em código. Uma resposta recusada, cortada ou ilegível não dá escolha nenhuma: todas as linhas ficam inválidas, `LOW` e sinalizadas. Uma entrada fora do esquema perde só a sua linha. O log guarda só o motivo de paragem ou o tipo de erro.

**Chave.** A chave do responsável foi usada uma vez, à mão, só pelo ambiente. Não está em nenhum ficheiro.

### CHG-0034 · Réplicas sem dados das amostras, XLSX recusado e padrão do conjunto dourado

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0033
- **Estado:** activa
- **Requisitos:** REQ-ING-001, REQ-ING-009, NFR-TST-001, D-3.6, D-3.18
- **Commit:** `64bfa67`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/tests/fixtures/synthetic_invoices.py` e os testes que usam as suas réplicas; `tests/domain/test_entity_check.py`, `test_export_rules.py`, `test_lexical_scoring.py`, `test_line_type.py`, `tests/api/test_startup_logging.py`
  - `backend/src/sextante/ingestion/` (motivo de recusa do XLSX), `platform/user_messages.py`, exemplos de docstrings em `platform/` e `export/domain/`
  - `docs/00-decisoes-e-lacunas.md` (§3.6), `docs/04-padroes-de-codigo.md` (§3.6 e comandos), ticket 12
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 290 testes; nenhum nome de empresa, NIF, número de documento ou descrição das amostras nos testes nem nos exemplos do código; `mypy`, `ruff`, 8 contratos do `import-linter`.

**Réplicas.** As réplicas dos tickets 02 a 10 usavam valores das amostras reais: nomes de fornecedores e clientes, NIFs, números de factura, descrições e moradas. Passam a valores inventados, com a mesma estrutura. A fixture `taag_air_ticket_to_amt` passa a `air_ticket_to_amt`. Os valores antigos continuam no histórico, por decisão do responsável.

**XLSX.** É recusado com `unsupported_document_type`, porque REQ-ING-001 manda um XLSX para a recusa de REQ-ING-009. O motivo `extractor_not_configured` deixou de ter uso e foi retirado.

**Conjunto dourado em 04.** O padrão de código dizia que `make golden` imprime precisão por aba, distribuição de confiança e taxa de sinalização. Passa a dizer o que §3.18 decidiu: as etapas determinísticas, sem o modelo. As medidas que precisam do modelo ficam para o comando manual, publicadas só depois da confirmação da AMT.

### CHG-0033 · Histórico sem Co-Authored-By e hashes actualizados

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0032
- **Estado:** activa
- **Requisitos:** nenhum
- **Commit:** `8124617`
- **Migração:** nenhuma
- **Ficheiros:** `CHANGELOG.md`, tickets 01 e 02 (hashes citados)
- **Reversibilidade:** não
- **Reversão:** a reescrita do histórico não se desfaz por um commit. As mensagens antigas só existem enquanto o ramo de segurança `backup/before-strip-coauthor` e `refs/original` não forem apagados.
- **Verificação:** 35 commits reescritos com `git filter-branch --msg-filter`; nenhum tem a linha `Co-Authored-By`; a árvore final é idêntica à de antes (`git diff` vazio); os assuntos dos commits antigos e novos coincidem um a um.

**Pedido do responsável.** Retirar a linha `Co-Authored-By` de todos os commits e nunca mais a acrescentar. A reescrita mudou todos os hashes. Os campos `Commit` das entradas, e os hashes citados nos tickets 01 e 02, foram actualizados para os novos, o que a regra 4 permite. O texto de CHG-0032 cita o hash novo do commit de CHG-0030.

### CHG-0032 · Correcções da revisão dos tickets 12 e 13

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0031
- **Estado:** activa
- **Requisitos:** REQ-ING-002, REQ-ING-003, NFR-TST-001, D-3.18, SEC-15, SEC-20
- **Commit:** `4fcd0e1`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/ingestion/` (extractor, leitor do layout, `missing_fields`, contratos), `worker.py`, `platform/settings.py`
  - `backend/tests/golden/runner.py` e `expected_results.yaml` (movidos de `src/sextante/golden_set.py` e `config/golden_expected.yaml`); `backend/scripts/golden.py` retirado; `backend/Makefile`
  - testes: `tests/fixtures/synthetic_pdf.py`, `tests/extraction/`, `tests/api/test_pdf_ingestion.py`, `tests/golden/`
  - `README.md`, `config/.env.example`, tickets 12 e 13
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 290 testes. O teste da página digitalizada falha com a regra antiga, a da média. `make golden` sobre as 12 amostras, localmente: 12 sem divergências. `mypy`, `ruff`, 8 contratos do `import-linter`, `make licenses` (inclui `pdfplumber`, MIT pelo classificador do pacote, que não preenche o campo `License`), funções com 20 linhas ou menos.

**Excertos de amostras.** As réplicas sintéticas de CHG-0030 traziam valores tirados das amostras reais: números de bilhete, de contentor e de processo, NIFs, nomes de clientes e descrições. Foram substituídos por valores inventados, que mantêm as particularidades: quebra a meio da palavra, quebra num espaço, número com espaço, nome longo na faixa de topo. Os valores antigos continuam no histórico do commit `a444f0a`.

**Texto por página.** O mínimo de caracteres vale para cada página, e não para a média do ficheiro. Uma página digitalizada no meio de páginas nativas recusa o PDF.

**Campos ausentes.** Além do log, ficam na auditoria da factura (`extraction_fields_missing`), só pelo nome. A função que os lista é partilhada pelo extractor, pelo trabalhador e pelo conjunto dourado.

**Conjunto dourado.**
- Passa para `backend/tests/golden/`, como 02 §2.4 o coloca; `make golden` corre `python -m tests.golden.runner`.
- A variável é `SEXTANTE_GOLDEN_SAMPLES_PATH`, como 02 a documenta.
- Mede também os campos que a extracção não encontrou, pelo nome.
- As variáveis são validadas como as da aplicação: um valor inválido, incluindo um mínimo de texto igual a 0, termina com código 2 e o nome da variável.

**Robustez.** Os caracteres da descrição são indexados por altura uma só vez, em vez de percorridos em cada linha da tabela. Um PDF ilegível tem teste do motivo exacto.

### CHG-0031 · Conjunto dourado sem o modelo

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0030
- **Estado:** activa
- **Requisitos:** NFR-TST-001, D-3.18, L-02, SEC-15
- **Commit:** `78e01e1`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/golden_set.py` (novo), `backend/scripts/golden.py`, `backend/Makefile`
  - `config/golden_expected.yaml` (novo), `config/.env.example`
  - testes: `tests/golden/test_golden_set.py` (novo)
  - `README.md`, ticket 13
- **Reversibilidade:** total
- **Reversão:** reverter o commit. `make golden` volta a dizer que não está implementado.
- **Verificação:** 285 testes, incluindo o conjunto dourado sobre amostras sintéticas, uma divergência que falha com o nome do campo, a mensagem sem a pasta das amostras, e um relatório sem texto de amostra. Corrido localmente sobre as 12 amostras: 12 sem divergências. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Medição.** `make golden` lê as amostras de `SEXTANTE_GOLDEN_SAMPLES_DIR` e mede, sem chamar o modelo, extracção, entidade, aba de destino, número e tipos de linha, e recusas. Falha quando alguma diverge. Sem a variável, termina com uma mensagem clara.

**Resultados esperados.** `config/golden_expected.yaml` tem a proposta do ticket, por confirmar pela AMT. As linhas são identificadas pela posição, e não pela descrição, para que nenhum excerto de amostra entre no repositório. O relatório tem só identificadores, nomes de campo e valores de conjuntos fechados.

**Por fazer.** O comando manual que mede os códigos de item com o modelo real depende do adaptador do ticket 11.

### CHG-0030 · Extracção de PDF nativo no modelo das amostras

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0029
- **Estado:** activa
- **Requisitos:** REQ-ING-001, REQ-ING-002, REQ-ING-003, REQ-ING-004, REQ-ING-005, REQ-ING-006, REQ-ING-008, REQ-ING-009, D-3.6, L-01, L-14, SEC-16
- **Commit:** `a444f0a`
- **Migração:** nenhuma
- **Dependência nova:** `pdfplumber` 0.11 (MIT), com `pdfminer.six` (MIT), `pypdfium2` (BSD-3-Clause ou Apache-2.0) e `Pillow` (MIT-CMU). `make licenses` passa.
- **Ficheiros:**
  - `backend/src/sextante/ingestion/infrastructure/pdf_invoice_extractor.py` e `model_invoice_layout.py` (novos); `unconfigured_extractor.py` retirado
  - `backend/src/sextante/main.py`, `platform/settings.py` (`pdf_min_chars_per_page`), `platform/limits.py` (`MAX_PDF_PAGES`), `platform/user_messages.py`, `ingestion/domain/model.py`
  - `backend/pyproject.toml`
  - testes: `tests/extraction/test_pdf_extractor.py`, `tests/api/test_pdf_ingestion.py`, `tests/fixtures/synthetic_pdf.py` (novos)
  - `README.md`, `config/.env.example`, ticket 12
- **Reversibilidade:** total
- **Reversão:** reverter o commit. O extractor volta a recusar todo o documento com `extractor_not_configured`.
- **Verificação:** 285 testes. As réplicas sintéticas reproduzem as quatro particularidades; extracção pela porta `InvoiceExtractor` e ponta a ponta pela API; recusas de digitalizado, de documento fora do modelo e de PDF ilegível. As 12 amostras, lidas localmente fora do repositório, dão o que a proposta do conjunto dourado espera. `mypy`, `ruff`, 8 contratos do `import-linter`, licenças, funções com 20 linhas ou menos.

**Extracção.** O layout é lido pelas coordenadas das palavras. O fornecedor é a letra maior da faixa de topo, mesmo quando corre por baixo de "INVOICE / FACTURA". FROM e BILL TO separam-se pelo x do rótulo "BILL TO". As linhas "c/o" e "a/c" ficam como "ao cuidado de", e cada bloco tem o seu NIF. O número da factura pode ter espaço ("FT 2026/0001").

**Linhas.** Cada valor vai para a coluna cujo título termina mais perto, porque os valores estão alinhados à direita. Uma linha de continuação junta-se pelos caracteres em bruto: com espaço quando a quebra caiu num espaço, sem espaço quando caiu a meio da palavra. Os valores são lidos no formato `1,206.00`, e o IVA em `14%`. Subtotal, IVA e total ficam como linhas de resumo, mesmo com o total colado ao rótulo.

**Recusas.** Um PDF com menos caracteres por página do que `SEXTANTE_PDF_MIN_CHARS_PER_PAGE` (100 por omissão) é `pdf_without_text_layer`. Um PDF sem os rótulos do modelo, com mais de 20 páginas, ou ilegível, é `unsupported_document_type`. XLSX continua por ler nesta versão (D-3.6) e é recusado com `extractor_not_configured`, agora com um texto que o diz.

**Campos ausentes.** Ficam vazios e são registados no log só pelo nome (`extraction_fields_missing`), nunca com texto da factura.

### CHG-0029 · Saída da resolução humana e do duplicado provável

- **Data:** 2026-11-18
- **Tipo:** improve
- **Pai:** CHG-0028
- **Estado:** activa
- **Requisitos:** REQ-ENT-006, REQ-ING-011, REQ-REV-006, REQ-EXP-004
- **Commit:** `58f99b5`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/matching/domain/entity_check.py` e contratos (`exact_entity_match_label` com o motivo, `entity_notes`)
  - `backend/src/sextante/worker.py` (motivo `reviewer_resolution` no cabeçalho)
  - `backend/src/sextante/ingestion/` (motivo da entidade e factura anterior nas leituras)
  - `backend/src/sextante/export/application/build_job_export.py`, `review/application/list_job_results.py`, `platform/user_messages.py`
  - testes: `test_entity_resolution.py`, `test_possible_duplicate.py`
  - `docs/00-decisoes-e-lacunas.md` (§3.21), tickets 09 e 10
- **Reversibilidade:** total
- **Reversão:** reverter o commit. As facturas resolvidas antes desta alteração têm motivo vazio no cabeçalho e continuam a mostrar `YES`.
- **Verificação:** 262 testes, incluindo `Exact_Entity_Match` `NO` com a nota do revisor nos resultados e na exportação, e a nota do duplicado com o ficheiro e a data da anterior; `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Resolução humana.** Uma resolução `MATCH` grava no cabeçalho o motivo `reviewer_resolution`. `Exact_Entity_Match` fica `NO`, porque a verificação não encontrou correspondência exacta, e as linhas levam a nota "Entidade confirmada pelo revisor.".

**Duplicado provável.** Na exportação, a sinalização diz "Possível duplicado de <ficheiro>, carregada a <dd-mm-aaaa>.", com o ficheiro e a data da factura anterior.

### CHG-0028 · Correcções da revisão dos tickets 09 e 10

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0027
- **Estado:** activa
- **Requisitos:** REQ-REV-006, REQ-ING-011, REQ-CNF-001, REQ-AUD-002, SEC-19
- **Commit:** `eedb6dd`
- **Migração:** `0007` alterada antes de sair deste ramo: índice parcial também com condição para PostgreSQL, e descida sem trabalho manual
- **Ficheiros:**
  - `backend/src/sextante/platform/insert_if_absent.py` (novo), `idempotency.py`
  - `backend/src/sextante/ingestion/` (porta da resolução, mensagens de erro, duplicado gravado uma vez)
  - `backend/src/sextante/worker.py`, `matching/infrastructure/tables.py`, migração 0007
  - testes: `test_entity_resolution.py`, `test_possible_duplicate.py`
  - spec (tipo de auditoria `possible_duplicate_detected`), ticket 14
- **Reversibilidade:** total
- **Reversão:** reverter o commit. A migração 0007 volta à forma de CHG-0027.
- **Verificação:** 261 testes. O teste da auditoria única falha sem a correcção. A descida da 0007 é testada com codificações substituídas presentes. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**SQL portável.** A reserva da chave de idempotência e a gravação da resolução deixam de usar `INSERT OR IGNORE`, que só existe em SQLite (02 §5), e passam a `INSERT ... SELECT ... WHERE NOT EXISTS`. O índice único parcial de `encoded_line` declara a condição para SQLite e para PostgreSQL.

**Migração 0007.** A descida apaga primeiro as codificações substituídas, e as suas sinalizações e revisões, porque a restrição da 0006 só admite uma por linha. O histórico fica em `audit_event`. A Reversão de CHG-0027 deixa de exigir trabalho manual.

**Duplicado.** `possible_duplicate_detected` é gravado uma só vez, mesmo quando a factura é codificada de novo depois de uma resolução. O tipo fica declarado na spec.

**Resolução.** Uma resolução repetida e uma factura não ambígua têm mensagens de erro distintas, cada uma com a condição que falhou. A resolução tem uma porta própria, que estende a do reprocessamento. Um teste prova que uma factura resolvida chega a `HIGH` sem sinalização.

**Pendente para o ticket 14.** `lexical_score` não está ligado a uma codificação. Recodificar uma linha que já tem scores falharia na chave primária. Hoje não acontece, porque a factura ambígua não grava scores.

### CHG-0027 · Resolução de entidade e duplicado provável

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0026
- **Estado:** activa
- **Requisitos:** REQ-REV-006, REQ-ING-011, REQ-REV-004, REQ-AUD-002, SEC-08, SEC-19, D-3.10, D-3.15
- **Commit:** `17bcc08`
- **Migração:** `0007_entity_resolution_and_duplicates` (tabela `entity_resolution`; `encoded_line.superseded_at` com índice único parcial no lugar da restrição única; `invoice_header.supplier_key` e `possible_duplicate_of`, com índice não único sobre fornecedor e número)
- **Ficheiros:**
  - `backend/src/sextante/ingestion/` (caso de uso `ResolveEntity`, rota, repositório, tabelas)
  - `backend/src/sextante/matching/` (codificações substituídas, sinalização da factura inteira)
  - `backend/src/sextante/worker.py`, `main.py`
  - `backend/src/sextante/platform/supplier_key.py` (novo, partilhado com a exportação), `limits.py`, `user_messages.py`
  - `backend/src/sextante/review/` (resultados com `possible_duplicate_of`)
  - testes: `test_entity_resolution.py`, `test_possible_duplicate.py` (novos), harness e fixtures
  - `README.md`, tickets 09 e 10
- **Reversibilidade:** parcial
- **Reversão:** reverter o commit e descer a migração para `0006`. A descida repõe a restrição única em `encoded_line`, e falha se houver codificações substituídas: essas têm de ser retiradas à mão primeiro. As resoluções gravadas perdem-se com a tabela; os eventos `entity_resolved` e `possible_duplicate_detected` ficam em `audit_event`.
- **Verificação:** 258 testes, incluindo resolução `MATCH` para OUTLAYS e `NO_MATCH` para OUTLAYSP com `O00999`, auditoria com o veredicto anterior e o novo, codificação anterior guardada como substituída, recusa de factura não ambígua, resolução repetida que codifica uma só vez, contrato da nota, lista de exclusão inalterada, duplicado sinalizado com referência, mesmo digest sem sinalização, factura sem número e outro fornecedor com o mesmo número; migração verificada a subir, descer e subir; `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Resolução de entidade.** `POST /api/invoices/{id}/entity-resolution` aceita `MATCH` ou `NO_MATCH` e uma nota obrigatória de 500 caracteres no máximo, com `Idempotency-Key`. Só uma factura `AMBIGUOUS` por resolver é aceite. A resolução fica em `entity_resolution`, gera `entity_resolved` com o autor configurado e põe a factura na fila. O trabalhador usa a resolução em vez da verificação, e as linhas seguem a regra normal de confiança. A lista de exclusão não muda.

**Codificação substituída.** As linhas da factura ambígua já tinham um registo sem código. A nova codificação marca-o como substituído (`superseded_at`) em vez de o sobrescrever; leituras, revisão, candidatos e exportação mostram só a codificação em vigor.

**Duplicado provável.** Uma factura com o mesmo fornecedor (NIF, ou nome normalizado) e o mesmo número de outra carregada antes, com outro digest, é codificada e todas as linhas ficam com `possible_duplicate`. Os resultados indicam a anterior em `possible_duplicate_of`. Sem número nunca é duplicado; o mesmo ficheiro continua a devolver o trabalho existente.

### CHG-0026 · Isenção do carregamento e reprocessamento só de falhas

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0025
- **Estado:** activa
- **Requisitos:** SEC-19, NFR-REL-002, REQ-ING-007
- **Commit:** `7844846`
- **Migração:** nenhuma
- **Ficheiros:**
  - `docs/00-decisoes-e-lacunas.md` (§3.19, §3.20)
  - `docs/03-seguranca.md` (SEC-19), `docs/02-arquitectura.md` (§6)
  - `.scratch/nucleo-codificacao/issues/14-recodificacao-com-historico.md` (novo), tickets 07 e 08
- **Reversibilidade:** total
- **Reversão:** reverter o commit. O código não muda.
- **Verificação:** decisões tomadas pelo responsável em 18-11-2026; o código já se comporta assim (CHG-0023, CHG-0024).

**Carregamento.** Fica isento de `Idempotency-Key`, por ser idempotente pelo digest do conteúdo. A isenção fica escrita em SEC-19 e na arquitectura, e não se estende a outras escritas.

**Reprocessamento.** Nesta versão aceita só facturas com falha. Recodificar uma factura já codificada, com histórico, passa a ticket próprio (14), bloqueado pelo ticket 11.

### CHG-0025 · Correcções da revisão dos tickets 07 e 08

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0024
- **Estado:** activa
- **Requisitos:** SEC-19, REQ-REV-003, REQ-REV-004, REQ-AUD-004
- **Commit:** `47e4c6e`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/platform/idempotency.py`, `idempotent_route.py`, `http_params.py` (novo), `limits.py`
  - `backend/src/sextante/review/` (auditoria, docstrings, mensagens de erro, progresso com tokens por factura)
  - `backend/src/sextante/matching/` (tokens por factura), rotas de `ingestion` e `export`, `main.py`
  - testes: `test_idempotency.py` (novo), `test_line_review.py`, `test_worker_resilience.py`, contratos
  - `README.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit. O esquema não mudou.
- **Verificação:** 243 testes. O teste de concorrência falha contra uma versão que verifica e depois escreve (`IntegrityError`) e passa com a reserva como primeira escrita. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Idempotência.** A reserva da chave é a primeira escrita da transacção (`INSERT OR IGNORE`). Um pedido simultâneo com a mesma chave espera pelo primeiro e recebe a resposta guardada, nunca um 500. A purga das respostas com mais de 24 horas passa para uma tarefa periódica, de hora a hora, como SEC-19 pede, em vez de correr dentro de cada escrita. O código de estado guardado é o que se devolve na repetição. Um pedido recusado não guarda nada, e a mesma chave pode ser reenviada. Os erros de chave e de item fora da aba têm estado explícito.

**Auditoria.** `line_accepted` e `line_corrected` registam o valor anterior e o novo do item, do estado de revisão e da nota (REQ-REV-004).

**Tokens.** `GET /api/jobs/{id}` mostra os tokens de cada factura, além do total (ticket 07).

**Normas.** Exemplos e `Raises` por erro nas docstrings da revisão. Mensagens de erro com o valor e a forma esperada. O limite da nota vai para `platform/limits.py`. O parâmetro de identificador fica num só sítio, o que também aplica o padrão ao `job_id` dos resultados, que não o tinha. Os contratos de entrada da revisão aparam espaços (SEC-08).

### CHG-0024 · Revisão de linhas

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0023
- **Estado:** activa
- **Requisitos:** REQ-REV-001, REQ-REV-002, REQ-REV-003, REQ-REV-004, REQ-REV-005, REQ-REV-007, REQ-EXP-004, SEC-08, SEC-18, SEC-19
- **Commit:** `040a42c`
- **Migração:** `0006_review_and_idempotency` (tabelas `line_review` e `idempotency_record`)
- **Ficheiros:**
  - `backend/src/sextante/review/` (domínio, casos de uso, repositório, rotas e contratos)
  - `backend/src/sextante/platform/idempotency.py`, `idempotent_route.py`, `audit.py`, `settings.py`, `user_messages.py`
  - `backend/src/sextante/matching/` (leitura de uma linha codificada e dos candidatos)
  - `backend/src/sextante/ingestion/` (linhas por factura, pertença de uma linha, reprocessamento na transacção da chave)
  - `backend/src/sextante/export/application/build_job_export.py`, `main.py`
  - `backend/migrations/versions/0006_review_and_idempotency.py`
  - `README.md`, `config/.env.example`, tickets 06 e 08
- **Reversibilidade:** parcial
- **Reversão:** reverter o commit e descer a migração para `0005`. As revisões gravadas em `line_review` perdem-se com a tabela; os eventos `line_accepted` e `line_corrected` ficam em `audit_event`, que é só de inserção.
- **Verificação:** 240 testes, incluindo correcção na aba, recusas (outra aba, código mal formado, campos de controlo, nota longa, linha sem aba), aceitação só de linha pendente, repetição e reutilização da chave, filtros, candidatos e reflexo na exportação; `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Revisão.** `PATCH /api/encoded-lines/{id}` corrige o código com um item da aba de destino da linha, validado no servidor. `POST /api/encoded-lines/{id}/accept` passa uma linha `pending` a `accepted`. As duas aceitam uma nota de 500 caracteres no máximo, recusam campos extra e são recusadas para uma linha sem aba de destino.

**Registo.** O estado de revisão fica em `line_review`, à parte de `encoded_line`, que nunca é sobrescrito. Cada acção gera `line_accepted` ou `line_corrected` em `audit_event`, com o valor anterior, o novo, o autor (`SEXTANTE_REVIEWER_ID`, nova variável obrigatória) e o momento.

**Idempotência.** `POST` e `PATCH` de revisão e o reprocessamento exigem `Idempotency-Key`. A chave é registada na mesma transacção da acção; a mesma chave repete a resposta, e com outro corpo é recusada. As respostas guardadas duram 24 horas. O carregamento fica isento: o digest do conteúdo já o torna idempotente.

**Resultados e exportação.** Os resultados mostram os valores em vigor e filtram por confiança, aba, sinalização e factura, antes da paginação. A exportação usa os mesmos valores, e a nota de revisão entra em `Notes_or_Flags`.

### CHG-0023 · Trabalhador robusto e reprocessamento

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0022
- **Estado:** activa
- **Requisitos:** REQ-PLT-001, REQ-PLT-002, REQ-PLT-003, REQ-AUD-004, NFR-REL-001, NFR-REL-002, L-12
- **Commit:** `14c0b15`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/platform/retry.py`
  - `backend/src/sextante/ingestion/application/reprocess_invoice.py`, repositório e rotas
  - `backend/src/sextante/matching/` (`ItemClassifierUnavailableError`, `TokenUsageReader`)
  - `backend/src/sextante/review/application/read_job_progress.py`
  - `backend/src/sextante/worker.py`, `main.py`, `platform/settings.py`
  - `README.md`, `config/.env.example`
- **Reversibilidade:** total
- **Reversão:** reverter o commit. O esquema não mudou. As facturas reabertas por um reprocessamento ficam no estado em que estiverem.
- **Verificação:** 217 testes, incluindo repetições com espera registada, falha permanente sem repetição, reprocessamento sem segunda extracção e tokens por trabalho; `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Repetições.** Só o modelo indisponível (`ItemClassifierUnavailableError`) é repetido, com recuo exponencial (1 s, 2 s, …). O número de tentativas é configurável, 3 por omissão. Qualquer outra falha é final, e uma resposta inválida nunca é repetida.

**Falhas.** Uma factura que falha fica `failed`, com o motivo, e o trabalho continua.

**Reprocessamento.** `POST /api/invoices/{id}/reprocess` volta a pôr na fila uma factura `failed`. O trabalho é reaberto e a factura é codificada a partir do texto guardado, sem nova extracção. Pedir duas vezes põe-na na fila uma só vez.

**Estado do trabalho.** `GET /api/jobs/{id}` mostra as facturas por estado e no total, e os tokens gastos.

### CHG-0022 · Correcções da revisão dos tickets 05 e 06

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0021
- **Estado:** activa
- **Requisitos:** REQ-ING-006, REQ-EXP-003, REQ-EXP-006, REQ-EXP-007, SEC-17, D-3.17
- **Commit:** 9e2d8e0
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/ingestion/domain/line_type.py`
  - `backend/src/sextante/export/` (porta `SpreadsheetWriter`, caso de uso `ExportJob`)
  - `backend/src/sextante/platform/text_normalization.py` (`digits_only`)
  - `backend/src/sextante/matching/domain/entity_check.py` (`exact_entity_match_label`)
  - `backend/pyproject.toml` (contrato que proíbe `export.api` de chegar à infraestrutura)
  - os tickets 05 e 06
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:**
  - Feito:
    - 211 testes, incluindo 25 casos da classificação de linhas;
    - a neutralização nas nove colunas;
    - a cobertura das mensagens de recusa;
    - `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.
  - Não verificado: o reflexo de uma correcção na exportação, que espera pelo ticket 08.

Resolve os achados da revisão dos tickets 05 e 06.

**Spec:**

- **Classificação das linhas.** Uma linha só é IVA, ou desconto, quando nomeia o IVA ou o desconto e todas as suas palavras pertencem a esse vocabulário. Passam a ser IVA "Valor do IVA", "14% IVA" e "I.V.A.". Passam a ser descontos "Descontos" e "Desc.". "Vat handling fee" e "(isento de IVA)" ficam como serviços.
- **`Invoice_ID`.** Um número só com espaços passa a dar lugar ao digest.
- **Deferições declaradas no ticket 06.** O reflexo de uma correcção espera pelo ticket 08, e os identificadores são calculados na exportação.

**Padrões:**

- A rota de exportação passa a usar só a camada de aplicação, que escreve através de uma porta. O contrato do `import-linter` passa a cobri-la.
- Os dígitos do NIF e o `Exact_Entity_Match` passam a viver num só sítio cada.
- As mensagens de recusa saem de um mapa com valor por omissão, testado contra todos os motivos.
- O tipo de linha, a nota e o estado da factura passam a ter tipos com nome.
- O JSON da entidade passa a ser lido uma só vez.

### CHG-0021 · Exportação em CSV e XLSX

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0020
- **Estado:** activa
- **Requisitos:** REQ-EXP-001 a REQ-EXP-007, SEC-16, SEC-17, R6, L-13
- **Commit:** c689698
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/export/` (módulo novo)
  - `backend/src/sextante/ingestion/` (leitor publicado `InvoiceExportReader`)
  - `backend/src/sextante/platform/settings.py`, `limits.py`, `user_messages.py`
  - `backend/src/sextante/main.py`, `backend/pyproject.toml` (contrato de camadas do `export`)
  - `README.md`, `config/.env.example`
- **Reversibilidade:** total
- **Reversão:** reverter o commit. O esquema não mudou.
- **Verificação:**
  - Feito:
    - 195 testes, incluindo a neutralização em CSV e XLSX, o separador `;` com aspas, e a exportação depois de reiniciar a aplicação;
    - `mypy`, `ruff`, 8 contratos do `import-linter`;
    - exportação no servidor real.
  - Não verificado: abrir os ficheiros no Excel em configuração portuguesa.

`GET /api/exports/{job_id}?format=csv|xlsx` exporta as nove colunas do enunciado, a partir do estado persistido:

- **Neutralização:** aplica-se a todas as células, num só ponto (SEC-17). O CSV sai em UTF-8 com BOM, escrito com `csv.writer`, e o separador é configurável. No XLSX, cada célula leva tipo texto explícito.
- **`Invoice_ID`:** combina o NIF do fornecedor, ou o seu nome normalizado, com o número da factura, ou com um digest curto quando falta o número.
- **Facturas ambíguas:** saem com a aba de destino vazia e o motivo.
- **Documentos recusados ou falhados:** saem numa linha `LOW` com o motivo em português.
- **`Notes_or_Flags`:** junta as sinalizações, as notas de tipo de linha e as linhas "ao cuidado de".
- **Entrega:** a resposta é sempre um anexo com `nosniff`.

### CHG-0020 · Tipos de linha

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0019
- **Estado:** activa
- **Requisitos:** REQ-ING-004, REQ-ING-006, D-3.17, L-06, L-16
- **Commit:** c16f64c
- **Migração:** `0005`, a partir de `0004`
- **Ficheiros:**
  - `backend/src/sextante/ingestion/domain/line_type.py`
  - `backend/src/sextante/ingestion/infrastructure/` (tabela e repositório)
  - `backend/src/sextante/matching/domain/line_decision.py` (`LineNote`, `non_service_line_decision`)
  - `backend/src/sextante/matching/application/encode_invoice.py`, `worker.py`, `review/`
  - `backend/migrations/versions/0005_line_types.py`
- **Reversibilidade:** total
- **Reversão:**
  1. Correr `alembic downgrade 0004`, que apaga `invoice_line.line_type` e `encoded_line.note`.
  2. Reverter o commit.

  Os eventos de auditoria `summary_rows_extracted` ficam.
- **Verificação:** 171 testes, incluindo 12 casos de tabela da classificação; `mypy`, `ruff`, 7 contratos do `import-linter`, funções com 20 linhas ou menos.

Cada linha é classificada como serviço, IVA ou desconto. O IVA só é reconhecido quando a descrição começa por "IVA", "VAT" ou "Imposto sobre o Valor Acrescentado". Assim ficam como serviços "Taxa de pilotagem", os direitos aduaneiros e uma descrição que menciona "(isento de IVA)".

Só as linhas de serviço vão ao modelo, e não há chamada se não houver nenhuma. As linhas de IVA e de desconto ficam sem código, com `HIGH`, aceites, sem sinalização e com uma nota do tipo. As linhas de resumo ficam registadas uma vez, na auditoria da factura. A percentagem de IVA de cada linha fica guardada como atributo.

### CHG-0019 · Correcções da revisão dos tickets 03 e 04

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0018
- **Estado:** activa
- **Requisitos:** REQ-ENT-003, REQ-ENT-007, REQ-CNF-002, REQ-PLT-002, NFR-REL-001, D-3.8, D-3.15, SEC-18
- **Commit:** 09d6f77
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/matching/domain/entity_check.py`, `line_decision.py`
  - `backend/src/sextante/matching/application/encode_invoice.py`, `worker.py`, `main.py`
  - `backend/src/sextante/ingestion/` (registo `EntityCheckRecord`)
  - `backend/src/sextante/review/`
  - `README.md`, e os testes
- **Reversibilidade:** total
- **Reversão:** reverter o commit. O esquema não mudou.
- **Verificação:** 154 testes, `mypy`, `ruff`, 7 contratos do `import-linter`, funções com 20 linhas ou menos.

Resolve os achados da revisão dos tickets 03 e 04.

**Spec:**

- Os limiares de `HIGH` passam a estritos ("acima", D-3.8). No limite exacto, a linha é `MEDIUM` e fica sinalizada como conflito.
- Um NIF sem dígitos, como "N/D", conta como não extraído e não veta a AMT.
- O arranque recusa uma lista de exclusão que contenha a própria AMT.
- O veredicto da entidade e as linhas passam a gravar-se na mesma transacção.

**Padrões:**

- `AmbiguityReason` sai: a verificação de entidade passa a usar `FlagReason`.
- A lista de exclusão é um objecto de valor, normalizado uma só vez.
- A decisão das linhas sem código passa a viver na regra de confiança.
- Os dados de referência, o registo do veredicto e a projecção da resposta passam a ter tipos com nome.
- As mensagens de erro passam a indicar a forma esperada.

### CHG-0018 · Confiança, recurso e sinalização

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0017
- **Estado:** activa
- **Requisitos:** REQ-CNF-001 a REQ-CNF-005, REQ-MAP-007 a REQ-MAP-009, REQ-MAP-013, REQ-REV-005, D-3.8, D-3.16, L-08, L-13
- **Commit:** 0927ffe
- **Migração:** `0004`, a partir de `0003`
- **Ficheiros:**
  - `backend/src/sextante/matching/domain/line_decision.py`, `scoring.py`
  - `backend/src/sextante/matching/application/encode_invoice.py`, `records.py`
  - `backend/src/sextante/matching/infrastructure/` (tabelas e repositório)
  - `backend/src/sextante/review/`, `worker.py`, `main.py`
  - `backend/src/sextante/platform/settings.py`, `user_messages.py`
  - `backend/migrations/versions/0004_confidence_and_flags.py`
  - `README.md`, `config/.env.example`
- **Reversibilidade:** parcial
- **Reversão:**
  1. Salvaguardar `sextante.db`.
  2. Apagar as linhas de `encoded_line` sem aba de destino: `DELETE FROM encoded_line WHERE target_sheet IS NULL`, depois de apagar as suas linhas de `line_flag`.
  3. Correr `alembic downgrade 0003`.
  4. Reverter o commit.

  Os eventos de auditoria `line_not_coded` ficam: a auditoria é só de inserção.
- **Verificação:**
  - Feito: 146 testes, incluindo 13 casos de tabela da regra de confiança com os limites exactos dos limiares; `mypy`, `ruff`, 7 contratos do `import-linter`, funções com 20 linhas ou menos.
  - Não verificado: calibração dos limiares, que espera pelo conjunto dourado (L-02).

A confiança é calculada pela regra de D-3.8:

- `HIGH` só quando o item escolhido é o topo lexical, com score de pelo menos 85 e pelo menos 10 de distância ao segundo;
- `MEDIUM` para os restantes itens válidos;
- `LOW` para o recurso, para a ausência de item, para uma resposta inválida e para um item genérico.

O `O00999` é atribuído em código, só em OUTLAYSP. Em OUTLAYS a linha fica vazia e sinalizada. Cada sinalização traz um motivo de um conjunto fechado, com texto em português. As linhas de facturas ambíguas ficam registadas com `LOW`, sem aba de destino e com o motivo da entidade, o que fecha o critério que a CHG-0017 deixou pendente. A auditoria regista a confiança, a regra que a produziu e as sinalizações.

### CHG-0017 · Verificação de entidade e encaminhamento para OUTLAYSP

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0016
- **Estado:** activa
- **Requisitos:** REQ-ENT-001 a REQ-ENT-008, REQ-MAP-001, D-3.15, L-04, L-13
- **Commit:** 2e9a846
- **Migração:** `0003`, a partir de `0002`
- **Ficheiros:**
  - `backend/src/sextante/matching/domain/entity_check.py`, `routing.py`
  - `backend/src/sextante/matching/infrastructure/denylist_file.py`
  - `backend/src/sextante/platform/text_normalization.py` (`fold_for_matching`)
  - `backend/src/sextante/worker.py`, `main.py`, `review/`
  - `backend/migrations/versions/0003_entity_check.py`
  - `config/entity_denylist.yaml`, novo e vazio; `config/.env.example`
  - dependência nova: PyYAML (MIT)
- **Reversibilidade:** total
- **Reversão:**
  1. Correr `alembic downgrade 0002`, que apaga as colunas `entity_verdict` e `entity_reason` e o seu conteúdo.
  2. Reverter o commit.
  3. Retirar `SEXTANTE_ENTITY_DENYLIST_PATH` do `.env`.
- **Verificação:**
  - Feito: 124 testes, incluindo 18 casos de tabela da regra de entidade; `mypy`, `ruff`, 7 contratos do `import-linter`, funções com 20 linhas ou menos.
  - Pendente: o critério "linhas de factura ambígua com `LOW` e sinalizadas" depende da confiança e das sinalizações do ticket 04 (CHG-0018).

A verificação de entidade aplica as sete regras de D-3.15, pela ordem, sem modelo:

- a lista de exclusão primeiro;
- o veto pelo NIF;
- a igualdade do nome normalizado;
- o limiar baixo de `token_sort_ratio`, a 60 e provisório.

Uma não correspondência é codificada contra OUTLAYSP. Uma entidade ambígua fica por codificar, com o motivo registado no cabeçalho, e nunca chega ao modelo. Os resultados mostram a entidade detectada e o `Exact_Entity_Match`. A lista de exclusão vem de configuração, com a estrutura definida e sem conteúdo (L-04).

### CHG-0016 · Diagramas regenerados com o desenho actual

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0015
- **Estado:** activa
- **Requisitos:** D-3.15, D-3.16, D-3.17, D-3.18
- **Commit:** df760ad
- **Migração:** nenhuma
- **Ficheiros:**
  - `scripts/gen_diagrams.py`
  - `docs/diagramas/*.excalidraw`
  - `assets/fluxo-codificacao.svg` e `assets/arquitectura-modulos.svg`, novos
  - `assets/architecture.png` e `assets/invoice-encoding-flow.png`, removidos
  - `docs/02-arquitectura.md` (§3)
  - `docs/agents/triage-labels.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit. Os PNG removidos voltam com ele.
- **Verificação:**
  - Feito:
    - script corrido;
    - os dois SVG abertos no Chrome sem interface e inspeccionados;
    - `graphify update` sem arestas de um nó para si próprio.
  - Não verificado: abrir os `.excalidraw` regenerados em excalidraw.com.

Os dois diagramas mostravam o desenho anterior: o desempate de entidade pelo Claude e as portas `EntityTiebreaker` e `CandidateRetriever`. Foram corrigidos no script e regenerados. Agora o Claude aparece num só passo, a entidade ambígua vai a um revisor, e as portas são as actuais.

Os PNG tinham sido exportados à mão, o que o `CLAUDE.md` não permite. Foram substituídos por SVG escritos pelo mesmo script, a partir dos mesmos elementos.

O título de `triage-labels.md` passou a «Triage label vocabulary». O título anterior gerava no grafo o mesmo identificador que o nome do ficheiro, e daí a aresta que ligava um nó a si próprio.

### CHG-0015 · Skill do graphify no projecto e correcção da CHG-0014

- **Data:** 2026-11-18
- **Tipo:** infra
- **Pai:** CHG-0014
- **Estado:** activa
- **Requisitos:** nenhum
- **Commit:** 3f4ff0f
- **Migração:** nenhuma
- **Ficheiros:**
  - `.claude/skills/graphify/`
  - `.claude/settings.json`
  - `.claude/CLAUDE.md`
  - `.gitattributes`, que a CHG-0014 criou mas não listou
- **Reversibilidade:** total
- **Reversão:**
  1. Correr `graphify claude uninstall`, que retira os hooks e a secção do `CLAUDE.md`.
  2. Apagar `.claude/skills/graphify/` e `.claude/CLAUDE.md`.
  3. Reverter o commit.
- **Verificação:**
  - Feito: `/graphify . --update` corrido sobre os documentos e as duas imagens de `assets/`, com o resultado em `graphify-out/` (fora do repositório).
  - Não verificado: os hooks não foram exercitados noutra máquina.

Corrige a CHG-0014 por adição, como manda a regra 4. Primeiro, a lista de ficheiros da CHG-0014 omitia o `.gitattributes` criado por `graphify hook install`, que regista o driver de fusão de `graph.json`. Segundo, os hooks do Claude Code passam de `.claude/settings.local.json` para `.claude/settings.json`, agora com o comando `graphify` sem caminho absoluto, e por isso partilháveis. O skill `/graphify` passa a viver no projecto.

### CHG-0014 · Graphify como memória do projecto

- **Data:** 2026-11-18
- **Tipo:** infra
- **Pai:** CHG-0012
- **Estado:** activa
- **Requisitos:** nenhum
- **Commit:** 35a41d0
- **Migração:** nenhuma
- **Ficheiros:**
  - `.graphifyignore`
  - `.gitignore`
  - `CLAUDE.md` (secção graphify)
  - fora do repositório: `.claude/settings.local.json`, `.git/hooks/post-*`, `~/.local/share/graphify/venv`, `~/.local/bin/graphify`
- **Reversibilidade:** total
- **Reversão:**
  1. Correr `graphify claude uninstall` e `graphify hook uninstall`.
  2. Apagar `.claude/settings.local.json`, `.graphifyignore` e `graphify-out/`.
  3. Retirar de `.gitignore` as linhas de `graphify-out/` e de `.claude/settings.local.json`.
  4. Apagar `~/.local/share/graphify/` e `~/.local/bin/graphify`.
  5. Reverter o commit.
- **Verificação:**
  - Feito:
    - pacote `graphifyy` 0.9.112 confirmado no PyPI, Apache-2.0, com o repositório oficial nos metadados;
    - `graphify update .` local, sem chamar modelo (1315 nós, 2622 arestas);
    - `graphify query` responde;
    - as definições globais do Claude Code ficaram intactas.
  - Por fazer: a extracção semântica dos documentos (`/graphify . --update`). Envia o texto dos documentos ao modelo do assistente; os documentos não têm dados de facturas.

Grafo de conhecimento local do código e dos documentos, que serve de memória entre sessões. As facturas, o catálogo real, as bases de dados e os segredos ficam excluídos por `.graphifyignore`. Os hooks guardam um caminho absoluto desta máquina, por isso ficam fora do repositório.

### CHG-0013 · Registo de alterações e a sua regra

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0012
- **Estado:** activa
- **Requisitos:** nenhum
- **Commit:** 35a41d0
- **Migração:** nenhuma
- **Ficheiros:** `CHANGELOG.md`, `CLAUDE.md` (secção «Registo de alterações» e passo 6 do fecho de tarefa)
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** a árvore e as entradas CHG-0001 a CHG-0012 foram conferidas com `git log` e com o histórico das sessões.

Cria este registo e torna-o obrigatório para qualquer agente, nesta sessão e nas seguintes. As entradas CHG-0001 a CHG-0012 foram reconstruídas depois dos factos, a partir dos commits e das sessões de 18-11-2026.

### CHG-0012 · Correcções da revisão do ticket 02

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0011
- **Estado:** activa
- **Requisitos:** REQ-ING-007, REQ-ING-008, REQ-MAP-005, REQ-MAP-007, REQ-AUD-001, REQ-PLT-001, SEC-14, SEC-16, SEC-18
- **Commit:** 56c85a3
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/review/`
  - `backend/src/sextante/ingestion/`
  - `backend/src/sextante/matching/`
  - `backend/src/sextante/main.py`
  - `backend/pyproject.toml`
  - `backend/tests/api/test_encoding_review_regressions.py`
- **Reversibilidade:** total
- **Reversão:** reverter o commit. As facturas já carregadas mantêm-se válidas, porque o esquema não mudou.
- **Verificação:**
  - Feito: 95 testes, `mypy --strict`, `ruff`, 7 contratos do `import-linter`, contagem automática das funções (nenhuma acima de 20 linhas), teste no servidor real.
  - Não verificado: `gitleaks`, que não está instalado.

Resolve os achados da revisão do ticket 02:

- todo o texto extraído é normalizado;
- o modelo recebe o contexto da factura;
- as respostas do modelo são revalidadas pelo esquema;
- a auditoria guarda todos os scores;
- um carregamento misto devolve os trabalhos já existentes;
- os resultados de um trabalho inexistente dão 404;
- a API passa a usar só a camada de aplicação;
- um módulo `review` compõe os leitores publicados pelos outros módulos.

### CHG-0011 · Carregamento e codificação em segundo plano

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0010
- **Estado:** activa
- **Requisitos:** REQ-PLT-001, REQ-ING-001, REQ-ING-007, REQ-MAP-001, REQ-MAP-003 a REQ-MAP-006, REQ-AUD-001, REQ-AUD-002, SEC-04, SEC-14
- **Commit:** 2d6af1b
- **Migração:** `0002`, a partir de `0001`
- **Ficheiros:**
  - `backend/src/sextante/ingestion/`
  - `backend/src/sextante/matching/`
  - `backend/src/sextante/worker.py`
  - `backend/src/sextante/platform/audit.py`
  - `backend/migrations/versions/0002_encoding_tables.py`
  - dependências novas: `rapidfuzz` (MIT) e `python-multipart` (Apache-2.0)
- **Reversibilidade:** parcial
- **Reversão:**
  1. Salvaguardar `sextante.db` e `uploads/`.
  2. Correr `alembic downgrade 0001`, que apaga as tabelas e os dados.
  3. Reverter o commit.

  Os eventos de auditoria apagados pelo `downgrade` só se recuperam pela salvaguarda. Sem ela, a reversão é `não`.
- **Verificação:** 87 testes, `mypy`, `ruff`, 5 contratos do `import-linter`, teste no servidor real (sem extractor configurado, a factura é recusada).

Carregamento com idempotência pelo digest e um trabalhador em processo que codifica contra OUTLAYS. O modelo recebe a aba inteira e responde com um índice validado. Cada linha codificada fica numa auditoria só de inserção. O extractor e o classificador ficam provisórios, recusando com motivo explícito, até aos tickets 12 e 11.

### CHG-0010 · Correcções da revisão do ticket 01

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0009
- **Estado:** activa
- **Requisitos:** REQ-MAP-012, REQ-PLT-005, REQ-PLT-006, REQ-PLT-007, NFR-OBS-001, SEC-15
- **Commit:** 753a000
- **Migração:** nenhuma; a migração `0001` muda de pasta para `backend/migrations/`
- **Ficheiros:** `backend/src/sextante/platform/`, `backend/src/sextante/catalog/`, `backend/migrations/`, `backend/tests/`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 52 testes, `mypy`, `ruff`, 3 contratos do `import-linter`, teste no servidor real com o identificador de correlação.

Resolve os achados da revisão do ticket 01:

- valores obrigatórios em branco passam a ser recusados;
- os logs do uvicorn saem em JSON, com `correlation_id` por pedido;
- os registos não se propagam além do handler JSON, por isso a redacção já não se pode perder;
- os erros de domínio herdam `DomainError`;
- os outros módulos só chegam ao catálogo pelos seus contratos.

### CHG-0009 · Arranque com catálogo validado

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0008
- **Estado:** activa
- **Requisitos:** REQ-MAP-012, REQ-PLT-007, REQ-PLT-008, NFR-OBS-001, D-3.5, D-3.9
- **Commit:** 5651ff7
- **Migração:** `0001` (base), sem revisão anterior
- **Ficheiros:** `backend/`, `config/.env.example`, `README.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit e apagar `sextante.db` e `backend/.venv`.
- **Verificação:** 33 testes, `mypy`, `ruff`, `import-linter`, licenças, `make run` com o catálogo real.

A aplicação arranca com um comando, escuta só em `127.0.0.1` e valida o catálogo. Recusa arrancar quando falta configuração ou o catálogo é inválido.

### CHG-0008 · Repositório git

- **Data:** 2026-11-18
- **Tipo:** infra
- **Pai:** CHG-0007
- **Estado:** activa
- **Requisitos:** SEC-03
- **Commit:** 8979ec5 (commit de base, agrega as entradas CHG-0001 a CHG-0008)
- **Migração:** nenhuma
- **Ficheiros:** `.gitignore`, ramo `feature/REQ-PLT-007-startup-catalog-validation`
- **Reversibilidade:** parcial
- **Reversão:** apagar `.git` elimina todo o histórico. A alternativa recomendada é manter o repositório e reverter commits concretos.
- **Verificação:** `git log` e `git status`. `sources/` está fora do controlo de versões por causa dos metadados do catálogo real (ponto 17 do OPEN-ITEMS).

Põe o projecto sob controlo de versões. Facturas, bases de dados, segredos e o catálogo real ficam fora.

### CHG-0007 · Limite de itens enviados ao modelo

- **Data:** 2026-11-18
- **Tipo:** security
- **Pai:** CHG-0006
- **Estado:** activa
- **Requisitos:** SEC-09, SEC-14, D-3.16
- **Commit:** 8979ec5 (agregado)
- **Migração:** nenhuma
- **Ficheiros:** `docs/03-seguranca.md`, a spec, os tickets 01 e 02
- **Reversibilidade:** total
- **Reversão:** reverter a alteração aos documentos e repor o limite de 20 candidatos por linha. Isso exige reverter também D-3.16 (a aba inteira enviada ao modelo).
- **Verificação:** pesquisa por `MAX_CANDIDATES` e `candidatos recuperados` em `docs/`, sem ocorrências.

O limite de 20 candidatos por linha passou a 100 itens por aba, por coerência com o envio da aba inteira. O índice continua validado pelo comprimento real da lista.

### CHG-0006 · Alinhamento dos documentos de desenho

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0005
- **Estado:** activa
- **Requisitos:** D-3.6, D-3.7, D-3.8, D-3.15 a D-3.18, L-13 a L-16
- **Commit:** 8979ec5 (agregado)
- **Migração:** nenhuma
- **Ficheiros:**
  - `docs/00-decisoes-e-lacunas.md`, `docs/01-requisitos.md`, `docs/02-arquitectura.md` e `docs/04-padroes-de-codigo.md` (versão 0.2)
  - `CLAUDE.md`
  - `OPEN-ITEMS.md`
- **Reversibilidade:** total
- **Reversão:** reverter as alterações aos documentos. O código que as implementa (CHG-0009 em diante) passaria a contradizê-los.
- **Verificação:** pesquisa por termos retirados (desempate, `token_set_ratio`, `other`, `EntityTiebreaker`), só encontrados em notas de retirada.

Passa para os documentos oficiais as decisões Q1 a Q24 e a evidência das amostras:

- a verificação de entidade deixa de usar o modelo;
- o NIF passa a vetar a correspondência, e o "ao cuidado de" não conta como entidade;
- o modelo recebe a aba inteira;
- a confiança é recalculada;
- entram os tipos de linha, as recusas e o conjunto dourado.

### CHG-0005 · Tickets 01 a 13 e emenda pelas amostras

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0004
- **Estado:** activa
- **Requisitos:** REQ-ING-009, REQ-ING-010, REQ-ENT-007, REQ-ENT-008
- **Commit:** 8979ec5 (agregado)
- **Migração:** nenhuma
- **Ficheiros:** `.scratch/nucleo-codificacao/issues/`, `.scratch/nucleo-codificacao/spec.md`, `GLOSSARY.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** os códigos esperados das amostras foram conferidos com o catálogo real.

Divide a spec em 13 tickets verticais e emenda-a com a extracção de PDF nativo, depois de analisar as 12 amostras.

### CHG-0004 · Especificação do núcleo de codificação

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0003
- **Estado:** activa
- **Requisitos:** REQ-ENT, REQ-MAP, REQ-CNF, REQ-REV, REQ-EXP (as cinco áreas)
- **Commit:** 8979ec5 (agregado)
- **Migração:** nenhuma
- **Ficheiros:** `.scratch/nucleo-codificacao/spec.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** fronteiras de teste confirmadas pelo utilizador.

Spec do núcleo de codificação, com 58 histórias de utilizador e duas fronteiras de teste: a API HTTP e as regras de domínio puras.

### CHG-0003 · Glossário e pontos em aberto da sessão de grilling

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0001
- **Estado:** activa
- **Requisitos:** L-01 a L-12
- **Commit:** 8979ec5 (agregado)
- **Migração:** nenhuma
- **Ficheiros:** `GLOSSARY.md`, `OPEN-ITEMS.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** as decisões Q1 a Q24 foram confirmadas pelo utilizador.

Fixa o vocabulário do domínio e regista os pontos que esperam resposta do avaliador e da AMT, com a decisão provisória de cada um.

### CHG-0002 · Configuração dos skills de engenharia

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0001
- **Estado:** activa
- **Requisitos:** nenhum
- **Commit:** 8979ec5 (agregado)
- **Migração:** nenhuma
- **Ficheiros:** `docs/agents/`, `CLAUDE.md` (secção «Agent skills»)
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** nenhuma além da leitura.

Tracker local em `.scratch/`, rótulos de triagem por omissão e documentação de domínio num único contexto.

### CHG-0001 · Documentação inicial do projecto

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** nenhum
- **Estado:** activa
- **Requisitos:** todos os de `docs/01-requisitos.md` (versão 0.1)
- **Commit:** 8979ec5 (agregado)
- **Migração:** nenhuma
- **Ficheiros:** `docs/00-decisoes-e-lacunas.md` a `docs/04-padroes-de-codigo.md`, `CLAUDE.md`, `assets/`, `scripts/gen_diagrams.py`
- **Reversibilidade:** total
- **Reversão:** não aplicável; é a raiz da árvore.
- **Verificação:** nenhuma.

Documentos de partida do projecto, anteriores às sessões de 18-11-2026.
