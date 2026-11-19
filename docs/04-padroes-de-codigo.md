# Padrões de Código

**Projecto:** Sextante, Pipeline de Codificação Automática de Linhas de Facturas de Fornecedores
**Stack:** Python 3.12 com FastAPI · React 18 com TypeScript · SQLite · Claude
**Versão:** 0.1 · 18-11-2026

---

## 0. Regra zero: idioma

**Todo o código é escrito em Inglês.** Identificadores, nomes de ficheiro, nomes de módulo, comentários, docstrings, mensagens de log, nomes de evento, nomes de tabela e de coluna, mensagens de commit e descrições de pull request.

**Todo o texto apresentado ao utilizador existe em Inglês e em Português** (REQ-PLT-006, revisto em 19-11-2026). Rótulos, estados, mensagens de validação, mensagens de erro e motivos de sinalização. Vive em catálogos de tradução, nunca em literais espalhados pelo código.

```python
# Correcto
class NoCandidateMatchesInOutlaysError(DomainError):
    """Raised when an OUTLAYS line has no acceptable catalog candidate."""

    user_message_key = "errors.matching.no_match_in_outlays"

# Errado
class ErroSemCorrespondencia(Exception):
    """Lançado quando não há correspondência."""
```

Razão: o código é mantido por quem vier depois e lido por ferramentas; a interface é lida pela contabilidade da AMT. São audiências diferentes.

**Excepção única, e é importante:** os prompts em `src/sextante/prompts/` são escritos em Inglês, mas contêm exemplos de descrições de factura em Português e em Inglês, porque é isso que o sistema recebe. Os exemplos são sintéticos, por SEC-02.

---

## 1. Estilo de código

### 1.1 Funções

* **4 a 20 linhas.** Mais do que 20 linhas, dividir.
* **Uma coisa por função.** Se o nome precisa de "e" para descrever o que faz, são duas funções.
* **Retorno antecipado em vez de ifs aninhados.** Máximo 2 níveis de indentação dentro do corpo.

```python
# Errado: três níveis, difícil de seguir
def resolve_item_number(line: InvoiceLine, choice: ItemChoice, sheet: TargetSheet) -> ItemNumber | None:
    if choice.candidate_index is not None:
        if choice.candidate_index < len(line.candidates):
            candidate = line.candidates[choice.candidate_index]
            if candidate.sheet == sheet:
                return candidate.item_number
            else:
                return None
    return None

# Correcto: retorno antecipado, um nível
def resolve_item_number(line: InvoiceLine, choice: ItemChoice, sheet: TargetSheet) -> ItemNumber | None:
    """Return the chosen candidate's item number, or None when the choice is unusable.

    The index is validated against the list the server built, and the candidate's
    sheet against the routed sheet, because the model's answer is untrusted input
    (03-seguranca.md SEC-14).

    Example:
        number = resolve_item_number(line, choice, TargetSheet.OUTLAYS)
    """
    if choice.candidate_index is None:
        return None
    if choice.candidate_index >= len(line.candidates):
        return None
    candidate = line.candidates[choice.candidate_index]
    if candidate.sheet is not sheet:
        return None
    return candidate.item_number
```

### 1.2 Ficheiros e módulos

* **Menos de 500 linhas por ficheiro.** Dividir por responsabilidade, não por tamanho.
* **Uma responsabilidade por módulo.**
* Módulos pequenos e focados em vez de ficheiros omnibus. Um `services.py` com 1200 linhas é um sintoma, não uma organização.

### 1.3 Nomes

* **Específicos e únicos.** Preferir nomes que devolvam menos de 5 ocorrências numa busca no repositório.
* **Proibidos:** `data`, `info`, `handler`, `manager`, `helper`, `utils`, `process`, `item` isolado, `obj`, `temp`, `result` isolado.

