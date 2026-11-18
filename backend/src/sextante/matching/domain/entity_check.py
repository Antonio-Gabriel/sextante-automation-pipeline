"""Billed entity check: MATCH, NO_MATCH or AMBIGUOUS, with no language model (D-3.15).

The rule order is the point of this module. The denylist comes first, because a sister
company of a freight forwarder usually shares the parent's name and similarity alone
would accept it (R4, REQ-ENT-003). The NIF vetoes a match before name equality is
looked at (REQ-ENT-007). Anything that only a human can decide is AMBIGUOUS.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from rapidfuzz import fuzz

from sextante.ingestion.contracts import BilledEntityBlock
from sextante.platform.text_normalization import fold_for_matching

# Provisional until the golden set calibrates it (L-02). Measured on the samples: third
# parties score below 40, names close to AMT's score above 70.
ENTITY_SIMILARITY_LOW: Final = 60
CORPORATE_SUFFIXES: Final = frozenset({"limitada", "lda", "ltda"})


class EntityVerdict(StrEnum):
    """Result of the entity check (REQ-ENT-004)."""

    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    AMBIGUOUS = "AMBIGUOUS"


class AmbiguityReason(StrEnum):
    """Why an entity is ambiguous. These are also flag reasons (REQ-CNF-004)."""

    ENTITY_LABEL_NOT_FOUND = "entity_label_not_found"
    MULTIPLE_BILLED_ENTITIES = "multiple_billed_entities"
    ENTITY_SIMILAR_NOT_EQUAL = "entity_similar_not_equal"
    ENTITY_NIF_MISMATCH = "entity_nif_mismatch"


@dataclass(frozen=True, slots=True)
class TargetEntity:
    """The entity whose invoices route to OUTLAYS: AMT, from configuration (REQ-ENT-001)."""

    name: str
    nif: str


@dataclass(frozen=True, slots=True)
class EntityCheckResult:
    """The verdict and, when AMBIGUOUS, the reason."""

    verdict: EntityVerdict
    reason: AmbiguityReason | None = None


def normalize_entity_name(name: str) -> str:
    """Fold the name and drop a trailing corporate suffix (R5, REQ-ENT-002).

    Example:
        normalize_entity_name("ADVANCED MARITIME TRANSPORTS TRANSITARIOS LDA")
        # "advanced maritime transports transitarios"
    """
    words = fold_for_matching(name).split()
    while words and words[-1] in CORPORATE_SUFFIXES:
        words.pop()
    return " ".join(words)


def check_billed_entity(
    blocks: Sequence[BilledEntityBlock], target: TargetEntity, denylist: frozenset[str]
) -> EntityCheckResult:
    """Apply the seven rules of D-3.15, in order. "Care of" lines never take part.

    Example:
        check_billed_entity(extraction.billed_entities, amt, denylist).verdict  # MATCH

    ``denylist`` holds names as written in configuration; they are normalized here.
    """
    if not blocks:
        return EntityCheckResult(EntityVerdict.AMBIGUOUS, AmbiguityReason.ENTITY_LABEL_NOT_FOUND)
    if len(blocks) > 1:
        return EntityCheckResult(EntityVerdict.AMBIGUOUS, AmbiguityReason.MULTIPLE_BILLED_ENTITIES)
    name = normalize_entity_name(blocks[0].name)
    if name in {normalize_entity_name(entry) for entry in denylist}:
        return EntityCheckResult(EntityVerdict.NO_MATCH)
    same_name = name == normalize_entity_name(target.name)
    if _nif_differs(blocks[0].nif, target.nif) and same_name:
        return EntityCheckResult(EntityVerdict.AMBIGUOUS, AmbiguityReason.ENTITY_NIF_MISMATCH)
    if same_name and not _nif_differs(blocks[0].nif, target.nif):
        return EntityCheckResult(EntityVerdict.MATCH)
    return _by_similarity(name, normalize_entity_name(target.name))


def _nif_differs(extracted_nif: str | None, target_nif: str) -> bool:
    # An absent NIF neither vetoes nor confirms: only a present, different one vetoes.
    if extracted_nif is None:
        return False
    return _digits(extracted_nif) != _digits(target_nif)


def _digits(nif: str) -> str:
    return "".join(character for character in nif if character.isdigit())


def _by_similarity(name: str, target_name: str) -> EntityCheckResult:
    # token_sort_ratio, never token_set_ratio: a name contained in the target must not
    # score 100 (D-3.15).
    if fuzz.token_sort_ratio(name, target_name) < ENTITY_SIMILARITY_LOW:
        return EntityCheckResult(EntityVerdict.NO_MATCH)
    return EntityCheckResult(EntityVerdict.AMBIGUOUS, AmbiguityReason.ENTITY_SIMILAR_NOT_EQUAL)
