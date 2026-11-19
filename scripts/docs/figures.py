"""Figures 2 to 10 of the technical documentation, drawn with the diagram kit.

Each function draws one figure in the kit's language; ``gen_diagrams.py`` lists them.
"""

from diagram_kit import BLUE, GRAY, GREEN, INK, MUTED, ORANGE, PURPLE, RED, YELLOW, Kit


def pipeline(k: Kit) -> None:
    k.title(k.tr("O percurso de uma factura", "The journey of one invoice"),
            k.tr("do PDF à exportação · só o passo 7 usa o modelo", "from PDF to export · only step 7 uses the model"))
    k.legend([(k.tr("determinístico", "deterministic"), BLUE), (k.tr("modelo", "model"), YELLOW),
              (k.tr("fronteira", "boundary"), RED), (k.tr("humano", "human"), ORANGE)])
    top = [
        (k.tr("CARREGAMENTO", "UPLOAD"), k.tr("digest SHA-256: o mesmo PDF abre o trabalho que já existe · até 50 ficheiros de 25 MiB", "SHA-256 digest: the same PDF opens the job that exists · up to 50 files of 25 MiB")),
        (k.tr("EXTRACÇÃO", "EXTRACTION"), k.tr("subprocesso isolado · PDF digitalizado → recusada (pdf_without_text_layer)", "isolated subprocess · scanned PDF → rejected (pdf_without_text_layer)")),
        (k.tr("TIPOS DE LINHA", "LINE TYPES"), k.tr("serviço segue · IVA e desconto ficam sem código, com nota", "service goes on · VAT and discount get no code, with a note")),
        (k.tr("ENTIDADE FACTURADA", "BILLED ENTITY"), k.tr("exclusão → igualdade → NIF → semelhança (figura 3)", "denylist → equality → NIF → similarity (figure 3)")),
        (k.tr("ABA DE DESTINO", "TARGET SHEET"), k.tr("MATCH → OUTLAYS · NO_MATCH → OUTLAYSP · AMBIGUOUS → revisão (passo 10)", "MATCH → OUTLAYS · NO_MATCH → OUTLAYSP · AMBIGUOUS → review (step 10)")),
    ]
    for i, (label, note) in enumerate(top):
        x = 40 + i * 250
        k.box(x, 150, 210, 62, BLUE, label, badge=str(i + 1), size=16)
        k.text(note, x + 4, 222, 206, size=13)
        if i < 4:
            k.arrow([(x + 210, 181), (x + 248, 181)])
    bottom = [
        (k.tr("SCORES LEXICAIS", "LEXICAL SCORES"), BLUE, k.tr("rapidfuzz sobre PT e EN · todos os itens da aba", "rapidfuzz over PT and EN · every item of the sheet")),
        ("CLAUDE", YELLOW, k.tr("uma chamada por factura · devolve índices (figura 4)", "one call per invoice · returns indices (figure 4)")),
        (k.tr("VALIDAÇÃO", "VALIDATION"), RED, k.tr("índice dentro da lista e item da aba, senão LOW", "index within the list and item of the sheet, else LOW")),
        (k.tr("REGRAS", "RULES"), BLUE, k.tr("confiança · O00999 só em OUTLAYSP · sinalizações (figura 5)", "confidence · O00999 only in OUTLAYSP · flags (figure 5)")),
        (k.tr("REVISÃO HUMANA", "HUMAN REVIEW"), ORANGE, k.tr("aceitar · corrigir · resolver a entidade (figura 6)", "accept · correct · resolve the entity (figure 6)")),
        (k.tr("EXPORTAÇÃO", "EXPORT"), BLUE, k.tr("CSV ou XLSX · 9 colunas · fórmulas neutralizadas", "CSV or XLSX · 9 columns · formulas neutralised")),
    ]
    for i, (label, colors, note) in enumerate(bottom):
        x = 40 + i * 210
        k.box(x, 430, 180, 62, colors, label, badge=str(i + 6), size=16)
        k.text(note, x + 4, 502, 176, size=13)
        if i < 5:
            k.arrow([(x + 180, 461), (x + 208, 461)])
    k.arrow([(1145, 300), (1145, 340), (130, 340), (130, 428)])
    k.text("MATCH / NO_MATCH", 560, 314, 200, size=13)
    k.arrow([(970, 570), (970, 610), (100, 610), (100, 494)], ORANGE, dashed=True)
    k.text(k.tr("entidade resolvida → volta à fila e recodifica do texto já extraído",
                "entity resolved → back to the queue, recoded from the text already extracted"), 300, 584, 640, size=13, color=ORANGE)
    k.code(40, 660, 1230, k.tr("CADA PASSO DEIXA REGISTO (REQ-AUD-001)", "EVERY STEP LEAVES A RECORD (REQ-AUD-001)"), [
        k.tr("model_call: modelo, versão do prompt, tokens de entrada, de saída e de cache", "model_call: model, prompt version, input, output and cache tokens"),
        k.tr("encoded_line: item, regra, confiança, índice escolhido, digest do catálogo · line_flag · lexical_score · audit_event",
             "encoded_line: item, rule, confidence, chosen index, catalog digest · line_flag · lexical_score · audit_event"),
    ], GRAY)


