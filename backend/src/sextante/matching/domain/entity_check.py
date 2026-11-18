"""Billed entity check: MATCH, NO_MATCH or AMBIGUOUS, with no language model (D-3.15).

The rule order is the point of this module. The denylist comes first, because a sister
company of a freight forwarder usually shares the parent's name and similarity alone
would accept it (R4, REQ-ENT-003). The NIF vetoes a match before name equality is
looked at (REQ-ENT-007). Anything that only a human can decide is AMBIGUOUS.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from rapidfuzz import fuzz

from sextante.ingestion.contracts import BilledEntityBlock
from sextante.matching.domain.line_decision import FlagReason
from sextante.platform.errors import DomainError
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


class EntityVerdictWithoutReasonError(DomainError):
    """An AMBIGUOUS verdict reached the caller without its reason: a defect, never a gap."""


@dataclass(frozen=True, slots=True)
class TargetEntity:
    """The entity whose invoices route to OUTLAYS: AMT, from configuration (REQ-ENT-001)."""

    name: str
    nif: str


@dataclass(frozen=True, slots=True)
class EntityCheckResult:
    """The verdict and, when AMBIGUOUS, the flag that says why."""

    verdict: EntityVerdict
    reason: FlagReason | None = None

    def ambiguity_flag(self) -> FlagReason:
        """Return the reason of an AMBIGUOUS verdict.

        Example:
            result.ambiguity_flag()  # FlagReason.ENTITY_NIF_MISMATCH

        Raises:
            EntityVerdictWithoutReasonError: when there is no reason to return.
        """
        if self.reason is None:
            raise EntityVerdictWithoutReasonError(
                f"Entity verdict {self.verdict} has no reason. Expected one for AMBIGUOUS."
            )
        return self.reason


@dataclass(frozen=True, slots=True)
class EntityDenylist:
    """Denylisted names, normalized once when the list is loaded (REQ-ENT-003).

    Example:
        EntityDenylist.of(["AMT - Agentes de Navegação Lda"])
    """

    normalized_names: frozenset[str]

    @classmethod
    def of(cls, names: Iterable[str]) -> "EntityDenylist":
        """Build the denylist from names as written in configuration."""
        return cls(frozenset(normalize_entity_name(name) for name in names))

    def excludes(self, name: str) -> bool:
        """Tell whether the name, once normalized, is on the list.

        Example:
            denylist.excludes("AMT - AGENTES DE NAVEGACAO, LDA.")  # True
        """
        return normalize_entity_name(name) in self.normalized_names


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
    blocks: Sequence[BilledEntityBlock], target: TargetEntity, denylist: EntityDenylist
) -> EntityCheckResult:
    """Apply the seven rules of D-3.15, in order. "Care of" lines never take part.

    Example:
        check_billed_entity(extraction.billed_entities, amt, denylist).verdict  # MATCH
    """
    if not blocks:
        return EntityCheckResult(EntityVerdict.AMBIGUOUS, FlagReason.ENTITY_LABEL_NOT_FOUND)
    if len(blocks) > 1:
        return EntityCheckResult(EntityVerdict.AMBIGUOUS, FlagReason.MULTIPLE_BILLED_ENTITIES)
    if denylist.excludes(blocks[0].name):
        return EntityCheckResult(EntityVerdict.NO_MATCH)
    name, target_name = normalize_entity_name(blocks[0].name), normalize_entity_name(target.name)
    nif_vetoes = _nif_differs(blocks[0].nif, target.nif)
    if name == target_name:
        if nif_vetoes:
            return EntityCheckResult(EntityVerdict.AMBIGUOUS, FlagReason.ENTITY_NIF_MISMATCH)
        return EntityCheckResult(EntityVerdict.MATCH)
    return _by_similarity(name, target_name)


def _nif_differs(extracted_nif: str | None, target_nif: str) -> bool:
    # Only an extracted NIF can veto. An absent one, or a placeholder with no digits such
    # as "N/D", neither vetoes nor confirms (REQ-ENT-007).
    digits = _digits(extracted_nif or "")
    return bool(digits) and digits != _digits(target_nif)


def _digits(nif: str) -> str:
    return "".join(character for character in nif if character.isdigit())


def _by_similarity(name: str, target_name: str) -> EntityCheckResult:
    # token_sort_ratio, never token_set_ratio: a name contained in the target must not
    # score 100 (D-3.15).
    if fuzz.token_sort_ratio(name, target_name) < ENTITY_SIMILARITY_LOW:
        return EntityCheckResult(EntityVerdict.NO_MATCH)
    return EntityCheckResult(EntityVerdict.AMBIGUOUS, FlagReason.ENTITY_SIMILAR_NOT_EQUAL)
