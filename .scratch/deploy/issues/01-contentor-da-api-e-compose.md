# 01: Contentor da API e docker compose

**What to build:** Quem receber o projecto arranca a API com `docker compose up`, sem instalar Python, e com os dados num volume que sobrevive a reinícios. Continua a ser possível arrancar sem Docker, exactamente como hoje.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Imagem multi-etapa, com base mínima oficial fixada por digest, a correr como utilizador não privilegiado e com o sistema de ficheiros em leitura apenas excepto o volume
- [ ] A porta é publicada só em `127.0.0.1`; dentro do contentor o servidor escuta onde o contentor exige, e esse é o único sítio onde isso acontece (SEC-06)
- [ ] A configuração entra por variáveis de ambiente a partir de `config/.env`, sem segredos na imagem
- [ ] O catálogo e a lista de exclusão chegam ao contentor; a base de dados e os ficheiros carregados ficam no volume
- [ ] Sem Docker, `make install` e `make run` continuam a funcionar
- [ ] O `README.md` documenta os dois caminhos, com e sem Docker, lado a lado
- [ ] Verificação: o contentor arranca, `/api/health` responde, e um carregamento sobrevive a um reinício
