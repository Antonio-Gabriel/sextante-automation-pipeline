"""Entity check, as a pure rule (D-3.15, REQ-ENT-001 to REQ-ENT-008). Table-driven."""

from typing import Final

import pytest

from sextante.ingestion.contracts import BilledEntityBlock
from sextante.matching.domain.entity_check import (
    EntityDenylist,
    EntityVerdict,
    TargetEntity,
    check_billed_entity,
)
from sextante.matching.domain.line_decision import FlagReason

AMT: Final = TargetEntity(
    name="Advanced Maritime Transports - Transitarios Limitada", nif="5419990000"
)
SISTER_IN_DENYLIST: Final = "Advanced Maritime Transports Agentes Lda"


def _block(name: str, nif: str | None = None, care_of: tuple[str, ...] = ()) -> BilledEntityBlock:
    return BilledEntityBlock(name=name, nif=nif, care_of=care_of, address_lines=())


def _check(*blocks: BilledEntityBlock) -> tuple[EntityVerdict, FlagReason | None]:
    result = check_billed_entity(blocks, AMT, denylist=EntityDenylist.of([SISTER_IN_DENYLIST]))
    return result.verdict, result.reason


MATCH_CASES: Final = {
    "exact name and NIF": _block(
        "Advanced Maritime Transports - Transitarios Limitada", "5419990000"
    ),
    "capitals, no hyphen, LDA (INV-003)": _block(
        "ADVANCED MARITIME TRANSPORTS TRANSITARIOS LDA", "5419990000"
    ),
    "accent and Lda.": _block("Advanced Maritime Transports - Transitários Lda.", None),
    "no NIF on the invoice": _block("Advanced Maritime Transports Transitarios Ltda"),
}


@pytest.mark.requirement("REQ-ENT-001", "REQ-ENT-002", "R5")
@pytest.mark.parametrize("block", MATCH_CASES.values(), ids=list(MATCH_CASES))
def test_minor_variations_of_the_target_name_match(block: BilledEntityBlock) -> None:
    """Case, punctuation, hyphen, accents and the form of the suffix do not break a match."""
    assert _check(block) == (EntityVerdict.MATCH, None)


NO_MATCH_CASES: Final = {
    "third-party client (oil company)": _block(
        "Petrolífera Sintética de Cabinda Lda", "5419990003"
    ),
    "third-party client (services company)": _block(
        "Serviços Petrolíferos Sintéticos Angola", "5419990007"
    ),
    "third-party client (engineering company)": _block("Engenharia Sintética Angola", "5419990008"),
    "shipping line": _block("Linha de Navegação Sintética Limitada"),
    "client billed care of AMT (INV-002)": _block(
        "Operadora Sintética de Petróleo Angola",
        "5419990005",
        care_of=("c/o Advanced Maritime Transports",),
    ),
    "sister company with another NIF (INV-010)": _block(
        "AMT - Empresa Irmã Sintética Limitada", "5419990099"
    ),
    "sister company in the denylist, near-identical name": _block(SISTER_IN_DENYLIST, None),
}


@pytest.mark.requirement("REQ-ENT-003", "REQ-ENT-008", "R4")
@pytest.mark.parametrize("block", NO_MATCH_CASES.values(), ids=list(NO_MATCH_CASES))
def test_other_entities_are_a_definite_no_match(block: BilledEntityBlock) -> None:
    """Clients, shipping lines and sister companies route to OUTLAYSP, never to OUTLAYS."""
    assert _check(block) == (EntityVerdict.NO_MATCH, None)


AMBIGUOUS_CASES: Final = {
    "unlisted sister with a geographic suffix": (
        (_block("Advanced Maritime Transports Moçambique Limitada"),),
        FlagReason.ENTITY_SIMILAR_NOT_EQUAL,
    ),
    "name contained in the target name": (
        (_block("Advanced Maritime Transports"),),
        FlagReason.ENTITY_SIMILAR_NOT_EQUAL,
    ),
    "target name with another NIF": (
        (_block("Advanced Maritime Transports - Transitarios Limitada", "5419990099"),),
        FlagReason.ENTITY_NIF_MISMATCH,
    ),
    "similar name with another NIF": (
        (_block("Advanced Maritime Transports - Agentes de Navegação", "5419990099"),),
        FlagReason.ENTITY_SIMILAR_NOT_EQUAL,
    ),
    "no billed-entity block": ((), FlagReason.ENTITY_LABEL_NOT_FOUND),
    "two billed-entity blocks": (
        (
            _block("Engenharia Sintética Angola"),
            _block("Advanced Maritime Transports - Transitarios Limitada"),
        ),
        FlagReason.MULTIPLE_BILLED_ENTITIES,
    ),
}


@pytest.mark.requirement("REQ-ENT-004", "REQ-ENT-007", "L-04", "L-09")
@pytest.mark.parametrize("case", AMBIGUOUS_CASES, ids=list(AMBIGUOUS_CASES))
def test_undecidable_entities_are_ambiguous_with_their_reason(case: str) -> None:
    """What only a human can decide is ambiguous, with the reason that says why."""
    blocks, reason = AMBIGUOUS_CASES[case]

    assert _check(*blocks) == (EntityVerdict.AMBIGUOUS, reason)


@pytest.mark.requirement("REQ-ENT-007")
def test_the_target_nif_alone_never_makes_a_match() -> None:
    """A different company carrying AMT's NIF is not AMT: the name must match too."""
    verdict, _ = _check(_block("Engenharia Sintética Angola", "5419990000"))

    assert verdict is not EntityVerdict.MATCH


@pytest.mark.requirement("REQ-ENT-007")
@pytest.mark.parametrize("unreadable_nif", ["N/D", "", "—"])
def test_a_nif_without_digits_counts_as_not_extracted(unreadable_nif: str) -> None:
    """Only an extracted NIF can veto: a placeholder is not a different NIF."""
    block = _block("Advanced Maritime Transports - Transitarios Limitada", unreadable_nif)

    assert _check(block) == (EntityVerdict.MATCH, None)
