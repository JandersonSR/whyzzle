# Roadmap do Whyzzle

Do iniciante ao especialista, com uso real em escola e em empresa.

## Como ler este roteiro

- **Tópico**: um assunto (ex.: Mensageria e streaming). Assuntos que se sobrepunham foram juntados num tópico só.
- **Trilha**: todo tópico tem três.
  - **Fundamentos**: escola, leigos e quem está começando. Simulação visual, sem instalar nada.
  - **Prática**: devs e analistas. Casos reais de empresa e, quando der, motores reais rodando no navegador (modelos de IA, bancos de dados, Python), além do modo opcional "sua chave de API".
  - **Produção**: empresas e times. Operação, custo, segurança, conformidade (LGPD), monitoramento e decisões de arquitetura com casos reais.
- **Etapa**: de 5 a 8 lições do mesmo assunto e da mesma trilha. É a unidade de entrega: cada etapa sobe sozinha para o site.
- **Missão final**: o desafio que fecha cada trilha. Sem dicas, junta tudo o que a trilha ensinou.
- **Preparatório de certificação** (opcional): uma etapa extra no fim da trilha Produção, quando o tópico tem uma prova reconhecida.

### Uma etapa só sobe quando tem

1. PT e EN completos.
2. As 3 camadas de explicação (Simples, Dev, Especialista).
3. Modo receita com "deu certo se você vê isto".
4. Erros comuns explicados e dicas em níveis.
5. Fatos e versões conferidos na documentação oficial atual.
6. Funcionamento no celular.
7. Build sem erro, com os testes de conteúdo e de jornada passando.

Ao concluir uma etapa: commit, push (a Vercel publica) e atualização deste arquivo, marcando a etapa como feita e indicando a próxima.

### Legenda

- `[x]` feita e publicada
- `[ ]` a fazer
- **→** próxima etapa

### Motores reais no navegador (conferidos em nov/2026; conferir de novo ao construir cada etapa)

| Motor | Uso no Whyzzle |
| --- | --- |
| Transformers.js v4 (`@huggingface/transformers`, WebGPU com fallback em WASM) | tokenizadores reais, embeddings, classificação, fala e modelos pequenos com chamada de ferramentas |
| WebLLM (`@mlc-ai/web-llm`, API no estilo OpenAI, precisa de WebGPU) | chat com LLM aberto rodando no aparelho |
| Sua chave de API (chamada direta do navegador; a chave fica só no aparelho da pessoa) | modelos de fronteira, quando a pessoa quiser |
| PGlite (Postgres em WASM) e SQLite WASM | Bancos de dados, SQL, índices e planos de execução reais |
| DuckDB-WASM | Dados e analytics |
| Pyodide | Python no navegador |

Quando não existe motor real viável no navegador (Kafka, Kubernetes, nuvem), a Prática usa simuladores fiéis com a sintaxe real dos comandos (`kubectl`, `kafka-console-*`, `az`, `aws`, `terraform`). O modo receita leva a pessoa a fazer de verdade.

---

## Ordem de prioridade

