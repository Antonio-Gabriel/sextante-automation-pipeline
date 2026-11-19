# 08: Interface em Inglês e Português

**What to build:** A interface existe em Inglês, por omissão, e em Português, com uma opção para trocar. No idioma escolhido aparecem também os textos do servidor: erros, sinalizações, notas, motivos de recusa, descrições do catálogo (Description 2 em Inglês) e a exportação. Pedido pelo responsável em 19-11-2026.

**Blocked by:** 01 a 07 do frontend

**Status:** resolved

- [x] Catálogos do frontend em Inglês e Português, com as mesmas chaves verificadas pelo compilador
- [x] Inglês por omissão; escolha na barra lateral e no ecrã de entrada, guardada no navegador
- [x] Cada pedido envia `Accept-Language`; o servidor responde no idioma pedido, e em Inglês sem cabeçalho
- [x] Descrição do catálogo em Inglês pela Description 2, com a portuguesa quando falta a inglesa
- [x] Exportação no idioma escolhido, com os nomes das colunas inalterados
- [x] Decisão 3.25, R12 e REQ-PLT-006 revistos

## Comments

Owner's answers on 19-11-2026: revise R12 with English as the default; the export follows the language; a missing English description falls back to the Portuguese one.
