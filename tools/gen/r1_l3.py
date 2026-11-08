"""R1 · 03 · LLM como juiz e sua calibração (concordância e kappa de Cohen)."""
from r1_common import *

N = 50
AGG = {'vague0': (42, 7, 0, 1), 'vague1': (41, 5, 1, 3), 'criteria0': (40, 3, 2, 5), 'criteria1': (41, 2, 1, 6)}
HUMAN_PAIR = (40, 1, 2, 7)


def kappa(tp, fp, fn, tn):
    n = tp + fp + fn + tn
    po = (tp + tn) / n
    jp = (tp + fp) / n
    hp = (tp + fn) / n
    pe = jp * hp + (1 - jp) * (1 - hp)
    return round(po * 100), round((po - pe) / (1 - pe), 2)


for v in AGG.values():
    assert sum(v) == N and v[0] + v[2] == 42  # o RH aprova 42 e reprova 8
assert kappa(*AGG['vague0']) == (86, 0.19) and kappa(*AGG['criteria0']) == (90, 0.61) and kappa(*AGG['criteria1']) == (94, 0.76)
assert kappa(*HUMAN_PAIR) == (94, 0.79) and kappa(42, 8, 0, 0) == (84, 0.0)

QUESTION = LQ('Quantos dias de férias posso vender?', 'How much of my vacation can I sell?')
A_OK = LQ('Até um terço das férias, pedindo junto com a solicitação das férias [1].', 'Up to one third of your vacation, asking together with the vacation request [1].')
A_LONG = LQ('Ótima pergunta! Na Aurora você pode vender até metade das suas férias. É só pedir ao seu gestor com antecedência e o valor entra no pagamento seguinte. Aproveite seu descanso!',
            'Great question! At Aurora you can sell up to half of your vacation. Just ask your manager in advance and the money comes in the next payment. Enjoy your rest!')
A_SHORT = LQ('Até 1/3 [1].', 'Up to 1/3 [1].')
A_REFUSE = LQ('Não encontrei isso no manual. Vou encaminhar sua pergunta para o RH.', 'I couldn’t find that in the handbook. I’ll forward your question to HR.')
VERDICTS = {  # o que o juiz simulado diz em cada configuração
    'ok': {'vague0': 'pass', 'vague1': 'pass', 'criteria0': 'pass', 'criteria1': 'pass'},
    'long': {'vague0': 'pass', 'vague1': 'pass', 'criteria0': 'fail', 'criteria1': 'fail'},
    'short': {'vague0': 'pass', 'vague1': 'pass', 'criteria0': 'fail', 'criteria1': 'pass'},
    'refuse': {'vague0': 'pass', 'vague1': 'fail', 'criteria0': 'fail', 'criteria1': 'fail'}}
HUMAN = {'ok': 'pass', 'long': 'fail', 'short': 'pass', 'refuse': 'fail'}
# a configuração recomendada acerta as 4 do exemplo; a vaga sem exemplos erra 2
assert all(VERDICTS[a]['criteria1'] == HUMAN[a] for a in HUMAN) and sum(VERDICTS[a]['vague0'] != HUMAN[a] for a in HUMAN) == 2

RUBRICS = [opt('vague', 'vaga', 'vague'), opt('criteria', 'criterios', 'criteria')]

