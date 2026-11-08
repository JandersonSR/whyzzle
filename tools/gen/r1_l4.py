"""R1 · 04 · testes de regressão no CI."""
from r1_common import *

N, NCRIT, BASE = 60, 20, 51
C_SHORT = LQ('encurtar o prompt de sistema', 'shorten the system prompt')
C_CHEAP = LQ('trocar para um modelo mais barato', 'switch to a cheaper model')
C_CHUNK = LQ('aumentar os trechos para 200 palavras', 'make chunks 200 words long')
C_TYPO = LQ('corrigir um erro de digitação no README', 'fix a typo in the README')
CHANGES = [(C_SHORT, 50, 18, True), (C_CHEAP, 46, 20, True), (C_CHUNK, 53, 20, False), (C_TYPO, 51, 20, False)]
pct = lambda h: round(h / N * 100)
assert [pct(x) for x in (51, 50, 46, 53)] == [85, 83, 77, 88]

s = step('r-testes-de-regressao-no-ci', 4, 20, ['avaliacao', 'ci', 'regressao', 'github-actions', 'portao'],
 ['r-llm-como-juiz'], ['simulado'], LQ('ci', 'ci'),
 {'name': 'text', 'required': False, 'ui': 'examples', 'default': C_SHORT, 'examples': ex(C_SHORT, C_CHEAP, C_CHUNK, C_TYPO)},
 [flag('limit', 'limite', 'threshold', 'number', min=0.5, max=0.95, step=0.01, default=0.8, ui='slider'),
  flag('maxDrop', 'queda', 'max-drop', 'int', min=0, max=20, default=3, ui='slider'),
  flag('critical', 'criticos', 'critical', 'bool', default=True, ui='switch')],
 {'options': ['pass', 'block'], 'answer': 'block'}, 'shipped',
 {'live': True,
  'consts': {'nCases': N, 'nCrit': NCRIT, 'baseHits': BASE},
  'compute': {
   'rec': 'lookup(changes, text, unknownChange)',
   'known': 'rec.known',
   'scorePct': 'round(rec.hits / nCases * 100)',
   'basePct': 'round(baseHits / nCases * 100)',
   'limitPct': 'round(limit * 100)',
   'drop': 'basePct - scorePct',
   'okScore': 'scorePct >= limitPct',
   'okDrop': 'drop <= maxDrop',
   'critAll': 'rec.crit == nCrit',
   'okCrit': '!critical || critAll',
   'isGreen': 'okScore && okDrop && okCrit',
   'critL': 'critical ? critOn : critOff',
   'logLines': ("concat(['$ python gate.py ' + limit, '~ score ' + scorePct + '% (main ' + basePct + '%) · critical ' + rec.crit + '/' + nCrit],"
                " okScore ? [] : ['! ' + lineScore], okDrop ? [] : ['! ' + lineDrop], okCrit ? [] : ['! ' + lineCrit],"
                " (!critical && !critAll) ? ['? ' + lineCritOff] : [], [isGreen ? '+ PASSED' : '! FAILED'])")},
  'cases': [
   {'when': '!known', 'error': 'unknownChange'},
   {'when': 'known && isGreen', 'flags': ['green']},
   {'when': 'known && !isGreen', 'flags': ['red']},
   {'when': 'known && isGreen && rec.regressed', 'flags': ['shipped']},
   {'when': 'known && !isGreen && rec.regressed', 'flags': ['blocked']},
   {'when': 'known && !isGreen && !rec.regressed', 'flags': ['needless']},
   {'when': 'true', 'vars': {'change': 'text', 'damage': 'rec.damage', 'scorePct': 'scorePct', 'basePct': 'basePct', 'limitPct': 'limitPct',
                             'maxDrop': 'maxDrop', 'critL': 'critL', 'crit': 'rec.crit', 'nCrit': 'nCrit', 'drop': 'drop'}}],
  'widgets': [
   {'type': 'flow', 'steps': [{'label': '@sPR', 'sub': '=text', 'tone': 'info'},
                              {'label': '@sEval', 'sub': '@subEval', 'tone': 'neutral'},
                              {'label': '@sGate', 'sub': "=isGreen ? '@subGreen' : '@subRed'", 'tone': "=isGreen ? 'ok' : 'bad'"},
                              {'label': '@sMain', 'sub': "=isGreen ? '@subMerged' : '@subBlocked'", 'tone': "=isGreen && rec.regressed ? 'bad' : (isGreen ? 'ok' : 'warn')"}]},
   {'type': 'terminal', 'label': '@log', 'lines': '=logLines'},
   {'type': 'checks', 'label': '@checks', 'items': [
     {'label': '@chkScore', 'ok': '=okScore', 'why': '@whyScore'},
     {'label': '@chkDrop', 'ok': '=okDrop', 'why': '@whyDrop'},
     {'label': '@chkCrit', 'ok': "=critical ? critAll : !rec.regressed || critAll", 'why': "=critical ? '@whyCrit' : '@whyCritOff'"}]},
   {'type': 'metrics', 'items': [
     {'label': '@mScore', 'value': '=scorePct', 'format': 'pct', 'tone': "=okScore ? 'ok' : 'bad'"},
     {'label': '@mBase', 'value': '=basePct', 'format': 'pct', 'tone': 'dim'},
     {'label': '@mCrit', 'value': "=rec.crit + ' / ' + nCrit", 'tone': "=critAll ? 'ok' : 'bad'"}]},
   {'type': 'note', 'when': '=isGreen && rec.regressed', 'tone': 'bad', 'text': '@shippedNote'},
   {'type': 'note', 'when': '=!isGreen && !rec.regressed', 'tone': 'warn', 'text': '@needlessNote'},
   {'type': 'note', 'tone': 'info', 'text': '@simNote'}]})

