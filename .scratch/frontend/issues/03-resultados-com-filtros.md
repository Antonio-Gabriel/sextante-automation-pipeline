# 03: Ecrã de resultados com filtros

**What to build:** Uma pessoa abre os resultados de um trabalho e vê a tabela das linhas: factura, entidade detectada, correspondência exacta, aba, descrição, código, descrição do catálogo, confiança, estado de revisão, sinalizações e notas em Português, e a nota de revisão. Filtra por confiança, aba, sinalização e factura, e partilha a vista copiando o endereço, porque os filtros vivem na rota.

**Blocked by:** 01 (Esqueleto do frontend e login por token)

**Status:** resolved

- [x] Os filtros de confiança, aba, sinalização e factura ficam na rota, validados, e um endereço com um filtro inválido cai para a vista sem esse filtro
- [x] A paginação respeita o máximo do servidor e mostra quando o pedido foi truncado
- [x] As sinalizações e as notas aparecem com o texto em Português que a API devolve
- [x] Uma linha leva à revisão dessa linha; uma factura leva ao ecrã da factura
- [x] Nenhum `dangerouslySetInnerHTML`; o conteúdo das facturas é sempre texto
- [x] O `README.md` descreve o ecrã e os filtros
- [x] Testes do componente para cada filtro e para a paginação truncada

## Comments

Resolved on 2026-11-19 (CHG-0059). The invoice and line routes exist and are filled by tickets 05 and 04.

Review fixes on 2026-11-19 (CHG-0060): visible invoice filter, a way back past the last page, server errors shown, accessible names per row, centralized cache keys, and §8.6 aligned with this ticket on the flag texts the API sends.
