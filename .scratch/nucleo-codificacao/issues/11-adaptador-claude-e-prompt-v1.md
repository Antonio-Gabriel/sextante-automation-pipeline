# 11: Adaptador Claude do ItemClassifier e prompt v1

**What to build:** O sistema passa a codificar com o modelo real, através da API da Anthropic, atrás da porta `ItemClassifier`, sem nenhuma alteração nos módulos que a usam.

O prompt v1 é versionado no repositório, sem segredos. **O texto do prompt tem de ser confirmado pelo responsável antes de entrar no repositório**, porque é código que muda o comportamento do sistema. Por isso este ticket é para um humano: o agente prepara a proposta, e o humano aprova-a.

**Blocked by:** 02

**Status:** ready-for-human

- [ ] O adaptador usa `temperature` 0, saída estruturada por ferramenta com esquema declarado e `max_tokens` proporcional ao número de linhas
- [ ] O prompt pede apenas um índice da lista ou `none` por linha, e nunca um código, uma confiança ou uma justificação usada em decisões
- [ ] A versão do prompt e o identificador do modelo ficam registados em cada decisão
- [ ] O prompt não duplica regras que vivem em código: lista de exclusão, recurso e confiança
- [ ] O conteúdo da factura vai no prompt como dados delimitados, nunca como instrução
- [ ] O texto do prompt foi aprovado pelo responsável, e a aprovação está registada
- [ ] Nenhum teste chama a API da Anthropic. Os testes do adaptador verificam a construção do pedido e a interpretação da resposta com um cliente HTTP falso
- [ ] O adaptador escolhe o modelo Claude mais recente adequado, com o identificador em configuração
