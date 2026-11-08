"""R1 · 07 · ciclo de feedback de usuários."""
from r1_common import *

ACC0, THUMBS0 = 74, 70  # acerto no 2026-11 e polegar para cima na semana 0
def acc_end(opt_, review, new):
    if opt_ == 'thumbs':
        return 67
    return ACC0 + 2 + round(review / 20) if new else ACC0 + 1
assert acc_end('accuracy', 40, True) == 78 and acc_end('accuracy', 0, True) == 76 and acc_end('accuracy', 100, True) == 81

C_WRONG = LQ('Ele disse que posso vender metade das férias, mas o RH falou que é um terço.', 'It said I can sell half my vacation, but HR told me it’s one third.')
C_MISSING = LQ('Perguntei do auxílio creche e ele não soube responder.', 'I asked about the daycare allowance and it couldn’t answer.')
C_TONE = LQ('Acertou, mas a resposta veio seca demais.', 'It got it right, but the answer was too curt.')
C_PRAISE = LQ('Perfeito, obrigado!', 'Perfect, thanks!')
CATS = ['wrong_answer', 'missing_doc', 'tone', 'praise', 'other']

s = step('r-ciclo-de-feedback-de-usuarios', 7, 20, ['avaliacao', 'feedback', 'producao', 'bajulacao', 'revisao-humana'],
 ['r-casos-dificeis-e-perguntas-sem-resposta'], ['simulado', 'no-navegador', 'sua-chave'], LQ('ciclo', 'loop'),
 {'name': 'text', 'required': False, 'ui': 'examples', 'default': C_WRONG, 'examples': ex(C_WRONG, C_MISSING, C_TONE, C_PRAISE)},
 [flag('optimize', 'otimizar', 'optimize', 'enum', options=[opt('accuracy', 'acerto', 'accuracy'), opt('thumbs', 'polegar', 'thumbs')], default='accuracy', ui='select'),
  flag('review', 'revisao', 'review', 'int', min=0, max=100, default=40, ui='slider'),
  flag('newCases', 'novos-casos', 'new-cases', 'bool', default=True, ui='switch')],
 {'options': ['up', 'down'], 'answer': 'down'}, 'pleaser',
 {'live': True,
  'consts': {'real': False, 'realFields': {}, 'realValid': False, 'acc0': ACC0, 'thumbs0': THUMBS0, 'weeks': 4, 'downsPerWeek': 18, 'downPatterns': 12,
             'wrongRate': 0.15, 'wfrac': [0, 0.25, 0.5, 0.75, 1], 'weekLabels': ['0', '1', '2', '3', '4']},
  'compute': {
   'pleasing': "optimize == 'thumbs'",
   'foundWeek': 'round(review * wrongRate)',
   'found': 'foundWeek * weeks',
   'added': 'newCases ? downPatterns + found : 0',
   'accEnd': 'pleasing ? 67 : (newCases ? acc0 + 2 + round(review / 20) : acc0 + 1)',
   'thumbsEnd': 'pleasing ? 82 : 73',
   'likedWrong': 'pleasing ? 14 : 6',
   'likedWrongS': "review > 0 ? likedWrong + '%' : '?'",
   'accSeries': 'roundall(affine(wfrac, acc0, accEnd - acc0), 0)',
   'thumbsSeries': 'roundall(affine(wfrac, thumbs0, thumbsEnd - thumbs0), 0)',
   'downs': 'downsPerWeek * weeks',
   'rec': 'lookup(comments, text, unknownComment)',
   'known': 'rec.known',
   'cat': "real ? (realValid ? realFields.category : 'invalid') : rec.sim",
   'catL': 'lookup(catNames, cat, cat)',
   'addIt': 'real ? (realValid && realFields.add_to_eval == true) : rec.simAdd',
   'catRight': 'cat == rec.expected',
   'expL': 'lookup(catNames, rec.expected, rec.expected)'},
  'cases': [
   {'when': '!known && !real', 'error': 'unknownComment'},
   {'when': 'pleasing', 'flags': ['pleaser']},
   {'when': 'review == 0', 'flags': ['blind']},
   {'when': '!pleasing && accEnd > acc0', 'flags': ['improving']},
   {'when': '!pleasing && !newCases', 'flags': ['notLocked']},
   {'when': 'known && catRight', 'flags': ['triagedRight']},
   {'when': 'known && !catRight', 'flags': ['triagedWrong']},
   {'when': 'real && !realValid', 'flags': ['invalidJson']},
   {'when': 'true', 'vars': {'acc0': 'acc0', 'accEnd': 'accEnd', 'thumbs0': 'thumbs0', 'thumbsEnd': 'thumbsEnd', 'found': 'found', 'added': 'added',
                             'downs': 'downs', 'review': 'review', 'likedWrongS': 'likedWrongS', 'catL': 'catL', 'expL': 'expL'}}],
  'widgets': [
   {'type': 'flow', 'label': '@loopLabel', 'steps': [
     {'label': '@sSignals', 'sub': '@subSignals', 'tone': 'info'},
     {'label': '@sReview', 'sub': "=review > 0 ? '@subReview' : '@subNoReview'", 'tone': "=review > 0 ? 'ok' : 'warn'"},
     {'label': '@sCases', 'sub': "=newCases ? '@subAdded' : '@subNotAdded'", 'tone': "=newCases ? 'ok' : 'warn'"},
     {'label': '@sChange', 'sub': "=pleasing ? '@subThumbs' : '@subAccuracy'", 'tone': "=pleasing ? 'bad' : 'ok'"}]},
   {'type': 'chart', 'label': '@chart', 'kind': 'line', 'labels': '=weekLabels', 'max': 100,
    'series': [{'label': '@serThumbs', 'values': '=thumbsSeries'}, {'label': '@serAcc', 'values': '=accSeries'}]},
   {'type': 'metrics', 'items': [
     {'label': '@mThumbs', 'value': "=thumbs0 + '% → ' + thumbsEnd + '%'", 'tone': 'info'},
     {'label': '@mAcc', 'value': "=acc0 + '% → ' + accEnd + '%'", 'tone': "=accEnd > acc0 ? 'ok' : 'bad'"},
     {'label': '@mFound', 'value': '=found', 'format': 'int', 'tone': "=review > 0 ? 'ok' : 'warn'"},
     {'label': '@mLikedWrong', 'value': '=likedWrongS', 'tone': "=review > 0 ? 'neutral' : 'warn'"}]},
   {'type': 'flow', 'label': '@triageLabel', 'steps': [
     {'label': '@sComment', 'sub': '=text', 'tone': 'info'},
     {'label': '@sCategory', 'sub': '=catL', 'tone': "=catRight ? 'ok' : 'bad'"},
     {'label': '@sToEval', 'sub': "=addIt ? '@subYes' : '@subNo'", 'tone': 'neutral'}]},
   {'type': 'note', 'when': '=pleasing', 'tone': 'bad', 'text': '@pleaserNote'},
   {'type': 'note', 'when': '=review == 0', 'tone': 'warn', 'text': '@blindNote'},
   {'type': 'note', 'when': '=real', 'tone': 'info', 'text': '@realNote'},
   {'type': 'note', 'when': '=!real', 'tone': 'info', 'text': '@simNote'}]},
 real_chat('json', {'system': '{triageSys}', 'user': '{text}',
                    'schema': {'category': 'enum:' + '|'.join(CATS), 'add_to_eval': 'boolean'}}))