| # | Tópico | Junta | Por que nesta posição |
| --- | --- | --- | --- |
| 1 | **IA aplicada** | IA aplicada (trilha, engenharia a fundo, corporativa avançada), Azure AI (AI-901, AI-103, AI-200) | Já começado; é o tema de maior demanda em escola e empresa |
| 2 | **Desenvolvimento assistido por IA** | LLMs no time, desenvolvimento assistido avançado, IA para DevOps e AIOps | Uso imediato no dia a dia de qualquer time de software |
| 3 | **Mensageria e streaming** | Mensageria (RabbitMQ, Kafka, padrões), Kafka e Event Hubs com .NET, Confluent | Base de sistemas que aguentam escala |
| 4 | **Contêineres e Kubernetes** | AKS na prática, CKA, contêineres de Cloud | Onde quase tudo roda em produção hoje |
| 5 | **C# e ASP.NET Core** | Trilha C#/ASP.NET, De Node e TypeScript para C# | Stack corporativa muito pedida no Brasil |
| 6 | **System design e sistemas distribuídos** | System design, system design aprofundado, sistemas distribuídos, parte de design do preparatório big tech | Raciocínio de sênior e arquiteto |
| 7 | **Bancos de dados, consistência e cache** | Bancos de dados por dentro e a fundo, decisão de dados/consistência/cache, cache e Redis | Toda aplicação depende disso |
| 8 | **APIs, contratos e integração** | Decisão de APIs e contratos | Fronteira entre times e sistemas |
| 9 | **Segurança de aplicações e identidade** | Segurança de aplicações (dois volumes), autenticação e autorização por stack | Obrigatório em qualquer empresa |
| 10 | **Arquitetura de software e DDD** | Fundamentos de engenharia de software, estrutura de código por stack, DDD estratégico/Event Storming/BDD | Código que dura |
| 11 | **Observabilidade, performance e confiabilidade** | Observabilidade na prática, performance/carga/caos | Saber o que está acontecendo em produção |
| 12 | **Nuvem: Azure e AWS** | Cloud em qualquer provedor, onde rodar cada coisa, AWS na prática, AZ-104, AZ-305, AWS SAA | Escolher e operar serviços de nuvem |
| 13 | **DevOps, IaC e Platform Engineering** | AZ-400, Terraform para AKS e Event Hubs, Platform Engineering e FinOps | Entregar com segurança e custo sob controle |
| 14 | **Node.js e TypeScript** | Trilha Node/TS, runtimes (Node, Deno, Bun) | Stack muito usada em startups |
| 15 | **Python para backend e IA** | Python para backend e IA | Ponte para IA e dados |
| 16 | **Frontend** | Frontend do navegador ao Next.js, React e Angular, frontend avançado e micro-frontends | Interface de tudo |
| 17 | **Dados e analytics** | Engenharia de dados, dados e analytics, DP-700, PL-300 | Decisão com dados |
| 18 | **Machine learning e deep learning** | ML e deep learning | Por dentro dos modelos |
| 19 | **Tech Lead e gestão de times** | Tech Lead (dois volumes), gestão de projetos e equipes, IA na gestão de projetos | Liderar gente e entrega |
| 20 | **Staff Engineer e carreira técnica** | Staff e arquitetura evolutiva, do pleno ao Staff, roteiro de 24 meses | Crescer além do sênior |
| 21 | **Algoritmos e entrevistas técnicas** | Algoritmos e estruturas de dados, preparatório big tech, carreira e entrevistas | Passar em processos seletivos exigentes |
| 22 | **Arquitetura SaaS multi-tenant** | Arquitetura SaaS | Produtos para muitos clientes |
| 23 | **Redes, sistemas operacionais e concorrência** | Redes, SO e concorrência, conceitos de runtimes | O que está por baixo de tudo |
| 24 | **Segurança em nuvem e SecOps** | SC-100, SC-200/SC-300, SC-500 | Especialização em segurança corporativa |
| 25 | **Integrações de mercado** | Ferramentas e integrações (n8n, WhatsApp, pagamentos, identidade, busca, flags) | Automação e produto no mundo real |
| 26 | **Negócios, produto e empreendedorismo** | Negócios e produto para engenheiros, criar sua empresa de tecnologia | Engenharia que gera resultado |
| 27 | **Telefonia e agentes de voz** | Asterisk e telefonia | Nicho forte em atendimento |
| 28 | **Projeto integrador** | Projeto final integrador | Fecha tudo num produto completo |

## 0. Plataforma (antes da Prática de IA aplicada)

Etapas de motor e interface. Não têm lições, mas seguem a mesma regra de pronto: PT e EN, celular, build e testes.

- [x] **PL1 · Tema escuro e catálogo de tópicos**: tema claro/escuro (segue o sistema, com botão de troca); página inicial com busca e filtro por área; página de cada tópico com as três trilhas; todos os 28 tópicos listados, com o que já está disponível e o que vem em breve.
- [x] **PL2 · Cenas reutilizáveis configuradas por dados**: terminal, fila/mensagens, cluster/pods, tabela de banco, fluxo de requisição e gráfico; mais um modelo declarativo (casos e fórmulas no `step.json`), para que a maioria das lições novas seja só `step.json` + textos, sem cena e modelo novos.
- [x] **PL3 · Executores reais**: `no-navegador` (Transformers.js para tokenizador, embeddings e modelos pequenos; WebLLM para chat), com download sob demanda, aviso de tamanho e volta para o simulado sem WebGPU; e `sua-chave`, com a chave guardada só no aparelho.

---

## 1. IA aplicada

### Fundamentos (escolas e curiosos)
- [x] **Etapa F1 · Como um LLM funciona por dentro** (8 lições): próximo token, tokens e contexto, temperatura, prompt, embeddings, RAG, ferramentas e agentes, alucinação e avaliação.
- [x] **Missão final**: o assistente da secretaria da Escola Girassol.

### Prática (devs e analistas)

Depende das etapas de plataforma PL1 a PL3.

- [x] **Etapa P1 · Modelos reais no navegador** (7 lições)
  1. Tokenizador real: contar tokens de PT × EN e de código (custo e janela de verdade).
  2. Embeddings reais: similaridade entre frases do seu domínio.
  3. Busca semântica sobre um FAQ real de RH.
  4. LLM local no aparelho (WebLLM): temperatura, top-p e limite de tokens de verdade.
  5. Saída estruturada: JSON com esquema e validação.
  6. Chamada de ferramentas com um modelo pequeno.
  7. Quando usar modelo local, aberto ou de fronteira (custo, privacidade, qualidade).
