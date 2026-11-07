# Arquitetura do Whyzzle

Este documento é o contrato do motor. Ele descreve como as lições são dados, quais são as peças que se
plugam por nome e onde as próximas fases (Prática, Produção, guia do professor e modo turma) entram sem
mudar as lições já escritas.

## Princípios

1. **Um motor, muitas lições.** Uma lição é uma pasta de arquivos JSON. Código só entra quando uma
   lição precisa de uma cena ou de um modelo que ainda não existe.
2. **Tudo no navegador.** Site estático, sem backend, progresso salvo no `localStorage`. Deploy no Vercel.
3. **Bilíngue desde o primeiro dia.** Todo texto visível existe em `pt.json` e `en.json`, com as mesmas
   chaves e os mesmos `{placeholders}` (conferido por teste).
4. **O ciclo de todo passo:** prever → executar → ver → entender o porquê → quebrar de propósito.
5. **Três camadas de explicação** no mesmo passo: Simples, Dev e Especialista.

## Hierarquia do conteúdo

```
Tema (topic.json)
└── Trilha: fundamentos · pratica · producao
    └── Passo (pasta NN-slug/)  ← kind "step" (ciclo completo) ou "mission" (missão final)
```

```
content/ia-aplicada/
  topic.json                       título, chamada e as 3 trilhas (ready | soon)
  fundamentos/
    03-temperatura/
      step.json    definição neutra de idioma: comando, modelo, cena, palpite, quebra, dados numéricos
      pt.json      todos os textos em português + dados que dependem do idioma
      en.json      o mesmo em inglês
      teacher.json guia do professor (pt e en)
```

O nome da pasta sem o número vira a URL: `/ia-aplicada/fundamentos/temperatura`.
`receitas` e `professor` são reservados para páginas da trilha.

## As 5 peças do motor

| Peça | Onde | O que é | Como a lição usa |
| --- | --- | --- | --- |
| **Cenas** | `src/scenes/` | Componentes React que desenham o que acontece por dentro; `widgets` é a cena reutilizável configurada por dados | `"scene": "widgets"` |
| **Executores** | `src/engine/executors.ts` | Quem gera a resposta: `simulado`, `no-navegador`, `sua-chave` | `"executors": [...]` em ordem de preferência |
| **Modelos simulados** | `src/models/` | Os “modelos de brinquedo” do executor simulado | `"model": "sampler"` |
| **Checagens** | `src/engine/registry.ts` | O que conta como acerto (flags levantadas pelo modelo) | `"break": { "flag": "weird" }` |
| **Comandos** | `src/engine/command.ts` | Gramática `verbo "texto" --opcao valor`, nos dois idiomas | bloco `"command"` do `step.json` |
| **Eventos** | `src/engine/events.ts` | Toda ação vira um evento (palpitou, rodou, errou, dica, concluiu) | automático |

### Comandos

`step.json → command` declara verbo, argumento entre aspas e opções (`number`, `int`, `string`, `enum`,
`list`, `bool`) com limites. A partir disso o motor:

- lê o que a pessoa digita, aceitando verbos e opções em português **ou** inglês, aspas curvas do celular e
  vírgula decimal;
- devolve erros estruturados (`notNumber`, `oneDash`, `aboveMax`…) que cada passo explica com texto próprio
  em `errors["<código>.<opção>"]`, caindo num texto genérico quando não há;
- gera o **modo Botões** (controle deslizante, caixas de seleção, chips) e o comando equivalente ao vivo;
- traduz o comando quando a pessoa troca de idioma, mantendo os valores.

### Executores

- `simulado` — modelos de brinquedo determinísticos (com sorteio controlado). Funciona em qualquer celular.
- `no-navegador` — modelo real baixado para o navegador sob demanda (`src/runtime/`): Transformers.js
  (tokenizadores, embeddings; usa WebGPU se houver, senão WASM) e WebLLM (chat; exige WebGPU). Antes de baixar,
  a pessoa vê o tamanho e confirma; o arquivo fica no cache do navegador. Sem WebGPU, o painel explica e
  sugere "Sua chave". Os modelos ficam em `src/runtime/catalog.ts`.
