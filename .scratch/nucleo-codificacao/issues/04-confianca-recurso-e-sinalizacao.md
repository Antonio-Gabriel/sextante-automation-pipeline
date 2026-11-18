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

**Status:** ready-for-agent

- [ ] A confiança é uma função de domínio pura, com os limiares em constantes num só lugar e marcados como provisórios
- [ ] `HIGH` só quando o item escolhido é o topo lexical, o score dele está acima do limiar alto e a distância ao segundo está acima do mínimo
- [ ] `MEDIUM` quando o item é válido e não se cumpre o resto da condição `HIGH`
- [ ] `LOW` quando há recurso, `none`, resposta inválida ou item genérico
- [ ] `conflicting_candidates` só quando o item escolhido é um dos dois primeiros lexicais e os dois estão a menos da distância mínima
- [ ] `O00999` só é aplicado quando a aba de destino é OUTLAYSP, e essa verificação está em código
- [ ] Em OUTLAYS com `none`, o código fica vazio, e nunca é preenchido com `O00999` nem com o melhor candidato
- [ ] Os itens genéricos são uma lista de configuração, inicialmente com `O00052`
- [ ] Um índice fora dos limites, um código fora da aba ou uma linha sem resposta dá `model_response_invalid`, e nunca um código improvisado
- [ ] Os motivos são um conjunto fechado, com texto em português num catálogo de tradução
- [ ] As linhas sinalizadas começam em `pending` e as restantes em `accepted`
- [ ] A auditoria regista a regra que produziu a confiança
- [ ] Os testes de tabela da confiança ficam nos limites de cada limiar, e os testes pela API cobrem cada linha da tabela de recurso
