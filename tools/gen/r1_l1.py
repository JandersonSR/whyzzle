"""R1 · 01 · conjunto de avaliação versionado."""
from r1_common import *

SCORES = {'v1': {'s2606': 11, 's2610': 41, 'hold': 13},
          'v2': {'s2606': 12, 's2610': 45, 'hold': 15},
          'v3': {'s2606': 12, 's2610': 51, 'hold': 17}}
SIZES = {'s2606': 13, 's2610': 60}
LEAK = {'s2606': 13, 's2610': 59}
SET_LABELS = {'s2606': '2026-06', 's2610': '2026-10'}
pct = lambda h, n: round(h / n * 100)
assert pct(51, 60) == 85 and pct(45, 60) == 75 and pct(12, 13) == 92 and pct(59, 60) == 98

SETS = [opt('s2606', '2026-06'), opt('s2610', '2026-10')]
PROMPTS = [opt('v1', 'v1'), opt('v2', 'v2'), opt('v3', 'v3')]

s = step('r-conjunto-de-avaliacao-versionado', 1, 15, ['avaliacao', 'eval', 'versionamento', 'holdout', 'contaminacao'],
 ['p-missao-assistente-de-rh'], ['simulado'], LQ('comparar', 'compare'),
 {'name': 'text', 'required': False, 'ui': 'examples', 'default': LQ('v3', 'v3'), 'examples': ex(LQ('v3', 'v3'), LQ('v2', 'v2'), LQ('v1', 'v1'))},
 [flag('base', 'base', 'base', 'enum', options=PROMPTS, default='v2', ui='select'),
  flag('set', 'conjunto', 'set', 'enum', options=SETS, default='s2610', ui='select'),
  flag('baseSet', 'conjunto-base', 'base-set', 'enum', options=SETS, default='s2610', ui='select'),
  flag('leak', 'vazar', 'leak', 'bool', default=False, ui='switch')],
 {'options': ['v3', 'v2', 'tie'], 'answer': 'v3'}, 'mismatch',
 {'live': True,
  'consts': {'scores': SCORES, 'sizes': SIZES, 'leakHits': LEAK, 'setLabels': SET_LABELS, 'holdN': 20},
  'compute': {
   'cand': 'lower(text)',
   'known': "includes(['v1', 'v2', 'v3'], cand)",
   'candRow': 'lookup(scores, cand, scores.v3)',
   'baseRow': 'lookup(scores, base, scores.v2)',
   'candN': 'lookup(sizes, set, 60)',
   'baseN': 'lookup(sizes, baseSet, 60)',
   'cleanHits': 'lookup(candRow, set, 0)',
   'candHits': 'leak ? lookup(leakHits, set, 0) : cleanHits',
   'baseHits': 'lookup(baseRow, baseSet, 0)',
   'candPct': 'round(candHits / candN * 100)',
   'cleanPct': 'round(cleanHits / candN * 100)',
   'basePct': 'round(baseHits / baseN * 100)',
   'shown': 'candPct - basePct',
   'shownS': "(shown > 0 ? '+' : '') + shown",
   'sameSet': 'set == baseSet',
   'baseOnCandPct': 'round(lookup(baseRow, set, 0) / candN * 100)',
   'candSetL': 'lookup(setLabels, set, set)',
   'baseSetL': 'lookup(setLabels, baseSet, baseSet)',
   'holdCPct': 'round(candRow.hold / holdN * 100)',
   'holdBPct': 'round(baseRow.hold / holdN * 100)'},
  'cases': [
   {'when': '!known', 'error': 'unknownPrompt'},
   {'when': 'known && !sameSet', 'flags': ['mismatch']},
   {'when': 'known && leak', 'flags': ['leaked']},
   {'when': 'known && sameSet && !leak && shown > 0', 'flags': ['better']},
   {'when': 'known && sameSet && !leak && shown < 0', 'flags': ['worse']},
   {'when': 'known && sameSet && !leak && shown == 0', 'flags': ['tie']},
   {'when': 'true', 'vars': {'cand': 'cand', 'base': 'base', 'candPct': 'candPct', 'basePct': 'basePct', 'cleanPct': 'cleanPct',
                             'shownS': 'shownS', 'candSetL': 'candSetL', 'baseSetL': 'baseSetL', 'baseOnCandPct': 'baseOnCandPct',
                             'holdCPct': 'holdCPct', 'holdBPct': 'holdBPct', 'candN': 'candN'}}],
  'widgets': [
   {'type': 'table', 'label': '@cmpTable', 'columns': ['@colWho', '@colPrompt', '@colSet', '@colScore'],
    'rows': "=[['@rowCand', cand, candSetL, candHits + '/' + candN + ' (' + candPct + '%)'], ['@rowBase', base, baseSetL, baseHits + '/' + baseN + ' (' + basePct + '%)']]",
    'tones': "=sameSet ? ['neutral', 'neutral'] : ['warn', 'warn']"},
   {'type': 'metrics', 'items': [
     {'label': '@mShown', 'value': '=shownS', 'tone': "=sameSet && !leak ? (shown >= 0 ? 'ok' : 'bad') : 'warn'"},
     {'label': '@mHold', 'value': "=holdCPct + '% · ' + holdBPct + '%'", 'tone': "=holdCPct >= holdBPct ? 'ok' : 'bad'"}]},
   {'type': 'checks', 'label': '@checks', 'items': [
     {'label': '@chkSame', 'ok': '=sameSet', 'why': '@whySame'},
     {'label': '@chkLeak', 'ok': '=!leak', 'why': '@whyLeak'},
     {'label': '@chkHold', 'ok': '=holdCPct >= holdBPct', 'why': '@whyHold'}]},
   {'type': 'note', 'when': '=!sameSet', 'tone': 'bad', 'text': '@mismatchNote'},
   {'type': 'note', 'when': '=leak', 'tone': 'warn', 'text': '@leakNote'},
   {'type': 'note', 'when': '=sameSet && !leak', 'tone': 'info', 'text': '@fairNote'},
   {'type': 'note', 'tone': 'info', 'text': '@simNote'}]})