GATE = '''import json
import pathlib
import sys

from assistant import handle

SET = pathlib.Path("evals/rh/2026-10.jsonl")
MIN_SCORE = float(sys.argv[1]) if len(sys.argv) > 1 else 0.80
MAX_DROP = 0.03
EXPECTED = {"answer": "answer", "outside": "refuse", "sensitive": "handoff"}

cases = [json.loads(line) for line in SET.read_text(encoding="utf-8").splitlines() if line.strip()]
BASELINE = pathlib.Path("evals/rh/baseline.json")
baseline = json.loads(BASELINE.read_text()) if BASELINE.exists() else {"score": 0.0}

fails = []
critical_fails = []
for case in cases:
    r = handle(case["question"])
    ok = r["action"] == EXPECTED[case["kind"]]
    if ok and case["kind"] == "answer":
        ok = bool(set(r["cited"]) & set(case["gold"]))
    if not ok:
        fails.append(case["id"])
        if case["kind"] != "answer":
            critical_fails.append(case["id"])

score = 1 - len(fails) / len(cases)
print(f"score {score:.0%} (main {baseline['score']:.0%}) | failed: {fails}")

problems = []
if score < MIN_SCORE:
    problems.append(f"score below {MIN_SCORE:.0%}")
if baseline["score"] - score > MAX_DROP:
    problems.append(f"dropped more than {MAX_DROP:.0%} vs main")
if critical_fails:
    problems.append(f"critical cases failed: {critical_fails}")

if problems:
    sys.exit("FAILED: " + "; ".join(problems))
print("PASSED")'''

WORKFLOW = '''name: eval-rh

on:
  pull_request:
    paths:
      - "assistant.py"
      - "corpus.py"
      - "evals/**"

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install torch --index-url https://download.pytorch.org/whl/cpu
      - run: pip install sentence-transformers rank_bm25 anthropic
      - run: python gate.py 0.80
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}'''