def entity(k: Kit) -> None:
    k.title(k.tr("Verificação da entidade facturada", "Billed-entity check"),
            k.tr("determinística · a ordem é a regra (REQ-ENT-003)", "deterministic · the order is the rule (REQ-ENT-003)"))
    k.legend([("MATCH", GREEN), ("NO_MATCH", BLUE), ("AMBIGUOUS", ORANGE)])
    k.box(20, 195, 140, 90, GRAY, k.tr("entidade extraída", "extracted entity"), sub=k.tr("nome + NIF", "name + NIF"), size=15)
    gates = [
        (180, k.tr("0 · uma só entidade?", "0 · one entity only?"), k.tr("etiqueta presente, um só bloco", "label present, one block")),
        (420, k.tr("1 · na lista de exclusão?", "1 · on the denylist?"), k.tr("igualdade sobre o nome normalizado · irmãs, armadores, clientes", "equality on the normalised name · sister companies, shipping lines, clients")),
        (660, k.tr("2 · nome igual ao da AMT?", "2 · name equal to AMT's?"), k.tr("normalizado · Limitada ≡ Lda", "normalised · Limitada ≡ Lda")),
        (900, k.tr("3 · NIF sem conflito?", "3 · NIF without conflict?"), k.tr("só um NIF extraído pode vetar; ausente não veta", "only an extracted NIF can veto; an absent one does not")),
    ]
    for x, label, hint in gates:
        k.diamond(x, 165, 200, 150, PURPLE, label, size=14)
        k.text(hint, x + 10, 118, 190, size=12, color=MUTED, align="center")
    k.arrow([(160, 240), (178, 240)])
    k.arrow([(380, 240), (418, 240)], label=k.tr("sim", "yes"), at=(385, 214))
    k.arrow([(620, 240), (658, 240)], label=k.tr("não", "no"), at=(625, 214))
    k.arrow([(860, 240), (898, 240)], label=k.tr("sim", "yes"), at=(865, 214))
    k.arrow([(1100, 240), (1138, 240)], label=k.tr("sim", "yes"), at=(1102, 214))
    k.box(1140, 195, 145, 90, GREEN, "MATCH", sub=k.tr("→ aba OUTLAYS", "→ OUTLAYS sheet"))
    k.arrow([(280, 315), (280, 428)], label=k.tr("não", "no"), at=(288, 360))
    k.box(190, 430, 180, 80, ORANGE, "AMBIGUOUS", sub="entity_label_not_found · multiple_billed_entities", size=15)
    k.arrow([(520, 315), (520, 428)], label=k.tr("sim", "yes"), at=(528, 360))
    k.box(430, 430, 180, 80, BLUE, "NO_MATCH", sub=k.tr("definitivo, qualquer semelhança", "final, whatever the similarity"), size=15)
    k.arrow([(760, 315), (760, 398)], label=k.tr("não", "no"), at=(768, 340))
    k.diamond(660, 400, 200, 140, PURPLE, k.tr("4 · semelhança ≥ 60?", "4 · similarity ≥ 60?"), size=14)
    k.text("token_sort_ratio", 600, 548, 160, size=12, color=MUTED)
    k.arrow([(860, 470), (908, 470)], label=k.tr("sim", "yes"), at=(864, 444))
    k.arrow([(1000, 315), (1000, 428)], label=k.tr("não", "no"), at=(1008, 360))
    k.box(910, 430, 190, 80, ORANGE, "AMBIGUOUS", sub="entity_similar_not_equal · entity_nif_mismatch", size=15)
    k.arrow([(760, 540), (760, 638)], label=k.tr("não", "no"), at=(768, 580))
    k.box(670, 640, 180, 70, BLUE, "NO_MATCH", sub=k.tr("→ aba OUTLAYSP", "→ OUTLAYSP sheet"), size=15)
    k.note(30, 580, 600, [
        k.tr("Porquê esta ordem: uma empresa irmã tem um nome quase igual ao da AMT. Se a semelhança decidisse antes da lista de exclusão, a factura seria ambígua ou MATCH e a regra R4 ficava violada em silêncio.",
             "Why this order: a sister company has a name almost equal to AMT's. If similarity decided before the denylist, the invoice would be ambiguous or MATCH and rule R4 would be broken silently."),
        k.tr("O modelo de linguagem não entra nesta decisão.", "The language model takes no part in this decision."),
    ], PURPLE)
    k.listing(900, 560, 380, k.tr("DEPOIS", "AFTERWARDS"), [
        "MATCH → OUTLAYS",
        "NO_MATCH → OUTLAYSP",
        k.tr("AMBIGUOUS → sem aba nem códigos; um revisor decide, com nota obrigatória, e a factura volta à fila",
             "AMBIGUOUS → no sheet, no codes; a reviewer decides, with a mandatory note, and the invoice goes back to the queue"),
    ], ORANGE)


