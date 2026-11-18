# 02: Contentor do frontend no compose

**What to build:** `docker compose up` arranca também o frontend compilado, servido por um servidor estático que encaminha `/api` para a API, de forma que a pessoa abre um só endereço, entra com o token e usa a aplicação. Sem Docker, o frontend continua a correr com o seu servidor de desenvolvimento.

**Blocked by:** 01 (Contentor da API e docker compose), frontend 01 (Esqueleto do frontend e login por token)

**Status:** ready-for-agent

- [ ] Imagem multi-etapa do frontend, com o código compilado servido por um servidor estático mínimo, sem segredos no código compilado
- [ ] `/api` encaminhado para o contentor da API, na mesma origem, para que o cookie de sessão funcione
- [ ] Os cabeçalhos de segurança de SEC-11 aplicados ao frontend servido
- [ ] Porta publicada só em `127.0.0.1`
- [ ] Sem Docker, o servidor de desenvolvimento do frontend continua a funcionar
- [ ] O `README.md` documenta o arranque completo com e sem Docker
- [ ] Verificação: `docker compose up`, abrir o endereço, entrar com o token e ver o estado do servidor
