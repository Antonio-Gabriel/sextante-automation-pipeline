"""Invoice_ID of the export: supplier and invoice number (REQ-EXP-006, D-3.10)."""

from typing import Final

from sextante.platform.text_normalization import digits_only, fold_for_matching

SHORT_DIGEST_LENGTH: Final = 12


def invoice_identifier(
    supplier_nif: str | None, supplier_name: str | None, number: str | None, digest: str
) -> str:
    """Return ``<supplier>/<number>``; a short file digest stands in for a missing number.

    The supplier is its NIF when one was extracted, otherwise its normalized name, and
    is left out when neither exists. Never a counter: it would not survive reprocessing.

    Example:
        invoice_identifier("5419990001", "companhia aérea", "SYN-2026-001", digest)
        # "5419990001/SYN-2026-001"
    """
    reference = number.strip() if number and number.strip() else digest[:SHORT_DIGEST_LENGTH]
    supplier = _supplier_key(supplier_nif, supplier_name)
    return f"{supplier}/{reference}" if supplier else reference


def _supplier_key(supplier_nif: str | None, supplier_name: str | None) -> str | None:
    digits = digits_only(supplier_nif)
    if digits:
        return digits
    return fold_for_matching(supplier_name) if supplier_name else None