def RUN_EVAL(L):
    pt = L == 'pt'
    c1 = '# rótulo da versão do prompt, ex.: v3' if pt else '# label of the prompt version, e.g. v3'
    c2 = '# arquivo do conjunto, ex.: evals/rh/2026-10.jsonl' if pt else '# set file, e.g. evals/rh/2026-10.jsonl'
    return f'''import argparse
import hashlib
import json
import os
import pathlib

from assistant import handle

p = argparse.ArgumentParser()
p.add_argument("--prompt", required=True)  {c1}
p.add_argument("--set", required=True)  {c2}
args = p.parse_args()

path = pathlib.Path(args.set)
digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
expected = {{"answer": "answer", "outside": "refuse", "sensitive": "handoff", "clarify": "clarify"}}

correct = 0
for case in cases:
    r = handle(case["question"])
    ok = r["action"] == expected[case["kind"]]
    if ok and case["kind"] == "answer":
        ok = bool(set(r["cited"]) & set(case["gold"]))
    correct += ok
    print(("OK " if ok else "XX ") + case["id"])

out = {{"prompt": args.prompt, "model": os.environ.get("CLAUDE_MODEL", "claude-haiku-5-5"), "set": path.stem, "sha256": digest, "correct": correct, "total": len(cases)}}
pathlib.Path("results").mkdir(exist_ok=True)
pathlib.Path(f"results/{{args.prompt}}__{{path.stem}}.json").write_text(json.dumps(out))
print(f"{{args.prompt}} @ {{path.stem}} ({{digest}}): {{correct}}/{{len(cases)}}")'''


