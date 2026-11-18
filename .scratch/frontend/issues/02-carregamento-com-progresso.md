# 02: Ecrã de carregamento com progresso

**What to build:** Depois de entrar, uma pessoa arrasta um ou mais PDF para o ecrã de carregamento e acompanha o trabalho até terminar: quantas facturas estão em fila, codificadas, recusadas, com falha ou por resolver, e os tokens gastos. Se o ficheiro já tinha sido carregado, o ecrã diz em que trabalho está. No fim, o ecrã leva aos resultados do trabalho.

**Blocked by:** 01 (Esqueleto do frontend e login por token)

**Status:** ready-for-agent

- [ ] Arrastar ou escolher ficheiros; os limites de tamanho e de número de ficheiros são os do servidor, e uma recusa mostra a mensagem do servidor em Português
- [ ] O progresso vem do estado do trabalho, actualizado até o trabalho terminar, com as facturas por estado e os tokens
- [ ] Um ficheiro já carregado mostra o trabalho existente, sem o tratar como erro
- [ ] O ecrã leva aos resultados do trabalho quando termina
- [ ] Nenhum texto visível em literal; tudo pelo catálogo de tradução
- [ ] O `README.md` descreve o fluxo de carregamento
- [ ] Testes do componente com a API simulada, incluindo um ficheiro recusado e um já carregado
