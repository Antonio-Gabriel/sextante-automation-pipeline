"""Line type classification, as a pure rule (REQ-ING-006, D-3.17). Table-driven."""

from typing import Final

import pytest

from sextante.ingestion.domain.line_type import LineType, classify_line_type

LINE_TYPES: Final = {
    "IVA 14%": LineType.TAX,
    "VAT 14%": LineType.TAX,
    "Imposto sobre o Valor Acrescentado (14%)": LineType.TAX,
    "iva - regime geral": LineType.TAX,
    "Desconto comercial 5%": LineType.DISCOUNT,
    "Discount": LineType.DISCOUNT,
    "Taxa de pilotagem sintética": LineType.SERVICE,
    "Imposto Sobre a Importação": LineType.SERVICE,
    "Taxa de Serviços Aduaneiros": LineType.SERVICE,
    "Passagem aérea Sintética - Rota Teste (isento de IVA)": LineType.SERVICE,
    "Ivanhoe Logistics handling fee": LineType.SERVICE,
    "Alojamento de 2 noites": LineType.SERVICE,
}


@pytest.mark.requirement("REQ-ING-006", "D-3.17", "L-06")
@pytest.mark.parametrize("description", LINE_TYPES, ids=list(LINE_TYPES))
def test_only_the_supplier_vat_and_discounts_are_not_services(description: str) -> None:
    """Tax means the supplier's VAT only; "taxa" or "imposto" alone is a service."""
    assert classify_line_type(description) is LINE_TYPES[description]