s = step('r-llm-como-juiz', 3, 20, ['avaliacao', 'llm-como-juiz', 'calibracao', 'kappa', 'rubrica'],
 ['r-metricas-de-rag'], ['simulado', 'no-navegador', 'sua-chave'], LQ('julgar', 'judge'),
 {'name': 'text', 'required': False, 'ui': 'examples', 'default': A_LONG, 'examples': ex(A_LONG, A_OK, A_SHORT, A_REFUSE)},
 [flag('rubric', 'rubrica', 'rubric', 'enum', options=RUBRICS, default='criteria', ui='select'),
  flag('examples', 'exemplos', 'examples', 'bool', default=False, ui='switch')],
 {'options': ['yes', 'no'], 'answer': 'no'}, 'fooled',
 {'live': False,
  'consts': {'real': False, 'realFields': {}, 'realValid': False, 'nAnswers': N, 'humanFail': 8},
  'compute': {
   'rec': 'lookup(answers, text, unknownAnswer)',
   'known': 'rec.known',
   'cfg': "rubric + (examples ? '1' : '0')",
   'agg': 'lookup(aggs, cfg, aggs.criteria0)',
   'simV': "lookup(rec.v, cfg, '')",
   'verdict': "real ? (realValid ? realFields.verdict : 'invalid') : simV",
   'human': 'rec.human',
   'agreePct': 'agg.agreePct',
   'kappaOk': 'agg.kappa >= 0.6',
   'same': "human != '' && verdict == human",
   'verdictKey': "verdict == 'pass' ? '@vPass' : (verdict == 'fail' ? '@vFail' : (verdict == 'invalid' ? '@vInvalid' : '@vNone'))",
   'humanKey': "human == 'pass' ? '@vPass' : (human == 'fail' ? '@vFail' : '@vNone')",
   'rubricL': "rubric == 'vague' ? rubricVague : rubricCriteria"},
  'cases': [
   {'when': '!known && !real', 'error': 'unknownAnswer'},
   {'when': 'agreePct >= 80 && agg.kappa < 0.4', 'flags': ['fooled']},
   {'when': '!kappaOk', 'flags': ['untrusted']},
   {'when': 'kappaOk', 'flags': ['trusted']},
   {'when': "human != '' && verdict == human", 'flags': ['agrees']},
   {'when': "human != '' && verdict != human && verdict != 'invalid'", 'flags': ['disagrees']},
   {'when': 'real && !realValid', 'flags': ['judgeBroken']},
   {'when': 'true', 'vars': {'agreePct': 'agreePct', 'kappaS': 'agg.kappaS', 'alwaysPct': 'alwaysPct', 'fp': 'agg.fp', 'humanFail': 'humanFail',
                             'nAnswers': 'nAnswers', 'humanKappaS': 'humanKappaS', 'rubricL': 'rubricL'}}],
  'widgets': [
   {'type': 'flow', 'steps': [{'label': '@sAnswer', 'sub': "=real ? '@subAny' : '@subExample'", 'tone': 'info'},
                              {'label': '@sJudge', 'sub': "=(rubric == 'vague' ? '@subVague' : '@subCriteria')", 'tone': 'neutral'},
                              {'label': '@sVerdict', 'sub': '=verdictKey', 'tone': "=human == '' ? 'neutral' : (same ? 'ok' : 'bad')"},
                              {'label': '@sHuman', 'sub': '=humanKey', 'tone': 'neutral'}]},
   {'type': 'metrics', 'label': '@aggLabel', 'items': [
     {'label': '@mAgree', 'value': '=agreePct', 'format': 'pct', 'tone': 'info'},
     {'label': '@mKappa', 'value': '=agg.kappaS', 'tone': "=kappaOk ? 'ok' : 'bad'"},
     {'label': '@mAlways', 'value': '=alwaysPct', 'format': 'pct', 'tone': 'dim'},
     {'label': '@mHumans', 'value': '=humanKappaS', 'tone': 'dim'}]},
   {'type': 'table', 'label': '@confLabel', 'columns': ['@colJudge', '@colHPass', '@colHFail'],
    'rows': "=[['@rowJPass', agg.tp, agg.fp], ['@rowJFail', agg.fn, agg.tn]]", 'tones': "=['neutral', 'neutral']", 'caption': '@confCaption'},
   {'type': 'checks', 'items': [
     {'label': '@chkKappa', 'ok': '=kappaOk', 'why': '@whyKappa'},
     {'label': '@chkThis', 'ok': "=human == '' || same", 'why': '@whyThis'}]},
   {'type': 'note', 'when': '=real && realValid', 'tone': 'info', 'text': "=str(realFields.reason)"},
   {'type': 'note', 'when': '=real && !realValid', 'tone': 'warn', 'text': '@brokenNote'},
   {'type': 'note', 'when': '=real', 'tone': 'info', 'text': '@realNote'},
   {'type': 'note', 'when': '=!real', 'tone': 'info', 'text': '@simNote'}]},
 real_chat('json', {'systemFrom': 'systems', 'systemBy': 'cfg', 'user': '{qLabel}: {question}\n{ctxLabel}: {context}\n{aLabel}: {text}',
                    'schema': {'verdict': 'enum:pass|fail', 'reason': 'string'}}))