- [x] **Etapa P2 · RAG de verdade** (8 lições): ingestão e limpeza de documentos; chunking (tamanho e sobreposição); embeddings e banco vetorial no navegador; busca híbrida (palavra-chave + vetor); reranking; citação de fonte e recusa; perguntas multi-documento; avaliação de recuperação (recall@k).
  Lições: ingestão e limpeza; fatiar sem cortar a resposta; índice vetorial no navegador; busca híbrida; reranking; citar e recusar; perguntas com duas partes; medir a busca com recall@k.

- [x] **Etapa P3 · Prompts e agentes para o trabalho** (7 lições): prompt de sistema e papéis; exemplos (few-shot) e formato; extração de dados de e-mails e notas fiscais; classificação e triagem de tickets de atendimento; agente com ferramentas e limites; memória de conversa e resumo; MCP para conectar sistemas da empresa.
- [x] **Missão final da Prática**: assistente de RH que responde dúvidas a partir das políticas da empresa (fonte citada, recusa quando não sabe, triagem para humano), rodando no navegador.

### Produção (empresas e times)
- [ ] → **Etapa R1 · Avaliação e qualidade** (7 lições): conjunto de avaliação versionado; métricas de RAG (fidelidade, relevância); LLM como juiz e sua calibração; testes de regressão no CI; testes A/B de prompt; casos difíceis e perguntas sem resposta; ciclo de feedback de usuários.
  - Em andamento: escrita das 7 lições começou (subagente); falta revisão independente e publicação.
- [ ] **Etapa R2 · Segurança, privacidade e governança** (7 lições): prompt injection direta e indireta; guardrails de entrada e saída; vazamento de dados e permissões por documento; dados pessoais e LGPD (minimização, retenção, base legal); jailbreak e red teaming; auditoria e rastreabilidade; política de uso de IA na empresa.
- [ ] **Etapa R3 · Custo, latência e operação** (7 lições): custo por token e por conversa; cache de prompt e de respostas; roteamento entre modelos; streaming e latência percebida; limites de taxa e filas; observabilidade de LLM (traces, custo, qualidade); incidentes e rollback de prompt.
- [ ] **Etapa R4 · Casos reais de empresa** (8 lições): FAQ de RH; atendimento com triagem e passagem para humano; triagem de documentos; revisão de PR assistida; assistente de tech lead (reuniões, status, riscos); skills e regras para o LLM consultar a documentação e os sistemas internos; IA para análise de logs; plano de implantação e ROI.
- [ ] **Missão final da Produção**: colocar no ar o assistente de atendimento de uma empresa fictícia, com avaliação no CI, guardrails, custo por conversa dentro do orçamento, LGPD atendida e painel de monitoramento.
- [ ] **Preparatório de certificação** (opcional): AI-901, AI-103 e AI-200 (Azure AI).

## 2. Desenvolvimento assistido por IA
- **Fundamentos**
  - [x] F1 · IA no editor (6): autocompletar × chat × agente; contexto que o modelo enxerga; pedir com especificação; revisar o que a IA escreveu; quando não usar; ética e autoria.
  - [x] Missão: corrigir um bug pequeno com ajuda da IA, provando com teste.
- **Prática**
  - [ ] → P1 · Fluxo com agentes de código (7): especificação antes do código; arquivos de regras do repositório; tarefas pequenas e verificáveis; testes como contrato; refatoração assistida; legado e código desconhecido; vários agentes em paralelo.
  - [ ] P2 · Revisão e qualidade (6): revisão de PR com IA; checklists de segurança; testes gerados e seus limites; documentação viva; medição de retrabalho; prompts do time versionados.
  - [ ] Missão: entregar uma feature num repositório real com spec, testes e PR revisado.
- **Produção**
  - [ ] R1 · IA no time e na esteira (7): política de uso e segredos; IA no CI/CD; ChatOps e runbooks; AIOps para anomalias e incidentes; MCP para sistemas internos; métricas de produtividade sem ilusão; adoção e treinamento do time.
  - [ ] Missão: plano de adoção de IA para um time de 18 devs, com métricas, riscos e piloto de 30 dias.

## 3. Mensageria e streaming
- **Fundamentos**
  - [x] F1 · Por que filas existem (7): síncrono × assíncrono; comando × evento; garantias de entrega e ack; consumidor idempotente; ordem, DLQ e prefetch; pub/sub; quando não usar fila.
  - [x] Missão: pagamentos na Black Friday sem venda perdida nem cobrança duplicada.
- **Prática**
  - [ ] → P1 · RabbitMQ no trabalho (6): exchanges e bindings; filas duráveis e quorum; publisher confirms; retry com atraso e DLX; prefetch e escala de consumidores; RabbitMQ × Kafka.
  - [ ] P2 · Kafka a fundo (8): log, partições e offsets; chave e ordem; consumer groups e rebalance; acks, idempotência e transações do produtor; esquemas e compatibilidade; Kafka Connect; Event Hubs com API Kafka; reprocessamento.
  - [ ] P3 · Padrões de integração (6): transactional outbox; saga (coreografia × orquestração); backoff com jitter; correlation ID; inbox e deduplicação; evolução de eventos.
  - [ ] Missão: integrar pedidos, estoque e pagamento com outbox, saga e reprocessamento.
