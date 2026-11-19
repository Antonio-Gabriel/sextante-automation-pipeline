# Registo de Alterações

Regista cada alteração à aplicação com o seu identificador, a alteração de que parte e a forma de a reverter. A obrigação de registar está no `CLAUDE.md`, na secção «Registo de alterações».

## Árvore

Cada alteração aparece por baixo daquela de que parte. A entrada mais recente de um ramo é o estado actual desse ramo.

```
CHG-0001  docs      Documentação inicial do projecto
├── CHG-0002  docs      Configuração dos skills de engenharia
└── CHG-0003  docs      Glossário e pontos em aberto da sessão de grilling
    └── CHG-0004  docs      Especificação do núcleo de codificação
        └── CHG-0005  docs      Tickets 01 a 13 e emenda pelas amostras
            └── CHG-0006  docs      Alinhamento dos documentos de desenho
                └── CHG-0007  security  Limite de itens enviados ao modelo
                    └── CHG-0008  infra     Repositório git
                        └── CHG-0009  feat      Arranque com catálogo validado
                            └── CHG-0010  fix       Correcções da revisão do ticket 01
                                └── CHG-0011  feat      Carregamento e codificação em segundo plano
                                    └── CHG-0012  fix       Correcções da revisão do ticket 02
                                        ├── CHG-0013  docs      Registo de alterações e a sua regra
                                        └── CHG-0014  infra     Graphify como memória do projecto
                                            └── CHG-0015  infra     Skill do graphify no projecto e correcção da CHG-0014
                                                └── CHG-0016  docs      Diagramas regenerados com o desenho actual
                                                    └── CHG-0017  feat      Verificação de entidade e encaminhamento para OUTLAYSP
                                                        └── CHG-0018  feat      Confiança, recurso e sinalização
                                                            └── CHG-0019  fix       Correcções da revisão dos tickets 03 e 04
                                                                └── CHG-0020  feat      Tipos de linha
                                                                    └── CHG-0021  feat      Exportação em CSV e XLSX
                                                                        └── CHG-0022  fix       Correcções da revisão dos tickets 05 e 06
                                                                            └── CHG-0023  feat      Trabalhador robusto e reprocessamento
                                                                                └── CHG-0024  feat      Revisão de linhas
                                                                                    └── CHG-0025  fix       Correcções da revisão dos tickets 07 e 08
                                                                                        └── CHG-0026  docs      Isenção do carregamento e reprocessamento só de falhas
                                                                                            └── CHG-0027  feat      Resolução de entidade e duplicado provável
                                                                                                └── CHG-0028  fix       Correcções da revisão dos tickets 09 e 10
                                                                                                    └── CHG-0029  improve   Saída da resolução humana e do duplicado provável
                                                                                                        └── CHG-0030  feat      Extracção de PDF nativo no modelo das amostras
                                                                                                            └── CHG-0031  feat      Conjunto dourado sem o modelo
                                                                                                                └── CHG-0032  fix       Correcções da revisão dos tickets 12 e 13
                                                                                                                    └── CHG-0033  docs      Histórico sem Co-Authored-By e hashes actualizados
                                                                                                                        └── CHG-0034  fix       Réplicas sem dados das amostras, XLSX recusado e padrão do conjunto dourado
                                                                                                                            └── CHG-0035  feat      Adaptador Claude do ItemClassifier e prompt v1
                                                                                                                                └── CHG-0036  feat      Medição manual dos códigos com o modelo real
                                                                                                                                    └── CHG-0037  fix       Correcções da revisão dos tickets 11 e 13
                                                                                                                                        └── CHG-0038  docs      Fornecedor e moeda no pedido ao modelo (REQ-MAP-005)
                                                                                                                                            └── CHG-0039  security  Repositório e histórico sem dados das amostras
                                                                                                                                                └── CHG-0040  infra     Catálogo no repositório, sem metadados pessoais
                                                                                                                                                    └── CHG-0041  improve   Modelo por omissão passa a Sonnet
                                                                                                                                                        └── CHG-0042  improve   Prompt v2 com cache de prompt
                                                                                                                                                            └── CHG-0043  feat      Recodificação com histórico
                                                                                                                                                                └── CHG-0044  fix       Correcções da revisão do ticket 14
                                                                                                                                                                    └── CHG-0045  docs      Pasta sources fora do .gitignore e regra dos pedidos repetidos confirmada
                                                                                                                                                                        └── CHG-0046  fix       Idempotency-Key declarado na documentação da API
                                                                                                                                                                            └── CHG-0047  security  Chave da API em todo o /api excepto health
                                                                                                                                                                                └── CHG-0048  docs      Tickets do frontend, da operação e do deploy
                                                                                                                                                                                    └── CHG-0049  security  Limites de taxa por endpoint
                                                                                                                                                                                        └── CHG-0050  fix       Correcções da revisão dos limites de taxa
                                                                                                                                                                                            └── CHG-0051  security  Tecto de chamadas ao modelo no trabalhador
                                                                                                                                                                                                └── CHG-0052  fix       Correcções da revisão do tecto de chamadas ao modelo
                                                                                                                                                                                                    └── CHG-0053  security  Extracção de PDF isolada com limites
                                                                                                                                                                                                        └── CHG-0054  fix       Correcções da revisão da extracção isolada
                                                                                                            └── CHG-0055  feat      Esqueleto do frontend e login por token
                                                                                                                └── CHG-0056  fix       Correcções da revisão do ticket 01 do frontend
                                                                                                                    └── CHG-0057  feat      Painel AMT e carregamento com progresso
                                                                                                                        └── CHG-0058  fix       Correcções da revisão do ticket 02 do frontend
                                                                                                                            └── CHG-0059  feat      Resultados com filtros na rota
                                                                                                                                └── CHG-0060  fix       Correcções da revisão do ticket 03 do frontend
                                                                                                                                    └── CHG-0061  feat      Ecrã da factura e resolução de entidade
                                                                                                                                        └── CHG-0062  fix       Correcções da revisão do ticket 05 do frontend
                                                                                                                                            └── CHG-0063  feat      Revisão de linha
                                                                                                                                                └── CHG-0064  feat      Exportação e reprocessamento na interface
                                                                                                                                                    └── CHG-0065  fix       Correcções da revisão dos tickets 04 e 06 do frontend
                                                                                                                                                        └── CHG-0066  feat      Lista e apagamento lógico de trabalhos, e UX da tabela e do carregamento
                                                                                                                                                            └── CHG-0067  fix       Correcções da revisão do ticket 07 do frontend
                                                                                                                                                                └── CHG-0068  feat      Interface em Inglês e Português, com os textos do servidor no idioma escolhido
                                                                                                                                                                    └── CHG-0069  fix       Correcções da revisão da interface em dois idiomas
                                                                                                                                                                        └── CHG-0070  infra     Contentor da API e docker compose
                                                                                                                                                                            └── CHG-0071  infra     Contentor do frontend e correcções da revisão do contentor da API
                                                                                                                                                                                └── CHG-0072  fix       Correcções da revisão do contentor do frontend
                                                                                                                                                                                    └── CHG-0073  fix       API sem rede depois de um conflito de porta, e ecrã de erro da página
                                                                                                                                                                                        └── CHG-0074  infra     CI/CD no GitHub Actions, imagem no Docker Hub e publicação na ShardCloud
                                                                                                                                                                                            └── CHG-0075  fix       Correcções da revisão do CI/CD e da publicação na ShardCloud
                                                                                                                                                                                                └── CHG-0076  fix       Versão escrita no contexto da ShardCloud
                                                                                                                                                                                                    └── CHG-0077  infra     Assistente da configuração única da ShardCloud, do Docker Hub e do GitHub
                                                                                                                                                                                                        └── CHG-0078  fix       Assistente parado com uma resposta vazia
                                                                                                                                                                                                            └── CHG-0079  fix       Assistente explica a recusa do token da ShardCloud
                                                                                                                                                                                                                └── CHG-0080  fix       Retirada a recusa de tokens de audiência /mcp
                                                                                                                                                                                                                    └── CHG-0081  fix       Assistente mostra a razão da ShardCloud para uma recusa
                                                                                                                                                                                                                        └── CHG-0082  infra     Deploy na ShardCloud por um repositório de deploy
                                                                                                                                                                                                                            └── CHG-0083  fix       Assistente aceita o endereço da app em qualquer forma
                                                                                                                                                                                                                                └── CHG-0084  fix       O desafio do Cloudflare no endereço da app é detectado
                                                                                                                                                                                                                                    └── CHG-0085  fix       Deploy com caminho relativo, e deploy automático opcional
                                                                                                                                                                                                                                        └── CHG-0086  fix       Artefacto do release com o Dockerfile na raiz
                                                                                                                                                                                                                                            └── CHG-0087  infra     O release acaba no zip; sem deploy automático na ShardCloud
                                                                                                                                                                                                                                                └── CHG-0088  fix       Imagem da ShardCloud a correr com qualquer utilizador
                                                                                                                                                                                                                                                    └── CHG-0089  fix       Imagem da ShardCloud como root sem capacidades
                                                                                                                                                                                                                                                        └── CHG-0090  fix       Código fora do directório de trabalho da imagem da ShardCloud
```

## Regras

1. **Quando registar.** Regista-se toda a alteração a:
   - código, testes ou migrações;
   - infraestrutura, dependências ou configuração da aplicação;
   - documentos que definem o comportamento da aplicação (`docs/`, `CLAUDE.md`, `GLOSSARY.md`, a spec e os tickets).
2. **Identificador.** `CHG-nnnn`, sequencial e nunca reutilizado.
3. **Alteração-pai.** É o último `CHG` do ramo em que se trabalhou. Alterações paralelas têm o mesmo pai.
4. **Imutabilidade.** Uma entrada nunca é reescrita nem apagada. Só os campos `Estado` e `Commit` podem ser actualizados.
5. **Reversão.** Uma reversão é uma entrada nova, do tipo `rollback`, cujo pai é a alteração revertida. A entrada revertida passa ao estado `revertida por CHG-nnnn`.
6. **Ordem.** As entradas ficam da mais recente para a mais antiga.
7. **Commit.** Uma alteração e a sua entrada entram no mesmo commit, com `Changelog: CHG-nnnn` na mensagem. Nesse momento o campo `Commit` fica `pendente`; o hash é preenchido no commit seguinte, como permite a regra 4.

### Tipos

| Tipo | Uso |
|---|---|
| `feat` | Funcionalidade nova |
| `improve` | Melhoria de funcionalidade existente |
| `fix` | Correcção de defeito |
| `security` | Controlo ou correcção de segurança |
| `test` | Apenas testes |
| `migration` | Esquema ou dados |
| `infra` | Contentores, dependências, configuração |
| `docs` | Documentos que definem o comportamento |
| `rollback` | Reversão de uma alteração anterior |

### Reversibilidade

| Valor | Significado |
|---|---|
| `total` | Reverter o commit repõe o estado anterior |
| `parcial` | Parte fica. O campo `Reversão` diz qual |
| `não` | Não se pode reverter. O campo `Reversão` diz a alternativa, por exemplo uma correcção posterior |

Três casos estão sempre limitados:

- **Auditoria.** Os registos de `audit_event` são só de inserção (SEC-04, REQ-AUD-002): nunca se libertam nem se alteram, e nenhuma reversão os pode apagar.
- **Migração que remove dados.** É, no máximo, `parcial`, salvo se o campo `Reversão` indicar uma salvaguarda da base de dados.
- **Pedido ao modelo.** Uma factura já enviada ao modelo não se "desenvia". Reverter o código não desfaz essa chamada.

### Modelo de entrada

```markdown
### CHG-nnnn · <título curto>

- **Data:** AAAA-MM-DD
- **Tipo:** feat
- **Pai:** CHG-nnnn
- **Estado:** activa | revertida por CHG-nnnn
- **Requisitos:** REQ-xxx-nnn, NFR-xxx-nnn, SEC-nn, D-n.n, L-nn, ou "nenhum"
- **Commit:** <hash> | pendente
- **Migração:** <revisão Alembic e revisão anterior>, ou "nenhuma"
- **Ficheiros:** <caminhos principais>
- **Reversibilidade:** total | parcial | não
- **Reversão:** <passos exactos, incluindo migração, índice e configuração>
- **Verificação:** <o que foi corrido e o que não foi verificado>

<Uma ou duas frases: o que mudou e porquê.>
```

## Alterações

### CHG-0090 · Código fora do directório de trabalho da imagem da ShardCloud

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0089
- **Estado:** activa
- **Requisitos:** REQ-PLT-008
- **Commit:** pendente
- **Migração:** nenhuma
- **Ficheiros:** `deploy/shardcloud/Dockerfile`, `deploy/shardcloud/entrypoint.sh`, `deploy/shardcloud/nginx.conf`, `backend/tests/deploy/test_container_config.py`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:**
  - `tests/deploy` com 32 testes.
  - Imagem construída sem argumentos e corrida de cinco formas. Em todas, o *health check* deu a versão e as páginas responderam 200:
    - como na ShardCloud (root sem capacidades excepto `CHOWN`, volume vazio montado no directório de trabalho, `PATH`, `PYTHONPATH`, versão e caminhos da imagem apagados);
    - o mesmo volume outra vez, para confirmar que os dados ficam;
    - root com capacidades;
    - utilizador 4242;
    - root sem nenhuma capacidade.

**Relato do responsável.** Com CHG-0089 a app parou com `ModuleNotFoundError: No module named 'sextante'`. O código estava em `/app/src`, o directório de trabalho da imagem. A explicação mais provável, que junta este erro ao da pasta `/data`, é que a ShardCloud monta o seu armazenamento persistente (a aba Files) sobre o directório de trabalho e esconde o que a imagem lá tinha. A documentação da ShardCloud não o diz.

**Correcções.**
- **Código fora do directório de trabalho.** Tudo o que a app precisa vive em `/opt`: código, migrações (`platform/database.py` encontra-as em `/opt/sextante/migrations`), páginas, catálogo e lista de exclusão.
- **`WORKDIR /data`.** Onde a ShardCloud montar o seu armazenamento, a base de dados e as facturas ficam nele e sobrevivem a novos deploys.
- **Caminhos no *entrypoint*.** O *entrypoint* define ele próprio `PATH`, `PYTHONPATH`, os caminhos do catálogo e da lista de exclusão e o desligar da documentação da API. Não depende do `ENV` da imagem.
- **Versão em ficheiro.** A versão fica também em `/opt/sextante/VERSION`.
- **Teste novo:** nada é copiado para o directório de trabalho, e o *entrypoint* define os caminhos.

### CHG-0089 · Imagem da ShardCloud como root sem capacidades

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0088
- **Estado:** activa
- **Requisitos:** REQ-PLT-008, SEC-04
- **Commit:** `80cc502`
- **Migração:** nenhuma
- **Ficheiros:** `deploy/shardcloud/entrypoint.sh`, `deploy/shardcloud/nginx.conf`, `backend/tests/deploy/test_container_config.py`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:**
  - `tests/deploy` com 31 testes.
  - Imagem construída sem argumentos e corrida de cinco formas; em todas, o *health check* e as páginas responderam:
    - root com capacidades: dados do uid 10001;
    - root sem capacidades (`--cap-drop ALL`, o caso da ShardCloud): dados do uid 0;
    - utilizador 4242: dados do uid 4242;
    - root com capacidades num volume;
    - depois, root sem capacidades excepto `CHOWN` no mesmo volume, deixado pelo uid 10001: dados retomados pelo uid 0.

**Relato do responsável.** Com CHG-0088 a app passou a falhar com `setpriv: setresuid failed: Operation not permitted`. A ShardCloud corre o contentor como root, mas sem as capacidades de mudar de utilizador. O `chown` do arranque anterior funcionou, por isso a capacidade `CHOWN` existe.

**Correcções.**
- **Largar privilégios só se der.** O *entrypoint* experimenta primeiro mudar de utilizador e só larga os privilégios se isso funcionar. Não funcionando, os dois processos ficam com o utilizador recebido.
- **Pastas de outro dono.** Uma pasta deixada a outro dono por um arranque anterior é retomada: primeiro cada pasta, para se poder ler o seu conteúdo, depois tudo o que está dentro.
- **nginx.** O `user www-data` sai de `nginx.conf` e passa ao *entrypoint*, só onde mudar de utilizador funciona. Como root sem capacidades, o nginx serve num só processo como root, sem mudar o dono das suas pastas temporárias, o que falhava com `chown … failed`.

**Efeito na segurança, declarado.** Na ShardCloud, a API e o nginx correm como uid 0 sem capacidades. Não há a separação de utilizadores que existe noutros sítios, porque a plataforma não a permite. Sem capacidades, o root do contentor não pode mudar de utilizador, montar sistemas de ficheiros nem ligar-se a portas além das permitidas. A API continua só em `127.0.0.1`. Fica registado como risco residual da instalação na ShardCloud (§3.27).

### CHG-0088 · Imagem da ShardCloud a correr com qualquer utilizador

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0087
- **Estado:** activa
- **Requisitos:** REQ-PLT-008, SEC-04
- **Commit:** `1548c82`
- **Migração:** nenhuma
- **Ficheiros:** `deploy/shardcloud/Dockerfile`, `deploy/shardcloud/entrypoint.sh`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:**
  - `tests/deploy` com 31 testes.
  - Imagem construída sem argumentos, como a ShardCloud a constrói. Foi corrida localmente de três formas:
    - como root: *health check* com a versão, ficheiros `-rw-------` do uid 10001;
    - como o utilizador arbitrário 4242: *health check* com a versão, ficheiros `-rw-------` do uid 4242;
    - como 4242 sem a regra que deixa portas baixas sem root: a porta 80 abriu na mesma.

**Relato do responsável.** A imagem foi construída na ShardCloud, mas a app parou ao arrancar com `mkdir: cannot create directory '/data': Permission denied`. A ShardCloud não corre o contentor como root, e `/data` não existia em execução. O `VOLUME` provavelmente fez o construtor deles deixar a pasta de fora. A imagem supunha root.

**Correcções.**
- **`/data`:** sem `VOLUME`, gravável por qualquer utilizador (`1777`). O `umask 077` mantém cada ficheiro privado do seu dono.
- **Pasta de dados configurável** por `SEXTANTE_DATA_DIR`. O *entrypoint* deriva dela a base de dados, os carregamentos e os temporários, e pára com uma mensagem clara se a pasta não for gravável.
- **Sem privilégios a largar:** como root, entrega a pasta ao uid 10001 e larga os privilégios como antes; com outro utilizador, corre directamente com ele.
- **nginx com `-e stderr`:** nunca precisa de um `/var/log` gravável.

**Em aberto.** A ShardCloud não documenta que pasta do contentor persiste. A aba Files da app mostra-a. Se não for `/data`, aponta-se `SEXTANTE_DATA_DIR` para ela nas variáveis da app.

### CHG-0087 · O release acaba no zip; sem deploy automático na ShardCloud

- **Data:** 2026-11-19
- **Tipo:** infra
- **Pai:** CHG-0086
- **Estado:** activa
- **Requisitos:** REQ-PLT-008
- **Commit:** `c111278`
- **Migração:** nenhuma
- **Ficheiros:** `.github/workflows/release.yml`, `scripts/setup_shardcloud.sh`, `deploy/shardcloud/push_context.sh` e `deploy/shardcloud/wait_for_release.sh` (apagados), `backend/tests/deploy/test_shardcloud_deploy.py` (apagado), `backend/tests/deploy/test_workflows.py`, `docs/00` §3.29, `README.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** backend com 459 testes e 1 xfail (os testes do deploy por repositório saíram com ele); `tests/deploy` com 31 testes. Um teste garante que o release só tem os trabalhos `ci` e `publish` e não fala com `shardcloud.app`.

**Pedido do responsável.** O trabalho de deploy da v1.0.1 enviou o contexto e ficou à espera do endereço público. Esse endereço está atrás do desafio do Cloudflare e o runner via-o como «sem resposta». O responsável pediu que o release gere apenas o zip.

**Release.** Fica CI, a imagem no Docker Hub e o artefacto com o contexto. O resumo diz como pôr a versão na ShardCloud: Rebuild com o zip, backup, Restart e confirmação no navegador.

**Assistente.** Fica com cinco fases: ferramentas, o repositório e o token do Docker Hub (segredos e variável no GitHub), a imagem na ShardCloud a partir de um zip montado localmente, e a app, com a confirmação no navegador. Já não cria o repositório de deploy, a *deploy key* nem o ambiente `production`.

**Arrumação pelo responsável, opcional (§3.29).** Pode apagar o que já não se usa: o repositório `sextante-shardcloud`, o segredo `SHARDCLOUD_DEPLOY_KEY`, as variáveis `SHARDCLOUD_DEPLOY_REPOSITORY` e `SHARDCLOUD_URL`, e o ambiente `production`.

### CHG-0086 · Artefacto do release com o Dockerfile na raiz

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0085
- **Estado:** activa
- **Requisitos:** REQ-PLT-008
- **Commit:** `84b4120`
- **Migração:** nenhuma
- **Ficheiros:** `.github/workflows/release.yml`, `backend/tests/deploy/test_workflows.py`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** `tests/deploy` com 38 testes. O contexto montado não tem ficheiros escondidos, que o `upload-artifact` deixaria de fora, e tem o `Dockerfile` na raiz.

**Relato do responsável.** A ShardCloud recusou `shardcloud-context.zip` com «must contain a Dockerfile at its root». O GitHub embrulha sempre um artefacto num zip, e esse zip continha outro zip, `sextante-1.0.0.zip`.

**Correcção.** O artefacto passa a ser o próprio directório do contexto, `sextante-X.Y.Z-shardcloud`. O zip que o GitHub dá para descarregar tem o `Dockerfile` na raiz e envia-se à ShardCloud tal como está. O trabalho de deploy descarrega o mesmo artefacto para um directório e envia-o. O zip intermédio desaparece.

**Para a v1.0.0, já publicada:** descomprimir `shardcloud-context.zip` e enviar o `sextante-1.0.0.zip` de dentro.

### CHG-0085 · Deploy com caminho relativo, e deploy automático opcional

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0084
- **Estado:** activa
- **Requisitos:** REQ-PLT-008
- **Commit:** `a0e5c1b`
- **Migração:** nenhuma
- **Ficheiros:** `deploy/shardcloud/push_context.sh`, `.github/workflows/release.yml`, `backend/tests/deploy/test_shardcloud_deploy.py`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** `tests/deploy` com 37 testes, incluindo o caminho relativo tal como o release o passa. O log do trabalho que falhou foi lido com o `gh` do responsável: `cp: cannot stat 'build/context/.'`.

**Defeito, no primeiro release real (v1.0.0).** `push_context.sh` recebia o contexto como caminho relativo e copiava-o depois de entrar no clone, onde esse caminho não existe. Os testes passavam caminhos absolutos. O caminho passa a ser resolvido antes da cópia.

**Deploy automático opcional, a pedido.** Se a variável `SHARDCLOUD_DEPLOY_REPOSITORY` não existir, o trabalho de deploy não corre e o release acaba no zip. Em qualquer caso, o resumo do trabalho de publicação mostra a imagem do Docker Hub, o nome do zip e os passos para o enviar à mão.

**v1.0.0.** A imagem e o zip dessa versão ficaram publicados. Só o envio para o repositório de deploy falhou.

### CHG-0084 · O desafio do Cloudflare no endereço da app é detectado

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0083
- **Estado:** activa
- **Requisitos:** REQ-PLT-008
- **Commit:** `9021350`
- **Migração:** nenhuma
- **Ficheiros:** `deploy/shardcloud/wait_for_release.sh`, `.github/workflows/release.yml`, `scripts/setup_shardcloud.sh`, `backend/tests/deploy/test_shardcloud_deploy.py`, `docs/00` §3.28
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** `tests/deploy` com 36 testes, incluindo o desafio, que termina com o código 2 sem esperar. O agente pediu `https://sextante.shardweb.app/` e `/api/health` sem credencial: ambos responderam 403 com `cf-mitigated: challenge` e «Just a moment…».

