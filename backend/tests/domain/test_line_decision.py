"""Confidence, fallback and flags, as pure rules (D-3.8, D-3.16, REQ-CNF-001 to REQ-CNF-003)."""

from typing import Final

import pytest

from sextante.catalog.contracts import CatalogItem, ItemNumber, TargetSheet
from sextante.matching.domain.choice_resolution import ChoiceOutcome, LineChoice
from sextante.matching.domain.line_decision import (
    ITEM_MARGIN_MIN,
    ITEM_SCORE_HIGH,
    Confidence,
    FlagReason,
    decide_line,
)
from sextante.matching.domain.scoring import LexicalScore


def _item(number: str, sheet: TargetSheet = TargetSheet.OUTLAYS) -> CatalogItem:
    return CatalogItem(ItemNumber(number), sheet, number, number, number, number)


FALLBACK: Final = _item("O00999", TargetSheet.OUTLAYSP)
GENERIC: Final = frozenset({ItemNumber("O00052")})


def _scores(*pairs: tuple[str, float]) -> tuple[LexicalScore, ...]:
    return tuple(LexicalScore(number, score, rank) for rank, (number, score) in enumerate(pairs, 1))


def _decide(choice: LineChoice, sheet: TargetSheet, scores: tuple[LexicalScore, ...]):  # type: ignore[no-untyped-def]
    return decide_line(choice, sheet, scores, FALLBACK, GENERIC)


def _chosen(number: str) -> LineChoice:
    return LineChoice(ChoiceOutcome.CHOSEN, 0, _item(number))


@pytest.mark.requirement("REQ-CNF-001", "REQ-CNF-002", "D-3.8")
@pytest.mark.parametrize(
    ("chosen", "scores", "confidence", "flags"),
    [
        ("O00004", _scores(("O00004", 92), ("O00051", 70)), Confidence.HIGH, ()),
        (
            "O00004",
            _scores(("O00004", ITEM_SCORE_HIGH), ("O00051", ITEM_SCORE_HIGH - ITEM_MARGIN_MIN)),
            Confidence.HIGH,
            (),
        ),
        ("O00004", _scores(("O00004", ITEM_SCORE_HIGH - 1), ("O00051", 20)), Confidence.MEDIUM, ()),
        ("O00051", _scores(("O00004", 92), ("O00051", 60)), Confidence.MEDIUM, ()),
        (
            "O00004",
            _scores(("O00004", 90), ("O00051", 90 - ITEM_MARGIN_MIN + 1)),
            Confidence.MEDIUM,
            (FlagReason.CONFLICTING_CANDIDATES,),
        ),
        (
            "O00051",
            _scores(("O00004", 88), ("O00051", 85)),
            Confidence.MEDIUM,
            (FlagReason.CONFLICTING_CANDIDATES,),
        ),
        ("O00060", _scores(("O00004", 88), ("O00051", 85), ("O00060", 40)), Confidence.MEDIUM, ()),
    ],
    ids=[
        "top, high score, wide gap",
        "at both thresholds exactly",
        "top, one point below the high score",
        "second item, wide gap",
        "top, gap one point too narrow",
        "second item, close to the top",
        "third item while the top two are close",
    ],
)
def test_confidence_of_a_chosen_item_follows_the_lexical_signal(
    chosen: str,
    scores: tuple[LexicalScore, ...],
    confidence: Confidence,
    flags: tuple[FlagReason, ...],
) -> None:
    """HIGH only when the model and the lexical signal agree with a margin."""
    decision = _decide(_chosen(chosen), TargetSheet.OUTLAYS, scores)

    assert (decision.confidence, decision.flags) == (confidence, flags)
    assert decision.catalog_item is not None
    assert decision.catalog_item.item_number.value == chosen


@pytest.mark.requirement("REQ-MAP-008", "R3", "SEC-14")
def test_no_item_fits_in_outlaysp_falls_back_to_o00999() -> None:
    """The fallback is decided in code, after checking the sheet is OUTLAYSP."""
    decision = _decide(LineChoice(ChoiceOutcome.NO_ITEM_FITS, None, None), TargetSheet.OUTLAYSP, ())

    assert decision.catalog_item is FALLBACK
    assert (decision.confidence, decision.flags) == (Confidence.LOW, (FlagReason.FALLBACK_APPLIED,))


@pytest.mark.requirement("REQ-MAP-009", "L-08", "R3")
def test_no_item_fits_in_outlays_leaves_the_line_empty() -> None:
    """OUTLAYS has no fallback: never O00999, never the best candidate."""
    scores = _scores(("O00004", 95), ("O00051", 20))

    decision = _decide(
        LineChoice(ChoiceOutcome.NO_ITEM_FITS, None, None), TargetSheet.OUTLAYS, scores
    )

    assert decision.catalog_item is None
    assert (decision.confidence, decision.flags) == (
        Confidence.LOW,
        (FlagReason.NO_MATCH_IN_OUTLAYS,),
    )


@pytest.mark.requirement("REQ-MAP-013", "L-08")
def test_a_generic_item_is_always_low_and_flagged() -> None:
    """Other Expenses is valid, but choosing it freely would be a hidden fallback."""
    decision = _decide(
        _chosen("O00052"), TargetSheet.OUTLAYS, _scores(("O00052", 99), ("O00004", 10))
    )

    assert decision.catalog_item is not None
    assert (decision.confidence, decision.flags) == (
        Confidence.LOW,
        (FlagReason.GENERIC_CATALOG_ITEM,),
    )


@pytest.mark.requirement("REQ-MAP-007", "SEC-14")
def test_an_invalid_model_answer_is_a_line_failure_never_a_code() -> None:
    """No code, LOW, flagged: the line goes to a reviewer."""
    decision = _decide(
        LineChoice(ChoiceOutcome.INVALID_RESPONSE, 7, None), TargetSheet.OUTLAYSP, ()
    )

    assert decision.catalog_item is None
    assert (decision.confidence, decision.flags) == (
        Confidence.LOW,
        (FlagReason.MODEL_RESPONSE_INVALID,),
    )


@pytest.mark.requirement("REQ-REV-005", "REQ-CNF-003")
def test_flagged_lines_start_pending_and_the_others_accepted() -> None:
    """The review state is born from the flags, never set separately."""
    flagged = _decide(
        LineChoice(ChoiceOutcome.INVALID_RESPONSE, None, None), TargetSheet.OUTLAYS, ()
    )
    clean = _decide(_chosen("O00004"), TargetSheet.OUTLAYS, _scores(("O00004", 95), ("O00051", 10)))

    assert (flagged.review_status, clean.review_status) == ("pending", "accepted")


@pytest.mark.requirement("REQ-AUD-001")
def test_every_decision_names_the_rule_that_produced_it() -> None:
    """The audit trail records which rule set the confidence."""
    decision = _decide(LineChoice(ChoiceOutcome.NO_ITEM_FITS, None, None), TargetSheet.OUTLAYSP, ())

    assert decision.rule == "fallback_outlaysp"