- **Produção**
  - [ ] R1 · Operar mensageria (7): dimensionar partições e retenção; lag e alertas; capacidade e custo (Confluent, Event Hubs, MSK); segurança (SASL, ACL, TLS); multi-região e recuperação de desastre; incidentes clássicos; runbooks.
  - [ ] Missão: plano de operação de um cluster que processa 50 mil eventos por segundo.
  - [ ] Preparatório: Confluent CCDAK e CCAAK.

## 4. Contêineres e Kubernetes
- **Fundamentos**
  - [x] F1 · Do programa ao contêiner (6): processo × contêiner × VM; imagem e camadas; Dockerfile; registro; por que orquestrar; o que é um cluster.
  - [x] Missão: empacotar uma API e explicar cada linha do Dockerfile.
- **Prática**
  - [ ] → P1 · Kubernetes com `kubectl` (8): pods e deployments; services e ingress; configmaps e secrets; probes; requests e limits; rolling update e rollback; HPA; troubleshooting (CrashLoopBackOff, ImagePullBackOff, OOMKilled).
  - [ ] P2 · AKS na prática (6): cluster com Terraform; ACR e identidade; Key Vault e segredos; rede e ingress; observabilidade; custo.
  - [ ] Missão: subir uma API .NET no AKS com segredos, probes, escala e rollback.
- **Produção**
  - [ ] R1 · Kubernetes em produção (7): multi-ambiente e GitOps; políticas e segurança; atualização de versão do cluster; capacidade e custo; resiliência (PDB, anti-affinity); backup; incidentes.
  - [ ] Missão: plano de produção para um cluster com 30 serviços.
  - [ ] Preparatório: CKA.

## 5. C# e ASP.NET Core
- **Fundamentos**
  - [ ] → F1 · C# do zero (7): tipos e variáveis; controle de fluxo; coleções e LINQ; classes e records; nulabilidade; exceções; async/await.
    - Em andamento: escrita das lições e da missão começou (subagente); falta revisão independente e publicação.
  - [ ] Missão: calculadora de empréstimo com testes.
- **Prática**
  - [ ] P1 · Web APIs com ASP.NET Core (8): minimal APIs × controllers; injeção de dependência e ciclos de vida; validação e ProblemDetails; EF Core e migrations; autenticação JWT; configuração e options; logging; testes de integração.
  - [ ] P2 · Vindo de Node e TypeScript (6): equivalências de linguagem; Task × Promise; pacotes e projetos; middleware; padrões idiomáticos; armadilhas comuns.
  - [ ] Missão: API de simulação de crédito com banco, autenticação e testes.
- **Produção**
  - [ ] R1 · .NET em produção (7): monólito modular; performance e alocação; resiliência com Polly; observabilidade com OpenTelemetry; background services; contêiner e AKS; segurança.
  - [ ] Missão: preparar a API de crédito para 1.000 requisições por segundo.

## 6. System design e sistemas distribuídos
- **Fundamentos**
  - [ ] F1 · Como sistemas grandes funcionam (6): cliente e servidor; escalar vertical × horizontal; balanceador; cache; banco e réplica; fila.
  - [ ] Missão: desenhar um encurtador de links para uma escola.
- **Prática**
  - [ ] P1 · Método de system design (7): requisitos; estimativas de capacidade; API; modelo de dados; blocos de construção; gargalos; trade-offs.
  - [ ] P2 · Sistemas distribuídos a fundo (8): tempo e relógios; consistência; replicação; consenso; transações distribuídas; partições de rede; idempotência; falhas parciais.
  - [ ] Missão: desenhar um sistema de pagamentos com saga e consistência.
- **Produção**
  - [ ] R1 · Casos reais (8): feed; chat em tempo real; busca; upload de mídia; multi-região; limitador de taxa; notificações; sistema com IA.
  - [ ] Missão: entrevista de system design simulada, do requisito ao custo.

## 7. Bancos de dados, consistência e cache
- **Fundamentos**
  - [ ] F1 · Dados organizados (6): tabelas e chaves; SQL básico; relacionamentos; índices; transação; SQL × NoSQL.
  - [ ] Missão: modelar a biblioteca da escola.
- **Prática**
  - [ ] P1 · SQL de verdade no navegador (PGlite) (8): modelagem; índices B-tree e compostos; planos de execução; N+1 e ORM; níveis de isolamento; locks e deadlocks; migrations sem downtime; MongoDB e documentos.
  - [ ] P2 · Cache e Redis (6): camadas de cache; cache-aside e invalidação; stampede; estruturas do Redis; rate limiter; maxmemory e eviction.
  - [ ] Missão: deixar uma consulta lenta 100 vezes mais rápida sem perder consistência.
