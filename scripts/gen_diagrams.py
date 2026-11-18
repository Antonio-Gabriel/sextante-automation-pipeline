"""Generate the two Sextante diagrams: editable Excalidraw sources and SVG renderings.

The .excalidraw files go to docs/diagramas/ and the .svg renderings to assets/. Both come
from the same element list, so a design change edits this script and regenerates both;
nothing is exported or edited by hand (CLAUDE.md, section «Diagramas»).

Usage, from the repository root:
    python3 scripts/gen_diagrams.py
"""

import json
from html import escape
from pathlib import Path

OUT = Path("./docs/diagramas")
OUT.mkdir(parents=True, exist_ok=True)
SVG_OUT = Path("./assets")
SVG_OUT.mkdir(parents=True, exist_ok=True)
SVG_MARGIN = 30
FONT_FAMILIES = {
    1: "Virgil, 'Segoe Print', 'Comic Sans MS', cursive",
    2: "Helvetica, Arial, sans-serif",
    3: "'Cascadia Code', Consolas, monospace",
}

BLUE = ("#1971c2", "#e7f5ff")
YELLOW = ("#f59f00", "#fff9db")
GREEN = ("#2f9e44", "#d3f9d8")
PURPLE = ("#862e9c", "#f3d9fa")
RED = ("#c92a2a", "#ffe3e3")
GRAY = ("#495057", "#f8f9fa")

DARK = "#1e1e1e"
MUTED = "#868e96"

_seq = [0]


def _nid(prefix: str) -> str:
    _seq[0] += 1
    return f"{prefix}-{_seq[0]}"


def base(kind: str, x: float, y: float, w: float, h: float, **over) -> dict:
    element = {
        "id": _nid(kind),
        "type": kind,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "angle": 0,
        "strokeColor": DARK,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
    }
    element.update(over)
    return element


def rect(x, y, w, h, colors, *, radius=True, stroke_width=2, style="solid") -> dict:
    return base(
        "rectangle",
        x,
        y,
        w,
        h,
        strokeColor=colors[0],
        backgroundColor=colors[1],
        strokeWidth=stroke_width,
        strokeStyle=style,
        roundness={"type": 3} if radius else None,
    )


def text(value, x, y, w, *, size=16, color=DARK, align="center", family=1) -> dict:
    lines = value.count("\n") + 1
    return base(
        "text",
        x,
        y,
        w,
        round(size * 1.25 * lines),
        strokeColor=color,
        text=value,
        originalText=value,
        fontSize=size,
        fontFamily=family,
        textAlign=align,
        verticalAlign="top",
        containerId=None,
        lineHeight=1.25,
    )


def arrow(x, y, dx, dy, color=DARK, *, style="solid") -> dict:
    return base(
        "arrow",
        x,
        y,
        abs(dx),
        abs(dy),
        strokeColor=color,
        strokeStyle=style,
        roundness={"type": 2},
        points=[[0, 0], [dx, dy]],
        lastCommittedPoint=None,
        startBinding=None,
        endBinding=None,
        startArrowhead=None,
        endArrowhead="arrow",
    )


def wrap(elements: list[dict]) -> dict:
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"},
        "files": {},
    }


def labelled_box(x, y, w, h, colors, title, note, *, stroke_width=2):
    out = [rect(x, y, w, h, colors, stroke_width=stroke_width)]
    out.append(text(title, x, y + 9, w, size=16))
    if note:
        out.append(text(note, x, y + 32, w, size=12, color=MUTED))
    return out


