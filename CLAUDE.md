# Sextante · instruções para agentes de IA

**Projecto:** Sextante, pipeline de codificação automática de linhas de facturas de fornecedores
**Cliente:** AMT, Advanced Maritime Transports - Transitarios Limitada
**Stack:** Python 3.12 com FastAPI · React 18 com TypeScript · SQLite · Claude

Este ficheiro é lido antes de qualquer trabalho neste repositório. Vale igualmente para o Claude, para o Antigravity e para qualquer outro agente.

---

## Ordem de leitura

Antes de escrever a primeira linha de código de uma tarefa, ler o que a tarefa toca:

| Documento | Quando é obrigatório |
|---|---|
| `docs/00-decisoes-e-lacunas.md` | Sempre. É onde está o porquê de cada escolha e o que ainda não está decidido |
| `docs/01-requisitos.md` | Sempre que a tarefa implementa comportamento |
| `docs/02-arquitectura.md` | Sempre que a tarefa cria um módulo, uma porta ou um endpoint |
| `docs/03-seguranca.md` | Sempre que a tarefa toca input externo, ficheiros, dados, rede ou prompts |
| `docs/04-padroes-de-codigo.md` | Sempre |

Se o que o código pede contradizer um destes documentos, **perguntar**. Não resolver a contradição por iniciativa própria, em nenhuma das direcções.

---

## As cinco regras que, se forem esquecidas, estragam o projecto

Estas cinco não são preferências de estilo. Cada uma existe por um defeito concreto que evita.

### 1. O modelo nunca devolve um código de item

O Claude devolve **o índice** de um candidato na lista que o servidor construiu, ou `none`. Nunca um código em texto livre. O índice é validado contra o comprimento da lista, e o código correspondente contra a aba de destino daquela linha, antes de ter qualquer efeito.

O conteúdo de uma factura é dado de origem externa e chega ao prompt. Sem esta restrição, uma descrição construída para parecer instrução consegue dirigir a atribuição de códigos contabilísticos.

Detalhe completo em `docs/03-seguranca.md` SEC-14. **Nenhuma alteração enfraquece esta fronteira.** Se parecer que simplificaria o código, é sinal de que se perdeu o motivo: voltar ao documento antes de continuar.

### 2. A regra de recurso `O00999` aplica-se apenas a OUTLAYSP

Uma linha encaminhada para `OUTLAYS` sem correspondência fica com o código **vazio**, confiança `LOW` e sinalização obrigatória. Não recebe `O00999`, nem o melhor candidato disponível.

É a regra R3 do enunciado, mais a lacuna L-08 que o enunciado deixa aberta. **Uma lacuna é devolvida ao humano, nunca preenchida por omissão.** Ver `REQ-MAP-008` e `REQ-MAP-009`.

### 3. A lista de exclusão de entidades vem antes da correspondência aproximada

Empresas irmãs, companhias de navegação e clientes conhecidos são `NO_MATCH` definitivo, qualquer que seja a semelhança com o nome da AMT. A lista é avaliada **primeiro**, por igualdade sobre o nome normalizado.

Um transitário tem empresas irmãs com nome quase idêntico. Ordem invertida, a correspondência aproximada decide antes e a regra R4 fica violada em silêncio. Ver `REQ-ENT-003`.

### 4. A confiança é calculada, nunca pedida ao modelo

`HIGH`, `MEDIUM` e `LOW` saem de uma regra determinística sobre o score do candidato de topo, o intervalo até ao segundo, e a concordância do modelo. Nunca de uma pergunta ao Claude.

Modelos de linguagem são maus avaliadores da sua própria certeza, e a classificação que devolvem não é reproduzível entre execuções. Num sistema cujo propósito é decidir o que vai para revisão humana, isso é pior do que nada. Ver `REQ-CNF-001` e `docs/02-arquitectura.md` §4.10.

### 5. Nada da factura entra nos logs

Descrições, nomes de fornecedor, valores monetários, corpo de prompt e resposta integral do modelo ficam fora do log. Scores, posições, digests, classificações e identificadores podem ir.

A distinção: **o que explica a decisão pode ir para o log, o que a alimentou não.** Ver `docs/03-seguranca.md` SEC-15.

---

## Quando perguntar em vez de decidir

Perguntar sempre que:

- O requisito não existe ou é ambíguo.
- Duas abordagens têm impacto de segurança diferente.
- A alteração toca em identidade, permissões, dados pessoais ou configuração de infraestrutura.
- O que o código pede contradiz um documento desta pasta.
- Uma lacuna aberta (⚠) bloqueia a implementação de forma que a parametrização não resolve.

Uma pergunta custa minutos. Uma suposição errada num requisito contratual custa um marco.

---

## Lacunas abertas que bloqueiam implementação

Lista viva. O estado autoritativo está em `docs/00-decisoes-e-lacunas.md` §4 e §5.