- **Produção**
  - [ ] R1 · Dados em produção (7): réplicas e leitura; sharding e particionamento; backup e restore testado; consistência entre serviços; multi-tenant; LGPD em dados; custo.
  - [ ] Missão: migrar um banco de 2 TB sem parar o sistema.

## 8. APIs, contratos e integração
- **Fundamentos**
  - [ ] F1 · Como sistemas conversam (5): HTTP; REST; JSON; status codes; documentação.
  - [ ] Missão: projetar a API da cantina da escola.
- **Prática**
  - [ ] P1 · APIs bem projetadas (7): recursos e verbos; paginação e filtros; versionamento; idempotência e concorrência (ETag); gRPC; GraphQL; webhooks e eventos.
  - [ ] Missão: integrar com um parceiro sem quebrar clientes antigos.
- **Produção**
  - [ ] R1 · Contratos e governança (6): OpenAPI e contract testing; API gateway; limites e cotas; deprecação; segurança de APIs; observabilidade.
  - [ ] Missão: lançar a versão 2 de uma API pública.

## 9. Segurança de aplicações e identidade
- **Fundamentos**
  - [ ] F1 · Segurança no dia a dia (6): senhas e MFA; phishing; o que é um ataque web; autenticação × autorização; dados pessoais; atualizações.
  - [ ] Missão: proteger a conta da escola.
- **Prática**
  - [ ] P1 · OWASP na prática (8): injeção; XSS; CSRF; controle de acesso quebrado; SSRF; segredos no código; dependências vulneráveis; logs seguros.
  - [ ] P2 · Identidade (7): sessões e cookies; OAuth 2 e OIDC; JWT e seus riscos; RBAC e ABAC; autorização por recurso; identidade em cada stack; identidade gerenciada na nuvem.
  - [ ] Missão: auditar e corrigir uma aplicação vulnerável.
- **Produção**
  - [ ] R1 · Segurança contínua (7): modelagem de ameaças; SAST, DAST e SCA no CI; supply chain e SBOM; contêiner seguro; segurança de LLM; resposta a incidentes; LGPD.
  - [ ] Missão: plano de segurança para lançar um produto financeiro.

## 10. Arquitetura de software e DDD
- **Fundamentos**
  - [ ] F1 · Código que dura (6): nomes e funções; responsabilidade única; testes; Git; débito técnico; documentação.
  - [ ] Missão: limpar um código bagunçado sem quebrar nada.
- **Prática**
  - [ ] P1 · Princípios e padrões (7): SOLID; padrões de projeto úteis; camadas, hexagonal e clean; estrutura de pastas por stack; testes por camada; concorrência; refatoração.
  - [ ] P2 · DDD e descoberta (7): Event Storming; linguagem ubíqua; bounded contexts; context map; agregados; BDD; times e fronteiras.
  - [ ] Missão: modelar o domínio de crédito com Event Storming até o código.
- **Produção**
  - [ ] R1 · Arquitetura evolutiva (6): monólito modular; quando extrair serviços; ADRs e RFCs; fitness functions; governança leve; migração estrangulada.
  - [ ] Missão: plano de evolução de um monólito de 10 anos.

## 11. Observabilidade, performance e confiabilidade
- **Fundamentos**
  - [ ] F1 · Ver o que o sistema faz (5): logs; métricas; traces; alertas; painéis.
  - [ ] Missão: descobrir por que o site da escola ficou lento.
- **Prática**
  - [ ] P1 · OpenTelemetry e Prometheus (7): instrumentação; métricas RED e USE; PromQL; traces distribuídos; logs estruturados; correlação; painéis úteis.
  - [ ] P2 · Performance e carga (6): método de investigação; profiling; banco lento; cache; teste de carga; capacidade.
  - [ ] Missão: achar e corrigir um gargalo com dados, não com palpite.
- **Produção**
  - [ ] R1 · SRE (7): SLI, SLO e error budget; alertas que valem; on-call; postmortem sem culpa; caos controlado; custo de observabilidade; resiliência.
  - [ ] Missão: definir SLOs e on-call de um produto com 1 milhão de usuários.

## 12. Nuvem: Azure e AWS
- **Fundamentos**
  - [ ] F1 · O que é nuvem (6): IaaS, PaaS e SaaS; regiões e zonas; rede; identidade; armazenamento; custo.
  - [ ] Missão: escolher onde hospedar o site da escola.
- **Prática**
  - [ ] P1 · Azure no trabalho (7): assinaturas e governança; Entra ID e RBAC; VNets; App Service × Container Apps × AKS; storage; Key Vault; monitoramento.
  - [ ] P2 · AWS no trabalho (7): contas e Organizations; IAM; VPC; EC2 × Lambda × ECS × EKS; S3 e RDS; SQS e SNS; CloudWatch.
  - [ ] Missão: decidir e justificar onde roda cada parte de um sistema, com custo.
