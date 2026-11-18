"""How a supplier is identified across invoices (D-3.10, REQ-EXP-006, REQ-ING-011)."""

from sextante.platform.text_normalization import digits_only, fold_for_matching


def supplier_key(supplier_nif: str | None, supplier_name: str | None) -> str | None:
    """Return the supplier's NIF digits when extracted, otherwise its folded name, or None.

    Shared by the export's Invoice_ID and the possible-duplicate check, so both agree on
    what "the same supplier" means.

    Example:
        supplier_key("541-999-0001", "companhia aérea")  # "5419990001"
    """
    digits = digits_only(supplier_nif)
    if digits:
        return digits
    return fold_for_matching(supplier_name) if supplier_name else None