def loc(L):
    pt = L == 'pt'; T = lambda a, b: a if pt else b
    cheat = T(f'ci "{C_SHORT[L]}" --criticos nao', f'ci "{C_SHORT[L]}" --critical no')
    damage = {C_SHORT[L]: T('2 das 20 perguntas críticas (fora do manual ou delicadas) passaram a receber resposta inventada', '2 of the 20 critical questions (outside the handbook or delicate) started getting made-up answers'),
              C_CHEAP[L]: T('a nota caiu de 85% para 77%, 8 pontos a menos', 'the score fell from 85% to 77%, 8 points down'),
              C_CHUNK[L]: '', C_TYPO[L]: ''}
    changes = {c[L]: {'known': True, 'hits': h, 'crit': cr, 'regressed': reg, 'damage': damage[c[L]]} for c, h, cr, reg in CHANGES}
    return {
  'title': T('Testes de regressão no CI', 'Regression tests in CI'),
  'subtitle': T('Todo PR que mexe no assistente roda o conjunto e pode ficar vermelho', 'Every PR that touches the assistant runs the set and can turn red'),
  'mission': T('Na Aurora, qualquer pessoa do time abre PR no assistente: prompt, modelo, tamanho dos trechos. Agora cada PR roda o conjunto 2026-10 (60 perguntas, 20 delas críticas: fora do manual ou delicadas) no GitHub Actions, e o portão decide se dá para fazer merge. Ajuste o portão para barrar o que piora e deixar passar o que melhora.',
               'At Aurora, anyone on the team opens PRs on the assistant: prompt, model, chunk size. Now every PR runs set 2026-10 (60 questions, 20 of them critical: outside the handbook or delicate) on GitHub Actions, and the gate decides whether it can be merged. Tune the gate to block what gets worse and let through what gets better.'),
  'predict': {'question': T('o PR "encurtar o prompt de sistema" baixa a nota de 85% para 83%, acima do limite de 80% e dentro da queda máxima de 3 pontos. O CI…',
                            'the PR "shorten the system prompt" lowers the score from 85% to 83%, above the 80% threshold and within the 3-point max drop. CI…'),
              'options': {'pass': T('Fica verde', 'Goes green'), 'block': T('Fica vermelho', 'Goes red')}},
  'feedback': {'right': T('isso: a média quase não mexeu, mas 2 das 20 perguntas críticas passaram a ganhar resposta inventada. Caso crítico não entra na média: basta um para barrar.',
                          'right: the average barely moved, but 2 of the 20 critical questions started getting made-up answers. Critical cases don’t go into the average: one is enough to block.'),
               'wrong': T('fica vermelho: a média quase não mexeu, mas 2 das 20 perguntas críticas passaram a ganhar resposta inventada. Caso crítico não entra na média: basta um para barrar.',
                          'it goes red: the average barely moved, but 2 of the 20 critical questions started getting made-up answers. Critical cases don’t go into the average: one is enough to block.'),
               'skipped': T('sem palpite? Rode o PR do prompt curto e leia o log.', 'no guess? Run the short-prompt PR and read the log.')},
  'coach': {'ui': T('palpite anotado. Escolha o PR do prompt curto e rode com o portão padrão.', 'guess noted. Pick the short-prompt PR and run with the default gate.'),
            'cmd': T(f'palpite anotado. Rode ci "{C_SHORT[L]}" e leia o log.', f'guess noted. Run ci "{C_SHORT[L]}" and read the log.')},
  'tryNext': {'ui': T('Agora o PR dos trechos maiores: ele melhora. Suba o limite para 90% e veja o portão barrar uma melhoria.', 'Now the bigger-chunks PR: it improves things. Raise the threshold to 90% and watch the gate block an improvement.'),
              'cmd': T(f'Rode ci "{C_CHUNK[L]}" --limite 0.9 e veja quem o portão barrou.', f'Run ci "{C_CHUNK[L]}" --threshold 0.9 and see what the gate blocked.')},
  'why': {'simples': T('Antes de servir um prato novo, a cozinha prova. Se a receita mudou (menos sal, outro fornecedor), prova de novo, sempre do mesmo jeito. E tem coisa que nunca pode acontecer, como amendoim no prato de quem tem alergia: aí não importa se o resto ficou gostoso.\nO CI é essa prova automática: cada mudança no assistente roda as mesmas perguntas, e o merge só acontece se a nota não cair e nenhum caso crítico falhar.',
                       'Before serving a new dish, the kitchen tastes it. If the recipe changed (less salt, another supplier), it tastes again, always the same way. And some things must never happen, like peanuts in the dish of someone allergic: then it doesn’t matter how good the rest is.\nCI is that automatic tasting: every change to the assistant runs the same questions, and the merge only happens if the score doesn’t drop and no critical case fails.'),
          'dev': T('O portão tem três regras, cada uma pegando um tipo de regressão: nota mínima absoluta (o modelo mais barato cai para 77%), queda máxima contra o main (o baseline gravado no último merge) e casos críticos que bloqueiam sozinhos, fora da média (recusar o que não está no manual, passar assédio para uma pessoa). O script sai com código diferente de zero quando alguma falha, e o GitHub Actions marca o job como falho; com a regra de proteção da branch exigindo esse job, o merge fica bloqueado.\nRode o eval só quando mudar o que afeta respostas (filtro de paths), fixe a versão do modelo, guarde o log de casos que viraram e atualize baseline.json só depois do merge. Avaliação com LLM varia um pouco entre rodadas: deixe uma folga de alguns pontos na queda máxima e, nos casos críticos, rode mais de uma vez antes de culpar o PR.',
                   'The gate has three rules, each catching a kind of regression: an absolute minimum score (the cheaper model drops to 77%), a maximum drop against main (the baseline stored at the last merge) and critical cases that block on their own, outside the average (refusing what isn’t in the handbook, handing harassment to a person). The script exits non-zero when any fails, and GitHub Actions marks the job as failed; with a branch protection rule requiring that job, the merge is blocked.\nRun the eval only when what affects answers changes (paths filter), pin the model version, keep the log of flipped cases and update baseline.json only after merging. LLM evaluation varies a little between runs: leave a few points of slack in the max drop and, for critical cases, run more than once before blaming the PR.'),
          'especialista': T('Regressão também chega sem PR. Em janeiro de 2024, o chatbot de atendimento da DPD, no Reino Unido, xingou um cliente e escreveu um poema falando mal da empresa; a DPD atribuiu o caso a um erro depois de uma atualização do sistema e desligou a parte de IA. Mudança de modelo do provedor, de índice ou de dependência é mudança de produção: rode o mesmo portão agendado (todo dia, por exemplo) e a cada troca de versão, não só em PR.\nO custo importa: 60 perguntas com juiz LLM por PR é barato; 5.000 não. Separe um conjunto de fumaça rápido para todo PR e o completo para o merge no main ou para a noite. E lembre que o portão só pega o que o conjunto tem: caso crítico que ninguém escreveu não bloqueia nada (próximas lições: casos difíceis e feedback de usuários).',
                            'Regressions also arrive without a PR. In January 2024, UK delivery firm DPD’s support chatbot swore at a customer and wrote a poem criticizing the company; DPD blamed an error after a system update and switched the AI part off. A provider model change, an index change or a dependency bump is a production change: run the same gate on a schedule (daily, say) and on every version bump, not only on PRs.\nCost matters: 60 questions with an LLM judge per PR is cheap; 5,000 isn’t. Keep a fast smoke set for every PR and the full one for merges to main or nightly. And remember the gate only catches what the set contains: a critical case nobody wrote blocks nothing (next lessons: hard cases and user feedback).')},
  'break': {'mission': {'ui': T('hora de quebrar: PR do prompt curto com os casos críticos desligados no portão.', 'time to break it: the short-prompt PR with critical cases turned off in the gate.'),
                        'cmd': T(f'hora de quebrar: rode {cheat}', f'time to break it: run {cheat}')},
            'success': T('Quebrou: o CI ficou verde e o PR "{change}" entrou no main, mas {damage}. O portão olhava nota de pelo menos {limitPct}%, queda de até {maxDrop} pontos e casos críticos {critL}. Regressão que o portão não mede vai para produção.',
                         'Broken: CI went green and the PR "{change}" landed on main, but {damage}. The gate checked a score of at least {limitPct}%, a drop of up to {maxDrop} points and critical cases {critL}. A regression the gate doesn’t measure goes to production.'),
            'calm': T('PR "{change}": {scorePct}% (main {basePct}%), críticos {crit}/{nCrit}. Para quebrar, deixe uma regressão passar pelo portão.',
                      'PR "{change}": {scorePct}% (main {basePct}%), critical {crit}/{nCrit}. To break it, let a regression through the gate.')},
  'hints': {'ui': T(['Escolha um PR e rode. O log mostra o que o portão conferiu.', 'Limite é a nota mínima; queda é quantos pontos pode cair contra o main; críticos bloqueiam sozinhos quando ligados.', 'PR do prompt curto, críticos desligados.'],
                    ['Pick a PR and run. The log shows what the gate checked.', 'Threshold is the minimum score; max drop is how many points it may fall against main; critical cases block on their own when on.', 'Short-prompt PR, critical cases off.']),
            'cmd': T(['O PR vai entre aspas, depois de ci.', '--limite de 0,5 a 0,95; --queda de 0 a 20 pontos; --criticos sim ou nao.', cheat],
                     ['The PR goes in quotes, after ci.', '--threshold 0.5 to 0.95; --max-drop 0 to 20 points; --critical yes or no.', cheat])},
  'errors': {'belowMin.limit': T('Abaixo de 50% o portão aceita quase qualquer coisa.', 'Below 50% the gate accepts almost anything.'), 'aboveMax.limit': T('Acima de 95% quase nenhum PR passa.', 'Above 95% almost no PR passes.'),
             'belowMin.maxDrop': T('A queda é de 0 a 20 pontos.', 'The drop goes from 0 to 20 points.'), 'aboveMax.maxDrop': T('Mais de 20 pontos de queda permitida é portão aberto.', 'More than 20 points of allowed drop is an open gate.'),
             'notBool.critical': yn(T), 'model.unknownChange': T('Escolha um dos quatro PRs de exemplo: só eles têm resultado de avaliação nesta lição.', 'Pick one of the four example PRs: only they have evaluation results in this lesson.')},
  'controls': {'arg': 'Pull request', 'limit': T('Nota mínima', 'Minimum score'), 'maxDrop': T('Queda máxima contra o main (pontos)', 'Max drop against main (points)'), 'critical': T('Casos críticos bloqueiam', 'Critical cases block')},
  'scene': {'label': T('Portão de avaliação no CI', 'Evaluation gate in CI'), 'empty': T('Rode para abrir o PR.', 'Run to open the PR.'),
    'sPR': 'PR', 'sEval': T('Avaliação', 'Evaluation'), 'subEval': T('2026-10 · 60 perguntas', '2026-10 · 60 questions'), 'sGate': T('Portão', 'Gate'),
    'subGreen': T('verde', 'green'), 'subRed': T('vermelho', 'red'), 'sMain': 'main', 'subMerged': T('merge feito', 'merged'), 'subBlocked': T('merge bloqueado', 'merge blocked'),
    'log': T('Log do job eval', 'eval job log'), 'checks': T('Regras do portão', 'Gate rules'),
    'chkScore': T('Nota mínima', 'Minimum score'), 'whyScore': T('{scorePct}%, abaixo de {limitPct}%', '{scorePct}%, below {limitPct}%'),
    'chkDrop': T('Queda contra o main', 'Drop against main'), 'whyDrop': T('caiu {drop} pontos; o máximo é {maxDrop}', 'dropped {drop} points; the max is {maxDrop}'),
    'chkCrit': T('Casos críticos', 'Critical cases'), 'whyCrit': T('{crit} de {nCrit} críticos passaram', '{crit} of {nCrit} critical cases passed'),
    'whyCritOff': T('desligado no portão, e {crit} de {nCrit} críticos passaram', 'off in the gate, and {crit} of {nCrit} critical cases passed'),
    'mScore': T('nota do PR', 'PR score'), 'mBase': T('nota do main', 'main score'), 'mCrit': T('críticos', 'critical'),
    'shippedNote': T('Verde, mas regrediu: {damage}.', 'Green, but it regressed: {damage}.'),
    'needlessNote': T('Este PR não piora nada (nota {scorePct}%, main {basePct}%), e o portão barrou mesmo assim. Portão apertado demais ensina o time a ignorar o vermelho.', 'This PR makes nothing worse (score {scorePct}%, main {basePct}%), and the gate blocked it anyway. A gate that’s too tight teaches the team to ignore red.'),
    'simNote': T('Resultados fixos da lição para cada PR no conjunto 2026-10. Na receita, o mesmo portão roda de verdade no GitHub Actions.', 'Fixed lesson results for each PR on set 2026-10. In the recipe, the same gate runs for real on GitHub Actions.')},
  'data': {'changes': changes, 'unknownChange': {'known': False, 'hits': 0, 'crit': 0, 'regressed': False, 'damage': ''},
           'critOn': T('obrigatórios', 'required'), 'critOff': T('desligados', 'turned off'),
           'lineScore': T('score abaixo do limite', 'score below threshold'), 'lineDrop': T('caiu mais que o permitido contra o main', 'dropped more than allowed vs main'),
           'lineCrit': T('casos críticos falharam', 'critical cases failed'), 'lineCritOff': T('casos críticos falharam, mas o portão não olha', 'critical cases failed, but the gate isn’t looking')},
  'recipe': {'steps': [
     T('No repositório do assistente (com assistant.py da missão de Prática e o evals/rh/2026-10.jsonl da lição 1), crie gate.py. Ele roda o conjunto, compara com o baseline do main e sai com erro se a nota ficar abaixo do mínimo, cair mais de 3 pontos ou se algum caso crítico (tipo outside ou sensitive) falhar:\n',
       'In the assistant’s repository (with assistant.py from the Practice mission and evals/rh/2026-10.jsonl from lesson 1), create gate.py. It runs the set, compares with main’s baseline and exits with an error if the score falls below the minimum, drops more than 3 points or any critical case (kind outside or sensitive) fails:\n') + GATE,
     T('Rode no main (sem baseline.json, a queda não é conferida) e grave o baseline, trocando 0.85 pela nota que você obteve:\npython gate.py 0.0\necho \'{"score": 0.85}\' > evals/rh/baseline.json',
       'Run it on main (without baseline.json the drop isn’t checked) and store the baseline, replacing 0.85 with the score you got:\npython gate.py 0.0\necho \'{"score": 0.85}\' > evals/rh/baseline.json'),
     T('Crie .github/workflows/eval-rh.yml. Ele roda em todo PR que mexe no assistente, no corpus ou no conjunto:\n', 'Create .github/workflows/eval-rh.yml. It runs on every PR that touches the assistant, the corpus or the set:\n') + WORKFLOW,
     T('Guarde a chave em Settings > Secrets and variables > Actions com o nome ANTHROPIC_API_KEY (PRs vindos de fork não recebem segredos). Em Settings > Branches, crie uma regra de proteção para o main exigindo o check "eval". Depois abra um PR que apaga a frase de recusa do SYSTEM.',
       'Store the key in Settings > Secrets and variables > Actions as ANTHROPIC_API_KEY (PRs from forks don’t get secrets). In Settings > Branches, add a protection rule for main requiring the "eval" check. Then open a PR that deletes the refusal sentence from SYSTEM.')],
   'ok': T('o job eval do PR fica vermelho com "FAILED: critical cases failed: [...]" e o botão de merge fica bloqueado; ao desfazer a mudança, o job fica verde com PASSED.',
           'the PR’s eval job turns red with "FAILED: critical cases failed: [...]" and the merge button is blocked; when you undo the change, the job turns green with PASSED.')}}