- **Produção**
  - [ ] R1 · Arquitetura de nuvem (7): bem-arquitetado (pilares); continuidade e DR; migração; segurança e conformidade; LGPD e residência de dados; FinOps; multi-nuvem com critério.
  - [ ] Missão: desenho de referência para uma fintech.
  - [ ] Preparatório: AZ-104, AZ-305 e AWS Solutions Architect Associate.

## 13. DevOps, IaC e Platform Engineering
- **Fundamentos**
  - [ ] F1 · Do código ao ar (5): versionamento; integração contínua; entrega contínua; ambientes; automação.
  - [ ] Missão: primeira esteira de um projeto escolar.
- **Prática**
  - [ ] P1 · Pipelines e Terraform (8): pipelines no GitHub Actions e no Azure DevOps; testes e qualidade na esteira; artefatos e versões; Terraform (estado, módulos, plan); ambientes e aprovações; segredos; deploy azul-verde e canário; feature flags.
  - [ ] Missão: infraestrutura de AKS e Event Hubs inteira em Terraform, com pipeline.
- **Produção**
  - [ ] R1 · Plataforma interna e FinOps (7): plataforma como produto; portal do desenvolvedor; golden paths; métricas DORA; FinOps (alocação, rightsizing, compromissos); segurança na esteira; governança.
  - [ ] Missão: plano de plataforma interna para 10 times.
  - [ ] Preparatório: AZ-400.

## 14. Node.js e TypeScript
- **Fundamentos**
  - [ ] F1 · JavaScript e TypeScript (6): tipos; funções; objetos; módulos; promises e async; erros.
  - [ ] Missão: um pequeno bot de tarefas.
- **Prática**
  - [ ] P1 · Backend com Node (8): event loop; HTTP e frameworks; validação; MongoDB e SQL; Redis; RabbitMQ; testes; Node × Deno × Bun.
  - [ ] Missão: API de pedidos com fila e cache.
- **Produção**
  - [ ] R1 · Node em produção (6): performance e memória; worker threads; observabilidade; segurança de dependências; contêiner; escala.
  - [ ] Missão: estabilizar uma API Node com vazamento de memória.

## 15. Python para backend e IA
- **Fundamentos**
  - [ ] F1 · Python do zero no navegador (Pyodide) (7): tipos; listas e dicionários; funções; arquivos; erros; bibliotecas; pequenos scripts úteis.
  - [ ] Missão: analisar as notas da turma.
- **Prática**
  - [ ] P1 · Backend e workers (7): ambientes e dependências; tipagem; asyncio; FastAPI; banco; testes; filas e workers.
  - [ ] Missão: API de IA com FastAPI e fila.
- **Produção**
  - [ ] R1 · Python em produção (5): empacotamento; concorrência e GIL; observabilidade; contêiner; desempenho.
  - [ ] Missão: levar um protótipo de notebook para produção.

## 16. Frontend
- **Fundamentos**
  - [ ] F1 · Como uma página nasce (6): HTML; CSS; JavaScript; o navegador por dentro; acessibilidade; responsivo.
  - [ ] Missão: a página da feira de ciências.
- **Prática**
  - [ ] P1 · React e Angular (8): componentes; estado; efeitos e dados; formulários; roteamento; Angular e injeção de dependência; testes; desempenho.
  - [ ] P2 · Renderização e Next.js (6): CSR, SSR, SSG e streaming; Server Components; cache; SEO; imagens; Web Vitals.
  - [ ] Missão: loja com carrinho, acessível e rápida no celular.
- **Produção**
  - [ ] R1 · Frontend em escala (7): design system; micro-frontends; estado global; observabilidade de frontend; segurança; IA na interface; contratos com o backend.
  - [ ] Missão: dividir um frontend gigante entre 5 times.

## 17. Dados e analytics
- **Fundamentos**
  - [ ] F1 · Perguntas com dados (5): tabelas; médias e distribuições; gráficos honestos; correlação × causa; amostra.
  - [ ] Missão: a pesquisa da escola.
- **Prática**
  - [ ] P1 · SQL analítico no navegador (DuckDB) (7): agregações; joins; janelas; modelagem dimensional; qualidade de dados; métricas de produto; testes A/B.
  - [ ] P2 · Engenharia de dados (7): ingestão; batch × streaming; lakehouse; orquestração; transformação; governança; Power BI e Fabric.
  - [ ] Missão: painel de métricas de um e-commerce com dados confiáveis.
- **Produção**
  - [ ] R1 · Plataforma de dados (6): custo; segurança e acesso; linhagem; LGPD; contratos de dados; monitoramento de pipelines.
  - [ ] Missão: plataforma de dados para 3 áreas da empresa.
  - [ ] Preparatório: DP-700 e PL-300.

## 18. Machine learning e deep learning
- **Fundamentos**
  - [ ] F1 · Como uma máquina aprende (6): exemplos e rótulos; treino e teste; erro; sobreajuste; classificação; viés.
  - [ ] Missão: classificador de frutas (com modelo real no navegador).
