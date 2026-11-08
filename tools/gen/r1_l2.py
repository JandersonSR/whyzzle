"""R1 · 02 · métricas de RAG (fidelidade e relevância)."""
from r1_common import *

QUESTION = LQ('Posso pedir reembolso da internet de casa?', 'Can I get my home internet bill reimbursed?')
CTX_IDX = [6, 7, 8, 9]
A_FAITH = LQ('Não. Internet e energia de casa não são reembolsáveis: esse custo já é coberto pelo auxílio home office de R$ 120 por mês.',
             'No. Home internet and electricity aren’t reimbursable: that cost is already covered by the R$ 120 monthly home office allowance.')
A_INVENT = LQ('Pode sim! Envie a conta de internet pelo app de despesas em até 30 dias e o valor volta junto com o salário.',
              'Yes, you can! Upload the internet bill in the expenses app within 30 days and the money comes back with your salary.')
A_DODGE = LQ('Na Aurora, o trabalho remoto é permitido até 2 dias por semana, combinados com o gestor no início de cada mês.',
             'At Aurora, remote work is allowed up to 2 days a week, agreed with the manager at the start of each month.')


def answers(L):
    T = lambda a, b: a if L == 'pt' else b
    def rec(id, rel, claims, sup, bad, flaw):
        return {'id': id, 'known': True, 'rel': rel, 'claims': claims, 'sup': sup, 'supL': ['@supYes' if x else '@supNo' for x in sup],
                'tones': ['ok' if x else 'bad' for x in sup], 'nSup': sum(sup), 'nClaims': len(sup), 'bad': bad, 'flaw': flaw}
    return {
     A_FAITH[L]: rec('faith', 0.92, [T('internet não é reembolsável', 'internet isn’t reimbursable'), T('coberto pelo auxílio home office', 'covered by the home office allowance'), T('auxílio de R$ 120 por mês', 'R$ 120 monthly allowance')], [1, 1, 1], False, ''),
     A_INVENT[L]: rec('invent', 0.90, [T('conta de internet é reembolsável', 'internet bill is reimbursable'), T('envio pelo app em até 30 dias', 'upload in the app within 30 days'), T('o valor volta com o salário', 'money comes back with the salary')], [0, 1, 0], True,
                      T('inventa que a internet de casa é reembolsável', 'makes up that home internet is reimbursable')),
     A_DODGE[L]: rec('dodge', 0.71, [T('remoto até 2 dias por semana', 'remote up to 2 days a week'), T('combinado com o gestor todo mês', 'agreed with the manager monthly')], [1, 1], True,
                     T('não responde à pergunta', 'doesn’t answer the question'))}


METRICS = [opt('relevance', 'relevancia', 'relevance'), opt('faithfulness', 'fidelidade', 'faithfulness')]