QUEUE = '''import csv
import json
import random
import sys

week = sys.argv[1]  # e.g. 2026-W46
convs = [json.loads(line) for line in open(f"logs/{week}.jsonl", encoding="utf-8") if line.strip()]
down = [c for c in convs if c.get("rating") == "down"]
down_ids = {c["id"] for c in down}
others = [c for c in convs if c["id"] not in down_ids]
random.seed(week)
sample = random.sample(others, min(40, len(others)))

with open(f"review-{week}.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "source", "question", "answer", "comment", "verdict", "feedback", "category", "kind", "gold", "add_to_eval"])
    for c in down:
        w.writerow([c["id"], "thumbs_down", c["question"], c["answer"], c.get("comment", "")] + [""] * 6)
    for c in sample:
        w.writerow([c["id"], "random", c["question"], c["answer"], ""] + [""] * 6)
print(f"{len(down)} thumbs-down + {len(sample)} random conversations in review-{week}.csv")'''

ADD = '''import csv
import json
import sys

review, old, new = sys.argv[1:4]
text = open(old, encoding="utf-8").read().rstrip("\\n") + "\\n"
added = 0
with open(new, "w", encoding="utf-8") as out:
    out.write(text)
    for row in csv.DictReader(open(review, encoding="utf-8")):
        if row["add_to_eval"].strip().lower() != "yes":
            continue
        gold = [int(x) for x in row["gold"].replace(";", ",").split(",") if x.strip()]
        case = {"id": "fb-" + row["id"], "question": row["question"], "kind": row["kind"], "gold": gold,
                "category": row["category"], "feedback": row["feedback"], "source": row["source"]}
        out.write(json.dumps(case, ensure_ascii=False) + "\\n")
        added += 1
print(f"{new}: {added} new cases on top of {old}")'''


