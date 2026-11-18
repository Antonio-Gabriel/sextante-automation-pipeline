"""Routing of an invoice to a target sheet (R2, REQ-MAP-001)."""

from collections.abc import Sequence

from sextante.catalog.contracts import TargetSheet
from sextante.ingestion.contracts import BilledEntityBlock


def route_invoice(
    billed_entities: Sequence[BilledEntityBlock], target_entity_name: str
) -> TargetSheet | None:
    """Return OUTLAYS when the invoice is billed to the target entity, otherwise None.

    Only the exact name is recognised here. The full entity check (normalization,
    denylist, NIF veto, OUTLAYSP routing) arrives with ticket 03; until then any other
    entity is left uncoded rather than routed by guess.

    Example:
        route_invoice(blocks, "Advanced Maritime Transports - Transitarios Limitada")
    """
    if len(billed_entities) != 1:
        return None
    if billed_entities[0].name.strip() != target_entity_name:
        return None
    return TargetSheet.OUTLAYS