# ---------------------------------------------------------------- diagram 1
def flow_diagram() -> dict:
    els: list[dict] = []
    col_x, col_w = 60, 380
    side_x, side_w = 520, 260
    pitch, box_h = 96, 60
    top = 128

    els.append(text("Sextante · fluxo de codificação de uma factura", 60, 24, 720, size=26))
    els.append(
        text(
            "Amarelo: decidido em código   ·   Violeta: decidido pelo Claude   ·   "
            "Vermelho: devolvido ao humano",
            60,
            66,
            720,
            size=13,
            color=MUTED,
        )
    )
    els.append(
        text(
            "O Claude entra num só ponto, a escolha do item, e não devolve um código de item.",
            60,
            88,
            720,
            size=13,
            color=MUTED,
        )
    )

    # Revised on 2026-11-18 (00-decisoes-e-lacunas.md §3.15 to §3.18): the entity check
    # no longer uses the model, and the model receives the whole target sheet.
    steps = [
        (BLUE, "1 · Carregamento", "PDF ou XLSX, pela API", 2),
        (YELLOW, "2 · Tipo real e digest", "primeiros bytes, SHA-256, idempotência", 2),
        (YELLOW, "3 · Extracção", "PDF nativo no modelo das amostras", 2),
        (YELLOW, "4 · Normalização e tipo de linha", "NFC · service / tax / discount", 2),
        (YELLOW, "5 · Verificação de entidade", "exclusão, veto pelo NIF, igualdade", 2),
        (YELLOW, "6 · Encaminhamento", "MATCH: OUTLAYS · NO_MATCH: OUTLAYSP", 2),
        (YELLOW, "7 · Pontuação lexical", "todos os itens da aba, PT e EN", 2),
        (PURPLE, "8 · Escolha do item", "Claude devolve o índice na aba inteira", 2),
        (YELLOW, "9 · Validação da escolha", "esquema, índice na lista, item na aba", 4),
        (YELLOW, "10 · Recurso ou vazio", "O00999 só em OUTLAYSP, senão vazio", 2),
        (YELLOW, "11 · Confiança", "topo lexical, score e distância", 2),
        (GREEN, "12 · Persistência e auditoria", "scores, modelo, prompt, digest", 2),
        (GREEN, "13 · Revisão e exportação", "CSV e XLSX com as nove colunas", 2),
    ]

    for index, (colors, title, note, width) in enumerate(steps):
        y = top + index * pitch
        els += labelled_box(col_x, y, col_w, box_h, colors, title, note, stroke_width=width)
        if index < len(steps) - 1:
            els.append(arrow(col_x + col_w / 2, y + box_h, 0, pitch - box_h - 6))

    def side(step_index, colors, title, note, label):
        y = top + step_index * pitch
        els.append(arrow(col_x + col_w, y + box_h / 2, side_x - col_x - col_w, 0, colors[0]))
        els.append(
            text(label, col_x + col_w, y + box_h / 2 - 20, side_x - col_x - col_w, size=11, color=MUTED)
        )
        els.extend(labelled_box(side_x, y, side_w, box_h, colors, title, note))

    side(2, RED, "Recusado, sem codificar", "PDF sem texto ou outro documento", "recusa")
    side(4, RED, "Resolução de entidade", "ambígua: decide um revisor, L-13", "ambígua")
    side(8, RED, "Sem código, LOW, revisão", "resposta fora do esquema ou da aba", "inválida")
    side(9, RED, "Vazio, LOW, revisão", "sem correspondência em OUTLAYS, L-08", "OUTLAYS")

    note_y = top + len(steps) * pitch + 20
    els.append(rect(60, note_y, 720, 92, GRAY))
    els.append(text("O controlo do passo 9 é o que sustenta a regra R13", 60, note_y + 12, 720, size=16))
    els.append(
        text(
            "O conteúdo de uma factura é dado de origem externa e chega ao prompt. "
            "Como o Claude só devolve um índice\nda lista que o servidor construiu, e esse "
            "índice é validado antes de ser usado, uma instrução escondida numa\n"
            "descrição de factura não consegue atribuir um código que o catálogo não tenha.",
            60,
            note_y + 38,
            720,
            size=12,
            color=MUTED,
        )
    )
    return wrap(els)