- **Prática**
  - [ ] P1 · ML clássico e redes (7): regressão; árvores; métricas; redes neurais; PyTorch; transformers; ajuste fino.
  - [ ] Missão: classificar tickets de atendimento e medir de verdade.
- **Produção**
  - [ ] R1 · ML em produção (6): modelos locais; quantização; voz; monitoramento de deriva; custo; responsabilidade.
  - [ ] Missão: levar um classificador para produção com monitoramento.

## 19. Tech Lead e gestão de times
- **Fundamentos**
  - [ ] F1 · Trabalhar em time (5): papéis; combinados; feedback; reuniões; pedir ajuda.
  - [ ] Missão: organizar um trabalho em grupo.
- **Prática**
  - [ ] P1 · Ser tech lead (8): transição; 1:1; feedback; decisões técnicas; decompor e estimar; caminho crítico; fluxo e WIP; stakeholders.
  - [ ] P2 · Gestão de projetos com IA (6): backlog; priorização; previsão; riscos; comunicação; automação.
  - [ ] Missão: conduzir um projeto atrasado de volta aos trilhos.
- **Produção**
  - [ ] R1 · Liderar vários times (6): estrutura de times; métricas sem tóxico; contratação; desempenho; crise; cultura.
  - [ ] Missão: liderar 3 times de 6 pessoas num trimestre crítico.

## 20. Staff Engineer e carreira técnica
- **Fundamentos**
  - [ ] F1 · Carreira em tecnologia (5): níveis; o que cada nível espera; portfólio; aprender a aprender; plano de estudos.
  - [ ] Missão: seu plano de 6 meses.
- **Prática**
  - [ ] P1 · Influência sem cargo (7): escrita técnica; RFC; decisões; estratégia técnica; projetos entre times; mentoria; promoção.
  - [ ] Missão: escrever e defender uma RFC.
- **Produção**
  - [ ] R1 · Staff no dia a dia (6): arquitetura evolutiva; plataforma; operação; pessoas; estratégia; roteiro de 24 meses.
  - [ ] Missão: estratégia técnica de 1 ano para uma área.

## 21. Algoritmos e entrevistas técnicas
- **Fundamentos**
  - [ ] F1 · Pensar como computador (6): passo a passo; Big O; listas; busca; ordenação; recursão.
  - [ ] Missão: o jogo de adivinhar o número.
- **Prática**
  - [ ] P1 · Padrões de algoritmo (8): hash; dois ponteiros e janela; pilha e busca binária; árvores; grafos; heap e union-find; backtracking; programação dinâmica.
  - [ ] P2 · Entrevistas (6): STAR; comportamental; pitch; vitrine; system design em entrevista; negociação.
  - [ ] Missão: loop de entrevista simulado.
- **Produção**
  - [ ] R1 · Algoritmos no mundo real (5): estruturas em bancos; filas de prioridade em sistemas; grafos em rotas; caching; trade-offs de memória.
  - [ ] Missão: escolher a estrutura certa para 3 problemas de produção.

## 22. Arquitetura SaaS multi-tenant
- **Fundamentos**: [ ] F1 · O que é SaaS (5): clientes, planos, isolamento, cobrança, suporte. · [ ] Missão: o SaaS da cantina.
- **Prática**: [ ] P1 · Construir multi-tenant (7): modelos de isolamento; contexto do tenant; onboarding; limites; billing; dados; enterprise (SSO). · [ ] Missão: transformar um sistema single-tenant em SaaS.
- **Produção**: [ ] R1 · Operar SaaS (6): vizinho barulhento; custo por tenant; migrações por tenant; SLAs; segurança; negócio. · [ ] Missão: SaaS com 500 clientes e 3 enterprise.

## 23. Redes, sistemas operacionais e concorrência
- **Fundamentos**: [ ] F1 · Por baixo do capô (6): processos; memória; arquivos; IP e DNS; TCP; HTTP. · [ ] Missão: o que acontece quando você digita uma URL.
- **Prática**: [ ] P1 · Concorrência e I/O (7): threads; locks; async e event loop; I/O bloqueante; TLS; HTTP/2 e 3; diagnóstico de rede. · [ ] Missão: corrigir uma condição de corrida.
- **Produção**: [ ] R1 · Diagnóstico em produção (5): latência de rede; limites do SO; conexões; contêineres e cgroups; ferramentas. · [ ] Missão: incidente de timeouts intermitentes.

## 24. Segurança em nuvem e SecOps
- **Fundamentos**: [ ] F1 · Defesa em camadas (5): identidade; rede; dados; monitoramento; resposta. · [ ] Missão: mapa de riscos da escola.
- **Prática**: [ ] P1 · Operação de segurança (7): Zero Trust; acesso condicional; privilégio mínimo; Defender e Sentinel; caça a ameaças; segurança de IA; postura. · [ ] Missão: investigar um incidente.
- **Produção**: [ ] R1 · Arquitetura de segurança (6): estratégia; governança e conformidade; SecOps; dados; infraestrutura; IA. · [ ] Missão: arquitetura de segurança de uma empresa de 500 pessoas. · [ ] Preparatório: SC-100, SC-200, SC-300 e SC-500.