s = step('r-metricas-de-rag', 2, 15, ['avaliacao', 'rag', 'fidelidade', 'relevancia', 'ragas'],
 ['r-conjunto-de-avaliacao-versionado'], ['simulado', 'no-navegador'], LQ('medir', 'measure'),
 {'name': 'text', 'required': False, 'ui': 'examples', 'default': A_FAITH, 'examples': ex(A_FAITH, A_INVENT, A_DODGE)},
 [flag('metrics', 'metricas', 'metrics', 'list', options=METRICS, default=['relevance', 'faithfulness'], ui='checkboxes'),
  flag('limit', 'limite', 'threshold', 'number', min=0.5, max=0.95, step=0.01, default=0.8, ui='slider')],
 {'options': ['high', 'low'], 'answer': 'high'}, 'fooled',
 {'live': False,
  'consts': {'real': False, 'realSims': []},
  'compute': {
   'rec': 'lookup(answers, text, unknownAnswer)',
   'known': 'rec.known',
   'answerList': '[text]',
   'rel': 'real && len(realSims) > 0 ? realSims[0] : rec.rel',
   'faith': 'rec.nClaims > 0 ? rec.nSup / rec.nClaims : 0',
   'useRel': "includes(metrics, 'relevance')",
   'useFaith': "includes(metrics, 'faithfulness')",
   'relOk': 'rel >= limit',
   'faithOk': 'faith >= limit',
   'gatePass': '(!useRel || relOk) && (!useFaith || faithOk)',
   'relPct': 'round(rel * 100)',
   'faithPct': 'round(faith * 100)',
   'limitPct': 'round(limit * 100)',
   'watched': 'useRel && useFaith ? watchBoth : (useRel ? watchRel : (useFaith ? watchFaith : watchNone))',
   'flaw': 'rec.flaw'},
  'cases': [
   {'when': '!known && !real', 'error': 'unknownAnswer'},
   {'when': 'known && gatePass && rec.bad', 'flags': ['fooled']},
   {'when': 'known && !gatePass && rec.bad', 'flags': ['caught']},
   {'when': 'known && gatePass && !rec.bad', 'flags': ['passed']},
   {'when': 'known && !gatePass && !rec.bad', 'flags': ['falseAlarm']},
   {'when': 'true', 'vars': {'relPct': 'relPct', 'faithPct': 'faithPct', 'limitPct': 'limitPct', 'nSup': 'rec.nSup', 'nClaims': 'rec.nClaims',
                             'watched': 'watched', 'flaw': 'flaw'}}],
  'widgets': [
   {'type': 'flow', 'steps': [{'label': '@sQuestion', 'sub': '=question', 'tone': 'info'},
                              {'label': '@sContext', 'sub': '@subContext', 'tone': 'neutral'},
                              {'label': '@sAnswer', 'sub': "=real ? '@subReal' : '@subSim'", 'tone': 'neutral'},
                              {'label': '@sGate', 'sub': "=gatePass ? '@subPass' : '@subBlock'", 'tone': "=gatePass ? (known && rec.bad ? 'bad' : 'ok') : 'warn'"}]},
   {'type': 'metrics', 'items': [
     {'label': '@mRel', 'value': '=relPct', 'format': 'pct', 'tone': "=!useRel ? 'dim' : (relOk ? 'ok' : 'bad')"},
     {'label': '@mFaith', 'value': "=known ? faithPct : '—'", 'format': 'pct', 'tone': "=!useFaith ? 'dim' : (faithOk ? 'ok' : 'bad')"},
     {'label': '@mLimit', 'value': '=limitPct', 'format': 'pct', 'tone': 'info'}]},
   {'type': 'table', 'label': '@claimsTable', 'columns': ['@colClaim', '@colSup'], 'rows': '=zip(rec.claims, rec.supL)', 'tones': '=rec.tones', 'caption': '@claimsCaption'},
   {'type': 'checks', 'label': '@checks', 'items': [
     {'label': '@chkRel', 'ok': '=!useRel || relOk', 'why': '@whyRel'},
     {'label': '@chkFaith', 'ok': '=!useFaith || faithOk', 'why': '@whyFaith'}]},
   {'type': 'note', 'when': '=known && gatePass && rec.bad', 'tone': 'bad', 'text': '@fooledNote'},
   {'type': 'note', 'when': '=real', 'tone': 'info', 'text': '@realNote'},
   {'type': 'note', 'when': '=!real', 'tone': 'info', 'text': '@simNote'}]},
 {'no-navegador': {'adapter': 'declarative', 'model': E5, 'op': 'embed',
                   'args': {'query': 'question', 'against': 'answerList', 'queryPrefix': 'query: ', 'passagePrefix': 'query: '}}})

