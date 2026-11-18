# 04: Confiança, recurso e sinalização

**What to build:** Um contabilista vê em cada linha codificada uma confiança `HIGH`, `MEDIUM` ou `LOW`, calculada por uma regra fixa. Vê também as linhas duvidosas sinalizadas, cada uma com um motivo em português.

O ticket aplica a regra de recurso:

| Situação | Resultado |
|---|---|
| OUTLAYSP sem item adequado | `O00999` |
| OUTLAYS sem item adequado | Sem código, com `no_match_in_outlays` |
| Item genérico escolhido | `LOW`, com `generic_catalog_item` |
| Resposta inválida do modelo | Sem código, `LOW`, com `model_response_invalid` |

**Blocked by:** 02

**Status:** resolved

- [x] A confiança é uma função de domínio pura, com os limiares em constantes num só lugar e marcados como provisórios
- [x] `HIGH` só quando o item escolhido é o topo lexical, o score dele está acima do limiar alto e a distância ao segundo está acima do mínimo
- [x] `MEDIUM` quando o item é válido e não se cumpre o resto da condição `HIGH`
- [x] `LOW` quando há recurso, `none`, resposta inválida ou item genérico
- [x] `conflicting_candidates` só quando o item escolhido é um dos dois primeiros lexicais e os dois estão a menos da distância mínima
- [x] `O00999` só é aplicado quando a aba de destino é OUTLAYSP, e essa verificação está em código
- [x] Em OUTLAYS com `none`, o código fica vazio, e nunca é preenchido com `O00999` nem com o melhor candidato
- [x] Os itens genéricos são uma lista de configuração, inicialmente com `O00052`
- [x] Um índice fora dos limites, um código fora da aba ou uma linha sem resposta dá `model_response_invalid`, e nunca um código improvisado
- [x] Os motivos são um conjunto fechado, com texto em português num catálogo de tradução
- [x] As linhas sinalizadas começam em `pending` e as restantes em `accepted`
- [x] A auditoria regista a regra que produziu a confiança
- [x] Os testes de tabela da confiança ficam nos limites de cada limiar, e os testes pela API cobrem cada linha da tabela de recurso

## Comments

Resolved on 2026-11-18 (CHG-0018). Thresholds: HIGH score 85, margin 10, both provisional and declared in README.md (REQ-CNF-005). Also delivers the pending criterion of ticket 03: lines of an ambiguous invoice are recorded LOW, without target sheet, flagged with the entity reason.
