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
    }
)