def model_call(k: Kit) -> None:
    k.title(k.tr("Chamada ao modelo e poupança de tokens", "Model call and token savings"),
            k.tr("o que se corta antes · o que se envia · o que se valida depois", "what is cut before · what is sent · what is checked after"))
    k.legend([(k.tr("poupança", "savings"), BLUE), (k.tr("modelo", "model"), YELLOW),
              (k.tr("fronteira", "boundary"), RED), (k.tr("qualidade", "quality"), GREEN)])
    cuts = [
        (k.tr("DEDUP POR DIGEST", "DEDUP BY DIGEST"), k.tr("o mesmo PDF nunca é recodificado; reprocessar parte do texto extraído", "the same PDF is never recoded; reprocessing starts from the extracted text")),
        (k.tr("SÓ LINHAS DE SERVIÇO", "SERVICE LINES ONLY"), k.tr("IVA e desconto decididos por regras, fora do pedido", "VAT and discount decided by rules, left out of the request")),
        (k.tr("UMA ABA, DECIDIDA ANTES", "ONE SHEET, DECIDED FIRST"), k.tr("o modelo vê só a aba de destino, até 100 itens", "the model sees only the target sheet, up to 100 items")),
        (k.tr("TECTO DE CHAMADAS", "CALL CEILING"), k.tr("200 por hora por omissão; acima disso a fila espera", "200 per hour by default; above that the queue waits")),
    ]
    for i, (label, sub) in enumerate(cuts):
        k.box(40, 140 + i * 102, 290, 84, BLUE, label, sub=sub, badge=str(i + 1), size=15)
    k.arrow([(330, 300), (378, 300)])
    k.shape("rectangle", 380, 120, 460, 330, INK, fill=False)
    k.text(k.tr("PEDIDO · um por factura", "REQUEST · one per invoice"), 400, 132, 420, size=19)
    blocks = [
        (GRAY, "system 1 · prompt item-choice-v2", k.tr("fixo · versionado · aprovado pelo responsável", "fixed · versioned · approved by the owner")),
        (YELLOW, "system 2 · <catalog_candidates>", k.tr("itens da aba em PT e EN · cache_control: ephemeral", "sheet items in PT and EN · cache_control: ephemeral")),
        (ORANGE, "user · <invoice_data>", k.tr("fornecedor, moeda e linhas de serviço · '<' escapado", "supplier, currency and service lines · '<' escaped")),
    ]
    for i, (colors, label, sub) in enumerate(blocks):
        k.box(400, 172 + i * 88, 420, 72, colors, label, sub=sub, size=15)
    k.code(380, 470, 460, k.tr("PARÂMETROS", "PARAMETERS"), [
        "output_config.format = json_schema",
        "effort = low",
        k.tr("max_tokens = 2048 + 64 × linhas", "max_tokens = 2048 + 64 × lines"),
        "fallbacks = default",
        k.tr("3 tentativas com recuo exponencial", "3 attempts with exponential backoff"),
    ], GRAY)
    k.note(40, 560, 300, [
        k.tr("CACHE: a 1.ª factura de uma aba escreve a lista de candidatos; as seguintes lêem-na a cerca de 1/10 do preço enquanto a cache vive (5 min, renovados a cada uso).",
             "CACHE: the 1st invoice of a sheet writes the candidate list; the next ones read it at about 1/10 of the price while the cache lives (5 min, renewed on each use)."),
    ], GREEN)
    k.arrow([(340, 590), (398, 280)], GREEN, dashed=True)
    k.box(950, 130, 230, 58, YELLOW, "CLAUDE SONNET 5.5", badge="5")
    k.arrow([(840, 190), (948, 160)])
    k.code(900, 230, 370, k.tr("RESPOSTA · só índices", "ANSWER · indices only"), [
        '{"choices": [',
        ' {"line_position":1,"candidate_index":4},',
        ' {"line_position":2,"candidate_index":null}',
        ']}',
    ], YELLOW)
    k.arrow([(1065, 188), (1065, 228)])
    k.box(900, 400, 170, 70, RED, k.tr("VALIDAÇÃO", "VALIDATION"), sub=k.tr("índice e aba · SEC-14", "index and sheet · SEC-14"), badge="6", size=15)
    k.arrow([(985, 352), (985, 398)])
    k.box(1100, 400, 170, 70, BLUE, k.tr("REGRAS", "RULES"), sub=k.tr("confiança calculada", "computed confidence"), badge="7", size=15)
    k.arrow([(1070, 435), (1098, 435)])
    k.table(900, 510, 370, "model_call", [
        "model_id · prompt_version",
        "input_tokens · output_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
    ], colors=BLUE)
    k.listing(40, 720, 840, k.tr("QUALIDADE", "QUALITY"), [
        k.tr("candidatos completos da aba em PT e EN · a confiança cruza o score lexical com a escolha do modelo · desacordo baixa a confiança e sinaliza · golden set: make golden e make golden-model · versão do prompt em cada decisão",
             "complete sheet candidates in PT and EN · confidence crosses the lexical score with the model's choice · disagreement lowers confidence and flags · golden set: make golden and make golden-model · prompt version stored with each decision"),
    ])