**Relato do responsável.** A fase 6 do assistente esperava sem fim, com «no answer». O endereço da app também está atrás do desafio do Cloudflare, que responde com uma página HTML. O script lia essa página como «sem resposta».

**Correcções.**
- `wait_for_release.sh` reconhece o cabeçalho `cf-mitigated: challenge`, pára com o código 2 e diz o que confirmar no navegador. O desafio não é contornado.
- O release, com o código 2, acrescenta ao resumo o passo de confirmar a versão no navegador e não falha.
- O assistente abre o endereço no navegador e pergunta se mostra a versão.
- Corrido de novo, o assistente já não obriga a gerar uma *deploy key* nova quando o segredo já existe.

**Consequência registada em §3.28.** Os programas não conseguem usar a API do Sextante publicado com `X-API-Key` enquanto o desafio estiver activo. As pessoas, no navegador, conseguem.

### CHG-0083 · Assistente aceita o endereço da app em qualquer forma

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0082
- **Estado:** activa
- **Requisitos:** REQ-PLT-008
- **Commit:** `a34091c`
- **Migração:** nenhuma
- **Ficheiros:** `scripts/setup_shardcloud.sh`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** `bash -n` sem erros. A normalização foi testada com quatro formas: `sextante`, `sextante.shardweb.app`, `https://sextante.shardweb.app/` e `http://sextante.shardweb.app/api`. Todas dão `sextante`.

**Relato do responsável.** A fase 6 só aceitava o subdomínio sozinho e recusava `sextante.shardweb.app` e `https://sextante.shardweb.app`, sem dizer porquê. Passa a aceitar o subdomínio, o anfitrião ou o endereço, e mostra o endereço que vai usar.

### CHG-0082 · Deploy na ShardCloud por um repositório de deploy

- **Data:** 2026-11-19
- **Tipo:** infra
- **Pai:** CHG-0081
- **Estado:** activa
- **Requisitos:** REQ-PLT-008, SEC-02, SEC-06
- **Commit:** `a5bfd14`
- **Migração:** nenhuma
- **Ficheiros:** `deploy/shardcloud/push_context.sh` e `deploy/shardcloud/wait_for_release.sh` (novos), `deploy/shardcloud/deploy.sh` (apagado), `.github/workflows/release.yml`, `scripts/setup_shardcloud.sh`, `backend/tests/deploy/test_shardcloud_deploy.py` (reescrito), `.gitignore`, `docs/00` §3.28, `README.md`
- **Reversibilidade:** total no repositório. O repositório de deploy e a *deploy key* criados pelo assistente apagam-se no GitHub.
- **Reversão:** reverter o commit.
- **Verificação:**
  - Backend: 463 testes e 1 xfail; `tests/deploy` com 35 testes. `push_context.sh` foi testado contra um repositório git local, e `wait_for_release.sh` contra um servidor local.
  - A chave de anfitrião ed25519 do github.com foi conferida em `api.github.com/meta`.
  - O assistente não foi corrido pelo agente.

**Problema.** A API REST da ShardCloud (`/api/*`) responde com um desafio do Cloudflare a clientes automáticos, tanto ao `curl` como à CLI oficial. O agente leu o código da CLI (`shard-cloud-cli` 2.0.0, do npm, com integridade verificada, e o código Go de `github.com/shard-cloud/cli`) e confirmou que usa o mesmo endereço e a mesma autenticação. O desafio não é contornado (`CLAUDE.md`). As alternativas foram dadas ao responsável, que escolheu o repositório de deploy (§3.28).

**Pipeline.** Depois da aprovação, `push_context.sh` substitui o `main` do repositório de deploy pelo contexto da versão, num só commit «Release X.Y.Z». Recusa um contexto sem `Dockerfile` na raiz. A *deploy key* vem de um segredo, com a chave de anfitrião do github.com fixada e `StrictHostKeyChecking=yes`. O resumo do trabalho diz o que fazer na ShardCloud: esperar pela construção, fazer o backup e reiniciar a app. `wait_for_release.sh` espera até 60 minutos pela versão no endereço público.

**Assistente.** Já não chama a API da ShardCloud. Usa o `gh` e o `ssh-keygen` locais para:
- criar o repositório privado de deploy;
- gerar a *deploy key*, registá-la com escrita e guardá-la como o segredo `SHARDCLOUD_DEPLOY_KEY`, sem nunca a escrever num ficheiro do projecto;
- enviar o primeiro contexto e deixar o mesmo como `build/sextante-setup.zip`.

No dashboard da ShardCloud, guia a ligação ao GitHub, a imagem ligada ao repositório e a app com as variáveis. A chave da API e o token de acesso são gerados e mostrados uma vez, e o ecrã limpa-se depois.

**Perde-se:** o backup e o reinício automáticos de §3.27, que passam a ser feitos à mão no dashboard até a API aceitar a chave.

### CHG-0081 · Assistente mostra a razão da ShardCloud para uma recusa

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0080
- **Estado:** activa
- **Requisitos:** REQ-PLT-008
- **Commit:** `4ba11ee`
- **Migração:** nenhuma
- **Ficheiros:** `scripts/setup_shardcloud.sh`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** `bash -n` sem erros.

**Relato do responsável.** Com o plano Core 1 activo, `GET /custom-images` continua a responder 403. A mensagem do assistente, «sem plano activo», era uma suposição errada. O assistente passa a mostrar o código e a resposta da própria ShardCloud, até 500 caracteres; essa resposta nunca contém a chave. Fica em aberto se a API Key de Settings → Integrations, de audiência `…/api/mcp`, serve a API REST, ou se o plano Core 1 inclui imagens personalizadas.

### CHG-0080 · Retirada a recusa de tokens de audiência /mcp

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0079
- **Estado:** activa
- **Requisitos:** REQ-PLT-008
- **Commit:** `548a0ee`
- **Migração:** nenhuma
- **Ficheiros:** `scripts/setup_shardcloud.sh`, `README.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** `bash -n` sem erros.

**Correcção de CHG-0079.** O responsável confirmou que o token veio de Settings → Integrations → API Key, a chave da API REST. Essa chave também tem a audiência `…/api/mcp`. A suposição de CHG-0079 estava errada, e a recusa impediria a chave certa. É retirada. O caminho no assistente e no README passa a ser o real: Settings → Integrations → API Key → Manage. O 403 explica-se pela falta de um plano activo, que o assistente já diz, com o caminho Settings → Plan & Billing.

### CHG-0079 · Assistente explica a recusa do token da ShardCloud

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0078
- **Estado:** activa
- **Requisitos:** REQ-PLT-008, SEC-02
- **Commit:** `5fbb598`
- **Migração:** nenhuma
- **Ficheiros:** `scripts/setup_shardcloud.sh`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** `bash -n` sem erros. A leitura da audiência foi testada com um JWT sintético (`aud` terminado em `/mcp`) e com um valor que não é JWT. O token real do responsável não foi usado.

**Relato do responsável.** A fase 4 parou com um 403. No `openapi.json` da ShardCloud, o 403 de `/custom-images` significa «No valid subscription». O token mostrado tinha a audiência `https://shardcloud.app/api/mcp`, que é o da integração MCP e não o da API REST de Settings → API Token.

**Correcção.** O assistente lê localmente a audiência do token, sem o enviar a lado nenhum, e recusa um token de MCP dizendo onde se cria o certo. O 401, o 403 (falta de plano activo), a falta de rede e os outros códigos passam a ter mensagens próprias.

**Segurança.** O token foi colado na conversa. Recomendou-se revogá-lo na ShardCloud e criar outro, a escrever só na entrada escondida do assistente.

### CHG-0078 · Assistente parado com uma resposta vazia

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0077
- **Estado:** activa
- **Requisitos:** REQ-PLT-008
- **Commit:** `5fed31e`
- **Migração:** nenhuma
- **Ficheiros:** `scripts/setup_shardcloud.sh`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** `bash -n` sem erros. A pergunta nova foi testada sem terminal: Enter numa pergunta com sugestão dá a sugestão (`<utilizador>/sextante`), e uma resposta inválida é recusada e pedida de novo.

**Defeito relatado pelo responsável.** Na fase 2, a pergunta do repositório recebeu Enter. O exemplo entre parênteses não era um valor por omissão, por isso o valor ficou vazio. `gh variable set` com corpo vazio fica à espera de um valor no terminal, sem o dizer, e o assistente parecia parado.

**Correcção.** Uma pergunta nova, `ask_required`, repete-se até a resposta ter a forma esperada, e o Enter aceita a sugestão quando há uma. Passa a servir:
- o utilizador e o repositório do Docker Hub;
- a entidade alvo e o NIF;
- o revisor;
- o subdomínio;
- a memória.

Os valores por omissão, quando existem, aparecem na própria pergunta.

### CHG-0077 · Assistente da configuração única da ShardCloud, do Docker Hub e do GitHub

- **Data:** 2026-11-19
- **Tipo:** infra
- **Pai:** CHG-0076
- **Estado:** activa
- **Requisitos:** REQ-PLT-008, SEC-02
- **Commit:** `628f579`
- **Migração:** nenhuma
- **Ficheiros:** `scripts/setup_shardcloud.sh` (novo), `backend/tests/deploy/test_workflows.py`, `README.md`
- **Reversibilidade:** total no repositório. O que o assistente cria na ShardCloud, no Docker Hub e no GitHub apaga-se lá.
- **Reversão:** reverter o commit.
- **Verificação:**
  - `bash -n` sem erros. Teste novo: o assistente define exactamente os segredos e as variáveis que o release lê. `tests/deploy` com 37 testes.
  - Os corpos dos pedidos à ShardCloud foram conferidos com o seu `openapi.json`: criar a imagem, o estado da construção, criar a app a partir da imagem, substituir as variáveis, a web e o subdomínio.
  - **Não foi corrido pelo agente.** Pede segredos, cria recursos em contas do responsável e abre o navegador.

**Pedido do responsável.** Fazer a configuração única pelas linhas de comandos. O que só a pessoa pode fazer fica com a pessoa:
- abrir as contas e gerar os tokens no Docker Hub e na ShardCloud;
- escrever os segredos;
- instalar e autenticar o `gh`;
- enviar o código e as tags.

O assistente gerado com o skill `wizard` faz o resto:
- valida o token da ShardCloud;
- monta o contexto do git e cria a imagem, esperando pela construção;
- cria a app com a memória escolhida (2048 MB recomendados), o subdomínio e as variáveis;
- liga o acesso web e espera pelo *health check*;
- define os segredos e as variáveis do GitHub;
- cria o ambiente `production` com o utilizador como revisor obrigatório.

**Segredos.** Cada segredo é escrito com a entrada escondida e vai directamente para a ShardCloud, pelo `curl` na entrada padrão, ou para o GitHub, pelo `gh secret set`. Nunca vai para um ficheiro nem para a linha de comandos. A chave da API para programas é gerada. O token de acesso pode ser escrito pela pessoa ou gerado e mostrado uma vez, e o ecrã limpa-se depois. Em `config/.env.shardcloud`, ignorado pelo git, ficam só identificadores, para retomar.

**Suposições declaradas.**
- A memória em MB: a API não diz a unidade, e o ficheiro `.shardcloud` usa MB.
- O endereço `https://<subdomínio>.shardweb.app`, como diz a documentação.
- Ambientes com revisores obrigatórios num repositório privado exigem um plano pago do GitHub. Se o GitHub recusar, o assistente diz que o ambiente tem de ser criado à mão.

### CHG-0076 · Versão escrita no contexto da ShardCloud

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0075
- **Estado:** activa
- **Requisitos:** REQ-PLT-008
- **Commit:** `1f07865`
- **Migração:** nenhuma
- **Ficheiros:** `deploy/shardcloud/build_context.sh`, `.github/workflows/release.yml`, `backend/tests/deploy/test_container_config.py`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** `tests/deploy` com 36 testes. Contexto montado com a versão 9.9.9 e construído sem argumentos, como a ShardCloud o constrói: o *health check* respondeu `"version": "9.9.9"`. Em repouso, o contentor usa 135 MiB.

**Defeito.** A ShardCloud constrói o zip tal como está, sem argumentos de construção. A versão só chegava à imagem do Docker Hub, por `--build-arg`. Na ShardCloud ficava `dev`, e o deploy esperaria pela versão nova até esgotar o tempo. `build_context.sh` passa a receber a versão e a escrevê-la no `ARG` do Dockerfile do contexto. Uma versão com caracteres fora de `[0-9A-Za-z.+-]` é recusada. O release passa-lhe a versão da tag.

