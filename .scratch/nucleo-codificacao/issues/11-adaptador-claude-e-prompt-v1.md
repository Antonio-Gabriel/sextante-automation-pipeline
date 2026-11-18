# 11: Adaptador Claude do ItemClassifier e prompt v1

**What to build:** O sistema passa a codificar com o modelo real, através da API da Anthropic, atrás da porta `ItemClassifier`, sem nenhuma alteração nos módulos que a usam.

O prompt v1 é versionado no repositório, sem segredos. **O texto do prompt tem de ser confirmado pelo responsável antes de entrar no repositório**, porque é código que muda o comportamento do sistema. Por isso este ticket é para um humano: o agente prepara a proposta, e o humano aprova-a.

**Blocked by:** 02

**Status:** resolved

- [x] O adaptador usa ~~`temperature` 0,~~ saída estruturada ~~por ferramenta~~ com esquema declarado e `max_tokens` proporcional ao número de linhas *(revisto: a API já não aceita `temperature` nem ferramenta forçada; ver §3.22)*
- [x] O prompt pede apenas um índice da lista ou `none` por linha, e nunca um código, uma confiança ou uma justificação usada em decisões
- [x] A versão do prompt e o identificador do modelo ficam registados em cada decisão
- [x] O prompt não duplica regras que vivem em código: lista de exclusão, recurso e confiança
- [x] O conteúdo da factura vai no prompt como dados delimitados, nunca como instrução
- [x] O texto do prompt foi aprovado pelo responsável, e a aprovação está registada
- [x] Nenhum teste chama a API da Anthropic. Os testes do adaptador verificam a construção do pedido e a interpretação da resposta com um cliente HTTP falso
- [x] O adaptador escolhe o modelo Claude mais recente adequado, com o identificador em configuração

## Comments

Resolved on 2026-11-18 (CHG-0035). **Approval:** the project owner approved the call configuration and the prompt text `item-choice-v1` on 2026-11-18, in the working session, as proposed and without changes; recorded in 00-decisoes-e-lacunas.md §3.22. The API refuses sampling parameters on every model and forced tool choice on the current ones, so the call uses a JSON schema through `output_config.format`, low effort and server-side fallbacks on a refusal. The adapter tests answer from an in-memory HTTP transport; no test calls the API.

A first real call, made by hand with the owner's key, was refused by the API for lack of credit, so the request has not yet been confirmed against the live API. `make golden-model` repeats it once there is credit.

Confirmed on 2026-11-18 (CHG-0037): with credit on the account, `make golden-model` ran against the live API with `claude-opus-5-5`; the request was accepted and every answer read. Review fixes: 408 and 409 count as transient; error messages name the status; deciding the lines moved to `LineCoder`, which the application and the manual measurement share.
