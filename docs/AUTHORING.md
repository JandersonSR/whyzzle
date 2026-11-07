# Escrever uma etapa do Whyzzle (guia para quem escreve lições)

Whyzzle ("Pare de decorar. Entenda o porquê.") é um guia interativo: cada lição é um passo de jogo com
missão, caixa de comando e uma cena animada. Ciclo: **palpite → rodar → ver → por quê → quebrar de propósito**.
Tom bem-humorado e acolhedor, para leigos, escolas e empresas (não é livro infantil). Sem vídeos.
Nada de links ou menções ao learnFlow.

## Onde fica o quê

```
content/<topico>/topic.json                  # trilhas: fundamentos | pratica | producao, status ready|soon
content/<topico>/<trilha>/NN-slug/step.json  # comando, modelo, cena, palpite, flag de quebra, simulação
content/<topico>/<trilha>/NN-slug/pt.json    # todos os textos em português
content/<topico>/<trilha>/NN-slug/en.json    # os mesmos textos em inglês (mesmas chaves)
content/<topico>/<trilha>/NN-slug/teacher.json  # guia do professor {pt:{…}, en:{…}}
tools/gen/*.py                               # geradores Python que escrevem esses JSON
```

Lições são **só dados**: modelo `declarative` + cena `widgets`. Leia antes de escrever:
- `ARCHITECTURE.md`, seção "Lições só com dados" (formato de `data.sim`: consts, compute, cases, widgets).
- `src/engine/expr.ts` (a lista de funções permitidas nas expressões fica no objeto `FUNCS`).
- `src/scenes/Widgets.tsx` e `src/scenes/gallery.json` (as 9 peças: metrics, terminal, queue, cluster, table, flow, chart, checks, note).
- Exemplos completos: `tools/gen/p2_a.py` e `tools/gen/p2_b.py` (8 lições de RAG). Para geradores novos use `tools/gen/common.py`
  (`write(topic, track, folder, step, pt, en, teacher)`, `flag(...)`, `step(..., track, ...)`).

Regras do modelo declarativo, na prática:
- String que começa com `=` é expressão; com `@chave` é texto da cena (`scene.chave` no pt/en), com `{vars}` preenchidas.
- Um valor de `compute` não pode ter o mesmo nome de uma flag (ele sobrescreve a flag).
- `cases` aplicam todos os que batem, em ordem: `flags`, `vars` (usadas em `{…}` nos textos), `error` (texto em `errors["model.<codigo>"]`).
- Erros do parser: `errors["aboveMax.<flag>"]`, `belowMin`, `notInEnum`, `notBool`, `missingArg`.
- Funções úteis para listas: `mul`, `cumsum`, `maxall`, `geall`, `ltall`, `pickrows`, `lookupall`, `containsany`, `memberall`, `tagmatching`, `topk`, `blend`, `zip`, `mark`, `fill`.
  Não há map/filter com expressão por item: pré-calcule tabelas no gerador Python quando precisar.
- `live: true` faz a cena atualizar enquanto a pessoa mexe nos controles (bom para lições de cálculo).

## Cada lição precisa de (o teste de conteúdo cobra a maior parte)

- PT e EN completos com as mesmas chaves: `title`, `subtitle`, `mission`, `predict` (pergunta + texto de cada opção),
  `feedback` (right, wrong, skipped), `coach` (ui, cmd), `tryNext` (ui, cmd), `why` com as **3 camadas**
  (`simples`, `dev`, `especialista`), `break` (mission ui/cmd, success, calm), `hints` (ui e cmd, 3 níveis cada; o 3º
  nível de `hints.cmd` é exatamente o comando que quebra), `errors`, `controls`, `scene`, `data`,
  `recipe` (`steps` + `ok` = "deu certo se você vê isto").
- `teacher.json`: objectives, minutes, activity, discussion, misconceptions (pt e en).
- Fatos e versões conferidos na documentação oficial atual (use WebSearch/WebFetch). Na dúvida, não afirme número/versão.
- Missão final da trilha: `kind: "mission"`, sem `predict`, a flag de `break` é a de sucesso, e o locale tem `success`.
  Os critérios aparecem num widget `checks`. A missão começa com padrões ruins que a pessoa precisa consertar.

## Testes e verificação

- Escreva `tests/<topico>-<trilha>.test.ts` (veja `tests/pratica.test.ts`): em PT e EN, o comando padrão roda sem erro,
  o comando de `hints.cmd[2]` levanta a flag de quebra, e o palpite certo é o que a simulação mostra.
- Ao publicar lições num tópico, mude o status da trilha para `"ready"` no `topic.json` desse tópico (o teste exige).
- Rode `npx vitest run` e `npx tsc -p .` até passar tudo. Não rode git.

## Limites para quem escreve em paralelo

Mexa só em: `content/<seu-topico>/<sua-trilha>/`, no `topic.json` do seu tópico (status da trilha), no seu gerador em
`tools/gen/` e no seu arquivo de teste. **Não edite** `ROADMAP.md`, `CHANGELOG.md`, `src/`, nem testes de outros.
Se precisar de uma função nova no motor, contorne com as que existem e descreva a necessidade no relatório final.
