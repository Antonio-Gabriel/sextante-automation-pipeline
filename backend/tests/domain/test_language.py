"""Decision 3.25: English by default, Portuguese on request; descriptions by language."""

import pytest

from sextante.catalog.contracts import Catalog, CatalogDigest, CatalogItem, ItemNumber, TargetSheet
from sextante.platform.language import Language, parse_accept_language
from sextante.platform.user_messages import USER_MESSAGES_EN, USER_MESSAGES_PT


@pytest.mark.requirement("REQ-PLT-006")
@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (None, Language.EN),
        ("", Language.EN),
        ("pt-PT,pt;q=0.9,en;q=0.8", Language.PT),
        ("en-GB,en;q=0.9", Language.EN),
        ("fr-FR,pt;q=0.5", Language.PT),
        ("en;q=0.2,pt;q=0.9", Language.PT),
        ("de, fr", Language.EN),
        ("pt;q=nonsense,en", Language.EN),
        ("pt" + ",x" * 200, Language.EN),
    ],
)
def test_the_language_comes_from_accept_language_and_defaults_to_english(
    header: str | None, expected: Language
) -> None:
    """The best supported language by quality; anything else is English."""
    assert parse_accept_language(header) is expected


@pytest.mark.requirement("REQ-PLT-006")
def test_both_catalogs_hold_the_same_keys_and_no_empty_text() -> None:
    """A text missing in one language would fail only when shown."""
    assert set(USER_MESSAGES_EN) == set(USER_MESSAGES_PT)
    assert all(USER_MESSAGES_EN.values()) and all(USER_MESSAGES_PT.values())


def _catalog(*items: tuple[str, str, str]) -> Catalog:
    outlays = tuple(
        CatalogItem(ItemNumber(n), TargetSheet.OUTLAYS, pt, en, pt.lower(), en.lower())
        for n, pt, en in items
    )
    return Catalog(CatalogDigest("0" * 64), outlays, ())


@pytest.mark.requirement("REQ-PLT-006", "D-3.25")
@pytest.mark.parametrize(
    ("item_number", "language", "recorded", "expected"),
    [
        ("O00004", Language.EN, "Bilhete Avião", "Air ticket"),
        ("O00004", Language.PT, "Bilhete Avião", "Bilhete Avião"),
        # No English in the catalog: the Portuguese description, never an empty one.
        ("O00061", Language.EN, "Sem tradução", "Sem tradução"),
        # Gone from the catalog: what was recorded with the decision.
        ("O00077", Language.EN, "Registado", "Registado"),
        (None, Language.EN, None, None),
    ],
)
def test_a_description_is_shown_in_the_language_with_portuguese_as_fallback(
    item_number: str | None, language: Language, recorded: str | None, expected: str | None
) -> None:
    """English from Description 2 of the catalog; Portuguese as recorded."""
    catalog = _catalog(("O00004", "Bilhete Avião", "Air ticket"), ("O00061", "Sem tradução", ""))

    assert catalog.description_in(item_number, language, recorded) == expected