def loc(L):
    pt = L == 'pt'; T = lambda a, b: a if pt else b
    cheat = T('ciclo --otimizar polegar', 'loop --optimize thumbs')
    names = {'wrong_answer': T('resposta errada', 'wrong answer'), 'missing_doc': T('falta no manual', 'missing from handbook'), 'tone': T('tom', 'tone'),
             'praise': T('elogio', 'praise'), 'other': T('outro', 'other'), 'invalid': T('JSON inválido', 'invalid JSON')}
    c = lambda exp, add: {'known': True, 'expected': exp, 'sim': exp, 'simAdd': add}
    triage = T('Você faz a triagem de comentários de colaboradores sobre o assistente de RH da Aurora. Classifique o comentário numa categoria: wrong_answer (o assistente disse algo errado), missing_doc (o assunto não está no manual), tone (resposta certa, mas o jeito incomodou), praise (elogio) ou other. add_to_eval é true quando o caso deve virar teste no conjunto de avaliação (resposta errada ou assunto que falta no manual). Responda só com JSON: {"category":"...","add_to_eval":true}.',
               'You triage employee comments about Aurora’s HR assistant. Put the comment in one category: wrong_answer (the assistant said something wrong), missing_doc (the topic isn’t in the handbook), tone (right answer, but the way it said it bothered them), praise or other. add_to_eval is true when the case should become a test in the evaluation set (a wrong answer or a topic missing from the handbook). Reply only with JSON: {"category":"...","add_to_eval":true}.')
    log_line = T('{"id": "c-1042", "question": "Quantos dias de férias posso vender?", "answer": "Até metade das férias.", "rating": "down", "comment": "O RH disse que é um terço."}',
                 '{"id": "c-1042", "question": "How much of my vacation can I sell?", "answer": "Up to half your vacation.", "rating": "down", "comment": "HR said it’s one third."}')
    return {
  'title': T('Ciclo de feedback de usuários', 'The user feedback loop'),
  'subtitle': T('Polegar para baixo, revisão humana e casos novos no conjunto, sem ensinar o assistente a agradar', 'Thumbs-down, human review and new cases in the set, without teaching the assistant to please'),
  'mission': T('O assistente está no ar: são cerca de 2.000 conversas por semana, e umas 3% recebem polegar para cima ou para baixo, às vezes com comentário. O time tem 4 semanas e precisa decidir três coisas: o que otimizar (aprovação ou acerto medido no 2026-11), quantas conversas sorteadas o RH revisa por semana e se as falhas viram casos novos de avaliação. Monte o ciclo e faça o acerto subir.',
               'The assistant is live: about 2,000 conversations a week, and around 3% get a thumbs-up or thumbs-down, sometimes with a comment. The team has 4 weeks and must decide three things: what to optimize (approval, or accuracy measured on 2026-11), how many random conversations HR reviews each week and whether failures become new evaluation cases. Build the loop and make accuracy go up.'),
  'predict': {'question': T('se o time mudar o prompt toda semana para maximizar o polegar para cima, o acerto medido no conjunto 2026-11…', 'if the team changes the prompt every week to maximize thumbs-up, the accuracy measured on set 2026-11…'),
              'options': {'up': T('Sobe junto', 'Goes up too'), 'down': T('Cai', 'Goes down')}},
  'feedback': {'right': T('isso: a aprovação vai de 70% para 82% e o acerto cai de 74% para 67%. O prompt que agrada responde com mais certeza e recusa menos, inclusive quando devia recusar.',
                          'right: approval goes from 70% to 82% and accuracy drops from 74% to 67%. The pleasing prompt answers more confidently and refuses less, even when it should refuse.'),
               'wrong': T('cai: a aprovação vai de 70% para 82% e o acerto cai de 74% para 67%. O prompt que agrada responde com mais certeza e recusa menos, inclusive quando devia recusar.',
                          'it goes down: approval goes from 70% to 82% and accuracy drops from 74% to 67%. The pleasing prompt answers more confidently and refuses less, even when it should refuse.'),
               'skipped': T('sem palpite? Rode otimizando pelo acerto e depois pelo polegar, e compare as duas linhas do gráfico.', 'no guess? Run optimizing for accuracy and then for thumbs, and compare both chart lines.')},
  'coach': {'ui': T('palpite anotado. Rode com o ciclo padrão (otimizar acerto, revisão de 40 por semana) e olhe o gráfico.', 'guess noted. Run with the default loop (optimize accuracy, review 40 a week) and look at the chart.'),
            'cmd': T('palpite anotado. Rode ciclo e olhe as duas linhas do gráfico.', 'guess noted. Run loop and look at both chart lines.')},
  'tryNext': {'ui': T('Agora zere a revisão aleatória: você só vê quem reclamou. Quantas respostas erradas o time deixa de achar?', 'Now set the random review to zero: you only see who complained. How many wrong answers does the team stop finding?'),
              'cmd': T('Rode ciclo --revisao 0 e compare as falhas achadas.', 'Run loop --review 0 and compare the failures found.')},
  'why': {'simples': T('Opinião de cliente é ouro, mas engana: quem reclama é pouca gente, e muita gente agradece uma resposta errada que soou simpática. Se você mudar o restaurante só para ganhar mais "curti", ele pode passar a servir sobremesa para todo mundo e esquecer o prato principal.\nO ciclo bom usa o polegar para achar problemas, pede para uma pessoa conferir uma amostra sorteada e transforma cada erro achado em pergunta nova da prova. A nota que manda continua sendo a da prova.',
                       'Customer opinions are gold, but they mislead: few people complain, and many thank you for a wrong answer that sounded nice. If you change the restaurant only to get more "likes", it may start serving everyone dessert and forget the main course.\nThe good loop uses thumbs to find problems, has a person check a random sample, and turns every error found into a new exam question. The score that rules is still the exam’s.'),
          'dev': T('Três fontes, cada uma com seu viés: polegar para baixo com comentário (pouco volume, muito sinal, viés de quem reclama), revisão humana de uma amostra aleatória (acha as falhas silenciosas, aquelas que ninguém reclamou) e métricas automáticas no tráfego (recusas, encaminhamentos, perguntas repetidas). Toda semana: fila de revisão com os polegares para baixo + N conversas sorteadas, o RH marca veredito, feedback e categoria de avaliação, e o que é falha vira caso numa versão nova do conjunto (2026-12), com a origem registrada.\nA decisão de produto continua no conjunto: o polegar entra como métrica de guarda e como fonte de casos, não como alvo. Uma triagem automática dos comentários (a da lição, em JSON com categorias fechadas) ajuda a priorizar, mas o "vira teste ou não" passa por uma pessoa. Registre também o que falta no manual: "auxílio creche" não é bug do prompt, é documento que o RH precisa escrever.',
                   'Three sources, each with its bias: thumbs-down with a comment (low volume, lots of signal, complainer bias), human review of a random sample (finds silent failures, the ones nobody complained about) and automatic metrics on traffic (refusals, handoffs, repeated questions). Every week: a review queue with the thumbs-down + N random conversations, HR marks verdict, feedback and evaluation category, and failures become cases in a new set version (2026-12), with their origin recorded.\nThe product decision stays with the set: thumbs are a guardrail metric and a source of cases, not a target. Automatic triage of comments (the lesson’s one, in JSON with closed categories) helps prioritize, but "does it become a test" goes through a person. Also record what’s missing from the handbook: "daycare allowance" isn’t a prompt bug, it’s a document HR needs to write.'),
          'especialista': T('Otimizar direto pelo polegar tem precedente público. Em abril de 2025, a OpenAI reverteu uma atualização do GPT-4o que deixou o modelo bajulador; no relato da empresa, a atualização acrescentou um sinal de recompensa baseado no polegar para cima e para baixo do ChatGPT, e o conjunto das mudanças enfraqueceu o sinal principal que segurava a bajulação. As avaliações offline e os testes A/B não pegaram. A lição para um time pequeno é a mesma: aprovação é um alvo fácil de inflar.\nO feedback também é dado pessoal: o comentário pode trazer saúde, salário ou conflito com o gestor. Defina quem lê a fila de revisão, por quanto tempo os logs ficam guardados e o que é anonimizado antes de virar caso de teste (troque nomes e números antes de gravar no conjunto). E feche o ciclo com quem reclamou quando der: quem vê o problema corrigido volta a dar feedback.',
                            'Optimizing straight for thumbs has a public precedent. In April 2025, OpenAI rolled back a GPT-4o update that made the model sycophantic; by the company’s account, the update added a reward signal based on ChatGPT thumbs-up and thumbs-down, and the changes together weakened the main signal that had kept sycophancy in check. Offline evaluations and A/B tests didn’t catch it. The lesson for a small team is the same: approval is an easy target to inflate.\nFeedback is also personal data: a comment may carry health, salary or a conflict with a manager. Decide who reads the review queue, how long logs are kept and what is anonymized before becoming a test case (replace names and numbers before saving to the set). And close the loop with whoever complained when you can: people who see their problem fixed keep giving feedback.')},
  'break': {'mission': {'ui': T('hora de quebrar: mude o que o time otimiza para o polegar para cima.', 'time to break it: switch what the team optimizes to thumbs-up.'),
                        'cmd': T(f'hora de quebrar: rode {cheat}', f'time to break it: run {cheat}')},
            'success': T('Quebrou: otimizando pelo polegar, a aprovação subiu de {thumbs0}% para {thumbsEnd}% em 4 semanas e o acerto no conjunto 2026-11 caiu de {acc0}% para {accEnd}%. O assistente aprendeu a agradar: responde com mais certeza e recusa menos, inclusive quando devia recusar.',
                         'Broken: optimizing for thumbs, approval rose from {thumbs0}% to {thumbsEnd}% in 4 weeks and accuracy on set 2026-11 fell from {acc0}% to {accEnd}%. The assistant learned to please: it answers more confidently and refuses less, even when it should refuse.'),
            'calm': T('Em 4 semanas: acerto {acc0}% → {accEnd}%, aprovação {thumbs0}% → {thumbsEnd}%, {found} falhas silenciosas achadas e {added} casos novos. Para quebrar, otimize pelo sinal errado.',
                      'In 4 weeks: accuracy {acc0}% → {accEnd}%, approval {thumbs0}% → {thumbsEnd}%, {found} silent failures found and {added} new cases. To break it, optimize for the wrong signal.')},
  'hints': {'ui': T(['Escolha o que otimizar, quanto revisar e rode. O comentário de exemplo mostra a triagem de uma mensagem.', 'Revisão aleatória acha falhas que ninguém reclamou; casos novos travam a correção no conjunto. O polegar mede o quanto a pessoa gostou, não se estava certo.', 'Otimizar: polegar.'],
                    ['Pick what to optimize, how much to review and run. The example comment shows the triage of one message.', 'Random review finds failures nobody complained about; new cases lock the fix into the set. Thumbs measure how much the person liked it, not whether it was right.', 'Optimize: thumbs.']),
            'cmd': T(['O comentário vai entre aspas, depois de ciclo.', '--otimizar acerto ou polegar; --revisao de 0 a 100 conversas por semana; --novos-casos sim ou nao.', cheat],
                     ['The comment goes in quotes, after loop.', '--optimize accuracy or thumbs; --review from 0 to 100 conversations a week; --new-cases yes or no.', cheat])},
  'errors': {'notInEnum.optimize': T('"{value}" não é uma opção. Use: {options}.', '"{value}" is not an option. Use: {options}.'),
             'belowMin.review': T('A revisão vai de 0 a 100 conversas por semana.', 'Review goes from 0 to 100 conversations a week.'),
             'aboveMax.review': T('Mais de 100 por semana não cabe na agenda do RH desta lição.', 'More than 100 a week doesn’t fit this lesson’s HR schedule.'),
             'notInteger.review': T('Conversas inteiras, por favor.', 'Whole conversations, please.'), 'notBool.newCases': yn(T),
             'model.unknownComment': T('No modo simulado, use um dos quatro comentários de exemplo. Com "Sua chave" ou "No navegador", qualquer comentário vai para a triagem real.', 'In simulated mode, use one of the four example comments. With "Your key" or "In the browser", any comment goes to the real triage.')},
  'controls': {'arg': T('Comentário de um colaborador', 'An employee’s comment'), 'optimize': T('O que o time otimiza', 'What the team optimizes'),
               'review': T('Conversas sorteadas revisadas por semana', 'Random conversations reviewed per week'), 'newCases': T('Falhas viram casos no conjunto', 'Failures become set cases')},
  'scene': {'label': T('Quatro semanas em produção', 'Four weeks in production'), 'empty': T('Rode para simular o ciclo.', 'Run to simulate the loop.'),
    'loopLabel': T('O ciclo', 'The loop'), 'sSignals': T('Sinais', 'Signals'), 'subSignals': T('{downs} polegares para baixo', '{downs} thumbs-down'),
    'sReview': T('Revisão', 'Review'), 'subReview': T('{review} sorteadas/semana', '{review} random/week'), 'subNoReview': T('só quem reclamou', 'only complainers'),
    'sCases': T('Conjunto', 'Set'), 'subAdded': T('+{added} casos (2026-12)', '+{added} cases (2026-12)'), 'subNotAdded': T('nada entra', 'nothing goes in'),
    'sChange': T('Mudança', 'Change'), 'subThumbs': T('para agradar', 'to please'), 'subAccuracy': T('para acertar', 'to be right'),
    'chart': T('Semana a semana (%)', 'Week by week (%)'), 'serThumbs': T('polegar para cima', 'thumbs-up'), 'serAcc': T('acerto no 2026-11', 'accuracy on 2026-11'),
    'mThumbs': T('aprovação', 'approval'), 'mAcc': T('acerto no 2026-11', 'accuracy on 2026-11'), 'mFound': T('falhas silenciosas achadas', 'silent failures found'),
    'mLikedWrong': T('polegar para cima em resposta errada', 'thumbs-up on wrong answers'),
    'triageLabel': T('Triagem deste comentário', 'Triage of this comment'), 'sComment': T('Comentário', 'Comment'), 'sCategory': T('Categoria', 'Category'), 'sToEval': T('Vira teste?', 'Becomes a test?'),
    'subYes': T('sim', 'yes'), 'subNo': T('não', 'no'),
    'pleaserNote': T('A aprovação subiu para {thumbsEnd}% e o acerto caiu para {accEnd}%. Polegar é sinal para achar problema, não alvo.', 'Approval rose to {thumbsEnd}% and accuracy fell to {accEnd}%. Thumbs are a signal to find problems, not a target.'),
    'blindNote': T('Sem revisão aleatória, o time só vê os {downs} polegares para baixo. Resposta errada que ninguém reclamou (ou que ganhou polegar para cima) fica invisível.', 'With no random review, the team only sees the {downs} thumbs-down. A wrong answer nobody complained about (or that got a thumbs-up) stays invisible.'),
    'realNote': T('A triagem deste comentário vem do modelo real, em JSON com categorias fechadas. O gráfico continua com os números da lição.', 'This comment’s triage comes from the real model, in JSON with closed categories. The chart keeps the lesson’s numbers.'),
    'simNote': T('Modo simulado: 4 semanas com números da lição (cerca de 15% das conversas sorteadas têm resposta errada). Use "Sua chave" ou "No navegador" para triar um comentário com um modelo real.', 'Simulated mode: 4 weeks with lesson numbers (about 15% of random conversations have a wrong answer). Use "Your key" or "In the browser" to triage a comment with a real model.')},
  'data': {'catNames': names, 'triageSys': triage,
           'comments': {C_WRONG[L]: c('wrong_answer', True), C_MISSING[L]: c('missing_doc', True), C_TONE[L]: c('tone', False), C_PRAISE[L]: c('praise', False)},
           'unknownComment': {'known': False, 'expected': '', 'sim': '', 'simAdd': False}},
  'recipe': {'steps': [
     T('Guarde cada conversa do assistente num log semanal em JSON Lines, com a avaliação e o comentário quando houver (troque nomes e números pessoais antes de gravar). Exemplo de linha de logs/2026-W46.jsonl:\n', 'Store every assistant conversation in a weekly JSON Lines log, with the rating and comment when there is one (replace names and personal numbers before saving). Example line of logs/2026-W46.jsonl:\n') + log_line,
     T('Crie review_queue.py, que monta a fila da semana: todos os polegares para baixo e mais 40 conversas sorteadas (o sorteio usa a semana como semente, então dá para repetir):\n', 'Create review_queue.py, which builds the week’s queue: every thumbs-down plus 40 random conversations (the draw uses the week as its seed, so it can be repeated):\n') + QUEUE,
     T('Rode e entregue o CSV ao RH, que preenche verdict (ok ou wrong), feedback (wrong_answer, missing_doc, tone, praise ou other), category (a categoria de avaliação, como answerable ou false_premise), kind (answer, outside, sensitive ou clarify), gold (índices dos trechos certos, separados por ponto e vírgula; vazio se não for do tipo answer) e add_to_eval (yes ou no):\npython review_queue.py 2026-W46', 'Run it and hand the CSV to HR, who fills in verdict (ok or wrong), feedback (wrong_answer, missing_doc, tone, praise or other), category (the evaluation category, like answerable or false_premise), kind (answer, outside, sensitive or clarify), gold (indexes of the right chunks, separated by semicolons; empty if not kind answer) and add_to_eval (yes or no):\npython review_queue.py 2026-W46'),
     T('Crie add_cases.py, que gera a versão nova do conjunto com os casos marcados (a versão antiga fica como está):\n', 'Create add_cases.py, which builds the new set version with the marked cases (the old version stays as it is):\n') + ADD
     + T('\nRode:\npython add_cases.py review-2026-W46.csv evals/rh/2026-11.jsonl evals/rh/2026-12.jsonl', '\nRun:\npython add_cases.py review-2026-W46.csv evals/rh/2026-11.jsonl evals/rh/2026-12.jsonl')],
   'ok': T('review-2026-W46.csv traz os polegares para baixo e 40 conversas sorteadas; depois da revisão, add_cases.py cria o 2026-12.jsonl com o 2026-11 inteiro mais os casos marcados yes, e a próxima comparação de prompts usa essa versão nos dois lados.',
           'review-2026-W46.csv holds the thumbs-down plus 40 random conversations; after the review, add_cases.py creates 2026-12.jsonl with all of 2026-11 plus the cases marked yes, and the next prompt comparison uses that version on both sides.')}}