def COMPARE(L):
    msg = 'conjuntos diferentes' if L == 'pt' else 'different sets'
    pts = 'pontos' if L == 'pt' else 'points'
    on = 'no' if L == 'pt' else 'on'
    return f'''import json
import sys

a, b = (json.load(open(name)) for name in sys.argv[1:3])
if a["sha256"] != b["sha256"]:
    sys.exit(f"{msg}: {{a['set']}} ({{a['sha256']}}) x {{b['set']}} ({{b['sha256']}})")

pa = a["correct"] / a["total"]
pb = b["correct"] / b["total"]
print(f"{{a['prompt']}} {{pa:.0%}} x {{b['prompt']}} {{pb:.0%}} {on} {{a['set']}}: {{100 * (pa - pb):+.1f}} {pts}")'''


def JSONL(L):
    q = {'pt': ['Com quanta antecedência eu peço férias?', 'Qual o horário da academia da empresa?', 'Estou sofrendo assédio do meu gestor. O que eu faço?'],
         'en': ['How far in advance do I request vacation?', 'What are the company gym’s opening hours?', 'My manager is harassing me. What do I do?']}[L]
    return (f'{{"id": "rh-001", "question": "{q[0]}", "kind": "answer", "gold": [0]}}\n'
            f'{{"id": "rh-010", "question": "{q[1]}", "kind": "outside", "gold": []}}\n'
            f'{{"id": "rh-012", "question": "{q[2]}", "kind": "sensitive", "gold": []}}')