| Em vez de | Escrever |
|---|---|
| `data` | `invoice_payload`, `catalog_rows`, `retrieval_scores` |
| `item` | `catalog_item`, `invoice_line`, `item_number` |
| `handler` | `UnhandledErrorResponder`, `ModelTimeoutRetrier` |
| `Manager` | `CatalogIndexBuilder`, `EncodingJobClaimer` |
| `utils.py` | `text_normalization.py`, `formula_neutralization.py` |
| `process()` | `extract_lines_from_pdf()`, `classify_line_kind()` |
| `result` | `encoded_line`, `item_choice`, `entity_verdict` |

Neste projecto, `item` isolado é especialmente caro: existe o item do catálogo, a linha da factura e o código de item, e são três coisas diferentes que aparecem na mesma função. Ambiguidade aqui é a origem de defeitos reais, não um problema de estética.

### 1.4 Tipos

* **Tipagem explícita em toda a parte.** `mypy --strict` sem erros.
* **Proibido `Any`.** Também proibido `dict` e `list` sem parâmetros de tipo.
* Preferir `Protocol` a classe base abstracta para portas.
* Preferir `Literal` e `StrEnum` a cadeias livres em conjuntos fechados.
* `Final` em constantes de módulo, incluindo **todos** os limiares de confiança e todos os limites de comprimento.
* **Objectos de valor em vez de tipos primitivos** onde o domínio tem significado.

Esta última regra tem aqui uma aplicação concreta e não negociável:

```python
# Errado: três str que não são str, e que se trocam sem o compilador reclamar
def assign(self, description: str, sheet: str, code: str) -> str: ...

# Correcto
def assign(
    self,
    description: NormalizedDescription,
    sheet: TargetSheet,
    item_number: ItemNumber,
) -> EncodedLine:
    """Assign a catalog item number to one invoice line.

    Example:
        encoded = encoder.assign(description, TargetSheet.OUTLAYSP, ItemNumber("O00999"))

    Raises:
        ItemNumberNotInSheetError: when the number does not exist in that sheet.
    """
```

`ItemNumber` valida o padrão na construção. `TargetSheet` é um `StrEnum` de dois valores. `NormalizedDescription` só se constrói passando pela normalização NFC de SEC-09.3. Um `str` que é um código de item não é um `str`, e neste projecto trocar a aba por engano é o defeito mais caro possível: o tipo impede o que a revisão poderia não apanhar.

Objectos de valor do projecto: `ItemNumber`, `TargetSheet`, `Confidence`, `LineKind`, `FlagReason`, `ContentDigest`, `CatalogDigest`, `NormalizedDescription`, `EntityVerdict`, `PromptVersion`.

### 1.5 Duplicação

* **Zero duplicação de lógica.** Extrair para função ou módulo partilhado.
* Casos concretos neste projecto, onde duplicar produz divergência silenciosa:
  * A **normalização de texto** vive num único local, consumida pela verificação de entidade, pelos valores de comparação do catálogo e pela pontuação lexical. Duas normalizações diferentes produzem scores que ninguém consegue explicar.
  * A **regra de confiança** vive num único local, consumida pela codificação, pela sinalização e pela apresentação. Duplicá-la produz uma linha marcada `HIGH` na tabela e `MEDIUM` no detalhe.
  * A **lista de exclusão de entidades** vive em configuração e é lida num único local. Não é repetida no prompt, por SEC-14.
  * A **neutralização de fórmula** vive num único ponto da camada de exportação, nunca em cada construtor de linha, por SEC-17.
* Duplicação aceitável: entre contratos de entrada e de saída, que são deliberadamente separados por SEC-08, e entre módulos diferentes onde a semelhança é acidental.

### 1.6 Excepções

* **A mensagem inclui o valor ofensor e a forma esperada.**

```python
# Errado
raise ValueError("Invalid item number")

# Correcto
raise ItemNumberNotInSheetError(
    f"Item number {number!r} does not exist in sheet {sheet.value}. "
    f"Expected one of the {len(numbers)} numbers of that sheet, for example {numbers[0]!r}."
)
```

