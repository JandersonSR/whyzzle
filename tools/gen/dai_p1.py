"""Dev assistido por IA · Prática P1 · Fluxo com agentes de código (7 lições).
Scenario: the Pão de Mel order app grew; now a real team: Bia (tech lead, Claude Code), Caio (junior dev, Copilot in
VS Code), Rafa (dev, Cursor) and Duda (product analyst who writes the issues). Repo: encomendas, suite of 140 tests.
Run: python3 tools/gen/dai_p1.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write as _write, flag, step

TOPIC, TRACK = 'dev-assistido-por-ia', 'pratica'
SUITE = 140  # testes da suíte do app de encomendas, igual em todas as lições


def write(folder, s, pt, en, teacher): _write(TOPIC, TRACK, folder, s, pt, en, teacher)
def opt(id, pt, en): return {'id': id, 'pt': pt, 'en': en}
def LQ(pt, en): return {'pt': pt, 'en': en}
def ex(*qs): return [LQ(p, e) for p, e in qs]
def mk(L):
    pt = L == 'pt'
    return pt, (lambda a, b: a if pt else b)
def yn(T, pt, en): return T(f'--{pt} aceita sim ou nao.', f'--{en} takes yes or no.')
def rnd(x): return int(x + 0.5)


# ====================================================================== 1 · especificação antes do código
SPEC_V = ('Quero que o cliente possa agendar a retirada da encomenda.', 'I want customers to be able to schedule their order pickup.')
SPEC_P = ('Agendar retirada: o cliente escolhe dia e horário. Critérios: entre 7h e 19h; no máximo 20 retiradas por hora.',
          'Schedule pickup: the customer picks a day and time. Criteria: between 7am and 7pm; at most 20 pickups per hour.')
SPEC_F = ('Agendar retirada. Critérios de aceite: 1) cliente escolhe dia e horário entre 7h e 19h; 2) no máximo 20 retiradas por hora; 3) agendamento até 2 dias antes; 4) o recibo mostra o horário. Fora do escopo: SMS, pagamento, tela de admin.',
          'Schedule pickup. Acceptance criteria: 1) customer picks a day and time between 7am and 7pm; 2) at most 20 pickups per hour; 3) booking up to 2 days ahead; 4) the receipt shows the time. Out of scope: SMS, payment, admin screen.')
# (nível da especificação, plano antes?) → o que acontece com o PR do agente
RUNS1 = {'vague0': {'lines': 640, 'files': 14, 'extras': 3, 'rounds': 4, 'reviewMin': 95, 'rework': 6.0},
         'vague1': {'lines': 260, 'files': 7, 'extras': 0, 'rounds': 2, 'reviewMin': 35, 'rework': 1.5},
         'partial0': {'lines': 310, 'files': 8, 'extras': 1, 'rounds': 2, 'reviewMin': 45, 'rework': 2.0},
         'partial1': {'lines': 210, 'files': 6, 'extras': 0, 'rounds': 1, 'reviewMin': 25, 'rework': 0.5},
         'full0': {'lines': 180, 'files': 5, 'extras': 0, 'rounds': 1, 'reviewMin': 20, 'rework': 0.0},
         'full1': {'lines': 180, 'files': 5, 'extras': 0, 'rounds': 1, 'reviewMin': 20, 'rework': 0.0}}
assert [k for k, v in RUNS1.items() if v['rounds'] >= 3] == ['vague0']  # só o pedido vago sem plano vira retrabalho

s1 = step('dai-p-especificacao-antes-do-codigo', 1, TRACK, 18, ['especificacao', 'criterios-de-aceite', 'plano', 'escopo'],
  ['dai-missao-bug-com-teste'], ['simulado', 'sua-chave'], LQ('especificar', 'specify'),
  {'name': 'text', 'required': False, 'ui': 'examples', 'default': ex(SPEC_F)[0], 'examples': ex(SPEC_F, SPEC_P, SPEC_V)},
  [flag('plan', 'plano', 'plan', 'bool', default=True, ui='switch')],
  {'options': ['smaller', 'same', 'bigger'], 'answer': 'smaller'}, 'rework',
  {'live': False,
   'consts': {'real': False, 'realFields': {}, 'realValid': False, 'critOf': {'vague': 0, 'partial': 2, 'full': 4}, 'runs': RUNS1},
   'compute': {
     'pk': "plan ? '1' : '0'",
     'known': "lookup(specs, text, '')",
     'hCrit': 'containsany(text, critWords)',
     'hScope': 'containsany(text, scopeWords)',
     'simLevel': "known != '' ? known : ((hCrit && hScope) ? 'full' : ((hCrit || hScope) ? 'partial' : 'vague'))",
     'rCrit': 'real && realValid ? number(realFields.criteria) : 0',
     'rScope': 'real && realValid ? realFields.out_of_scope == true : false',
     'level': "real ? (realValid ? ((rCrit >= 3 && rScope) ? 'full' : (rCrit >= 1 ? 'partial' : 'vague')) : 'vague') : simLevel",
     'nCrit': 'real ? rCrit : lookup(critOf, level, 0)',
     'run': 'lookup(runs, level + pk, runs.vague0)',
     'lines': 'run.lines', 'files': 'run.files', 'extras': 'run.extras', 'rounds': 'run.rounds', 'reviewMin': 'run.reviewMin',
     'reworkS': 'fmt(run.rework, 1, lang)',
     'rV': "lookup(runs, 'vague' + pk, runs.vague0)", 'rP': "lookup(runs, 'partial' + pk, runs.vague0)", 'rF': "lookup(runs, 'full' + pk, runs.vague0)",
     'levelName': "lookup(levelNames, level, '')",
     'planQ': "lookup(planQs, level, '')",
     'realQ': "real && realValid ? str(realFields.question) : ''"},
   'cases': [
     {'when': 'real && !realValid', 'flags': ['gradeBroken']},
     {'when': 'rounds >= 3', 'flags': ['rework']},
     {'when': 'extras > 0', 'flags': ['creep']},
     {'when': 'rounds == 1', 'flags': ['lean']},
     {'when': 'true', 'vars': {'lines': 'lines', 'files': 'files', 'extras': 'extras', 'rounds': 'rounds', 'reviewMin': 'reviewMin',
                               'reworkS': 'reworkS', 'crit': 'nCrit', 'levelName': 'levelName', 'planQ': 'planQ', 'realQ': 'realQ'}}],
   'widgets': [
     {'type': 'flow', 'steps': [
       {'label': '@sSpec', 'sub': '@subSpec', 'tone': "=level == 'full' ? 'ok' : (level == 'partial' ? 'warn' : 'bad')"},
       {'label': '@sPlan', 'sub': "=plan ? '@planOn' : '@planOff'", 'tone': "=plan ? 'info' : 'dim'"},
       {'label': '@sDiff', 'sub': '@subDiff', 'tone': "=extras > 0 ? 'bad' : 'ok'"},
       {'label': '@sReview', 'sub': '@subReview', 'tone': "=rounds >= 3 ? 'bad' : (rounds == 2 ? 'warn' : 'ok')"}]},
     {'type': 'metrics', 'items': [
       {'label': '@mLines', 'value': '=lines', 'format': 'int', 'tone': "=lines > 400 ? 'bad' : (lines > 250 ? 'warn' : 'ok')"},
       {'label': '@mExtras', 'value': '=extras', 'format': 'int', 'tone': "=extras > 0 ? 'bad' : 'ok'"},
       {'label': '@mRounds', 'value': '=rounds', 'format': 'int', 'tone': "=rounds >= 3 ? 'bad' : (rounds == 2 ? 'warn' : 'ok')"},
       {'label': '@mReview', 'value': '=reviewMin', 'format': 'min', 'tone': 'info'},
       {'label': '@mRework', 'value': "=reworkS + ' h'", 'tone': "=run.rework > 0 ? 'warn' : 'ok'"}]},
     {'type': 'table', 'label': '@table', 'columns': ['@colSpec', '@colLines', '@colRounds', '@colReview'],
      'rows': [['@lvVague', '=rV.lines', '=rV.rounds', '=rV.reviewMin'], ['@lvPartial', '=rP.lines', '=rP.rounds', '=rP.reviewMin'],
               ['@lvFull', '=rF.lines', '=rF.rounds', '=rF.reviewMin']],
      'tones': ["=level == 'vague' ? 'bad' : 'dim'", "=level == 'partial' ? 'warn' : 'dim'", "=level == 'full' ? 'ok' : 'dim'"],
      'caption': "=plan ? '@capPlan' : '@capNoPlan'"},
     {'type': 'note', 'when': '=extras > 0', 'tone': 'bad', 'text': '@creepNote'},
     {'type': 'note', 'when': '=plan && !real', 'tone': 'info', 'text': '@planNote'},
     {'type': 'note', 'when': '=real && realValid', 'tone': 'info', 'text': '@realNote'},
     {'type': 'note', 'when': '=real && !realValid', 'tone': 'warn', 'text': '@brokenNote'},
     {'type': 'note', 'when': '=!real', 'tone': 'dim', 'text': '@simNote'}]},
  {'sua-chave': {'adapter': 'declarative', 'op': 'json',
                 'args': {'system': '{gradeSystem}', 'user': '{text}',
                          'schema': {'criteria': 'number', 'out_of_scope': 'boolean', 'question': 'string'}}}})

def loc1(L):
  pt, T = mk(L)
  i = 0 if pt else 1
  return {
  'title': T('Especificação antes do código', 'Spec before code'),
  'subtitle': T('Critérios de aceite e "fora do escopo" encolhem o diff do agente', 'Acceptance criteria and "out of scope" shrink the agent’s diff'),
  'mission': T('O app de encomendas da Pão de Mel virou coisa séria: agora são três lojas e um time de verdade. A Duda (analista de produto) escreve as issues, a Bia (tech lead) entrega para o agente de código e revisa o PR. A próxima feature é agendar a retirada. Compare três especificações da mesma feature e veja o que o agente faz com cada uma.',
               'The Pão de Mel order app got serious: three shops now, and a real team. Duda (product analyst) writes the issues, Bia (tech lead) hands them to the coding agent and reviews the PR. Next feature: scheduling pickups. Compare three specs of the same feature and see what the agent does with each one.'),
  'predict': {'question': T('mesma feature, especificação completa (4 critérios de aceite + fora do escopo). Comparado ao pedido vago, o diff do agente fica…', 'same feature, full spec (4 acceptance criteria + out of scope). Compared with the vague request, the agent’s diff is…'),
    'options': {'smaller': T('Menor: o agente faz só o que foi pedido', 'Smaller: the agent does only what was asked'),
                'same': T('Igual: a feature é a mesma', 'The same: it’s the same feature'),
                'bigger': T('Maior: mais detalhe vira mais código', 'Bigger: more detail means more code')}},
  'feedback': {'right': T('isso: 180 linhas contra 640. Com o pedido vago o agente "completou" a feature com SMS, um campo novo no banco e uma tela de admin que ninguém pediu. Especificação boa encolhe o diff.', 'right: 180 lines against 640. With the vague request the agent "completed" the feature with SMS, a new database column and an admin screen nobody asked for. A good spec shrinks the diff.'),
    'wrong': T('olha a tabela: 180 linhas com a especificação completa, 640 com o pedido vago. Lacuna na especificação o agente preenche com código, e geralmente com mais código do que você queria.', 'look at the table: 180 lines with the full spec, 640 with the vague request. The agent fills gaps in the spec with code, usually more code than you wanted.'),
    'skipped': T('sem palpite, tudo bem. A tabela compara as três especificações: repare quem gera o menor diff.', 'no guess, that’s fine. The table compares the three specs: notice which one produces the smallest diff.')},
  'coach': {'ui': T('palpite anotado. Rode com a especificação completa e depois troque para as outras duas.', 'guess noted. Run with the full spec, then switch to the other two.'),
            'cmd': T('palpite anotado. Rode como está e depois troque o texto pelos outros exemplos.', 'guess noted. Run it as is, then swap the text for the other examples.')},
  'tryNext': {'ui': T('Agora escolha o pedido vago e deixe o plano ligado: o agente faz perguntas antes de codar, e as respostas da Bia viram a especificação que faltava.', 'Now pick the vague request and keep the plan on: the agent asks questions before coding, and Bia’s answers become the missing spec.'),
              'cmd': T(f'Rode especificar "{SPEC_V[0]}" --plano sim e compare com --plano nao.', f'Run specify "{SPEC_V[1]}" --plan yes and compare with --plan no.')},
  'why': {
    'simples': T('Pedir "faz um bolo de aniversário" para a confeitaria rende um bolo de três andares, com vela, glacê e nome escrito. Você queria um bolo simples para 10 pessoas.\nQuem recebe um pedido vago não faz menos: faz o que imagina que você quer. Escrever antes o que é "pronto" (e o que não entra) economiza o bolo errado.',
                 'Ask a bakery for "a birthday cake" and you get three tiers, candles, frosting and a name on top. You wanted a simple cake for 10 people.\nWhoever gets a vague order doesn’t do less: they do what they imagine you want. Writing down first what "done" means (and what’s out) saves you the wrong cake.'),
    'dev': T('Uma boa issue para agente tem: objetivo em uma frase, critérios de aceite verificáveis (números, limites, mensagens), o que fica fora do escopo e como verificar (comando de teste). Cada critério vira um teste; "fora do escopo" corta as invenções.\nAntes de deixar o agente editar, peça um plano: no Claude Code, `claude --permission-mode plan` (ou Shift+Tab até aparecer "plan mode on") faz ele ler e propor sem tocar no disco; no Cursor, o Plan Mode também abre com Shift+Tab. No GitHub, você pode atribuir a issue ao Copilot: o texto da issue é a especificação que ele recebe.',
           'A good issue for an agent has: the goal in one sentence, verifiable acceptance criteria (numbers, limits, messages), what’s out of scope and how to verify (test command). Each criterion becomes a test; "out of scope" cuts the inventions.\nBefore letting the agent edit, ask for a plan: in Claude Code, `claude --permission-mode plan` (or Shift+Tab until "plan mode on" shows) makes it read and propose without touching disk; in Cursor, Plan Mode also opens with Shift+Tab. On GitHub you can assign the issue to Copilot: the issue text is the spec it gets.'),
    'especialista': T('O plano é uma especificação barata escrita "ao contrário": o agente mostra o que entendeu, e corrigir um parágrafo custa minutos, enquanto corrigir 640 linhas custa horas e rodadas de revisão. Por isso o pedido vago com plano já fica perto do pedido parcial.\nEm times, vale ter um modelo de issue com seções fixas (Objetivo, Critérios de aceite, Fora do escopo, Como verificar) e um verificador automático que reclama de issue sem critérios antes de ela chegar ao agente. Os números desta lição são de um cenário inventado, mas a direção (escopo aberto → diff maior → mais revisão) é o que times relatam.',
                      'A plan is a cheap spec written "backwards": the agent shows what it understood, and fixing a paragraph takes minutes, while fixing 640 lines takes hours and review rounds. That’s why the vague request with a plan already lands close to the partial one.\nIn teams it pays to have an issue template with fixed sections (Goal, Acceptance criteria, Out of scope, How to verify) and an automatic checker that complains about issues without criteria before they reach the agent. This lesson’s numbers come from a made-up scenario, but the direction (open scope → bigger diff → more review) is what teams report.')},
  'break': {'mission': {'ui': T('hora de quebrar: escolha o pedido vago e desligue o plano.', 'time to break it: pick the vague request and turn the plan off.'),
                        'cmd': T(f'hora de quebrar: rode especificar "{SPEC_V[0]}" --plano nao', f'time to break it: run specify "{SPEC_V[1]}" --plan no')},
    'success': T('Quebrou: sem critérios e sem plano, o agente entregou {lines} linhas em {files} arquivos, com {extras} coisas que ninguém pediu, e o PR precisou de {rounds} rodadas de revisão ({reworkS} h de retrabalho). O agente não errou o código: errou o pedido, porque ninguém disse qual era.',
                 'Broken: with no criteria and no plan, the agent delivered {lines} lines in {files} files, with {extras} things nobody asked for, and the PR needed {rounds} review rounds ({reworkS} h of rework). The agent didn’t get the code wrong: it got the request wrong, because nobody said what it was.'),
    'calm': T('Especificação "{levelName}": {lines} linhas, {rounds} rodada(s) de revisão, {reworkS} h de retrabalho. Para quebrar, use o pedido vago sem plano.',
              '"{levelName}" spec: {lines} lines, {rounds} review round(s), {reworkS} h of rework. To break it, use the vague request with no plan.')},
  'hints': {'ui': T(['Escolha uma especificação e rode; a tabela compara as três.', 'O plano faz o agente perguntar antes de codar. Veja o que acontece com o pedido vago com e sem ele.', 'Pedido vago + plano desligado.'],
                    ['Pick a spec and run; the table compares all three.', 'The plan makes the agent ask before coding. See what happens to the vague request with and without it.', 'Vague request + plan off.']),
            'cmd': T(['A especificação vai entre aspas depois de especificar.', '--plano aceita sim ou nao.', f'especificar "{SPEC_V[0]}" --plano nao'],
                     ['The spec goes in quotes after specify.', '--plan takes yes or no.', f'specify "{SPEC_V[1]}" --plan no'])},
  'errors': {'notBool.plan': yn(T, 'plano', 'plan'), 'missingArg': T('Faltou a especificação entre aspas.', 'The spec is missing, in quotes.')},
  'controls': {'arg': T('Especificação da Duda', 'Duda’s spec'), 'plan': T('Pedir um plano antes de editar', 'Ask for a plan before editing')},
  'scene': {'label': T('Da issue ao PR', 'From issue to PR'), 'empty': T('Rode para ver o PR que o agente entrega.', 'Run to see the PR the agent delivers.'),
    'sSpec': T('Especificação', 'Spec'), 'subSpec': T('{levelName}: {crit} critério(s)', '{levelName}: {crit} criteria'),
    'sPlan': T('Plano', 'Plan'), 'planOn': T('agente propõe, Bia aprova', 'agent proposes, Bia approves'), 'planOff': T('direto para o código', 'straight to code'),
    'sDiff': T('Diff do agente', 'Agent’s diff'), 'subDiff': T('{lines} linhas, {files} arquivos', '{lines} lines, {files} files'),
    'sReview': T('Revisão', 'Review'), 'subReview': T('{rounds} rodada(s)', '{rounds} round(s)'),
    'mLines': T('linhas no diff', 'lines in the diff'), 'mExtras': T('coisas não pedidas', 'unrequested things'), 'mRounds': T('rodadas de revisão', 'review rounds'),
    'mReview': T('minutos de revisão', 'review minutes'), 'mRework': T('retrabalho', 'rework'),
    'table': T('As três especificações', 'The three specs'), 'colSpec': T('especificação', 'spec'), 'colLines': T('linhas', 'lines'), 'colRounds': T('rodadas', 'rounds'), 'colReview': T('min de revisão', 'review min'),
    'lvVague': T('vaga (0 critérios)', 'vague (0 criteria)'), 'lvPartial': T('parcial (2 critérios)', 'partial (2 criteria)'), 'lvFull': T('completa (4 + fora do escopo)', 'full (4 + out of scope)'),
    'capPlan': T('Com plano antes de editar. Cenário inventado, números fixos.', 'With a plan before editing. Made-up scenario, fixed numbers.'),
    'capNoPlan': T('Sem plano: o agente vai direto ao código. Cenário inventado.', 'No plan: the agent goes straight to code. Made-up scenario.'),
    'creepNote': T('{extras} coisa(s) fora do pedido: SMS de lembrete, campo novo no banco, tela de admin. Cada uma é código para revisar, testar e manter.', '{extras} thing(s) beyond the request: reminder SMS, a new database column, an admin screen. Each one is code to review, test and maintain.'),
    'planNote': T('No plano, o agente pergunta: "{planQ}"', 'In the plan, the agent asks: "{planQ}"'),
    'realNote': T('Seu modelo contou {crit} critério(s) de aceite e perguntaria: "{realQ}"', 'Your model counted {crit} acceptance criteria and would ask: "{realQ}"'),
    'brokenNote': T('O modelo não devolveu o JSON pedido ({"criteria", "out_of_scope", "question"}); a lição tratou como especificação vaga.', 'The model didn’t return the requested JSON ({"criteria", "out_of_scope", "question"}); the lesson treated it as a vague spec.'),
    'simNote': T('No modo simulado, um texto seu vira "completa" se tiver critérios e fora do escopo, "parcial" se tiver um dos dois. Com a sua chave, um modelo de verdade avalia.', 'In simulated mode, your own text counts as "full" if it has criteria and out of scope, "partial" if it has one of them. With your key, a real model grades it.')},
  'data': {'specs': {SPEC_V[i]: 'vague', SPEC_P[i]: 'partial', SPEC_F[i]: 'full'},
           'critWords': T(['critério', 'criterio', 'aceite', 'dado que'], ['criteria', 'criterion', 'acceptance', 'given ']),
           'scopeWords': T(['fora do escopo', 'não inclui', 'nao inclui'], ['out of scope', 'not included', 'does not include']),
           'levelNames': {'vague': T('vaga', 'vague'), 'partial': T('parcial', 'partial'), 'full': T('completa', 'full')},
           'planQs': {'vague': T('Que horários a loja aceita? Tem limite por hora? Precisa avisar o cliente por SMS? Quem altera agendamentos?', 'What times does the shop take? Is there a per-hour limit? Should the customer get an SMS? Who changes bookings?'),
                      'partial': T('Até quantos dias antes dá para agendar? O horário aparece no recibo?', 'How many days ahead can people book? Does the time show on the receipt?'),
                      'full': T('Nenhuma dúvida: o plano lista um teste por critério e não toca em SMS, pagamento nem admin.', 'No questions: the plan lists one test per criterion and doesn’t touch SMS, payment or admin.')},
           'gradeSystem': T('Você avalia especificações de tarefas para um agente de código. Leia a especificação e responda só com JSON: {"criteria": número de critérios de aceite verificáveis (com números ou resultados observáveis), "out_of_scope": true se ela diz o que fica fora do escopo, "question": a pergunta mais importante que você faria antes de programar}.',
                            'You grade task specs for a coding agent. Read the spec and reply with JSON only: {"criteria": number of verifiable acceptance criteria (with numbers or observable results), "out_of_scope": true if it says what is out of scope, "question": the most important question you would ask before coding}.')},
  'recipe': {'steps': T([
      'Crie docs/specs/agendar-retirada.md no seu projeto (troque a feature pela sua):\n# Agendar retirada\n## Critérios de aceite\n- [ ] Cliente escolhe dia e horário entre 7h e 19h\n- [ ] No máximo 20 retiradas por hora\n- [ ] Agendamento até 2 dias antes\n- [ ] O recibo mostra o horário\n## Fora do escopo\n- SMS, pagamento, tela de admin\n## Como verificar\n- npm test',
      'Peça um plano antes de qualquer edição. No Claude Code:\nclaude --permission-mode plan\nDepois digite: Leia docs/specs/agendar-retirada.md e proponha um plano com os arquivos que vai mudar e um teste por critério. Nada fora do escopo.\nNo Cursor, use o Plan Mode (Shift+Tab no campo do Agent). No Copilot, peça o plano no chat antes de trocar para o modo agente.',
      'Confira o plano contra a lista: cada critério tem um teste? Algum item fala de SMS, pagamento ou admin? Corrija o plano, aprove e, no fim, rode:\ngit diff --stat'],
     ['Create docs/specs/schedule-pickup.md in your project (swap the feature for yours):\n# Schedule pickup\n## Acceptance criteria\n- [ ] Customer picks a day and time between 7am and 7pm\n- [ ] At most 20 pickups per hour\n- [ ] Booking up to 2 days ahead\n- [ ] The receipt shows the time\n## Out of scope\n- SMS, payment, admin screen\n## How to verify\n- npm test',
      'Ask for a plan before any edit. In Claude Code:\nclaude --permission-mode plan\nThen type: Read docs/specs/schedule-pickup.md and propose a plan with the files you will change and one test per criterion. Nothing out of scope.\nIn Cursor, use Plan Mode (Shift+Tab in the Agent input). In Copilot, ask for the plan in chat before switching to agent mode.',
      'Check the plan against the list: does each criterion have a test? Does any item mention SMS, payment or admin? Fix the plan, approve it and, at the end, run:\ngit diff --stat']),
    'ok': T('o plano tem um teste por critério e não cita SMS, pagamento nem admin, e o git diff --stat lista só os arquivos que estavam no plano.', 'the plan has one test per criterion and doesn’t mention SMS, payment or admin, and git diff --stat lists only the files that were in the plan.')}}

t1 = {'pt': {'objectives': ['Escrever critérios de aceite verificáveis e uma seção "fora do escopo".', 'Pedir um plano ao agente antes de deixá-lo editar.', 'Relacionar especificação vaga com diff maior e mais revisão.'], 'minutes': 25,
  'activity': 'Cada dupla recebe uma issue vaga do próprio sistema da empresa (ou da padaria) e reescreve com 3 a 5 critérios de aceite e um "fora do escopo". Depois trocam as issues e cada dupla tenta achar um jeito de "cumprir" a issue do outro fazendo algo que ninguém queria.',
  'discussion': ['Que perguntas o agente fez no plano que a issue já devia responder?', 'Quem deve escrever os critérios: produto, dev ou os dois juntos?'],
  'misconceptions': ['"Especificar é burocracia; o agente é rápido, depois a gente ajusta." Cada lacuna vira código, e código a mais custa revisão e manutenção.', '"Mais detalhe gera mais código." O detalhe certo (limites e fora do escopo) corta código.']},
 'en': {'objectives': ['Write verifiable acceptance criteria and an "out of scope" section.', 'Ask the agent for a plan before letting it edit.', 'Connect vague specs with bigger diffs and more review.'], 'minutes': 25,
  'activity': 'Each pair gets a vague issue from the company’s own system (or the bakery’s) and rewrites it with 3 to 5 acceptance criteria and an "out of scope". Then pairs swap issues and each tries to find a way to "meet" the other’s issue by doing something nobody wanted.',
  'discussion': ['Which questions did the agent ask in the plan that the issue should already answer?', 'Who should write the criteria: product, dev or both together?'],
  'misconceptions': ['"Specs are red tape; the agent is fast, we’ll adjust later." Every gap becomes code, and extra code costs review and maintenance.', '"More detail produces more code." The right detail (limits and out of scope) cuts code.']}}
write('01-especificacao-antes-do-codigo', s1, loc1('pt'), loc1('en'), t1)


# ====================================================================== 2 · arquivos de regras do repositório
FILES2 = [opt('agents', 'agents-md', 'agents-md'), opt('claude', 'claude-md', 'claude-md'),
          opt('copilot', 'copilot-instructions', 'copilot-instructions'), opt('cursor', 'cursor-rules', 'cursor-rules')]
Q2 = [('Em que unidade guardamos os preços?', 'What unit do we store prices in?'),
      ('Qual comando roda os testes?', 'Which command runs the tests?'),
      ('Posso editar uma migration antiga?', 'Can I edit an old migration?')]

s2 = step('dai-p-arquivos-de-regras', 2, TRACK, 18, ['agents-md', 'claude-md', 'copilot-instructions', 'cursor-rules', 'contexto'],
  ['dai-p-especificacao-antes-do-codigo'], ['simulado'], LQ('regras', 'rules'),
  {'name': 'text', 'required': False, 'ui': 'examples', 'default': ex(Q2[0])[0], 'examples': ex(*Q2)},
  [flag('files', 'arquivos', 'files', 'list', options=FILES2, default=['agents', 'claude'], ui='checkboxes'),
   flag('size', 'linhas', 'lines', 'int', min=5, max=1000, default=60, ui='slider')],
  {'options': ['direct', 'import', 'never'], 'answer': 'import'}, 'blind',
  {'live': True,
   'consts': {'toolNames': ['Claude Code', 'Copilot', 'Cursor']},
   'compute': {
     'hasA': "includes(files, 'agents')", 'hasC': "includes(files, 'claude')", 'hasP': "includes(files, 'copilot')", 'hasR': "includes(files, 'cursor')",
     'seeC': 'hasC && hasA', 'seeP': 'hasP || hasA', 'seeR': 'hasR || hasA',
     'nSee': '(seeC ? 1 : 0) + (seeP ? 1 : 0) + (seeR ? 1 : 0)',
     'blindNames': 'join(maskfilter(toolNames, [!seeC, !seeP, !seeR]), ", ")',
     'copies': '(hasA ? 1 : 0) + (hasP ? 1 : 0) + (hasR ? 1 : 0)',
     'adh': 'size <= 200 ? 95 : (size <= 500 ? 80 : 60)',
     'ans': 'lookup(answers, text, answersFallback)',
     'viaC': "seeC ? '@viaImport' : (hasC ? '@viaDangling' : (hasA ? '@viaNotRead' : '@viaNone'))",
     'viaP': "hasP && hasA ? '@viaBoth' : (hasP ? '@viaCopilotFile' : (hasA ? '@viaAgents' : '@viaNone'))",
     'viaR': "hasR && hasA ? '@viaBoth' : (hasR ? '@viaCursorFile' : (hasA ? '@viaAgents' : '@viaNone'))"},
   'cases': [
     {'when': 'nSee < 3', 'flags': ['blind']},
     {'when': 'nSee == 3', 'flags': ['allSee']},
     {'when': 'copies >= 2', 'flags': ['drift']},
     {'when': 'size > 200', 'flags': ['long']},
     {'when': 'true', 'vars': {'nSee': 'nSee', 'blindNames': 'blindNames', 'copies': 'copies', 'adh': 'adh', 'size': 'size', 'rightAns': 'ans.right', 'wrongAns': 'ans.wrong'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@mSee', 'value': "=nSee + ' / 3'", 'tone': "=nSee == 3 ? 'ok' : 'bad'"},
       {'label': '@mCopies', 'value': '=copies', 'format': 'int', 'tone': "=copies >= 2 ? 'warn' : (copies == 1 ? 'ok' : 'bad')"},
       {'label': '@mAdh', 'value': '=adh', 'format': 'pct', 'tone': "=adh >= 90 ? 'ok' : (adh >= 80 ? 'warn' : 'bad')"}]},
     {'type': 'table', 'label': '@table', 'columns': ['@colTool', '@colReads', '@colAnswer'],
      'rows': [['@tClaude', '=viaC', "=seeC ? ans.right : ans.wrong"], ['@tCopilot', '=viaP', "=seeP ? ans.right : ans.wrong"],
               ['@tCursor', '=viaR', "=seeR ? ans.right : ans.wrong"]],
      'tones': ["=seeC ? 'ok' : 'bad'", "=seeP ? 'ok' : 'bad'", "=seeR ? 'ok' : 'bad'"], 'caption': '@caption'},
     {'type': 'note', 'when': '=nSee < 3', 'tone': 'bad', 'text': '@blindNote'},
     {'type': 'note', 'when': "=hasC && !hasA", 'tone': 'warn', 'text': '@danglingNote'},
     {'type': 'note', 'when': '=copies >= 2', 'tone': 'warn', 'text': '@driftNote'},
     {'type': 'note', 'when': '=size > 200', 'tone': 'warn', 'text': '@longNote'},
     {'type': 'note', 'when': '=nSee == 3 && copies == 1 && size <= 200', 'tone': 'ok', 'text': '@okNote'}]})

def loc2(L):
  pt, T = mk(L)
  i = 0 if pt else 1
  answers = {Q2[0][i]: {'right': T('centavos, inteiros (regra)', 'cents, integers (rule)'), 'wrong': T('reais com decimal (chute)', 'reais as decimals (guess)')},
             Q2[1][i]: {'right': 'npm test', 'wrong': T('npx jest (chute)', 'npx jest (guess)')},
             Q2[2][i]: {'right': T('não: crie uma nova (regra)', 'no: create a new one (rule)'), 'wrong': T('pode, é só editar (chute)', 'sure, just edit it (guess)')}}
  return {
  'title': T('Arquivos de regras do repositório', 'Repository rules files'),
  'subtitle': T('AGENTS.md, CLAUDE.md, copilot-instructions e .cursor/rules: quem lê o quê', 'AGENTS.md, CLAUDE.md, copilot-instructions and .cursor/rules: who reads what'),
  'mission': T('Cada pessoa do time usa um agente: a Bia usa Claude Code, o Caio usa Copilot no VS Code e o Rafa usa Cursor. A regra mais importante do repositório é "preço sempre em centavos". Escolha quais arquivos de regras existem no repositório e descubra se os três agentes enxergam essa regra.',
               'Everyone on the team uses an agent: Bia uses Claude Code, Caio uses Copilot in VS Code and Rafa uses Cursor. The repo’s most important rule is "prices always in cents". Choose which rules files exist in the repository and find out whether all three agents see that rule.'),
  'predict': {'question': T('o repositório tem AGENTS.md e um CLAUDE.md com uma linha só: @AGENTS.md. Como o Claude Code da Bia chega nas regras?', 'the repo has AGENTS.md and a CLAUDE.md with a single line: @AGENTS.md. How does Bia’s Claude Code get to the rules?'),
    'options': {'direct': T('Lê o AGENTS.md direto, como as outras ferramentas', 'It reads AGENTS.md directly, like the other tools'),
                'import': T('Lê o CLAUDE.md, que importa o AGENTS.md', 'It reads CLAUDE.md, which imports AGENTS.md'),
                'never': T('Não chega: o Claude Code ignora AGENTS.md', 'It doesn’t: Claude Code ignores AGENTS.md')}},
  'feedback': {'right': T('isso. A documentação do Claude Code é direta: ele lê CLAUDE.md, não AGENTS.md. O jeito recomendado é um CLAUDE.md com @AGENTS.md, que puxa o conteúdo para dentro. Copilot e Cursor leem o AGENTS.md sozinhos.', 'right. Claude Code’s docs are blunt: it reads CLAUDE.md, not AGENTS.md. The recommended way is a CLAUDE.md with @AGENTS.md, which pulls the content in. Copilot and Cursor read AGENTS.md by themselves.'),
    'wrong': T('o Claude Code lê CLAUDE.md, não AGENTS.md. A linha @AGENTS.md dentro do CLAUDE.md é um import: o conteúdo do AGENTS.md entra junto. Sem esse CLAUDE.md, o agente da Bia fica sem regra nenhuma.', 'Claude Code reads CLAUDE.md, not AGENTS.md. The @AGENTS.md line inside CLAUDE.md is an import: AGENTS.md’s content comes along. Without that CLAUDE.md, Bia’s agent has no rules at all.'),
    'skipped': T('sem palpite? Olha a primeira linha da tabela: o caminho que a regra faz até o Claude Code.', 'no guess? Look at the table’s first row: the path the rule takes to Claude Code.')},
  'coach': {'ui': T('palpite anotado. Rode com AGENTS.md + CLAUDE.md e depois desmarque o CLAUDE.md.', 'guess noted. Run with AGENTS.md + CLAUDE.md, then untick CLAUDE.md.'),
            'cmd': T('palpite anotado. Rode como está e depois tente --arquivos agents-md sozinho.', 'guess noted. Run it as is, then try --files agents-md alone.')},
  'tryNext': {'ui': T('Agora marque também copilot-instructions e cursor-rules: todo mundo enxerga, mas a regra passa a morar em três lugares. Em três meses, alguém atualiza só um.', 'Now also tick copilot-instructions and cursor-rules: everyone sees it, but the rule now lives in three places. In three months, someone updates just one.'),
              'cmd': T('Rode regras --arquivos agents-md,claude-md,copilot-instructions,cursor-rules e olhe as cópias.', 'Run rules --files agents-md,claude-md,copilot-instructions,cursor-rules and look at the copies.')},
  'why': {
    'simples': T('Imagine o caderno de receitas da padaria. Se cada confeiteiro tem o seu, cada bolo sai de um jeito. Se existe um caderno só, na bancada, e cada um sabe onde ele fica, todo mundo faz o mesmo bolo.\nArquivo de regras é esse caderno para os agentes. O truque é que cada agente procura o caderno num lugar diferente.',
                 'Picture the bakery’s recipe book. If each baker has their own, every cake comes out different. If there’s one book on the counter and everybody knows where it is, everyone bakes the same cake.\nA rules file is that book for agents. The catch is that each agent looks for the book in a different place.'),
    'dev': T('Onde cada um procura (documentação oficial atual):\n• Claude Code: CLAUDE.md (ou .claude/CLAUDE.md) e .claude/rules/*.md. Ele não lê AGENTS.md; use um CLAUDE.md com @AGENTS.md (ou um link simbólico). /memory mostra o que foi carregado e /init gera um CLAUDE.md inicial.\n• Copilot: .github/copilot-instructions.md para o repositório todo, .github/instructions/NOME.instructions.md com applyTo para caminhos, e AGENTS.md para os agentes (o agente na nuvem também aceita CLAUDE.md).\n• Cursor: .cursor/rules/*.mdc (frontmatter com description, globs e alwaysApply) e AGENTS.md na raiz e em subpastas.\nUm AGENTS.md como fonte única, mais um CLAUDE.md que o importa, cobre os três.',
           'Where each one looks (current official docs):\n• Claude Code: CLAUDE.md (or .claude/CLAUDE.md) and .claude/rules/*.md. It doesn’t read AGENTS.md; use a CLAUDE.md with @AGENTS.md (or a symlink). /memory shows what was loaded and /init generates a starting CLAUDE.md.\n• Copilot: .github/copilot-instructions.md for the whole repo, .github/instructions/NAME.instructions.md with applyTo for paths, and AGENTS.md for agents (the cloud agent also accepts CLAUDE.md).\n• Cursor: .cursor/rules/*.mdc (frontmatter with description, globs and alwaysApply) and AGENTS.md at the root and in subfolders.\nOne AGENTS.md as the single source, plus a CLAUDE.md that imports it, covers all three.'),
    'especialista': T('Tamanho importa: a documentação do Claude Code recomenda menos de 200 linhas por CLAUDE.md (arquivo longo gasta contexto e reduz a adesão, e ele é carregado inteiro mesmo assim); a do Cursor fala em regras abaixo de 500 linhas, quebradas em regras menores. A porcentagem de "adesão" desta lição é de brinquedo.\nRegras por caminho evitam o arquivo gigante: paths: em .claude/rules, applyTo no Copilot, globs no Cursor, e AGENTS.md aninhado (no Copilot, o mais próximo na árvore tem precedência). E lembre: regra em arquivo é contexto, não trava. O que não pode falhar vira teste, hook ou checagem no CI.',
                      'Size matters: Claude Code’s docs recommend under 200 lines per CLAUDE.md (a long file uses context and lowers adherence, and it’s loaded in full anyway); Cursor’s docs say keep rules under 500 lines, split into smaller ones. This lesson’s "adherence" percentage is a toy.\nPath-scoped rules avoid the giant file: paths: in .claude/rules, applyTo in Copilot, globs in Cursor, and nested AGENTS.md (in Copilot, the nearest one in the tree takes precedence). And remember: a rule in a file is context, not a lock. Whatever must not fail becomes a test, a hook or a CI check.')},
  'break': {'mission': {'ui': T('hora de quebrar: deixe marcado só o agents-md.', 'time to break it: leave only agents-md ticked.'),
                        'cmd': T(f'hora de quebrar: rode regras "{Q2[0][0]}" --arquivos agents-md', f'time to break it: run rules "{Q2[0][1]}" --files agents-md')},
    'success': T('Quebrou: só {nSee} de 3 agentes enxergam as regras. {blindNames} trabalhou sem caderno e respondeu "{wrongAns}". É assim que aparece um preço em reais com vírgula num sistema todo em centavos.',
                 'Broken: only {nSee} of 3 agents see the rules. {blindNames} worked without the book and answered "{wrongAns}". That’s how a price in reais with decimals shows up in a system that’s all cents.'),
    'calm': T('Os 3 agentes enxergam as regras e respondem "{rightAns}", com a regra escrita em {copies} lugar(es). Para quebrar, deixe um agente sem o arquivo que ele lê.',
              'All 3 agents see the rules and answer "{rightAns}", with the rule written in {copies} place(s). To break it, leave one agent without the file it reads.')},
  'hints': {'ui': T(['Marque e desmarque arquivos; a tabela mostra o que cada agente lê.', 'O Claude Code só chega no AGENTS.md através do CLAUDE.md.', 'Deixe marcado só agents-md.'],
                    ['Tick and untick files; the table shows what each agent reads.', 'Claude Code only gets to AGENTS.md through CLAUDE.md.', 'Leave only agents-md ticked.']),
            'cmd': T(['--arquivos recebe uma lista separada por vírgula.', 'Opções: agents-md, claude-md, copilot-instructions, cursor-rules. --linhas é o tamanho do arquivo.', f'regras "{Q2[0][0]}" --arquivos agents-md'],
                     ['--files takes a comma-separated list.', 'Options: agents-md, claude-md, copilot-instructions, cursor-rules. --lines is the file size.', f'rules "{Q2[0][1]}" --files agents-md'])},
  'errors': {'notInEnum.files': T('“{value}” não é um arquivo daqui. Opções: {options}.', '“{value}” isn’t a file here. Options: {options}.'),
             'belowMin.size': T('Um arquivo de regras com menos de {min} linhas não diz quase nada.', 'A rules file under {min} lines says almost nothing.'),
             'aboveMax.size': T('Mais de {max} linhas? Ninguém (nem o agente) segue isso. Use até {max}.', 'Over {max} lines? Nobody (not even the agent) follows that. Use up to {max}.')},
  'controls': {'arg': T('Pergunta para os agentes', 'Question for the agents'), 'files': T('Arquivos no repositório', 'Files in the repository'), 'size': T('Linhas no arquivo de regras', 'Lines in the rules file')},
  'scene': {'label': T('Quem lê o caderno', 'Who reads the book'), 'empty': T('Rode para ver o que cada agente lê.', 'Run to see what each agent reads.'),
    'mSee': T('agentes com as regras', 'agents with the rules'), 'mCopies': T('lugares com a regra', 'places with the rule'), 'mAdh': T('adesão (de brinquedo)', 'adherence (toy)'),
    'table': T('Os agentes do time', 'The team’s agents'), 'colTool': T('agente', 'agent'), 'colReads': T('lê as regras por', 'reads the rules via'), 'colAnswer': T('resposta', 'answer'),
    'tClaude': T('Claude Code (Bia)', 'Claude Code (Bia)'), 'tCopilot': T('Copilot no VS Code (Caio)', 'Copilot in VS Code (Caio)'), 'tCursor': T('Cursor (Rafa)', 'Cursor (Rafa)'),
    'viaImport': T('CLAUDE.md → @AGENTS.md', 'CLAUDE.md → @AGENTS.md'), 'viaDangling': T('CLAUDE.md importa o nada', 'CLAUDE.md imports nothing'),
    'viaNotRead': T('nada: não lê AGENTS.md', 'nothing: skips AGENTS.md'), 'viaNone': T('nenhum arquivo', 'no file'),
    'viaAgents': 'AGENTS.md', 'viaBoth': T('AGENTS.md + arquivo próprio', 'AGENTS.md + its own file'),
    'viaCopilotFile': '.github/copilot-instructions.md', 'viaCursorFile': '.cursor/rules/*.mdc',
    'caption': T('Arquivo de regras com {size} linhas.', 'Rules file with {size} lines.'),
    'blindNote': T('{blindNames} não enxerga regra nenhuma e responde com o que é comum em outros projetos.', '{blindNames} sees no rules and answers with what’s common in other projects.'),
    'danglingNote': T('O CLAUDE.md tem @AGENTS.md, mas o AGENTS.md não existe: o import não traz nada.', 'CLAUDE.md has @AGENTS.md, but AGENTS.md doesn’t exist: the import brings nothing.'),
    'driftNote': T('A mesma regra escrita em {copies} arquivos. Quando ela mudar, alguém vai esquecer uma cópia. Prefira um AGENTS.md e deixe os outros só com o que é específico de cada ferramenta.', 'The same rule written in {copies} files. When it changes, someone will forget a copy. Prefer one AGENTS.md and keep the others only for tool-specific bits.'),
    'longNote': T('{size} linhas: o arquivo inteiro entra em toda conversa e as regras importantes se perdem no meio. Corte, ou separe por pasta.', '{size} lines: the whole file goes into every conversation and the important rules get lost in the middle. Trim it, or split it by folder.'),
    'okNote': T('Uma fonte só, curta, e os três agentes chegam nela. É esse o desenho.', 'One short source, and all three agents reach it. That’s the design.')},
  'data': {'answers': answers, 'answersFallback': answers[Q2[0][i]]},
  'recipe': {'steps': T([
      'Na raiz do repositório, crie o AGENTS.md (a fonte única):\n# Regras do repositório\n- Preços sempre em centavos (inteiros). Nunca float.\n- Testes: npm test (precisa passar antes do PR).\n- Nunca edite migrations antigas; crie uma nova.',
      'Crie o CLAUDE.md, também na raiz, importando o AGENTS.md:\n@AGENTS.md\n\n## Só para o Claude Code\n- Use plan mode para mudanças em src/pagamento/.',
      'Opcional, regra só para uma pasta. No Cursor, .cursor/rules/dinheiro.mdc:\n---\ndescription: Regras de dinheiro\nglobs: src/**/*.ts\nalwaysApply: false\n---\n- Valores em centavos.\nNo Copilot, .github/instructions/dinheiro.instructions.md começando com applyTo: "src/**/*.ts" entre linhas ---.',
      'No Claude Code, rode /memory e confira que o CLAUDE.md foi carregado. Abra uma conversa nova em cada ferramenta e pergunte: em que unidade guardamos os preços?'],
     ['At the repository root, create AGENTS.md (the single source):\n# Repository rules\n- Prices always in cents (integers). Never floats.\n- Tests: npm test (must pass before the PR).\n- Never edit old migrations; create a new one.',
      'Create CLAUDE.md, also at the root, importing AGENTS.md:\n@AGENTS.md\n\n## Claude Code only\n- Use plan mode for changes under src/payment/.',
      'Optional, a rule for one folder only. In Cursor, .cursor/rules/money.mdc:\n---\ndescription: Money rules\nglobs: src/**/*.ts\nalwaysApply: false\n---\n- Amounts in cents.\nIn Copilot, .github/instructions/money.instructions.md starting with applyTo: "src/**/*.ts" between --- lines.',
      'In Claude Code, run /memory and check that CLAUDE.md was loaded. Open a new conversation in each tool and ask: what unit do we store prices in?']),
    'ok': T('o /memory lista o CLAUDE.md, e nas três ferramentas a resposta é "centavos", citando a regra do AGENTS.md.', '/memory lists CLAUDE.md, and in all three tools the answer is "cents", citing the AGENTS.md rule.')}}

t2 = {'pt': {'objectives': ['Saber qual arquivo de regras cada ferramenta lê.', 'Manter uma fonte única (AGENTS.md) e importar no CLAUDE.md.', 'Manter o arquivo curto e separar regras por caminho.'], 'minutes': 20,
  'activity': 'A turma escreve o AGENTS.md de um projeto real em 10 linhas no máximo. Depois cada grupo testa em uma ferramenta (Claude Code, Copilot, Cursor) se a regra principal aparece na resposta do agente, numa conversa nova.',
  'discussion': ['O que entra no arquivo de regras e o que deveria virar teste ou checagem no CI?', 'Quem é dono do AGENTS.md no time?'],
  'misconceptions': ['"Todas as ferramentas leem AGENTS.md." O Claude Code lê CLAUDE.md; o AGENTS.md entra por import.', '"Escrevi a regra no arquivo, então está garantida." Arquivo de regras é contexto; o que não pode falhar precisa de teste ou trava.']},
 'en': {'objectives': ['Know which rules file each tool reads.', 'Keep one source (AGENTS.md) and import it in CLAUDE.md.', 'Keep the file short and split rules by path.'], 'minutes': 20,
  'activity': 'The class writes the AGENTS.md for a real project in at most 10 lines. Then each group checks in one tool (Claude Code, Copilot, Cursor) whether the main rule shows up in the agent’s answer, in a fresh conversation.',
  'discussion': ['What goes in the rules file, and what should become a test or a CI check?', 'Who owns AGENTS.md on the team?'],
  'misconceptions': ['"Every tool reads AGENTS.md." Claude Code reads CLAUDE.md; AGENTS.md comes in through an import.', '"I wrote the rule in the file, so it’s guaranteed." A rules file is context; what must not fail needs a test or a lock.']}}
write('02-arquivos-de-regras', s2, loc2('pt'), loc2('en'), t2)


# ====================================================================== 3 · tarefas pequenas e verificáveis
TOTAL3, BUGS3, CAUGHT3, PROD3 = 1200, 8, 5, 45

def run3(n, v):
    lines = rnd(TOTAL3 / n)
    rate = 0.9 if lines <= 200 else (0.75 if lines <= 400 else (0.5 if lines <= 600 else 0.25))
    remaining = BUGS3 - (CAUGHT3 if v else 0)
    found = rnd(remaining * rate)
    esc = remaining - found
    review = rnd(n * (5 + lines / 20))
    verify = 2 * n if v else 0
    return {'lines': lines, 'ratePct': rnd(rate * 100), 'auto': CAUGHT3 if v else 0, 'found': found, 'escaped': esc,
            'reviewMin': review, 'verifyMin': verify, 'totalMin': review + verify + esc * PROD3}

RUNS3 = {f'{n}{1 if v else 0}': run3(n, v) for n in range(1, 9) for v in (True, False)}
assert RUNS3['10']['escaped'] == 6 and RUNS3['61']['escaped'] == 0 and RUNS3['61']['totalMin'] == 102
assert sorted(k for k, r in RUNS3.items() if r['escaped'] >= 3) == ['10', '20']  # quebra: 1 ou 2 fatias sem verificar
TASK3 = ('Programa de fidelidade: pontos por compra, resgate e expiração', 'Loyalty program: points per purchase, redemption and expiry')

s3 = step('dai-p-tarefas-pequenas', 3, TRACK, 18, ['fatiar', 'tarefas-pequenas', 'verificacao', 'revisao', 'diff'],
  ['dai-p-arquivos-de-regras'], ['simulado'], LQ('fatiar', 'slice'),
  {'name': 'text', 'required': False, 'ui': 'examples', 'default': ex(TASK3)[0], 'examples': ex(TASK3)},
  [flag('slices', 'fatias', 'slices', 'int', min=1, max=8, default=6, ui='slider'),
   flag('verify', 'verificar', 'verify', 'bool', default=True, ui='switch')],
  {'options': ['few', 'half', 'most'], 'answer': 'most'}, 'leak',
  {'live': True,
   'consts': {'runs': RUNS3, 'bugs': BUGS3, 'prodMin': PROD3, 'total': TOTAL3, 'nLabels': [str(n) for n in range(1, 9)],
              'escV': [RUNS3[f'{n}1']['escaped'] for n in range(1, 9)], 'escN': [RUNS3[f'{n}0']['escaped'] for n in range(1, 9)]},
   'compute': {
     'r': "lookup(runs, str(slices) + (verify ? '1' : '0'), runs['61'])",
     'linesPer': 'r.lines', 'esc': 'r.escaped', 'found': 'r.found', 'auto': 'r.auto', 'remaining': 'bugs - r.auto',
     'reviewMin': 'r.reviewMin', 'verifyMin': 'r.verifyMin', 'totalMin': 'r.totalMin'},
   'cases': [
     {'when': 'esc >= 3', 'flags': ['leak']},
     {'when': 'esc == 0', 'flags': ['clean']},
     {'when': 'slices >= 8', 'flags': ['overSliced']},
     {'when': 'true', 'vars': {'slices': 'slices', 'lines': 'linesPer', 'escaped': 'esc', 'found': 'found', 'auto': 'auto', 'bugs': 'bugs',
                               'remaining': 'remaining', 'reviewMin': 'reviewMin', 'totalMin': 'totalMin', 'ratePct': 'r.ratePct'}}],
   'widgets': [
     {'type': 'flow', 'steps': [
       {'label': '@sTask', 'sub': '@subTask', 'tone': 'info'},
       {'label': '@sSlices', 'sub': '@subSlices', 'tone': "=linesPer > 400 ? 'bad' : (linesPer > 200 ? 'warn' : 'ok')"},
       {'label': '@sVerify', 'sub': "=verify ? '@verifyOn' : '@verifyOff'", 'tone': "=verify ? 'ok' : 'dim'"},
       {'label': '@sReview', 'sub': '@subReview', 'tone': "=esc >= 3 ? 'bad' : (esc > 0 ? 'warn' : 'ok')"}]},
     {'type': 'metrics', 'items': [
       {'label': '@mLines', 'value': '=linesPer', 'format': 'int', 'tone': "=linesPer > 400 ? 'bad' : (linesPer > 200 ? 'warn' : 'ok')"},
       {'label': '@mAuto', 'value': '=auto', 'format': 'int', 'tone': "=auto > 0 ? 'ok' : 'dim'"},
       {'label': '@mFound', 'value': '=found', 'format': 'int', 'tone': 'info'},
       {'label': '@mEscaped', 'value': '=esc', 'format': 'int', 'tone': "=esc >= 3 ? 'bad' : (esc > 0 ? 'warn' : 'ok')"},
       {'label': '@mTotal', 'value': '=totalMin', 'format': 'min', 'tone': 'info'}]},
     {'type': 'chart', 'label': '@chart', 'kind': 'bar', 'labels': '=nLabels',
      'series': [{'label': '@serV', 'values': '=escV'}, {'label': '@serN', 'values': '=escN'}]},
     {'type': 'note', 'when': '=esc >= 3', 'tone': 'bad', 'text': '@leakNote'},
     {'type': 'note', 'when': '=slices >= 8', 'tone': 'warn', 'text': '@overNote'},
     {'type': 'note', 'when': '=esc < 3 && slices < 8', 'tone': "=esc == 0 ? 'ok' : 'info'", 'text': '@calmNote'}]})

def loc3(L):
  pt, T = mk(L)
  return {
  'title': T('Tarefas pequenas e verificáveis', 'Small, verifiable tasks'),
  'subtitle': T('Fatiar a feature em PRs que cabem numa revisão, cada um com um comando que prova', 'Slice the feature into PRs that fit in one review, each with a command that proves it'),
  'mission': T('A Duda escreveu a issue do programa de fidelidade: 1.200 linhas de mudança, segundo o plano do agente. O agente vai inserir 8 bugs pelo caminho (no simulador, sempre 8). Escolha em quantas fatias dividir e se cada fatia termina com testes e checagem de tipos. Quantos bugs chegam na loja?',
               'Duda wrote the loyalty program issue: 1,200 lines of change, according to the agent’s plan. The agent will slip in 8 bugs along the way (in the simulator, always 8). Choose how many slices to cut it into and whether each slice ends with tests and a type check. How many bugs reach the shop?'),
  'predict': {'question': T('tudo numa fatia só (1.200 linhas num PR) e sem verificação por fatia: dos 8 bugs, quantos escapam da revisão? (o gráfico mostra)', 'everything in one slice (1,200 lines in one PR) with no per-slice verification: of the 8 bugs, how many slip past review? (the chart shows it)'),
    'options': {'few': T('1 ou 2: a Bia revisa com cuidado', '1 or 2: Bia reviews carefully'), 'half': T('Uns 4', 'About 4'), 'most': T('Uns 6: num diff gigante, quase tudo passa', 'About 6: in a giant diff, almost everything slips')}},
  'feedback': {'right': T('isso: 6 dos 8. Ninguém lê 1.200 linhas com a mesma atenção que lê 200. Com 6 fatias e testes no fim de cada uma, escapa zero.', 'right: 6 of 8. Nobody reads 1,200 lines with the attention they give 200. With 6 slices and tests at the end of each, zero slip.'),
    'wrong': T('escapam 6. Na barra "1" do gráfico (sem verificar), a revisão acha só 2 dos 8. Diff gigante cansa e esconde; testes por fatia pegam bugs antes de chegar na revisão.', '6 slip. In bar "1" of the chart (no verification), review finds only 2 of the 8. A giant diff tires and hides; per-slice tests catch bugs before review.'),
    'skipped': T('sem palpite? Olhe a barra "1" do gráfico, a série sem verificar.', 'no guess? Look at bar "1" on the chart, the no-verification series.')},
  'coach': {'ui': T('palpite anotado. A cena já mostra 6 fatias com verificação; o gráfico compara todas as quantidades.', 'guess noted. The scene already shows 6 slices with verification; the chart compares every count.'),
            'cmd': T('palpite anotado. Rode como está e depois teste --fatias 1 --verificar nao.', 'guess noted. Run it as is, then try --slices 1 --verify no.')},
  'tryNext': {'ui': T('Agora suba para 8 fatias: o número de bugs não melhora, mas o tempo de revisão sobe. Fatia pequena demais também tem custo.', 'Now go up to 8 slices: the bug count doesn’t improve, but review time goes up. Too-small slices have a cost too.'),
              'cmd': T('Rode fatiar --fatias 8 e compare o tempo total com --fatias 6.', 'Run slice --slices 8 and compare total time with --slices 6.')},
  'why': {
    'simples': T('Conferir uma fornada de 200 pães é fácil: dá para olhar um por um. Conferir 1.200 pães de uma vez, no fim do dia, cansado? Os queimados passam.\nCom o agente é igual: tarefa pequena, com um jeito claro de conferir no fim ("os testes passaram?"), é tarefa que você consegue revisar de verdade.',
                 'Checking a batch of 200 rolls is easy: you can look at each one. Checking 1,200 at once, at the end of the day, tired? The burnt ones get through.\nSame with the agent: a small task, with a clear way to check it at the end ("did the tests pass?"), is a task you can actually review.'),
    'dev': T('Cada fatia tem três coisas: um objetivo pequeno, um "feito quando" e um comando de verificação (ex.: npm test -- pontos e npx tsc --noEmit). Peça ao agente uma fatia por vez e que ele rode a verificação e pare. Um commit por fatia, e git diff --stat antes de abrir o PR para ver o tamanho.\nA documentação do Claude Code dá a mesma dica para refatoração: mudanças em incrementos pequenos e testáveis. O agente não cansa; quem cansa é a revisão.',
           'Each slice has three things: a small goal, a "done when" and a verification command (e.g., npm test -- points and npx tsc --noEmit). Ask the agent for one slice at a time, have it run the verification and stop. One commit per slice, and git diff --stat before opening the PR to see the size.\nClaude Code’s docs give the same tip for refactoring: changes in small, testable increments. The agent doesn’t get tired; the review does.'),
    'especialista': T('O modelo do simulador é de brinquedo: a revisão acha 90% dos bugs até 200 linhas, 75% até 400, 50% até 600 e 25% acima disso, e a verificação automática pega 5 dos 8. A forma da curva é o que importa: abaixo de um tamanho, fatiar mais só soma custo fixo de revisão (contexto, CI, troca de assunto).\nVerificação forte deixa fatias maiores seguras: tipos, testes de propriedade e testes de contrato pegam o que olho humano não pega. E fatia vertical (um pedaço da feature funcionando ponta a ponta) costuma revisar melhor que fatia horizontal (só o banco, depois só a API).',
                      'The simulator’s model is a toy: review finds 90% of bugs up to 200 lines, 75% up to 400, 50% up to 600 and 25% above that, and automatic verification catches 5 of the 8. The shape of the curve is what matters: below a certain size, more slicing only adds fixed review cost (context, CI, switching topics).\nStrong verification makes bigger slices safe: types, property tests and contract tests catch what human eyes miss. And a vertical slice (a piece of the feature working end to end) usually reviews better than a horizontal one (only the database, then only the API).')},
  'break': {'mission': {'ui': T('hora de quebrar: 1 fatia só e verificação desligada.', 'time to break it: just 1 slice and verification off.'),
                        'cmd': T('hora de quebrar: rode fatiar --fatias 1 --verificar nao', 'time to break it: run slice --slices 1 --verify no')},
    'success': T('Quebrou: {lines} linhas por PR e nenhum teste no caminho. A revisão achou {found} dos {bugs} bugs e {escaped} foram parar na loja, cada um custando retrabalho. Tempo total: {totalMin} min.',
                 'Broken: {lines} lines per PR and no tests along the way. Review found {found} of the {bugs} bugs and {escaped} ended up in the shop, each costing rework. Total time: {totalMin} min.'),
    'calm': T('{slices} fatia(s) de {lines} linhas: {escaped} bug(s) escaparam, {totalMin} min no total. Para quebrar, junte tudo numa fatia só e desligue a verificação.',
              '{slices} slice(s) of {lines} lines: {escaped} bug(s) slipped, {totalMin} min in total. To break it, put everything in one slice and turn verification off.')},
  'hints': {'ui': T(['Mexa no número de fatias; a cena atualiza sozinha.', 'O gráfico mostra bugs que escapam para cada número de fatias, com e sem verificação.', '1 fatia e verificação desligada.'],
                    ['Move the slice count; the scene updates by itself.', 'The chart shows bugs that slip for each slice count, with and without verification.', '1 slice and verification off.']),
            'cmd': T(['--fatias vai de 1 a 8.', '--verificar sim roda testes e checagem de tipos no fim de cada fatia.', 'fatiar --fatias 1 --verificar nao'],
                     ['--slices goes from 1 to 8.', '--verify yes runs tests and a type check at the end of each slice.', 'slice --slices 1 --verify no'])},
  'errors': {'belowMin.slices': T('Pelo menos {min} fatia.', 'At least {min} slice.'), 'aboveMax.slices': T('Até {max} fatias neste simulador.', 'Up to {max} slices in this simulator.'),
             'notBool.verify': yn(T, 'verificar', 'verify')},
  'controls': {'arg': T('Feature', 'Feature'), 'slices': T('Fatias (PRs)', 'Slices (PRs)'), 'verify': T('Testes e tipos no fim de cada fatia', 'Tests and types at the end of each slice')},
  'scene': {'label': T('Da feature aos PRs', 'From feature to PRs'), 'empty': T('Rode para ver quantos bugs chegam na loja.', 'Run to see how many bugs reach the shop.'),
    'sTask': T('Feature', 'Feature'), 'subTask': T('1.200 linhas, 8 bugs', '1,200 lines, 8 bugs'),
    'sSlices': T('Fatias', 'Slices'), 'subSlices': T('{slices} PR(s) de {lines} linhas', '{slices} PR(s) of {lines} lines'),
    'sVerify': T('Verificação', 'Verification'), 'verifyOn': T('pegou 5 antes da revisão', 'caught 5 before review'), 'verifyOff': T('nenhuma', 'none'),
    'sReview': T('Revisão', 'Review'), 'subReview': T('achou {found} de {remaining} ({ratePct}%)', 'found {found} of {remaining} ({ratePct}%)'),
    'mLines': T('linhas por PR', 'lines per PR'), 'mAuto': T('pegos pelos testes', 'caught by tests'), 'mFound': T('pegos na revisão', 'caught in review'),
    'mEscaped': T('chegaram na loja', 'reached the shop'), 'mTotal': T('tempo total', 'total time'),
    'chart': T('Bugs que chegam na loja, por número de fatias', 'Bugs reaching the shop, by slice count'),
    'serV': T('com verificação', 'with verification'), 'serN': T('sem verificação', 'without verification'),
    'leakNote': T('{escaped} bugs na loja. Cada um custa uns 45 min de retrabalho (de brinquedo), fora a cliente brava.', '{escaped} bugs in the shop. Each costs about 45 min of rework (toy number), plus an angry customer.'),
    'overNote': T('{slices} fatias: bugs não caem mais, mas a revisão sobe para {reviewMin} min. Cada PR tem custo fixo.', '{slices} slices: bugs don’t drop any further, but review goes up to {reviewMin} min. Each PR has a fixed cost.'),
    'calmNote': T('Revisão: {reviewMin} min ao todo; tempo total com retrabalho: {totalMin} min.', 'Review: {reviewMin} min in all; total time with rework: {totalMin} min.')},
  'data': {},
  'recipe': {'steps': T([
      'Peça ao agente (em plan mode) para quebrar a issue e salve em docs/plano-fidelidade.md, com este formato:\n## Fatia 1: modelo de pontos\nFeito quando: ganhar e expirar pontos têm teste\nVerificar: npm test -- pontos\n## Fatia 2: resgate no checkout\nFeito quando: resgate desconta do total em centavos\nVerificar: npm test -- checkout',
      'Peça uma fatia por vez:\nFaça só a Fatia 1 de docs/plano-fidelidade.md. No fim rode npm test -- pontos e npx tsc --noEmit, mostre a saída e pare.',
      'Antes de aceitar, veja o tamanho e faça um commit por fatia:\ngit diff --stat\ngit add -A\ngit commit -m "fidelidade: fatia 1 (modelo de pontos)"'],
     ['Ask the agent (in plan mode) to break the issue down and save it as docs/loyalty-plan.md, in this format:\n## Slice 1: points model\nDone when: earning and expiring points have tests\nVerify: npm test -- points\n## Slice 2: redemption at checkout\nDone when: redemption subtracts from the total in cents\nVerify: npm test -- checkout',
      'Ask for one slice at a time:\nDo only Slice 1 of docs/loyalty-plan.md. At the end run npm test -- points and npx tsc --noEmit, show the output and stop.',
      'Before accepting, check the size and make one commit per slice:\ngit diff --stat\ngit add -A\ngit commit -m "loyalty: slice 1 (points model)"']),
    'ok': T('o agente parou depois da Fatia 1, os testes e o tsc passaram, e o git diff --stat mostra poucos arquivos e algumas centenas de linhas no máximo.', 'the agent stopped after Slice 1, tests and tsc passed, and git diff --stat shows a few files and a few hundred lines at most.')}}

t3 = {'pt': {'objectives': ['Quebrar uma feature em fatias com "feito quando" e comando de verificação.', 'Relacionar tamanho do diff com qualidade da revisão.', 'Reconhecer o custo de fatiar demais.'], 'minutes': 20,
  'activity': 'Cada grupo pega uma feature grande de um sistema conhecido e escreve de 4 a 6 fatias, cada uma com "feito quando" e "verificar". Depois os grupos trocam e tentam achar uma fatia que não dá para verificar só com o comando escrito.',
  'discussion': ['Qual o maior PR que você já revisou com atenção de verdade?', 'Quando faz sentido aceitar uma fatia maior?'],
  'misconceptions': ['"O agente é rápido, então manda tudo de uma vez." O gargalo é a revisão, não a escrita.', '"Quanto menor a fatia, melhor." Abaixo de um tamanho, só aumenta o custo fixo por PR.']},
 'en': {'objectives': ['Break a feature into slices with "done when" and a verification command.', 'Connect diff size with review quality.', 'Recognize the cost of over-slicing.'], 'minutes': 20,
  'activity': 'Each group takes a big feature from a familiar system and writes 4 to 6 slices, each with "done when" and "verify". Then groups swap and try to find a slice that can’t be verified with the written command alone.',
  'discussion': ['What’s the biggest PR you ever reviewed with real attention?', 'When does it make sense to accept a bigger slice?'],
  'misconceptions': ['"The agent is fast, so send it all at once." The bottleneck is review, not writing.', '"The smaller the slice, the better." Below a certain size, it only adds fixed cost per PR.']}}
write('03-tarefas-pequenas-e-verificaveis', s3, loc3('pt'), loc3('en'), t3)


# ====================================================================== 4 · testes como contrato
LOCKS4 = [opt('none', 'nenhuma', 'none'), opt('rule', 'regra', 'rule'), opt('enforced', 'bloqueio', 'enforced')]
# (teste primeiro?, proteção dos testes) → resultado. Contrato: R$ 99,99 paga; R$ 100,00 paga; R$ 100,01 grátis; frete nunca negativo
RUNS4 = {'tenforced': {'total': 12, 'passed': 12, 'changed': 0, 'denied': 2, 'c': [True, True, True, True]},
         'trule': {'total': 12, 'passed': 12, 'changed': 1, 'denied': 0, 'c': [True, False, True, True]},
         'tnone': {'total': 12, 'passed': 12, 'changed': 2, 'denied': 0, 'c': [True, False, True, False]},
         'fnone': {'total': 6, 'passed': 6, 'changed': 0, 'denied': 0, 'c': [True, False, True, False]}}
RUNS4['frule'] = dict(RUNS4['fnone']); RUNS4['fenforced'] = dict(RUNS4['fnone'])
for r in RUNS4.values(): r['bugs'] = sum(1 for ok in r['c'] if not ok)
assert [k for k, r in RUNS4.items() if r['bugs'] == 0] == ['tenforced']
TASK4 = ('Frete grátis acima de R$ 100', 'Free delivery above R$ 100')

s4 = step('dai-p-testes-como-contrato', 4, TRACK, 18, ['testes', 'contrato', 'permissoes', 'ci', 'tdd'],
  ['dai-p-tarefas-pequenas'], ['simulado'], LQ('contrato', 'contract'),
  {'name': 'text', 'required': False, 'ui': 'examples', 'default': ex(TASK4)[0], 'examples': ex(TASK4)},
  [flag('testFirst', 'teste-primeiro', 'test-first', 'bool', default=True, ui='switch'),
   flag('lock', 'protecao', 'protection', 'enum', options=LOCKS4, default='enforced', ui='select')],
  {'options': ['fixcode', 'edittest', 'giveup'], 'answer': 'fixcode'}, 'fakeGreen',
  {'live': True,
   'consts': {'runs': RUNS4},
   'compute': {
     'cfg': "(testFirst ? 't' : 'f') + lock",
     'r': 'lookup(runs, cfg, runs.tenforced)',
     'nBugs': 'r.bugs', 'how': "lookup(hows, cfg, '')", 'term': 'lookup(terms, cfg, [])'},
   'cases': [
     {'when': 'nBugs > 0', 'flags': ['fakeGreen']},
     {'when': 'nBugs == 0', 'flags': ['honestGreen']},
     {'when': 'r.changed > 0', 'flags': ['testsEdited']},
     {'when': 'true', 'vars': {'passed': 'r.passed', 'total': 'r.total', 'bugs': 'nBugs', 'changed': 'r.changed', 'denied': 'r.denied', 'how': 'how'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@mSuite', 'value': "=r.passed + ' / ' + r.total", 'tone': 'ok'},
       {'label': '@mChanged', 'value': '=r.changed', 'format': 'int', 'tone': "=r.changed > 0 ? 'bad' : 'ok'"},
       {'label': '@mDenied', 'value': '=r.denied', 'format': 'int', 'tone': "=r.denied > 0 ? 'info' : 'dim'"},
       {'label': '@mBugs', 'value': '=nBugs', 'format': 'int', 'tone': "=nBugs > 0 ? 'bad' : 'ok'"}]},
     {'type': 'terminal', 'label': '@term', 'lines': '=term'},
     {'type': 'checks', 'label': '@checks', 'items': [
       {'label': '@c1', 'ok': '=r.c[0]', 'why': '@w1'}, {'label': '@c2', 'ok': '=r.c[1]', 'why': '@w2'},
       {'label': '@c3', 'ok': '=r.c[2]', 'why': '@w3'}, {'label': '@c4', 'ok': '=r.c[3]', 'why': '@w4'}]},
     {'type': 'note', 'when': '=nBugs > 0', 'tone': 'bad', 'text': '@fakeNote'},
     {'type': 'note', 'when': "=testFirst && lock == 'rule'", 'tone': 'warn', 'text': '@ruleNote'},
     {'type': 'note', 'when': '=nBugs == 0', 'tone': 'ok', 'text': '@okNote'}]})

def loc4(L):
  pt, T = mk(L)
  f_how = T('Sem teste antes, o agente escreveu código e testes juntos: os testes só confirmam o que ele entendeu (que R$ 100,00 já é grátis).', 'With no test first, the agent wrote code and tests together: the tests only confirm what it understood (that R$ 100.00 is already free).')
  terms = {
    'tenforced': ['$ npm test', T('! 2 falhando: frete.test.ts (R$ 100,00 exatos; frete negativo)', '! 2 failing: frete.test.ts (exactly R$ 100.00; negative fee)'),
                  T('? agente: Edit tests/frete.test.ts', '? agent: Edit tests/frete.test.ts'), T('! negado: Edit(/tests/**) em .claude/settings.json', '! denied: Edit(/tests/**) in .claude/settings.json'),
                  T('~ agente volta para src/frete.ts: usa > 10000, não >=', '~ agent goes back to src/frete.ts: uses > 10000, not >='), '$ npm test', T('+ 12 passando', '+ 12 passing'),
                  '$ git diff --name-only HEAD -- tests/', T('+ (nada: o contrato não mudou)', '+ (nothing: the contract didn’t change)')],
    'trule': ['$ npm test', T('! 2 falhando: frete.test.ts (R$ 100,00 exatos; frete negativo)', '! 2 failing: frete.test.ts (exactly R$ 100.00; negative fee)'),
              T('~ agente: "o teste de R$ 100,00 parece errado, ajustei"', '~ agent: "the R$ 100.00 test looks wrong, I adjusted it"'), '$ npm test', T('+ 12 passando', '+ 12 passing'),
              '$ git diff --name-only HEAD -- tests/', '! tests/frete.test.ts'],
    'tnone': ['$ npm test', T('! 2 falhando: frete.test.ts (R$ 100,00 exatos; frete negativo)', '! 2 failing: frete.test.ts (exactly R$ 100.00; negative fee)'),
              T('~ agente troca 2 valores esperados para bater com o código', '~ agent swaps 2 expected values to match the code'), '$ npm test', T('+ 12 passando', '+ 12 passing'),
              '$ git diff --name-only HEAD -- tests/', '! tests/frete.test.ts'],
    'fnone': [T('~ agente escreve src/frete.ts e 6 testes novos', '~ agent writes src/frete.ts and 6 new tests'), '$ npm test', T('+ 6 passando', '+ 6 passing'),
              T('? nenhum teste existia antes para discordar do código', '? no test existed before to disagree with the code')]}
  terms['frule'] = terms['fnone']; terms['fenforced'] = terms['fnone']
  hows = {'trule': T('A regra "não mexa em tests/" estava no AGENTS.md, mas regra é contexto: o agente achou que o teste estava errado e mudou 1 asserção.', 'The "don’t touch tests/" rule was in AGENTS.md, but a rule is context: the agent decided the test was wrong and changed 1 assertion.'),
          'tnone': T('Nada impedia o agente de editar os testes, e o caminho mais curto para o verde foi trocar 2 valores esperados.', 'Nothing stopped the agent from editing the tests, and the shortest path to green was changing 2 expected values.'),
          'fnone': f_how, 'frule': f_how, 'fenforced': f_how, 'tenforced': ''}
  return {
  'title': T('Testes como contrato', 'Tests as a contract'),
  'subtitle': T('O teste escrito antes diz o que é "certo", e o agente não pode reescrever o contrato', 'The test written first says what "right" is, and the agent can’t rewrite the contract'),
  'mission': T('A Duda pediu: "frete grátis acima de R$ 100" (R$ 100,00 exatos ainda paga R$ 8). O Caio vai pedir ao agente para implementar. Escolha se a Bia escreve os testes antes e como os testes ficam protegidos. No fim, a loja de verdade confere 4 regras.',
               'Duda asked for: "free delivery above R$ 100" (exactly R$ 100.00 still pays R$ 8). Caio will ask the agent to build it. Choose whether Bia writes the tests first and how the tests are protected. At the end, the real shop checks 4 rules.'),
  'predict': {'question': T('teste escrito antes e edição de tests/ bloqueada. O agente não consegue fazer 2 testes passarem de primeira. O que ele faz?', 'test written first and editing tests/ blocked. The agent can’t make 2 tests pass at first. What does it do?'),
    'options': {'fixcode': T('Volta e conserta o código', 'Goes back and fixes the code'), 'edittest': T('Dá um jeito de mudar o teste mesmo assim', 'Finds a way to change the test anyway'),
                'giveup': T('Desiste e diz que não dá', 'Gives up and says it can’t be done')}},
  'feedback': {'right': T('isso: a edição em tests/ foi negada duas vezes, e o único caminho para o verde que sobrou foi o certo, trocar >= por > no código.', 'right: the edit to tests/ was denied twice, and the only path to green left was the right one, swapping >= for > in the code.'),
    'wrong': T('olha o terminal: o agente tentou editar o teste, a regra de permissão negou, e ele voltou para o código. Com o contrato travado, o caminho mais curto para o verde passa a ser o certo.', 'look at the terminal: the agent tried to edit the test, the permission rule denied it, and it went back to the code. With the contract locked, the shortest path to green becomes the right one.'),
    'skipped': T('sem palpite? Leia o terminal de cima para baixo: tentativa, negado, conserto.', 'no guess? Read the terminal top to bottom: attempt, denied, fix.')},
  'coach': {'ui': T('palpite anotado. Rode com teste primeiro e bloqueio; depois troque a proteção para "regra".', 'guess noted. Run with test first and enforced; then switch protection to "rule".'),
            'cmd': T('palpite anotado. Rode como está e depois tente --protecao regra.', 'guess noted. Run it as is, then try --protection rule.')},
  'tryNext': {'ui': T('Agora deixe a proteção só como "regra" (uma linha no AGENTS.md): a suíte continua verde, mas um teste foi "ajustado".', 'Now leave protection as just "rule" (one line in AGENTS.md): the suite stays green, but one test got "adjusted".'),
              'cmd': T('Rode contrato --protecao regra e olhe o git diff no terminal.', 'Run contract --protection rule and look at the git diff in the terminal.')},
  'why': {
    'simples': T('Quando você encomenda um bolo, combina antes: chocolate, 2 kg, para sábado. Esse combinado é o contrato. Se o confeiteiro pudesse reescrever o pedido depois ("na verdade você pediu baunilha"), todo bolo sairia "certo".\nTeste escrito antes é o combinado. O agente pode mudar o código à vontade, mas não pode mudar o combinado.',
                 'When you order a cake, you agree on it first: chocolate, 2 kg, for Saturday. That agreement is the contract. If the baker could rewrite the order afterwards ("actually you asked for vanilla"), every cake would come out "right".\nA test written first is the agreement. The agent can change the code as it likes, but not the agreement.'),
    'dev': T('Fluxo: você (ou a Duda com você) escreve os testes de aceite, roda e vê falhar, faz commit, e só então pede: "faça tests/frete.test.ts passar alterando só src/". Proteja o contrato com algo que executa: no Claude Code, uma regra de permissão em .claude/settings.json com "deny": ["Edit(/tests/**)"] (regras deny são avaliadas antes de allow).\nPara qualquer ferramenta, confira no fim com git diff --name-only HEAD -- tests/: tem que sair vazio. No CI, a mesma ideia: PR de agente que mexe em teste pede revisão de outra pessoa.',
           'Flow: you (or Duda with you) write the acceptance tests, run them and watch them fail, commit, and only then ask: "make tests/frete.test.ts pass by changing only src/". Protect the contract with something that executes: in Claude Code, a permission rule in .claude/settings.json with "deny": ["Edit(/tests/**)"] (deny rules are evaluated before allow).\nFor any tool, check at the end with git diff --name-only HEAD -- tests/: it must print nothing. In CI, same idea: an agent PR that touches tests needs someone else’s review.'),
    'especialista': T('Por que o agente "ajusta" o teste? Porque o objetivo que você deu foi "fazer passar", e editar a asserção é o caminho mais curto. A regra no AGENTS.md ajuda, mas é contexto; a permissão é trava. E nem a trava é absoluta: a documentação do Claude Code avisa que regras de Edit não cobrem um script Node ou Python que escreve arquivos por conta própria, por isso a checagem no CI fecha a porta.\nTeste que o próprio agente escreveu junto com o código confirma o entendimento dele, não o seu. Para medir se os testes pegam bug de verdade, use testes de mutação (no JavaScript, o Stryker): ele muda o código de propósito e conta quantas mudanças os testes percebem.',
                      'Why does the agent "adjust" the test? Because the goal you gave was "make it pass", and editing the assertion is the shortest path. The AGENTS.md rule helps, but it’s context; the permission is a lock. And even the lock isn’t absolute: Claude Code’s docs warn that Edit rules don’t cover a Node or Python script that writes files on its own, which is why the CI check closes the door.\nTests the agent wrote together with the code confirm its understanding, not yours. To measure whether tests catch real bugs, use mutation testing (in JavaScript, Stryker): it changes the code on purpose and counts how many changes the tests notice.')},
  'break': {'mission': {'ui': T('hora de quebrar: deixe a proteção em "nenhuma".', 'time to break it: set protection to "none".'),
                        'cmd': T('hora de quebrar: rode contrato --protecao nenhuma', 'time to break it: run contract --protection none')},
    'success': T('Quebrou: a suíte diz {passed} de {total} verdes, mas {bugs} regra(s) do frete continuam erradas na loja. {how} Verde não é a mesma coisa que certo.',
                 'Broken: the suite says {passed} of {total} green, but {bugs} delivery rule(s) are still wrong in the shop. {how} Green isn’t the same as right.'),
    'calm': T('{passed} de {total} verdes e o contrato intacto: o agente tentou mexer nos testes {denied} vez(es) e foi barrado. Para quebrar, tire a proteção dos testes.',
              '{passed} of {total} green and the contract intact: the agent tried to touch the tests {denied} time(s) and was stopped. To break it, remove the test protection.')},
  'hints': {'ui': T(['Ligue e desligue o teste primeiro e troque a proteção; a cena atualiza sozinha.', 'Compare "regra" com "bloqueio": a regra é texto no AGENTS.md, o bloqueio é permissão que executa.', 'Proteção "nenhuma".'],
                    ['Toggle test first and switch protection; the scene updates by itself.', 'Compare "rule" with "enforced": the rule is text in AGENTS.md, enforced is a permission that executes.', 'Protection "none".']),
            'cmd': T(['--teste-primeiro aceita sim ou nao.', '--protecao aceita nenhuma, regra ou bloqueio.', 'contrato --protecao nenhuma'],
                     ['--test-first takes yes or no.', '--protection takes none, rule or enforced.', 'contract --protection none'])},
  'errors': {'notBool.testFirst': yn(T, 'teste-primeiro', 'test-first'), 'notInEnum.lock': T('“{value}” não é uma proteção daqui. Opções: {options}.', '“{value}” isn’t a protection here. Options: {options}.')},
  'controls': {'arg': T('Regra pedida', 'Requested rule'), 'testFirst': T('Bia escreve os testes antes', 'Bia writes the tests first'), 'lock': T('Proteção dos testes', 'Test protection')},
  'scene': {'label': T('O contrato do frete', 'The delivery contract'), 'empty': T('Rode para ver o que o agente faz com os testes.', 'Run to see what the agent does with the tests.'),
    'mSuite': T('suíte', 'suite'), 'mChanged': T('asserções alteradas', 'assertions changed'), 'mDenied': T('edições negadas', 'edits denied'), 'mBugs': T('regras erradas na loja', 'rules wrong in the shop'),
    'term': T('O que o agente fez', 'What the agent did'), 'checks': T('A loja de verdade confere', 'The real shop checks'),
    'c1': T('R$ 99,99 paga R$ 8', 'R$ 99.99 pays R$ 8'), 'c2': T('R$ 100,00 exatos ainda paga R$ 8', 'Exactly R$ 100.00 still pays R$ 8'),
    'c3': T('R$ 100,01 tem frete grátis', 'R$ 100.01 gets free delivery'), 'c4': T('Cupom nunca deixa o frete negativo', 'A coupon never makes the fee negative'),
    'w1': T('caso comum, todo mundo acerta', 'common case, everyone gets it'), 'w2': T('"acima de" é >, não >=: o limite é onde o agente chuta', '"above" is >, not >=: the boundary is where the agent guesses'),
    'w3': T('caso comum do outro lado do limite', 'common case on the other side'), 'w4': T('o caso esquisito que só o contrato lembra', 'the odd case only the contract remembers'),
    'fakeNote': T('Suíte verde, {bugs} regra(s) erradas. O verde só vale quando quem decidiu o "certo" não foi quem escreveu o código.', 'Green suite, {bugs} rule(s) wrong. Green only counts when whoever decided "right" isn’t whoever wrote the code.'),
    'ruleNote': T('Regra no AGENTS.md é contexto: o agente leu e mesmo assim decidiu que o teste estava errado. Para o que não pode falhar, use trava que executa.', 'A rule in AGENTS.md is context: the agent read it and still decided the test was wrong. For what must not fail, use a lock that executes.'),
    'okNote': T('Contrato escrito antes, travado, e o agente consertou o código. As 4 regras batem na loja.', 'Contract written first, locked, and the agent fixed the code. All 4 rules hold in the shop.')},
  'data': {'hows': hows, 'terms': terms},
  'recipe': {'steps': T([
      'Escreva o contrato antes, em tests/frete.test.ts (valores em centavos):\nimport { describe, expect, it } from \'vitest\';\nimport { frete } from \'../src/frete\';\n\ndescribe(\'frete (contrato)\', () => {\n  it(\'R$ 99,99 paga R$ 8\', () => expect(frete(9999)).toBe(800));\n  it(\'R$ 100,00 exatos ainda paga\', () => expect(frete(10000)).toBe(800));\n  it(\'acima de R$ 100 é grátis\', () => expect(frete(10001)).toBe(0));\n});',
      'Rode, veja falhar e faça commit do contrato:\nnpx vitest run tests/frete.test.ts\ngit add tests/frete.test.ts\ngit commit -m "contrato do frete grátis"',
      'No Claude Code, trave a pasta em .claude/settings.json:\n{\n  "permissions": {\n    "deny": ["Edit(/tests/**)"]\n  }\n}\nPeça: faça tests/frete.test.ts passar alterando só src/. Os testes são o contrato.',
      'Com qualquer ferramenta, confira no fim (as duas linhas):\nnpx vitest run\ngit diff --name-only HEAD -- tests/'],
     ['Write the contract first, in tests/frete.test.ts (amounts in cents):\nimport { describe, expect, it } from \'vitest\';\nimport { frete } from \'../src/frete\';\n\ndescribe(\'delivery fee (contract)\', () => {\n  it(\'R$ 99.99 pays R$ 8\', () => expect(frete(9999)).toBe(800));\n  it(\'exactly R$ 100.00 still pays\', () => expect(frete(10000)).toBe(800));\n  it(\'above R$ 100 is free\', () => expect(frete(10001)).toBe(0));\n});',
      'Run it, watch it fail and commit the contract:\nnpx vitest run tests/frete.test.ts\ngit add tests/frete.test.ts\ngit commit -m "free delivery contract"',
      'In Claude Code, lock the folder in .claude/settings.json:\n{\n  "permissions": {\n    "deny": ["Edit(/tests/**)"]\n  }\n}\nAsk: make tests/frete.test.ts pass by changing only src/. The tests are the contract.',
      'With any tool, check at the end (both lines):\nnpx vitest run\ngit diff --name-only HEAD -- tests/']),
    'ok': T('o vitest mostra os testes do frete passando e o git diff --name-only HEAD -- tests/ não imprime nada (no Claude Code, a tentativa de editar tests/ aparece como negada).', 'vitest shows the delivery tests passing and git diff --name-only HEAD -- tests/ prints nothing (in Claude Code, any attempt to edit tests/ shows up as denied).')}}

t4 = {'pt': {'objectives': ['Escrever os testes de aceite antes de pedir o código.', 'Diferenciar regra (contexto) de trava (permissão, CI).', 'Desconfiar de testes escritos junto com o código pelo mesmo agente.'], 'minutes': 20,
  'activity': 'Em duplas: uma pessoa escreve 3 testes de uma regra de negócio com um caso de limite; a outra faz o papel do agente e tenta deixar tudo verde do jeito mais preguiçoso possível. Depois discutem que proteção teria impedido cada atalho.',
  'discussion': ['Quem deve aprovar uma mudança em teste num PR feito por agente?', 'Que regra de negócio do seu sistema tem um limite (>, >=) que ninguém escreveu?'],
  'misconceptions': ['"Suíte verde = feature certa." Só se o "certo" foi definido antes e por outra pessoa.', '"Escrevi no AGENTS.md para não mexer nos testes, então está resolvido." Regra é contexto; trava é permissão ou CI.']},
 'en': {'objectives': ['Write acceptance tests before asking for code.', 'Tell a rule (context) from a lock (permission, CI).', 'Distrust tests written together with the code by the same agent.'], 'minutes': 20,
  'activity': 'In pairs: one person writes 3 tests for a business rule with a boundary case; the other plays the agent and tries to make everything green the laziest way possible. Then they discuss which protection would have blocked each shortcut.',
  'discussion': ['Who should approve a test change in an agent-made PR?', 'Which business rule in your system has a boundary (>, >=) nobody wrote down?'],
  'misconceptions': ['"Green suite = correct feature." Only if "correct" was defined first, by someone else.', '"I wrote in AGENTS.md not to touch tests, so it’s solved." A rule is context; a lock is a permission or CI.']}}
write('04-testes-como-contrato', s4, loc4('pt'), loc4('en'), t4)


# ====================================================================== 5 · refatoração assistida
LINES5, ORDERS5, ACC5, FIX5 = 900, 200, 3, 14
TASK5 = ('Quebrar calcularPedido (380 linhas) em módulos sem mudar comportamento', 'Split calcularPedido (380 lines) into modules without changing behavior')

s5 = step('dai-p-refatoracao-assistida', 5, TRACK, 18, ['refatoracao', 'golden-master', 'testes-de-caracterizacao', 'snapshot'],
  ['dai-p-testes-como-contrato'], ['simulado'], LQ('refatorar', 'refactor'),
  {'name': 'text', 'required': False, 'ui': 'examples', 'default': ex(TASK5)[0], 'examples': ex(TASK5)},
  [flag('golden', 'gravar', 'record', 'bool', default=True, ui='switch'),
   flag('mix', 'misturar', 'mix', 'bool', default=False, ui='switch'),
   flag('steps', 'passos', 'steps', 'int', min=1, max=6, default=4, ui='slider')],
  {'options': ['zero', 'three', 'many'], 'answer': 'three'}, 'silentChange',
  {'live': True,
   'consts': {'totalLines': LINES5, 'orders': ORDERS5, 'accidental': ACC5, 'intended': FIX5, 'suite': SUITE},
   'compute': {
     'perStep': 'round(totalLines / steps)',
     'badStep': 'max(1, ceil(steps / 2))',
     'shown': 'golden ? accidental + (mix ? intended : 0) : 0',
     'silent': 'golden ? (mix ? accidental : 0) : accidental',
     'caught': 'accidental - silent',
     'searchLines': 'golden ? perStep : totalLines',
     'reviewMin': 'round(steps * (5 + perStep / 30))',
     'how': "golden ? (mix ? howMix : '') : howNoGolden"},
   'cases': [
     {'when': 'silent > 0', 'flags': ['silentChange']},
     {'when': 'silent == 0', 'flags': ['preserved']},
     {'when': 'mix', 'flags': ['tangled']},
     {'when': 'steps == 1', 'flags': ['bigBang']},
     {'when': 'true', 'vars': {'silent': 'silent', 'caught': 'caught', 'shown': 'shown', 'orders': 'orders', 'suite': 'suite', 'steps': 'steps',
                               'perStep': 'perStep', 'badStep': 'badStep', 'searchLines': 'searchLines', 'reviewMin': 'reviewMin', 'how': 'how', 'intended': 'intended'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@mSuite', 'value': "=suite + ' / ' + suite", 'tone': 'ok'},
       {'label': '@mShown', 'value': "=golden ? str(shown) : '—'", 'tone': "=!golden ? 'dim' : (mix ? 'warn' : 'info')"},
       {'label': '@mSilent', 'value': '=silent', 'format': 'int', 'tone': "=silent > 0 ? 'bad' : 'ok'"},
       {'label': '@mSearch', 'value': '=searchLines', 'format': 'int', 'tone': "=searchLines > 400 ? 'bad' : 'ok'"},
       {'label': '@mReview', 'value': '=reviewMin', 'format': 'min', 'tone': 'info'}]},
     {'type': 'flow', 'steps': [
       {'label': '@sRecord', 'sub': "=golden ? '@recOn' : '@recOff'", 'tone': "=golden ? 'ok' : 'bad'"},
       {'label': '@sSteps', 'sub': '@subSteps', 'tone': "=steps == 1 ? 'warn' : 'ok'"},
       {'label': '@sCompare', 'sub': "=!golden ? '@cmpNone' : (mix ? '@cmpMixed' : '@cmpCaught')", 'tone': "=silent > 0 ? 'bad' : 'ok'"},
       {'label': '@sPr', 'sub': "=mix ? '@prMixed' : '@prPure'", 'tone': "=mix ? 'warn' : 'ok'"}]},
     {'type': 'note', 'when': '=silent > 0', 'tone': 'bad', 'text': '@silentNote'},
     {'type': 'note', 'when': '=golden && !mix', 'tone': 'ok', 'text': '@caughtNote'},
     {'type': 'note', 'when': '=steps == 1', 'tone': 'warn', 'text': '@bigNote'}]})

def loc5(L):
  pt, T = mk(L)
  return {
  'title': T('Refatoração assistida', 'Assisted refactoring'),
  'subtitle': T('Mudar a forma sem mudar o comportamento, e provar isso com pedidos reais', 'Change the shape without changing behavior, and prove it with real orders'),
  'mission': T('A função calcularPedido tem 380 linhas e ninguém quer encostar nela. A Bia vai pedir ao agente para quebrá-la em módulos (uns 900 linhas de diff ao todo). A suíte de 140 testes cobre só parte dela. Antes de começar, dá para gravar o resultado de 200 pedidos reais (anonimizados) e comparar depois de cada passo.',
               'The calcularPedido function has 380 lines and nobody wants to touch it. Bia will ask the agent to split it into modules (about 900 lines of diff in all). The 140-test suite covers only part of it. Before starting, you can record the result of 200 real (anonymized) orders and compare after every step.'),
  'predict': {'question': T('o agente terminou um passo e os 140 testes continuam verdes. Comparando com a gravação dos 200 pedidos reais, quantos mudaram de total?', 'the agent finished a step and the 140 tests are still green. Compared with the recording of 200 real orders, how many changed their total?'),
    'options': {'zero': T('Nenhum: os testes estão verdes', 'None: the tests are green'), 'three': T('Uns poucos (3)', 'A few (3)'), 'many': T('Muitos (uns 50)', 'Many (about 50)')}},
  'feedback': {'right': T('isso: 3 pedidos mudaram de total por centavos. O agente trocou a ordem do arredondamento ao mover um trecho, e nenhum dos 140 testes cobria esse caminho. A gravação pegou, e ele corrigiu antes do PR.', 'right: 3 orders changed their total by cents. The agent swapped the rounding order while moving a piece, and none of the 140 tests covered that path. The recording caught it, and it was fixed before the PR.'),
    'wrong': T('foram 3, por centavos. Testes verdes só dizem que o que eles testam não mudou. A gravação de pedidos reais cobre os caminhos que ninguém lembrou de testar.', 'it was 3, by cents. Green tests only say that what they test didn’t change. A recording of real orders covers the paths nobody remembered to test.'),
    'skipped': T('sem palpite? Olhe "diferenças na gravação": foram 3 com tudo verde.', 'no guess? Look at "differences in the recording": 3, with everything green.')},
  'coach': {'ui': T('palpite anotado. Rode com a gravação ligada; depois desligue e compare.', 'guess noted. Run with the recording on; then switch it off and compare.'),
            'cmd': T('palpite anotado. Rode como está e depois tente --gravar nao.', 'guess noted. Run it as is, then try --record no.')},
  'tryNext': {'ui': T('Agora ligue "aproveitar e corrigir o arredondamento": a gravação mostra 17 diferenças, 14 de propósito e 3 sem querer, e ninguém consegue separar umas das outras.', 'Now turn on "fix the rounding while at it": the recording shows 17 differences, 14 on purpose and 3 by accident, and nobody can tell them apart.'),
              'cmd': T('Rode refatorar --misturar sim e conte as diferenças.', 'Run refactor --mix yes and count the differences.')},
  'why': {
    'simples': T('Reorganizar a cozinha não pode mudar o gosto do pão. Um jeito de garantir: antes de mexer, assar 200 pães e anotar como cada um saiu. Depois de cada mudança, assar de novo e comparar.\nE se você quer mudar a receita também, faça outro dia. Senão, quando o pão sair diferente, ninguém sabe se foi a receita ou a cozinha nova.',
                 'Reorganizing the kitchen must not change how the bread tastes. One way to be sure: before touching anything, bake 200 loaves and write down how each came out. After each change, bake again and compare.\nAnd if you also want to change the recipe, do it another day. Otherwise, when the bread comes out different, nobody knows whether it was the recipe or the new kitchen.'),
    'dev': T('Refatorar é mudar a estrutura sem mudar o comportamento. Com agente: (1) grave o comportamento atual com testes de caracterização (golden master): rode a função com entradas reais e salve as saídas como snapshot (toMatchSnapshot no Vitest ou no Jest); (2) peça a refatoração em passos pequenos, um commit por passo; (3) depois de cada passo, rode a suíte e os snapshots.\nRegra de ouro: o agente nunca atualiza snapshot (nada de vitest -u) num PR de refatoração. Correção de bug vai num PR separado, antes ou depois.',
           'Refactoring is changing structure without changing behavior. With an agent: (1) record current behavior with characterization tests (golden master): run the function on real inputs and save the outputs as snapshots (toMatchSnapshot in Vitest or Jest); (2) ask for the refactor in small steps, one commit per step; (3) after each step, run the suite and the snapshots.\nGolden rule: the agent never updates snapshots (no vitest -u) in a refactoring PR. A bug fix goes in a separate PR, before or after.'),
    'especialista': T('"Teste de caracterização" é o nome que Michael Feathers deu, em Working Effectively with Legacy Code, a testes que registram o que o código faz hoje, certo ou errado. Ele protege refatoração, não correção.\nAgentes são ótimos em refatoração mecânica (mover, renomear, extrair) e perigosos em detalhes que parecem neutros: ordem de arredondamento, avaliação preguiçosa, efeitos colaterais escondidos. Passos pequenos também ajudam a achar o culpado: com 4 passos, você procura em uns 225 linhas, não em 900 (e git bisect funciona). Os números aqui são do cenário, não de estudo.',
                      '"Characterization test" is the name Michael Feathers gave, in Working Effectively with Legacy Code, to tests that record what the code does today, right or wrong. It protects refactoring, not fixing.\nAgents are great at mechanical refactoring (move, rename, extract) and dangerous with details that look neutral: rounding order, lazy evaluation, hidden side effects. Small steps also help find the culprit: with 4 steps you search about 225 lines, not 900 (and git bisect works). The numbers here come from the scenario, not a study.')},
  'break': {'mission': {'ui': T('hora de quebrar: desligue a gravação dos pedidos reais.', 'time to break it: switch off the recording of real orders.'),
                        'cmd': T('hora de quebrar: rode refatorar --gravar nao', 'time to break it: run refactor --record no')},
    'success': T('Quebrou: os {suite} testes ficaram verdes, mas {silent} dos {orders} pedidos reais mudaram de total e ninguém percebeu. {how} A cliente percebe no recibo.',
                 'Broken: the {suite} tests stayed green, but {silent} of the {orders} real orders changed their total and nobody noticed. {how} The customer notices on the receipt.'),
    'calm': T('Comportamento preservado: {caught} diferença(s) acidental(is) pega(s) pela gravação e corrigida(s), em {steps} passo(s) de uns {perStep} linhas. Para quebrar, refatore sem gravar.',
              'Behavior preserved: {caught} accidental difference(s) caught by the recording and fixed, in {steps} step(s) of about {perStep} lines. To break it, refactor without recording.')},
  'hints': {'ui': T(['Ligue e desligue a gravação e a mistura; a cena atualiza sozinha.', '"Misturar" junta uma correção de bug com a refatoração no mesmo PR.', 'Desligue a gravação.'],
                    ['Toggle the recording and the mix; the scene updates by itself.', '"Mix" puts a bug fix in the same PR as the refactor.', 'Switch the recording off.']),
            'cmd': T(['--gravar e --misturar aceitam sim ou nao.', '--passos vai de 1 a 6.', 'refatorar --gravar nao'],
                     ['--record and --mix take yes or no.', '--steps goes from 1 to 6.', 'refactor --record no'])},
  'errors': {'notBool.golden': yn(T, 'gravar', 'record'), 'notBool.mix': yn(T, 'misturar', 'mix'),
             'belowMin.steps': T('Pelo menos {min} passo.', 'At least {min} step.'), 'aboveMax.steps': T('Até {max} passos neste simulador.', 'Up to {max} steps in this simulator.')},
  'controls': {'arg': T('Refatoração', 'Refactor'), 'golden': T('Gravar 200 pedidos reais antes', 'Record 200 real orders first'),
               'mix': T('Aproveitar e corrigir o arredondamento junto', 'Fix the rounding while at it'), 'steps': T('Passos (commits)', 'Steps (commits)')},
  'scene': {'label': T('Refatorando calcularPedido', 'Refactoring calcularPedido'), 'empty': T('Rode para ver se o comportamento mudou.', 'Run to see whether behavior changed.'),
    'mSuite': T('testes da suíte', 'suite tests'), 'mShown': T('diferenças na gravação', 'differences in the recording'), 'mSilent': T('mudanças que ninguém viu', 'changes nobody saw'),
    'mSearch': T('linhas para procurar a causa', 'lines to search for the cause'), 'mReview': T('minutos de revisão', 'review minutes'),
    'sRecord': T('Antes', 'Before'), 'recOn': T('200 pedidos gravados', '200 orders recorded'), 'recOff': T('só os 140 testes', 'only the 140 tests'),
    'sSteps': T('Agente', 'Agent'), 'subSteps': T('{steps} passo(s) de ~{perStep} linhas', '{steps} step(s) of ~{perStep} lines'),
    'sCompare': T('Depois de cada passo', 'After each step'), 'cmpNone': T('nada para comparar', 'nothing to compare'),
    'cmpMixed': T('17 diferenças misturadas', '17 mixed-up differences'), 'cmpCaught': T('3 diferenças no passo {badStep}', '3 differences at step {badStep}'),
    'sPr': 'PR', 'prPure': T('só refatoração', 'refactor only'), 'prMixed': T('refatoração + correção', 'refactor + fix'),
    'silentNote': T('{silent} pedidos com total diferente, e os {suite} testes verdes. Comportamento mudou em silêncio.', '{silent} orders with a different total, and all {suite} tests green. Behavior changed silently.'),
    'caughtNote': T('A gravação mostrou 3 pedidos diferentes no passo {badStep}; o agente desfez a troca de arredondamento e a comparação voltou a bater com os {orders} pedidos.', 'The recording showed 3 different orders at step {badStep}; the agent undid the rounding swap and the comparison matched all {orders} orders again.'),
    'bigNote': T('Um passo só: se algo mudar, a causa está em algum lugar de {searchLines} linhas.', 'Just one step: if something changes, the cause is somewhere in {searchLines} lines.')},
  'data': {'howNoGolden': T('Sem gravação, nada comparou o antes e o depois.', 'With no recording, nothing compared before and after.'),
           'howMix': T('A gravação até mostrou as diferenças, mas misturadas com as 14 da correção pedida, e as 3 acidentais passaram como "esperadas".', 'The recording did show the differences, but mixed with the 14 from the requested fix, and the 3 accidental ones passed as "expected".')},
  'recipe': {'steps': T([
      'Exporte uns 200 pedidos reais, anonimizados, para tests/fixtures/pedidos-200.json e crie tests/pedido.golden.test.ts:\nimport { expect, test } from \'vitest\';\nimport pedidos from \'./fixtures/pedidos-200.json\';\nimport { calcularPedido } from \'../src/pedido\';\n\ntest.each(pedidos)(\'pedido $id\', (p) => {\n  expect(calcularPedido(p)).toMatchSnapshot();\n});',
      'Rode uma vez na sua máquina para gravar os snapshots e faça commit deles:\nnpx vitest run tests/pedido.golden.test.ts\ngit add tests\ngit commit -m "golden master de calcularPedido"',
      'Peça ao agente: refatore calcularPedido em 4 passos, um commit por passo, sem mudar comportamento. Depois de cada passo rode npx vitest run. Nunca rode com -u. Correções de bug ficam para outro PR.',
      'Depois de cada passo, confira:\nnpx vitest run\ngit status --short'],
     ['Export about 200 real orders, anonymized, to tests/fixtures/orders-200.json and create tests/order.golden.test.ts:\nimport { expect, test } from \'vitest\';\nimport orders from \'./fixtures/orders-200.json\';\nimport { calcularPedido } from \'../src/pedido\';\n\ntest.each(orders)(\'order $id\', (o) => {\n  expect(calcularPedido(o)).toMatchSnapshot();\n});',
      'Run it once on your machine to record the snapshots and commit them:\nnpx vitest run tests/order.golden.test.ts\ngit add tests\ngit commit -m "golden master for calcularPedido"',
      'Ask the agent: refactor calcularPedido in 4 steps, one commit per step, without changing behavior. After each step run npx vitest run. Never run with -u. Bug fixes go in another PR.',
      'After each step, check:\nnpx vitest run\ngit status --short']),
    'ok': T('os 200 snapshots passam depois de cada passo e o git status não mostra nada mudado em tests/__snapshots__/.', 'all 200 snapshots pass after every step and git status shows nothing changed in tests/__snapshots__/.')}}

t5 = {'pt': {'objectives': ['Gravar o comportamento atual antes de refatorar (golden master).', 'Separar refatoração de correção de bug.', 'Refatorar em passos pequenos para achar o culpado rápido.'], 'minutes': 20,
  'activity': 'A turma recebe uma função curta e feia com um bug de arredondamento. Primeiro grava 10 entradas e saídas numa tabela; depois refatora em dupla com o agente e compara a tabela a cada passo. Só no fim, num commit separado, corrige o bug.',
  'discussion': ['Por que o teste de caracterização "trava" até o comportamento errado?', 'Que dados reais você poderia gravar no seu sistema sem expor ninguém?'],
  'misconceptions': ['"Os testes passaram, então a refatoração está certa." Só o que eles testam está protegido.', '"Já que estou mexendo, aproveito e corrijo." Misturar esconde as mudanças acidentais no meio das propositais.']},
 'en': {'objectives': ['Record current behavior before refactoring (golden master).', 'Keep refactoring and bug fixing apart.', 'Refactor in small steps to find the culprit fast.'], 'minutes': 20,
  'activity': 'The class gets a short, ugly function with a rounding bug. First they record 10 inputs and outputs in a table; then they refactor in pairs with the agent and compare the table at every step. Only at the end, in a separate commit, do they fix the bug.',
  'discussion': ['Why does a characterization test "lock in" even wrong behavior?', 'What real data could you record in your system without exposing anyone?'],
  'misconceptions': ['"The tests passed, so the refactor is right." Only what they test is protected.', '"Since I’m in there, I’ll fix it too." Mixing hides accidental changes among the intended ones.']}}
write('05-refatoracao-assistida', s5, loc5('pt'), loc5('en'), t5)


# ====================================================================== 6 · legado e código desconhecido
TASK6 = [('Remover o código morto do módulo de nota fiscal', 'Remove the dead code from the invoice module'),
         ('Entender o módulo de nota fiscal antes de mexer', 'Understand the invoice module before touching it')]

s6 = step('dai-p-legado-e-codigo-desconhecido', 6, TRACK, 18, ['legado', 'exploracao', 'plan-mode', 'git-grep', 'alucinacao'],
  ['dai-p-refatoracao-assistida'], ['simulado'], LQ('explorar', 'explore'),
  {'name': 'text', 'required': False, 'ui': 'examples', 'default': ex(TASK6[0])[0], 'examples': ex(*TASK6)},
  [flag('readOnly', 'so-leitura', 'read-only', 'bool', default=True, ui='switch'),
   flag('cite', 'citar', 'cite', 'bool', default=True, ui='switch'),
   flag('search', 'buscar', 'search', 'bool', default=True, ui='switch')],
  {'options': ['none', 'two', 'six'], 'answer': 'two'}, 'brokeLegacy',
  {'live': True,
   'consts': {'claims': 10, 'wrong': 2},
   'compute': {
     'believed': '(search ? 0 : 1) + (cite ? 0 : 1)',
     'caughtN': 'wrong - believed',
     'key': "(search ? '1' : '0') + (cite ? '1' : '0')",
     'how': "lookup(hows, key, '')",
     'edited': 'readOnly ? 0 : 7',
     'statusA': "search ? '@stCaughtGrep' : '@stBelieved'",
     'statusB': "cite ? '@stCaughtCite' : '@stBelieved'",
     'grepLines': "search ? grepOn : grepOff"},
   'cases': [
     {'when': 'believed > 0', 'flags': ['brokeLegacy']},
     {'when': 'believed == 0', 'flags': ['understood']},
     {'when': '!readOnly', 'flags': ['editedBlind']},
     {'when': 'true', 'vars': {'believed': 'believed', 'caught': 'caughtN', 'claims': 'claims', 'wrong': 'wrong', 'edited': 'edited', 'how': 'how'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@mClaims', 'value': '=claims', 'format': 'int', 'tone': 'info'},
       {'label': '@mCaught', 'value': '=caughtN', 'format': 'int', 'tone': "=caughtN == wrong ? 'ok' : 'warn'"},
       {'label': '@mBelieved', 'value': '=believed', 'format': 'int', 'tone': "=believed > 0 ? 'bad' : 'ok'"},
       {'label': '@mEdited', 'value': '=edited', 'format': 'int', 'tone': "=edited > 0 ? 'warn' : 'ok'"}]},
     {'type': 'table', 'label': '@table', 'columns': ['@colClaim', '@colStatus'],
      'rows': [['@k1', '@stOk'], ['@k2', '@stOk'], ['@kA', '=statusA'], ['@kB', '=statusB']],
      'tones': ['ok', 'ok', "=search ? 'warn' : 'bad'", "=cite ? 'warn' : 'bad'"], 'caption': '@caption'},
     {'type': 'terminal', 'label': '@term', 'lines': '=grepLines'},
     {'type': 'note', 'when': '=believed > 0', 'tone': 'bad', 'text': '@brokeNote'},
     {'type': 'note', 'when': '=!readOnly', 'tone': 'warn', 'text': '@blindNote'},
     {'type': 'note', 'when': '=believed == 0', 'tone': 'ok', 'text': '@okNote'}]})

def loc6(L):
  pt, T = mk(L)
  return {
  'title': T('Legado e código desconhecido', 'Legacy and unfamiliar code'),
  'subtitle': T('O agente explica rápido e com confiança; você confere com arquivo:linha e busca', 'The agent explains fast and confidently; you check with file:line and search'),
  'mission': T('A Pão de Mel comprou o sistema de nota fiscal de uma padaria parceira: PHP de 2014, sem testes, e o autor sumiu. O Rafa precisa limpar o código morto do módulo. Ele pede ao agente para explicar o módulo primeiro. Escolha como explorar e quanto confiar no que o agente diz.',
               'Pão de Mel bought the invoice system of a partner bakery: PHP from 2014, no tests, and the author is gone. Rafa needs to clean the dead code out of the module. He asks the agent to explain the module first. Choose how to explore and how much to trust what the agent says.'),
  'predict': {'question': T('o agente explicou o módulo em 10 afirmações, todas com o mesmo tom confiante. Quantas estavam erradas?', 'the agent explained the module in 10 statements, all in the same confident tone. How many were wrong?'),
    'options': {'none': T('Nenhuma', 'None'), 'two': T('Umas 2', 'About 2'), 'six': T('Mais da metade', 'More than half')}},
  'feedback': {'right': T('isso: 2 de 10. Poucas, mas justo as perigosas: "gerarFechamento() não é usada" (é chamada por nome, num texto do cron) e "o CFOP sempre vem preenchido" (notas antigas têm CFOP vazio). A busca e a exigência de arquivo:linha pegaram as duas.', 'right: 2 of 10. Few, but the dangerous ones: "gerarFechamento() isn’t used" (it’s called by name, in a cron string) and "CFOP is always filled" (old invoices have an empty CFOP). Search and the file:line requirement caught both.'),
    'wrong': T('foram 2 de 10, e as duas eram as que importavam para apagar código. O tom é o mesmo nas certas e nas erradas: confiança não é evidência.', 'it was 2 of 10, and both were the ones that mattered for deleting code. The tone is the same for right and wrong ones: confidence isn’t evidence.'),
    'skipped': T('sem palpite? A tabela mostra 4 das 10 afirmações; olhe as duas de baixo.', 'no guess? The table shows 4 of the 10 statements; look at the bottom two.')},
  'coach': {'ui': T('palpite anotado. Rode com tudo ligado; depois desligue a busca.', 'guess noted. Run with everything on; then switch search off.'),
            'cmd': T('palpite anotado. Rode como está e depois tente --buscar nao.', 'guess noted. Run it as is, then try --search no.')},
  'tryNext': {'ui': T('Agora desligue "só leitura": o agente já sai apagando enquanto explica. Mesmo se você pegar o erro depois, tem 7 arquivos mexidos para desfazer.', 'Now switch "read only" off: the agent starts deleting while it explains. Even if you catch the mistake later, there are 7 touched files to undo.'),
              'cmd': T('Rode explorar --so-leitura nao e olhe os arquivos mexidos.', 'Run explore --read-only no and look at the touched files.')},
  'why': {
    'simples': T('Você herdou a cozinha de outra padaria. Um ajudante novo olha tudo e diz, todo seguro: "essa alavanca aí não serve para nada". Antes de arrancar, você segue o fio da alavanca. Às vezes ela desliga o forno.\nCom código antigo é igual: o agente explica muito bem e muito rápido, mas a explicação é um palpite até alguém mostrar onde está escrito.',
                 'You inherited another bakery’s kitchen. A new helper looks around and says, very sure: "that lever does nothing". Before ripping it out, you follow the lever’s wire. Sometimes it turns off the oven.\nOld code is the same: the agent explains very well and very fast, but the explanation is a guess until someone shows where it’s written.'),
    'dev': T('Explore primeiro sem editar: no Claude Code, plan mode (claude --permission-mode plan) lê e propõe sem tocar no disco; no Cursor, o Plan Mode. Peça "uma afirmação por linha, cada uma com arquivo:linha, e marque \'sem evidência\' quando não achar".\nDepois confira o que vai apagar com ferramentas que não chutam: git grep -n "nome" acha o nome em qualquer lugar, inclusive em textos e configs; git log -S "nome" mostra quando ele apareceu ou sumiu; git log --follow conta a história do arquivo. Só então escreva testes de caracterização e apague.',
           'Explore first without editing: in Claude Code, plan mode (claude --permission-mode plan) reads and proposes without touching disk; in Cursor, Plan Mode. Ask for "one statement per line, each with file:line, and mark \'no evidence\' when you can’t find it".\nThen check what you’re about to delete with tools that don’t guess: git grep -n "name" finds the name anywhere, including strings and configs; git log -S "name" shows when it appeared or vanished; git log --follow tells the file’s history. Only then write characterization tests and delete.'),
    'especialista': T('"Ninguém chama esta função" é a afirmação mais cara em código legado, porque chamadas dinâmicas não aparecem em "localizar referências": call_user_func em PHP, rotas montadas com texto, reflexão, jobs de cron, chamadas de outro sistema. O agente costuma raciocinar como a ferramenta de referências e erra junto.\nA cerca de Chesterton vale aqui: não tire a cerca antes de saber por que ela foi posta. Na prática: busca textual em todo o repositório (e nos repositórios vizinhos), logs de produção por algumas semanas e remoção atrás de uma flag antes de apagar de vez.',
                      '"Nobody calls this function" is the most expensive claim in legacy code, because dynamic calls don’t show up in "find references": call_user_func in PHP, routes built from strings, reflection, cron jobs, calls from another system. The agent tends to reason like the references tool and fails with it.\nChesterton’s fence applies: don’t remove the fence before knowing why it was put up. In practice: text search across the whole repo (and neighboring repos), production logs for a few weeks, and removal behind a flag before deleting for good.')},
  'break': {'mission': {'ui': T('hora de quebrar: desligue a busca.', 'time to break it: switch search off.'),
                        'cmd': T(f'hora de quebrar: rode explorar "{TASK6[0][0]}" --buscar nao', f'time to break it: run explore "{TASK6[0][1]}" --search no')},
    'success': T('Quebrou: você acreditou em {believed} afirmação(ões) erradas do agente. {how} Código legado não avisa: ele quebra no fim do mês.',
                 'Broken: you believed {believed} wrong statement(s) from the agent. {how} Legacy code doesn’t warn you: it breaks at the end of the month.'),
    'calm': T('{caught} de {wrong} afirmações erradas pegas antes de apagar qualquer coisa. Para quebrar, desligue a busca ou a exigência de arquivo:linha.',
              '{caught} of {wrong} wrong statements caught before deleting anything. To break it, switch off search or the file:line requirement.')},
  'hints': {'ui': T(['Ligue e desligue as três chaves; a cena atualiza sozinha.', 'Cada afirmação errada é pega por uma ferramenta diferente.', 'Desligue "buscar".'],
                    ['Toggle the three switches; the scene updates by itself.', 'Each wrong statement is caught by a different tool.', 'Switch "search" off.']),
            'cmd': T(['As três chaves aceitam sim ou nao.', '--so-leitura, --citar (arquivo:linha) e --buscar (git grep).', f'explorar "{TASK6[0][0]}" --buscar nao'],
                     ['All three switches take yes or no.', '--read-only, --cite (file:line) and --search (git grep).', f'explore "{TASK6[0][1]}" --search no'])},
  'errors': {'notBool.readOnly': yn(T, 'so-leitura', 'read-only'), 'notBool.cite': yn(T, 'citar', 'cite'), 'notBool.search': yn(T, 'buscar', 'search')},
  'controls': {'arg': T('Tarefa do Rafa', 'Rafa’s task'), 'readOnly': T('Explorar só lendo (plan mode)', 'Explore read-only (plan mode)'),
               'cite': T('Exigir arquivo:linha em cada afirmação', 'Require file:line for each statement'), 'search': T('Conferir com git grep antes de apagar', 'Check with git grep before deleting')},
  'scene': {'label': T('O que o agente disse do módulo', 'What the agent said about the module'), 'empty': T('Rode para ver a explicação do agente.', 'Run to see the agent’s explanation.'),
    'mClaims': T('afirmações do agente', 'agent statements'), 'mCaught': T('erradas e pegas', 'wrong and caught'), 'mBelieved': T('erradas e aceitas', 'wrong and accepted'), 'mEdited': T('arquivos mexidos antes de entender', 'files touched before understanding'),
    'table': T('4 das 10 afirmações', '4 of the 10 statements'), 'colClaim': T('o agente disse', 'the agent said'), 'colStatus': T('situação', 'status'),
    'k1': T('nota usa a tabela nf_itens', 'invoices use the nf_itens table'), 'k2': T('imposto sai de calc_imposto.php', 'tax comes from calc_imposto.php'),
    'kA': T('gerarFechamento() não é usada', 'gerarFechamento() is unused'), 'kB': T('CFOP sempre vem preenchido', 'CFOP is always filled'),
    'stOk': T('confere (arquivo:linha)', 'checks out (file:line)'), 'stCaughtGrep': T('errada: git grep achou', 'wrong: git grep found it'),
    'stCaughtCite': T('errada: sem arquivo:linha', 'wrong: no file:line'), 'stBelieved': T('errada e você acreditou', 'wrong and you believed it'),
    'caption': T('Mesmo tom de confiança nas 10. Só a evidência separa.', 'Same confident tone in all 10. Only evidence tells them apart.'),
    'term': T('Busca antes de apagar', 'Search before deleting'),
    'brokeNote': T('{believed} afirmação(ões) errada(s) viraram decisão. O agente não mentiu de propósito: ele raciocinou pelo que dava para ver.', '{believed} wrong statement(s) became decisions. The agent didn’t lie on purpose: it reasoned from what it could see.'),
    'blindNote': T('Sem só leitura, o agente mexeu em {edited} arquivos enquanto explicava. Explicação e edição no mesmo passo misturam aprender com apostar.', 'Without read-only, the agent touched {edited} files while explaining. Explaining and editing in the same step mixes learning with betting.'),
    'okNote': T('As {wrong} afirmações erradas caíram antes de virar código apagado. Agora dá para escrever testes de caracterização e limpar com calma.', 'The {wrong} wrong statements fell before becoming deleted code. Now you can write characterization tests and clean up calmly.')},
  'data': {'hows': {'01': T('O agente apagou gerarFechamento(), que é chamada por nome no config/cron.php, e o fechamento do mês parou.', 'The agent deleted gerarFechamento(), which is called by name in config/cron.php, and the month-end close stopped.'),
                    '10': T('A nova validação assumiu CFOP sempre preenchido e 3% das notas antigas passaram a dar erro.', 'The new validation assumed CFOP is always filled and 3% of old invoices started failing.'),
                    '00': T('gerarFechamento() foi apagada (o cron do fechamento parou) e a validação nova quebrou 3% das notas antigas, sem CFOP.', 'gerarFechamento() was deleted (the month-end cron stopped) and the new validation broke 3% of old invoices, which have no CFOP.'),
                    '11': ''},
           'grepOn': ['$ git grep -n "gerarFechamento"', "+ config/cron.php:12:  'fechamento' => 'gerarFechamento',", '+ src/nf/fechamento.php:40: function gerarFechamento() {',
                      T('? chamada por nome, via call_user_func: não é código morto', '? called by name, via call_user_func: not dead code')],
           'grepOff': [T('~ nenhuma busca: confiou em "não é usada"', '~ no search: trusted "is unused"'), '$ git rm src/nf/fechamento.php', T('! dia 30: cron "fechamento" falhou', '! day 30: "fechamento" cron failed')]},
  'recipe': {'steps': T([
      'Comece pela história, com git (troque o caminho e o nome pelos do seu projeto):\ngit log --oneline --follow -- src/nf/fechamento.php\ngit grep -n "gerarFechamento"\ngit log -S "gerarFechamento" --oneline',
      'Explore sem editar. No Claude Code:\nclaude --permission-mode plan\nPeça: explique o módulo src/nf/ em até 10 afirmações, uma por linha, cada uma com arquivo:linha. Marque "sem evidência" quando não achar. Não edite nada.\nNo Cursor, use o Plan Mode; no Copilot, faça a pergunta no chat.',
      'Para cada afirmação do tipo "não é usada", rode git grep -n com o nome. Se aparecer em texto, config ou cron, não é código morto. Só depois peça os testes de caracterização e a remoção.'],
     ['Start with the history, using git (swap the path and name for your project’s):\ngit log --oneline --follow -- src/nf/fechamento.php\ngit grep -n "gerarFechamento"\ngit log -S "gerarFechamento" --oneline',
      'Explore without editing. In Claude Code:\nclaude --permission-mode plan\nAsk: explain the src/nf/ module in at most 10 statements, one per line, each with file:line. Mark "no evidence" when you can’t find it. Don’t edit anything.\nIn Cursor, use Plan Mode; in Copilot, ask in chat.',
      'For every "is unused" statement, run git grep -n with the name. If it shows up in a string, config or cron, it isn’t dead code. Only then ask for characterization tests and the removal.']),
    'ok': T('você tem uma lista de afirmações com arquivo:linha, algumas marcadas "sem evidência", e o git grep mostrou pelo menos um uso que a explicação do agente não citou (ou confirmou que não há nenhum).', 'you have a list of statements with file:line, some marked "no evidence", and git grep showed at least one use the agent’s explanation didn’t mention (or confirmed there are none).')}}

t6 = {'pt': {'objectives': ['Explorar código desconhecido sem editar (plan mode).', 'Exigir evidência (arquivo:linha) das afirmações do agente.', 'Conferir "código morto" com busca textual e histórico do git.'], 'minutes': 20,
  'activity': 'A turma pega um repositório aberto antigo e pede ao agente 10 afirmações sobre um módulo, com arquivo:linha. Cada grupo confere 2 afirmações com git grep e git log -S e marca certa, errada ou sem evidência.',
  'discussion': ['Que tipos de chamada não aparecem em "localizar referências" no seu sistema?', 'Quanto tempo de observação em produção você exigiria antes de apagar algo?'],
  'misconceptions': ['"O agente leu o código inteiro, então sabe." Ele vê o que cabe no contexto e raciocina pelo que dá para ver.', '"Se o tom é confiante, deve estar certo." O tom é igual nas afirmações certas e nas erradas.']},
 'en': {'objectives': ['Explore unfamiliar code without editing (plan mode).', 'Require evidence (file:line) for the agent’s statements.', 'Check "dead code" with text search and git history.'], 'minutes': 20,
  'activity': 'The class takes an old open-source repo and asks the agent for 10 statements about a module, with file:line. Each group checks 2 statements with git grep and git log -S and marks them right, wrong or no evidence.',
  'discussion': ['Which kinds of calls don’t show up in "find references" in your system?', 'How long would you watch production before deleting something?'],
  'misconceptions': ['"The agent read the whole codebase, so it knows." It sees what fits in context and reasons from what it can see.', '"If the tone is confident, it must be right." The tone is the same for right and wrong statements.']}}
write('06-legado-e-codigo-desconhecido', s6, loc6('pt'), loc6('en'), t6)


# ====================================================================== 7 · vários agentes em paralelo
ORDER7 = ['cupom', 'agenda', 'relatorio', 'frete']
TASKS7 = {'cupom': {'agent': 25, 'review': 20, 'files': {'src/preco.ts', 'src/cupom.ts', 'tests/cupom.test.ts'}},
          'agenda': {'agent': 35, 'review': 20, 'files': {'src/agenda.ts', 'web/Agenda.tsx'}},
          'relatorio': {'agent': 30, 'review': 15, 'files': {'src/relatorio.ts', 'tests/relatorio.test.ts'}},
          'frete': {'agent': 20, 'review': 15, 'files': {'src/preco.ts', 'src/frete.ts'}}}
REBASE7 = 15

def run7(sel):
    ts = sorted(sel, key=lambda t: (TASKS7[t]['agent'], ORDER7.index(t)))
    end, merged, conflicts, rows, conflictFiles = 0, set(), 0, [], set()
    for t in ts:
        c = TASKS7[t]['files'] & merged
        start = max(end, TASKS7[t]['agent'])
        end = start + TASKS7[t]['review'] + (REBASE7 if c else 0)
        if c: conflicts += 1; conflictFiles |= c
        merged |= TASKS7[t]['files']
        rows.append([f'@t_{t}', len(TASKS7[t]['files']), TASKS7[t]['agent'], end])
    nr_end = max(TASKS7[t]['agent'] for t in ts) + REBASE7 * conflicts
    return {'n': len(ts), 'agentMax': max(TASKS7[t]['agent'] for t in ts), 'reviewSum': sum(TASKS7[t]['review'] for t in ts),
            'wall': end, 'wallNoReview': nr_end, 'seq': sum(TASKS7[t]['agent'] + TASKS7[t]['review'] for t in ts),
            'conflicts': conflicts, 'conflictFile': ', '.join(sorted(conflictFiles)), 'rows': rows}

RUNS7 = {}
for m in range(1, 16):
    sel = [ORDER7[i] for i in range(4) if m & (1 << (3 - i))]
    RUNS7[''.join('1' if t in sel else '0' for t in ORDER7)] = run7(sel)
assert RUNS7['1110']['wall'] == 80 and RUNS7['1110']['seq'] == 145 and RUNS7['1110']['conflicts'] == 0
assert RUNS7['1001']['conflicts'] == 1 and RUNS7['1001']['wall'] == 70
OPTS7 = [opt('cupom', 'cupom', 'coupon'), opt('agenda', 'agenda', 'booking'), opt('relatorio', 'relatorio', 'report'), opt('frete', 'frete', 'delivery')]
ISO7 = [opt('folder', 'mesma-pasta', 'same-folder'), opt('worktree', 'worktree', 'worktree')]
SPRINT7 = ('Sprint da semana: uma tarefa por agente', 'This week’s sprint: one task per agent')

s7 = step('dai-p-agentes-em-paralelo', 7, TRACK, 20, ['paralelo', 'git-worktree', 'isolamento', 'merge', 'revisao'],
  ['dai-p-legado-e-codigo-desconhecido'], ['simulado'], LQ('paralelo', 'parallel'),
  {'name': 'text', 'required': False, 'ui': 'examples', 'default': ex(SPRINT7)[0], 'examples': ex(SPRINT7)},
  [flag('tasks', 'tarefas', 'tasks', 'list', options=OPTS7, default=['cupom', 'agenda', 'relatorio'], ui='checkboxes'),
   flag('iso', 'isolamento', 'isolation', 'enum', options=ISO7, default='worktree', ui='select'),
   flag('review', 'revisar', 'review', 'bool', default=True, ui='switch')],
  {'options': ['agents', 'merge', 'review'], 'answer': 'review'}, 'clobbered',
  {'live': True,
   'consts': {'runs': RUNS7, 'order': ORDER7, 'rebase': REBASE7},
   'compute': {
     'mask': 'memberall(order, tasks)',
     'nT': 'sum(mask)',
     'rk': "join(mask, '')",
     'r': "lookup(runs, rk, runs['1110'])",
     'shared': "iso == 'folder' && nT >= 2",
     'red': 'shared ? nT * (nT - 1) : 0',
     'wallMin': "review ? r.wall : r.wallNoReview",
     'nConf': "iso == 'worktree' ? r.conflicts : 0",
     'tableRows': 'r.rows'},
   'cases': [
     {'when': 'nT == 0', 'error': 'noTasks'},
     {'when': 'shared', 'flags': ['clobbered']},
     {'when': "iso == 'worktree' && r.conflicts > 0", 'flags': ['conflict']},
     {'when': '!review', 'flags': ['unreviewed']},
     {'when': 'review && r.reviewSum > r.agentMax', 'flags': ['reviewBound']},
     {'when': 'true', 'vars': {'n': 'nT', 'red': 'red', 'wall': 'wallMin', 'seq': 'r.seq', 'agentMax': 'r.agentMax', 'reviewSum': 'r.reviewSum',
                               'conflicts': 'nConf', 'conflictFile': 'r.conflictFile', 'rebase': 'rebase'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@mAgents', 'value': '=r.agentMax', 'format': 'min', 'tone': 'info'},
       {'label': '@mReview', 'value': '=review ? r.reviewSum : 0', 'format': 'min', 'tone': "=review ? (r.reviewSum > r.agentMax ? 'warn' : 'ok') : 'bad'"},
       {'label': '@mWall', 'value': '=wallMin', 'format': 'min', 'tone': "=shared ? 'bad' : 'ok'"},
       {'label': '@mSeq', 'value': '=r.seq', 'format': 'min', 'tone': 'dim'},
       {'label': '@mConf', 'value': '=nConf', 'format': 'int', 'tone': "=nConf > 0 ? 'warn' : 'ok'"}]},
     {'type': 'table', 'label': '@table', 'columns': ['@colTask', '@colFiles', '@colAgent', '@colDone'], 'rows': '=tableRows', 'caption': "=review ? '@capReview' : '@capNoReview'"},
     {'type': 'terminal', 'label': '@term', 'lines': "=shared ? termShared : (nConf > 0 ? termConflict : termOk)"},
     {'type': 'note', 'when': '=shared', 'tone': 'bad', 'text': '@sharedNote'},
     {'type': 'note', 'when': '=!shared && nConf > 0', 'tone': 'warn', 'text': '@conflictNote'},
     {'type': 'note', 'when': '=!review', 'tone': 'bad', 'text': '@noReviewNote'},
     {'type': 'note', 'when': '=!shared && review && r.reviewSum > r.agentMax', 'tone': 'info', 'text': '@boundNote'}]})

def loc7(L):
  pt, T = mk(L)
  return {
  'title': T('Vários agentes em paralelo', 'Several agents in parallel'),
  'subtitle': T('Worktrees isolam os arquivos; o merge e a revisão continuam sendo seus', 'Worktrees isolate the files; merging and reviewing are still yours'),
  'mission': T('Sprint da semana: cupom, tela de agendamento, relatório de vendas e, talvez, a mudança do frete. A Bia quer um agente por tarefa, todos ao mesmo tempo. Escolha as tarefas, como isolar os agentes e se ela revisa cada PR. Quanto tempo leva de verdade?',
               'This week’s sprint: coupon, booking screen, sales report and maybe the delivery change. Bia wants one agent per task, all at once. Choose the tasks, how to isolate the agents and whether she reviews each PR. How long does it really take?'),
  'predict': {'question': T('3 agentes em worktrees separados (cupom, agenda, relatório), arquivos diferentes, e a Bia revisa cada PR. O que mais pesa no tempo total?', '3 agents in separate worktrees (coupon, booking, report), different files, and Bia reviews each PR. What weighs most on the total time?'),
    'options': {'agents': T('O trabalho dos agentes', 'The agents’ work'), 'merge': T('Os conflitos de merge', 'Merge conflicts'), 'review': T('A revisão da Bia', 'Bia’s review')}},
  'feedback': {'right': T('isso: os agentes terminam em 35 min, mas a Bia revisa um PR por vez e precisa de 55 min. O total fica em 80 min (contra 145 em fila), e o gargalo passou a ser gente.', 'right: the agents finish in 35 min, but Bia reviews one PR at a time and needs 55 min. The total is 80 min (against 145 in a queue), and the bottleneck is now people.'),
    'wrong': T('a revisão: os agentes acabam em 35 min, a Bia leva 55 min revisando um PR de cada vez. Paralelizar agentes não paraleliza a sua atenção.', 'the review: the agents finish in 35 min, Bia takes 55 min reviewing one PR at a time. Parallel agents don’t parallelize your attention.'),
    'skipped': T('sem palpite? Compare "agentes" com "revisão" nas métricas.', 'no guess? Compare "agents" with "review" in the metrics.')},
  'coach': {'ui': T('palpite anotado. Rode como está; depois marque também o frete.', 'guess noted. Run it as is; then also tick delivery.'),
            'cmd': T('palpite anotado. Rode como está e depois tente --tarefas cupom,frete.', 'guess noted. Run it as is, then try --tasks coupon,delivery.')},
  'tryNext': {'ui': T('Agora marque cupom e frete: as duas mexem em src/preco.ts. Worktree evita que os agentes se atropelem, mas o conflito aparece no merge.', 'Now tick coupon and delivery: both touch src/preco.ts. A worktree keeps the agents from trampling each other, but the conflict shows up at merge.'),
              'cmd': T('Rode paralelo --tarefas cupom,frete e veja o conflito.', 'Run parallel --tasks coupon,delivery and see the conflict.')},
  'why': {
    'simples': T('Três confeiteiros na mesma bancada, com a mesma tigela, fazem bagunça: um põe açúcar na massa do outro. Cada um na sua bancada funciona. Mas no fim alguém precisa provar os três bolos, e essa pessoa só tem uma boca.\nAgentes em paralelo são assim: separar as bancadas é fácil; a prova continua sendo uma de cada vez.',
                 'Three bakers at the same counter, with the same bowl, make a mess: one puts sugar in another’s dough. Each at their own counter works. But at the end someone has to taste all three cakes, and that person has only one mouth.\nParallel agents are like that: separating the counters is easy; the tasting is still one at a time.'),
    'dev': T('git worktree cria outra pasta de trabalho do mesmo repositório, com outro branch: git worktree add ../encomendas-cupom -b feat/cupom. Cada agente roda na sua pasta; git worktree list mostra todas; git worktree remove limpa. O git não deixa o mesmo branch em dois worktrees.\nNo Claude Code, claude --worktree cupom cria .claude/worktrees/cupom num branch worktree-cupom (coloque .claude/worktrees/ no .gitignore; .worktreeinclude copia arquivos como .env). No Cursor, cada agente em paralelo roda no seu worktree (.cursor/worktrees.json prepara o ambiente, /apply-worktree traz o resultado). O agente na nuvem do Copilot trabalha num branch e abre um PR por tarefa.',
           'git worktree creates another working folder of the same repository, on another branch: git worktree add ../encomendas-cupom -b feat/cupom. Each agent runs in its own folder; git worktree list shows them all; git worktree remove cleans up. Git won’t let the same branch be checked out in two worktrees.\nIn Claude Code, claude --worktree cupom creates .claude/worktrees/cupom on a worktree-cupom branch (add .claude/worktrees/ to .gitignore; .worktreeinclude copies files like .env). In Cursor, each parallel agent runs in its own worktree (.cursor/worktrees.json sets up the environment, /apply-worktree brings the result back). Copilot’s cloud agent works on a branch and opens one PR per task.'),
    'especialista': T('Worktree isola arquivos, não decisões: duas tarefas que mexem no mesmo módulo vão conflitar no merge, então escolha tarefas paralelas por fronteira de arquivos e faça merge do menor primeiro. Worktrees compartilham o mesmo .git; um worktree novo é um checkout limpo (instale dependências, copie .env).\nO limite real é revisão e contexto humano: se a revisão soma mais que o trabalho dos agentes, mais agentes só aumentam a fila. Os tempos aqui são inventados. No Claude Code também dá para isolar subagentes com isolation: worktree; no Cursor, o padrão é até 25 worktrees por máquina.',
                      'A worktree isolates files, not decisions: two tasks that touch the same module will conflict at merge, so pick parallel tasks along file boundaries and merge the smaller one first. Worktrees share the same .git; a new worktree is a clean checkout (install dependencies, copy .env).\nThe real limit is review and human context: if review adds up to more than the agents’ work, more agents only grow the queue. The times here are made up. In Claude Code you can also isolate subagents with isolation: worktree; in Cursor, the default is up to 25 worktrees per machine.')},
  'break': {'mission': {'ui': T('hora de quebrar: troque o isolamento para "mesma pasta".', 'time to break it: switch isolation to "same folder".'),
                        'cmd': T('hora de quebrar: rode paralelo --isolamento mesma-pasta', 'time to break it: run parallel --isolation same-folder')},
    'success': T('Quebrou: {n} agentes na mesma pasta dividem os mesmos arquivos e o mesmo branch. {red} rodadas de teste falharam com código pela metade de outro agente, e o PR saiu misturando {n} tarefas que ninguém consegue revisar separado.',
                 'Broken: {n} agents in the same folder share the same files and the same branch. {red} test runs failed on another agent’s half-written code, and the PR came out mixing {n} tasks nobody can review separately.'),
    'calm': T('{n} tarefa(s) isoladas: {wall} min no total (em fila seriam {seq}), com {conflicts} conflito(s) de merge. Para quebrar, ponha os agentes na mesma pasta.',
              '{n} isolated task(s): {wall} min in total ({seq} in a queue), with {conflicts} merge conflict(s). To break it, put the agents in the same folder.')},
  'hints': {'ui': T(['Marque tarefas e troque o isolamento; a cena atualiza sozinha.', 'Cupom e frete mexem no mesmo arquivo; agenda e relatório não.', 'Isolamento "mesma pasta" com 2 ou mais tarefas.'],
                    ['Tick tasks and switch isolation; the scene updates by itself.', 'Coupon and delivery touch the same file; booking and report don’t.', 'Isolation "same folder" with 2 or more tasks.']),
            'cmd': T(['--tarefas recebe uma lista: cupom, agenda, relatorio, frete.', '--isolamento aceita mesma-pasta ou worktree; --revisar aceita sim ou nao.', 'paralelo --isolamento mesma-pasta'],
                     ['--tasks takes a list: coupon, booking, report, delivery.', '--isolation takes same-folder or worktree; --review takes yes or no.', 'parallel --isolation same-folder'])},
  'errors': {'notInEnum.tasks': T('“{value}” não é uma tarefa da sprint. Opções: {options}.', '“{value}” isn’t a sprint task. Options: {options}.'),
             'notInEnum.iso': T('“{value}” não é um isolamento daqui. Opções: {options}.', '“{value}” isn’t an isolation option here. Options: {options}.'),
             'notBool.review': yn(T, 'revisar', 'review'), 'model.noTasks': T('Escolha pelo menos uma tarefa.', 'Pick at least one task.')},
  'controls': {'arg': T('Sprint', 'Sprint'), 'tasks': T('Tarefas (um agente cada)', 'Tasks (one agent each)'), 'iso': T('Isolamento', 'Isolation'), 'review': T('Bia revisa cada PR', 'Bia reviews each PR')},
  'scene': {'label': T('A sprint em paralelo', 'The sprint in parallel'), 'empty': T('Rode para ver a sprint.', 'Run to see the sprint.'),
    'mAgents': T('agentes (o mais lento)', 'agents (the slowest)'), 'mReview': T('revisão da Bia', 'Bia’s review'), 'mWall': T('tempo total', 'total time'),
    'mSeq': T('em fila, um por vez', 'queued, one at a time'), 'mConf': T('conflitos de merge', 'merge conflicts'),
    'table': T('Tarefas', 'Tasks'), 'colTask': T('tarefa', 'task'), 'colFiles': T('arquivos', 'files'), 'colAgent': T('agente (min)', 'agent (min)'), 'colDone': T('merge no min', 'merged at min'),
    't_cupom': T('cupom', 'coupon'), 't_agenda': T('tela de agendamento', 'booking screen'), 't_relatorio': T('relatório de vendas', 'sales report'), 't_frete': T('mudança do frete', 'delivery change'),
    'capReview': T('A Bia revisa um PR por vez, na ordem em que ficam prontos. Tempos inventados.', 'Bia reviews one PR at a time, in the order they finish. Made-up times.'),
    'capNoReview': T('Sem revisão: merge assim que o agente termina. Tempos inventados.', 'No review: merge as soon as the agent finishes. Made-up times.'),
    'term': T('No terminal da Bia', 'In Bia’s terminal'),
    'sharedNote': T('Mesma pasta: os {n} agentes escrevem nos mesmos arquivos e no mesmo branch. Um roda os testes enquanto o outro está no meio de uma edição.', 'Same folder: the {n} agents write to the same files and the same branch. One runs the tests while another is mid-edit.'),
    'conflictNote': T('{conflictFile} foi mexido por duas tarefas: o segundo merge precisa de rebase e de uma revisão a mais (+{rebase} min). Worktree não evita conflito; escolher tarefas com arquivos separados evita.', '{conflictFile} was touched by two tasks: the second merge needs a rebase and one more review (+{rebase} min). A worktree doesn’t prevent conflicts; picking tasks with separate files does.'),
    'noReviewNote': T('Mais rápido ({wall} min), mas {n} PR(s) entraram sem ninguém ler. Os erros dos agentes chegam juntos, e na loja.', 'Faster ({wall} min), but {n} PR(s) went in without anyone reading them. The agents’ mistakes arrive together, and in the shop.'),
    'boundNote': T('Os agentes terminam em {agentMax} min; a revisão soma {reviewSum} min. O gargalo agora é a Bia: mais agentes só aumentariam a fila dela.', 'The agents finish in {agentMax} min; review adds up to {reviewSum} min. The bottleneck is now Bia: more agents would only grow her queue.')},
  'data': {'termOk': ['$ git worktree list', '+ ~/encomendas            main', '+ ~/encomendas-cupom      [feat/cupom]', '+ ~/encomendas-agenda     [feat/agenda]',
                      '$ git merge feat/cupom', T('+ merge sem conflito', '+ merged without conflict')],
           'termConflict': ['$ git merge feat/frete', T('+ merge sem conflito', '+ merged without conflict'), '$ git merge feat/cupom',
                            'CONFLICT (content): Merge conflict in src/preco.ts', T('? resolva, rode npm test, peça nova revisão', '? resolve it, run npm test, ask for another review')],
           'termShared': ['$ git status --short', ' M src/preco.ts', ' M src/agenda.ts', ' M src/relatorio.ts', '$ npm test',
                          T('! agente do cupom: falhou em src/agenda.ts (pela metade)', '! coupon agent: failed in src/agenda.ts (half-written)')]},
  'recipe': {'steps': T([
      'Crie um worktree por tarefa, cada um no seu branch, e confira:\ngit worktree add ../encomendas-cupom -b feat/cupom\ngit worktree add ../encomendas-agenda -b feat/agenda\ngit worktree list',
      'Em um terminal por worktree, prepare e abra o agente da sua escolha:\ncd ../encomendas-cupom\nnpm install\nclaude\nNo Claude Code também dá para pular o passo 1 com claude --worktree cupom. No Cursor, use os agentes em paralelo (cada um ganha um worktree). No Copilot, atribua cada issue ao Copilot e ele abre um PR por tarefa.',
      'Revise e faça merge de um por vez, a partir do main. Se der conflito, resolva, rode os testes e peça nova revisão. Depois limpe:\ngit merge feat/cupom\ngit worktree remove ../encomendas-cupom\ngit branch -d feat/cupom'],
     ['Create one worktree per task, each on its own branch, and check:\ngit worktree add ../encomendas-cupom -b feat/cupom\ngit worktree add ../encomendas-agenda -b feat/agenda\ngit worktree list',
      'In one terminal per worktree, set up and open the agent of your choice:\ncd ../encomendas-cupom\nnpm install\nclaude\nIn Claude Code you can also skip step 1 with claude --worktree cupom. In Cursor, use parallel agents (each gets a worktree). In Copilot, assign each issue to Copilot and it opens one PR per task.',
      'Review and merge one at a time, from main. If there’s a conflict, resolve it, run the tests and ask for another review. Then clean up:\ngit merge feat/cupom\ngit worktree remove ../encomendas-cupom\ngit branch -d feat/cupom']),
    'ok': T('git worktree list mostra a pasta principal e uma linha por tarefa, cada uma com seu branch, e o git status de cada worktree só mostra os arquivos daquela tarefa.', 'git worktree list shows the main folder and one line per task, each on its own branch, and git status in each worktree shows only that task’s files.')}}

t7 = {'pt': {'objectives': ['Isolar agentes paralelos com git worktree.', 'Escolher tarefas paralelas por fronteira de arquivos.', 'Perceber que a revisão vira o gargalo.'], 'minutes': 25,
  'activity': 'A turma monta um quadro com 5 tarefas reais de um sistema e a lista de arquivos de cada uma. Em grupos, escolhem quais rodar em paralelo sem conflito e calculam, com tempos estimados, quando a pessoa que revisa termina.',
  'discussion': ['Quantos PRs de agente você consegue revisar bem num dia?', 'O que muda se duas pessoas revisam em vez de uma?'],
  'misconceptions': ['"Com worktree não tem conflito." Worktree separa as pastas; duas tarefas no mesmo arquivo ainda conflitam no merge.', '"Mais agentes, entrega mais rápida." Só até a revisão virar a fila.']},
 'en': {'objectives': ['Isolate parallel agents with git worktree.', 'Pick parallel tasks along file boundaries.', 'Notice that review becomes the bottleneck.'], 'minutes': 25,
  'activity': 'The class builds a board with 5 real tasks from a system and each one’s file list. In groups, they pick which can run in parallel without conflicts and compute, with estimated times, when the reviewer finishes.',
  'discussion': ['How many agent PRs can you review well in a day?', 'What changes if two people review instead of one?'],
  'misconceptions': ['"With worktrees there are no conflicts." Worktrees separate folders; two tasks in the same file still conflict at merge.', '"More agents, faster delivery." Only until review becomes the queue.']}}
write('07-agentes-em-paralelo', s7, loc7('pt'), loc7('en'), t7)
print('dai_p1: 7 lessons written')