## 25. Integrações de mercado
- **Fundamentos**: [ ] F1 · Automatizar o dia a dia (5): gatilhos; APIs; webhooks; planilhas; segurança. · [ ] Missão: automação da secretaria.
- **Prática**: [ ] P1 · Integrações reais (7): n8n; WhatsApp Business; pagamentos (Pix, cartão); identidade; analytics; busca; feature flags. · [ ] Missão: atendimento por WhatsApp com pagamento.
- **Produção**: [ ] R1 · Integrações confiáveis (5): retries e idempotência; limites; monitoramento; custo; LGPD. · [ ] Missão: integração que não perde pedido.

## 26. Negócios, produto e empreendedorismo
- **Fundamentos**: [ ] F1 · Como empresas ganham dinheiro (5): receita e custo; cliente; valor; preço; concorrência. · [ ] Missão: a lojinha da turma.
- **Prática**: [ ] P1 · Produto para engenheiros (7): descoberta; métricas; priorização; preço; vendas; contratos; estratégia. · [ ] Missão: validar uma ideia em 2 semanas.
- **Produção**: [ ] R1 · Criar sua empresa de tecnologia (6): nicho e oferta; validação; vendas; contratos; métricas; falar com a diretoria. · [ ] Missão: plano de negócios de um SaaS.

## 27. Telefonia e agentes de voz
- **Fundamentos**: [ ] F1 · Como a voz viaja (5): telefonia; VoIP; SIP; URA; filas. · [ ] Missão: a URA da escola.
- **Prática**: [ ] P1 · Asterisk e voz com IA (7): dialplan; URA e filas; interfaces (AMI e ARI); integração com CRM; gravação; transcrição real no navegador; agente de voz. · [ ] Missão: central de atendimento com agente de voz.
- **Produção**: [ ] R1 · Voz em escala (5): segurança e fraude; escala; qualidade; LGPD em gravações; custo. · [ ] Missão: central para 200 atendentes.

## 28. Projeto integrador
- [ ] Uma trilha única (8 lições): da ideia ao produto. Escopo; MVP; IA no produto; SaaS; operação; segurança; custo; apresentação.
- [ ] Missão: publicar um produto completo usando o que foi aprendido nos tópicos anteriores.

---

## Andamento

| Data | Etapa | Status |
| --- | --- | --- |
| nov/2026 | IA aplicada · Fundamentos F1 + missão | Publicada |
| nov/2026 | Plataforma · PL1 · tema escuro e catálogo de 28 tópicos | Publicada |
| nov/2026 | Plataforma · PL2 · modelo declarativo + 9 peças de cena reutilizáveis (galeria em /galeria) | Publicada |
| nov/2026 | Plataforma · PL3 · executores no navegador (Transformers.js 4.3.2, WebLLM 0.2.87) e sua chave (Anthropic, OpenAI, Gemini, compatível); ativos nos passos 2 e 4 dos Fundamentos | Publicada |
| nov/2026 | IA aplicada · Prática · P1 · 7 lições com modelos reais (tokenizador do GPT-4o, multilingual-e5-small, Llama 3.2 1B ou sua chave), todas só com dados | Publicada |
| nov/2026 | Contêineres e Kubernetes · Fundamentos F1 + missão (processo × contêiner × VM, imagem e camadas, Dockerfile, registro, por que orquestrar, cluster; missão do Dockerfile explicado linha a linha) | Publicada |
| nov/2026 | IA aplicada · Prática · missão final: assistente de RH da Aurora (limpeza, busca híbrida, limite, citação, recusa, triagem e avaliação em 13 perguntas) | Publicada |
| nov/2026 | IA aplicada · Prática · P3 · Prompts e agentes: 7 lições (prompt de sistema, few-shot, extração de notas, triagem, agente com limites, memória, MCP), com modo real por Llama 1B ou sua chave | Publicada |
| nov/2026 | Mensageria e streaming · Fundamentos F1 + missão (pizzaria: síncrono × assíncrono, comando × evento, ack, idempotência, ordem/DLQ/prefetch, pub/sub, quando não usar fila; missão Black Friday) | Publicada |
| nov/2026 | Desenvolvimento assistido por IA · Fundamentos F1 + missão (padaria Pão de Mel: autocompletar × chat × agente, contexto, especificação, revisão, quando não usar, ética e autoria; missão do bug 0,1 × 3) | Publicada |
| nov/2026 | IA aplicada · Prática · P2 · RAG de verdade: 8 lições sobre o manual da Aurora (BM25 real, embeddings e5 no navegador, reranker por LLM, citação e recusa, recall@k) | Publicada |

**Próxima etapa:** IA aplicada · Produção · R1 (Avaliação e qualidade).
