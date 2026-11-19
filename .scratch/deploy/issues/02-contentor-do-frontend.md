# 02: Contentor do frontend no compose

**What to build:** `docker compose up` arranca também o frontend compilado, servido por um servidor estático que encaminha `/api` para a API, de forma que a pessoa abre um só endereço, entra com o token e usa a aplicação. Sem Docker, o frontend continua a correr com o seu servidor de desenvolvimento.

**Blocked by:** 01 (Contentor da API e docker compose), frontend 01 (Esqueleto do frontend e login por token)

**Status:** resolved

- [x] Imagem multi-etapa do frontend, com o código compilado servido por um servidor estático mínimo, sem segredos no código compilado
- [x] `/api` encaminhado para o contentor da API, na mesma origem, para que o cookie de sessão funcione
- [x] Os cabeçalhos de segurança de SEC-11 aplicados ao frontend servido
- [x] Porta publicada só em `127.0.0.1`
- [x] Sem Docker, o servidor de desenvolvimento do frontend continua a funcionar
- [x] O `README.md` documenta o arranque completo com e sem Docker
- [x] Verificação: `docker compose up`, abrir o endereço, entrar com o token e ver o estado do servidor

## Comments

Resolved on 2026-11-19 (CHG-0071). Checked in a separate compose project on ports 18000/18080: both containers healthy, every SEC-11 header on pages, assets and /api, sign-in through nginx answers 204 with the session cookie, the session check and the health answer through the same address, and a job survives `docker compose down` and `up`. The nginx base is the slim mainline variant: 3 HIGH findings left (musl, zlib), fixed upstream but not yet in the image.

Review fixes on 2026-11-19 (CHG-0072): uploads spooled to the volume, nginx listen address explicit and recorded in decision 3.26, allowlisted build context. A sign-in in a real browser on port 8080 is still to be done by a person.