* Excepções de domínio herdam de `DomainError`, com `user_message_key` para tradução.
* **Nunca `except Exception: pass`.** Nunca capturar para silenciar. Se não há tratamento possível, deixar subir até ao tratador global.
* Capturar a excepção mais específica possível.
* **Nunca capturar uma falha de validação do modelo e seguir com um valor por omissão.** Uma resposta inválida do Claude é falha de linha, com `LOW` e sinalização, por REQ-MAP-007. Capturar e improvisar um código é o padrão de compensação que `03-seguranca.md` §22.3 proíbe.

---

## 2. Comentários

* **Manter os comentários existentes.** Não os retirar numa refactorização: carregam intenção e proveniência.
* **Escrever o PORQUÊ, não o QUÊ.** Nada de `# increment counter` sobre `i += 1`.
* **Docstring em toda a função pública:** intenção mais um exemplo de utilização.
* **Referenciar o motivo externo** quando a linha existe por causa de um requisito, de uma decisão ou de uma lacuna.

```python
# SQLite has foreign key enforcement disabled by default, which silently accepts
# orphan rows (02-arquitectura.md §5). Enabled per connection, not per database.
cursor.execute("PRAGMA foreign_keys = ON")
```

```python
# The denylist is evaluated before any fuzzy comparison, because a sister company
# of a freight forwarder usually shares the parent's prefix and fuzzy matching
# would accept it, violating the strict refusal rule (R4, REQ-ENT-003).
if normalized in self._denylist:
    return EntityVerdict.NO_MATCH
```

```python
# OUTLAYS has no fallback rule: the O00999 fallback is limited to OUTLAYSP (R3).
# An unmatched OUTLAYS line is handed back to a reviewer rather than filled in
# with a plausible code (L-08, REQ-MAP-009).
return None
```

Referenciar sempre `REQ-`, `NFR-`, `SEC-`, `D-`, `L-`, `R` ou o identificador do defeito, nunca "porque sim".

---

## 3. Testes

### 3.1 Comando único

```bash
# Backend
make test               # tudo
make test-unit          # rápido, sem I/O
make golden             # etapas determinísticas contra o conjunto dourado
make traceability-matrix # falha se algum REQ- ficar sem teste

# Frontend
pnpm test
pnpm test:e2e
```

### 3.2 Regras

* **Toda a função nova tem teste.** Toda a correcção de defeito tem teste de regressão que falha antes da correcção.
* **F.I.R.S.T:** rápidos, independentes, repetíveis, auto-verificáveis, atempados.
* Independentes significa que a ordem de execução não importa e que não há estado partilhado. Base de dados em memória por teste, ou ficheiro temporário descartado.
* Repetíveis significa relógio injectado, identificadores injectados, e **zero chamadas de rede**.
* **Nenhum teste chama a API da Anthropic.** Sem excepções, nem marcadas, nem opcionais, nem "só este". Um teste que chama a rede é lento, caro, não determinístico, e falha quando não há internet, que é precisamente quando se quer correr os testes.

### 3.3 Dublês nomeados, não stubs em linha

```python
# Errado
mock_classifier = Mock()
mock_classifier.choose.return_value = Mock(candidate_index=0)

# Correcto
class FakeItemClassifier(ItemClassifier):
    """In-memory classifier for tests. Returns declared choices and records calls.

    Example:
        classifier = FakeItemClassifier(choices={0: 2, 1: None})
    """

    def __init__(self, choices: Mapping[int, int | None]) -> None:
        self._choices = choices
        self.calls: list[ItemChoiceRequest] = []

    async def choose(self, request: ItemChoiceRequest) -> ItemChoiceResponse:
        self.calls.append(request)
        ...
```

Dublês do projecto, em `tests/fakes/`: `FakeInvoiceExtractor`, `FakeLexicalScorer`, `FakeItemClassifier`, `FakeInvoiceFileStore`, `FakeResultExporter`, `FixedClock`, `SequentialIdentifierGenerator`, `RecordingLogger`.

O duplo guarda as chamadas recebidas, e isso não é luxo: é o que permite ao teste de SEC-14 verificar o prompt construído, e ao teste de REQ-MAP-006 verificar que uma factura produziu **uma** chamada e não dez.

### 3.4 Marcação de rastreabilidade

Obrigatória. É o que gera a matriz de `01-requisitos.md` §0.

