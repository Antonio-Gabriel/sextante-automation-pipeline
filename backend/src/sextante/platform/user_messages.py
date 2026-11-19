"""Texts shown to people, in English and Portuguese, keyed by stable keys (REQ-PLT-006).

Both catalogs hold exactly the same keys; a test checks it.
"""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from sextante.platform.language import Language

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
        "errors.job.not_deletable": (
            "Só um trabalho terminado, concluído ou com falha, pode ser apagado."
        ),
        "errors.auth.credential_invalid": (
            "Credencial em falta ou inválida: entre com o token de acesso, ou envie a chave da API."
        ),
        "errors.auth.access_token_invalid": "Token de acesso inválido.",
        "errors.rate_limit.exceeded": "Pedidos a mais em pouco tempo. Tente de novo mais tarde.",
        "errors.invoice.not_found": "Factura não encontrada.",
        "errors.invoice.not_reprocessable": (
            "Só uma factura com falha ou já codificada pode ser reprocessada."
        ),
        "errors.invoice_line.not_found": "Linha de factura não encontrada.",
        "errors.review.line_not_found": "Linha codificada não encontrada.",
        "errors.review.line_without_sheet": (
            "Linha sem aba de destino: resolva primeiro a entidade da factura."
        ),
        "errors.review.item_not_in_sheet": (
            "O item escolhido não pertence à aba de destino da linha."
        ),
        "errors.review.not_pending": "Só uma linha pendente pode ser aceite.",
        "errors.entity.not_ambiguous": (
            "Só uma factura com entidade ambígua, ainda por resolver, pode ser resolvida."
        ),
        "errors.idempotency.key_required": "Falta o cabeçalho Idempotency-Key, ou é inválido.",
        "errors.idempotency.key_reused": "A chave Idempotency-Key já foi usada noutro pedido.",
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
        "flags.review_superseded": "Linha revista antes da recodificação: rever de novo.",
        "rejections.pdf_without_text_layer": "Documento recusado: PDF digitalizado, sem texto.",
        "rejections.unsupported_document_type": (
            "Documento recusado: não é uma factura no modelo suportado."
        ),
        "rejections.other": "Documento recusado.",
        "export.invoice_failed": "Falha no processamento: a factura pode ser reprocessada.",
        "export.line_not_coded": "Linha ainda por codificar.",
        "export.care_of": "Ao cuidado de: {}",
        "export.review_note": "Nota de revisão: {}",
        "export.possible_duplicate_of": "Possível duplicado de {}, carregada a {}.",
        "notes.line_type_tax": "Linha de IVA: sem código de item.",
        "notes.line_type_discount": "Linha de desconto: sem código de item.",
        "notes.entity_confirmed_by_reviewer": "Entidade confirmada pelo revisor.",
        "reasons.undescribed": "Motivo registado sem descrição. Contacte o suporte.",
    }
)

USER_MESSAGES_EN: Final[Mapping[str, str]] = MappingProxyType(
    {
        "errors.internal": "An internal error occurred. Contact support with the reference shown.",
        "errors.catalog.invalid": "The item catalog is invalid. The application cannot start.",
        "errors.catalog.unreadable": "The item catalog file could not be read.",
        "errors.upload.unsupported_type": "Unsupported format. Only PDF and XLSX are accepted.",
        "errors.upload.too_large": "The file is larger than the maximum allowed size.",
        "errors.upload.too_many_files": "Too many files were sent in one upload.",
        "errors.upload.invalid_file_name": "The file name is invalid.",
        "errors.upload.no_files": "No file was sent.",
        "errors.job.not_found": "Job not found.",
        "errors.job.not_deletable": "Only a finished job, completed or failed, can be deleted.",
        "errors.auth.credential_invalid": (
            "Missing or invalid credential: sign in with the access token, or send the API key."
        ),
        "errors.auth.access_token_invalid": "Invalid access token.",
        "errors.rate_limit.exceeded": "Too many requests in a short time. Try again later.",
        "errors.invoice.not_found": "Invoice not found.",
        "errors.invoice.not_reprocessable": (
            "Only a failed or already coded invoice can be reprocessed."
        ),
        "errors.invoice_line.not_found": "Invoice line not found.",
        "errors.review.line_not_found": "Coded line not found.",
        "errors.review.line_without_sheet": (
            "Line without a target sheet: resolve the invoice's entity first."
        ),
        "errors.review.item_not_in_sheet": "The chosen item is not in the line's target sheet.",
        "errors.review.not_pending": "Only a pending line can be accepted.",
        "errors.entity.not_ambiguous": (
            "Only an invoice with an ambiguous entity, not yet resolved, can be resolved."
        ),
        "errors.idempotency.key_required": "The Idempotency-Key header is missing or invalid.",
        "errors.idempotency.key_reused": (
            "The Idempotency-Key was already used for another request."
        ),
        "flags.entity_label_not_found": "The billed entity was not found on the invoice.",
        "flags.multiple_billed_entities": "The invoice names more than one billed entity.",
        "flags.entity_similar_not_equal": "Entity similar to AMT, but not equal: confirm.",
        "flags.entity_nif_mismatch": "Same name as AMT, but a different tax number.",
        "flags.no_match_in_outlays": "No OUTLAYS item fits: code left unassigned.",
        "flags.fallback_applied": "No item fits: fallback O00999 (OUTLAYSP) assigned.",
        "flags.generic_catalog_item": "A generic item was assigned: check there is no better one.",
        "flags.conflicting_candidates": "Two catalog items are very close.",
        "flags.model_response_invalid": "The model's answer was invalid: code left unassigned.",
        "flags.possible_duplicate": "Possible duplicate of an invoice already uploaded.",
        "flags.review_superseded": "Line reviewed before it was coded again: review it again.",
        "rejections.pdf_without_text_layer": "Document refused: scanned PDF, without text.",
        "rejections.unsupported_document_type": (
            "Document refused: not an invoice in the supported layout."
        ),
        "rejections.other": "Document refused.",
        "export.invoice_failed": "Processing failed: the invoice can be reprocessed.",
        "export.line_not_coded": "Line not coded yet.",
        "export.care_of": "Care of: {}",
        "export.review_note": "Review note: {}",
        "export.possible_duplicate_of": "Possible duplicate of {}, uploaded on {}.",
        "notes.line_type_tax": "VAT line: no item code.",
        "notes.line_type_discount": "Discount line: no item code.",
        "notes.entity_confirmed_by_reviewer": "Entity confirmed by the reviewer.",
        "reasons.undescribed": "Reason recorded without a description. Contact support.",
    }
)

_MESSAGES: Final[Mapping[Language, Mapping[str, str]]] = MappingProxyType(
    {Language.EN: USER_MESSAGES_EN, Language.PT: USER_MESSAGES_PT}
)


def user_message(key: str, language: Language) -> str:
    """The text of a key in a language.

    Example:
        user_message("errors.job.not_found", Language.PT)  # "Trabalho não encontrado."

    Raises:
        KeyError: when the key is not in the catalogs.
    """
    return _MESSAGES[language][key]


def has_user_message(key: str) -> bool:
    """Whether the key has a text; both catalogs hold the same keys."""
    return key in USER_MESSAGES_EN