def line_decision(k: Kit) -> None:
    k.title(k.tr("Decisão de uma linha", "Decision for one line"),
            k.tr("confiança e recurso calculados em código, nunca pedidos ao modelo", "confidence and fallback computed in code, never asked of the model"))
    k.legend([("HIGH", GREEN), ("MEDIUM", YELLOW), ("LOW", RED)])
    k.box(20, 200, 150, 80, BLUE, k.tr("escolha validada", "validated choice"), sub=k.tr("índice ou null", "index or null"), size=15)
    k.arrow([(170, 240), (198, 240)])
    k.diamond(200, 165, 210, 150, PURPLE, k.tr("resposta válida?", "valid answer?"))
    k.arrow([(410, 240), (448, 240)], label=k.tr("sim", "yes"), at=(414, 214))
    k.diamond(450, 165, 210, 150, PURPLE, k.tr("índice = null?", "index = null?"))
    k.arrow([(660, 240), (698, 240)], label=k.tr("não", "no"), at=(664, 214))
    k.diamond(700, 165, 210, 150, PURPLE, k.tr("item genérico? (O00052…)", "generic item? (O00052…)"), size=14)
    k.arrow([(910, 240), (948, 240)], label=k.tr("não", "no"), at=(914, 214))
    k.diamond(950, 155, 220, 170, PURPLE, k.tr("1.º no score · score > 85 · margem > 10?", "1st by score · score > 85 · margin > 10?"), size=13)
    k.arrow([(1170, 240), (1178, 240)], label=k.tr("sim", "yes"), at=(1140, 190))
    k.box(1180, 200, 120, 80, GREEN, "HIGH", sub="high_\nagreement", size=16)
    k.arrow([(305, 315), (305, 360), (125, 360), (125, 398)], label=k.tr("não", "no"), at=(240, 334))
    k.box(30, 400, 190, 80, RED, k.tr("LOW · sem código", "LOW · no code"), sub="model_response_invalid", size=15)
    k.arrow([(555, 315), (555, 388)], label=k.tr("sim", "yes"), at=(562, 340))
    k.diamond(450, 390, 210, 140, PURPLE, k.tr("aba = OUTLAYSP?", "sheet = OUTLAYSP?"))
    k.arrow([(555, 530), (555, 618)], label=k.tr("sim", "yes"), at=(562, 560))
    k.box(460, 620, 190, 80, RED, "LOW · O00999", sub="fallback_applied", size=15)
    k.arrow([(450, 460), (305, 460), (305, 618)], label=k.tr("não", "no"), at=(360, 434))
    k.box(210, 620, 190, 80, RED, k.tr("LOW · código vazio", "LOW · empty code"), sub="no_match_in_outlays", size=15)
    k.arrow([(805, 315), (805, 418)], label=k.tr("sim", "yes"), at=(812, 350))
    k.box(710, 420, 190, 80, RED, k.tr("LOW · item genérico", "LOW · generic item"), sub="generic_catalog_item", size=15)
    k.arrow([(1060, 325), (1060, 418)], label=k.tr("não", "no"), at=(1068, 350))
    k.box(950, 420, 220, 80, YELLOW, "MEDIUM", sub=k.tr("+ conflicting_candidates se é 1.º ou 2.º com margem ≤ 10", "+ conflicting_candidates if 1st or 2nd with margin ≤ 10"), size=16)
    k.note(700, 560, 580, [
        k.tr("R3 + L-08: em OUTLAYS, a falta de item volta ao revisor. Nunca O00999, nunca «o melhor disponível».",
             "R3 + L-08: in OUTLAYS, a missing item goes back to the reviewer. Never O00999, never \"the best available\"."),
        k.tr("Uma linha sem sinalizações nasce aceite; uma sinalizada nasce pendente.", "A line without flags starts accepted; a flagged one starts pending."),
        k.tr("Fora desta árvore: IVA e desconto → sem código, HIGH, com nota · factura ambígua → sem código, LOW, sinalizada.",
             "Outside this tree: VAT and discount → no code, HIGH, with a note · ambiguous invoice → no code, LOW, flagged."),
    ], RED)