FAITH_CODE = '''import json
import os
import sys

from anthropic import Anthropic
from sentence_transformers import SentenceTransformer

MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-5-5")
client = Anthropic()
embedder = SentenceTransformer("intfloat/multilingual-e5-small")

JUDGE = (
    "Split the ANSWER into short factual claims. For each claim, say whether the CONTEXT supports it. "
    'Reply only with JSON: {"claims": [{"claim": "...", "supported": true}]}'
)


def faithfulness(context, answer):
    reply = client.messages.create(
        model=MODEL,
        max_tokens=600,
        thinking={"type": "disabled"},
        system=JUDGE,
        messages=[{"role": "user", "content": f"CONTEXT:\\n{context}\\n\\nANSWER:\\n{answer}"}],
    )
    text = "".join(b.text for b in reply.content if b.type == "text")
    if "{" not in text:
        raise RuntimeError("the judge returned no JSON")
    claims = json.loads(text[text.index("{"): text.rindex("}") + 1])["claims"]
    return sum(bool(c["supported"]) for c in claims) / max(1, len(claims)), claims


def relevance(question, answer):
    q, a = embedder.encode(["query: " + question, "query: " + answer], normalize_embeddings=True)
    return float(q @ a)


case = json.load(open(sys.argv[1], encoding="utf-8"))
score, claims = faithfulness("\\n".join(case["context"]), case["answer"])
for c in claims:
    print(("+ " if c["supported"] else "! ") + c["claim"])
print(f"faithfulness {score:.0%} | relevance {relevance(case['question'], case['answer']):.2f}")'''


def case_json(L):
    ctx = ', '.join(f'"{chunk(L, i)}"' for i in CTX_IDX)
    return f'{{"question": "{QUESTION[L]}", "context": [{ctx}], "answer": "{A_INVENT[L]}"}}'