# ---------------------------------------------------------------- diagram 2
def modules_diagram() -> dict:
    els: list[dict] = []
    els.append(text("Sextante · módulos, camadas e portas", 40, 24, 1000, size=26))
    els.append(
        text(
            "Um processo, módulos com fronteira explícita. A dependência aponta sempre para dentro.",
            40,
            64,
            1000,
            size=13,
            color=MUTED,
        )
    )

    outer_x, outer_y, outer_w = 40, 100, 1000
    mod_w, mod_gap = 182, 15
    mod_x0 = outer_x + 18
    layer_h, layer_gap = 48, 9
    layers_y = outer_y + 92

    modules = [
        ("ingestion", "carregar, extrair"),
        ("catalog", "abas e comparação"),
        ("matching", "entidade e item"),
        ("review", "revisão e resultados"),
        ("export", "CSV e XLSX"),
    ]
    layers = [
        ("api", BLUE, "HTTP, validação, serialização"),
        ("application", YELLOW, "orquestra, abre transacção"),
        ("domain", GREEN, "regras, sem I/O"),
        ("infrastructure", GRAY, "SQLite, ficheiros, Claude"),
    ]

    outer_h = 92 + len(layers) * (layer_h + layer_gap) + 10
    els.append(rect(outer_x, outer_y, outer_w, outer_h, GRAY, stroke_width=3))
    els.append(text("sextante · processo único FastAPI", outer_x, outer_y + 12, outer_w, size=19))
    els.append(
        text(
            "a comunicação entre módulos passa por contracts, nunca pelo modelo interno do vizinho",
            outer_x,
            outer_y + 40,
            outer_w,
            size=12,
            color=MUTED,
        )
    )

    for m_index, (mod_name, mod_note) in enumerate(modules):
        mx = mod_x0 + m_index * (mod_w + mod_gap)
        els.append(text(mod_name, mx, layers_y - 36, mod_w, size=16, family=3))
        els.append(text(mod_note, mx, layers_y - 17, mod_w, size=11, color=MUTED))
        for l_index, (layer_name, colors, _) in enumerate(layers):
            ly = layers_y + l_index * (layer_h + layer_gap)
            els.append(rect(mx, ly, mod_w, layer_h, colors))
            els.append(text(layer_name, mx, ly + 14, mod_w, size=14, family=3))

    legend_y = layers_y + len(layers) * (layer_h + layer_gap) + 22
    els.append(text("camadas, de fora para dentro", outer_x, legend_y, 360, size=14, align="left"))
    for l_index, (layer_name, colors, note) in enumerate(layers):
        ly = legend_y + 26 + l_index * 26
        els.append(rect(outer_x + 4, ly, 16, 16, colors, radius=False))
        els.append(
            text(f"{layer_name} — {note}", outer_x + 30, ly - 1, 420, size=12, align="left", color=MUTED)
        )

    plat_y = legend_y + 26
    plat_x, plat_w = 520, 520
    els.append(rect(plat_x, plat_y, plat_w, 120, PURPLE, stroke_width=3))
    els.append(text("platform · transversal a todos os módulos", plat_x, plat_y + 12, plat_w, size=16))
    els.append(
        text(
            "Clock · IdentifierGenerator · Settings · logging estruturado\n"
            "limites de validação · idempotência · tratador global de erros",
            plat_x,
            plat_y + 40,
            plat_w,
            size=12,
            color=MUTED,
        )
    )

    ports_y = plat_y + 150
    els.append(text("portas do projecto e o que as implementa", 40, ports_y, 1000, size=19))
    els.append(
        text(
            "cada porta tem uma implementação real e um duplo nomeado em tests/fakes, "
            "para que nenhum teste chame a rede",
            40,
            ports_y + 28,
            1000,
            size=12,
            color=MUTED,
        )
    )

    # EntityTiebreaker was removed and CandidateRetriever became LexicalScorer
    # (04-padroes-de-codigo.md §4, revised on 2026-11-18).
    ports = [
        (BLUE, "InvoiceExtractor", "pdfplumber · PDF nativo"),
        (BLUE, "OpticalCharacterRecognizer", "não implementada · L-01"),
        (YELLOW, "LexicalScorer", "rapidfuzz · aba inteira"),
        (PURPLE, "ItemClassifier", "Claude · devolve índice"),
        (GREEN, "EncodedResultRepository", "SQLite · SQLAlchemy"),
        (GREEN, "AuditEventRepository", "só inserção · gatilhos"),
        (GREEN, "InvoiceFileStore", "disco local, nome do servidor"),
        (GREEN, "ResultExporter", "CSV com BOM · XLSX"),
    ]
    port_w, port_h, port_gap = 237, 66, 17
    for p_index, (colors, name, impl) in enumerate(ports):
        row, col = divmod(p_index, 4)
        px = 40 + col * (port_w + port_gap)
        py = ports_y + 58 + row * (port_h + port_gap)
        els.append(rect(px, py, port_w, port_h, colors))
        els.append(text(name, px, py + 10, port_w, size=13, family=3))
        els.append(text(impl, px, py + 34, port_w, size=11, color=MUTED))

    ext_y = ports_y + 58 + 2 * (port_h + port_gap) + 34
    els.append(text("fora do processo", 40, ext_y, 1000, size=19))
    externals = [
        (BLUE, "API da Anthropic", "único destino de rede saído"),
        (GREEN, "sextante.db", "SQLite com WAL"),
        (GREEN, "catálogo .xlsx", "lido uma vez, versionado por digest"),
        (GRAY, "uploads/", "fora da árvore servida"),
    ]
    for e_index, (colors, name, note) in enumerate(externals):
        ex = 40 + e_index * (port_w + port_gap)
        ey = ext_y + 36
        els.append(rect(ex, ey, port_w, port_h, colors, style="dashed"))
        els.append(text(name, ex, ey + 10, port_w, size=13))
        els.append(text(note, ex, ey + 34, port_w, size=11, color=MUTED))

    return wrap(els)