JUDGE_CODE = '''import json
import os
import sys

from anthropic import Anthropic

MODEL = os.environ.get("JUDGE_MODEL", "claude-haiku-5-5")
client = Anthropic()
RUBRIC = open("rubric.txt", encoding="utf-8").read()


def judge(case):
    content = f"Question: {case['question']}\\nChunk: {case['context']}\\nAnswer: {case['answer']}"
    reply = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=RUBRIC,
        messages=[{"role": "user", "content": content}],
    )
    text = "".join(b.text for b in reply.content if b.type == "text")
    return json.loads(text[text.index("{"): text.rindex("}") + 1])["verdict"]


cases = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8") if line.strip()]
tp = fp = fn = tn = 0
for case in cases:
    j = judge(case) == "pass"
    h = case["human"] == "pass"
    tp += j and h
    fp += j and not h
    fn += h and not j
    tn += not j and not h

n = len(cases)
po = (tp + tn) / n
pe = ((tp + fp) / n) * ((tp + fn) / n) + ((fn + tn) / n) * ((fp + tn) / n)
kappa = (po - pe) / (1 - pe) if pe < 1 else 0.0
print(f"judge pass & human pass {tp} | judge pass & human fail {fp} | judge fail & human pass {fn} | both fail {tn}")
print(f"agreement {po:.0%} | Cohen's kappa {kappa:.2f}")'''