```python
@pytest.mark.requirement("REQ-MAP-009", "L-08")
async def test_no_match_in_outlays_leaves_item_number_empty() -> None:
    """OUTLAYS has no fallback rule, so the gap goes back to the reviewer."""


@pytest.mark.requirement("REQ-ENT-003", "R4")
async def test_sister_company_with_near_identical_name_is_refused() -> None:
    """The denylist wins over fuzzy similarity, always."""


@pytest.mark.requirement("SEC-14")
async def test_prompt_injection_in_description_cannot_assign_unlisted_code() -> None:
    """A description that reads like an instruction cannot widen the choice set."""
```

```bash
make traceability-matrix   # falha se algum REQ- ou SEC- ficar sem teste
```

### 3.5 Nomes dos testes

Frase que descreve o comportamento, não o método chamado.

```python
# Errado
def test_assign() -> None: ...
def test_entity() -> None: ...

# Correcto
def test_outlaysp_line_without_candidate_falls_back_to_o00999() -> None: ...
def test_outlays_line_without_candidate_is_left_empty_and_flagged() -> None: ...
def test_entity_with_lda_instead_of_limitada_still_matches() -> None: ...
def test_model_returning_index_beyond_candidate_list_is_rejected() -> None: ...
def test_same_file_uploaded_twice_returns_the_existing_job() -> None: ...
def test_exported_description_starting_with_equals_is_prefixed() -> None: ...
```

### 3.6 Conjunto dourado

`make golden` corre, sem chamar o modelo, as etapas determinísticas sobre as amostras da pasta `SEXTANTE_GOLDEN_SAMPLES_PATH`: extracção, verificação de entidade, aba de destino, tipos de linha e recusas. Compara-as com os resultados esperados de `tests/golden/expected_results.yaml` e falha quando divergem. *Revisto em 18-11-2026*, por 00-decisoes-e-lacunas.md §3.18.

A precisão dos códigos de item por aba, a distribuição de confiança e a taxa de sinalização precisam do modelo real. São medidas por um comando manual e explícito, fora de `make test` e da integração contínua, e só são publicadas depois de a AMT confirmar os resultados esperados (L-02).

Regras:

* As facturas sintéticas estão identificadas como sintéticas no nome e num cabeçalho dentro do ficheiro, e **nunca** são apresentadas como amostras reais, por NFR-TST-001.
* Nenhuma factura real entra no repositório, por SEC-03.
* O conjunto cobre os casos de NFR-TST-002. Um caso limite novo descoberto em uso entra no conjunto antes de a correcção ser escrita.
* O comando imprime também o número de chamadas ao modelo que teriam sido feitas, para que uma regressão em REQ-MAP-006 seja visível.

---

## 4. Dependências

* **Injectar por construtor ou parâmetro, nunca por importação global nem singleton de módulo.**
* **Envolver bibliotecas de terceiros atrás de uma interface própria do projecto.**

```python
# Errado: a biblioteca atravessa todo o domínio
import anthropic

class EncodeInvoiceUseCase:
    def execute(self, invoice_id: InvoiceId) -> None:
        client = anthropic.Anthropic()
        ...

# Correcto: porta do projecto, implementação substituível
class ItemClassifier(Protocol):
    """Chooses one catalog item of the target sheet per invoice line, or none."""

    async def choose(self, request: ItemChoiceRequest) -> ItemChoiceResponse: ...


class EncodeInvoiceUseCase:
    def __init__(
        self,
        extractor: InvoiceExtractor,
        scorer: LexicalScorer,
        classifier: ItemClassifier,
        clock: Clock,
    ) -> None:
        self._extractor = extractor
        self._scorer = scorer
        self._classifier = classifier
        self._clock = clock
```

Isto não é cerimónia. É a condição que permite três coisas concretas: testar sem chamar a rede, trocar de modelo ou de fornecedor sem tocar no domínio, e garantir que a validação de SEC-14 acontece num único ponto, dentro do adaptador, e não espalhada por quem usa o cliente.