def review(k: Kit) -> None:
    k.title(k.tr("Revisão humana e auditoria", "Human review and audit"),
            k.tr("o revisor decide · nada se apaga · tudo fica registado", "the reviewer decides · nothing is deleted · everything is recorded"))
    k.legend([(k.tr("1–5 painel", "1–5 panel"), ORANGE), (k.tr("recodificação", "recoding"), PURPLE), (k.tr("registos", "records"), BLUE)])
    k.people(40, 150, k.tr("revisor", "reviewer"))
    k.arrow([(140, 190), (178, 190)])
    k.box(180, 160, 220, 60, ORANGE, k.tr("RESULTADOS", "RESULTS"), badge="1")
    k.note(180, 240, 220, [
        k.tr("a. filtros: confiança, aba, sinalização", "a. filters: confidence, sheet, flag"),
        k.tr("b. filtros no endereço, partilháveis", "b. filters in the address, shareable"),
        k.tr("c. até 100 linhas por página", "c. up to 100 lines per page"),
    ], ORANGE)
    k.arrow([(400, 190), (448, 190)])
    k.box(450, 160, 220, 60, ORANGE, k.tr("REVER LINHA", "REVIEW LINE"), badge="2")
    k.note(450, 240, 220, [
        k.tr("a. todos os itens da aba, por score", "a. every item of the sheet, by score"),
        k.tr("b. escolha do modelo marcada", "b. model's choice marked"),
        k.tr("c. histórico das codificações", "c. coding history"),
    ], ORANGE)
    k.box(730, 110, 190, 66, GREEN, k.tr("ACEITAR", "ACCEPT"), sub=k.tr("só pendentes", "pending only"), size=16)
    k.box(730, 200, 190, 66, YELLOW, k.tr("CORRIGIR", "CORRECT"), sub=k.tr("item da mesma aba", "item of the same sheet"), size=16)
    k.arrow([(670, 180), (728, 143)])
    k.arrow([(670, 200), (728, 233)])
    k.arrow([(920, 143), (978, 160)], BLUE)
    k.arrow([(920, 233), (978, 190)], BLUE)
    k.table(980, 110, 290, "line_review", [
        "encoded_line_id · review_status",
        "item_number · note",
        "reviewed_by · reviewed_at",
    ], colors=BLUE)
    k.table(980, 300, 290, "audit_event", [
        "event_type · subject · author",
        k.tr("recorded_at · só inserção", "recorded_at · insert only"),
    ], colors=BLUE)
    k.box(180, 440, 220, 66, ORANGE, k.tr("POR RESOLVER", "TO RESOLVE"), sub=k.tr("entidade ambígua", "ambiguous entity"), badge="3", size=16)
    k.arrow([(400, 473), (448, 473)])
    k.box(450, 440, 220, 66, ORANGE, k.tr("RESOLVER ENTIDADE", "RESOLVE ENTITY"), sub=k.tr("é / não é a AMT · nota obrigatória", "is / is not AMT · mandatory note"), badge="4", size=15)
    k.text("INSERT entity_resolution + audit_event", 450, 512, 240, size=13, color=BLUE)
    k.arrow([(670, 473), (728, 473)])
    k.box(730, 440, 190, 66, PURPLE, k.tr("FILA", "QUEUE"), sub="queued", size=16)
    k.arrow([(825, 506), (825, 568)])
    k.box(730, 570, 190, 76, PURPLE, k.tr("TRABALHADOR", "WORKER"), sub=k.tr("recodifica do texto extraído, na aba decidida", "recodes from the extracted text, in the decided sheet"), size=15)
    k.arrow([(920, 608), (978, 608)], BLUE)
    k.table(980, 520, 290, "encoded_line", [
        k.tr("nova codificação em vigor", "new coding in force"),
        k.tr("anterior: superseded_at preenchido", "previous: superseded_at set"),
        k.tr("revisão anterior → review_superseded", "previous review → review_superseded"),
    ], colors=BLUE)
    k.box(180, 650, 220, 66, GREEN, k.tr("EXPORTAÇÃO", "EXPORT"), sub=k.tr("codificação em vigor + revisão", "coding in force + review"), badge="5", size=16)
    k.code(450, 690, 470, k.tr("REGRAS QUE NÃO SE QUEBRAM", "RULES THAT DO NOT BREAK"), [
        k.tr("a codificação original nunca é apagada", "the original coding is never deleted"),
        k.tr("uma resolução nunca muda a lista de exclusão (D-3.15)", "a resolution never changes the denylist (D-3.15)"),
    ])


def integration(k: Kit) -> None:
    k.title(k.tr("Camada de integração", "Integration layer"),
            k.tr("portas e adaptadores · tracejado = a construir", "ports and adapters · dashed = to build"))
    k.legend([(k.tr("núcleo e portas", "core and ports"), PURPLE), (k.tr("adaptadores", "adapters"), BLUE), (k.tr("opcional", "optional"), GRAY)])
    k.box(505, 100, 290, 70, GRAY, k.tr("ORQUESTRADOR (opcional)", "ORCHESTRATOR (optional)"),
          sub=k.tr("n8n · Power Automate · Logic Apps: chama a API, não guarda regras", "n8n · Power Automate · Logic Apps: calls the API, holds no rules"), dashed=True, size=15)
    k.arrow([(650, 170), (650, 208)], GRAY, dashed=True)
    k.shape("rectangle", 440, 210, 420, 360, PURPLE, width=3)
    k.text(k.tr("NÚCLEO SEXTANTE", "SEXTANTE CORE"), 460, 226, 380, size=20, color=PURPLE[0], align="center")
    k.text(k.tr("regras, sem saber de onde vêm os dados", "rules, unaware of where data comes from"), 535, 256, 230, size=13, color=MUTED, align="center")
    k.text(k.tr("· carregar factura\n· codificar: entidade, aba, scores, modelo, regras\n· rever e auditar\n· exportar · lançar",
                "· upload invoice\n· code: entity, sheet, scores, model, rules\n· review and audit\n· export · post"), 530, 300, 240, size=15)
    k.table(530, 430, 240, k.tr("outbox de lançamento", "posting outbox"), [
        k.tr("linha · idempotency_key · estado · tentativa · documento no ERP", "line · idempotency_key · status · attempt · ERP document"),
    ], colors=GREEN, size=13)
    for y, name, future in [(250, "InvoiceSource", True), (350, "CatalogSource", False), (450, "Identity", True)]:
        k.box(370, y, 150, 40, PURPLE, name, size=14, dashed=future)
    for y, name, future in [(250, "PostingTarget", True), (350, "EventPublisher", True), (450, "ItemClassifier", False)]:
        k.box(780, y, 150, 40, PURPLE, name, size=14, dashed=future)
    k.box(575, 550, 150, 40, PURPLE, "InvoiceExtractor", size=14)
    left = [
        (120, k.tr("API REST (hoje)", "REST API (today)"), False, 270),
        (180, "E-MAIL · Microsoft Graph", True, 270),
        (240, k.tr("PASTA PARTILHADA · SFTP", "SHARED FOLDER · SFTP"), True, 270),
        (330, k.tr("XLSX DO CATÁLOGO (hoje)", "CATALOG XLSX (today)"), False, 370),
        (390, k.tr("ITENS E CONTAS DO ERP", "ERP ITEMS AND ACCOUNTS"), True, 370),
        (470, "ENTRA ID · OIDC", True, 470),
    ]
    for y, label, future, port_y in left:
        k.box(30, y, 270, 46, BLUE, label, size=14, dashed=future)
        k.arrow([(300, y + 23), (368, port_y)], BLUE, dashed=future)
    right = [
        (120, "DYNAMICS 365", True, 270),
        (180, k.tr("OUTRO ERP (SAP, Primavera…)", "OTHER ERP (SAP, Primavera…)"), True, 270),
        (290, "WEBHOOKS", True, 370),
        (350, "AZURE SERVICE BUS", True, 370),
        (430, k.tr("CLAUDE (hoje)", "CLAUDE (today)"), False, 470),
        (490, k.tr("OUTRO MODELO OU FORNECEDOR", "OTHER MODEL OR PROVIDER"), True, 470),
    ]
    for y, label, future, port_y in right:
        k.box(1010, y, 270, 46, BLUE, label, size=14, dashed=future)
        k.arrow([(930, port_y), (1008, y + 23)], BLUE, dashed=future)
    k.box(470, 650, 170, 46, BLUE, k.tr("PDF NATIVO (hoje)", "NATIVE PDF (today)"), size=14)
    k.box(660, 650, 170, 46, BLUE, "OCR · L-01", size=14, dashed=True)
    k.arrow([(620, 590), (560, 648)], BLUE)
    k.arrow([(680, 590), (740, 648)], BLUE, dashed=True)
    k.note(30, 580, 400, [
        k.tr("a. cada sistema novo é um adaptador de uma porta; as regras não mudam", "a. each new system is an adapter of a port; the rules do not change"),
        k.tr("b. cada adaptador passa os testes do contrato da porta", "b. each adapter passes the port's contract tests"),
        k.tr("c. lançamentos passam pela outbox: um reenvio nunca duplica", "c. postings go through the outbox: a resend never duplicates"),
    ], PURPLE)
    k.note(870, 590, 410, [
        k.tr("ao ERP vão só linhas aceites ou corrigidas, nunca um LOW por rever", "only accepted or corrected lines go to the ERP, never an unreviewed LOW"),
        k.tr("credenciais por sistema (OAuth client credentials), com o mínimo de permissões", "credentials per system (OAuth client credentials), least privilege"),
    ], RED)


