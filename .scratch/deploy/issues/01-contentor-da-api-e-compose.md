# 01: Contentor da API e docker compose

**What to build:** Quem receber o projecto arranca a API com `docker compose up`, sem instalar Python, e com os dados num volume que sobrevive a reinícios. Continua a ser possível arrancar sem Docker, exactamente como hoje.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] Imagem multi-etapa, com base mínima oficial fixada por digest, a correr como utilizador não privilegiado e com o sistema de ficheiros em leitura apenas excepto o volume
- [x] A porta é publicada só em `127.0.0.1`; dentro do contentor o servidor escuta onde o contentor exige, e esse é o único sítio onde isso acontece (SEC-06)
- [x] A configuração entra por variáveis de ambiente a partir de `config/.env`, sem segredos na imagem
- [x] O catálogo e a lista de exclusão chegam ao contentor; a base de dados e os ficheiros carregados ficam no volume
- [x] Sem Docker, `make install` e `make run` continuam a funcionar
- [x] O `README.md` documenta os dois caminhos, com e sem Docker, lado a lado
- [x] Verificação: o contentor arranca, `/api/health` responde, e um carregamento sobrevive a um reinício

## Comments

Resolved on 2026-11-19. The owner accepted the one exception to the 127.0.0.1 rule: the API listens on 0.0.0.0 only in the CMD of backend/Dockerfile, with ports published on 127.0.0.1 (docs/00 §3.26). Checked: the container is healthy, runs as uid 10001 with a read-only root, `/api/health` answers, and a job survives a restart.
