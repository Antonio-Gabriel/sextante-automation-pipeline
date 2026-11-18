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

### CHG-0015 · Skill do graphify no projecto e correcção da CHG-0014

- **Data:** 2026-11-18
- **Tipo:** infra
- **Pai:** CHG-0014
- **Estado:** activa
- **Requisitos:** nenhum
- **Commit:** pendente
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
- **Commit:** 05dd1a6
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
- **Commit:** 05dd1a6
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
- **Commit:** 88cf235
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
- **Commit:** 2eff0ce
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
- **Commit:** fd1a823
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
- **Commit:** 03b579b
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
- **Commit:** d0d633c (commit de base, agrega as entradas CHG-0001 a CHG-0008)
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
- **Commit:** d0d633c (agregado)
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
- **Commit:** d0d633c (agregado)
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
- **Commit:** d0d633c (agregado)
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
- **Commit:** d0d633c (agregado)
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
- **Commit:** d0d633c (agregado)
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
- **Commit:** d0d633c (agregado)
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
- **Commit:** d0d633c (agregado)
- **Migração:** nenhuma
- **Ficheiros:** `docs/00-decisoes-e-lacunas.md` a `docs/04-padroes-de-codigo.md`, `CLAUDE.md`, `assets/`, `scripts/gen_diagrams.py`
- **Reversibilidade:** total
- **Reversão:** não aplicável; é a raiz da árvore.
- **Verificação:** nenhuma.

Documentos de partida do projecto, anteriores às sessões de 18-11-2026.