def hybrid(k: Kit) -> None:
    k.title(k.tr("Modo híbrido com o Dynamics 365", "Hybrid mode with Dynamics 365"),
            k.tr("o Sextante codifica e revê · o D365 é o sistema de registo", "Sextante codes and reviews · D365 is the system of record"))
    k.legend([("A · " + k.tr("lançamento", "posting"), BLUE), ("B · " + k.tr("pedido pontual", "on-demand"), ORANGE),
              ("C · " + k.tr("catálogo", "catalog"), GREEN)])
    k.group(20, 130, 560, 500, k.tr("AMT · infra própria ou nuvem privada", "AMT · own infrastructure or private cloud"))
    k.group(840, 130, 440, 500, "Microsoft Cloud")
    k.box(50, 170, 230, 64, PURPLE, "SEXTANTE", sub=k.tr("API · trabalhador · painel", "API · worker · panel"), badge="1")
    k.box(50, 310, 230, 70, BLUE, k.tr("BASE DE DADOS + FICHEIROS", "DATABASE + FILES"), sub=k.tr("PDF e descrições ficam aqui", "PDFs and descriptions stay here"), badge="2", size=15)
    k.arrow([(165, 234), (165, 308)], BLUE, both=True)
    k.box(330, 170, 220, 64, BLUE, k.tr("ADAPTADOR D365", "D365 ADAPTER"), sub=k.tr("outbox · idempotência por linha", "outbox · idempotency per line"), badge="3", size=15)
    k.box(330, 310, 220, 70, ORANGE, k.tr("LEITOR DE PEDIDOS", "REQUEST READER"), sub=k.tr("lê a fila, só ligações de saída", "reads the queue, outbound only"), badge="4", size=15)
    k.arrow([(280, 202), (328, 202)], BLUE)
    k.arrow([(328, 340), (280, 225)], ORANGE)
    k.people(120, 450, k.tr("revisores · SSO Entra ID", "reviewers · Entra ID SSO"))
    k.box(620, 190, 180, 260, YELLOW, "AZURE SERVICE BUS", sub=k.tr("filas:\nsextante-posting\nsextante-requests\nsextante-results", "queues:\nsextante-posting\nsextante-requests\nsextante-results"), badge="5", size=15)
    k.arrow([(550, 202), (618, 240)], BLUE, label="A", at=(566, 228))
    k.arrow([(618, 340), (552, 340)], ORANGE, label="B", at=(578, 310))
    k.arrow([(552, 365), (618, 400)], ORANGE)
    k.text(k.tr("resultado", "result"), 550, 392, 80, size=13, color=ORANGE[0])
    k.box(870, 170, 380, 74, BLUE, "DYNAMICS 365 FINANCE / BUSINESS CENTRAL",
          sub=k.tr("factura de fornecedor · linhas · contas", "vendor invoice · lines · accounts"), badge="6", size=15)
    k.box(870, 310, 380, 74, GRAY, "POWER AUTOMATE / LOGIC APPS",
          sub=k.tr("lê e escreve nas filas · chama a API do D365", "reads and writes the queues · calls the D365 API"), badge="7", size=15)
    k.box(870, 450, 380, 74, ORANGE, "ENTRA ID",
          sub=k.tr("SSO dos revisores · identidade da aplicação (client credentials)", "reviewers' SSO · application identity (client credentials)"), badge="8", size=15)
    k.arrow([(800, 320), (868, 345)], BLUE, both=True)
    k.arrow([(1060, 308), (1060, 246)], BLUE, both=True)
    k.arrow([(1060, 168), (1060, 116), (165, 116), (165, 168)], GREEN, dashed=True)
    k.text(k.tr("C · itens e contas, sincronização diária", "C · items and accounts, daily sync"), 600, 92, 420, size=13, color=GREEN[0])
    k.listing(30, 650, 620, k.tr("QUANDO USAR CADA MODO", "WHEN TO USE EACH MODE"), [
        k.tr("A. lançamento normal: as linhas aceites seguem do Sextante para o D365", "A. normal posting: accepted lines go from Sextante to D365"),
        k.tr("B. caso específico: uma factura chegou ao D365 primeiro; um fluxo pede a codificação e recebe as linhas sugeridas", "B. specific case: an invoice reached D365 first; a flow requests the coding and receives the suggested lines"),
        k.tr("C. o catálogo e o plano de contas passam a vir do D365", "C. the catalog and chart of accounts come from D365"),
    ], BLUE)
    k.note(680, 650, 600, [
        k.tr("a. nenhuma porta aberta para dentro da AMT: o Sextante só abre ligações de saída para o Service Bus", "a. no inbound port into AMT: Sextante only opens outbound connections to Service Bus"),
        k.tr("b. ao D365 vão só linhas aceites, com a chave de idempotência da linha", "b. only accepted lines go to D365, with the line's idempotency key"),
        k.tr("c. a revisão continua no painel do Sextante; o D365 recebe o resultado", "c. review stays in Sextante's panel; D365 receives the result"),
    ], RED)