*Revisto em 18-11-2026: `EntityTiebreaker` foi retirada, porque a verificação de entidade deixou de usar o modelo, e `CandidateRetriever` passou a `LexicalScorer`, que pontua a aba inteira sem filtrar.*

**Portas do projecto:** `Clock`, `IdentifierGenerator`, `InvoiceExtractor`, `OpticalCharacterRecognizer` (declarada, não implementada, por L-01), `LexicalScorer`, `ItemClassifier`, `InvoiceFileStore`, `EncodedResultRepository`, `AuditEventRepository`, `ResultExporter`.

**Nenhuma dependência entra sem verificação de licença**, por NFR-LIC-001 e pela regra transversal do `CLAUDE.md`.

---

## 5. Estrutura

* **Seguir a convenção do framework.** FastAPI no backend, Vite e React no frontend.
* **Caminhos previsíveis.** No backend, `modulo/{contracts,domain,application,infrastructure,api}`. Estrutura completa em `02-arquitectura.md` §2.4.
* As fronteiras são verificadas por `import-linter` e `eslint-plugin-boundaries`, no pipeline, não por revisão.

Regra prática para saber onde pôr código novo:

| O código... | Vai para |
|---|---|
| Expressa uma regra de negócio e não faz I/O | `domain` |
| Orquestra uma operação, abre transacção, chama portas | `application` |
| Fala com base de dados, rede, ficheiros, bibliotecas externas | `infrastructure` |
| Recebe HTTP, valida entrada, serializa saída | `api` |
| É consumido por outro módulo | `contracts` |
| É transversal a todos os módulos | `platform` |

Dois casos que geram dúvida neste projecto, resolvidos aqui:

* **A regra de confiança** é `domain` do módulo `matching`. É regra de negócio e não faz I/O, mesmo que consuma scores que vieram de `infrastructure`.
* **A construção do prompt** é `infrastructure` do módulo `matching`. É um detalhe do adaptador do Claude, e o domínio não deve saber que existe um prompt. Trocar de fornecedor de modelo não deve tocar em `domain`.

---

## 6. Formatação

Formatador por omissão da linguagem. Não se discute estilo para além disso.

| Linguagem | Ferramenta | Comando |
|---|---|---|
| Python | `ruff format` e `ruff check --fix` | `make fmt` |
| TypeScript, TSX | `prettier` e `eslint --fix` | `pnpm fmt` |
| SQL de migração | `sqlfluff` | `make fmt-sql` |
| YAML, Markdown | `prettier` | `pnpm fmt` |

Configuração em `pyproject.toml` e `.prettierrc`, versionada. Imposta por `pre-commit` e verificada no pipeline. Comprimento de linha: 100.

---

## 7. Registo de eventos

* **JSON estruturado** para depuração e observabilidade, escrito em `stdout`.
* **Texto simples** apenas na saída de comandos de linha destinados a pessoas.

```python
logger.info(
    "line_encoded",
    extra={
        "invoice_id": str(invoice.id),
        "line_index": line.index,
        "target_sheet": sheet.value,
        "assigned_item_no": str(item_number) if item_number else None,
        "confidence": confidence.value,
        "top_score": top_score,
        "chosen_position": chosen_position,
        "catalog_digest": str(catalog_digest),
        "correlation_id": correlation_id,
    },
)
```

Regras:

* Nome do evento em `snake_case`, estável, em Inglês. Serve de chave de agregação; não se reescreve a frase a cada alteração.
* `correlation_id` em todos os registos, propagado do HTTP para o trabalhador. Sem isto, uma codificação falhada é impossível de ligar ao carregamento que a originou.
* **Nunca registar** conteúdo de factura, descrição de linha, nome de fornecedor, valor monetário, corpo de prompt, resposta integral do modelo, nem a chave da API. A lista completa e o porquê estão em `03-seguranca.md` SEC-15.
* O registo acima é o modelo a seguir: guarda o score e a posição escolhida, que explicam a decisão, e não a descrição, que a alimentou.
* Níveis: `DEBUG` para diagnóstico de desenvolvimento, `INFO` para factos de negócio, `WARNING` para situações recuperáveis, `ERROR` para falhas que exigem atenção, `CRITICAL` para indisponibilidade.
* Nunca `print()` em código de aplicação.

