# 01: Esqueleto do frontend e login por token

**What to build:** Uma pessoa abre o frontend e vê um ecrã de entrada que pede um token de acesso, em vez de email e palavra-passe. O backend compara o token com o valor de uma variável de ambiente e, se coincidir, abre uma sessão. A partir daí, a pessoa navega na aplicação sem voltar a escrever o token, e o navegador nunca guarda a chave da API nem a recebe no código compilado. O ecrã inicial mostra o estado do servidor e o digest do catálogo carregado, e há uma acção para sair.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] O token de acesso vem de uma variável de ambiente do backend, obrigatória, com comprimento mínimo; sem ela a aplicação recusa arrancar, com mensagem que nomeia a variável
- [ ] O token é comparado no servidor, em tempo constante; um token errado é recusado com a mensagem de erro habitual, e o log regista a recusa sem o valor enviado
- [ ] Um token certo abre uma sessão em cookie `HttpOnly`, `SameSite=Strict`, com validade limitada; sair termina a sessão
- [ ] A API aceita a sessão do navegador ou o cabeçalho `X-API-Key`; as duas formas continuam a ser recusadas em `/api` sem credencial, e `/api/health` continua aberto
- [ ] O frontend é React com TypeScript, nos termos de `docs/02-arquitectura.md` §7: os tipos da API são gerados a partir do OpenAPI e nunca escritos à mão, e todo o texto visível vem do catálogo de tradução em Português
- [ ] Nenhum segredo entra no código compilado do frontend (SEC-02)
- [ ] Corre sem Docker, com o backend e o servidor de desenvolvimento do frontend, que encaminha `/api` para o backend
- [ ] O `README.md` explica como definir o token, como instalar e arrancar o frontend sem Docker, e como entrar
- [ ] Testes do backend para o login, a sessão e a recusa; testes do frontend para o ecrã de entrada e para a saída