def production(k: Kit) -> None:
    k.title(k.tr("Produção segura", "Secure production"),
            k.tr("alvo para uso real · hoje: ShardCloud, um contentor, token partilhado", "target for real use · today: ShardCloud, one container, shared token"))
    k.legend([(k.tr("borda", "edge"), RED), (k.tr("aplicação", "application"), PURPLE), (k.tr("dados", "data"), BLUE), (k.tr("serviços", "services"), ORANGE)])
    k.people(30, 220, k.tr("revisores", "reviewers"))
    k.arrow([(130, 260), (168, 260)])
    k.box(170, 170, 170, 180, RED, "CLOUDFLARE / WAF", sub=k.tr("TLS · regras · limites · bots", "TLS · rules · limits · bots"), badge="1", size=15)
    k.arrow([(340, 260), (378, 260)])
    k.box(380, 200, 150, 120, GRAY, "PROXY", sub=k.tr("nginx · cabeçalhos SEC-11", "nginx · SEC-11 headers"), badge="2", size=15)
    k.group(570, 120, 420, 470, k.tr("rede privada", "private network"))
    k.arrow([(530, 230), (588, 200)])
    k.stack(590, 170, 170, 60, ORANGE, "API × N", badge="3")
    k.stack(590, 290, 170, 60, PURPLE, k.tr("TRABALHADORES × N", "WORKERS × N"), badge="4")
    k.box(800, 160, 170, 70, BLUE, "POSTGRESQL", sub=k.tr("gerido · cifrado · cópias", "managed · encrypted · backups"), badge="5", size=15)
    k.box(800, 270, 170, 70, BLUE, k.tr("OBJECTOS", "OBJECTS"), sub=k.tr("PDF privados · cifra por envelope", "private PDFs · envelope encryption"), badge="6", size=15)
    k.box(800, 380, 170, 70, RED, k.tr("COFRE", "VAULT"), sub=k.tr("segredos · rotação", "secrets · rotation"), badge="7", size=15)
    k.arrow([(760, 200), (798, 195)], BLUE, both=True)
    k.arrow([(760, 320), (798, 305)], BLUE, both=True)
    k.arrow([(675, 350), (675, 415), (798, 415)], RED, dashed=True)
    k.box(590, 470, 170, 60, GRAY, k.tr("PROXY DE SAÍDA", "EGRESS PROXY"), sub=k.tr("lista de destinos", "destination allowlist"), size=14)
    k.arrow([(640, 350), (640, 468)], GRAY)
    k.box(1050, 150, 220, 64, ORANGE, "ENTRA ID · OIDC", sub=k.tr("pessoas e perfis", "people and roles"), badge="8", size=15)
    k.box(1050, 290, 220, 64, YELLOW, "ANTHROPIC API", sub=k.tr("só pela saída controlada", "only through controlled egress"), size=15)
    k.box(1050, 430, 220, 64, GRAY, k.tr("OBSERVABILIDADE", "OBSERVABILITY"), sub=k.tr("métricas · alertas · logs sem dados", "metrics · alerts · logs without data"), badge="9", size=15)
    k.arrow([(760, 500), (1010, 500), (1010, 322), (1048, 322)], GRAY)
    k.arrow([(700, 158), (720, 132), (1030, 132), (1048, 170)], ORANGE, dashed=True)
    k.box(30, 640, 230, 60, GRAY, "GITHUB ACTIONS", sub=k.tr("testes · auditorias · Trivy", "tests · audits · Trivy"), size=15)
    k.arrow([(260, 670), (318, 670)])
    k.box(320, 640, 230, 60, GRAY, k.tr("REGISTO PRIVADO", "PRIVATE REGISTRY"), sub=k.tr("imagens por digest", "images by digest"), size=15)
    k.arrow([(550, 670), (608, 670)])
    k.box(610, 640, 230, 60, GRAY, k.tr("DEPLOY COM APROVAÇÃO", "DEPLOY WITH APPROVAL"), sub=k.tr("ambiente protegido", "protected environment"), size=15)
    k.arrow([(725, 640), (725, 592)], dashed=True)
    k.note(880, 620, 400, [
        k.tr("a. autor de cada revisão = a pessoa, não SEXTANTE_REVIEWER_ID", "a. author of each review = the person, not SEXTANTE_REVIEWER_ID"),
        k.tr("b. acordo de tratamento de dados com a Anthropic e o alojamento", "b. data processing agreements with Anthropic and the host"),
        k.tr("c. retenção definida (L-11) · limiares calibrados (L-02)", "c. retention defined (L-11) · thresholds calibrated (L-02)"),
    ], RED)


