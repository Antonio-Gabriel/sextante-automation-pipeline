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
    "Passagem aérea de teste (isento de IVA)": LineType.SERVICE,
    "Ivanhoe Logistics handling fee": LineType.SERVICE,
    "Alojamento de 2 noites": LineType.SERVICE,
    "Valor do IVA": LineType.TAX,
    "Total IVA": LineType.TAX,
    "14% IVA": LineType.TAX,
    "I.V.A. 14%": LineType.TAX,
    "Value Added Tax": LineType.TAX,
    "Imposto s/ Valor Acrescentado": LineType.TAX,
    "Tax / IVA": LineType.TAX,
    "Vat handling fee": LineType.SERVICE,
    "Descontos": LineType.DISCOUNT,
    "Desc. 5%": LineType.DISCOUNT,
    "Desconto de pronto pagamento": LineType.DISCOUNT,
    "Descarga de contentor": LineType.SERVICE,
    "Discounted storage fee": LineType.SERVICE,
}


@pytest.mark.requirement("REQ-ING-006", "D-3.17", "L-06")
@pytest.mark.parametrize("description", LINE_TYPES, ids=list(LINE_TYPES))
def test_only_the_supplier_vat_and_discounts_are_not_services(description: str) -> None:
    """A line is VAT or a discount only when every word of it belongs to that vocabulary.

    "Taxa" or "imposto" alone is a service, and so is any service that merely mentions
    VAT, such as "(isento de IVA)" or "Vat handling fee".
    """
    assert classify_line_type(description) is LINE_TYPES[description]