def loc(L):
    pt = L == 'pt'; T = lambda a, b: a if pt else b
    cheat = T('julgar --rubrica vaga', 'judge --rubric vague')
    ctx = chunk(L, 2)
    fmt = lambda x: (f'{x:.2f}'.replace('.', ',') if pt else f'{x:.2f}')
    aggs = {}
    for k, v in AGG.items():
        a, kap = kappa(*v)
        aggs[k] = {'tp': v[0], 'fp': v[1], 'fn': v[2], 'tn': v[3], 'agreePct': a, 'kappa': kap, 'kappaS': fmt(kap)}
    rec = lambda id, txt: {'known': True, 'v': VERDICTS[id], 'human': HUMAN[id]}
    out_json = T('Responda só com JSON: {"verdict":"pass|fail","reason":"uma frase em português"}.', 'Reply only with JSON: {"verdict":"pass|fail","reason":"one sentence"}.')
    vague = T('Você avalia respostas do assistente de RH da Aurora. A resposta é boa? ', 'You grade answers from Aurora’s HR assistant. Is the answer good? ') + out_json
    criteria = T('Você avalia respostas do assistente de RH da Aurora. Passa (pass) só se as três coisas forem verdade: 1) responde ao que foi perguntado; 2) toda afirmação está no trecho do manual; 3) não recusa quando o trecho responde. Qualquer falha: fail. ',
                 'You grade answers from Aurora’s HR assistant. Pass only if all three are true: 1) it answers what was asked; 2) every claim is in the handbook chunk; 3) it doesn’t refuse when the chunk answers. Any failure: fail. ') + out_json
    shots = T(' Exemplos rotulados pelo RH: "Pergunta: Quanto é o VR? Resposta: R$ 45 por dia útil [1]." → pass (curta e certa basta). "Pergunta: Quanto é o VR? Resposta: Uns R$ 50, depende do mês!" → fail (não está no trecho). "Pergunta: Quanto é o VR? Resposta: Não encontrei isso no manual." → fail (o trecho responde).',
              ' Examples labeled by HR: "Question: How much is the VR? Answer: R$ 45 per working day [1]." → pass (short and right is enough). "Question: How much is the VR? Answer: About R$ 50, depends on the month!" → fail (not in the chunk). "Question: How much is the VR? Answer: I couldn’t find that in the handbook." → fail (the chunk answers).')
    rubric_txt = criteria + shots
    return {
  'title': T('LLM como juiz, com prova de calibração', 'LLM as a judge, with a calibration test'),
  'subtitle': T('Concordar muito não basta: compare com o acaso usando o kappa', 'Agreeing a lot isn’t enough: compare with chance using kappa'),
  'mission': T('Para não depender do RH a cada mudança, o time quer um LLM que dê "passa" ou "não passa" para cada resposta. Antes de deixar o juiz bloquear deploy, duas pessoas do RH rotularam 50 respostas (aprovaram 42, reprovaram 8) e o juiz julgou as mesmas 50. Ajuste a rubrica e os exemplos até o juiz merecer confiança, e descubra por que 86% de concordância pode ser quase nada.',
               'So it doesn’t depend on HR at every change, the team wants an LLM that says "pass" or "fail" for each answer. Before letting the judge block deploys, two HR people labeled 50 answers (passed 42, failed 8) and the judge graded the same 50. Tune the rubric and examples until the judge deserves trust, and find out why 86% agreement can be almost nothing.'),
  'predict': {'question': T('com rubrica vaga ("a resposta é boa?") e 3 exemplos rotulados, o juiz concorda com o RH em 88% das 50 respostas. Ele já serve para bloquear deploy (kappa de pelo menos 0,6)?',
                            'with a vague rubric ("is the answer good?") and 3 labeled examples, the judge agrees with HR on 88% of the 50 answers. Is it good enough to block deploys (kappa of at least 0.6)?'),
              'options': {'yes': T('Serve: 88% é muito', 'Yes: 88% is a lot'), 'no': T('Não serve ainda', 'Not yet')}},
  'feedback': {'right': T('isso: o kappa é só 0,44. Como o RH aprova 84% das respostas, um juiz que aprovasse tudo já concordaria 84%. Os 88% estão só 4 pontos acima do acaso.',
                          'right: kappa is only 0.44. Since HR passes 84% of the answers, a judge that passed everything would already agree 84%. The 88% is only 4 points above chance.'),
               'wrong': T('ainda não: o kappa é 0,44. Como o RH aprova 84% das respostas, um juiz que aprovasse tudo já concordaria 84%. Os 88% estão só 4 pontos acima do acaso.',
                          'not yet: kappa is 0.44. Since HR passes 84% of the answers, a judge that passed everything would already agree 84%. The 88% is only 4 points above chance.'),
               'skipped': T('sem palpite? Rode com rubrica vaga e exemplos e olhe o kappa.', 'no guess? Run with a vague rubric and examples and look at kappa.')},
  'coach': {'ui': T('palpite anotado. Escolha a rubrica vaga, ligue os exemplos e rode.', 'guess noted. Pick the vague rubric, turn examples on and run.'),
            'cmd': T('palpite anotado. Rode julgar --rubrica vaga --exemplos sim e olhe o kappa.', 'guess noted. Run judge --rubric vague --examples yes and look at kappa.')},
  'tryNext': {'ui': T('Agora rubrica com critérios e exemplos, e julgue a resposta curta "Até 1/3 [1]." com e sem exemplos. Para um juiz real, escolha "Sua chave" ou "No navegador".',
                      'Now a rubric with criteria plus examples, and judge the short answer "Up to 1/3 [1]." with and without examples. For a real judge, pick "Your key" or "In the browser".'),
              'cmd': T(f'Rode julgar "{A_SHORT[L]}" --exemplos sim e compare com o veredito do RH.', f'Run judge "{A_SHORT[L]}" --examples yes and compare with HR’s verdict.')},
  'why': {'simples': T('Um juiz robô é como um corretor novo de redação: antes de deixar ele corrigir sozinho, você dá a ele 50 redações que professores já corrigiram e confere se ele chega às mesmas notas.\nSó que contar acertos engana. Se quase todas as redações são boas, um corretor que dá "aprovado" para tudo acerta quase sempre, sem ler nada. O kappa desconta essa sorte: 0 é "tanto faz", 1 é "concorda sempre".',
                       'A robot judge is like a new essay grader: before letting it grade alone, you give it 50 essays teachers already graded and check whether it reaches the same marks.\nBut counting matches fools you. If almost every essay is good, a grader that says "pass" to all of them is right almost every time, without reading anything. Kappa discounts that luck: 0 means "no better than chance", 1 means "always agrees".'),
          'dev': T('Kappa de Cohen: κ = (pₒ − pₑ) ÷ (1 − pₑ), onde pₒ é a concordância observada e pₑ é a concordância esperada por acaso, calculada pelas taxas de "passa" de cada lado. Com o RH aprovando 42 de 50, um juiz que aprova 49 tem pₑ ≈ 0,83: os 86% observados viram κ = 0,19.\nO que funciona na prática: rubrica com critérios explícitos e saída binária (passa ou não passa) em vez de nota de 1 a 10; poucos exemplos rotulados pelo RH, incluindo casos de fronteira (a resposta curta e certa); um juiz por critério quando eles conflitam; o motivo junto com o veredito. Meça o juiz contra rótulos humanos, guarde essas 50 como o "conjunto do juiz" versionado e meça de novo a cada troca de modelo ou de rubrica.',
                   'Cohen’s kappa: κ = (pₒ − pₑ) ÷ (1 − pₑ), where pₒ is the observed agreement and pₑ is the agreement expected by chance, from each side’s pass rate. With HR passing 42 of 50, a judge that passes 49 has pₑ ≈ 0.83: the observed 86% becomes κ = 0.19.\nWhat works in practice: a rubric with explicit criteria and a binary output (pass or fail) instead of a 1 to 10 score; a few examples labeled by HR, including borderline cases (the short, right answer); one judge per criterion when they conflict; the reason alongside the verdict. Measure the judge against human labels, keep those 50 as the versioned "judge set" and measure again whenever the model or rubric changes.'),
          'especialista': T('O estudo do MT-Bench (Zheng et al., 2023) achou mais de 80% de concordância entre juízes fortes como o GPT-4 e preferências humanas, o mesmo nível entre humanos, e também vieses de posição, de verbosidade e de autopromoção. Os três aparecem em avaliação de RAG: a resposta longa e simpática da lição passa no juiz vago; ao comparar duas respostas, troque a ordem e só conte a vitória que se mantém; e evite que o mesmo modelo gere e julgue.\nUse a concordância entre as duas pessoas do RH como teto (aqui κ = 0,79): um juiz perto dela está bom, e cobrar mais que isso é cobrar do robô o que nem as pessoas fazem. Olhe a matriz de confusão, não só o κ: para um portão de deploy, aprovar resposta ruim (falso "passa") custa mais que reprovar uma boa, então ajuste a rubrica para errar para o lado da reprovação. A faixa "substancial" de Landis e Koch (0,61 a 0,80) é uma convenção, não uma lei: defina o mínimo do seu time e registre o motivo.',
                            'The MT-Bench study (Zheng et al., 2023) found over 80% agreement between strong judges like GPT-4 and human preferences, the same level as between humans, and also position, verbosity and self-enhancement biases. All three show up in RAG evaluation: the lesson’s long, friendly answer passes the vague judge; when comparing two answers, swap the order and only count a win that holds; and avoid having the same model generate and judge.\nUse the agreement between the two HR people as the ceiling (here κ = 0.79): a judge close to it is good, and demanding more asks the robot for what not even people do. Look at the confusion matrix, not only κ: for a deploy gate, passing a bad answer (a false "pass") costs more than failing a good one, so tune the rubric to err toward failing. Landis and Koch’s "substantial" band (0.61 to 0.80) is a convention, not a law: set your team’s minimum and record why.')},
  'break': {'mission': {'ui': T('hora de quebrar: rubrica vaga e sem exemplos.', 'time to break it: vague rubric and no examples.'),
                        'cmd': T(f'hora de quebrar: rode {cheat}', f'time to break it: run {cheat}')},
            'success': T('Quebrou: o juiz concorda com o RH em {agreePct}% das {nAnswers} respostas, o que parece ótimo, mas o kappa é {kappaS}. Um juiz que aprovasse tudo concordaria {alwaysPct}%. Ele aprovou {fp} das {humanFail} respostas que o RH reprovou: como portão de deploy, deixaria passar quase todo erro.',
                         'Broken: the judge agrees with HR on {agreePct}% of the {nAnswers} answers, which looks great, but kappa is {kappaS}. A judge that passed everything would agree {alwaysPct}%. It passed {fp} of the {humanFail} answers HR failed: as a deploy gate, it would let almost every error through.'),
            'calm': T('Rubrica {rubricL}: concordância {agreePct}%, kappa {kappaS} (entre as duas pessoas do RH: {humanKappaS}). Para quebrar, deixe o juiz com cara de bom e kappa baixo.',
                      'Rubric {rubricL}: {agreePct}% agreement, kappa {kappaS} (between the two HR people: {humanKappaS}). To break it, make the judge look good with a low kappa.')},
  'hints': {'ui': T(['Escolha uma resposta e uma rubrica e rode. As métricas de cima valem para as 50 respostas.', 'Concordância conta acertos; o kappa desconta o que um juiz que aprova tudo acertaria por acaso. Exemplos rotulados ensinam onde fica a linha.', 'Rubrica vaga, sem exemplos.'],
                    ['Pick an answer and a rubric and run. The metrics at the top cover all 50 answers.', 'Agreement counts matches; kappa discounts what a pass-everything judge would match by chance. Labeled examples teach where the line is.', 'Vague rubric, no examples.']),
            'cmd': T(['A resposta a julgar vai entre aspas, depois de julgar.', '--rubrica vaga ou criterios; --exemplos sim ou nao.', cheat],
                     ['The answer to judge goes in quotes, after judge.', '--rubric vague or criteria; --examples yes or no.', cheat])},
  'errors': {'notInEnum.rubric': T('"{value}" não é uma rubrica. Use: {options}.', '"{value}" is not a rubric. Use: {options}.'), 'notBool.examples': yn(T),
             'model.unknownAnswer': T('No modo simulado, julgue uma das quatro respostas de exemplo (o RH já rotulou essas). Com "Sua chave" ou "No navegador", o juiz real julga qualquer texto.',
                                      'In simulated mode, judge one of the four example answers (HR already labeled those). With "Your key" or "In the browser", the real judge grades any text.')},
  'controls': {'arg': T('Resposta a julgar', 'Answer to judge'), 'rubric': T('Rubrica do juiz', 'Judge’s rubric'), 'examples': T('3 exemplos rotulados pelo RH', '3 examples labeled by HR')},
  'scene': {'label': T('Juiz de respostas', 'Answer judge'), 'empty': T('Rode para julgar.', 'Run to judge.'),
    'sAnswer': T('Resposta', 'Answer'), 'subExample': T('exemplo rotulado', 'labeled example'), 'subAny': T('qualquer texto', 'any text'),
    'sJudge': T('Juiz', 'Judge'), 'subVague': T('rubrica vaga', 'vague rubric'), 'subCriteria': T('3 critérios', '3 criteria'),
    'sVerdict': T('Veredito', 'Verdict'), 'sHuman': T('RH disse', 'HR said'),
    'vPass': T('passa', 'pass'), 'vFail': T('não passa', 'fail'), 'vInvalid': T('JSON inválido', 'invalid JSON'), 'vNone': T('sem rótulo', 'no label'),
    'aggLabel': T('Nas 50 respostas rotuladas pelo RH', 'On the 50 answers labeled by HR'),
    'mAgree': T('concordância com o RH', 'agreement with HR'), 'mKappa': T('kappa de Cohen', 'Cohen’s kappa'), 'mAlways': T('juiz que aprova tudo', 'pass-everything judge'), 'mHumans': T('kappa entre as 2 pessoas', 'kappa between the 2 people'),
    'confLabel': T('Matriz de confusão', 'Confusion matrix'), 'colJudge': T('juiz', 'judge'), 'colHPass': T('RH: passa', 'HR: pass'), 'colHFail': T('RH: não', 'HR: fail'),
    'rowJPass': T('passa', 'pass'), 'rowJFail': T('não passa', 'fail'),
    'confCaption': T('o canto de cima à direita são respostas ruins que o juiz deixou passar ({fp} de {humanFail})', 'the top-right cell is bad answers the judge let through ({fp} of {humanFail})'),
    'chkKappa': T('Kappa de pelo menos 0,6 (regra do time)', 'Kappa of at least 0.6 (team rule)'), 'whyKappa': T('kappa {kappaS}: a concordância de {agreePct}% está perto do acaso ({alwaysPct}%)', 'kappa {kappaS}: the {agreePct}% agreement is close to chance ({alwaysPct}%)'),
    'chkThis': T('Nesta resposta, o juiz concorda com o RH', 'On this answer, the judge agrees with HR'), 'whyThis': T('o juiz e o RH discordaram nesta resposta', 'the judge and HR disagreed on this answer'),
    'brokenNote': T('O modelo não devolveu o JSON pedido ({"verdict": "pass" ou "fail"}). Juiz que não segue formato também é juiz descalibrado.', 'The model didn’t return the requested JSON ({"verdict": "pass" or "fail"}). A judge that doesn’t follow the format is also an uncalibrated judge.'),
    'realNote': T('O veredito desta resposta vem do modelo real, com a rubrica escolhida. As métricas das 50 respostas continuam sendo as da lição: para medir o seu juiz, rode a receita.', 'This answer’s verdict comes from the real model, with the chosen rubric. The 50-answer metrics are still the lesson’s: to measure your own judge, run the recipe.'),
    'simNote': T('Modo simulado: vereditos e matrizes escritos à mão para as 4 rubricas possíveis. Use "Sua chave" ou "No navegador" para um juiz de verdade nesta resposta.', 'Simulated mode: verdicts and matrices hand-written for the 4 possible rubrics. Use "Your key" or "In the browser" for a real judge on this answer.')},
  'data': {'question': QUESTION[L], 'context': ctx, 'qLabel': T('Pergunta', 'Question'), 'ctxLabel': T('Trecho do manual', 'Handbook chunk'), 'aLabel': T('Resposta', 'Answer'),
           'answers': {A_OK[L]: rec('ok', A_OK), A_LONG[L]: rec('long', A_LONG), A_SHORT[L]: rec('short', A_SHORT), A_REFUSE[L]: rec('refuse', A_REFUSE)},
           'unknownAnswer': {'known': False, 'v': {}, 'human': ''},
           'aggs': aggs, 'alwaysPct': 84, 'humanKappaS': fmt(kappa(*HUMAN_PAIR)[1]),
           'rubricVague': T('vaga', 'vague'), 'rubricCriteria': T('com critérios', 'with criteria'),
           'systems': {'vague0': vague, 'vague1': vague + shots, 'criteria0': criteria, 'criteria1': criteria + shots}},
  'recipe': {'steps': [
     T('Separe 50 respostas reais do assistente (sem dados pessoais) e peça para duas pessoas do RH rotularem cada uma como pass ou fail, sem uma ver a outra. Salve as respostas e o rótulo final em judge_set.jsonl, um caso por linha:\n',
       'Pick 50 real answers from the assistant (no personal data) and ask two HR people to label each as pass or fail, without seeing each other’s. Save the answers and the final label in judge_set.jsonl, one case per line:\n')
     + f'{{"question": "{QUESTION[L]}", "context": "{ctx}", "answer": "{A_LONG[L]}", "human": "fail"}}',
     T('Escreva a rubrica em rubric.txt (critérios + exemplos rotulados), por exemplo:\n', 'Write the rubric in rubric.txt (criteria + labeled examples), for example:\n') + rubric_txt,
     T('Instale o SDK (pip install anthropic), guarde a chave em ANTHROPIC_API_KEY e crie judge_eval.py, que julga cada caso e calcula a concordância e o kappa contra o rótulo humano:\n',
       'Install the SDK (pip install anthropic), keep your key in ANTHROPIC_API_KEY and create judge_eval.py, which grades each case and computes agreement and kappa against the human label:\n') + JUDGE_CODE,
     T('Rode, depois troque rubric.txt por uma rubrica vaga ("A resposta é boa?" + o pedido de JSON) e rode de novo:\npython judge_eval.py judge_set.jsonl',
       'Run it, then swap rubric.txt for a vague rubric ("Is the answer good?" + the JSON request) and run again:\npython judge_eval.py judge_set.jsonl')],
   'ok': T('o script imprime a matriz e o kappa; a rubrica com critérios e exemplos tem kappa maior que a vaga, e você escolhe o mínimo do time olhando também quantas respostas ruins o juiz deixou passar.',
           'the script prints the matrix and kappa; the rubric with criteria and examples has a higher kappa than the vague one, and you pick the team’s minimum also looking at how many bad answers the judge let through.')}}