def loc(L):
    pt = L == 'pt'; T = lambda a, b: a if pt else b
    cheat = T(f'medir "{A_INVENT[L]}" --metricas relevancia', f'measure "{A_INVENT[L]}" --metrics relevance')
    return {
  'title': T('Métricas de RAG: fidelidade e relevância', 'RAG metrics: faithfulness and relevance'),
  'subtitle': T('Responder ao assunto não é o mesmo que responder com o que o manual diz', 'Answering the topic isn’t the same as answering with what the handbook says'),
  'mission': T('No conjunto 2026-10, "acertou" ainda é decidido à mão pelo RH, e isso não escala. O time quer duas notas automáticas por resposta: relevância (responde à pergunta?) e fidelidade (cada afirmação está nos trechos que a busca trouxe?). Meça três respostas à mesma pergunta e descubra o que cada métrica deixa passar.',
               'On set 2026-10, "correct" is still decided by hand by HR, and that doesn’t scale. The team wants two automatic scores per answer: relevance (does it answer the question?) and faithfulness (is every claim in the chunks search brought?). Measure three answers to the same question and find out what each metric lets through.'),
  'predict': {'question': T('a resposta "Pode sim! Envie a conta de internet pelo app…" está errada, mas fala exatamente do assunto da pergunta. A relevância dela fica…',
                            'the answer "Yes, you can! Upload the internet bill…" is wrong, but it talks exactly about what was asked. Its relevance is…'),
              'options': {'high': T('Alta, perto da resposta certa', 'High, close to the right answer'), 'low': T('Baixa, porque está errada', 'Low, because it’s wrong')}},
  'feedback': {'right': T('isso: 90% de relevância, quase os 92% da resposta certa. Relevância mede se a resposta é sobre a pergunta, não se é verdade. Quem pega a mentira é a fidelidade: só 1 das 3 afirmações está nos trechos.',
                          'right: 90% relevance, almost the right answer’s 92%. Relevance measures whether the answer is about the question, not whether it’s true. Faithfulness catches the lie: only 1 of the 3 claims is in the chunks.'),
               'wrong': T('fica alta: 90%, quase os 92% da resposta certa. Relevância mede se a resposta é sobre a pergunta, não se é verdade. Quem pega a mentira é a fidelidade: só 1 das 3 afirmações está nos trechos.',
                          'it’s high: 90%, almost the right answer’s 92%. Relevance measures whether the answer is about the question, not whether it’s true. Faithfulness catches the lie: only 1 of the 3 claims is in the chunks.'),
               'skipped': T('sem palpite? Meça a resposta que diz "Pode sim!" e olhe as duas notas.', 'no guess? Measure the answer that says "Yes, you can!" and look at both scores.')},
  'coach': {'ui': T('palpite anotado. Escolha a resposta "Pode sim!" e rode com as duas métricas.', 'guess noted. Pick the "Yes, you can!" answer and run with both metrics.'),
            'cmd': T(f'palpite anotado. Rode medir "{A_INVENT[L]}" e compare as duas notas.', f'guess noted. Run measure "{A_INVENT[L]}" and compare both scores.')},
  'tryNext': {'ui': T('Agora a resposta que fala de trabalho remoto: tudo nela é verdade, mas ela não responde. Qual métrica pega?', 'Now the answer about remote work: everything in it is true, but it doesn’t answer. Which metric catches it?'),
              'cmd': T(f'Rode medir "{A_DODGE[L]}" e veja qual métrica pega.', f'Run measure "{A_DODGE[L]}" and see which metric catches it.')},
  'why': {'simples': T('Pense em dois professores corrigindo a mesma redação. Um só pergunta "falou do tema?". O outro confere "cada coisa que você escreveu está no livro?". Uma redação no tema, cheia de invenção, passa no primeiro e reprova no segundo. Uma redação toda verdadeira, mas sobre outro assunto, faz o contrário.\nO assistente precisa dos dois: responder ao que perguntaram (relevância) e só com o que o manual diz (fidelidade).',
                       'Picture two teachers grading the same essay. One only asks "is it on topic?". The other checks "is everything you wrote in the book?". An on-topic essay full of made-up facts passes the first and fails the second. An all-true essay about something else does the opposite.\nThe assistant needs both: answer what was asked (relevance) and only with what the handbook says (faithfulness).'),
          'dev': T('As duas métricas mais usadas para a resposta de um RAG, nos termos do Ragas: fidelidade (faithfulness) = afirmações da resposta sustentadas pelo contexto recuperado ÷ total de afirmações. Um LLM quebra a resposta em afirmações e confere cada uma contra os trechos. Relevância da resposta (response relevancy) no Ragas: um LLM gera perguntas a partir da resposta (3, por padrão) e a métrica é a média do cosseno entre os embeddings delas e o da pergunta original. Respostas evasivas (que não se comprometem) ganham nota 0 nessa métrica. Aqui simplificamos para o cosseno entre pergunta e resposta.\nNenhuma basta sozinha: ponha as duas no portão, cada uma com seu limite, e guarde as afirmações reprovadas no relatório, que é o que alguém vai ler quando a nota cair. Para a busca, use as métricas de recuperação da lição de Prática (recall@k) ou as de contexto do Ragas (precisão e recall de contexto).',
                   'The two most used metrics for a RAG answer, in Ragas’ terms: faithfulness = answer claims supported by the retrieved context ÷ total claims. An LLM splits the answer into claims and checks each one against the chunks. Response relevancy in Ragas: an LLM generates questions from the answer (3 by default) and the metric is the mean cosine between their embeddings and the original question’s. Noncommittal answers get a score of 0 on this metric. Here we simplify to the cosine between question and answer.\nNeither is enough alone: put both in the gate, each with its threshold, and keep the failed claims in the report, which is what someone will read when the score drops. For search, use the retrieval metrics from the Practice lesson (recall@k) or Ragas’ context metrics (context precision and recall).'),
          'especialista': T('Essas métricas são feitas por modelos e herdam os defeitos deles. A fidelidade depende de como o LLM fatia as afirmações (uma frase com três fatos pode virar uma afirmação só) e de quão bem ele julga negação e números ("até um terço" contra "metade"). A relevância por embeddings mede proximidade de assunto: a resposta errada que fala de internet fica perto da pergunta, e o cosseno de modelos como o e5 fica numa faixa alta e estreita, então o limite se calibra por modelo.\nAntes de usar como portão, meça a métrica contra rótulos humanos (próxima lição: o juiz também precisa de prova). E lembre o que elas não medem: fidelidade alta com contexto errado é uma resposta fiel ao trecho errado; por isso a fidelidade anda junto com as métricas de recuperação, não no lugar delas.',
                            'These metrics are computed by models and inherit their flaws. Faithfulness depends on how the LLM splits claims (a sentence with three facts may become one claim) and how well it judges negation and numbers ("up to one third" versus "half"). Embedding relevance measures topical closeness: the wrong answer about internet sits close to the question, and the cosine of models like e5 sits in a high, narrow band, so the threshold is calibrated per model.\nBefore using one as a gate, measure the metric against human labels (next lesson: the judge needs testing too). And remember what they don’t measure: high faithfulness with the wrong context is an answer faithful to the wrong chunk; that’s why faithfulness goes with retrieval metrics, not instead of them.')},
  'break': {'mission': {'ui': T('hora de quebrar: deixe só a relevância ligada e meça a resposta "Pode sim!".', 'time to break it: leave only relevance on and measure the "Yes, you can!" answer.'),
                        'cmd': T(f'hora de quebrar: rode {cheat}', f'time to break it: run {cheat}')},
            'success': T('Quebrou: o portão aprovou uma resposta que {flaw}. Ela teve relevância {relPct}% e fidelidade {faithPct}% ({nSup} de {nClaims} afirmações sustentadas pelos trechos), e o portão olhava {watched}, com limite de {limitPct}%. Cada métrica cobre o ponto cego da outra.',
                         'Broken: the gate approved an answer that {flaw}. It had {relPct}% relevance and {faithPct}% faithfulness ({nSup} of {nClaims} claims supported by the chunks), and the gate watched {watched}, with a {limitPct}% threshold. Each metric covers the other’s blind spot.'),
            'calm': T('Relevância {relPct}%, fidelidade {faithPct}%, limite {limitPct}% (o portão olha {watched}). Para quebrar, deixe passar uma resposta ruim com uma métrica só.',
                      'Relevance {relPct}%, faithfulness {faithPct}%, threshold {limitPct}% (the gate watches {watched}). To break it, let a bad answer through with a single metric.')},
  'hints': {'ui': T(['Escolha uma das três respostas e rode.', 'Relevância pergunta "é sobre a pergunta?"; fidelidade pergunta "cada afirmação está nos trechos?". O portão aprova quando todas as métricas ligadas passam do limite.', 'Só relevância ligada, resposta "Pode sim!".'],
                    ['Pick one of the three answers and run.', 'Relevance asks "is it about the question?"; faithfulness asks "is every claim in the chunks?". The gate approves when every metric that’s on is above the threshold.', 'Only relevance on, the "Yes, you can!" answer.']),
            'cmd': T(['A resposta vai entre aspas, depois de medir.', '--metricas relevancia,fidelidade (ou só uma, ou nenhuma); --limite de 0,5 a 0,95.', cheat],
                     ['The answer goes in quotes, after measure.', '--metrics relevance,faithfulness (or just one, or none); --threshold from 0.5 to 0.95.', cheat])},
  'errors': {'notInEnum.metrics': T('"{value}" não é uma métrica. Use: {options}.', '"{value}" is not a metric. Use: {options}.'),
             'belowMin.limit': T('Abaixo de 0,5 quase tudo passa.', 'Below 0.5 almost everything passes.'), 'aboveMax.limit': T('Acima de 0,95 nada passa.', 'Above 0.95 nothing passes.'),
             'model.unknownAnswer': T('No modo simulado, use uma das três respostas de exemplo (as afirmações delas foram conferidas à mão). Com "No navegador", a relevância é calculada de verdade para qualquer texto.',
                                      'In simulated mode, use one of the three example answers (their claims were checked by hand). With "In the browser", relevance is computed for real for any text.')},
  'controls': {'arg': T('Resposta do assistente', 'Assistant’s answer'), 'metrics': T('Métricas no portão', 'Metrics in the gate'), 'limit': T('Nota mínima de cada métrica', 'Minimum score per metric')},
  'scene': {'label': T('Medir uma resposta', 'Measuring an answer'), 'empty': T('Rode para medir.', 'Run to measure.'),
    'sQuestion': T('Pergunta', 'Question'), 'sContext': T('Contexto', 'Context'), 'subContext': T('4 trechos da busca', '4 chunks from search'), 'sAnswer': T('Resposta', 'Answer'),
    'subSim': T('afirmações conferidas', 'claims checked'), 'subReal': T('relevância real (e5)', 'real relevance (e5)'), 'sGate': T('Portão', 'Gate'), 'subPass': T('aprovada', 'approved'), 'subBlock': T('barrada', 'blocked'),
    'mRel': T('relevância', 'relevance'), 'mFaith': T('fidelidade', 'faithfulness'), 'mLimit': T('limite', 'threshold'),
    'claimsTable': T('Afirmações da resposta', 'Claims in the answer'), 'colClaim': T('afirmação', 'claim'), 'colSup': T('nos trechos?', 'in the chunks?'),
    'supYes': T('sim', 'yes'), 'supNo': T('não', 'no'),
    'claimsCaption': T('fidelidade = {nSup} de {nClaims} afirmações sustentadas', 'faithfulness = {nSup} of {nClaims} claims supported'),
    'checks': T('Portão de qualidade', 'Quality gate'),
    'chkRel': T('Relevância acima do limite', 'Relevance above the threshold'), 'whyRel': T('relevância {relPct}%, abaixo de {limitPct}%: não responde ao que foi perguntado', 'relevance {relPct}%, below {limitPct}%: it doesn’t answer what was asked'),
    'chkFaith': T('Fidelidade acima do limite', 'Faithfulness above the threshold'), 'whyFaith': T('fidelidade {faithPct}%: há afirmações que os trechos não sustentam', 'faithfulness {faithPct}%: some claims aren’t supported by the chunks'),
    'fooledNote': T('O portão aprovou, mas a resposta {flaw}. Ele olhava {watched}.', 'The gate approved, but the answer {flaw}. It watched {watched}.'),
    'realNote': T('Relevância real: cosseno entre a pergunta e a resposta no multilingual-e5-small, no seu navegador. Os cossenos do e5 ficam numa faixa alta e estreita (quase tudo passa de 0,8), então para ele um limite mais rígido, perto de 0,88, é o que separa melhor. A fidelidade só existe para as 3 respostas de exemplo (vem das afirmações conferidas à mão); para um texto desconhecido ela aparece como 0.',
                  'Real relevance: cosine between question and answer with multilingual-e5-small, in your browser. e5 cosines sit in a high, narrow band (almost everything is above 0.8), so for it a stricter threshold, around 0.88, separates better. Faithfulness exists only for the 3 built-in example answers (it comes from the hand-checked claims); for unknown text it shows as 0.'),
    'simNote': T('Modo simulado: afirmações e relevância escritas à mão para as três respostas. Use "No navegador" para a relevância com embeddings de verdade.', 'Simulated mode: claims and relevance hand-written for the three answers. Use "In the browser" for relevance with real embeddings.')},
  'data': {'question': QUESTION[L], 'answers': answers(L),
           'unknownAnswer': {'id': 'unknown', 'known': False, 'rel': 0, 'claims': [], 'sup': [], 'supL': [], 'tones': [], 'nSup': 0, 'nClaims': 0, 'bad': False, 'flaw': ''},
           'watchBoth': T('relevância e fidelidade', 'relevance and faithfulness'), 'watchRel': T('só a relevância', 'relevance only'),
           'watchFaith': T('só a fidelidade', 'faithfulness only'), 'watchNone': T('nenhuma métrica', 'no metric')},
  'recipe': {'steps': [
     T('Instale as bibliotecas e guarde a chave da API da Anthropic (no PowerShell: $env:ANTHROPIC_API_KEY = "sua-chave"):\npip install anthropic sentence-transformers\nexport ANTHROPIC_API_KEY="sua-chave"',
       'Install the libraries and keep your Anthropic API key in the environment (in PowerShell: $env:ANTHROPIC_API_KEY = "your-key"):\npip install anthropic sentence-transformers\nexport ANTHROPIC_API_KEY="your-key"'),
     T('Salve um caso como case_invent.json (pergunta, trechos recuperados e a resposta a medir):\n', 'Save a case as case_invent.json (question, retrieved chunks and the answer to measure):\n') + case_json(L),
     T('Crie rag_metrics.py. Um LLM quebra a resposta em afirmações e diz se o contexto sustenta cada uma (fidelidade); a relevância é o cosseno entre pergunta e resposta (uma simplificação da métrica do Ragas, que gera perguntas a partir da resposta):\n',
       'Create rag_metrics.py. An LLM splits the answer into claims and says whether the context supports each one (faithfulness); relevance is the cosine between question and answer (a simplification of Ragas’ metric, which generates questions from the answer):\n') + FAITH_CODE,
     T('Rode com a resposta que inventa e depois troque "answer" no JSON pela resposta fiel e pela que enrola:\npython rag_metrics.py case_invent.json', 'Run it with the answer that makes things up, then swap "answer" in the JSON for the faithful one and the one that dodges:\npython rag_metrics.py case_invent.json')],
   'ok': T('a resposta que inventa sai com fidelidade baixa (a afirmação de que a internet é reembolsável marcada com !) e relevância parecida com a da resposta fiel; a que enrola sai com fidelidade alta e relevância menor que as outras duas.',
           'the made-up answer comes out with low faithfulness (the claim that internet is reimbursable marked with !) and relevance close to the faithful answer’s; the dodging one comes out with high faithfulness and lower relevance than the other two.')}}