| ⚠ | Lacuna | Bloqueia |
|---|---|---|
| ⚠ | **L-01** · facturas nativas ou digitalizadas | Já tem decisão registada (D-3.6, 18-11-2026): extracção só de PDF nativo no modelo das amostras, recusa de digitalizados com `pdf_without_text_layer`. Não escrever OCR nem extracção de XLSX sem nova decisão |
| ⚠ | **L-02** · amostras recebidas (12), resultados esperados por confirmar | A publicação de métricas de precisão e a calibração dos limiares. **As amostras nunca entram no repositório** (D-3.18). Limiares provisórios |
| ⚠ | **L-04** · lista das empresas irmãs e companhias de navegação | O conteúdo de `config/entity_denylist.yaml`. A estrutura pode avançar, o conteúdo não se inventa |
| ⚠ | **L-08** · ausência de correspondência em OUTLAYS | Já tem decisão por omissão, na regra 2 acima. Confirmar com o avaliador, porque a escolha é visível na saída |
| ⚠ | **L-06** · linhas de imposto e de subtotal | A política de classificação de tipo de linha. Decisão por omissão já aplicada |
| ⚠ | **L-07** · autenticação | Está decidido não haver nesta versão, com ligação a `127.0.0.1` e risco residual declarado. **Nunca alterar o anfitrião para `0.0.0.0`** |

Uma lacuna com decisão por omissão aplicada não é uma lacuna fechada: a decisão está registada e pode ser revertida pela resposta. Não a tratar como definitiva.

---

## Antes de declarar uma tarefa concluída

1. Percorrer o gate de `docs/03-seguranca.md` §1 se a tarefa tocou input externo, ficheiros, dados, rede ou prompts.
2. Preencher o bloco de fecho de `docs/03-seguranca.md` §21, com evidência concreta. "Deve estar bem" não é evidência.
3. Percorrer a lista de verificação de `docs/04-padroes-de-codigo.md` §10.
4. Confirmar que os testes novos têm `@pytest.mark.requirement`.
5. Correr `make test`, `make golden` e `make traceability-matrix`.

**Nunca declarar concluído com itens aplicáveis por verificar.** Listar os pendentes e o motivo.

---

## Transversal

- Não acrescentar dependência sem verificar a licença.
- Não gerar segredos reais em exemplos nem em dados de teste.
- Não resolver nem contornar desafios anti automação.

---

## Transversal, específico deste projecto

- **Não chamar a API da Anthropic num teste.** Sem excepções, nem marcadas, nem opcionais. Usar `FakeItemClassifier`. A verificação de entidade não usa o modelo, e por isso não tem duplo de modelo.
- **Não commitar uma factura real nem um ficheiro `.db`.** As facturas de teste são sintéticas e identificadas como tal.
- **Não alterar um prompt sem confirmação.** Um prompt é código: alterá-lo muda o comportamento do sistema. Cada prompt tem versão, registada em cada decisão que o usou.
- **Não duplicar uma regra entre código e prompt.** A lista de exclusão, a regra de recurso e a regra de confiança vivem em código. Duas cópias de uma regra acabam por divergir.
- **Não desactivar um controlo para fazer um teste passar.** Se a validação do índice, um limite de comprimento ou a neutralização de fórmula estorva, o problema está no desenho.
- **Não capturar uma falha de validação do modelo e seguir com um valor por omissão.** Resposta inválida é falha de linha, com `LOW` e sinalização. Nunca um código improvisado.
- **Não escrever `0.0.0.0` como anfitrião de escuta** enquanto L-07 estiver aberta.
- **Não ler um ficheiro carregado com `pandas.read_excel`.** A leitura passa por `openpyxl` em `read_only` e `data_only`, depois da validação de tipo de SEC-16. O `pandas` entra depois.
- **Não acrescentar `dangerouslySetInnerHTML`.** Não há nenhum caso neste projecto que o justifique.

---

## Convenções de nomenclatura do projecto

| Artefacto | Valor |
|---|---|
| Pacote Python | `sextante` |
| Prefixo de variáveis de ambiente | `SEXTANTE_` |
| Prefixo de variáveis públicas do frontend | `VITE_SEXTANTE_` |
| Base de dados | `sextante.db` |
| Ramos | `feature/<req-id>-descricao-curta` |
| Mensagens de commit | Inglês, formato convencional, com `Implements: REQ-...` |
| Nomes de evento de log | `snake_case` em Inglês |

Código, identificadores, comentários e logs em **Inglês**. Texto de interface em **Português**, em catálogo de tradução.

Cuidado com `item`: existem o item do catálogo, a linha da factura e o código de item, e são três coisas diferentes que aparecem na mesma função. Usar `catalog_item`, `invoice_line` e `item_number`.

---

## Diagramas

Os diagramas de `docs/diagramas/` são gerados por `scripts/gen_diagrams.py`.

Uma alteração de desenho altera o script e regenera. Editar à mão em excalidraw.com é legítimo para explorar; o que vai para o repositório sai do script, para que as coordenadas não se degradem com edições manuais sucessivas.

---

## Agent skills

### Issue tracker

Issues are kept as local markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Uses the five default roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), each recorded as a `Status:` line. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context (`GLOSSARY.md` and `docs/adr/` at the root). See `docs/agents/domain.md`.