def to_svg(payload: dict) -> str:
    """Render the rectangles, texts and arrows of an Excalidraw payload as SVG.

    Example:
        Path("assets/fluxo-codificacao.svg").write_text(to_svg(flow_diagram()))
    """
    elements = payload["elements"]
    width = max(e["x"] + e["width"] for e in elements) + SVG_MARGIN
    height = max(e["y"] + e["height"] for e in elements) + SVG_MARGIN
    body = "\n".join(_svg_element(e) for e in elements)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}">\n'
        '<defs><marker id="head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
        'fill="context-stroke"/></marker></defs>\n'
        f'<rect width="100%" height="100%" fill="#ffffff"/>\n{body}\n</svg>\n'
    )


def _svg_element(element: dict) -> str:
    renderers = {"rectangle": _svg_rect, "text": _svg_text, "arrow": _svg_arrow}
    return renderers[element["type"]](element)


def _svg_dash(element: dict) -> str:
    return ' stroke-dasharray="8 6"' if element["strokeStyle"] == "dashed" else ""


def _svg_rect(element: dict) -> str:
    radius = 8 if element["roundness"] else 0
    return (
        f'<rect x="{element["x"]}" y="{element["y"]}" width="{element["width"]}" '
        f'height="{element["height"]}" rx="{radius}" fill="{element["backgroundColor"]}" '
        f'stroke="{element["strokeColor"]}" stroke-width="{element["strokeWidth"]}"'
        f"{_svg_dash(element)}/>"
    )


def _svg_text(element: dict) -> str:
    size = element["fontSize"]
    centered = element["textAlign"] == "center"
    x = element["x"] + element["width"] / 2 if centered else element["x"]
    lines = element["text"].split("\n")
    spans = "".join(
        f'<tspan x="{x}" y="{element["y"] + size * 0.95 + index * size * 1.25:.1f}">'
        f"{escape(line)}</tspan>"
        for index, line in enumerate(lines)
    )
    return (
        f'<text font-family="{escape(FONT_FAMILIES[element["fontFamily"]])}" '
        f'font-size="{size}" fill="{element["strokeColor"]}" '
        f'text-anchor="{"middle" if centered else "start"}">{spans}</text>'
    )


def _svg_arrow(element: dict) -> str:
    (start_x, start_y), (dx, dy) = element["points"]
    x1, y1 = element["x"] + start_x, element["y"] + start_y
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x1 + dx}" y2="{y1 + dy}" '
        f'stroke="{element["strokeColor"]}" stroke-width="{element["strokeWidth"]}"'
        f'{_svg_dash(element)} marker-end="url(#head)"/>'
    )


for stem, builder in (
    ("fluxo-codificacao", flow_diagram),
    ("arquitectura-modulos", modules_diagram),
):
    payload = builder()
    path = OUT / f"{stem}.excalidraw"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    svg_path = SVG_OUT / f"{stem}.svg"
    svg_path.write_text(to_svg(payload), encoding="utf-8")
    print(f"{path}  {len(payload['elements'])} elementos  ·  {svg_path}")
