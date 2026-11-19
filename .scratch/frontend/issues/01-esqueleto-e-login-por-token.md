# 01: Esqueleto do frontend e login por token

**What to build:** Uma pessoa abre o frontend e vê um ecrã de entrada que pede um token de acesso, em vez de email e palavra-passe. O backend compara o token com o valor de uma variável de ambiente e, se coincidir, abre uma sessão. A partir daí, a pessoa navega na aplicação sem voltar a escrever o token, e o navegador nunca guarda a chave da API nem a recebe no código compilado. O ecrã inicial mostra o estado do servidor e o digest do catálogo carregado, e há uma acção para sair.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] O token de acesso vem de uma variável de ambiente do backend, obrigatória, com comprimento mínimo; sem ela a aplicação recusa arrancar, com mensagem que nomeia a variável
- [x] O token é comparado no servidor, em tempo constante; um token errado é recusado com a mensagem de erro habitual, e o log regista a recusa sem o valor enviado
- [x] Um token certo abre uma sessão em cookie `HttpOnly`, `SameSite=Strict`, com validade limitada; sair termina a sessão
- [x] A API aceita a sessão do navegador ou o cabeçalho `X-API-Key`; as duas formas continuam a ser recusadas em `/api` sem credencial, e `/api/health` continua aberto
- [x] O frontend é React com TypeScript, nos termos de `docs/02-arquitectura.md` §7: os tipos da API são gerados a partir do OpenAPI e nunca escritos à mão, e todo o texto visível vem do catálogo de tradução em Português
- [x] Nenhum segredo entra no código compilado do frontend (SEC-02)
- [x] Corre sem Docker, com o backend e o servidor de desenvolvimento do frontend, que encaminha `/api` para o backend
- [x] O `README.md` explica como definir o token, como instalar e arrancar o frontend sem Docker, e como entrar
- [x] Testes do backend para o login, a sessão e a recusa; testes do frontend para o ecrã de entrada e para a saída

## Comments

Resolved on 2026-11-19 (CHG-0055). `SEXTANTE_ACCESS_TOKEN` is mandatory; `POST /api/session` opens an HttpOnly, SameSite=Strict, Secure session cookie of 8 hours, `POST /api/session/end` ends it, `GET /api/session` reports it. The `/api` guard accepts the key or the session, one principal sharing one quota; login has its own limit. React 18 skeleton with login and home screens, API types generated from `frontend/openapi.json`, kept current by a backend test. Not checked in a real browser: the Chrome extension was not connected; curl through the Vite proxy covered the whole flow.

Review fixes on 2026-11-19 (CHG-0056): logout navigates only when the server confirms, a second login closes the previous session, the token must differ from the key, secrets compared by digest, cookie attributes in one place, the token limit read from the OpenAPI document, no visible literal left in JSX, the health status decided in the hook, the Idempotency-Key exemption of the session endpoints written in SEC-19, and the shared anonymous login quota declared.

