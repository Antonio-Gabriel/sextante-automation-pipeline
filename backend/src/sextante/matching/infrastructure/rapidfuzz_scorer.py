"""LexicalScorer with rapidfuzz (D-3.16, REQ-MAP-004)."""

from collections.abc import Sequence

from rapidfuzz import fuzz, utils

from sextante.catalog.contracts import CatalogItem
from sextante.matching.application.ports import LexicalScore
from sextante.platform.text_normalization import normalize_for_comparison


class RapidfuzzLexicalScorer:
    """Score a line against PT and EN descriptions and keep the better of the two.

    token_set_ratio suits line descriptions, which carry extra tokens such as container
    or ticket numbers around the service name. It is not used for entity names, where a
    contained name must not score 100 (D-3.15).

    Example:
        RapidfuzzLexicalScorer().score("Passagem aérea Sintética", outlays_items)
    """

    def score(
        self, description: str, catalog_items: Sequence[CatalogItem]
    ) -> tuple[LexicalScore, ...]:
        """Return one score per item, ranked best first, ties in catalog order."""
        line_text = normalize_for_comparison(description)
        scored = [
            (_best_score(line_text, catalog_item), catalog_item) for catalog_item in catalog_items
        ]
        ranked = sorted(enumerate(scored), key=lambda entry: (-entry[1][0], entry[0]))
        return tuple(
            LexicalScore(item_number=catalog_item.item_number.value, score=score, rank=rank)
            for rank, (_, (score, catalog_item)) in enumerate(ranked, start=1)
        )


def _best_score(line_text: str, catalog_item: CatalogItem) -> float:
    return max(
        fuzz.token_set_ratio(
            line_text, catalog_item.comparison_pt, processor=utils.default_process
        ),
        fuzz.token_set_ratio(
            line_text, catalog_item.comparison_en, processor=utils.default_process
        ),
    )
