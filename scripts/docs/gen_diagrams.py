"""Generate the Excalidraw diagrams of the technical documentation, in Portuguese and English.

Each diagram is a function of a ``Kit``; the .excalidraw files are the editable sources
and ``render_diagrams.mjs`` turns them into the SVGs the documents show (CLAUDE.md,
section «Diagramas»: a design change edits this script and regenerates).

Usage, from the repository root:
    python3 scripts/docs/gen_diagrams.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import figures  # noqa: E402
from diagram_kit import BLUE, GRAY, GREEN, MUTED, ORANGE, PURPLE, RED, YELLOW, Kit  # noqa: E402

OUT = Path("docs/diagramas/documentacao")


def architecture(k: Kit) -> None:
    k.title(k.tr("Sextante · arquitectura", "Sextante · architecture"),
            k.tr("visão geral · o que está construído", "high-level design · what is built"))
    k.legend([(k.tr("1–2 entrada", "1–2 entry"), ORANGE), (k.tr("3–4 processamento", "3–4 processing"), PURPLE),
              (k.tr("5 modelo", "5 model"), YELLOW), (k.tr("6–7 dados", "6–7 data"), BLUE)])
    k.people(40, 250, k.tr("revisores AMT", "AMT reviewers"))
    k.box(40, 470, 120, 64, GRAY, k.tr("programas", "programs"), sub="X-API-Key", size=15)
    k.box(200, 150, 110, 400, GRAY, "nginx", sub=k.tr("TLS\ncabeçalhos\nSEC-11", "TLS\nheaders\nSEC-11"))
    k.arrow([(140, 290), (198, 290)])
    k.arrow([(160, 502), (198, 502)])
    k.box(370, 160, 230, 58, ORANGE, k.tr("PAINEL REACT", "REACT PANEL"), badge="1")
    k.text(k.tr("páginas estáticas · EN e PT · sessão em cookie HttpOnly",
                "static pages · EN and PT · session in an HttpOnly cookie"), 370, 224, 240, size=13)
    k.box(370, 330, 230, 58, ORANGE, k.tr("API FASTAPI", "FASTAPI API"), badge="2")
    k.arrow([(310, 189), (368, 189)])
    k.arrow([(310, 359), (368, 359)])
    k.note(370, 420, 262, [
        k.tr("a. autentica: chave ou sessão", "a. authenticates: key or session"),
        k.tr("b. limita a taxa por credencial", "b. rate-limits per credential"),
        k.tr("c. valida o corpo (extra=forbid)", "c. validates the body (extra=forbid)"),
        k.tr("d. grava o PDF, cria o trabalho", "d. stores the PDF, creates the job"),
        k.tr("e. responde já com o job_id", "e. answers at once with the job_id"),
    ], ORANGE, badge="2")
    k.note(680, 110, 290, [
        k.tr("a. reclama um trabalho: UPDATE … WHERE status='queued'", "a. claims a job: UPDATE … WHERE status='queued'"),
        k.tr("b. extrai o PDF num subprocesso", "b. extracts the PDF in a subprocess"),
        k.tr("c. entidade → aba → scores lexicais", "c. entity → sheet → lexical scores"),
        k.tr("d. uma chamada ao modelo por factura", "d. one model call per invoice"),
        k.tr("e. regras: confiança, recurso, sinalizações", "e. rules: confidence, fallback, flags"),
    ], PURPLE, badge="3")
    k.box(680, 330, 230, 58, PURPLE, k.tr("TRABALHADOR", "WORKER"), badge="3")
    k.arrow([(600, 345), (640, 345), (640, 300), (985, 300), (985, 318)], BLUE)
    k.text(k.tr("INSERT trabalho, factura", "INSERT job, invoice"), 700, 276, 240, size=13, color=BLUE)
    k.arrow([(910, 365), (968, 365)], BLUE, both=True)
    k.text(k.tr("reclama /\ngrava", "claim /\nsave"), 916, 374, 60, size=13, color=BLUE)
    k.box(680, 470, 190, 58, PURPLE, k.tr("EXTRACÇÃO\nISOLADA", "ISOLATED\nEXTRACTION"), badge="4", size=15)
    k.text(k.tr("subprocesso · 512 MiB · 30 s\nsó PDF com camada de texto", "subprocess · 512 MiB · 30 s\nPDF with a text layer only"),
           680, 534, 230, size=13)
    k.arrow([(760, 388), (760, 468)])
    k.box(680, 650, 230, 58, YELLOW, "CLAUDE SONNET 5.5", badge="5")
    k.arrow([(895, 388), (895, 648)], both=True)
    k.text(k.tr("uma chamada\npor factura", "one call\nper invoice"), 902, 560, 120, size=13)
    k.group(660, 620, 290, 140, "Anthropic API · HTTPS")
    k.table(980, 330, 290, "SQLite (WAL)", [
        "job · invoice · invoice_header",
        "invoice_line · entity_resolution",
        "encoded_line · lexical_score",
        "line_flag · model_call",
        "line_review · audit_event",
        "idempotency_record",
    ], colors=BLUE, framed=True, badge="6")
    k.listing(980, 110, 300, k.tr("ÍNDICES E RESTRIÇÕES", "INDEXES AND CONSTRAINTS"), [
        k.tr("1. UNIQUE invoice(content_digest): dedup", "1. UNIQUE invoice(content_digest): dedup"),
        "2. UNIQUE invoice_line(invoice_id, position)",
        k.tr("3. UNIQUE encoded_line em vigor (superseded_at nulo)", "3. UNIQUE encoded_line in force (superseded_at null)"),
        k.tr("4. invoice_header(supplier_key, invoice_number): duplicados", "4. invoice_header(supplier_key, invoice_number): duplicates"),
    ])
    k.code(980, 600, 290, k.tr("FRONTEIRA DO MODELO (SEC-14)", "MODEL BOUNDARY (SEC-14)"), [
        "{line_position, candidate_index|null}",
        k.tr("0 ≤ índice < len(candidatos)", "0 ≤ index < len(candidates)"),
        k.tr("item ∈ aba da linha", "item ∈ line's sheet"),
        k.tr("senão: LOW + model_response_invalid", "else: LOW + model_response_invalid"),
    ])
    k.box(370, 650, 230, 58, BLUE, k.tr("CATÁLOGO + EXCLUSÃO", "CATALOG + DENYLIST"), badge="7", size=15)
    k.text(k.tr("XLSX e YAML só de leitura · digest em cada decisão", "read-only XLSX and YAML · digest in every decision"),
           370, 714, 240, size=13)
    k.arrow([(600, 679), (640, 679), (640, 420), (678, 420), (678, 392)], BLUE, dashed=True)
    k.text(k.tr("ⓘ  nada da factura entra nos logs: só identificadores, scores, digests e classificações (SEC-15)",
                "ⓘ  nothing from the invoice enters the logs: only identifiers, scores, digests and classifications (SEC-15)"),
           40, 790, 1000, size=14, color=MUTED)


DIAGRAMS = {
    "01-arquitectura": architecture,
}


DIAGRAMS.update({
    "02-percurso-factura": figures.pipeline,
    "03-entidade": figures.entity,
    "04-modelo-tokens": figures.model_call,
    "05-decisao-linha": figures.line_decision,
    "06-revisao": figures.review,
    "07-integracao": figures.integration,
    "08-hibrido-d365": figures.hybrid,
    "09-producao": figures.production,
    "10-capacidade": figures.capacity,
})


def main() -> None:
    only = set(sys.argv[1:])
    for language in ("pt", "en"):
        for name, draw in DIAGRAMS.items():
            if only and name not in only:
                continue
            kit = Kit(language)
            draw(kit)
            kit.save(OUT / language / f"{name}.excalidraw")
            print(f"{OUT / language / name}.excalidraw  {len(kit.elements)}")


if __name__ == "__main__":
    main()