def tch():
    return teacher(
 {'objectives': ['Usar feedback de usuários como fonte de casos, não como alvo.', 'Combinar polegar para baixo com revisão aleatória.', 'Versionar o conjunto com os casos achados.'], 'minutes': 20,
  'activity': 'Distribua 20 cartões de "conversa" com resposta, se estava certa e se a pessoa gostou. Um grupo escolhe mudanças olhando só "gostou"; outro olha uma amostra sorteada de "certa". Comparem o que cada grupo consertou.',
  'discussion': ['Que sinal de satisfação a sua empresa já otimizou e se arrependeu?', 'Quem pode ler os comentários dos colaboradores, e por quanto tempo?'],
  'misconceptions': ['"Mais polegar para cima é melhor qualidade." Pode ser só mais bajulação.', '"Se ninguém reclamou, está certo." Falhas silenciosas só aparecem na revisão aleatória.']},
 {'objectives': ['Use user feedback as a source of cases, not as a target.', 'Combine thumbs-down with random review.', 'Version the set with the cases found.'], 'minutes': 20,
  'activity': 'Hand out 20 "conversation" cards with the answer, whether it was right and whether the person liked it. One group picks changes looking only at "liked"; another looks at a random sample of "right". Compare what each group fixed.',
  'discussion': ['Which satisfaction signal has your company optimized and regretted?', 'Who may read employees’ comments, and for how long?'],
  'misconceptions': ['"More thumbs-up means better quality." It may just be more flattery.', '"If nobody complained, it’s right." Silent failures only show up in random review.']})


def build():
    write('07-ciclo-de-feedback-de-usuarios', s, loc('pt'), loc('en'), tch())