---

## 8. Específico do frontend

### 8.1 TypeScript

* `strict: true`, `noUncheckedIndexedAccess: true`, `exactOptionalPropertyTypes: true`.
* **Proibido `any`.** `unknown` com estreitamento quando o tipo é desconhecido.
* Proibida a asserção `as` excepto em estreitamento comprovado, com comentário.
* Tipos de API **gerados** a partir do OpenAPI. Nunca escritos à mão.

### 8.2 Componentes

* Componentes de função, com props tipadas explicitamente.
* Menos de 150 linhas por componente. Mais do que isso, extrair subcomponente ou gancho.
* Lógica de estado em ganchos `use-*`, não dentro do JSX.
* Sem lógica de negócio no componente: o componente apresenta, o gancho decide.
* Componentes de base vêm do `ui-kit`, shadcn/ui copiado. Não se instalam bibliotecas de componentes concorrentes nem se recria um botão que já existe.

### 8.3 Onde vive cada tipo de estado

Regra única, para não haver duplicação:

| Estado | Onde vive | Nunca |
|---|---|---|
| Dados do servidor | TanStack Query | Copiados para outra loja |
| Filtros, página, ordenação partilháveis | Rota do TanStack Router, validada por Zod | `useState` solto |
| Campos de formulário de correcção | React Hook Form | `useState` por campo |
| Painéis abertos, preferências de vista | Zustand, loja pequena | Context API |

A Context API fica reservada a injecção de dependências que não muda. Estado que muda vai para Zustand.

Os filtros de confiança e de aba vão para a rota de propósito: um revisor que encontra um caso difícil precisa de poder enviar o endereço a um colega, e um filtro em `useState` não é partilhável.

### 8.4 Formulários

React Hook Form com resolvedor Zod. O esquema vem do OpenAPI, não é reescrito.

* `mode: "onBlur"`. Validar a cada tecla é hostil.
* Mensagens de erro vindas do catálogo, não de literais no esquema Zod, e avaliadas na validação (`error: () => t(...)`), para seguirem o idioma escolhido.
* Botão de submissão desactivado durante o envio, com o `Idempotency-Key` gerado antes do primeiro clique, por SEC-19.
* O selector de código de item **só oferece itens da aba de destino daquela linha**, por REQ-REV-002. A restrição é também validada no servidor, porque o selector é conveniência e não controlo.

### 8.5 Chamadas à API

* Instância única do cliente HTTP, em `shared/api`. Nunca uma chamada directa num componente.
* Todas as chamadas passam pelos ganchos gerados do OpenAPI.
* Chaves de cache do TanStack Query estruturadas e centralizadas, nunca literais espalhados:

```ts
export const encodingKeys = {
  all: ["encoding"] as const,
  job: (jobId: string) => [...encodingKeys.all, "job", jobId] as const,
  results: (jobId: string, filters: ResultFilters) =>
    [...encodingKeys.all, "results", jobId, filters] as const,
  candidates: (lineId: string) => [...encodingKeys.all, "candidates", lineId] as const,
} as const;
```

* Mutações declaram `Idempotency-Key` e invalidam as chaves afectadas em `onSuccess`.
* O acompanhamento do progresso de um trabalho usa sondagem com intervalo crescente, e para quando o trabalho termina (`completed` ou `failed`) ou não existe. Um trabalho em fila ou à espera de quota do modelo (`waiting_model`) ainda muda, e continua a ser sondado. Sondar indefinidamente um trabalho terminado é desperdício visível em qualquer registo de acesso.
* Erros apresentados por **Sonner**, com a mensagem no idioma escolhido, vinda do contrato de erro do servidor. Nunca `alert()`.

### 8.6 Texto da interface

Sem literais de texto visível no JSX. Tudo por catálogo de tradução.

```tsx
// Errado
<Button>Exportar resultados</Button>

// Correcto
<Button>{t("export.actions.download")}</Button>
```