def loc(L):
    pt = L == 'pt'; T = lambda a, b: a if pt else b
    cheat = T('comparar "v3" --conjunto-base 2026-06', 'compare "v3" --base-set 2026-06')
    return {
  'title': T('Conjunto de avaliação versionado', 'A versioned evaluation set'),
  'subtitle': T('Nota só se compara com a mesma régua: mesmas perguntas, mesma versão', 'Scores only compare on the same ruler: same questions, same version'),
  'mission': T('O assistente de RH da Aurora passou na missão das 13 perguntas e vai para produção. O time guardou essas 13 como o conjunto 2026-06 e, depois do piloto, criou o 2026-10, com 60 perguntas: as 13 da missão e 47 tiradas dos logs (rotuladas pelo RH). Agora chegou o prompt v3 e alguém já colou no canal: "v3 tirou 85%, a v2 tinha 92%, piorou!". Compare as versões do jeito certo e descubra se a v3 piorou mesmo.',
               'Aurora’s HR assistant passed the 13-question mission and is going to production. The team kept those 13 as set 2026-06 and, after the pilot, built 2026-10, with 60 questions: the 13 from the mission plus 47 taken from the logs (labeled by HR). Now prompt v3 arrived and someone already posted in the channel: "v3 scored 85%, v2 had 92%, it got worse!". Compare the versions the right way and find out whether v3 really got worse.'),
  'predict': {'question': T('a v3 tirou 85% no 2026-10 (60 perguntas); a v2 tinha tirado 92% no 2026-06 (13). Rodando as duas no mesmo 2026-10, quem ganha?',
                            'v3 scored 85% on 2026-10 (60 questions); v2 had scored 92% on 2026-06 (13). Running both on the same 2026-10, who wins?'),
              'options': {'v3': T('A v3', 'v3'), 'v2': T('A v2', 'v2'), 'tie': T('Empate', 'A tie')}},
  'feedback': {'right': T('isso: no mesmo 2026-10, a v3 faz 85% e a v2 faz 75%. A v3 é 10 pontos melhor; os 92% da v2 eram de um conjunto menor e mais fácil.',
                          'right: on the same 2026-10, v3 scores 85% and v2 scores 75%. v3 is 10 points better; v2’s 92% came from a smaller, easier set.'),
               'wrong': T('a v3 ganha: no mesmo 2026-10 ela faz 85% e a v2 faz 75%. Os 92% da v2 vieram do 2026-06, com 13 perguntas fáceis da missão. Conjunto diferente, régua diferente.',
                          'v3 wins: on the same 2026-10 it scores 85% and v2 scores 75%. v2’s 92% came from 2026-06, with 13 easy mission questions. Different set, different ruler.'),
               'skipped': T('sem palpite? Rode a comparação padrão, que põe as duas versões no 2026-10.', 'no guess? Run the default comparison, which puts both versions on 2026-10.')},
  'coach': {'ui': T('palpite anotado. Deixe os dois conjuntos em 2026-10 e rode.', 'guess noted. Keep both sets at 2026-10 and run.'),
            'cmd': T('palpite anotado. Rode comparar "v3" e leia as duas linhas da tabela.', 'guess noted. Run compare "v3" and read both table rows.')},
  'tryNext': {'ui': T('Agora ligue "vazar": alguém copiou perguntas do conjunto como exemplos no prompt. Veja a nota subir e o holdout não mexer.',
                      'Now turn on "leak": someone copied set questions into the prompt as examples. Watch the score jump while the holdout stays put.'),
              'cmd': T('Rode comparar "v3" --vazar sim e compare a nota com o holdout.', 'Run compare "v3" --leak yes and compare the score with the holdout.')},
  'why': {'simples': T('Comparar notas de provas diferentes não diz quem estudou mais. Se a turma A fez a prova fácil e a turma B fez a difícil, o 9 de uma e o 7 da outra não se comparam.\nCom IA é igual: o conjunto de perguntas é a prova. Ele ganha um número de versão, fica guardado e não muda escondido. Quem quer saber se o prompt novo é melhor roda o novo e o antigo na mesma versão da prova. E ninguém pode colar: pergunta da prova copiada no prompt dá nota alta e não ensina nada.',
                       'Comparing grades from different exams doesn’t tell you who studied more. If class A took the easy exam and class B the hard one, a 9 and a 7 don’t compare.\nAI is the same: the set of questions is the exam. It gets a version number, is stored and doesn’t change behind your back. To know whether the new prompt is better, run the new and the old one on the same version of the exam. And no cheating: exam questions pasted into the prompt give a high score and teach nothing.'),
          'dev': T('Trate o conjunto de avaliação como código: um arquivo por versão (evals/rh/2026-10.jsonl), no git, com id estável por caso, tipo (responder, recusar, encaminhar) e gabarito. Versão publicada não se edita: conserto vira versão nova, com nota do que mudou. Cada resultado guarda o prompt, o modelo, o nome do conjunto e um hash do arquivo, e o script de comparação recusa resultados de hashes diferentes.\nQuando o conjunto cresce, rode de novo o baseline nele: a v2 cai de 92% para 75% não porque piorou, mas porque a prova ficou mais parecida com a vida real. Guarde também um holdout, perguntas que ninguém usa para ajustar prompt, e olhe nele antes de comemorar.',
                   'Treat the evaluation set like code: one file per version (evals/rh/2026-10.jsonl), in git, with a stable id per case, a kind (answer, refuse, hand off) and an answer key. A published version is never edited: a fix becomes a new version, with a note on what changed. Every result stores the prompt, the model, the set name and a hash of the file, and the comparison script refuses results with different hashes.\nWhen the set grows, rerun the baseline on it: v2 drops from 92% to 75% not because it got worse, but because the exam got closer to real life. Also keep a holdout, questions nobody uses to tune prompts, and check it before celebrating.'),
          'especialista': T('Três detalhes separam um conjunto útil de um número bonito. Contaminação: exemplo few-shot, caso de teste usado para depurar ou pergunta vazada no fine-tuning fazem o modelo "decorar" a prova; a nota sobe no conjunto e não no holdout (aqui, 98% contra os mesmos 85%). Por isso o holdout fica fora do alcance de quem ajusta o prompt, e é renovado de tempos em tempos.\nRepresentatividade: 13 perguntas da missão eram as que o time imaginou; 47 vieram dos logs do piloto, com proporções parecidas com as de produção. Registre de onde veio cada caso e reamostre quando o uso mudar. Tamanho e ruído: com 60 casos, cada caso vale 1,7 ponto, então diferenças de 2 ou 3 pontos podem ser ruído; olhe os casos que viraram (de OK para XX e vice-versa), não só a média, e cresça o conjunto onde as decisões são apertadas.',
                            'Three details separate a useful set from a pretty number. Contamination: few-shot examples, test cases used for debugging or questions leaked into fine-tuning make the model "memorize" the exam; the score rises on the set and not on the holdout (here, 98% against the same 85%). That’s why the holdout stays out of reach of whoever tunes the prompt, and gets refreshed from time to time.\nRepresentativeness: the 13 mission questions were the ones the team imagined; 47 came from pilot logs, in proportions close to production. Record where each case came from and resample when usage changes. Size and noise: with 60 cases each case is worth 1.7 points, so 2 or 3 point differences may be noise; look at the cases that flipped (OK to XX and back), not just the mean, and grow the set where decisions are tight.')},
  'break': {'mission': {'ui': T('hora de quebrar: deixe a v3 no 2026-10 e mude o conjunto da base para 2026-06.', 'time to break it: keep v3 on 2026-10 and switch the base set to 2026-06.'),
                        'cmd': T(f'hora de quebrar: rode {cheat}', f'time to break it: run {cheat}')},
            'success': T('Quebrou: o painel mostra {cand} com {candPct}% no {candSetL} e {base} com {basePct}% no {baseSetL}, uma diferença de {shownS} pontos entre provas diferentes. No mesmo {candSetL}, {cand} faz {cleanPct}% e {base} faz {baseOnCandPct}%. É essa a conta que vale.',
                         'Broken: the dashboard shows {cand} at {candPct}% on {candSetL} and {base} at {basePct}% on {baseSetL}, a {shownS} point difference between different exams. On the same {candSetL}, {cand} scores {cleanPct}% and {base} scores {baseOnCandPct}%. That’s the number that counts.'),
            'calm': T('{cand}: {candPct}% no {candSetL} · {base}: {basePct}% no {baseSetL}. Para quebrar, compare notas de versões diferentes do conjunto.',
                      '{cand}: {candPct}% on {candSetL} · {base}: {basePct}% on {baseSetL}. To break it, compare scores from different versions of the set.')},
  'hints': {'ui': T(['Escolha o prompt candidato e o de base, e a versão do conjunto de cada um.', 'A comparação só é justa com o mesmo conjunto dos dois lados. O holdout são 20 perguntas novas que ninguém usou para ajustar nada.', 'Candidato v3 no 2026-10, base v2 no 2026-06.'],
                    ['Pick the candidate prompt and the base one, and each side’s set version.', 'The comparison is only fair with the same set on both sides. The holdout is 20 fresh questions nobody used to tune anything.', 'Candidate v3 on 2026-10, base v2 on 2026-06.']),
            'cmd': T(['O prompt candidato vai entre aspas: "v1", "v2" ou "v3".', '--base escolhe o prompt de referência; --conjunto e --conjunto-base escolhem a versão de cada lado (2026-06 ou 2026-10); --vazar sim cola perguntas do teste no prompt.', cheat],
                     ['The candidate prompt goes in quotes: "v1", "v2" or "v3".', '--base picks the reference prompt; --set and --base-set pick each side’s version (2026-06 or 2026-10); --leak yes pastes test questions into the prompt.', cheat])},
  'errors': {'notInEnum.base': T('"{value}" não é um prompt. Use: {options}.', '"{value}" is not a prompt. Use: {options}.'),
             'notInEnum.set': T('"{value}" não é uma versão do conjunto. Use: {options}.', '"{value}" is not a set version. Use: {options}.'),
             'notInEnum.baseSet': T('"{value}" não é uma versão do conjunto. Use: {options}.', '"{value}" is not a set version. Use: {options}.'),
             'notBool.leak': yn(T),
             'model.unknownPrompt': T('Neste projeto só existem os prompts v1, v2 e v3.', 'This project only has prompts v1, v2 and v3.')},
  'controls': {'arg': T('Prompt candidato', 'Candidate prompt'), 'base': T('Prompt de base', 'Base prompt'), 'set': T('Conjunto do candidato', 'Candidate’s set'),
               'baseSet': T('Conjunto da base', 'Base’s set'), 'leak': T('Perguntas do teste no prompt', 'Test questions in the prompt')},
  'scene': {'label': T('Comparar versões do prompt', 'Comparing prompt versions'), 'empty': T('Rode para comparar.', 'Run to compare.'),
    'cmpTable': T('O que o painel compara', 'What the dashboard compares'), 'colWho': T('lado', 'side'), 'colPrompt': 'prompt', 'colSet': T('conjunto', 'set'), 'colScore': T('acertos', 'correct'),
    'rowCand': T('candidato', 'candidate'), 'rowBase': 'base',
    'mShown': T('diferença mostrada (pontos)', 'difference shown (points)'), 'mHold': T('holdout: candidato · base', 'holdout: candidate · base'),
    'checks': T('A comparação vale?', 'Is the comparison valid?'),
    'chkSame': T('Mesma versão do conjunto nos dois lados', 'Same set version on both sides'), 'whySame': T('{candSetL} contra {baseSetL}: provas diferentes', '{candSetL} against {baseSetL}: different exams'),
    'chkLeak': T('Nenhuma pergunta do teste dentro do prompt', 'No test question inside the prompt'), 'whyLeak': T('o prompt tem perguntas do conjunto como exemplos: a nota mede memória', 'the prompt holds set questions as examples: the score measures memory'),
    'chkHold': T('No holdout, o candidato não fica atrás', 'On the holdout, the candidate isn’t behind'), 'whyHold': T('holdout: {holdCPct}% contra {holdBPct}%', 'holdout: {holdCPct}% against {holdBPct}%'),
    'mismatchNote': T('Conjuntos diferentes. No mesmo {candSetL}: {cand} {cleanPct}% e {base} {baseOnCandPct}%.', 'Different sets. On the same {candSetL}: {cand} {cleanPct}% and {base} {baseOnCandPct}%.'),
    'leakNote': T('Com as perguntas do teste no prompt, {cand} foi a {candPct}% no {candSetL}; sem elas, {cleanPct}%. No holdout ficou em {holdCPct}%, como antes.', 'With test questions in the prompt, {cand} went to {candPct}% on {candSetL}; without them, {cleanPct}%. On the holdout it stayed at {holdCPct}%, as before.'),
    'fairNote': T('Comparação justa no {candSetL}: {cand} {candPct}% e {base} {basePct}% ({shownS} pontos). Com {candN} casos, cada caso vale cerca de {stepPts} ponto(s).', 'Fair comparison on {candSetL}: {cand} {candPct}% and {base} {basePct}% ({shownS} points). With {candN} cases, each case is worth about {stepPts} point(s).'),
    'simNote': T('Notas fixas da lição (acertos de cada prompt em cada conjunto), sem chamar modelo. No seu projeto, elas saem do script de avaliação da receita.', 'Fixed lesson scores (each prompt’s hits on each set), no model called. In your project they come from the recipe’s evaluation script.')},
  'data': {'langCode': T('pt', 'en')},
  'recipe': {'steps': [
     T('Crie a pasta evals/rh/ e salve o conjunto como um arquivo por versão, uma pergunta por linha (JSON Lines). Comece pelas perguntas da missão de Prática e acrescente perguntas reais dos logs, rotuladas pelo RH. Exemplo de evals/rh/2026-10.jsonl:\n',
       'Create the evals/rh/ folder and save the set as one file per version, one question per line (JSON Lines). Start with the Practice mission questions and add real questions from the logs, labeled by HR. Example of evals/rh/2026-10.jsonl:\n') + JSONL(L),
     T('Crie run_eval.py ao lado do assistant.py da missão de Prática (qualquer função handle(pergunta) que devolva action e cited serve). Ele roda o conjunto, guarda o resultado com o nome e o hash do arquivo e imprime o placar:\n',
       'Create run_eval.py next to the Practice mission’s assistant.py (any handle(question) function that returns action and cited works). It runs the set, saves the result with the file’s name and hash and prints the score:\n') + RUN_EVAL(L),
     T('Crie compare.py, que só compara resultados do mesmo arquivo de conjunto:\n', 'Create compare.py, which only compares results from the same set file:\n') + COMPARE(L),
     T('Rode as duas versões no mesmo conjunto e compare (troque o SYSTEM do assistant.py entre as rodadas):\npython run_eval.py --prompt v2 --set evals/rh/2026-10.jsonl\npython run_eval.py --prompt v3 --set evals/rh/2026-10.jsonl\npython compare.py results/v3__2026-10.json results/v2__2026-10.json\nDepois tente comparar com um resultado do 2026-06 e veja o script recusar.',
       'Run both versions on the same set and compare (swap SYSTEM in assistant.py between runs):\npython run_eval.py --prompt v2 --set evals/rh/2026-10.jsonl\npython run_eval.py --prompt v3 --set evals/rh/2026-10.jsonl\npython compare.py results/v3__2026-10.json results/v2__2026-10.json\nThen try comparing against a 2026-06 result and watch the script refuse.')],
   'ok': T('compare.py imprime a diferença em pontos quando os dois resultados vêm do mesmo arquivo, e encerra com "conjuntos diferentes" quando um deles veio de outra versão do conjunto.',
           'compare.py prints the difference in points when both results come from the same file, and exits with "different sets" when one of them came from another version of the set.')}}