def tch():
    return teacher(
 {'objectives': ['Medir um juiz LLM contra rótulos humanos.', 'Calcular e interpretar o kappa de Cohen.', 'Escrever rubrica com critérios e exemplos.'], 'minutes': 25,
  'activity': 'A turma rotula 20 respostas como passa/não passa. Um grupo faz o "juiz preguiçoso" que aprova tudo; outro usa uma rubrica de 3 critérios. Calculem concordância e kappa no quadro para os dois.',
  'discussion': ['Que erro do juiz é mais caro para a Aurora: aprovar resposta ruim ou reprovar boa?', 'Quantos casos rotulados vocês precisam para confiar no kappa?'],
  'misconceptions': ['"90% de concordância é ótimo." Depende de quanto o acaso já daria.', '"O juiz é um modelo forte, então está certo." Ele tem vieses de posição, tamanho e autopromoção.']},
 {'objectives': ['Measure an LLM judge against human labels.', 'Compute and interpret Cohen’s kappa.', 'Write a rubric with criteria and examples.'], 'minutes': 25,
  'activity': 'The class labels 20 answers as pass/fail. One group plays the "lazy judge" that passes everything; another uses a 3-criteria rubric. Compute agreement and kappa on the board for both.',
  'discussion': ['Which judge error costs Aurora more: passing a bad answer or failing a good one?', 'How many labeled cases do you need to trust kappa?'],
  'misconceptions': ['"90% agreement is great." It depends on what chance would already give.', '"The judge is a strong model, so it’s right." It has position, length and self-enhancement biases.']})


def build():
    write('03-llm-como-juiz', s, loc('pt'), loc('en'), tch())
