"""Portuguese texts shown to the user, keyed by stable English keys (REQ-PLT-006, R12)."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

USER_MESSAGES_PT: Final[Mapping[str, str]] = MappingProxyType(
    {
        "errors.internal": "Ocorreu um erro interno. Contacte o suporte com a referência indicada.",
        "errors.catalog.invalid": "O catálogo de itens é inválido. A aplicação não pode arrancar.",
        "errors.catalog.unreadable": "O ficheiro do catálogo de itens não pôde ser lido.",
        "errors.upload.unsupported_type": "Formato não suportado. Só são aceites PDF e XLSX.",
        "errors.upload.too_large": "O ficheiro excede o tamanho máximo permitido.",
        "errors.upload.too_many_files": "Foram enviados ficheiros a mais num só carregamento.",
        "errors.upload.invalid_file_name": "O nome do ficheiro é inválido.",
        "errors.upload.no_files": "Nenhum ficheiro foi enviado.",
        "errors.job.not_found": "Trabalho não encontrado.",
        "flags.entity_label_not_found": "Não foi encontrada a entidade facturada na factura.",
        "flags.multiple_billed_entities": "A factura indica mais do que uma entidade facturada.",
        "flags.entity_similar_not_equal": "Entidade parecida com a AMT, mas não igual: confirmar.",
        "flags.entity_nif_mismatch": "Nome igual ao da AMT, mas com NIF diferente.",
        "flags.no_match_in_outlays": "Nenhum item de OUTLAYS serve: código por atribuir.",
        "flags.fallback_applied": "Nenhum item serve: atribuído o recurso O00999 (OUTLAYSP).",
        "flags.generic_catalog_item": "Atribuído um item genérico: confirmar se não há outro.",
        "flags.conflicting_candidates": "Dois itens do catálogo estão muito próximos.",
        "flags.model_response_invalid": "A resposta do modelo foi inválida: código por atribuir.",
        "flags.possible_duplicate": "Possível duplicado de uma factura já carregada.",
        "rejections.pdf_without_text_layer": "Documento recusado: PDF digitalizado, sem texto.",
        "rejections.unsupported_document_type": (
            "Documento recusado: não é uma factura no modelo suportado."
        ),
        "rejections.extractor_not_configured": (
            "Documento recusado: a leitura de facturas não está configurada."
        ),
        "export.invoice_failed": "Falha no processamento: a factura pode ser reprocessada.",
        "export.line_not_coded": "Linha ainda por codificar.",
        "export.care_of": "Ao cuidado de: {}",
        "notes.line_type_tax": "Linha de IVA: sem código de item.",
        "notes.line_type_discount": "Linha de desconto: sem código de item.",
    }
)