Isto não é preparação para outro idioma: é o que garante que o texto em Português de REQ-PLT-006 é revisível num só lugar, incluindo estados, motivos de sinalização e mensagens de erro.

Os motivos de sinalização merecem nota: o código é um `FlagReason` em Inglês, estável, que vai para a base de dados e para o log; o texto apresentado vem do catálogo em Português. Os dois nunca se confundem, e o código nunca aparece no ecrã. *Nota de 19-11-2026:* a API já devolve, ao lado de cada código de sinalização e de nota, o texto em Português do catálogo do servidor (`user_messages.py`), e o ticket 03 do frontend pede que o ecrã mostre esse texto. O frontend não mantém uma segunda cópia destes textos: uma regra em dois sítios acaba por divergir. Os restantes textos da interface continuam no catálogo do frontend.

---

## 9. Git

* Ramos: `feature/<req-id>-descricao-curta`, por exemplo `feature/REQ-MAP-009-outlays-no-match`.
* Mensagens de commit em Inglês, no formato convencional, referenciando o requisito:

```
feat(matching): leave item number empty when OUTLAYS has no match

The O00999 fallback is limited to OUTLAYSP by the statement's rule, so an
unmatched OUTLAYS line is flagged for review instead of filled in with a
plausible code.

Implements: REQ-MAP-009 (L-08)
```

* Pull request não funde sem: formatação, `mypy --strict`, `ruff`, `import-linter`, `bandit`, testes unitários, conjunto dourado, matriz de rastreabilidade, auditoria de dependências e auditoria de licenças, todos verdes.
* **Varredura de segredos sobre o histórico completo antes de o repositório ser partilhado**, por SEC-03. O enunciado prevê entrega por link de GitHub, pelo que esta não é opcional.
* Nenhuma factura real e nenhum `.db` entram num commit.

---

## 10. Lista de verificação antes de abrir pull request

- [ ] Funções entre 4 e 20 linhas, ficheiros abaixo de 500
- [ ] Nenhum nome genérico (`data`, `item` isolado, `handler`, `manager`, `utils`)
- [ ] `mypy --strict` sem erros e sem `Any`
- [ ] Objecto de valor onde o domínio tem significado, não `str` solto
- [ ] Nenhuma duplicação de lógica introduzida, em especial normalização, confiança e neutralização de fórmula
- [ ] Máximo 2 níveis de indentação, retorno antecipado
- [ ] Mensagens de excepção com valor ofensor e forma esperada
- [ ] Nenhum `except Exception: pass` e nenhum valor por omissão a tapar falha de validação do modelo
- [ ] Docstring com intenção e exemplo em toda a função pública
- [ ] Comentários existentes preservados, com referência a `REQ-`, `SEC-`, `D-` ou `L-`
- [ ] Teste por função nova, regressão por defeito corrigido
- [ ] Dublês nomeados em `tests/fakes/`, sem `Mock()` em linha
- [ ] **Nenhum teste chama a API da Anthropic**
- [ ] Marca `@pytest.mark.requirement` nos testes novos
- [ ] Dependências injectadas, bibliotecas atrás de porta do projecto
- [ ] Licença verificada em qualquer dependência nova
- [ ] Código, identificadores e logs em Inglês
- [ ] Texto de interface em Inglês e em Português, nos dois catálogos
- [ ] **Todo o campo de texto com `max_length` declarado** (`03-seguranca.md` SEC-09.1)
- [ ] **Nada devolvido pelo modelo é usado sem validação de índice e de catálogo** (SEC-14)
- [ ] **Neutralização de fórmula aplicada a toda a coluna de texto exportada** (SEC-17)
- [ ] **Operação de escrita idempotente, com teste de concorrência** (SEC-19)
- [ ] Nenhum conteúdo de factura, nome de fornecedor nem valor monetário nos logs (SEC-15)
- [ ] Estado no sítio certo: servidor no Query, filtros na rota, formulário no RHF
- [ ] `import-linter` e `eslint-plugin-boundaries` verdes
- [ ] Gate de segurança percorrido e bloco de fecho preenchido (`03-seguranca.md` §1 e §21)