def tch():
    return teacher(
 {'objectives': ['Distinguir relevância de fidelidade.', 'Calcular fidelidade como afirmações sustentadas ÷ afirmações.', 'Combinar métricas num portão.'], 'minutes': 20,
  'activity': 'Cada dupla recebe uma pergunta, quatro trechos e três respostas. Uma pessoa sublinha cada afirmação e marca se está nos trechos; a outra dá nota de 0 a 10 para "responde à pergunta". Comparem as duas notas de cada resposta.',
  'discussion': ['Qual erro é pior para o RH: resposta no tema e inventada, ou verdadeira e fora do tema?', 'Quem confere o juiz que separa as afirmações?'],
  'misconceptions': ['"Se a resposta fala do assunto, está certa." Relevância não mede verdade.', '"Fidelidade 100% é resposta perfeita." Pode ser fiel e não responder.']},
 {'objectives': ['Tell relevance from faithfulness.', 'Compute faithfulness as supported claims ÷ claims.', 'Combine metrics in a gate.'], 'minutes': 20,
  'activity': 'Each pair gets a question, four chunks and three answers. One person underlines each claim and marks whether it’s in the chunks; the other rates "answers the question" 0 to 10. Compare both scores for each answer.',
  'discussion': ['Which error is worse for HR: on-topic and made up, or true and off-topic?', 'Who checks the judge that splits the claims?'],
  'misconceptions': ['"If the answer is on topic, it’s right." Relevance doesn’t measure truth.', '"100% faithfulness is a perfect answer." It can be faithful and not answer.']})


def build():
    write('02-metricas-de-rag', s, loc('pt'), loc('en'), tch())
