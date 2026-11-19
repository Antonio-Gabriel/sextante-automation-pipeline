# 06: Exportação e reprocessamento na interface

**What to build:** A partir dos resultados de um trabalho, uma pessoa descarrega a exportação em CSV ou XLSX. Numa factura com falha ou já codificada, pede o reprocessamento; antes de confirmar, o ecrã avisa que uma codificação existente fica substituída e que as linhas revistas voltam à revisão.

**Blocked by:** 03 (Ecrã de resultados com filtros)

**Status:** resolved

- [x] Botões de exportação em CSV e XLSX, que descarregam o ficheiro do servidor com a sessão da pessoa
- [x] O reprocessamento só é oferecido a facturas com falha ou codificadas, e pede confirmação com o aviso sobre as revisões
- [x] O pedido de reprocessamento gera a sua `Idempotency-Key` antes do primeiro envio
- [x] O `README.md` descreve a exportação e o reprocessamento pela interface
- [x] Testes do componente para a exportação, a confirmação e a recusa de uma factura que não pode ser reprocessada

## Comments

Resolved on 2026-11-19 (CHG-0064). The Radix alert dialog was not added: it brings `tslib` (0BSD), outside NFR-LIC-001.
