"""SYNTHETIC invoices for tests, modelled on the structure of the sample invoices.

Not real invoices (D-3.18, NFR-TST-001). Each one has the file bytes uploaded and the
extraction that FakeInvoiceExtractor returns for those bytes.
"""

import dataclasses
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from sextante.ingestion.contracts import (
    BilledEntityBlock,
    ExtractedInvoice,
    ExtractedLine,
    PartyIdentity,
    SummaryRow,
)

AMT_NAME: Final = "Advanced Maritime Transports - Transitarios Limitada"
AMT_NIF: Final = "5419990000"


@dataclass(frozen=True)
class SyntheticInvoice:
    """Bytes to upload, and the extraction the fake extractor returns for them."""

    file_name: str
    content: bytes
    extraction: ExtractedInvoice


def synthetic_pdf_bytes(label: str) -> bytes:
    """Bytes that start like a PDF, unique per label. Not a readable PDF.

    Example:
        synthetic_pdf_bytes("INV-001")
    """
    return b"%PDF-1.7\n% SYNTHETIC test invoice " + label.encode() + b"\n%%EOF\n"


def taag_air_ticket_to_amt() -> SyntheticInvoice:
    """Replica of the structure of sample INV-001: companhia aérea bills AMT for one air ticket.

    Example:
        invoice = taag_air_ticket_to_amt()
    """
    return SyntheticInvoice(
        file_name="INV-001_synthetic.pdf",
        content=synthetic_pdf_bytes("INV-001"),
        extraction=ExtractedInvoice(
            supplier=PartyIdentity(name="Companhia Aérea Sintética E.P.", nif="5419990001"),
            invoice_number="SYN-2026-001",
            invoice_date="2026-10-12",
            currency="AOA",
            billed_entities=(
                BilledEntityBlock(
                    name=AMT_NAME,
                    nif=AMT_NIF,
                    care_of=(),
                    address_lines=("Rua Sintética 1, Luanda, Angola",),
                ),
            ),
            lines=(
                ExtractedLine(
                    position=1,
                    description=(
                        "Passagem aérea Sintética - Rota Teste (Rotação equipa - Ref #SYN-0000001)"
                    ),
                    quantity=Decimal("1"),
                    unit_price=Decimal("320000.00"),
                    vat_rate=Decimal("0"),
                    amount=Decimal("320000.00"),
                ),
            ),
            summary_rows=(
                SummaryRow(label="Subtotal", amount=Decimal("320000.00")),
                SummaryRow(label="Tax / IVA", amount=Decimal("0.00")),
                SummaryRow(label="TOTAL", amount=Decimal("320000.00")),
            ),
            notes="Nota sintética: isento de IVA para efeitos de teste.",
        ),
    )


def hotel_stay_to_amt() -> SyntheticInvoice:
    """Replica of the structure of sample INV-009: two lines, both coded against OUTLAYS.

    Example:
        invoice = hotel_stay_to_amt()
    """
    lines = (
        ("Alojamento de 2 noites - Quarto Sintético (Visitante de teste)", "390000.00", "7"),
        ("Serviço de restaurante sintético", "65000.00", "0"),
    )
    return SyntheticInvoice(
        file_name="INV-009_Hotel_synthetic.pdf",
        content=synthetic_pdf_bytes("INV-009"),
        extraction=ExtractedInvoice(
            supplier=PartyIdentity(name="Hotel Sintético Luanda", nif="5419990006"),
            invoice_number="HTL-SYN-0001",
            invoice_date="2026-10-22",
            currency="AOA",
            billed_entities=(
                BilledEntityBlock(name=AMT_NAME, nif=AMT_NIF, care_of=(), address_lines=()),
            ),
            lines=tuple(
                ExtractedLine(
                    position=index,
                    description=description,
                    quantity=Decimal("1"),
                    unit_price=Decimal(amount),
                    vat_rate=Decimal(vat),
                    amount=Decimal(amount),
                )
                for index, (description, amount, vat) in enumerate(lines, start=1)
            ),
            summary_rows=(),
            notes="",
        ),
    )


def billed_to(
    label: str, name: str | None, nif: str | None = None, care_of: tuple[str, ...] = ()
) -> SyntheticInvoice:
    """The INV-001 replica, billed to another entity (or to none, when ``name`` is None).

    Example:
        invoice = billed_to("INV-004", "Petrolífera Sintética de Cabinda Lda", "5419990003")
    """
    base = taag_air_ticket_to_amt()
    blocks = (
        ()
        if name is None
        else (BilledEntityBlock(name=name, nif=nif, care_of=care_of, address_lines=()),)
    )
    extraction = dataclasses.replace(
        base.extraction, billed_entities=blocks, invoice_number=f"{label}-SYN"
    )
    return SyntheticInvoice(f"{label}_synthetic.pdf", synthetic_pdf_bytes(label), extraction)