def capacity(k: Kit) -> None:
    k.title(k.tr("Capacidade: 5000 facturas por mês", "Capacity: 5000 invoices a month"),
            k.tr("como processa hoje · como cresce", "how it processes today · how it grows"))
    k.legend([(k.tr("hoje", "today"), PURPLE), (k.tr("para crescer", "to grow"), BLUE)])
    figures = [("5000", k.tr("por mês", "a month")), ("≈ 250", k.tr("por dia útil", "per working day")), ("≈ 32", k.tr("por hora, em 8 h", "per hour, over 8 h"))]
    for i, (big, small) in enumerate(figures):
        x = 40 + i * 300
        k.box(x, 120, 240, 90, GRAY, big, sub=small, size=30)
        if i < 2:
            k.arrow([(x + 240, 165), (x + 298, 165)])
    k.box(40, 280, 200, 70, ORANGE, k.tr("CARREGAMENTO", "UPLOAD"), sub=k.tr("lotes até 50 · resposta em ms", "batches up to 50 · answer in ms"), badge="1", size=15)
    k.arrow([(240, 315), (278, 315)])
    k.box(280, 280, 200, 70, BLUE, k.tr("FILA SQLITE", "SQLITE QUEUE"), sub=k.tr("ordem de chegada", "arrival order"), badge="2", size=15)
    k.arrow([(480, 315), (518, 315)])
    k.box(520, 280, 220, 70, PURPLE, k.tr("1 TRABALHADOR", "1 WORKER"), sub=k.tr("uma factura de cada vez · falha isolada", "one invoice at a time · isolated failure"), badge="3", size=15)
    k.arrow([(740, 315), (778, 315)])
    k.code(780, 262, 260, k.tr("POR FACTURA", "PER INVOICE"), [
        k.tr("extracção < 1 s", "extraction < 1 s"),
        k.tr("modelo: alguns s", "model: a few s"),
        k.tr("1 chamada", "1 call"),
    ], PURPLE)
    k.arrow([(1040, 315), (1078, 315)])
    k.box(1080, 280, 200, 70, ORANGE, k.tr("REVISÃO", "REVIEW"), sub=k.tr("só o que está sinalizado", "only what is flagged"), badge="4", size=15)
    k.text(k.tr("UM DIA ÚTIL (8 h)", "ONE WORKING DAY (8 h)"), 40, 410, 600, size=15, color=PURPLE[0])
    k.shape("rectangle", 40, 440, 1200, 46, GRAY, rounded=False)
    k.shape("rectangle", 40, 440, 75, 46, PURPLE, rounded=False)
    k.text(k.tr("< 30 min de processamento para 250 facturas · o resto do dia fica livre",
                "< 30 min of processing for 250 invoices · the rest of the day is free"), 130, 452, 1100, size=15)
    k.text(k.tr("tecto por omissão: 200 chamadas por hora, mais de 5 vezes a média · tokens registados por chamada",
                "default ceiling: 200 calls per hour, over 5 times the average · tokens recorded per call"), 40, 500, 1200, size=14, color=MUTED)
    k.text(k.tr("PARA CRESCER (por exemplo 50 000 por mês ou picos de fim de mês)", "TO GROW (for example 50 000 a month or month-end peaks)"), 40, 560, 1000, size=15, color=BLUE[0])
    grow = [
        ("POSTGRESQL", k.tr("N trabalhadores em paralelo; a reclamação já é atómica", "N workers in parallel; claiming is already atomic")),
        (k.tr("CONCORRÊNCIA", "CONCURRENCY"), k.tr("chamadas em paralelo dentro do tecto", "parallel calls within the ceiling")),
        ("BATCHES API", k.tr("metade do custo, resposta em horas", "half the cost, answers within hours")),
        (k.tr("EXTRACÇÃO EM POOL", "EXTRACTION POOL"), k.tr("processos isolados em paralelo", "isolated processes in parallel")),
        (k.tr("OBJECTOS", "OBJECTS"), k.tr("ficheiros fora do disco local", "files off local disk")),
    ]
    for i, (label, sub) in enumerate(grow):
        k.box(40 + i * 250, 600, 220, 90, BLUE, label, sub=sub, dashed=True, size=15)
