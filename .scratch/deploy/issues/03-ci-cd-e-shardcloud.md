# 03: CI/CD, imagem versionada no Docker Hub e publicação na ShardCloud

**What to build:** A cada push corre o CI. Uma tag `vX.Y.Z` publica a versão: imagem `X.Y.Z` no repositório privado do Docker Hub e, depois de aprovação, a mesma versão na ShardCloud, com HTTPS. Pedido pelo responsável em 19-11-2026.

**Blocked by:** 01 e 02 do deploy

**Status:** resolved

- [x] Workflow de CI em cada push e pull request, sem segredos
- [x] Workflow de release numa tag `vX.Y.Z`: CI completo, imagem versionada no Docker Hub privado, scan
- [x] Deploy na ShardCloud depois de aprovação no ambiente `production`: backup, reconstrução da imagem a partir do mesmo contexto, reinício, verificação da versão pública
- [x] Imagem única para a ShardCloud (nginx na porta 80, API em 127.0.0.1), sem documentação da API, com a versão no health check
- [x] Decisão 3.27, SEC-06 e L-07 revistos; README com a configuração única

## Comments

Owner's answers on 19-11-2026: public with the access token (AMT to confirm data at ShardCloud before real use); same version to Docker Hub and ShardCloud (ShardCloud cannot pull a private registry image); a backup before each deploy; a tag vX.Y.Z publishes, behind manual approval. Nothing was published by the agent: the first release needs the one-time setup of the README and a tag pushed by the owner.
