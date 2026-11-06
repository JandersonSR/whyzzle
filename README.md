# Whyzzle

**Pare de decorar. Entenda o porquê.** · *Stop memorizing. Understand the why.*

Um guia interativo de aprendizado que mistura jogo passo a passo e livro de receitas. Em cada passo você
**prevê** o que vai acontecer, **executa** (digitando um comando ou usando botões), **vê** uma cena animada
reagir, **entende o porquê** em três níveis (Simples, Dev, Especialista) e **quebra de propósito** para
descobrir o limite. No fim, o **modo receita** mostra como fazer o mesmo fora do simulador.

Sem vídeo, sem instalar nada, sem backend. Português e inglês, tema claro e escuro.

O catálogo tem 28 tópicos (de IA aplicada a Kubernetes, system design e liderança), cada um com as trilhas Fundamentos, Prática e Produção. O que já existe e o que vem a seguir está em [ROADMAP.md](ROADMAP.md).

## Primeiro tema: IA aplicada — trilha Fundamentos

1. O que um LLM faz (prever o próximo token)
2. Tokens e janela de contexto
3. Temperatura
4. Prompt bem feito × mal feito
5. Embeddings e similaridade
6. RAG
7. Ferramentas e agentes
8. Alucinação e avaliação
9. Missão final: o assistente da secretaria da Escola Girassol

As trilhas **Prática** (modelos reais no navegador e “sua chave de API”) e **Produção** (avaliação, custo,
latência, prompt injection, guardrails, LGPD e monitoramento, com casos reais) vêm nas próximas fases.
Cada trilha tem guia do professor (`/ia-aplicada/fundamentos/professor`) e livro de receitas
(`/ia-aplicada/fundamentos/receitas`).

> Os modelos da trilha Fundamentos são de brinquedo: números feitos à mão para mostrar o mecanismo.

## Rodando

```bash
npm install
npm run dev        # http://localhost:5173
npm test           # motor, leitor de comandos, jornadas das lições e paridade pt/en
npm run build      # valida o conteúdo, faz o typecheck e gera dist/
```

## Deploy no Vercel

Importe o repositório no Vercel. O `vercel.json` já define `npm run build`, a pasta `dist` e a regra que
manda todas as rotas para o `index.html`. Não há variáveis de ambiente.

## Estrutura

```
content/<tema>/<trilha>/NN-slug/   step.json · pt.json · en.json · teacher.json
src/engine/                        esquema, comandos, executores, ciclo do passo, eventos, progresso
src/models/                        modelos de brinquedo do executor simulado
src/scenes/                        cenas animadas
src/step/ · src/pages/             interface
tests/                             testes (vitest)
```

Detalhes do motor e de como criar lições: [ARCHITECTURE.md](ARCHITECTURE.md).

## Licença

MIT