- `sua-chave` — a chave de API da própria pessoa (Anthropic, OpenAI, Gemini ou compatível com OpenAI, como o
  OpenRouter), chamada direto do navegador. A chave fica só na memória da aba, ou no aparelho se a pessoa marcar
  "lembrar". A lista de modelos vem da API do provedor, para não ficar desatualizada. Configuração em `/sua-chave`.

Um passo oferece um executor real só se declarar em `step.json`:

```json
"real": {
  "no-navegador": { "adapter": "chat-prompt", "model": "Llama-3.2-1B-Instruct-q4f16_1-MLC" },
  "sua-chave": { "adapter": "chat-prompt" }
}
```

Para lições só com dados, o adaptador `declarative` roda uma **operação real** (`src/runtime/realOps.ts`) e
injeta o resultado na simulação da lição, que escolhe com `real ? realX : estimativa`:

| op | O que faz | Nomes injetados |
| --- | --- | --- |
| `tokens` | conta tokens com o tokenizador real | `realTokens`, `realTokensPieces` |
| `embed` | similaridade da pergunta com uma lista (prefixos E5 via `queryPrefix`/`passagePrefix`) | `realSims`, `realTop`, `realTopSim`, `realOrder` |
| `chat` | gera N amostras com temperatura, top-p e máximo de tokens | `realOutputs`, `realOutput`, `realDistinct` |
| `json` | pede JSON, extrai e valida contra um esquema simples | `realOutput`, `realJson`, `realValid`, `realProblems` |
| `tools` | loop de ferramentas por protocolo JSON, com limite de passos | `realTrace`, `realAnswer`, `realCalls`, `realLimit` |

O **adaptador** (`src/runtime/adapters.ts`) converte a saída do modelo real no mesmo formato que a cena do
passo já desenha, então as cenas não mudam. Falhas reais (download, WebGPU, CORS, chave recusada, limite,
modelo inválido) viram mensagens explicadas no painel "Quem responde". Enquanto um executor real está ativo,
a cena não faz prévia ao digitar: a resposta vem só quando a pessoa roda.

### Eventos e progresso

`emit()` publica eventos; `connectEvents(store)` deriva o progresso deles. O `ProgressStore` é uma
interface: hoje `createLocalStore()` grava no `localStorage` (até 500 eventos). O modo turma troca por um
store que também sincroniza com um backend, sem mexer nas lições.

## Lições só com dados (modelo `declarative` + cena `widgets`)

A maioria das lições novas não precisa de código: `step.json` usa `"model": "declarative"` e
`"scene": "widgets"`, e descreve a simulação em `data.sim`.

```jsonc
"data": {
  "sim": {
    "live": true,                       // a cena acompanha o que é digitado (senão mostra a última rodada)
    "consts": { "disponibilidade": 0.99 },
    "compute": {                        // em ordem; enxerga consts, os valores do comando e pt/en.json → data
      "total": "round(pow(disponibilidade, servicos) * 100, 2)"
    },
    "cases": [                          // todo caso verdadeiro se aplica, em ordem
      { "when": "modo == 'sincrono' && queda > 0", "flags": ["cascata"], "vars": { "falhas": "queda * 100" } },
      { "when": "len(text) == 0", "error": "vazio" }   // explicado em errors["model.vazio"]
    ],
    "widgets": [                        // "=expr" é expressão; "@chave" é texto da lição (pt/en.json → scene)
      { "type": "metrics", "items": [ { "label": "@total", "value": "=total", "format": "pct", "tone": "=total < 99 ? 'bad' : 'ok'" } ] },
      { "type": "terminal", "lines": ["$ kubectl get pods", "=ok ? '+api 1/1 Running' : '!api 0/1 CrashLoopBackOff'"] }
    ]
  }
}
```

**Expressões** (`src/engine/expr.ts`): números, textos, listas, `a.b`, `x[0]`, `+ - * / % **`,
comparações, `&& || !`, `cond ? a : b` e só as funções da lista branca (`min max pow round floor ceil clamp
sqrt abs log10 len includes range fill sum count join concat slice lower str number rand pick`). Não há
`eval` nem acesso a nada fora do que a lição define. `rand()` usa o sorteio controlado do motor (a prévia e os
testes são determinísticos).

