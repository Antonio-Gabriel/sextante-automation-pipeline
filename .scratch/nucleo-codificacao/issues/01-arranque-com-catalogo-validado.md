# 01: Arranque da aplicação com catálogo validado

**What to build:** Um operador arranca a aplicação com um único comando, a partir de um repositório acabado de clonar e de um ficheiro de configuração de exemplo, e obtém uma resposta em `/api/health`.

A aplicação **recusa arrancar**, com uma mensagem que diz a aba e a condição em falha, quando:

- falta configuração obrigatória: a chave da API, o caminho do catálogo, o nome da entidade alvo ou o NIF da entidade alvo;
- o catálogo é inválido:
  - falta uma das abas OUTLAYS ou OUTLAYSP;
  - falta a coluna A numa delas;
  - há códigos vazios ou repetidos numa aba;
  - `O00999` não existe em OUTLAYSP;
  - uma aba excede o limite de 100 itens enviados ao modelo.

A aplicação **arranca com um aviso** quando o catálogo tem caracteres invisíveis ou uma descrição em inglês vazia.

O catálogo fica em memória, com os valores de apresentação e os de comparação de cada item, e com o digest SHA-256 do ficheiro. A base de dados nasce das migrações, com as três condições de uso do SQLite (WAL, chaves estrangeiras ligadas e espera em escrita concorrente). Os logs são JSON estruturado, e a aplicação escuta apenas em `127.0.0.1`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Um comando documentado arranca a aplicação, e `/api/health` responde
- [ ] Cada configuração obrigatória em falta impede o arranque, com uma mensagem própria
- [ ] Cada condição inválida do catálogo impede o arranque, com uma mensagem que nomeia a aba e a condição
- [ ] Os caracteres invisíveis e as descrições EN vazias geram um aviso, não uma falha
- [ ] Os valores de comparação estão em NFKC, sem caracteres invisíveis e com os espaços colapsados; os valores de apresentação conservam o código exacto e a descrição PT sem espaços nas pontas
- [ ] O digest do catálogo fica disponível para os módulos seguintes
- [ ] A base de dados é criada pelas migrações, com os três pragmas activos
- [ ] Os testes usam um catálogo sintético com a estrutura real das colunas, incluindo `O00999`, um item genérico, um par PT/EN divergente, um item sem EN e um caracter invisível
- [ ] Os testes têm a marca de requisito (REQ-MAP-012, REQ-PLT-007, REQ-PLT-008)