def tch():
    return teacher(
 {'objectives': ['Rodar o conjunto de avaliação em cada PR.', 'Combinar nota mínima, queda máxima e casos críticos.', 'Reconhecer regressões que a média esconde.'], 'minutes': 20,
  'activity': 'A turma escreve 3 regras de portão num cartaz. O professor anuncia PRs fictícios com nota, queda e casos críticos; a turma decide verde ou vermelho e confere se alguma regressão passou.',
  'discussion': ['Que caso, na sua empresa, deveria bloquear sozinho, mesmo com a média boa?', 'Quem pode mudar o limite do portão, e com que justificativa?'],
  'misconceptions': ['"A média subiu, então pode subir." Um caso crítico quebrado vale mais que a média.', '"Portão mais rígido é sempre melhor." Ele barra melhorias e o time aprende a contorná-lo.']},
 {'objectives': ['Run the evaluation set on every PR.', 'Combine minimum score, max drop and critical cases.', 'Recognize regressions the average hides.'], 'minutes': 20,
  'activity': 'The class writes 3 gate rules on a poster. The teacher announces fictional PRs with score, drop and critical cases; the class decides green or red and checks whether any regression got through.',
  'discussion': ['Which case at your company should block on its own, even with a good average?', 'Who may change the gate threshold, and with what justification?'],
  'misconceptions': ['"The average went up, so ship it." One broken critical case outweighs the average.', '"A stricter gate is always better." It blocks improvements and the team learns to work around it.']})


def build():
    write('04-testes-de-regressao-no-ci', s, loc('pt'), loc('en'), tch())