**Peças da cena** (`src/scenes/Widgets.tsx`; todas aceitam `label` e `when`):

| Tipo | Campos | Uso típico |
| --- | --- | --- |
| `metrics` | `items: [{ label, value, format: pct·int·ms·min·money·num, tone }]` | disponibilidade, latência, custo |
| `terminal` | `lines: [...]` com prefixos `$` comando, `+` ok, `!` erro, `?` aviso, `~` apagado | `kubectl`, `kafka-*`, `psql`, `az` |
| `queue` | `producer`, `messages` (número ou lista), `consumers: [{ label, note, tone }]`, `dlq` | filas, DLQ, prefetch |
| `cluster` | `nodes: [{ name, status, pods: [{ name, status }] }]` (status do Kubernetes vira cor) | pods e nós |
| `table` | `columns`, `rows`, `tones`, `caption` | tabelas de banco, resultados |
| `flow` | `steps: [{ label, sub, tone }]` | fluxo de requisição, pipeline |
| `chart` | `kind: bar·line`, `labels`, `series: [{ label, values }]`, `threshold` | latência, lag, custo no tempo |
| `checks` | `items: [{ label, ok, why }]` | critérios de missão |
| `note` | `text`, `tone` | avisos e explicações curtas |

Tons: `ok`, `warn`, `bad`, `info`, `dim`, `neutral`, iguais nos temas claro e escuro.

**Validação**: o carregador de conteúdo roda `declIssues` em toda lição declarativa. Dados inválidos,
expressão que não faz parse, peça desconhecida ou texto `@chave` faltando em PT ou EN quebram o build com a
mensagem do problema. A página `/galeria` mostra todas as peças funcionando (estado saudável × incidente).

## Fluxo de um passo

```
digita / mexe nos botões ──► parseCommand ──► preview (modelo, determinístico) ──► cena reage ao vivo
                                   │
                    Rodar ─────────┴──► executor.run ──► ModelResult ──► reducer (stepMachine) ──► eventos
```

`src/engine/stepMachine.ts` é um reducer puro (testável e reproduzível): fase, palpite, rodadas, dicas,
erro e se o passo foi quebrado. Passos completam quando uma rodada da fase "Quebrar" levanta a flag de
quebra; missões completam em qualquer rodada que atinja todos os critérios.

## Qualidade

`npm test` roda:

- **content.test.ts** — todas as lições passam no esquema zod; pt e en têm as mesmas chaves, tamanhos de
  lista e placeholders; comando padrão, exemplos e a "cola" da dica 3 são comandos válidos; textos de erro
  apontam para opções que existem.
- **lessons.test.ts** — a jornada prometida de cada passo acontece de verdade no modelo, nos dois idiomas
  (ex.: temperatura 0 nunca varia; o RAG sem busca alucina; o teste só de tamanho dá 100% ao mentiroso;
  a missão começa quebrada e tem solução).
- **command.test.ts** e **stepMachine.test.ts** — leitor de comandos e ciclo do passo.

O build (`npm run build`) roda a validação de conteúdo antes do typecheck e do bundle; a CI roda tudo a
cada push.

## Onde entram as próximas fases

| Fase | O que muda | O que não muda |
| --- | --- | --- |
| 2 · Prática | lições em `pratica/` com adaptadores reais (executores já existem) | esquema, cenas existentes, comandos |
| 3 · Produção | casos reais com dados de exemplo em `producao/`; arquivo de preços datado; missões finais | motor |
| 4 · Professor e turma | página do professor já existe (`/…/professor`); turma = novo `ProgressStore` + painel | lições |
| Aprendizado direcionado | usar `requires`, `tags` e o histórico de eventos para recomendar o próximo passo | lições |

## Como criar uma lição

1. Copie uma pasta de passo (`content/<tema>/<trilha>/NN-slug/`).
2. Edite `step.json` (comando, modelo, cena, palpite, flag de quebra) e os textos em `pt.json`/`en.json`.
3. Se precisar de um modelo ou cena novos, crie em `src/models/` e `src/scenes/` e registre o nome.
4. Rode `npm test`: o teste de conteúdo aponta qualquer chave faltando ou diferente entre os idiomas.