def tch():
    return teacher(
 {'objectives': ['Versionar o conjunto de avaliação como código.', 'Comparar versões de prompt só na mesma versão do conjunto.', 'Reconhecer contaminação e usar um holdout.'], 'minutes': 20,
  'activity': 'Duas equipes fazem "provas" diferentes (uma com 5 perguntas fáceis, outra com 15 mais difíceis) e anunciam a nota. A turma discute quem foi melhor; depois as duas fazem a mesma prova e comparam de novo.',
  'discussion': ['Quem pode editar o conjunto de avaliação na sua empresa, e como isso fica registrado?', 'O que vocês fariam se a nota subisse no conjunto e não no holdout?'],
  'misconceptions': ['"A nota caiu, então o prompt piorou." Talvez a prova tenha mudado; compare na mesma versão.', '"Usar as perguntas do teste como exemplo ajuda o modelo." Ajuda a decorar a prova, não a responder pergunta nova.']},
 {'objectives': ['Version the evaluation set like code.', 'Compare prompt versions only on the same set version.', 'Recognize contamination and use a holdout.'], 'minutes': 20,
  'activity': 'Two teams take different "exams" (one with 5 easy questions, another with 15 harder ones) and announce their grades. The class debates who did better; then both take the same exam and compare again.',
  'discussion': ['Who may edit the evaluation set at your company, and how is that recorded?', 'What would you do if the score rose on the set and not on the holdout?'],
  'misconceptions': ['"The score dropped, so the prompt got worse." Maybe the exam changed; compare on the same version.', '"Using test questions as examples helps the model." It helps memorize the exam, not answer new questions.']})


def build():
    s['data']['sim']['compute']['stepPts'] = 'fmt(100 / candN, 1, langCode)'
    s['data']['sim']['cases'][-1]['vars']['stepPts'] = 'stepPts'
    write('01-conjunto-de-avaliacao-versionado', s, loc('pt'), loc('en'), tch())