### CHG-0075 · Correcções da revisão do CI/CD e da publicação na ShardCloud

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0074
- **Estado:** activa
- **Requisitos:** SEC-03, SEC-09, SEC-20, REQ-PLT-008
- **Commit:** `83440fa`
- **Migração:** nenhuma
- **Ficheiros:** `.github/workflows/{ci,release}.yml`, `deploy/shardcloud/{deploy.sh,entrypoint.sh,Dockerfile}`, `backend/src/sextante/platform/{health,settings}.py`, `backend/tests/deploy/*`, `frontend/openapi.json`, `schema.d.ts`; `docs/00` §3.27, `README.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:**
  - Backend: 463 testes e 1 xfail; `tests/deploy` com 35 testes.
  - Frontend: 80 testes.
  - Auditorias de SEC-20 corridas localmente com as mesmas versões do CI: `pip-audit` sem vulnerabilidades conhecidas; `bandit` sem achados médios nem altos; `npm audit`, 0; `gitleaks` em 99 commits, sem fugas.
  - Imagem da ShardCloud reconstruída com o nginx fixado (1.22.1). Trivy: 0. `docker stop` termina em 1 s. Matar a API faz parar o contentor (código 137), para que a plataforma o reinicie inteiro.

**Falhas da revisão corrigidas.**
- **SEC-20 no CI.** Há um trabalho de segurança com `pip-audit` (dependências bloqueadas, com hash), `bandit` (médio e alto), `npm audit --audit-level=high` e `gitleaks` em todo o histórico, com versões e digest fixados.
- **Imagens do compose.** Passam a bloquear um CRITICAL com correcção, como pede SEC-20; antes só eram reportadas. As três análises ficam numa matriz.
- **Backup.** O deploy passa a esperar que o backup termine (`done`), em vez de seguir logo para a reconstrução.
- **Limite de backups.** A ShardCloud guarda até 10 por app. Quando já há 10, o deploy apaga o mais antigo e pára se a ShardCloud o recusar (idade mínima de retenção).
- **Construção antiga.** A reconstrução só conta quando o `updated_at` da imagem muda: um «success» da construção anterior já não leva ao reinício.
- **`entrypoint.sh`.** Com `set -e`, um processo que parasse com erro terminava o script antes da limpeza. O `trap` passa a estar instalado antes de os processos arrancarem.
- **`version` do health check** com `max_length` (SEC-09.1).
- **Release.** A versão chega ao `zip` por `env`, não dentro do `run:`. Um teste verifica que nenhum `run:` expande valores de fora do ficheiro.
- **Contexto e `COPY`.** Um teste verifica que cada `COPY` do Dockerfile da ShardCloud tem o seu ficheiro no contexto montado pelo git.
- **nginx fixado** em `1.22.1-9+deb12u10`, para que a imagem que a ShardCloud constrói seja igual em conteúdo à do Docker Hub.
- **Documentação.** A porta 80 passa a ser descrita como suposição a confirmar no primeiro deploy.
- **Injecção de código.** O identificador do backup entra no Python por argumento, nunca dentro da expressão avaliada.

**Fica como está, com o motivo.**
- **A imagem que a ShardCloud corre não é analisada.** Fica no registo interno da plataforma, onde o pipeline não chega. As fixações acima tornam-na igual em conteúdo à analisada.
- **`SEXTANTE_API_DOCS_ENABLED` vem ligado por omissão**, para que `make run` continue a mostrar `/docs`. A única instalação pública é a imagem, que o desliga, e um teste guarda-o.
- **Sistema de ficheiros só de leitura e utilizador da imagem.** A ShardCloud não documenta nem um nem o outro. A imagem arranca como root só para a porta 80, e um teste guarda que a API e os workers do nginx não correm como root.
- **`X-Forwarded-For`.** Nada lê o endereço do cliente: SEC-12 conta por credencial.
- **CI duas vezes num pull request** de um ramo deste repositório, uma pelo push e outra pelo pull request. É o custo de correr em todos os ramos.
- **A versão é uma `str` com padrão** nas definições e com limite na resposta. Um tipo próprio seria mais do que este valor de texto pede.

### CHG-0074 · CI/CD no GitHub Actions, imagem no Docker Hub e publicação na ShardCloud

- **Data:** 2026-11-19
- **Tipo:** infra
- **Pai:** CHG-0073
- **Estado:** activa
- **Requisitos:** REQ-PLT-008, SEC-02, SEC-04, SEC-06, SEC-11, SEC-15, SEC-20
- **Commit:** `18e9714`
- **Migração:** nenhuma
- **Ficheiros:** `.github/workflows/{ci,release}.yml` (novos), `deploy/shardcloud/{Dockerfile,nginx.conf,entrypoint.sh,build_context.sh,deploy.sh}` (novos), `backend/src/sextante/{main.py,platform/health.py,platform/settings.py}`, `backend/tests/api/test_release_settings.py` (novo), `backend/tests/deploy/{test_shardcloud_deploy,test_workflows}.py` (novos), `backend/tests/deploy/test_container_config.py`, `frontend/src/entities/health/*`, `frontend/src/shared/i18n/{pt,en}.ts`, `frontend/src/test/api.ts`, `frontend/openapi.json`, `schema.d.ts`; `docs/00` §3.26 e §3.27, `docs/03` SEC-06, `CLAUDE.md`, `config/.env.example`, `README.md`, ticket 03 do deploy
- **Reversibilidade:** total no repositório. Uma versão já publicada no Docker Hub ou na ShardCloud apaga-se lá.
- **Reversão:** reverter o commit. Na ShardCloud, voltar a uma publicação anterior (`POST /apps/{id}/deploys/{deploy_id}/restore`) ou restaurar o backup que o pipeline cria antes de cada publicação.
- **Verificação:**
  - Backend: 456 testes e 1 xfail; `tests/deploy` com 28 testes. `make golden`, 12 amostras sem divergências. Matriz de rastreabilidade, 68 de 79. Licenças.
  - Frontend: 80 testes, `tsc`, ESLint, licenças, build.
  - Imagem da ShardCloud construída a partir do contexto do git (443 KB em zip, 286 MB a imagem). Corrida localmente, com a porta 80 publicada em `127.0.0.1:18081` e segredos gerados só para a verificação. Os resultados estão no bloco de segurança abaixo.
  - `deploy.sh` testado contra um substituto local da API da ShardCloud.
  - **Nada foi publicado pelo agente.** O primeiro release depende da configuração única do README e de uma tag enviada pelo responsável.

**Pedido do responsável.** CI/CD no GitHub Actions: publicar no Docker Hub privado uma imagem com versão e publicar a aplicação na ShardCloud usando essa imagem. Antes de implementar fez-se a leitura da documentação da ShardCloud (docs.shardcloud.app) e quatro perguntas; as respostas estão em §3.27. A ShardCloud constrói a partir de um zip e não vai buscar imagens a um registo privado. Por isso «usar a imagem» passou a «mesma versão, construída a partir do mesmo contexto», com a concordância do responsável.

**App.**
- `SEXTANTE_RELEASE_VERSION` aparece no *health check* (`version`) e na barra lateral.
- `SEXTANTE_API_DOCS_ENABLED` desliga `/docs`, `/redoc` e `/openapi.json`, como pede 02 §6 para produção. Por omissão estão ligados, para uso local.
- A ShardCloud não define a porta: os seus tutoriais servem a porta 80. Se a plataforma esperar outra, muda-se o `listen` de `deploy/shardcloud/nginx.conf`.

```
SEGURANÇA
- Itens aplicáveis: 2, 4, 5, 6, 11, 12, 15, 16, 20
- Verificados:
  2  test_ci_reads_no_secret_and_only_reads_the_repository; segredos só nos trabalhos de
     publicação; contexto montado do git (nada do disco local); token da ShardCloud para o
     curl pela entrada padrão, test_the_token_never_reaches_the_output; grep do token de
     verificação no log do contentor: zero
  4  ps no contentor: API como sextante (uid 10001, sem capacidades, setpriv), workers do
     nginx como www-data, só o mestre do nginx como root para a porta 80; /data e a base de
     dados -rw------- 10001; test_the_shardcloud_image_keeps_root_to_binding_port_80_only
  5  HTTPS terminado pela ShardCloud (subdomínio e domínio próprio com certificado automático)
  6  entrada pelo token, 204 pelo nginx da imagem; API alcançável só em 127.0.0.1 do
     contentor (porta 8000 fechada no IP do contentor)
  11 os oito cabeçalhos de §11.2 nas respostas da imagem;
     test_the_served_frontend_carries_every_security_header_in_every_location[shardcloud]
  12 limites de taxa de SEC-12 inalterados; entrada limitada a 10 por minuto
  15 /docs e /openapi.json 404 na API da imagem pública;
     test_the_api_description_can_be_switched_off; versão sem caracteres livres
     (test_a_malformed_release_version_refuses_startup)
  16 corpo limitado a 50 × 25 MiB no nginx; carregamentos no disco de /data/tmp
  20 Trivy na imagem da ShardCloud: 0 HIGH ou CRITICAL com correcção; o CI falha se aparecer
     algum; acções fixadas por commit (test_every_action_is_pinned_by_commit); bases por
     digest; dependências Python por hash; npm ci --ignore-scripts
- Pendentes:
  a AMT confirmar que as facturas podem ficar na ShardCloud;
  a ShardCloud confirmar que /data sobrevive a um novo deploy;
  a porta 80 confirmada no primeiro deploy real;
  nginx-light do Debian instalado por apt sem versão fixa (a base está fixada por digest);
  contas por pessoa (SEC-07) antes de alargar o uso
- Não suportado pelo stack: a ShardCloud não aceita credenciais de registo; alternativa, o
  mesmo contexto de construção nos dois destinos (§3.27)
- Risco residual: médio-alto, por um token partilhado numa aplicação pública e por dados de
  terceiros num serviço externo (§3.27).
```

### CHG-0073 · API sem rede depois de um conflito de porta, e ecrã de erro da página

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0072
- **Estado:** activa
- **Requisitos:** REQ-PLT-008, REQ-PLT-005, REQ-PLT-006
- **Commit:** `9a915a1`
- **Migração:** nenhuma
- **Ficheiros:** `compose.yaml`, `README.md`, `frontend/src/shared/layout/route-error.tsx` (novo), `frontend/src/shared/layout/route-error.test.tsx` (novo), `frontend/src/router.tsx`, `frontend/src/shared/i18n/{pt,en}.ts`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:**
  - Frontend: 80 testes, `tsc`, ESLint, licenças, build. Backend: `tests/deploy`, 13 testes.
  - Reproduzido num projecto compose de verificação, com a porta 18000 ocupada por outro processo. `docker compose up` falha com `address already in use` e o contentor fica parado, sem reinício.

**Problema relatado pelo responsável.** Em `http://127.0.0.1:8080` aparecia «Something went wrong!», e o nginx registava `api could not be resolved` e 502 em `/api/session`.

**Causa, pelo log do Docker.** O primeiro arranque da API falhou com `failed to bind host port 127.0.0.1:8000: address already in use`, porque `make run` ainda ocupava a porta. A política `restart: unless-stopped` voltou a arrancar o contentor 20 segundos depois, e o Docker deixou-o sem rede nenhuma. A verificação de saúde corre no `127.0.0.1` do próprio contentor, por isso ele aparecia saudável, mas o nginx não o encontrava.

**Correcções.**
- **Política de reinício removida.** Um conflito de porta passa a parar `docker compose up` com o erro à vista, em vez de deixar uma API saudável e inalcançável. O README diz o que fazer.
- **Ecrã de erro da página.** O frontend passa a ter um ecrã próprio para uma página que não carrega, em vez do texto inglês por omissão do router. Mostra o motivo no idioma escolhido («Não foi possível contactar o servidor») e um botão para tentar de novo, e tem um teste com o 502 do nginx.

**O que o responsável faz.** Parar `make run` e correr `docker compose down && docker compose up --build`.

### CHG-0072 · Correcções da revisão do contentor do frontend

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0071
- **Estado:** activa
- **Requisitos:** SEC-04, SEC-06, SEC-11, SEC-16, SEC-20
- **Commit:** `4ad9e47`
- **Migração:** nenhuma
- **Ficheiros:** `backend/Dockerfile`, `backend/Makefile`, `backend/scripts/lock_dependencies.sh`, `backend/tests/deploy/test_container_config.py`, `frontend/Dockerfile`, `frontend/.dockerignore`, `frontend/nginx/default.conf`; `docs/00` §3.26, `docs/03` SEC-06 e SEC-11, `CLAUDE.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:**
  - Backend: 436 testes e 1 xfail; `tests/deploy` com 13 testes. Matriz de rastreabilidade, 68 de 79.
  - Frontend: 79 testes e build.
  - Projecto compose de verificação nas portas 18000 e 18080, com uma chave do modelo inválida e um token de acesso gerado só para a verificação.
  - Os dois contentores ficam saudáveis.
  - Entrada pelo nginx, 204.
  - Carregamento de 12 ficheiros de 24 MiB, 302 MB no total, pelo nginx: resposta 202, ficheiros no volume em `/data/tmp`, com modo 700, e `/tmp` do contentor a 0%.
  - Trivy na imagem do frontend: 3 achados, iguais aos de CHG-0071. O projecto de verificação foi removido com o seu volume.

**Carregamentos grandes (falha da revisão).** O Starlette guarda em ficheiro temporário cada ficheiro carregado acima de 1 MiB. Com o `/tmp` de 256 MiB em memória, um carregamento acima disso falhava com 500. A API passa a usar `TMPDIR=/data/tmp`, no disco do volume, criado no arranque com `umask 077`.

**`0.0.0.0` no nginx (falha da revisão).** `listen 8080;` escutava em todas as interfaces sem o dizer, e a guarda não o via.
- O `listen` passa a nomear o endereço (`0.0.0.0:8080`).
- A guarda aceita os dois ficheiros dos contentores e falha com um `listen` sem endereço.
- A decisão 3.26, SEC-06 e o `CLAUDE.md` passam a nomear os dois servidores dos contentores. A opção aceite pelo responsável publicava as duas portas, e o nginx num contentor está sujeito ao mesmo problema que a API; o texto inicial nomeava só a API.

**API publicada em 8000 (contradição com SEC-11).** SEC-11 dizia que o nginx era o único ponto publicado. A porta 8000 fica publicada, por ser a opção aceite pelo responsável, para programas e para a documentação interactiva. §3.26 e SEC-11 passam a dizê-lo: o nginx é o único ponto publicado que serve páginas.

**Outras.**
- O contexto do frontend passa a lista do que entra, como o do backend, e deixa de fora `.npmrc`, `.env` e o estado incremental do `tsc` (`*.tsbuildinfo`).
- `npm ci --ignore-scripts`.
- `pip-tools==7.7.0` fixado.
- O digest da base da API vive só no `Dockerfile`, e o `Makefile` lê-o de lá.
- `Host` com a porta (`$http_host`), e `nosniff` só uma vez nos descarregamentos.
- A verificação de saúde do nginx fica igual à da API.
- O teste dos cabeçalhos deixa de depender da indentação, e as dependências lêem-se com `tomllib`.

**Fica pendente.** Não foi feita a entrada num navegador real em `http://127.0.0.1:8080`, porque a extensão do navegador não estava ligada. O mesmo cookie `Secure` sobre HTTP em `127.0.0.1` já é aceite pelo navegador do responsável no frontend de desenvolvimento (`127.0.0.1:5173`). Os 3 achados da imagem do nginx continuam, como em CHG-0071.

### CHG-0071 · Contentor do frontend e correcções da revisão do contentor da API

- **Data:** 2026-11-19
- **Tipo:** infra
- **Pai:** CHG-0070
- **Estado:** activa
- **Requisitos:** REQ-PLT-008, SEC-02, SEC-03, SEC-04, SEC-06, SEC-11, SEC-16, SEC-20
- **Commit:** `78c30c0`
- **Migração:** nenhuma
- **Ficheiros:** `frontend/Dockerfile`, `frontend/.dockerignore`, `frontend/nginx/{default,security-headers}.conf` (novos); `backend/requirements.lock`, `backend/scripts/lock_dependencies.sh` (novos), `backend/Dockerfile`, `backend/.dockerignore`, `backend/Makefile`, `compose.yaml`, `backend/tests/deploy/test_container_config.py`; `config/.env.example`, `docs/03` SEC-11, `README.md`, ticket 02 do deploy
- **Reversibilidade:** total
- **Reversão:** reverter o commit; `docker compose down` pára os contentores, e `docker compose down -v` apaga também o volume com os dados.
- **Verificação:**
  - Backend: `make test`, 435 testes e 1 xfail. `make golden`, 12 amostras sem divergências. Matriz de rastreabilidade, 68 de 79. Licenças.
  - Frontend: 79 testes, `tsc`, ESLint, licenças, build.
  - Projecto compose de verificação nas portas 18000 e 18080, com uma chave do modelo inválida. Os resultados estão no bloco de segurança abaixo.

**Ticket 02.**
- **Imagem do frontend.** Multi-etapa: Node 22 compila (`tsc -b && vite build`) e o nginx sem privilégios serve os ficheiros compilados.
- **Imagem base.** Variante slim, `mainline-alpine-slim`, fixada por digest. Foi escolhida pelo Trivy: a primeira escolhida, `1.28-alpine`, tinha 82 vulnerabilidades HIGH ou CRITICAL com correcção; `stable-alpine` tinha 19; a slim de mainline tem 3.
- **Encaminhamento de `/api`.** O nginx encaminha `/api` para o contentor da API na mesma origem. O nome da API resolve-se a cada pedido, por isso o nginx arranca mesmo antes da API.
- **Cabeçalhos de SEC-11.** Estão em todas as `location`, através de um ficheiro incluído, porque um `add_header` numa `location` apagaria os do servidor.
- **Outros pormenores.** `server_tokens off`. Recursos compilados guardados um ano, por terem o hash no nome; as páginas não ficam em cache. Corpo até 1260 MiB, que cobre 50 ficheiros de 25 MiB.

**Correcções da revisão de CHG-0070.**
- **Dependências bloqueadas (SEC-20, falha dura).** `requirements.lock` fixa as 40 dependências por versão e hash, e a imagem instala com `--require-hashes`. `make lock` regenera o ficheiro num contentor da mesma base, e a regeneração dá exactamente o mesmo ficheiro.
- **Bloco de segurança.** Estava em falta em CHG-0070 e fica abaixo, para os dois tickets.
- **Endurecimento do compose.** Uma âncora partilhada pelos dois contentores, com `/tmp` `noexec,nosuid,nodev` limitado a 256 MiB, `pids_limit` e `mem_limit`.
- **SEC-04.** A API arranca com `umask 077` e `/data` tem modo 700, por isso a base de dados e os ficheiros ficam `-rw-------`.
- **Imagem da API.** A imagem base é um só `ARG`. A verificação de saúde passa a correr de 30 em 30 segundos. `*.egg-info` fica fora da imagem.
- **Guarda do `0.0.0.0`.** Passa a ler todos os ficheiros do repositório excepto Markdown, e também `[::]` e `--host ::`. Só `backend/Dockerfile` pode ter um destes endereços.
- **`config/.env`.** O exemplo e o README avisam que o compose não é uma shell: os valores ficam sem `$`, crases nem `#`.
- **Doc.** SEC-11 deixa de dizer que a API não tem `DELETE`.

**Fica como está, com o motivo.**
- Os caminhos dentro do contentor aparecem no `environment` e nos `volumes` do compose. Juntá-los exigiria variáveis de interpolação que tornam o ficheiro mais difícil de ler.
- A sessão vive em memória, por isso reiniciar a API termina as sessões (SEC-06, já declarado).

```
SEGURANÇA
- Itens aplicáveis: 2, 3, 4, 5, 6, 11, 15, 16, 20
- Verificados:
  2  grep no bundle servido por SEXTANTE_API_KEY, SEXTANTE_ACCESS_TOKEN, ANTHROPIC e sk-ant:
     só o nome SEXTANTE_API_KEY, no texto da descrição OpenAPI, nenhum valor;
     .dockerignore de ambas as imagens sem .env; test_no_secret_or_local_data_enters_an_image
  3  git status antes do commit: nenhum .env, .db nem carregamento; .gitignore inalterado
  4  contentores com uid 10001 (API) e 101 (nginx), raiz só de leitura, cap_drop ALL,
     no-new-privileges; ls -ln /data: base de dados, WAL e uploads -rw------- 10001;
     test_each_container_is_locked_down[api|web]
  5  sem TLS local, tráfego confinado a 127.0.0.1 (SEC-05, já declarado)
  6  docker port: 127.0.0.1:18000->8000 e 127.0.0.1:18080->8080;
     test_every_published_port_is_on_127_0_0_1_only;
     test_only_the_api_image_listens_on_every_interface (excepção D-3.26 num só ficheiro)
  11 curl -D - às páginas: os oito cabeçalhos de §11.2, CSP não em modo de relatório;
     test_the_served_frontend_carries_every_security_header_in_every_location
  15 grep da chave da API no log do contentor da API (verificação de CHG-0070): zero;
     o nginx regista só a linha do pedido, nunca o corpo da entrada; Server sem versão
  16 corpo limitado no nginx a 50 × 25 MiB; os limites por ficheiro continuam na API
  20 Trivy (HIGH e CRITICAL com correcção): sextante-api 0; sextante-web 3 (ver pendentes);
     requirements.lock com hashes e --require-hashes; make licenses e npm run licenses verdes;
     test_base_images_are_pinned_by_digest_and_run_without_root;
     test_the_api_dependencies_install_from_the_hashed_lock
- Pendentes: imagem web com 3 achados HIGH (musl CVE-2026-107891, zlib CVE-2026-85091)
  já corrigidos no Alpine mas ainda não na imagem oficial; actualizar o digest quando sair
- Não suportado pelo stack: nenhum nesta alteração
- Risco residual: médio, o de SEC-06: quem aceda à máquina alcança a API com a chave ou o
  token; HSTS é ignorado em HTTP local até haver TLS.
```

### CHG-0070 · Contentor da API e docker compose

- **Data:** 2026-11-19
- **Tipo:** infra
- **Pai:** CHG-0069
- **Estado:** activa
- **Requisitos:** REQ-PLT-008, SEC-02, SEC-03, SEC-04, SEC-06, SEC-20
- **Commit:** `47ecdf4`
- **Migração:** nenhuma
- **Ficheiros:** `backend/Dockerfile` (novo), `backend/.dockerignore` (novo), `compose.yaml` (novo), `backend/tests/deploy/` (novo); `docs/00` §3.26, `docs/03` SEC-06, `CLAUDE.md`, `README.md`, ticket 01 do deploy
- **Reversibilidade:** total
- **Reversão:** reverter o commit; `docker compose down` pára o contentor, e `docker compose down -v` apaga o volume com os dados.
- **Verificação:**
  - Testes estáticos: `tests/deploy`, 6 testes.
  - Imagem construída: 277 MB.
  - Contentor arrancado num projecto de verificação na porta 18000, com uma chave do modelo inválida para não gastar créditos. O contentor fica saudável, corre com uid 10001, `/app` é só de leitura e `/data` é gravável, e a porta está publicada só em `127.0.0.1`.
  - `/api/health` responde 200.
  - Um PDF sintético carregado fica `rejected` e o trabalho continua igual depois de `docker compose restart`. A chave da API não aparece no log.

**Pedido.** Tickets do deploy, começando pela API.

**Excepção ao `0.0.0.0`.** Perguntada antes, porque contradizia o `CLAUDE.md`. O responsável aceitou a excepção só no `CMD` do contentor, com as portas publicadas em `127.0.0.1`, e ela fica registada em §3.26, SEC-06 e `CLAUDE.md`. Um teste falha se `0.0.0.0` aparecer noutro ficheiro que configura um servidor.

**Imagem.**
- Multi-etapa: a primeira etapa instala as dependências de `pyproject.toml` num ambiente virtual e a final copia-o.
- A aplicação corre de `/app/src`, ao lado das migrações, que `platform/database.py` procura aí.
- Base `python:3.12-slim-bookworm` fixada por digest, sem servidor anunciado no cabeçalho.
- Verificação de saúde a partir do próprio contentor.

**Compose.**
- `config/.env` entra no arranque, e os caminhos de dentro do contentor substituem os do `.env`.
- Volume `sextante-data` para a base de dados e os carregamentos; catálogo e lista de exclusão montados só para leitura.
- `read_only`, `/tmp` em tmpfs, `cap_drop: ALL`, `no-new-privileges`.

### CHG-0069 · Correcções da revisão da interface em dois idiomas

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0068
- **Estado:** activa
- **Requisitos:** REQ-PLT-006, REQ-PLT-005, REQ-CNF-004, SEC-15
- **Commit:** `773b9c0`
- **Migração:** nenhuma
- **Ficheiros:** `backend/src/sextante/platform/{http_errors,coded_text,language,request_language,user_messages}.py`, `review/api/routes.py`, `export/application/build_job_export.py`, `main.py`, `tests/domain/test_language.py`, `tests/api/test_language.py`; `frontend/src/shared/i18n/language.ts`, `root-layout.tsx`, `index.html`, `features/language/language.test.tsx`; `frontend/openapi.json`, `schema.d.ts`; `docs/04` §8.6, `README.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** backend 423 testes e 1 xfail, mypy, ruff, import-linter, funções até 20 linhas; frontend 79 testes, `tsc`, ESLint, licenças, build.

**Recusas do próprio framework.** Um pedido inválido (422 de validação), um endereço inexistente (404) e um método não aceite (405) respondiam com o `detail` do FastAPI, em Inglês e com eco do input. Passam a ter o corpo de erro de sempre, com a mensagem no idioma pedido e sem o detalhe (SEC-15).

**Código desconhecido.** Uma sinalização ou nota sem texto no catálogo fazia falhar os resultados com 500. Passa pela mesma função de `coded_text` (`coded_texts`) e mostra o texto «motivo sem descrição».

**`Accept-Language`.** `q=0` recusa o idioma (RFC 9110). Uma qualidade fora de [0, 1] ou não finita conta como 0. Cada resposta leva `Vary: Accept-Language`, para que nenhuma cache dê a uma pessoa o idioma de outra.

**Normas.**
- `error_response` exige o idioma, para que nenhum caminho novo responda em Inglês sem querer.
- O cabeçalho lê-se num só sítio (`request_language`).
- `_Texts` passa a `_Localised`.
- O atributo `lang` da página usa o mesmo mapa de locales que os formatos (`en-GB`, `pt-PT`).
- O §8.6 de `docs/04` deixa de dizer que o texto é só em Português.

**README.** Os nomes dos ecrãs passam a estar em Inglês, com o Português entre parênteses, como a secção «Language» anuncia.

**Fica como está, com o motivo.**
- `Catalog.description_in` decide o texto a mostrar em cada idioma. Está no catálogo porque só o catálogo conhece a Description 2, e é uma função pura.
- A data da nota de duplicado na exportação fica `dd-mm-aaaa` nos dois idiomas, legível em ambos.
- Os testes do frontend correm em Português, porque cobrem o comportamento. Os de idioma cobrem o Inglês por omissão.
- O trabalho está no ramo `feature/REQ-PLT-007-startup-catalog-validation`, que já acumula várias entregas. Mudar de ramo fica para quando o responsável o pedir.

### CHG-0068 · Interface em Inglês e Português, com os textos do servidor no idioma escolhido

- **Data:** 2026-11-19
- **Tipo:** feat
- **Pai:** CHG-0067
- **Estado:** activa
- **Requisitos:** REQ-PLT-006 (revisto), REQ-PLT-005, REQ-CNF-004, REQ-EXP-001, R6, R12 (revista)
- **Commit:** `e0598a7`
- **Migração:** nenhuma
- **Ficheiros:** `backend/src/sextante/platform/{language,request_language}.py` (novos), `platform/{user_messages,http_errors,coded_text}.py`, `catalog/domain/model.py`, `export/application/{build_job_export,export_job}.py`, `export/api/routes.py`, `review/api/routes.py`, `ingestion/api/routes.py`, `main.py`, `tests/domain/test_language.py` e `tests/api/test_language.py` (novos), `tests/api/encoding_harness.py`, `tests/api/test_pdf_ingestion.py`, `tests/domain/test_export_rules.py`; `frontend/src/shared/i18n/{en,language}.ts` (novos), `shared/i18n/{pt,t}.ts`, `shared/api/client.ts`, `shared/format.ts`, `features/language/*` (novo), `root-layout.tsx`, `app-shell.tsx`, `pages/login-page.tsx`, `features/line-review/candidates-table.tsx`, esquemas Zod, `index.html`, `vitest.setup.ts`; `frontend/openapi.json`, `schema.d.ts`; `docs/00` R12 e §3.25, `docs/01` REQ-PLT-006, `docs/04` §1 e §8, `CLAUDE.md`, `README.md`, ticket 08 do frontend
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** backend 412 testes e 1 xfail, mypy, ruff, import-linter, funções até 20 linhas; frontend 79 testes, `tsc`, ESLint, licenças, build.

**Pedido do responsável.** Tradução da interface em Inglês e Português, com o Inglês por omissão e a opção de trocar. Em Inglês, a descrição do catálogo vem da Description 2, e as sinalizações e notas vêm também em Inglês. Contradizia R12 e REQ-PLT-006. Por isso perguntou-se antes, e o responsável respondeu: rever R12 com o Inglês por omissão, a exportação segue o idioma, e a descrição em falta mostra a portuguesa.

**Servidor.**
- O idioma vem de `Accept-Language` (o primeiro suportado, por qualidade). É Inglês sem cabeçalho, ou com um cabeçalho inválido ou longo de mais.
- `USER_MESSAGES_EN` tem exactamente as chaves de `USER_MESSAGES_PT`, e um teste verifica-o.
- Os erros, os códigos com texto (`coded_text`), os resultados, as respostas da revisão, o histórico e a exportação usam o idioma do pedido.
- A descrição do catálogo em Inglês vem do catálogo carregado (`Catalog.description_in`). A decisão continua registada com a descrição portuguesa, e uma resposta de revisão repetida pela mesma `Idempotency-Key` mostra-se no idioma de quem a repete.
- Os testes existentes pedem Português explicitamente. Testes novos cobrem o Inglês, a omissão, a exportação e o histórico nos dois idiomas.

**Frontend.**
- `en.ts` tem o mesmo formato de `pt.ts`, e o compilador recusa uma chave em falta ou a mais.
- O idioma vive num estado guardado no navegador, com Inglês por omissão.
- `t()`, os formatos de número e data (`en-GB` ou `pt-PT`), o atributo `lang` da página e o cabeçalho de cada pedido seguem-no.
- Ao trocar, as páginas montam-se de novo no idioma escolhido e as leituras do servidor voltam a ser pedidas.
- As mensagens dos esquemas Zod passam a ser avaliadas na validação.
- Na tabela de candidatos aparece primeiro a descrição no idioma escolhido.
- Os testes existentes correm em Português. Testes novos cobrem o Inglês por omissão, a troca e o cabeçalho enviado.

### CHG-0067 · Correcções da revisão do ticket 07 do frontend

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0066
- **Estado:** activa
- **Requisitos:** REQ-PLT-009, REQ-ING-011, SEC-19, REQ-REV-006
- **Commit:** `ca5e1fa`
- **Migração:** nenhuma
- **Ficheiros:** `backend/src/sextante/ingestion/application/job_lifecycle.py` (era `manage_jobs.py`), `ingestion/application/{ports,records,upload_invoices}.py`, `ingestion/domain/statuses.py`, `ingestion/infrastructure/repository.py`, `ingestion/api/routes.py`, `main.py`, `tests/api/test_job_deletion.py`; `frontend/src/features/results/{results-table.tsx,use-row-opens-line.ts}`, `features/jobs/*`, `features/upload/*`, `pages/{jobs,upload}-page.tsx`, `shared/i18n/{t,pt}.ts`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** backend 391 testes e 1 xfail, mypy, ruff, import-linter, funções até 20 linhas, matriz 68 de 79; frontend 74 testes, `tsc`, ESLint, licenças, build.

**Ainda se via um trabalho apagado.** Uma factura de um trabalho apagado deixava de contar como cópia anterior: antes, uma factura nova podia ficar «possível duplicado» de uma escondida, com ligação para um 404.

**Corrida entre apagar e reprocessar.** O `UPDATE` do apagamento verifica o estado na mesma instrução, por isso um trabalho reposto na fila entretanto é recusado. O trabalhador também não reclama trabalhos apagados. Dois apagamentos simultâneos, com chaves diferentes, respondem ambos 200 e gravam um só evento.

**Testes novos.** Correcção e resolução de entidade num trabalho apagado, dois apagamentos em simultâneo, carregamento misto (ficheiro novo mais ficheiro de um trabalho apagado), e cópia de uma factura apagada.

**Normas.**
- Estados como `JobStatus` em vez de texto livre, e `invoice_total` passa a viver no registo.
- O resultado de gravar um carregamento passa a registo com nome, e o relógio e os identificadores deixam de viajar num tuplo.
- `manage_jobs.py` passa a `job_lifecycle.py`.
- A mensagem de «não encontrado» diz o que se esperava.

**Frontend.**
- Um trabalho restaurado volta aos trabalhos recentes.
- Apagar actualiza também o estado e os resultados guardados em cache.
- O singular e o plural passam a usar uma só função (`tCount`).
- A navegação da linha passa a gancho, com a rota num só sítio.
- A paginação dos trabalhos tem os seus próprios textos.

**Fica como está, com o motivo.**
- `JobCollaborators` é partilhado pelos três casos de uso, que vivem no mesmo módulo, embora a listagem use só dois campos. É a forma de §4 para injectar dependências, e separá-lo dava três registos quase iguais.
- O filtro do trabalho activo repete-se em quatro consultas. Uma vista SQL esconderia o filtro a quem lê a consulta.
- Se o restauro falhar depois de o trabalho novo ter sido gravado, a resposta é 500 e o trabalho novo fica na fila. Repetir o carregamento restaura, porque o restauro é idempotente.
- As chaves `invoice_counts` continuam texto, como em `JobSummary`.

### CHG-0066 · Lista e apagamento lógico de trabalhos, e UX da tabela e do carregamento

- **Data:** 2026-11-19
- **Tipo:** feat
- **Pai:** CHG-0065
- **Estado:** activa
- **Requisitos:** REQ-PLT-009 (novo), REQ-PLT-004, REQ-ING-007, SEC-18, SEC-19, REQ-AUD-002, REQ-PLT-006
- **Commit:** `aa13ccb`
- **Migração:** `0010_job_soft_delete` (coluna `job.deleted_at`; a descida remove-a e os trabalhos apagados voltam a aparecer)
- **Ficheiros:** `backend/migrations/versions/0010_job_soft_delete.py` (novo), `ingestion/application/manage_jobs.py` (novo), `ingestion/application/{ports,records,upload_invoices}.py`, `ingestion/infrastructure/{repository,tables}.py`, `ingestion/api/routes.py`, `review/application/review_line.py`, `platform/user_messages.py`, `main.py`, `tests/api/test_job_deletion.py` (novo), dois testes ajustados; `frontend/src/pages/jobs-page.tsx` (novo), `features/jobs/*` (novo), `entities/job/use-jobs.ts` (novo), `shared/ui-kit/confirm-dialog.tsx` (novo), `shared/ui-kit/use-confirmation-focus.ts` (movido de `features/reprocess`), `features/results/results-table.tsx`, `features/upload/*`, `pages/{upload,job}-page.tsx`, `app-shell.tsx`, `router.tsx`, `shared/i18n/pt.ts`, `shared/format.ts`, testes; `docs/00` §3.24, `docs/01` REQ-PLT-009, `docs/02` §6, `docs/03` SEC-19, `README.md`, ticket 07 do frontend
- **Reversibilidade:** total
- **Reversão:** reverter o commit e descer a migração para 0009 (`alembic downgrade 0009`).
- **Verificação:** backend 387 testes e 1 xfail, mypy, ruff, import-linter, funções até 20 linhas, matriz 68 de 79; frontend 73 testes, `tsc`, ESLint, licenças, build.

**Pedido do responsável.** Três pontos: a tabela de resultados não mostrava que a descrição se clica; o carregamento deixava muito espaço vazio; e devia poder apagar-se um trabalho, de forma lógica, com modal de confirmação. As três decisões de desenho do apagamento foram perguntadas e respondidas: restaurar no recarregamento, só trabalhos terminados, página «Trabalhos» com lista do servidor.

**Apagamento.** `DELETE /api/jobs/{job_id}` marca `deleted_at` e grava `job_deleted`. Um trabalho apagado desaparece da lista, do estado, dos resultados, da exportação, da factura, dos candidatos e do histórico, e a revisão, a resolução e o reprocessamento respondem 404. Recarregar um ficheiro dele restaura-o (`job_restored`, `restored_job_ids`). Só se apagam trabalhos concluídos ou com falha.

**Lista.** `GET /api/jobs`, do mais recente para o mais antigo, paginado, sem nome de ficheiro (SEC-18). Página «Trabalhos» com data, estado, facturas por estado, resultados e apagar.

**Modal.** `ConfirmDialog`, sem dependência nova: `alertdialog` modal sobre a página escurecida, foco a começar em «Cancelar» e preso no modal, Escape e clique fora cancelam, foco devolvido ao botão.

**Tabela de resultados.** A descrição passa a ligação visível (cor da marca, sublinhado). Uma coluna final, fixa à direita, tem «Rever» numa linha pendente e «Abrir» nas outras. A linha inteira abre a revisão, excepto quando o clique é numa ligação, num botão ou numa selecção de texto.

**Carregamento.** Conteúdo centrado com largura máxima. A zona de largar encolhe para uma linha quando há ficheiros, a lista mostra quantos e o tamanho total, e o botão diz quantos envia. Abaixo, três notas sobre o que o servidor faz e os últimos cinco trabalhos.

### CHG-0065 · Correcções da revisão dos tickets 04 e 06 do frontend

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0064
- **Estado:** activa
- **Requisitos:** REQ-REV-002, REQ-REV-003, SEC-19, NFR-REL-002, REQ-PLT-006
- **Commit:** `8d4cfce`
- **Migração:** nenhuma
- **Ficheiros:** `frontend/src/shared/api/use-idempotency-key.ts`, `shared/api/use-invoice-changed.ts` (novo), `shared/api/query-keys.ts`, `shared/format.ts`, `features/line-review/*`, `features/reprocess/*`, `features/export/*`, `features/entity-resolution/use-resolution-form.ts`, `entities/invoice/use-invoice.ts`, `entities/health/server-status.tsx`, `pages/line-review-page.tsx`, `shared/i18n/pt.ts`, testes
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 64 testes do frontend; `tsc`, ESLint, licenças, build. Backend sem alterações.

**Chaves de idempotência.** Uma chave passa a valer para um corpo: mantém-se enquanto o corpo é o mesmo (duplo clique, nova tentativa depois de uma falha) e muda quando o corpo muda. Antes, depois de uma recusa, corrigir para outro item ou mudar a nota reutilizava a chave e o servidor recusava sempre (SEC-19). Vale para a revisão, a resolução e o reprocessamento.

**Revisão de linha.** A linha é procurada página a página nos resultados da factura, e uma factura com mais de 100 linhas encontra a sua última. Uma falha a ler a linha, os candidatos ou o histórico mostra-se como falha, e o histórico deixa de parecer vazio enquanto carrega. Uma linha por codificar já não culpa a entidade. A recusa do servidor aparece também junto às acções; a coluna de escolha tem nome e as escolhas estão num `fieldset`; o contador é anunciado. Estado, decisão e textos dos botões passam ao gancho, e as acções recebem props estreitas. O limite da nota falha alto se faltar no OpenAPI, em vez de valer 0.

**Exportação e reprocessamento.** A ligação de descarga entra no documento e o endereço do ficheiro é revogado depois, para não cancelar a descarga. A confirmação começa no "Cancelar", mantém o foco, fecha com Escape e devolve o foco ao botão. A factura reprocessada é seguida pela fila com intervalo que recomeça a cada vez que fica em fila. As leituras afectadas por uma alteração da factura vivem numa lista só (`useInvoiceChanged`).

**Normas.** Um só texto para "sem valor" (`common.none`); digest encurtado num só sítio.

**Fica como está, com o motivo.** O estado de confirmação aberta é local ao componente: é um passo de uma acção, não um painel nem uma preferência de vista (§8.3). A invalidação por prefixo pede mais leituras do que o mínimo, em troca de nunca deixar uma vista desactualizada. Os testes do frontend não têm marca de requisito: a matriz de rastreabilidade só lê os testes do backend.

**Correcção do registo.** CHG-0063 lista `shared/i18n/pt.ts` nos ficheiros, mas as chaves da revisão já tinham entrado em CHG-0062.

### CHG-0064 · Exportação e reprocessamento na interface

- **Data:** 2026-11-19
- **Tipo:** feat
- **Pai:** CHG-0063
- **Estado:** activa
- **Requisitos:** REQ-EXP-001, NFR-REL-002, SEC-19, REQ-PLT-006
- **Commit:** `244eb46`
- **Migração:** nenhuma
- **Ficheiros:** `frontend/src/features/export/*`, `features/reprocess/*`, `pages/results-page.tsx`, `pages/invoice-page.tsx`, `shared/i18n/pt.ts`, `vitest.setup.ts`, testes; `README.md`, ticket 06 do frontend
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 57 testes do frontend; `tsc`, ESLint, licenças. Backend sem alterações (379 testes e o `xfail` estrito).

Botões de exportação em CSV e XLSX no ecrã de resultados: o ficheiro vem do servidor pelo cliente único, com a sessão, e é guardado com o nome que o servidor dá; uma recusa mostra a mensagem e não guarda nada. Reprocessamento no ecrã da factura, só para facturas com falha ou codificadas, atrás de uma confirmação acessível (`alertdialog`, foco na confirmação, Escape cancela) que avisa que a codificação existente fica substituída e que as linhas revistas voltam à revisão; `Idempotency-Key` feita antes do envio.

**Dependência recusada.** O diálogo do Radix (`@radix-ui/react-alert-dialog`) traz o `tslib`, com licença 0BSD, fora da lista de NFR-LIC-001. Sem decisão registada não entra: a confirmação é um painel próprio, sem dependências.

### CHG-0063 · Revisão de linha

- **Data:** 2026-11-19
- **Tipo:** feat
- **Pai:** CHG-0062
- **Estado:** activa
- **Requisitos:** REQ-REV-002, REQ-REV-003, REQ-REV-004, SEC-19, REQ-PLT-006
- **Commit:** `9a0a98d`
- **Migração:** nenhuma
- **Ficheiros:** `frontend/src/features/line-review/*`, `pages/line-review-page.tsx`, `shared/i18n/pt.ts`, testes; `README.md`, ticket 04 do frontend
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 47 testes do frontend; `tsc`, ESLint. Backend sem alterações (379 testes e o `xfail` estrito).

Ecrã da revisão de uma linha: codificação em vigor, todos os itens da aba de destino por score com a posição e a escolha do modelo, histórico das codificações com a versão do prompt, o modelo, o digest do catálogo e a revisão. Aceitar só numa linha pendente; corrigir só para um item da tabela, que é a aba da linha; nota com limite lido do OpenAPI e contador. Cada acção com a sua `Idempotency-Key`, feita antes do primeiro envio, e botões desactivados durante o envio. Uma linha sem aba não oferece correcção e liga à factura. Depois de cada acção invalidam-se os resultados, o histórico, os candidatos e a factura.

**Correcção do registo.** A verificação de CHG-0061 e de CHG-0062 indica 384 testes do backend; eram 379 (374 antes, mais os 5 do endpoint novo). CHG-0062 indica 47 testes do frontend; eram 40. As entradas não se reescrevem (regra 4), por isso a correcção fica aqui.

### CHG-0062 · Correcções da revisão do ticket 05 do frontend

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0061
- **Estado:** activa
- **Requisitos:** REQ-REV-006, SEC-18, SEC-19, REQ-PLT-006
- **Commit:** `d774621`
- **Migração:** nenhuma
- **Ficheiros:** `backend/src/sextante/ingestion/application/errors.py` (novo), `read_invoice.py`, `reprocess_invoice.py`, `resolve_entity.py`, `records.py`, `ingestion/api/routes.py`, `ingestion/infrastructure/repository.py`, `platform/coded_text.py`, `platform/user_messages.py`, `main.py`, `tests/api/test_invoice_view.py`; `frontend/src/entities/invoice/*`, `features/entity-resolution/*`, `pages/invoice-page.tsx`, `shared/api/*`, `shared/i18n/pt.ts`, testes; ticket 05 do frontend
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 384 testes do backend e o `xfail` estrito; 47 testes do frontend. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos; `tsc`, ESLint, licenças.

**Servidor.** Um motivo sem texto no catálogo passa a aparecer, com um texto que o diz, em vez de desaparecer. Depois da resolução, o motivo da ambiguidade dá lugar à resolução registada. `InvoiceNotFoundError` passa a um módulo de erros da ingestão; colunas do cabeçalho nomeadas uma a uma; exemplo no comentário do repositório.

**Frontend.** Depois da resolução, a factura é lida de novo com intervalo crescente enquanto está em fila, e o estado do trabalho é invalidado também. Aviso, com ligação aos resultados filtrados, quando a factura tem mais linhas do que a página. As duas resoluções vivem numa lista só, verificada contra o OpenAPI, e um valor desconhecido não passa por "Não é a AMT"; os limites da nota vêm do OpenAPI. Uma chave já usada noutro pedido é renovada. O erro de cada campo fica ligado ao campo (`aria-describedby`), e o foco vai para a entidade depois de resolver. O título e a navegação saem do componente para o gancho.

**Fica como está, com o motivo.** O NIF do fornecedor e o motivo de recusa, que o ticket não lista, ficam: são cabeçalho extraído e explicam o estado. A cópia campo a campo entre registos e modelos de resposta é a separação que SEC-18 pede.

### CHG-0061 · Ecrã da factura e resolução de entidade

- **Data:** 2026-11-19
- **Tipo:** feat
- **Pai:** CHG-0060
- **Estado:** activa
- **Requisitos:** REQ-REV-006, REQ-ENT-006, REQ-ING-011, SEC-18, SEC-19, REQ-PLT-006
- **Commit:** `8022f65`
- **Migração:** nenhuma
- **Ficheiros:** `backend/src/sextante/ingestion/api/routes.py`, `ingestion/application/read_invoice.py` (novo), `ingestion/application/records.py`, `ingestion/application/ports.py`, `ingestion/application/resolve_entity.py`, `ingestion/infrastructure/repository.py`, `platform/coded_text.py` (novo), `review/api/routes.py`, `main.py`, `tests/api/test_invoice_view.py`; `frontend/openapi.json`, tipos gerados, `frontend/src/entities/invoice/*`, `features/entity-resolution/*`, `pages/invoice-page.tsx`, `shared/api/use-idempotency-key.ts`, `shared/ui-kit/textarea.tsx`; `README.md`, ticket 05 do frontend
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 384 testes do backend e o `xfail` estrito; 36 testes do frontend. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos; `tsc`, ESLint, licenças.

**Servidor.** `GET /api/invoices/{invoice_id}` devolve o cabeçalho extraído, o estado e o seu motivo, a entidade facturada, o veredicto e o motivo em Português, a resolução registada, a aba de destino, a factura anterior de um duplicado provável e se a factura pode ser resolvida; projecção explícita, sem nome de ficheiro, digest nem caminho (SEC-18), e 404 para uma factura inexistente. A regra de quando uma factura espera resolução passa a viver num só sítio (`InvoiceState.awaits_entity_resolution`), usada pela resolução e pela leitura. O par código e texto (`FlagResponse`) passa à plataforma, partilhado pelos dois módulos.

**Frontend.** Ecrã da factura com o cabeçalho, a entidade, as linhas e o aviso de duplicado com ligação. Formulário de resolução com decisão e nota obrigatória, limite lido do OpenAPI e contador, `Idempotency-Key` feita antes do primeiro envio e mantida numa nova tentativa, botão desactivado durante o envio.

### CHG-0060 · Correcções da revisão do ticket 03 do frontend

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0059
- **Estado:** activa
- **Requisitos:** REQ-REV-001, REQ-PLT-006
- **Commit:** `07208b6`
- **Migração:** nenhuma
- **Ficheiros:** `frontend/src/entities/result/*`, `features/results/*`, `pages/results-page.tsx`, `pages/invoice-page.tsx`, `pages/line-review-page.tsx`, `query-client.ts`, `shared/api/query-keys.ts`, `shared/i18n/pt.ts`, `test/api.ts`, testes; `docs/04-padroes-de-codigo.md` (§8.6), ticket 03 do frontend
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 29 testes do frontend; `tsc`, ESLint.

**Comportamento.** O filtro por factura passa a ver-se, com o número da factura. Depois da última linha, o ecrã diz que não há mais e deixa voltar atrás. Um erro do servidor mostra a sua mensagem, em vez de parecer uma lista vazia, e um 404 não é repetido. O botão de filtrar por factura diz qual factura; uma linha sem descrição continua a ter nome acessível; sinalizações e notas com o mesmo código já não colidem.

**Normas.** Chaves de cache numa só fonte (`queryKeys`). A conversão dos valores dos filtros sai do componente para o gancho. Rótulos com tipo nomeado e guardas de tipo, sem asserções. Os três filtros partilham um componente. Ajudantes de teste com os tipos gerados. Comentários com exemplo nas funções públicas.

**Documentos.** §8.6 regista que as sinalizações e as notas mostram o texto em Português que a API devolve, como pede o ticket 03, sem segunda cópia no frontend.

### CHG-0059 · Resultados com filtros na rota

- **Data:** 2026-11-19
- **Tipo:** feat
- **Pai:** CHG-0058
- **Estado:** activa
- **Requisitos:** REQ-REV-001, REQ-PLT-006, SEC-08
- **Commit:** `f237ea9`
- **Migração:** nenhuma
- **Ficheiros:** `frontend/src/entities/result/*`, `features/results/*`, `pages/results-page.tsx`, `pages/invoice-page.tsx` e `pages/line-review-page.tsx` (rotas, preenchidas nos tickets 04 e 05), `router.tsx`, `shared/ui-kit/select.tsx`, `shared/i18n/*`, testes; `README.md`, ticket 03 do frontend
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 25 testes do frontend; `tsc`, ESLint.

Tabela das linhas de um trabalho com as onze colunas do ticket, texto das facturas sempre como texto. Filtros de confiança, aba, sinalização e factura na rota, validados campo a campo por Zod: um inválido cai, os outros ficam. Paginação pelo limite que o servidor devolve, com aviso quando o pedido foi cortado. Ligações para a revisão da linha e para a factura.

### CHG-0058 · Correcções da revisão do ticket 02 do frontend

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0057
- **Estado:** activa
- **Requisitos:** REQ-ING-007, REQ-PLT-006
- **Commit:** `505472a`
- **Migração:** nenhuma
- **Ficheiros:** `frontend/src/entities/job/*`, `entities/health/*`, `features/upload/*`, `pages/job-page.tsx`, `pages/upload-page.tsx`, `pages/results-page.tsx`, `app-shell.tsx`, `shared/i18n/*`, `shared/format.ts`, `shared/api/errors.ts`, `shared/ui-kit/*`, testes; `README.md`, `docs/04-padroes-de-codigo.md` (§8.5)
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 17 testes do frontend; `tsc`, ESLint.

**Comportamento.** Um envio só com ficheiros já carregados, em vários trabalhos, diz que nenhum trabalho novo foi criado e liga os outros. A sondagem cresce também com as falhas e pára quando o trabalho não existe, que o ecrã diz. Abrir um trabalho junta-o aos recentes. O estado e o progresso são anunciados (`aria-live`), a barra tem valores válidos com zero facturas, e a zona de arrastar não pisca nem acende quando desactivada.

**Normas.** O texto composto passa ao catálogo, com marcadores (`t(chave, valores)`), incluindo as unidades de tamanho. A decisão sai dos componentes para `useJobView`; a barra de progresso passa a `entities/job`. Identificador curto, formato de número e chave de ficheiro num só sítio; estados de saúde num só registo; estados de factura tipados. Comentários com exemplo nas funções públicas novas. Saem a chave e a variante de botão sem uso. §8.5 passa a dizer que a sondagem pára quando o trabalho termina ou não existe.

### CHG-0057 · Painel AMT e carregamento com progresso

- **Data:** 2026-11-19
- **Tipo:** feat
- **Pai:** CHG-0056
- **Estado:** activa
- **Requisitos:** REQ-ING-001, REQ-ING-007, REQ-PLT-006, SEC-15
- **Commit:** `4b1fcc8`
- **Migração:** nenhuma
- **Ficheiros:** `frontend/src/` (painel, carregamento, trabalho, tema, `ui-kit`), `frontend/scripts/generate-api-types.mjs`, `frontend/package.json`, `CLAUDE.md` (L-07), `README.md`, ticket 02 do frontend
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 15 testes do frontend com a API simulada; `tsc`, ESLint, licenças (`lucide-react` ISC, `zustand` MIT).

**Painel.** Barra lateral com o logo da AMT, a navegação, os trabalhos recentes deste navegador (só identificadores, em `localStorage`), o estado do servidor, a versão do catálogo e a saída. Paleta a partir do azul do logo (`#00137c`), com verde, âmbar e vermelho só para estados. O ecrã de entrada passa a mostrar o logo.

**Carregamento.** Arrastar ou escolher PDF, ver a lista, carregar. O ecrã do trabalho sonda com intervalo crescente até o trabalho terminar e mostra as facturas por estado, o progresso e os tokens; ficheiros já carregados mostram o trabalho onde estão. Os tipos da API passam a ser gerados por um script que dá `Blob` aos campos binários, para enviar ficheiros sem asserções de tipo.

**CLAUDE.md.** A linha de L-07 passa a registar o token de acesso e a sessão, por decisão do responsável.

### CHG-0056 · Correcções da revisão do ticket 01 do frontend

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0055
- **Estado:** activa
- **Requisitos:** SEC-06, SEC-19, SEC-15, REQ-PLT-006, REQ-PLT-007
- **Commit:** `3419814`
- **Migração:** nenhuma
- **Ficheiros:** `backend/src/sextante/platform/session.py`, `platform/credentials.py`, `platform/settings.py`, `platform/user_messages.py`, `tests/api/test_session_login.py`; `frontend/src/features/auth/*`, `entities/health/use-health.ts`, `pages/home-page.tsx`, `shared/i18n/pt.ts`, `test/api.ts`, `tsconfig.json`, `openapi.json` e tipos gerados; `README.md`, `docs/03-seguranca.md` (SEC-06, SEC-19), ticket 01 do frontend
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 374 testes do backend e o `xfail` estrito; 8 testes do frontend. `make golden` com 12 amostras sem divergências. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos; `tsc`, ESLint, licenças, build.

**Sessão.** A saída só leva à entrada quando o servidor a confirma; se falhar, a pessoa fica e vê a mensagem. Entrar de novo fecha a sessão anterior. O token tem de ser diferente da chave da API, ou o servidor recusa arrancar. Chave e token comparam-se pelos digests, para que nem o comprimento transpareça, numa só função. Os atributos do cookie vivem num só sítio. A mensagem de credencial recusada serve também a programas com a chave.

**Frontend.** O limite do token vem do documento OpenAPI, não de uma cópia. O ecrã inicial não tem texto literal, e o estado do servidor decide-se no gancho. A subscrição dos erros de sessão deixa de estar duplicada.

**Documentos.** SEC-19 regista a isenção de `Idempotency-Key` na entrada e na saída da sessão. SEC-06 e o README declaram a quota anónima única do login, risco aceite com o servidor ligado só a `127.0.0.1`.

### CHG-0055 · Esqueleto do frontend e login por token

- **Data:** 2026-11-19
- **Tipo:** feat
- **Pai:** CHG-0054
- **Estado:** activa
- **Requisitos:** SEC-06, SEC-02, SEC-12, SEC-15, REQ-PLT-006, REQ-PLT-007, NFR-DOC-001, NFR-LIC-001
- **Commit:** `4414e7f`
- **Migração:** nenhuma
- **Ficheiros:** `backend/src/sextante/platform/session.py` (novo), `platform/credentials.py` (era `api_key.py`), `platform/rate_limit.py`, `platform/settings.py`, `platform/http_errors.py`, `platform/user_messages.py`, `main.py`, `backend/Makefile`, testes `tests/api/test_session_login.py`, `test_openapi_contract.py`, `test_api_key.py`, `test_rate_limits.py`, `test_startup.py`, `conftest.py`; `frontend/` (novo); `config/.env.example`, `README.md`, `docs/00-decisoes-e-lacunas.md` (L-07), `docs/02-arquitectura.md` (§7), `docs/03-seguranca.md` (SEC-06, SEC-11)
- **Reversibilidade:** total
- **Reversão:** reverter o commit e retirar `SEXTANTE_ACCESS_TOKEN` do `config/.env`.
- **Verificação:** 372 testes do backend e o `xfail` estrito; 7 testes do frontend com a API simulada. `make golden` com 12 amostras sem divergências. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos. `tsc` estrito, ESLint, licenças de produção dentro de NFR-LIC-001, `npm audit` sem vulnerabilidades. Ensaio manual pelo proxy do Vite: recusa sem sessão, token errado, login com o cookie esperado, sessão, saída, cookie antigo recusado, e nenhum token no log.

**Servidor.** `SEXTANTE_ACCESS_TOKEN` passa a obrigatório, com pelo menos 16 caracteres. `POST /api/session` compara-o em tempo constante e abre uma sessão em cookie `HttpOnly`, `SameSite=Strict`, `Secure`, `Path=/api`, de 8 horas (`SEXTANTE_SESSION_HOURS`); `POST /api/session/end` termina-a; `GET /api/session` diz se há sessão. As sessões vivem na memória do processo, só pelo digest do identificador. O guarda de `/api` aceita a chave ou a sessão, que representam o mesmo principal e partilham a quota; o erro passa a `errors.auth.credential_invalid` e o evento a `credential_rejected`. O login tem limite próprio, 10 por minuto. O corpo de erro passa a modelo (`ErrorResponse`) declarado no OpenAPI.

**Frontend.** React 18, TypeScript estrito, Vite, TanStack Query e Router, React Hook Form com Zod, Sonner, Tailwind e componentes do shadcn/ui copiados para `ui-kit`. Os tipos da API são gerados de `frontend/openapi.json`, que um teste do backend mantém actualizado (`make openapi`). Ecrã de entrada e ecrã inicial com o estado do servidor, o digest do catálogo e a saída; um 401 a meio da sessão volta à entrada. Texto todo do catálogo `pt.ts`. Em desenvolvimento o Vite encaminha `/api` para o backend, e só variáveis `VITE_SEXTANTE_` chegam ao código compilado.

### CHG-0054 · Correcções da revisão da extracção isolada

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0053
- **Estado:** activa
- **Requisitos:** SEC-16, SEC-15, REQ-PLT-002, REQ-ING-003
- **Commit:** `a576754`
- **Migração:** nenhuma
- **Ficheiros:** `backend/src/sextante/ingestion/infrastructure/isolated_extractor.py`, `platform/settings.py`, `tests/extraction/test_isolated_extraction.py`, `tests/fixtures/synthetic_pdf.py`, `README.md`, `docs/03-seguranca.md` (SEC-16), ticket de operação 03
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 356 testes e o `xfail` estrito. A paridade com a leitura no processo passa a cobrir também um documento de outro tipo e um ficheiro ilegível. Os testes que dependem do `RLIMIT_AS` só correm em Linux. `make golden` com 12 amostras sem divergências. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Protocolo.** O limite atingido e as mensagens do filho passam a conjuntos fechados (`ExtractionLimit`, `StrEnum`), e cada tipo de mensagem é tratado pelo nome. Um filho que morre sem responder só conta como limite de memória quando morreu por SIGKILL, que é como o kernel termina um processo sem memória; outra morte falha a factura. Uma falha do filho regista `pdf_extraction_failed` com o tipo do erro, que a razão da factura (`PdfExtractionError`) já não mostra.

**Limites.** No Linux, um limite que não se consegue pôr falha a factura: o controlo falha fechado, nunca lê sem limite. Noutra plataforma o limite de memória não é aplicado (o macOS aceita `RLIMIT_AS` sem o aplicar), e o filho di-lo no log. O filho tem também um limite de CPU, o tempo mais 5 s, para terminar sozinho se o servidor morrer durante a leitura. O contexto de processos é criado no primeiro uso, com `forkserver` onde exista e `spawn` onde não, em vez de falhar na importação.

**Normas.** As fixtures hostis partilham o construtor de documentos, sem parâmetros que só os valores por omissão usavam. Os novos campos de configuração deixam de partir o par do tecto de chamadas.

### CHG-0053 · Extracção de PDF isolada com limites

- **Data:** 2026-11-19
- **Tipo:** security
- **Pai:** CHG-0052
- **Estado:** activa
- **Requisitos:** SEC-16, SEC-15, REQ-PLT-002, REQ-ING-003, REQ-ING-009
- **Commit:** `43a496d`
- **Migração:** nenhuma
- **Ficheiros:** `backend/src/sextante/ingestion/infrastructure/isolated_extractor.py`, `ingestion/infrastructure/pdf_invoice_extractor.py` (`MemoryError` reconhecido sob a excepção do pdfplumber), `worker.py` (extracção fora do ciclo de eventos), `main.py`, `platform/settings.py`, `tests/extraction/test_isolated_extraction.py`, `tests/fixtures/synthetic_pdf.py` (PDF sintético com bomba de descompressão e PDF lento), `README.md`, `config/.env.example`, `docs/02-arquitectura.md` §4.3, `docs/03-seguranca.md` (SEC-16), ticket de operação 03
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 354 testes e o `xfail` estrito. Testes novos: um PDF válido e um digitalizado dão o mesmo resultado lidos à parte e no processo; um PDF sintético de 1 MiB que expande para 1 GiB é recusado pelo limite de memória; um PDF sintético com cinco milhões de operadores é recusado pelo limite de tempo em menos de 5 s; o log regista o limite sem conteúdo; um XLSX é recusado sem abrir processo; pela API, o trabalhador recusa a bomba e codifica a factura seguinte; valores por omissão e limites fora do intervalo recusam o arranque. `make golden` com 12 amostras sem divergências. `mypy`, `ruff`, 8 contratos do `import-linter`, licenças, funções com 20 linhas ou menos.

**Comportamento.** Cada PDF é lido num processo filho, com limite de espaço de endereçamento (`SEXTANTE_PDF_EXTRACTION_MEMORY_MIB`, 512 por omissão) e de tempo (`SEXTANTE_PDF_EXTRACTION_TIMEOUT_SECONDS`, 30 por omissão). Acima de um limite o filho é parado, o documento é recusado como `unsupported_document_type`, e o log regista `pdf_extraction_limit_reached` com o limite atingido. Um filho que morre sem responder, como o kernel faz a um processo sem memória, conta como limite de memória. Outra falha do filho falha a factura, como antes, nunca é engolida.

**Decisões.** Os filhos partem de um servidor de processos (`forkserver`) com o extractor já importado: nem `fork` a partir de um processo com threads, nem um interpretador novo por PDF. A extracção corre fora do ciclo de eventos (`asyncio.to_thread`), para que a API continue a responder durante uma leitura de até 30 s. O limite de memória é `RLIMIT_AS`, aplicado pelo Linux, com ou sem Docker; noutra plataforma o filho regista `pdf_memory_limit_unavailable` e só o limite de tempo se aplica.

### CHG-0052 · Correcções da revisão do tecto de chamadas ao modelo

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0051
- **Estado:** activa
- **Requisitos:** SEC-12, NFR-REL-001, NFR-REL-002, REQ-PLT-003, SEC-15
- **Commit:** `dc32a24`
- **Migração:** nenhuma (o esquema continua na revisão `0009`)
- **Ficheiros:** `backend/src/sextante/platform/model_call_ceiling.py` (`CeilingObserver`), `platform/rate_limit.py` (`RateLimit.window_at`, `seconds_left`), `worker.py` (`JobCeilingStatus`, reposição no arranque), `ingestion/domain/statuses.py`, `ingestion/application/ports.py` e `ingestion/infrastructure/repository.py` (`change_job_status`, `finish_job` condicional, `requeue_interrupted_jobs`), `main.py` (`model_call_limit`), `tests/api/test_model_call_ceiling.py`, `tests/platform/test_model_call_ceiling.py`, `tests/fakes/held_clock.py`, `tests/fakes/fixed_clock.py`, `README.md`, `docs/03-seguranca.md` (SEC-12), ticket de operação 02
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 345 testes e o `xfail` estrito. Testes novos: uma nova tentativa acima do tecto marca o trabalho como `waiting_model`; uma factura recusada não espera; uma factura reprocessada durante a espera é codificada de novo; um trabalho deixado em espera por um processo parado é codificado depois do reinício; testes unitários das janelas do tecto. `make golden` com 12 amostras sem divergências. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Onde se espera.** A espera passa da verificação antes de cada factura para a própria chamada ao modelo. Um observador (`JobCeilingStatus`) marca o trabalho reivindicado e regista o log. Assim, uma nova tentativa a meio de uma factura também marca o trabalho, e uma factura que não chama o modelo nunca espera.

**Estado do trabalho.** As mudanças entre `running` e `waiting_model`, e o fecho do trabalho, passam a ser condicionais. Um trabalho que um reprocessamento repôs em `queued` fica em `queued`, e o trabalhador reivindica-o de novo. Antes, o fecho sobrescrevia-o com `completed`, e a factura reposta ficava em `queued` para sempre. No arranque, os trabalhos em `running` ou `waiting_model` voltam a `queued`: há um só trabalhador, no único processo (D-3.4), e um trabalho reivindicado no arranque foi interrompido.

**Normas.** A aritmética da janela fixa passa a viver em `RateLimit`, partilhada pelos limites de taxa e pelo tecto. O duplo de relógio passa para `tests/fakes/`. O teste deixa de usar `Any`. As docstrings novas têm exemplo.

### CHG-0051 · Tecto de chamadas ao modelo no trabalhador

- **Data:** 2026-11-19
- **Tipo:** security
- **Pai:** CHG-0050
- **Estado:** activa
- **Requisitos:** SEC-12, REQ-PLT-002, REQ-PLT-003, SEC-15
- **Commit:** `3517ee5`
- **Migração:** nenhuma (o estado do trabalho é texto; o esquema continua na revisão `0009`)
- **Ficheiros:** `backend/src/sextante/platform/model_call_ceiling.py`, `matching/application/ceiling_classifier.py`, `worker.py`, `main.py`, `platform/settings.py`, `ingestion/domain/statuses.py` (`waiting_model`), `ingestion/application/ports.py` e `ingestion/infrastructure/repository.py` (`set_job_status`), `tests/api/test_model_call_ceiling.py`, `README.md`, `config/.env.example`, `docs/02-arquitectura.md`, `docs/03-seguranca.md` (SEC-12), ticket de operação 02
- **Reversibilidade:** total
- **Reversão:** reverter o commit. Um trabalho deixado em `waiting_model` por um processo parado fica como um em `running`.
- **Verificação:** 339 testes e o `xfail` estrito; testes novos com o `FakeItemClassifier` e um relógio monotónico controlado: acima do tecto a factura fica `queued`, o trabalho mostra `waiting_model`, e tudo é codificado quando a janela abre, sem nenhuma factura `failed`; uma nova tentativa conta no tecto; o log regista a espera sem conteúdo da factura; valores por omissão; tecto ou janela abaixo de 1 recusam o arranque. `make golden` com 12 amostras sem divergências. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Comportamento.** O trabalhador faz no máximo `SEXTANTE_MODEL_CALL_CEILING` chamadas ao modelo por `SEXTANTE_MODEL_CALL_WINDOW_SECONDS`, 200 por hora por omissão, valor provisório. Cada chamada conta, novas tentativas incluídas, porque cada tentativa é paga. Antes de cada factura, se o tecto está cheio, o trabalho passa a `waiting_model`, o log regista `model_call_ceiling_reached` com o trabalho e os segundos de espera, e o trabalhador espera pela janela seguinte; depois volta a `running`. Recusar seria perder trabalho; atrasar é só atrasar.

**Limites declarados.** O contador vive na memória do processo, como os limites de taxa. Uma nova tentativa a meio de uma factura também espera pelo tecto, mas sem marcar o trabalho. Uma factura que não chama o modelo (rejeitada, entidade ambígua, sem linhas de serviço) espera igualmente quando o tecto está cheio.

### CHG-0050 · Correcções da revisão dos limites de taxa

- **Data:** 2026-11-19
- **Tipo:** fix
- **Pai:** CHG-0049
- **Estado:** activa
- **Requisitos:** SEC-12, SEC-19, SEC-15
- **Commit:** `98a2968`
- **Migração:** nenhuma (o esquema continua na revisão `0009`)
- **Ficheiros:** `backend/src/sextante/platform/rate_limit.py`, `platform/errors.py` (`response_headers`), `platform/http_errors.py`, `main.py`, `tests/api/test_rate_limits.py`, `docs/03-seguranca.md` (SEC-12), `README.md`, ticket de operação 01
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 333 testes e o `xfail` estrito, agora preso a `AssertionError`; `Retry-After` verificado no valor exacto; testes novos para os valores por omissão, para a chave de idempotência repetida que conta no limite, para o pedido recusado que não gasta quota geral, e para a resolução de entidade e a aceitação sob os limites caros. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Regras.** Os nomes dos limites passam a um conjunto fechado (`RateRule`). As rotas caras são nomeadas pela função da rota, na composição: uma rota renomeada falha na importação, em vez de perder o limite em silêncio.

**Contagem.** Um pedido só conta quando todos os limites o deixam passar. A memória é um contador por regra e chamador, sem percorrer o dicionário a cada pedido. O `Retry-After` sai por um método do erro de domínio, sem o tratador genérico inspeccionar uma subclasse.

**Âmbito.** A resolução de entidade, que põe codificação paga na fila, partilha o limite do reprocessamento; a aceitação de linha partilha o da correcção. O ramo do endereço de origem, que a verificação da chave tornava inalcançável, sai. SEC-12 e o `README.md` passam a dizer que, com uma só chave, há uma só quota partilhada, e que uma janela fixa deixa passar até o dobro da quota na fronteira.

### CHG-0049 · Limites de taxa por endpoint

- **Data:** 2026-11-19
- **Tipo:** security
- **Pai:** CHG-0048
- **Estado:** activa
- **Requisitos:** SEC-12, SEC-19, SEC-15
- **Commit:** `1d7e54e`
- **Migração:** nenhuma (o esquema continua na revisão `0009`)
- **Ficheiros:**
  - `backend/src/sextante/platform/rate_limit.py` (novo), `platform/http_errors.py` (`Retry-After`), `platform/settings.py`, `platform/user_messages.py`, `main.py`
  - testes: `tests/api/test_rate_limits.py` (novo)
  - `docs/03-seguranca.md` (SEC-12), `README.md`, `config/.env.example`, ticket de operação 01
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 329 testes e um `xfail` estrito: 429 com `Retry-After` acima do limite, a janela que reabre, o limite geral sobre todas as chamadas, health e credenciais recusadas fora das quotas, limites próprios de reprocessamento, exportação e correcção, e um limite abaixo de 1 a recusar o arranque. O teste com duas instâncias falha na asserção esperada, como documentação da limitação. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Limites.** Os de SEC-12, configuráveis: 300 por minuto em todo o `/api`, 10 carregamentos por minuto, 20 reprocessamentos por hora, 30 exportações por hora e 120 correcções por minuto. Acima de um limite, `429` com `Retry-After` e a mensagem habitual em Português. `/api/health` fica de fora, e a verificação da chave corre antes, para que uma credencial recusada não gaste quota.

**Limitação declarada.** O contador vive em memória do processo. Com duas instâncias, cada uma permite a quota inteira; o teste que o prova falha de propósito. Em produção, um contador partilhado.

### CHG-0048 · Tickets do frontend, da operação e do deploy

- **Data:** 2026-11-19
- **Tipo:** docs
- **Pai:** CHG-0047
- **Estado:** activa
- **Requisitos:** SEC-06, SEC-11, SEC-12, SEC-19, L-07, L-11, REQ-PLT-008
- **Commit:** `99f231e`
- **Migração:** nenhuma (o esquema continua na revisão `0009`)
- **Ficheiros:** `.scratch/frontend/issues/` (6 tickets), `.scratch/operacao/issues/` (4), `.scratch/deploy/issues/` (2)
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** a divisão foi aprovada pelo responsável em 19-11-2026.

**Tickets.** Doze fatias verticais, numa pasta por grupo, aprovadas pelo responsável:
- **frontend:** esqueleto e login por token, carregamento, resultados, revisão de linha, factura e resolução de entidade, exportação e reprocessamento;
- **operação:** limites de taxa, tecto de chamadas ao modelo, extracção isolada com limites, retenção e purga;
- **deploy:** contentor da API e compose, contentor do frontend.

**Decisões do responsável.** O frontend entra com um token de acesso definido numa variável de ambiente do backend, comparado no servidor, em vez de email e palavra-passe. Os tickets que dependiam de respostas da AMT ficam de fora. Tudo tem de correr com e sem Docker e ficar documentado no `README.md`. Retenção e purga fica em `needs-info`, à espera dos prazos de L-11.

### CHG-0047 · Chave da API em todo o /api excepto health

- **Data:** 2026-11-19
- **Tipo:** security
- **Pai:** CHG-0046
- **Estado:** activa
- **Requisitos:** SEC-06, SEC-02, SEC-15, REQ-PLT-007, L-07
- **Commit:** `bbdbb1a`
- **Migração:** nenhuma (o esquema continua na revisão `0009`)
- **Ficheiros:**
  - `backend/src/sextante/platform/api_key.py` (novo), `platform/settings.py` (`api_key`), `platform/user_messages.py`, `main.py`
  - testes: `tests/api/test_api_key.py` (novo), `tests/conftest.py`, harness e clientes de teste
  - `docs/03-seguranca.md` (SEC-06), `docs/00-decisoes-e-lacunas.md` (L-07), `CLAUDE.md` (tabela de lacunas), `OPEN-ITEMS.md` (item 14), `README.md`, `config/.env.example`
- **Reversibilidade:** total
- **Reversão:** reverter o commit. A API volta a ficar aberta a quem chegue à máquina.
- **Verificação:** 323 testes, incluindo: sem chave ou com chave errada, 401 com a mensagem em Português; com a chave certa, o pedido chega à rota; `/api/health` e `/docs` abertos; o esquema `X-API-Key` na descrição da API; a chave recusada nunca no log; uma chave curta recusa o arranque. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Decisão do responsável (L-07).** A API deixa de estar aberta. Uma chave única, `SEXTANTE_API_KEY`, obrigatória e com pelo menos 16 caracteres, é exigida no cabeçalho `X-API-Key` em todo o `/api` excepto `/api/health`. É comparada em tempo constante. A recusa é um 401 com o corpo de erro habitual e fica no log sem a chave enviada. O Swagger fica aberto para leitura, com o botão "Authorize". Não há perfis nem chave por pessoa: o autor das revisões continua a ser `SEXTANTE_REVIEWER_ID`, e o servidor continua só em `127.0.0.1`.

### CHG-0046 · Idempotency-Key declarado na documentação da API

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0045
- **Estado:** activa
- **Requisitos:** SEC-19, NFR-DOC-001
- **Commit:** `84872fc`
- **Migração:** nenhuma (o esquema continua na revisão `0009`)
- **Ficheiros:** `backend/src/sextante/platform/idempotent_route.py`, rotas de `ingestion` e `review`, `tests/api/test_upload_and_listing_contracts.py`, `config/.env.example`, `README.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 314 testes. O teste novo falha quando se retira a declaração das rotas. A aplicação arrancou localmente: `/docs` responde 200 e `/openapi.json` tem os 11 caminhos.

**Defeito.** O cabeçalho `Idempotency-Key` é obrigatório nas escritas de revisão, no reprocessamento e na resolução de entidade, mas não estava declarado na descrição da API. No Swagger não havia onde o preencher, e esses pedidos falhavam todos com 422. Passa a estar declarado nas quatro rotas; a validação continua em `require_key`.

**Configuração.** O comentário do NIF em `config/.env.example` dizia que o valor vinha das amostras; o valor é sintético desde CHG-0039. Passa a dizer que tem de ser substituído pelo NIF real da AMT, senão as facturas da AMT ficam ambíguas pelo veto do NIF.

**README.** Diz onde está o Swagger e como preencher o cabeçalho.

### CHG-0045 · Pasta sources fora do .gitignore e regra dos pedidos repetidos confirmada

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0044
- **Estado:** activa
- **Requisitos:** D-3.23, SEC-19
- **Commit:** `badb8f3`
- **Migração:** nenhuma (o esquema continua na revisão `0009`)
- **Ficheiros:** `.gitignore`, `docs/00-decisoes-e-lacunas.md` (§3.23), ticket 14
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** `sources/catalog.xlsx` continua versionado e igual à cópia sem metadados de CHG-0040; nenhum outro ficheiro em `sources/`.

**Pedido do responsável.** A pasta `sources/` deixa de constar do `.gitignore`. O catálogo já estava versionado, por excepção a essa regra; a regra sai. Fica a cautela: um ficheiro novo posto em `sources/` passa a poder entrar num commit, por isso o catálogo original, com metadados, não deve voltar para lá.

**Confirmação.** O responsável confirmou a regra dos pedidos repetidos de §3.23: a mesma chave repete a resposta; outra chave, com a factura em fila, não faz nada; um pedido depois de a recodificação terminar é uma recodificação nova.

### CHG-0044 · Correcções da revisão do ticket 14

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0043
- **Estado:** activa
- **Requisitos:** NFR-REL-002, REQ-REV-004, D-3.23, SEC-19
- **Commit:** `1aca630`
- **Migração:** nenhuma (o esquema continua na revisão `0009`)
- **Ficheiros:**
  - `backend/src/sextante/matching/` (porta `ReviewedLinesReader`, sinalização das linhas revistas dentro da transacção, `read_line_history`, `summary_in_force` em vez de `codings_in_force`)
  - `backend/src/sextante/review/` (`ReadLineHistory`, rota de histórico, `CodingsInForce.reviewed_lines`), `worker.py`, `main.py`
  - testes: `tests/api/test_recoding.py`
  - `docs/00-decisoes-e-lacunas.md` (§3.23), `docs/02-arquitectura.md` (`lexical_score`), spec, `README.md`, ticket 14
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 313 testes; os da recodificação verificam pela API (histórico e tokens do trabalho) o que antes verificavam com SQL directo. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Histórico consultável.** `GET /api/invoices/{id}/lines/{line_id}/history` mostra todas as codificações da linha, em vigor ou substituídas, cada uma com a versão do prompt, o modelo, o digest do catálogo e a revisão que uma pessoa fez dela. Antes, a codificação anterior e a sua revisão só se viam na base de dados.

**Revisões lidas na transacção.** Saber se uma linha foi revista passa a correr na transacção que substitui a codificação, através de uma porta do módulo de codificação que o módulo de revisão implementa. Fecha a janela em que uma revisão gravada enquanto o modelo respondia se perdia sem sinalização. Cobre também a recodificação que dá entidade ambígua. As sinalizações por linha deixam de passar pelo trabalhador.

**Documentos.** `docs/02` descreve `lexical_score` por codificação. A spec deixa de pôr a cache de prompt e a recodificação fora do âmbito. §3.23 regista a regra dos pedidos repetidos com chaves diferentes, a confirmar pelo responsável.

### CHG-0043 · Recodificação com histórico

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0042
- **Estado:** activa
- **Requisitos:** NFR-REL-002, REQ-REV-004, REQ-AUD-002, REQ-AUD-003, SEC-19, D-3.23
- **Commit:** `64db2b8`
- **Migração:** `0009_scores_per_coding` (`lexical_score` passa a ter chave `(encoded_line_id, item_number)`; as pontuações existentes passam para a codificação em vigor da sua linha)
- **Ficheiros:**
  - `backend/src/sextante/ingestion/application/reprocess_invoice.py`, `worker.py`, `main.py`
  - `backend/src/sextante/matching/` (`LineCoder` com sinalizações por linha, `EncodeInvoice` com o evento `invoice_recoded`, pontuações por codificação, `codings_in_force`, sinalização `review_superseded`)
  - `backend/src/sextante/review/application/codings_in_force.py` (`reviewed`), `platform/user_messages.py`
  - `backend/migrations/versions/0009_scores_per_coding.py`
  - testes: `tests/api/test_recoding.py` (novo), `tests/api/test_worker_resilience.py`, `tests/api/test_startup_database.py`
  - `docs/00-decisoes-e-lacunas.md` (§3.23, nota em §3.20), `README.md`, ticket 14
- **Reversibilidade:** parcial
- **Reversão:** reverter o commit e descer a migração para `0008`. As pontuações das codificações substituídas perdem-se na descida; as codificações e a auditoria ficam.
- **Verificação:** 312 testes, incluindo a recodificação com a anterior guardada como substituída, uma chamada nova ao modelo e nenhuma extracção nova, resultados, candidatos e exportação só com a codificação em vigor, a linha revista de volta à revisão com a revisão anterior intacta, o evento `invoice_recoded`, e o mesmo pedido duas vezes a codificar uma só vez. A descida das migrações é exercida pelo teste da 0007. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Decisão do responsável.** Uma revisão humana feita sobre a codificação anterior não se perde nem vale em silêncio para o código novo: a linha volta à revisão com `review_superseded`, e a revisão anterior fica com a codificação anterior e na auditoria.

**Recodificação.** O reprocessamento aceita facturas com falha e codificadas. A codificação parte do texto guardado; as linhas anteriores ficam marcadas como substituídas e as suas pontuações ficam com elas. Uma factura recusada ou ambígua continua recusada com 409.

**Auditoria.** `invoice_recoded` regista as versões do prompt e os digests do catálogo anteriores e novos, o número de linhas substituídas e o de revisões sinalizadas de novo.

### CHG-0042 · Prompt v2 com cache de prompt

- **Data:** 2026-11-18
- **Tipo:** improve
- **Pai:** CHG-0041
- **Estado:** activa
- **Requisitos:** REQ-MAP-004, REQ-MAP-005, REQ-AUD-003, REQ-AUD-004, SEC-14
- **Commit:** `c1cae2b`
- **Migração:** `0008_model_call_cache_tokens` (colunas `cache_creation_input_tokens` e `cache_read_input_tokens` em `model_call`, a zero nas chamadas anteriores)
- **Ficheiros:**
  - `backend/src/sextante/prompts/item_choice_v2.txt` (novo, texto aprovado), `prompts/__init__.py` (versões)
  - `backend/src/sextante/matching/infrastructure/claude_classifier.py`, `tables.py`, `repository.py`, `matching/domain/item_choice.py`
  - `backend/migrations/versions/0008_model_call_cache_tokens.py`
  - testes: `tests/adapters/test_claude_classifier.py`, `tests/api/test_startup_database.py`, `tests/golden/`
  - `docs/00-decisoes-e-lacunas.md` (§3.22), `README.md`, ticket 11
- **Reversibilidade:** total
- **Reversão:** reverter o commit e descer a migração para `0007`. O prompt v1 continua no repositório.
- **Verificação:** 307 testes; `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos. `make golden-model` com `claude-sonnet-5-5` e o prompt v2: 12 linhas, 12 com o código esperado, 3 sinalizadas; 1 204 tokens de entrada sem cache, 4 436 escritos na cache e 17 744 lidos dela, contra 23 094 sem cache. O custo da entrada desce cerca de 63%.

**Aprovação.** O responsável aprovou o texto `item-choice-v2` e a passagem da lista de candidatos para a parte de sistema em cache, em 18-11-2026. Só o segundo parágrafo muda.

**Cache.** A lista de candidatos de uma aba é igual em todas as facturas que vão para essa aba. Passa a ser um segundo bloco de sistema, `<catalog_candidates>`, marcado com `cache_control`. A primeira chamada de cada aba escreve-a na cache, a 1,25 vezes o preço; as seguintes, nos cinco minutos, lêem-na a um décimo. O conteúdo da factura fica em `<invoice_data>`, na mensagem do utilizador, fora da parte em cache, e continua delimitado com `<` escapado. A lista de candidatos também.

**Registo.** Cada chamada guarda os tokens escritos e lidos da cache, que custam de forma diferente da entrada normal. O comando manual mostra-os.

### CHG-0041 · Modelo por omissão passa a Sonnet

- **Data:** 2026-11-18
- **Tipo:** improve
- **Pai:** CHG-0040
- **Estado:** activa
- **Requisitos:** REQ-MAP-005, REQ-AUD-003
- **Commit:** `920ad15`
- **Migração:** nenhuma
- **Ficheiros:** `backend/src/sextante/platform/settings.py`, `config/.env.example`, `README.md`, `docs/00-decisoes-e-lacunas.md` (§3.22), `backend/tests/adapters/test_claude_classifier.py`
- **Reversibilidade:** total
- **Reversão:** reverter o commit, ou definir `SEXTANTE_MODEL_ID=claude-opus-5-5`.
- **Verificação:** 306 testes. `make golden-model` com `claude-sonnet-5-5` e o prompt v1: 12 linhas, 12 com o código esperado, 3 sinalizadas, 23 094 tokens de entrada e 304 de saída, o mesmo resultado do Opus.

**Pedido do responsável.** O modelo por omissão passa de `claude-opus-5-5` a `claude-sonnet-5-5`, por custo: 2 USD por milhão de tokens de entrada e 10 de saída, contra 4 e 20. A configuração aprovada em §3.22 continua válida no Sonnet: sem parâmetros de amostragem, saída por esquema, esforço baixo e o recurso de servidor `"default"`, que é a forma que o Sonnet aceita. O modelo que respondeu continua registado em cada decisão.

### CHG-0040 · Catálogo no repositório, sem metadados pessoais

- **Data:** 2026-11-18
- **Tipo:** infra
- **Pai:** CHG-0039
- **Estado:** activa
- **Requisitos:** REQ-PLT-007, SEC-03
- **Commit:** `9dcf0d4`
- **Migração:** nenhuma
- **Ficheiros:** `sources/catalog.xlsx` (novo), `.gitignore`, `README.md`, `OPEN-ITEMS.md` (item 17)
- **Reversibilidade:** parcial
- **Reversão:** reverter o commit retira o ficheiro da versão, mas ele continua no histórico de um repositório já publicado.
- **Verificação:** as duas abas lidas com `openpyxl` são iguais às do original (45 e 21 linhas, cabeçalho incluído); o catálogo passa a validação de arranque (44 e 20 itens); nenhuma ocorrência do nome do autor nem do caminho do Windows no ficheiro.

**Pedido do responsável.** O catálogo entra no repositório, para que quem receber o projecto o possa testar. A cópia versionada não tem o autor, o último editor nem o caminho local do Windows que o original guardava nos metadados (item 17 de `OPEN-ITEMS.md`); os dados são os mesmos. O digest do catálogo muda com os metadados, por isso codificações antigas citam outro digest.

### CHG-0039 · Repositório e histórico sem dados das amostras

- **Data:** 2026-11-18
- **Tipo:** security
- **Pai:** CHG-0038
- **Estado:** activa
- **Requisitos:** D-3.18, SEC-03
- **Commit:** `dedb83a`
- **Migração:** nenhuma
- **Ficheiros:** 22 ficheiros versionados: tickets 02, 03, 12 e 13, `OPEN-ITEMS.md`, `CHANGELOG.md`, `docs/00` a `docs/02`, `config/.env.example`, testes e fixtures, e duas docstrings de exemplo do código
- **Reversibilidade:** não
- **Reversão:** a reescrita do histórico não se desfaz por um commit, e não deve: o objectivo é que nenhum commit publicado traga os dados.
- **Verificação:** 306 testes; nenhum dos valores das amostras em nenhum ficheiro versionado, nem em nenhum commit do ramo depois da reescrita. Os valores foram extraídos localmente das 12 amostras, para os procurar, e nenhum foi escrito no repositório.

**Motivo.** O repositório vai ser público. D-3.18 diz que nenhuma amostra, nem excerto de amostra, entra no repositório. Os documentos e o histórico citavam valores das amostras: nomes de fornecedores e clientes, NIFs, números de documento, moradas, descrições de linhas e observações, e os valores da nota da AGT.

**O que mudou.** Esses valores passam a valores sintéticos com a mesma estrutura, pelo mesmo mapa, na versão actual e em todos os commits do ramo, ficheiros e mensagens. O nome da AMT fica, porque é o cliente do enunciado. Os nomes dos itens do catálogo também ficam, porque o catálogo não é amostra. O NIF da AMT no repositório passa a sintético; o real fica só na configuração local.

**Hashes.** A reescrita muda os hashes de todos os commits. Os campos `Commit` e os hashes citados são actualizados no commit seguinte, como permite a regra 4.

### CHG-0038 · Fornecedor e moeda no pedido ao modelo (REQ-MAP-005)

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0037
- **Estado:** activa
- **Requisitos:** REQ-MAP-005, SEC-14
- **Commit:** `5a292e4`
- **Migração:** nenhuma
- **Ficheiros:** `docs/01-requisitos.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** o requisito passa a descrever o pedido que o adaptador já envia e que o prompt aprovado descreve; o código não muda.

**Decisão do responsável.** REQ-MAP-005 passa a listar o nome do fornecedor e a moeda entre o que o modelo recebe. Já iam no pedido, como dados delimitados, e o prompt aprovado descreve-os; o requisito não os mencionava.

### CHG-0037 · Correcções da revisão dos tickets 11 e 13

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0036
- **Estado:** activa
- **Requisitos:** REQ-MAP-005, REQ-MAP-007, REQ-PLT-003, NFR-TST-001
- **Commit:** `652577b`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/matching/application/line_coding.py` (novo: `LineCoder`), `encode_invoice.py`
  - `backend/src/sextante/matching/infrastructure/claude_classifier.py` (`create_model_client`, estados transitórios, mensagens)
  - `backend/src/sextante/main.py` (`coding_rules`, `require_generic_items_in_catalog`, classificador sem `None` intermédio), `platform/settings.py` (`ModelCallSettings`)
  - `backend/tests/golden/model_run.py`, `runner.py`; testes `tests/adapters/`, `tests/golden/`
  - tickets 11 e 13
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 306 testes; `mypy`, `ruff`, 8 contratos do `import-linter`, licenças, funções com 20 linhas ou menos. `make golden-model` contra a API real, com `claude-opus-5-5`: o pedido foi aceite e as respostas lidas; 12 linhas, 12 com o código esperado, 3 sinalizadas, 23 094 tokens de entrada e 304 de saída.

**Uma só lógica de codificação.** Decidir as linhas (chamada com repetições, validação, regra de confiança, sinalizações da factura) passa para `LineCoder`, sem persistência. `EncodeInvoice` guarda o que ele decide. O comando manual usa o mesmo `LineCoder`, as mesmas regras (`coding_rules`) e o mesmo cliente (`create_model_client`), em vez de uma cópia que já divergia nas repetições. Os parâmetros da chamada ficam em `ModelCallSettings`, partilhada pelas duas configurações.

**Adaptador.** 408 e 409 contam como transitórios, como 429 e 5xx. As mensagens de indisponível dizem o estado e a forma esperada. Um 400 não é repetido: o teste verifica um único pedido.

**Arranque.** O classificador deixa de passar por `None` e `replace`: o injectado ou o de Claude é passado directamente, e o cliente da API só é criado quando é preciso.

**Relatório manual.** O motivo de uma linha sem código (sem aba, modelo indisponível) deixa de ocupar o campo da confiança. Os tokens passam a ter um tipo próprio.

**Primeira medição real.** Contra a proposta ainda por confirmar pela AMT: 12 de 12 linhas com o código esperado; sinalizadas uma linha com o recurso O00999 e duas `MEDIUM` com candidatos próximos. Só para calibração, não para publicação (L-02).

### CHG-0036 · Medição manual dos códigos com o modelo real

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0035
- **Estado:** activa
- **Requisitos:** NFR-TST-001, D-3.18, L-02, SEC-15
- **Commit:** `0c1227e`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/tests/golden/model_run.py` (novo), `backend/tests/golden/runner.py`, `backend/Makefile` (`golden-model`)
  - `backend/src/sextante/matching/application/encode_invoice.py` (`item_choice_request` passa a público, para o comando usar o mesmo pedido)
  - testes: `tests/golden/test_golden_set.py`
  - ticket 13
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 304 testes, incluindo o relatório só com códigos e confiança; `mypy`, `ruff`, funções com 20 linhas ou menos. A primeira execução real foi recusada pela API por falta de crédito; o comando terminou com essa mensagem e código 2.

**Comando.** `make golden-model` codifica as amostras como a aplicação: o mesmo pedido, a mesma validação e a mesma regra de confiança. Reporta, por linha, o código esperado e o atribuído e a confiança, depois as linhas sinalizadas e os tokens gastos. Chama a API e custa dinheiro: só corre de propósito, fora de `make test` e da integração contínua. Um erro da API, como uma chave errada ou falta de crédito, termina com a mensagem da API e código 2. O ticket 13 fica fechado.

### CHG-0035 · Adaptador Claude do ItemClassifier e prompt v1

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0034
- **Estado:** activa
- **Requisitos:** REQ-MAP-005, REQ-MAP-007, REQ-AUD-003, REQ-AUD-004, REQ-PLT-003, SEC-14, SEC-15
- **Commit:** `d50659c`
- **Migração:** nenhuma
- **Dependência nova:** `anthropic` 1.17 (MIT), sobre `httpx2`, que já estava no projecto. `make licenses` passa.
- **Ficheiros:**
  - `backend/src/sextante/matching/infrastructure/claude_classifier.py` (novo); `unconfigured_classifier.py` retirado
  - `backend/src/sextante/prompts/` (novo: `item_choice_v1.txt`, o texto aprovado, e o carregador com a versão)
  - `backend/src/sextante/main.py`, `platform/settings.py` (`SEXTANTE_MODEL_ID`), `backend/pyproject.toml`
  - testes: `tests/adapters/test_claude_classifier.py` (novo), `tests/api/test_entity_routing.py`
  - `docs/00-decisoes-e-lacunas.md` (§3.22, e nota em §3.7), `docs/01-requisitos.md` (REQ-MAP-007), `docs/02-arquitectura.md`, spec, `config/.env.example`, `README.md`, tickets 11 e 14
- **Reversibilidade:** total
- **Reversão:** reverter o commit. Sem classificador, as facturas com linhas de serviço voltam a falhar sem código.
- **Verificação:** 304 testes. Os do adaptador respondem por um transporte HTTP em memória e verificam o pedido (prompt aprovado, esquema, esforço baixo, sem `temperature` nem ferramentas, recurso de servidor), os dados delimitados que uma descrição não consegue fechar, a leitura da resposta (índices, modelo, versão, tokens), as respostas inutilizáveis sem valor por omissão, e o mapeamento de 429, 5xx e falha de rede para indisponível. Nenhum teste chama a API. `mypy`, `ruff`, 8 contratos do `import-linter`, licenças.

**Aprovação.** O responsável aprovou a configuração da chamada e o texto do prompt `item-choice-v1` em 18-11-2026, tal como propostos. O registo está em §3.22 e no ticket 11.

**Configuração.** Sem `temperature`, que a API recusa em todos os modelos desde 21-10-2026. Resposta JSON restringida por `output_config.format`, porque os modelos actuais recusam ferramenta forçada. Modelo `SEXTANTE_MODEL_ID`, por omissão `claude-opus-5-5`. `effort` baixo. `max_tokens` de 2048 mais 64 por linha. Recurso de servidor numa recusa de segurança. O cliente não repete: a repetição é do caso de uso.

**Fronteira do modelo.** O conteúdo da factura vai como JSON dentro de `<invoice_data>`, com `<` escapado. O prompt pede só um índice ou `null` por linha e não repete nenhuma regra que vive em código. Uma resposta recusada, cortada ou ilegível não dá escolha nenhuma: todas as linhas ficam inválidas, `LOW` e sinalizadas. Uma entrada fora do esquema perde só a sua linha. O log guarda só o motivo de paragem ou o tipo de erro.

**Chave.** A chave do responsável foi usada uma vez, à mão, só pelo ambiente. Não está em nenhum ficheiro.

### CHG-0034 · Réplicas sem dados das amostras, XLSX recusado e padrão do conjunto dourado

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0033
- **Estado:** activa
- **Requisitos:** REQ-ING-001, REQ-ING-009, NFR-TST-001, D-3.6, D-3.18
- **Commit:** `64bfa67`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/tests/fixtures/synthetic_invoices.py` e os testes que usam as suas réplicas; `tests/domain/test_entity_check.py`, `test_export_rules.py`, `test_lexical_scoring.py`, `test_line_type.py`, `tests/api/test_startup_logging.py`
  - `backend/src/sextante/ingestion/` (motivo de recusa do XLSX), `platform/user_messages.py`, exemplos de docstrings em `platform/` e `export/domain/`
  - `docs/00-decisoes-e-lacunas.md` (§3.6), `docs/04-padroes-de-codigo.md` (§3.6 e comandos), ticket 12
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 290 testes; nenhum nome de empresa, NIF, número de documento ou descrição das amostras nos testes nem nos exemplos do código; `mypy`, `ruff`, 8 contratos do `import-linter`.

**Réplicas.** As réplicas dos tickets 02 a 10 usavam valores das amostras reais: nomes de fornecedores e clientes, NIFs, números de factura, descrições e moradas. Passam a valores inventados, com a mesma estrutura. A fixture `taag_air_ticket_to_amt` passa a `air_ticket_to_amt`. Os valores antigos continuam no histórico, por decisão do responsável.

**XLSX.** É recusado com `unsupported_document_type`, porque REQ-ING-001 manda um XLSX para a recusa de REQ-ING-009. O motivo `extractor_not_configured` deixou de ter uso e foi retirado.

**Conjunto dourado em 04.** O padrão de código dizia que `make golden` imprime precisão por aba, distribuição de confiança e taxa de sinalização. Passa a dizer o que §3.18 decidiu: as etapas determinísticas, sem o modelo. As medidas que precisam do modelo ficam para o comando manual, publicadas só depois da confirmação da AMT.

### CHG-0033 · Histórico sem Co-Authored-By e hashes actualizados

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0032
- **Estado:** activa
- **Requisitos:** nenhum
- **Commit:** `8124617`
- **Migração:** nenhuma
- **Ficheiros:** `CHANGELOG.md`, tickets 01 e 02 (hashes citados)
- **Reversibilidade:** não
- **Reversão:** a reescrita do histórico não se desfaz por um commit. As mensagens antigas só existem enquanto o ramo de segurança `backup/before-strip-coauthor` e `refs/original` não forem apagados.
- **Verificação:** 35 commits reescritos com `git filter-branch --msg-filter`; nenhum tem a linha `Co-Authored-By`; a árvore final é idêntica à de antes (`git diff` vazio); os assuntos dos commits antigos e novos coincidem um a um.

**Pedido do responsável.** Retirar a linha `Co-Authored-By` de todos os commits e nunca mais a acrescentar. A reescrita mudou todos os hashes. Os campos `Commit` das entradas, e os hashes citados nos tickets 01 e 02, foram actualizados para os novos, o que a regra 4 permite. O texto de CHG-0032 cita o hash novo do commit de CHG-0030.

### CHG-0032 · Correcções da revisão dos tickets 12 e 13

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0031
- **Estado:** activa
- **Requisitos:** REQ-ING-002, REQ-ING-003, NFR-TST-001, D-3.18, SEC-15, SEC-20
- **Commit:** `4fcd0e1`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/ingestion/` (extractor, leitor do layout, `missing_fields`, contratos), `worker.py`, `platform/settings.py`
  - `backend/tests/golden/runner.py` e `expected_results.yaml` (movidos de `src/sextante/golden_set.py` e `config/golden_expected.yaml`); `backend/scripts/golden.py` retirado; `backend/Makefile`
  - testes: `tests/fixtures/synthetic_pdf.py`, `tests/extraction/`, `tests/api/test_pdf_ingestion.py`, `tests/golden/`
  - `README.md`, `config/.env.example`, tickets 12 e 13
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 290 testes. O teste da página digitalizada falha com a regra antiga, a da média. `make golden` sobre as 12 amostras, localmente: 12 sem divergências. `mypy`, `ruff`, 8 contratos do `import-linter`, `make licenses` (inclui `pdfplumber`, MIT pelo classificador do pacote, que não preenche o campo `License`), funções com 20 linhas ou menos.

**Excertos de amostras.** As réplicas sintéticas de CHG-0030 traziam valores tirados das amostras reais: números de bilhete, de contentor e de processo, NIFs, nomes de clientes e descrições. Foram substituídos por valores inventados, que mantêm as particularidades: quebra a meio da palavra, quebra num espaço, número com espaço, nome longo na faixa de topo. Os valores antigos continuam no histórico do commit `a444f0a`.

**Texto por página.** O mínimo de caracteres vale para cada página, e não para a média do ficheiro. Uma página digitalizada no meio de páginas nativas recusa o PDF.

**Campos ausentes.** Além do log, ficam na auditoria da factura (`extraction_fields_missing`), só pelo nome. A função que os lista é partilhada pelo extractor, pelo trabalhador e pelo conjunto dourado.

**Conjunto dourado.**
- Passa para `backend/tests/golden/`, como 02 §2.4 o coloca; `make golden` corre `python -m tests.golden.runner`.
- A variável é `SEXTANTE_GOLDEN_SAMPLES_PATH`, como 02 a documenta.
- Mede também os campos que a extracção não encontrou, pelo nome.
- As variáveis são validadas como as da aplicação: um valor inválido, incluindo um mínimo de texto igual a 0, termina com código 2 e o nome da variável.

**Robustez.** Os caracteres da descrição são indexados por altura uma só vez, em vez de percorridos em cada linha da tabela. Um PDF ilegível tem teste do motivo exacto.

### CHG-0031 · Conjunto dourado sem o modelo

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0030
- **Estado:** activa
- **Requisitos:** NFR-TST-001, D-3.18, L-02, SEC-15
- **Commit:** `78e01e1`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/golden_set.py` (novo), `backend/scripts/golden.py`, `backend/Makefile`
  - `config/golden_expected.yaml` (novo), `config/.env.example`
  - testes: `tests/golden/test_golden_set.py` (novo)
  - `README.md`, ticket 13
- **Reversibilidade:** total
- **Reversão:** reverter o commit. `make golden` volta a dizer que não está implementado.
- **Verificação:** 285 testes, incluindo o conjunto dourado sobre amostras sintéticas, uma divergência que falha com o nome do campo, a mensagem sem a pasta das amostras, e um relatório sem texto de amostra. Corrido localmente sobre as 12 amostras: 12 sem divergências. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Medição.** `make golden` lê as amostras de `SEXTANTE_GOLDEN_SAMPLES_DIR` e mede, sem chamar o modelo, extracção, entidade, aba de destino, número e tipos de linha, e recusas. Falha quando alguma diverge. Sem a variável, termina com uma mensagem clara.

**Resultados esperados.** `config/golden_expected.yaml` tem a proposta do ticket, por confirmar pela AMT. As linhas são identificadas pela posição, e não pela descrição, para que nenhum excerto de amostra entre no repositório. O relatório tem só identificadores, nomes de campo e valores de conjuntos fechados.

**Por fazer.** O comando manual que mede os códigos de item com o modelo real depende do adaptador do ticket 11.

### CHG-0030 · Extracção de PDF nativo no modelo das amostras

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0029
- **Estado:** activa
- **Requisitos:** REQ-ING-001, REQ-ING-002, REQ-ING-003, REQ-ING-004, REQ-ING-005, REQ-ING-006, REQ-ING-008, REQ-ING-009, D-3.6, L-01, L-14, SEC-16
- **Commit:** `a444f0a`
- **Migração:** nenhuma
- **Dependência nova:** `pdfplumber` 0.11 (MIT), com `pdfminer.six` (MIT), `pypdfium2` (BSD-3-Clause ou Apache-2.0) e `Pillow` (MIT-CMU). `make licenses` passa.
- **Ficheiros:**
  - `backend/src/sextante/ingestion/infrastructure/pdf_invoice_extractor.py` e `model_invoice_layout.py` (novos); `unconfigured_extractor.py` retirado
  - `backend/src/sextante/main.py`, `platform/settings.py` (`pdf_min_chars_per_page`), `platform/limits.py` (`MAX_PDF_PAGES`), `platform/user_messages.py`, `ingestion/domain/model.py`
  - `backend/pyproject.toml`
  - testes: `tests/extraction/test_pdf_extractor.py`, `tests/api/test_pdf_ingestion.py`, `tests/fixtures/synthetic_pdf.py` (novos)
  - `README.md`, `config/.env.example`, ticket 12
- **Reversibilidade:** total
- **Reversão:** reverter o commit. O extractor volta a recusar todo o documento com `extractor_not_configured`.
- **Verificação:** 285 testes. As réplicas sintéticas reproduzem as quatro particularidades; extracção pela porta `InvoiceExtractor` e ponta a ponta pela API; recusas de digitalizado, de documento fora do modelo e de PDF ilegível. As 12 amostras, lidas localmente fora do repositório, dão o que a proposta do conjunto dourado espera. `mypy`, `ruff`, 8 contratos do `import-linter`, licenças, funções com 20 linhas ou menos.

**Extracção.** O layout é lido pelas coordenadas das palavras. O fornecedor é a letra maior da faixa de topo, mesmo quando corre por baixo de "INVOICE / FACTURA". FROM e BILL TO separam-se pelo x do rótulo "BILL TO". As linhas "c/o" e "a/c" ficam como "ao cuidado de", e cada bloco tem o seu NIF. O número da factura pode ter espaço ("FT 2026/0001").

**Linhas.** Cada valor vai para a coluna cujo título termina mais perto, porque os valores estão alinhados à direita. Uma linha de continuação junta-se pelos caracteres em bruto: com espaço quando a quebra caiu num espaço, sem espaço quando caiu a meio da palavra. Os valores são lidos no formato `1,206.00`, e o IVA em `14%`. Subtotal, IVA e total ficam como linhas de resumo, mesmo com o total colado ao rótulo.

**Recusas.** Um PDF com menos caracteres por página do que `SEXTANTE_PDF_MIN_CHARS_PER_PAGE` (100 por omissão) é `pdf_without_text_layer`. Um PDF sem os rótulos do modelo, com mais de 20 páginas, ou ilegível, é `unsupported_document_type`. XLSX continua por ler nesta versão (D-3.6) e é recusado com `extractor_not_configured`, agora com um texto que o diz.

**Campos ausentes.** Ficam vazios e são registados no log só pelo nome (`extraction_fields_missing`), nunca com texto da factura.

### CHG-0029 · Saída da resolução humana e do duplicado provável

- **Data:** 2026-11-18
- **Tipo:** improve
- **Pai:** CHG-0028
- **Estado:** activa
- **Requisitos:** REQ-ENT-006, REQ-ING-011, REQ-REV-006, REQ-EXP-004
- **Commit:** `58f99b5`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/matching/domain/entity_check.py` e contratos (`exact_entity_match_label` com o motivo, `entity_notes`)
  - `backend/src/sextante/worker.py` (motivo `reviewer_resolution` no cabeçalho)
  - `backend/src/sextante/ingestion/` (motivo da entidade e factura anterior nas leituras)
  - `backend/src/sextante/export/application/build_job_export.py`, `review/application/list_job_results.py`, `platform/user_messages.py`
  - testes: `test_entity_resolution.py`, `test_possible_duplicate.py`
  - `docs/00-decisoes-e-lacunas.md` (§3.21), tickets 09 e 10
- **Reversibilidade:** total
- **Reversão:** reverter o commit. As facturas resolvidas antes desta alteração têm motivo vazio no cabeçalho e continuam a mostrar `YES`.
- **Verificação:** 262 testes, incluindo `Exact_Entity_Match` `NO` com a nota do revisor nos resultados e na exportação, e a nota do duplicado com o ficheiro e a data da anterior; `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Resolução humana.** Uma resolução `MATCH` grava no cabeçalho o motivo `reviewer_resolution`. `Exact_Entity_Match` fica `NO`, porque a verificação não encontrou correspondência exacta, e as linhas levam a nota "Entidade confirmada pelo revisor.".

**Duplicado provável.** Na exportação, a sinalização diz "Possível duplicado de <ficheiro>, carregada a <dd-mm-aaaa>.", com o ficheiro e a data da factura anterior.

### CHG-0028 · Correcções da revisão dos tickets 09 e 10

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0027
- **Estado:** activa
- **Requisitos:** REQ-REV-006, REQ-ING-011, REQ-CNF-001, REQ-AUD-002, SEC-19
- **Commit:** `eedb6dd`
- **Migração:** `0007` alterada antes de sair deste ramo: índice parcial também com condição para PostgreSQL, e descida sem trabalho manual
- **Ficheiros:**
  - `backend/src/sextante/platform/insert_if_absent.py` (novo), `idempotency.py`
  - `backend/src/sextante/ingestion/` (porta da resolução, mensagens de erro, duplicado gravado uma vez)
  - `backend/src/sextante/worker.py`, `matching/infrastructure/tables.py`, migração 0007
  - testes: `test_entity_resolution.py`, `test_possible_duplicate.py`
  - spec (tipo de auditoria `possible_duplicate_detected`), ticket 14
- **Reversibilidade:** total
- **Reversão:** reverter o commit. A migração 0007 volta à forma de CHG-0027.
- **Verificação:** 261 testes. O teste da auditoria única falha sem a correcção. A descida da 0007 é testada com codificações substituídas presentes. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**SQL portável.** A reserva da chave de idempotência e a gravação da resolução deixam de usar `INSERT OR IGNORE`, que só existe em SQLite (02 §5), e passam a `INSERT ... SELECT ... WHERE NOT EXISTS`. O índice único parcial de `encoded_line` declara a condição para SQLite e para PostgreSQL.

**Migração 0007.** A descida apaga primeiro as codificações substituídas, e as suas sinalizações e revisões, porque a restrição da 0006 só admite uma por linha. O histórico fica em `audit_event`. A Reversão de CHG-0027 deixa de exigir trabalho manual.

**Duplicado.** `possible_duplicate_detected` é gravado uma só vez, mesmo quando a factura é codificada de novo depois de uma resolução. O tipo fica declarado na spec.

**Resolução.** Uma resolução repetida e uma factura não ambígua têm mensagens de erro distintas, cada uma com a condição que falhou. A resolução tem uma porta própria, que estende a do reprocessamento. Um teste prova que uma factura resolvida chega a `HIGH` sem sinalização.

**Pendente para o ticket 14.** `lexical_score` não está ligado a uma codificação. Recodificar uma linha que já tem scores falharia na chave primária. Hoje não acontece, porque a factura ambígua não grava scores.

### CHG-0027 · Resolução de entidade e duplicado provável

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0026
- **Estado:** activa
- **Requisitos:** REQ-REV-006, REQ-ING-011, REQ-REV-004, REQ-AUD-002, SEC-08, SEC-19, D-3.10, D-3.15
- **Commit:** `17bcc08`
- **Migração:** `0007_entity_resolution_and_duplicates` (tabela `entity_resolution`; `encoded_line.superseded_at` com índice único parcial no lugar da restrição única; `invoice_header.supplier_key` e `possible_duplicate_of`, com índice não único sobre fornecedor e número)
- **Ficheiros:**
  - `backend/src/sextante/ingestion/` (caso de uso `ResolveEntity`, rota, repositório, tabelas)
  - `backend/src/sextante/matching/` (codificações substituídas, sinalização da factura inteira)
  - `backend/src/sextante/worker.py`, `main.py`
  - `backend/src/sextante/platform/supplier_key.py` (novo, partilhado com a exportação), `limits.py`, `user_messages.py`
  - `backend/src/sextante/review/` (resultados com `possible_duplicate_of`)
  - testes: `test_entity_resolution.py`, `test_possible_duplicate.py` (novos), harness e fixtures
  - `README.md`, tickets 09 e 10
- **Reversibilidade:** parcial
- **Reversão:** reverter o commit e descer a migração para `0006`. A descida repõe a restrição única em `encoded_line`, e falha se houver codificações substituídas: essas têm de ser retiradas à mão primeiro. As resoluções gravadas perdem-se com a tabela; os eventos `entity_resolved` e `possible_duplicate_detected` ficam em `audit_event`.
- **Verificação:** 258 testes, incluindo resolução `MATCH` para OUTLAYS e `NO_MATCH` para OUTLAYSP com `O00999`, auditoria com o veredicto anterior e o novo, codificação anterior guardada como substituída, recusa de factura não ambígua, resolução repetida que codifica uma só vez, contrato da nota, lista de exclusão inalterada, duplicado sinalizado com referência, mesmo digest sem sinalização, factura sem número e outro fornecedor com o mesmo número; migração verificada a subir, descer e subir; `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Resolução de entidade.** `POST /api/invoices/{id}/entity-resolution` aceita `MATCH` ou `NO_MATCH` e uma nota obrigatória de 500 caracteres no máximo, com `Idempotency-Key`. Só uma factura `AMBIGUOUS` por resolver é aceite. A resolução fica em `entity_resolution`, gera `entity_resolved` com o autor configurado e põe a factura na fila. O trabalhador usa a resolução em vez da verificação, e as linhas seguem a regra normal de confiança. A lista de exclusão não muda.

**Codificação substituída.** As linhas da factura ambígua já tinham um registo sem código. A nova codificação marca-o como substituído (`superseded_at`) em vez de o sobrescrever; leituras, revisão, candidatos e exportação mostram só a codificação em vigor.

**Duplicado provável.** Uma factura com o mesmo fornecedor (NIF, ou nome normalizado) e o mesmo número de outra carregada antes, com outro digest, é codificada e todas as linhas ficam com `possible_duplicate`. Os resultados indicam a anterior em `possible_duplicate_of`. Sem número nunca é duplicado; o mesmo ficheiro continua a devolver o trabalho existente.

### CHG-0026 · Isenção do carregamento e reprocessamento só de falhas

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0025
- **Estado:** activa
- **Requisitos:** SEC-19, NFR-REL-002, REQ-ING-007
- **Commit:** `7844846`
- **Migração:** nenhuma
- **Ficheiros:**
  - `docs/00-decisoes-e-lacunas.md` (§3.19, §3.20)
  - `docs/03-seguranca.md` (SEC-19), `docs/02-arquitectura.md` (§6)
  - `.scratch/nucleo-codificacao/issues/14-recodificacao-com-historico.md` (novo), tickets 07 e 08
- **Reversibilidade:** total
- **Reversão:** reverter o commit. O código não muda.
- **Verificação:** decisões tomadas pelo responsável em 18-11-2026; o código já se comporta assim (CHG-0023, CHG-0024).

**Carregamento.** Fica isento de `Idempotency-Key`, por ser idempotente pelo digest do conteúdo. A isenção fica escrita em SEC-19 e na arquitectura, e não se estende a outras escritas.

**Reprocessamento.** Nesta versão aceita só facturas com falha. Recodificar uma factura já codificada, com histórico, passa a ticket próprio (14), bloqueado pelo ticket 11.

### CHG-0025 · Correcções da revisão dos tickets 07 e 08

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0024
- **Estado:** activa
- **Requisitos:** SEC-19, REQ-REV-003, REQ-REV-004, REQ-AUD-004
- **Commit:** `47e4c6e`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/platform/idempotency.py`, `idempotent_route.py`, `http_params.py` (novo), `limits.py`
  - `backend/src/sextante/review/` (auditoria, docstrings, mensagens de erro, progresso com tokens por factura)
  - `backend/src/sextante/matching/` (tokens por factura), rotas de `ingestion` e `export`, `main.py`
  - testes: `test_idempotency.py` (novo), `test_line_review.py`, `test_worker_resilience.py`, contratos
  - `README.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit. O esquema não mudou.
- **Verificação:** 243 testes. O teste de concorrência falha contra uma versão que verifica e depois escreve (`IntegrityError`) e passa com a reserva como primeira escrita. `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Idempotência.** A reserva da chave é a primeira escrita da transacção (`INSERT OR IGNORE`). Um pedido simultâneo com a mesma chave espera pelo primeiro e recebe a resposta guardada, nunca um 500. A purga das respostas com mais de 24 horas passa para uma tarefa periódica, de hora a hora, como SEC-19 pede, em vez de correr dentro de cada escrita. O código de estado guardado é o que se devolve na repetição. Um pedido recusado não guarda nada, e a mesma chave pode ser reenviada. Os erros de chave e de item fora da aba têm estado explícito.

**Auditoria.** `line_accepted` e `line_corrected` registam o valor anterior e o novo do item, do estado de revisão e da nota (REQ-REV-004).

**Tokens.** `GET /api/jobs/{id}` mostra os tokens de cada factura, além do total (ticket 07).

**Normas.** Exemplos e `Raises` por erro nas docstrings da revisão. Mensagens de erro com o valor e a forma esperada. O limite da nota vai para `platform/limits.py`. O parâmetro de identificador fica num só sítio, o que também aplica o padrão ao `job_id` dos resultados, que não o tinha. Os contratos de entrada da revisão aparam espaços (SEC-08).

### CHG-0024 · Revisão de linhas

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0023
- **Estado:** activa
- **Requisitos:** REQ-REV-001, REQ-REV-002, REQ-REV-003, REQ-REV-004, REQ-REV-005, REQ-REV-007, REQ-EXP-004, SEC-08, SEC-18, SEC-19
- **Commit:** `040a42c`
- **Migração:** `0006_review_and_idempotency` (tabelas `line_review` e `idempotency_record`)
- **Ficheiros:**
  - `backend/src/sextante/review/` (domínio, casos de uso, repositório, rotas e contratos)
  - `backend/src/sextante/platform/idempotency.py`, `idempotent_route.py`, `audit.py`, `settings.py`, `user_messages.py`
  - `backend/src/sextante/matching/` (leitura de uma linha codificada e dos candidatos)
  - `backend/src/sextante/ingestion/` (linhas por factura, pertença de uma linha, reprocessamento na transacção da chave)
  - `backend/src/sextante/export/application/build_job_export.py`, `main.py`
  - `backend/migrations/versions/0006_review_and_idempotency.py`
  - `README.md`, `config/.env.example`, tickets 06 e 08
- **Reversibilidade:** parcial
- **Reversão:** reverter o commit e descer a migração para `0005`. As revisões gravadas em `line_review` perdem-se com a tabela; os eventos `line_accepted` e `line_corrected` ficam em `audit_event`, que é só de inserção.
- **Verificação:** 240 testes, incluindo correcção na aba, recusas (outra aba, código mal formado, campos de controlo, nota longa, linha sem aba), aceitação só de linha pendente, repetição e reutilização da chave, filtros, candidatos e reflexo na exportação; `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Revisão.** `PATCH /api/encoded-lines/{id}` corrige o código com um item da aba de destino da linha, validado no servidor. `POST /api/encoded-lines/{id}/accept` passa uma linha `pending` a `accepted`. As duas aceitam uma nota de 500 caracteres no máximo, recusam campos extra e são recusadas para uma linha sem aba de destino.

**Registo.** O estado de revisão fica em `line_review`, à parte de `encoded_line`, que nunca é sobrescrito. Cada acção gera `line_accepted` ou `line_corrected` em `audit_event`, com o valor anterior, o novo, o autor (`SEXTANTE_REVIEWER_ID`, nova variável obrigatória) e o momento.

**Idempotência.** `POST` e `PATCH` de revisão e o reprocessamento exigem `Idempotency-Key`. A chave é registada na mesma transacção da acção; a mesma chave repete a resposta, e com outro corpo é recusada. As respostas guardadas duram 24 horas. O carregamento fica isento: o digest do conteúdo já o torna idempotente.

**Resultados e exportação.** Os resultados mostram os valores em vigor e filtram por confiança, aba, sinalização e factura, antes da paginação. A exportação usa os mesmos valores, e a nota de revisão entra em `Notes_or_Flags`.

### CHG-0023 · Trabalhador robusto e reprocessamento

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0022
- **Estado:** activa
- **Requisitos:** REQ-PLT-001, REQ-PLT-002, REQ-PLT-003, REQ-AUD-004, NFR-REL-001, NFR-REL-002, L-12
- **Commit:** `14c0b15`
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/platform/retry.py`
  - `backend/src/sextante/ingestion/application/reprocess_invoice.py`, repositório e rotas
  - `backend/src/sextante/matching/` (`ItemClassifierUnavailableError`, `TokenUsageReader`)
  - `backend/src/sextante/review/application/read_job_progress.py`
  - `backend/src/sextante/worker.py`, `main.py`, `platform/settings.py`
  - `README.md`, `config/.env.example`
- **Reversibilidade:** total
- **Reversão:** reverter o commit. O esquema não mudou. As facturas reabertas por um reprocessamento ficam no estado em que estiverem.
- **Verificação:** 217 testes, incluindo repetições com espera registada, falha permanente sem repetição, reprocessamento sem segunda extracção e tokens por trabalho; `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.

**Repetições.** Só o modelo indisponível (`ItemClassifierUnavailableError`) é repetido, com recuo exponencial (1 s, 2 s, …). O número de tentativas é configurável, 3 por omissão. Qualquer outra falha é final, e uma resposta inválida nunca é repetida.

**Falhas.** Uma factura que falha fica `failed`, com o motivo, e o trabalho continua.

**Reprocessamento.** `POST /api/invoices/{id}/reprocess` volta a pôr na fila uma factura `failed`. O trabalho é reaberto e a factura é codificada a partir do texto guardado, sem nova extracção. Pedir duas vezes põe-na na fila uma só vez.

**Estado do trabalho.** `GET /api/jobs/{id}` mostra as facturas por estado e no total, e os tokens gastos.

### CHG-0022 · Correcções da revisão dos tickets 05 e 06

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0021
- **Estado:** activa
- **Requisitos:** REQ-ING-006, REQ-EXP-003, REQ-EXP-006, REQ-EXP-007, SEC-17, D-3.17
- **Commit:** 9e2d8e0
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/ingestion/domain/line_type.py`
  - `backend/src/sextante/export/` (porta `SpreadsheetWriter`, caso de uso `ExportJob`)
  - `backend/src/sextante/platform/text_normalization.py` (`digits_only`)
  - `backend/src/sextante/matching/domain/entity_check.py` (`exact_entity_match_label`)
  - `backend/pyproject.toml` (contrato que proíbe `export.api` de chegar à infraestrutura)
  - os tickets 05 e 06
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:**
  - Feito:
    - 211 testes, incluindo 25 casos da classificação de linhas;
    - a neutralização nas nove colunas;
    - a cobertura das mensagens de recusa;
    - `mypy`, `ruff`, 8 contratos do `import-linter`, funções com 20 linhas ou menos.
  - Não verificado: o reflexo de uma correcção na exportação, que espera pelo ticket 08.

Resolve os achados da revisão dos tickets 05 e 06.

**Spec:**

- **Classificação das linhas.** Uma linha só é IVA, ou desconto, quando nomeia o IVA ou o desconto e todas as suas palavras pertencem a esse vocabulário. Passam a ser IVA "Valor do IVA", "14% IVA" e "I.V.A.". Passam a ser descontos "Descontos" e "Desc.". "Vat handling fee" e "(isento de IVA)" ficam como serviços.
- **`Invoice_ID`.** Um número só com espaços passa a dar lugar ao digest.
- **Deferições declaradas no ticket 06.** O reflexo de uma correcção espera pelo ticket 08, e os identificadores são calculados na exportação.

**Padrões:**

- A rota de exportação passa a usar só a camada de aplicação, que escreve através de uma porta. O contrato do `import-linter` passa a cobri-la.
- Os dígitos do NIF e o `Exact_Entity_Match` passam a viver num só sítio cada.
- As mensagens de recusa saem de um mapa com valor por omissão, testado contra todos os motivos.
- O tipo de linha, a nota e o estado da factura passam a ter tipos com nome.
- O JSON da entidade passa a ser lido uma só vez.

### CHG-0021 · Exportação em CSV e XLSX

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0020
- **Estado:** activa
- **Requisitos:** REQ-EXP-001 a REQ-EXP-007, SEC-16, SEC-17, R6, L-13
- **Commit:** c689698
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/export/` (módulo novo)
  - `backend/src/sextante/ingestion/` (leitor publicado `InvoiceExportReader`)
  - `backend/src/sextante/platform/settings.py`, `limits.py`, `user_messages.py`
  - `backend/src/sextante/main.py`, `backend/pyproject.toml` (contrato de camadas do `export`)
  - `README.md`, `config/.env.example`
- **Reversibilidade:** total
- **Reversão:** reverter o commit. O esquema não mudou.
- **Verificação:**
  - Feito:
    - 195 testes, incluindo a neutralização em CSV e XLSX, o separador `;` com aspas, e a exportação depois de reiniciar a aplicação;
    - `mypy`, `ruff`, 8 contratos do `import-linter`;
    - exportação no servidor real.
  - Não verificado: abrir os ficheiros no Excel em configuração portuguesa.

`GET /api/exports/{job_id}?format=csv|xlsx` exporta as nove colunas do enunciado, a partir do estado persistido:

- **Neutralização:** aplica-se a todas as células, num só ponto (SEC-17). O CSV sai em UTF-8 com BOM, escrito com `csv.writer`, e o separador é configurável. No XLSX, cada célula leva tipo texto explícito.
- **`Invoice_ID`:** combina o NIF do fornecedor, ou o seu nome normalizado, com o número da factura, ou com um digest curto quando falta o número.
- **Facturas ambíguas:** saem com a aba de destino vazia e o motivo.
- **Documentos recusados ou falhados:** saem numa linha `LOW` com o motivo em português.
- **`Notes_or_Flags`:** junta as sinalizações, as notas de tipo de linha e as linhas "ao cuidado de".
- **Entrega:** a resposta é sempre um anexo com `nosniff`.

### CHG-0020 · Tipos de linha

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0019
- **Estado:** activa
- **Requisitos:** REQ-ING-004, REQ-ING-006, D-3.17, L-06, L-16
- **Commit:** c16f64c
- **Migração:** `0005`, a partir de `0004`
- **Ficheiros:**
  - `backend/src/sextante/ingestion/domain/line_type.py`
  - `backend/src/sextante/ingestion/infrastructure/` (tabela e repositório)
  - `backend/src/sextante/matching/domain/line_decision.py` (`LineNote`, `non_service_line_decision`)
  - `backend/src/sextante/matching/application/encode_invoice.py`, `worker.py`, `review/`
  - `backend/migrations/versions/0005_line_types.py`
- **Reversibilidade:** total
- **Reversão:**
  1. Correr `alembic downgrade 0004`, que apaga `invoice_line.line_type` e `encoded_line.note`.
  2. Reverter o commit.

  Os eventos de auditoria `summary_rows_extracted` ficam.
- **Verificação:** 171 testes, incluindo 12 casos de tabela da classificação; `mypy`, `ruff`, 7 contratos do `import-linter`, funções com 20 linhas ou menos.

Cada linha é classificada como serviço, IVA ou desconto. O IVA só é reconhecido quando a descrição começa por "IVA", "VAT" ou "Imposto sobre o Valor Acrescentado". Assim ficam como serviços "Taxa de pilotagem", os direitos aduaneiros e uma descrição que menciona "(isento de IVA)".

Só as linhas de serviço vão ao modelo, e não há chamada se não houver nenhuma. As linhas de IVA e de desconto ficam sem código, com `HIGH`, aceites, sem sinalização e com uma nota do tipo. As linhas de resumo ficam registadas uma vez, na auditoria da factura. A percentagem de IVA de cada linha fica guardada como atributo.

### CHG-0019 · Correcções da revisão dos tickets 03 e 04

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0018
- **Estado:** activa
- **Requisitos:** REQ-ENT-003, REQ-ENT-007, REQ-CNF-002, REQ-PLT-002, NFR-REL-001, D-3.8, D-3.15, SEC-18
- **Commit:** 09d6f77
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/matching/domain/entity_check.py`, `line_decision.py`
  - `backend/src/sextante/matching/application/encode_invoice.py`, `worker.py`, `main.py`
  - `backend/src/sextante/ingestion/` (registo `EntityCheckRecord`)
  - `backend/src/sextante/review/`
  - `README.md`, e os testes
- **Reversibilidade:** total
- **Reversão:** reverter o commit. O esquema não mudou.
- **Verificação:** 154 testes, `mypy`, `ruff`, 7 contratos do `import-linter`, funções com 20 linhas ou menos.

Resolve os achados da revisão dos tickets 03 e 04.

**Spec:**

- Os limiares de `HIGH` passam a estritos ("acima", D-3.8). No limite exacto, a linha é `MEDIUM` e fica sinalizada como conflito.
- Um NIF sem dígitos, como "N/D", conta como não extraído e não veta a AMT.
- O arranque recusa uma lista de exclusão que contenha a própria AMT.
- O veredicto da entidade e as linhas passam a gravar-se na mesma transacção.

**Padrões:**

- `AmbiguityReason` sai: a verificação de entidade passa a usar `FlagReason`.
- A lista de exclusão é um objecto de valor, normalizado uma só vez.
- A decisão das linhas sem código passa a viver na regra de confiança.
- Os dados de referência, o registo do veredicto e a projecção da resposta passam a ter tipos com nome.
- As mensagens de erro passam a indicar a forma esperada.

### CHG-0018 · Confiança, recurso e sinalização

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0017
- **Estado:** activa
- **Requisitos:** REQ-CNF-001 a REQ-CNF-005, REQ-MAP-007 a REQ-MAP-009, REQ-MAP-013, REQ-REV-005, D-3.8, D-3.16, L-08, L-13
- **Commit:** 0927ffe
- **Migração:** `0004`, a partir de `0003`
- **Ficheiros:**
  - `backend/src/sextante/matching/domain/line_decision.py`, `scoring.py`
  - `backend/src/sextante/matching/application/encode_invoice.py`, `records.py`
  - `backend/src/sextante/matching/infrastructure/` (tabelas e repositório)
  - `backend/src/sextante/review/`, `worker.py`, `main.py`
  - `backend/src/sextante/platform/settings.py`, `user_messages.py`
  - `backend/migrations/versions/0004_confidence_and_flags.py`
  - `README.md`, `config/.env.example`
- **Reversibilidade:** parcial
- **Reversão:**
  1. Salvaguardar `sextante.db`.
  2. Apagar as linhas de `encoded_line` sem aba de destino: `DELETE FROM encoded_line WHERE target_sheet IS NULL`, depois de apagar as suas linhas de `line_flag`.
  3. Correr `alembic downgrade 0003`.
  4. Reverter o commit.

  Os eventos de auditoria `line_not_coded` ficam: a auditoria é só de inserção.
- **Verificação:**
  - Feito: 146 testes, incluindo 13 casos de tabela da regra de confiança com os limites exactos dos limiares; `mypy`, `ruff`, 7 contratos do `import-linter`, funções com 20 linhas ou menos.
  - Não verificado: calibração dos limiares, que espera pelo conjunto dourado (L-02).

A confiança é calculada pela regra de D-3.8:

- `HIGH` só quando o item escolhido é o topo lexical, com score de pelo menos 85 e pelo menos 10 de distância ao segundo;
- `MEDIUM` para os restantes itens válidos;
- `LOW` para o recurso, para a ausência de item, para uma resposta inválida e para um item genérico.

O `O00999` é atribuído em código, só em OUTLAYSP. Em OUTLAYS a linha fica vazia e sinalizada. Cada sinalização traz um motivo de um conjunto fechado, com texto em português. As linhas de facturas ambíguas ficam registadas com `LOW`, sem aba de destino e com o motivo da entidade, o que fecha o critério que a CHG-0017 deixou pendente. A auditoria regista a confiança, a regra que a produziu e as sinalizações.

### CHG-0017 · Verificação de entidade e encaminhamento para OUTLAYSP

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0016
- **Estado:** activa
- **Requisitos:** REQ-ENT-001 a REQ-ENT-008, REQ-MAP-001, D-3.15, L-04, L-13
- **Commit:** 2e9a846
- **Migração:** `0003`, a partir de `0002`
- **Ficheiros:**
  - `backend/src/sextante/matching/domain/entity_check.py`, `routing.py`
  - `backend/src/sextante/matching/infrastructure/denylist_file.py`
  - `backend/src/sextante/platform/text_normalization.py` (`fold_for_matching`)
  - `backend/src/sextante/worker.py`, `main.py`, `review/`
  - `backend/migrations/versions/0003_entity_check.py`
  - `config/entity_denylist.yaml`, novo e vazio; `config/.env.example`
  - dependência nova: PyYAML (MIT)
- **Reversibilidade:** total
- **Reversão:**
  1. Correr `alembic downgrade 0002`, que apaga as colunas `entity_verdict` e `entity_reason` e o seu conteúdo.
  2. Reverter o commit.
  3. Retirar `SEXTANTE_ENTITY_DENYLIST_PATH` do `.env`.
- **Verificação:**
  - Feito: 124 testes, incluindo 18 casos de tabela da regra de entidade; `mypy`, `ruff`, 7 contratos do `import-linter`, funções com 20 linhas ou menos.
  - Pendente: o critério "linhas de factura ambígua com `LOW` e sinalizadas" depende da confiança e das sinalizações do ticket 04 (CHG-0018).

A verificação de entidade aplica as sete regras de D-3.15, pela ordem, sem modelo:

- a lista de exclusão primeiro;
- o veto pelo NIF;
- a igualdade do nome normalizado;
- o limiar baixo de `token_sort_ratio`, a 60 e provisório.

Uma não correspondência é codificada contra OUTLAYSP. Uma entidade ambígua fica por codificar, com o motivo registado no cabeçalho, e nunca chega ao modelo. Os resultados mostram a entidade detectada e o `Exact_Entity_Match`. A lista de exclusão vem de configuração, com a estrutura definida e sem conteúdo (L-04).

### CHG-0016 · Diagramas regenerados com o desenho actual

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0015
- **Estado:** activa
- **Requisitos:** D-3.15, D-3.16, D-3.17, D-3.18
- **Commit:** df760ad
- **Migração:** nenhuma
- **Ficheiros:**
  - `scripts/gen_diagrams.py`
  - `docs/diagramas/*.excalidraw`
  - `assets/fluxo-codificacao.svg` e `assets/arquitectura-modulos.svg`, novos
  - `assets/architecture.png` e `assets/invoice-encoding-flow.png`, removidos
  - `docs/02-arquitectura.md` (§3)
  - `docs/agents/triage-labels.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit. Os PNG removidos voltam com ele.
- **Verificação:**
  - Feito:
    - script corrido;
    - os dois SVG abertos no Chrome sem interface e inspeccionados;
    - `graphify update` sem arestas de um nó para si próprio.
  - Não verificado: abrir os `.excalidraw` regenerados em excalidraw.com.

Os dois diagramas mostravam o desenho anterior: o desempate de entidade pelo Claude e as portas `EntityTiebreaker` e `CandidateRetriever`. Foram corrigidos no script e regenerados. Agora o Claude aparece num só passo, a entidade ambígua vai a um revisor, e as portas são as actuais.

Os PNG tinham sido exportados à mão, o que o `CLAUDE.md` não permite. Foram substituídos por SVG escritos pelo mesmo script, a partir dos mesmos elementos.

O título de `triage-labels.md` passou a «Triage label vocabulary». O título anterior gerava no grafo o mesmo identificador que o nome do ficheiro, e daí a aresta que ligava um nó a si próprio.

### CHG-0015 · Skill do graphify no projecto e correcção da CHG-0014

- **Data:** 2026-11-18
- **Tipo:** infra
- **Pai:** CHG-0014
- **Estado:** activa
- **Requisitos:** nenhum
- **Commit:** 3f4ff0f
- **Migração:** nenhuma
- **Ficheiros:**
  - `.claude/skills/graphify/`
  - `.claude/settings.json`
  - `.claude/CLAUDE.md`
  - `.gitattributes`, que a CHG-0014 criou mas não listou
- **Reversibilidade:** total
- **Reversão:**
  1. Correr `graphify claude uninstall`, que retira os hooks e a secção do `CLAUDE.md`.
  2. Apagar `.claude/skills/graphify/` e `.claude/CLAUDE.md`.
  3. Reverter o commit.
- **Verificação:**
  - Feito: `/graphify . --update` corrido sobre os documentos e as duas imagens de `assets/`, com o resultado em `graphify-out/` (fora do repositório).
  - Não verificado: os hooks não foram exercitados noutra máquina.

Corrige a CHG-0014 por adição, como manda a regra 4. Primeiro, a lista de ficheiros da CHG-0014 omitia o `.gitattributes` criado por `graphify hook install`, que regista o driver de fusão de `graph.json`. Segundo, os hooks do Claude Code passam de `.claude/settings.local.json` para `.claude/settings.json`, agora com o comando `graphify` sem caminho absoluto, e por isso partilháveis. O skill `/graphify` passa a viver no projecto.

### CHG-0014 · Graphify como memória do projecto

- **Data:** 2026-11-18
- **Tipo:** infra
- **Pai:** CHG-0012
- **Estado:** activa
- **Requisitos:** nenhum
- **Commit:** 35a41d0
- **Migração:** nenhuma
- **Ficheiros:**
  - `.graphifyignore`
  - `.gitignore`
  - `CLAUDE.md` (secção graphify)
  - fora do repositório: `.claude/settings.local.json`, `.git/hooks/post-*`, `~/.local/share/graphify/venv`, `~/.local/bin/graphify`
- **Reversibilidade:** total
- **Reversão:**
  1. Correr `graphify claude uninstall` e `graphify hook uninstall`.
  2. Apagar `.claude/settings.local.json`, `.graphifyignore` e `graphify-out/`.
  3. Retirar de `.gitignore` as linhas de `graphify-out/` e de `.claude/settings.local.json`.
  4. Apagar `~/.local/share/graphify/` e `~/.local/bin/graphify`.
  5. Reverter o commit.
- **Verificação:**
  - Feito:
    - pacote `graphifyy` 0.9.112 confirmado no PyPI, Apache-2.0, com o repositório oficial nos metadados;
    - `graphify update .` local, sem chamar modelo (1315 nós, 2622 arestas);
    - `graphify query` responde;
    - as definições globais do Claude Code ficaram intactas.
  - Por fazer: a extracção semântica dos documentos (`/graphify . --update`). Envia o texto dos documentos ao modelo do assistente; os documentos não têm dados de facturas.

Grafo de conhecimento local do código e dos documentos, que serve de memória entre sessões. As facturas, o catálogo real, as bases de dados e os segredos ficam excluídos por `.graphifyignore`. Os hooks guardam um caminho absoluto desta máquina, por isso ficam fora do repositório.

### CHG-0013 · Registo de alterações e a sua regra

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0012
- **Estado:** activa
- **Requisitos:** nenhum
- **Commit:** 35a41d0
- **Migração:** nenhuma
- **Ficheiros:** `CHANGELOG.md`, `CLAUDE.md` (secção «Registo de alterações» e passo 6 do fecho de tarefa)
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** a árvore e as entradas CHG-0001 a CHG-0012 foram conferidas com `git log` e com o histórico das sessões.

Cria este registo e torna-o obrigatório para qualquer agente, nesta sessão e nas seguintes. As entradas CHG-0001 a CHG-0012 foram reconstruídas depois dos factos, a partir dos commits e das sessões de 18-11-2026.

### CHG-0012 · Correcções da revisão do ticket 02

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0011
- **Estado:** activa
- **Requisitos:** REQ-ING-007, REQ-ING-008, REQ-MAP-005, REQ-MAP-007, REQ-AUD-001, REQ-PLT-001, SEC-14, SEC-16, SEC-18
- **Commit:** 56c85a3
- **Migração:** nenhuma
- **Ficheiros:**
  - `backend/src/sextante/review/`
  - `backend/src/sextante/ingestion/`
  - `backend/src/sextante/matching/`
  - `backend/src/sextante/main.py`
  - `backend/pyproject.toml`
  - `backend/tests/api/test_encoding_review_regressions.py`
- **Reversibilidade:** total
- **Reversão:** reverter o commit. As facturas já carregadas mantêm-se válidas, porque o esquema não mudou.
- **Verificação:**
  - Feito: 95 testes, `mypy --strict`, `ruff`, 7 contratos do `import-linter`, contagem automática das funções (nenhuma acima de 20 linhas), teste no servidor real.
  - Não verificado: `gitleaks`, que não está instalado.

Resolve os achados da revisão do ticket 02:

- todo o texto extraído é normalizado;
- o modelo recebe o contexto da factura;
- as respostas do modelo são revalidadas pelo esquema;
- a auditoria guarda todos os scores;
- um carregamento misto devolve os trabalhos já existentes;
- os resultados de um trabalho inexistente dão 404;
- a API passa a usar só a camada de aplicação;
- um módulo `review` compõe os leitores publicados pelos outros módulos.

### CHG-0011 · Carregamento e codificação em segundo plano

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0010
- **Estado:** activa
- **Requisitos:** REQ-PLT-001, REQ-ING-001, REQ-ING-007, REQ-MAP-001, REQ-MAP-003 a REQ-MAP-006, REQ-AUD-001, REQ-AUD-002, SEC-04, SEC-14
- **Commit:** 2d6af1b
- **Migração:** `0002`, a partir de `0001`
- **Ficheiros:**
  - `backend/src/sextante/ingestion/`
  - `backend/src/sextante/matching/`
  - `backend/src/sextante/worker.py`
  - `backend/src/sextante/platform/audit.py`
  - `backend/migrations/versions/0002_encoding_tables.py`
  - dependências novas: `rapidfuzz` (MIT) e `python-multipart` (Apache-2.0)
- **Reversibilidade:** parcial
- **Reversão:**
  1. Salvaguardar `sextante.db` e `uploads/`.
  2. Correr `alembic downgrade 0001`, que apaga as tabelas e os dados.
  3. Reverter o commit.

  Os eventos de auditoria apagados pelo `downgrade` só se recuperam pela salvaguarda. Sem ela, a reversão é `não`.
- **Verificação:** 87 testes, `mypy`, `ruff`, 5 contratos do `import-linter`, teste no servidor real (sem extractor configurado, a factura é recusada).

Carregamento com idempotência pelo digest e um trabalhador em processo que codifica contra OUTLAYS. O modelo recebe a aba inteira e responde com um índice validado. Cada linha codificada fica numa auditoria só de inserção. O extractor e o classificador ficam provisórios, recusando com motivo explícito, até aos tickets 12 e 11.

### CHG-0010 · Correcções da revisão do ticket 01

- **Data:** 2026-11-18
- **Tipo:** fix
- **Pai:** CHG-0009
- **Estado:** activa
- **Requisitos:** REQ-MAP-012, REQ-PLT-005, REQ-PLT-006, REQ-PLT-007, NFR-OBS-001, SEC-15
- **Commit:** 753a000
- **Migração:** nenhuma; a migração `0001` muda de pasta para `backend/migrations/`
- **Ficheiros:** `backend/src/sextante/platform/`, `backend/src/sextante/catalog/`, `backend/migrations/`, `backend/tests/`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** 52 testes, `mypy`, `ruff`, 3 contratos do `import-linter`, teste no servidor real com o identificador de correlação.

Resolve os achados da revisão do ticket 01:

- valores obrigatórios em branco passam a ser recusados;
- os logs do uvicorn saem em JSON, com `correlation_id` por pedido;
- os registos não se propagam além do handler JSON, por isso a redacção já não se pode perder;
- os erros de domínio herdam `DomainError`;
- os outros módulos só chegam ao catálogo pelos seus contratos.

### CHG-0009 · Arranque com catálogo validado

- **Data:** 2026-11-18
- **Tipo:** feat
- **Pai:** CHG-0008
- **Estado:** activa
- **Requisitos:** REQ-MAP-012, REQ-PLT-007, REQ-PLT-008, NFR-OBS-001, D-3.5, D-3.9
- **Commit:** 5651ff7
- **Migração:** `0001` (base), sem revisão anterior
- **Ficheiros:** `backend/`, `config/.env.example`, `README.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit e apagar `sextante.db` e `backend/.venv`.
- **Verificação:** 33 testes, `mypy`, `ruff`, `import-linter`, licenças, `make run` com o catálogo real.

A aplicação arranca com um comando, escuta só em `127.0.0.1` e valida o catálogo. Recusa arrancar quando falta configuração ou o catálogo é inválido.

### CHG-0008 · Repositório git

- **Data:** 2026-11-18
- **Tipo:** infra
- **Pai:** CHG-0007
- **Estado:** activa
- **Requisitos:** SEC-03
- **Commit:** 8979ec5 (commit de base, agrega as entradas CHG-0001 a CHG-0008)
- **Migração:** nenhuma
- **Ficheiros:** `.gitignore`, ramo `feature/REQ-PLT-007-startup-catalog-validation`
- **Reversibilidade:** parcial
- **Reversão:** apagar `.git` elimina todo o histórico. A alternativa recomendada é manter o repositório e reverter commits concretos.
- **Verificação:** `git log` e `git status`. `sources/` está fora do controlo de versões por causa dos metadados do catálogo real (ponto 17 do OPEN-ITEMS).

Põe o projecto sob controlo de versões. Facturas, bases de dados, segredos e o catálogo real ficam fora.

### CHG-0007 · Limite de itens enviados ao modelo

- **Data:** 2026-11-18
- **Tipo:** security
- **Pai:** CHG-0006
- **Estado:** activa
- **Requisitos:** SEC-09, SEC-14, D-3.16
- **Commit:** 8979ec5 (agregado)
- **Migração:** nenhuma
- **Ficheiros:** `docs/03-seguranca.md`, a spec, os tickets 01 e 02
- **Reversibilidade:** total
- **Reversão:** reverter a alteração aos documentos e repor o limite de 20 candidatos por linha. Isso exige reverter também D-3.16 (a aba inteira enviada ao modelo).
- **Verificação:** pesquisa por `MAX_CANDIDATES` e `candidatos recuperados` em `docs/`, sem ocorrências.

O limite de 20 candidatos por linha passou a 100 itens por aba, por coerência com o envio da aba inteira. O índice continua validado pelo comprimento real da lista.

### CHG-0006 · Alinhamento dos documentos de desenho

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0005
- **Estado:** activa
- **Requisitos:** D-3.6, D-3.7, D-3.8, D-3.15 a D-3.18, L-13 a L-16
- **Commit:** 8979ec5 (agregado)
- **Migração:** nenhuma
- **Ficheiros:**
  - `docs/00-decisoes-e-lacunas.md`, `docs/01-requisitos.md`, `docs/02-arquitectura.md` e `docs/04-padroes-de-codigo.md` (versão 0.2)
  - `CLAUDE.md`
  - `OPEN-ITEMS.md`
- **Reversibilidade:** total
- **Reversão:** reverter as alterações aos documentos. O código que as implementa (CHG-0009 em diante) passaria a contradizê-los.
- **Verificação:** pesquisa por termos retirados (desempate, `token_set_ratio`, `other`, `EntityTiebreaker`), só encontrados em notas de retirada.

Passa para os documentos oficiais as decisões Q1 a Q24 e a evidência das amostras:

- a verificação de entidade deixa de usar o modelo;
- o NIF passa a vetar a correspondência, e o "ao cuidado de" não conta como entidade;
- o modelo recebe a aba inteira;
- a confiança é recalculada;
- entram os tipos de linha, as recusas e o conjunto dourado.

### CHG-0005 · Tickets 01 a 13 e emenda pelas amostras

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0004
- **Estado:** activa
- **Requisitos:** REQ-ING-009, REQ-ING-010, REQ-ENT-007, REQ-ENT-008
- **Commit:** 8979ec5 (agregado)
- **Migração:** nenhuma
- **Ficheiros:** `.scratch/nucleo-codificacao/issues/`, `.scratch/nucleo-codificacao/spec.md`, `GLOSSARY.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** os códigos esperados das amostras foram conferidos com o catálogo real.

Divide a spec em 13 tickets verticais e emenda-a com a extracção de PDF nativo, depois de analisar as 12 amostras.

### CHG-0004 · Especificação do núcleo de codificação

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0003
- **Estado:** activa
- **Requisitos:** REQ-ENT, REQ-MAP, REQ-CNF, REQ-REV, REQ-EXP (as cinco áreas)
- **Commit:** 8979ec5 (agregado)
- **Migração:** nenhuma
- **Ficheiros:** `.scratch/nucleo-codificacao/spec.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** fronteiras de teste confirmadas pelo utilizador.

Spec do núcleo de codificação, com 58 histórias de utilizador e duas fronteiras de teste: a API HTTP e as regras de domínio puras.

### CHG-0003 · Glossário e pontos em aberto da sessão de grilling

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0001
- **Estado:** activa
- **Requisitos:** L-01 a L-12
- **Commit:** 8979ec5 (agregado)
- **Migração:** nenhuma
- **Ficheiros:** `GLOSSARY.md`, `OPEN-ITEMS.md`
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** as decisões Q1 a Q24 foram confirmadas pelo utilizador.

Fixa o vocabulário do domínio e regista os pontos que esperam resposta do avaliador e da AMT, com a decisão provisória de cada um.

### CHG-0002 · Configuração dos skills de engenharia

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** CHG-0001
- **Estado:** activa
- **Requisitos:** nenhum
- **Commit:** 8979ec5 (agregado)
- **Migração:** nenhuma
- **Ficheiros:** `docs/agents/`, `CLAUDE.md` (secção «Agent skills»)
- **Reversibilidade:** total
- **Reversão:** reverter o commit.
- **Verificação:** nenhuma além da leitura.

Tracker local em `.scratch/`, rótulos de triagem por omissão e documentação de domínio num único contexto.

### CHG-0001 · Documentação inicial do projecto

- **Data:** 2026-11-18
- **Tipo:** docs
- **Pai:** nenhum
- **Estado:** activa
- **Requisitos:** todos os de `docs/01-requisitos.md` (versão 0.1)
- **Commit:** 8979ec5 (agregado)
- **Migração:** nenhuma
- **Ficheiros:** `docs/00-decisoes-e-lacunas.md` a `docs/04-padroes-de-codigo.md`, `CLAUDE.md`, `assets/`, `scripts/gen_diagrams.py`
- **Reversibilidade:** total
- **Reversão:** não aplicável; é a raiz da árvore.
- **Verificação:** nenhuma.

Documentos de partida do projecto, anteriores às sessões de 18-11-2026.
