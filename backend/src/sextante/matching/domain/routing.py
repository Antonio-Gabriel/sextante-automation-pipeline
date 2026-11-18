"""Routing of an invoice to a target sheet, from the entity verdict (R2, REQ-MAP-001)."""

from sextante.catalog.contracts import TargetSheet
from sextante.matching.domain.entity_check import EntityVerdict


def target_sheet_for(verdict: EntityVerdict) -> TargetSheet | None:
    """MATCH goes to OUTLAYS, NO_MATCH to OUTLAYSP; AMBIGUOUS has no sheet (D-3.15).

    Routing is a plain rule of the statement, never decided by the model.

    Example:
        target_sheet_for(EntityVerdict.NO_MATCH)  # TargetSheet.OUTLAYSP
    """
    if verdict is EntityVerdict.MATCH:
        return TargetSheet.OUTLAYS
    if verdict is EntityVerdict.NO_MATCH:
        return TargetSheet.OUTLAYSP
    return None
