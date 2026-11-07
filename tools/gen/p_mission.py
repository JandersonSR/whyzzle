"""IA aplicada · Prática · 23 · Missão final: assistente de RH da Aurora (ingestão limpa, busca híbrida, limite,
citação [n], recusa, triagem para uma pessoa e avaliação com perguntas fixas). Rode com python3."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p1_common import *
from p2_corpus import *

N_CLEAN = 12
def opt(id, pt, en): return {'id': id, 'pt': pt, 'en': en}
def loc(pt, en): return {'pt': pt, 'en': en}

# ---- índice: 12 trechos limpos + 3 extras do PDF sujo (colunas 12..14 da matriz)
# col 12 = trecho 0 com palavra quebrada por hífen; col 13 = cópia do trecho 9 (rodapé repetido); col 14 = cabeçalho de página
BROKEN0 = {'pt': 'As férias devem ser solicitadas pelo portal do colaborador com 30 dias de ante- cedência e dependem da aprovação do gestor.',
           'en': 'Vacation must be requested through the employee portal 30 days in ad- vance and needs the manager’s approval.'}
HEADER = {'pt': 'AURORA TECNOLOGIA LTDA · CONFIDENCIAL Manual do Colaborador · Página 1 de 2',
          'en': 'AURORA TECNOLOGIA LTDA · CONFIDENTIAL Employee Handbook · Page 1 of 2'}
CLEAN_COLS = list(range(N_CLEAN))
DIRTY_COLS = [12] + list(range(1, N_CLEAN)) + [13, 14]
def all_texts(L):
    t = [x for _, x in CHUNKS[L]]
    return t + [BROKEN0[L], t[9], HEADER[L]]
def ext(v): return v + [v[0], v[9], 0.70]

OFF = {'pt': 'Qual o horário da academia da empresa?', 'en': 'What are the company gym’s opening hours?'}
DOG = {'pt': 'Posso levar meu cachorro para o escritório?', 'en': 'Can I bring my dog to the office?'}
HARASS = {'pt': 'Estou sofrendo assédio do meu gestor. O que eu faço?', 'en': 'My manager is harassing me. What do I do?'}
SALARY = {'pt': 'Quero contestar meu salário: acho que ganho menos que um colega na mesma função.',
          'en': 'I want to dispute my salary: I think I earn less than a colleague in the same role.'}
OFFSIMS = [0.73, 0.71, 0.71, 0.72, 0.73, 0.72, 0.74, 0.73, 0.71, 0.72, 0.71, 0.71]
# (texto, tipo, gold, sims de 12 trechos)
# a pergunta do reembolso da internet: em inglês o texto original compartilha "home" com o trecho 7 e passaria com k = 2
Q_INTERNET = {'pt': QUESTIONS[5][0]['pt'], 'en': 'Can I get my home internet bill reimbursed?'}
assert QUESTIONS[5][1] == [9, 7]
QSET = [({**q, **Q_INTERNET} if i == 5 else q, 'ans', g, s) for i, (q, g, s) in enumerate(QUESTIONS)] + [
    (OFF, 'out', [], OFFSIMS),
    (DOG, 'out', [], sem({6: 0.74, 0: 0.72, 7: 0.72})),
    (HARASS, 'sens', [], sem({0: 0.76, 6: 0.75, 1: 0.72})),
    (SALARY, 'sens', [], sem({7: 0.80, 5: 0.77, 3: 0.74}))]
TRIGGERS = {'pt': ['assédio', 'assedio', 'denúncia', 'denuncia', 'contestar', 'discriminação', 'discriminacao'],
            'en': ['harass', 'dispute', 'discriminat']}
NQ = len(QSET)
QSHORT = [loc('Antecedência das férias', 'Vacation notice'), loc('Dividir férias', 'Splitting vacation'), loc('Quando sai a PLR', 'When PLR is paid'),
          loc('Perfil de VPN', 'VPN profile'), loc('Dependente no plano', 'Health plan dependent'), loc('Internet de casa', 'Home internet bill'),
          loc('Avisar antes de descansar', 'Notice for time off'), loc('Vender férias e VR', 'Sell vacation and VR'), loc('Senha esquecida', 'Forgotten password'),
          loc('Academia (fora)', 'Gym (outside)'), loc('Cachorro (fora)', 'Dog (outside)'), loc('Assédio', 'Harassment'), loc('Contestar salário', 'Salary dispute')]
assert len(QSHORT) == NQ and all(len(x[l]) <= 25 for x in QSHORT for l in ('pt', 'en'))
KIND = [k for _, k, _, _ in QSET]
IANS = [i for i, k in enumerate(KIND) if k == 'ans']
IOUT = [i for i, k in enumerate(KIND) if k == 'out']
ISENS = [i for i, k in enumerate(KIND) if k == 'sens']
CONF = [max(s) for _, _, _, s in QSET]
for L in ('pt', 'en'):  # a máscara de triagem tem de bater com a lista de gatilhos nos dois idiomas
    for i, (q, k, _, _) in enumerate(QSET):
        hit = any(t in q[L].lower() for t in TRIGGERS[L])
        assert hit == (k == 'sens'), (L, i, q[L])

def sim():
    c = {}
    c['real'] = False; c['realMatrix'] = []
    c['semMatrix'] = [ext(s) for _, _, _, s in QSET]
    c['golds'] = [g for _, _, g, _ in QSET]
    c['confs'] = CONF
    c['cleanCols'] = CLEAN_COLS; c['dirtyCols'] = DIRTY_COLS
    c['ansMask'] = [1 if k == 'ans' else 0 for k in KIND]
    c['nAns'] = len(IANS); c['nOut'] = len(IOUT); c['nSens'] = len(ISENS)
    c['weight'] = 0.5; c['needRecall'] = 0.8
    comp = {}
    comp['cols'] = 'clean ? cleanCols : dirtyCols'
    comp['texts'] = 'pickall(allTexts, cols)'
    comp['M0'] = 'real ? realMatrix : semMatrix'
    comp['rowsM'] = '[' + ', '.join(f'pickall(M0[{i}], cols)' for i in range(NQ)) + ']'
    comp['VM'] = 'minmaxall(rowsM)'
    comp['KW'] = 'bm25all(questions, texts, stop)'
    comp['HY'] = 'blendall(VM, KW, weight)'
    comp['S'] = "mode == 'vector' ? VM : (mode == 'keyword' ? KW : HY)"
    comp['recK'] = 'recallall(S, golds, k)'
    comp['rec1'] = 'recallall(S, golds, 1)'
    good, wrongref, citebad, kinds = [], [], [], []
    for i, kd in enumerate(KIND):
        comp[f't{i}'] = 'triage' if kd == 'sens' else 'false'
        comp[f'r{i}'] = f'!t{i} && refuse && confs[{i}] < limit'
        if kd == 'ans':
            comp[f'g{i}'] = f'(!r{i} && recK[{i}] == 1) ? 1 : 0'
            comp[f'w{i}'] = f'r{i} ? 1 : 0'
            comp[f'cb{i}'] = f'(!r{i} && rec1[{i}] == 0) ? 1 : 0'
            comp[f'x{i}'] = f"r{i} ? '@xAnsRefused' : (recK[{i}] == 1 ? '@xAnsOk' : '@xAnsWrong')"
        elif kd == 'out':
            comp[f'g{i}'] = f'r{i} ? 1 : 0'
            comp[f'x{i}'] = f"r{i} ? '@xOutRefused' : '@xOutInvented'"
        else:
            comp[f'g{i}'] = f't{i} ? 1 : 0'
            comp[f'x{i}'] = f"t{i} ? '@xSensRouted' : (r{i} ? '@xSensRefused' : '@xSensAnswered')"
        good.append(f'g{i}')
    comp['meanRec'] = 'sum(mul(recK, ansMask)) / nAns'
    comp['nCorrect'] = ' + '.join(f'g{i}' for i in IANS)
    comp['nOutRef'] = ' + '.join(f'g{i}' for i in IOUT)
    comp['nRouted'] = ' + '.join(f'g{i}' for i in ISENS)
    comp['nFalseRef'] = ' + '.join(f'w{i}' for i in IANS)
    comp['nCiteBad'] = ' + '.join(f'cb{i}' for i in IANS)
    comp['okRecall'] = 'meanRec >= needRecall'
    comp['okAnswers'] = 'nCorrect == nAns'
    comp['okCite'] = 'cite && nCiteBad == 0'
    comp['okRefuse'] = 'nOutRef == nOut && nFalseRef == 0'
    comp['okTriage'] = 'nRouted == nSens'
    comp['okClean'] = 'clean'
    comp['okCount'] = ' + '.join(f'({x} ? 1 : 0)' for x in ['okRecall', 'okAnswers', 'okCite', 'okRefuse', 'okTriage', 'okClean'])
    comp['allOk'] = 'okCount == 6'
    comp['recPct'] = 'round(meanRec * 100)'
    comp['limitPct'] = 'round(limit * 100)'
    comp['nGood'] = ' + '.join(good)
    return c, comp

# ------------------------------------------------------------------ widgets
def widgets():
    exp_keys = {'ans': '@eAns', 'out': '@eOut', 'sens': '@eSens'}
    tones = '[' + ', '.join(f"g{i} == 1 ? 'ok' : 'bad'" for i in range(NQ)) + ']'
    results = '[' + ', '.join(f'x{i}' for i in range(NQ)) + ']'
    return [
        {'type': 'flow', 'label': '@pipeline', 'steps': [
            {'label': '@sIngest', 'sub': "=clean ? '@subClean' : '@subDirty'", 'tone': "=clean ? 'ok' : 'warn'"},
            {'label': '@sSearch', 'sub': "=mode == 'keyword' ? '@subKeyword' : (mode == 'vector' ? '@subVector' : '@subHybrid')",
             'tone': "=mode == 'hybrid' ? 'ok' : 'warn'"},
            {'label': '@sGate', 'sub': "=limit > 0 ? limitPct + '%' : '@subNoGate'", 'tone': "=limit > 0 ? 'ok' : 'warn'"},
            {'label': '@sAnswer', 'sub': "=cite ? (refuse ? '@subCiteRefuse' : '@subCite') : (refuse ? '@subNoCiteRefuse' : '@subNoCite')", 'tone': "=cite && refuse ? 'ok' : 'warn'"},
            {'label': '@sTriage', 'sub': "=triage ? '@subTriageOn' : '@subTriageOff'", 'tone': "=triage ? 'ok' : 'warn'"}]},
        {'type': 'checks', 'label': '@checks', 'items': [
            {'label': '@cRecall', 'ok': '=okRecall', 'why': '@cRecallWhy'},
            {'label': '@cAnswers', 'ok': '=okAnswers', 'why': "=!clean ? '@cAnswersWhyDirty' : (nFalseRef > 0 ? '@cAnswersWhyRef' : '@cAnswersWhyRet')"},
            {'label': '@cCite', 'ok': '=okCite', 'why': "=cite ? '@cCiteWhyBad' : '@cCiteWhyOff'"},
            {'label': '@cRefuse', 'ok': '=okRefuse', 'why': "=!refuse ? '@cRefuseWhyOff' : (nFalseRef > 0 ? '@cRefuseWhyHigh' : '@cRefuseWhyLow')"},
            {'label': '@cTriage', 'ok': '=okTriage', 'why': '@cTriageWhy'},
            {'label': '@cClean', 'ok': '=okClean', 'why': '@cCleanWhy'}]},
        {'type': 'metrics', 'items': [
            {'label': '@mRecall', 'value': '=recPct', 'format': 'pct', 'tone': "=okRecall ? 'ok' : 'bad'"},
            {'label': '@mAnswers', 'value': "=nCorrect + ' / ' + nAns", 'tone': "=okAnswers ? 'ok' : 'bad'"},
            {'label': '@mRefusals', 'value': "=nOutRef + ' / ' + nOut", 'tone': "=nOutRef == nOut ? 'ok' : 'bad'"},
            {'label': '@mRouted', 'value': "=nRouted + ' / ' + nSens", 'tone': "=okTriage ? 'ok' : 'bad'"}]},
        {'type': 'table', 'label': '@table', 'columns': ['@colRes', '@colQ', '@colConf', '@colExp'],
         'rows': f'=zip({results}, qShort, confLabels, expKeys)', 'tones': f'={tones}', 'caption': '@tableCaption'},
        {'type': 'note', 'when': '=real', 'tone': 'info', 'text': '@realNote'},
        {'type': 'note', 'when': '=!real', 'tone': 'info', 'text': '@simNote'}]

def sim_full():
    c, comp = sim()
    c['expKeys'] = [{'ans': '@eAns', 'out': '@eOut', 'sens': '@eSens'}[k] for k in KIND]
    c['confLabels'] = ['—' if k == 'sens' else f'{round(x * 100)}%' for x, k in zip(CONF, KIND)]
    cases = [
        {'when': 'allOk', 'flags': ['passed']},
        {'when': '!okRecall', 'flags': ['lowRecall']},
        {'when': '!okAnswers', 'flags': ['wrongAnswers']},
        {'when': '!okCite', 'flags': ['noCitation']},
        {'when': '!okRefuse', 'flags': ['badRefusal']},
        {'when': '!okTriage', 'flags': ['noTriage']},
        {'when': '!okClean', 'flags': ['dirtyIndex']},
        {'when': 'true', 'vars': {'recPct': 'recPct', 'nCorrect': 'nCorrect', 'nAns': 'nAns', 'nOutRef': 'nOutRef', 'nOut': 'nOut', 'nRouted': 'nRouted',
                                  'nSens': 'nSens', 'k': 'k', 'limitPct': 'limitPct', 'nFalseRef': 'nFalseRef', 'nCiteBad': 'nCiteBad', 'ok': 'okCount'}}]
    return {'live': True, 'consts': c, 'compute': comp, 'cases': cases, 'widgets': widgets()}

def flags_def():
    return [
        flag('clean', 'limpar', 'clean', 'bool', default=False, ui='switch'),
        flag('mode', 'modo', 'mode', 'enum', options=[opt('keyword', 'palavra', 'keyword'), opt('vector', 'vetor', 'vector'), opt('hybrid', 'hibrida', 'hybrid')],
             default='keyword', ui='select'),
        flag('k', 'k', 'k', 'int', min=1, max=6, default=1, ui='slider'),
        flag('limit', 'limite', 'threshold', 'number', min=0, max=0.99, step=0.01, default=0, ui='slider'),
        flag('cite', 'citar', 'cite', 'bool', default=False, ui='switch'),
        flag('refuse', 'recusar', 'refuse', 'bool', default=False, ui='switch'),
        flag('triage', 'triagem', 'triage', 'bool', default=False, ui='switch')]

def last_p3_id():
    import glob, json
    fs = sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'content', 'ia-aplicada', 'pratica', '22-*', 'step.json')))
    assert fs, 'faltam as lições P3 (22-*)'
    return json.load(open(fs[0]))['id']

# ------------------------------------------------------------------ código da receita (por idioma)
RECIPE_QS = {}
for L in ('pt', 'en'):
    lines = []
    for i in (0, 1, 2, 3, 6, 5):
        q, k, g, _ = QSET[i]; lines.append(f'    ("{q[L]}", "answer", {g}),')
    lines.append(f'    ("{OFF[L]}", "outside", []),')
    lines.append(f'    ("{HARASS[L]}", "sensitive", []),')
    RECIPE_QS[L] = lines

def corpus_code(L):
    chunks = '\n'.join(f'    "{t}",' for _, t in CHUNKS[L])
    cm = {'pt': '# (pergunta, tipo, índices dos trechos que respondem): "answer" = o manual responde; "outside" = não está no manual; "sensitive" = vai para uma pessoa',
          'en': '# (question, kind, indices of the chunks that answer): "answer" = the handbook answers; "outside" = not in the handbook; "sensitive" = goes to a person'}[L]
    return 'CHUNKS = [\n' + chunks + '\n]\n\n' + cm + '\nQUESTIONS = [\n' + '\n'.join(RECIPE_QS[L]) + '\n]'

def assistant_code(L):
    pt = L == 'pt'
    T = lambda a, b: a if pt else b
    refusal = T('Não encontrei isso no manual. Vou encaminhar sua pergunta para o RH.', "I couldn't find that in the handbook. I'll forward your question to HR.")
    mark = T('Não encontrei', 'find that in the handbook')
    system_lines = T(
        ['    "Você é o assistente de RH da Aurora. Responda em português, em uma ou duas frases, "',
         '    "usando só os trechos numerados. Termine cada frase com o número do trecho entre colchetes, como [3]. "',
         '    f\'Se os trechos não responderem, diga exatamente: "{REFUSAL}"\''],
        ['    "You are Aurora\'s HR assistant. Answer in English, in one or two sentences, "',
         '    "using only the numbered chunks. End each sentence with the chunk number in brackets, like [3]. "',
         '    f\'If the chunks don\\\'t answer, say exactly: "{REFUSAL}"\''])
    sensitive = T('ass[ée]dio|den[úu]ncia|contestar|discrimina', 'harass|discriminat|dispute')
    stop = T('"qual", "como", "quando", "quanto", "posso", "para", "com", "meu", "minha", "que", "uma", "de", "do", "da", "no", "na", "o", "a", "os", "as", "e", "ou", "eu", "em", "se", "devo", "vou"',
             '"what", "which", "how", "when", "can", "the", "for", "with", "my", "your", "that", "this", "and", "you", "do", "to", "of", "in", "is", "an", "on", "a", "i", "it", "me", "should", "tell", "them"')
    qlabel = T('Pergunta', 'Question')
    handoff = T('Passei sua pergunta para uma pessoa do RH (protocolo RH-', 'I passed your question to a person in HR (ticket HR-')
    return f'''import os, re, unicodedata, uuid
import numpy as np
from anthropic import Anthropic
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from corpus import CHUNKS

K = int(os.environ.get("K", "3"))
LIMIT = float(os.environ.get("LIMIT", "0.80"))
MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-5-5")
REFUSAL = "{refusal}"
REFUSAL_MARK = "{mark}"
SYSTEM = (
{chr(10).join(system_lines)}
)
SENSITIVE = re.compile(r"{sensitive}", re.I)
STOP = {{{stop}}}

def tokens(text):
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return [t for t in re.split(r"[^a-z0-9]+", text) if len(t) > 1 and t not in STOP]

def minmax(x):
    x = np.asarray(x, dtype=float)
    span = x.max() - x.min()
    return (x - x.min()) / span if span else np.zeros_like(x)

embedder = SentenceTransformer("intfloat/multilingual-e5-small")
vectors = embedder.encode(["passage: " + c for c in CHUNKS], normalize_embeddings=True)
bm25 = BM25Okapi([tokens(c) for c in CHUNKS])
client = Anthropic()

def search(question):
    q = embedder.encode("query: " + question, normalize_embeddings=True)
    sims = vectors @ q
    mix = 0.5 * minmax(sims) + 0.5 * minmax(bm25.get_scores(tokens(question)))
    top = [int(i) for i in np.argsort(-mix)[:K]]
    return top, float(sims.max())

def handle(question):
    if SENSITIVE.search(question):
        text = "{handoff}" + uuid.uuid4().hex[:6] + ")."
        return {{"action": "handoff", "text": text, "top": [], "cited": [], "conf": 0.0}}
    top, conf = search(question)
    if conf < LIMIT:
        return {{"action": "refuse", "text": REFUSAL, "top": top, "cited": [], "conf": conf}}
    context = "\\n".join(f"[{{i + 1}}] {{CHUNKS[i]}}" for i in top)
    reply = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=SYSTEM,
        messages=[{{"role": "user", "content": context + "\\n\\n{qlabel}: " + question}}],
    )
    text = "".join(b.text for b in reply.content if b.type == "text").strip()
    cited = [n - 1 for n in map(int, re.findall(r"\\[(\\d+)\\]", text)) if n - 1 in top]
    action = "refuse" if REFUSAL_MARK in text else "answer"
    return {{"action": action, "text": text, "top": top, "cited": cited, "conf": conf}}'''

def eval_code(L):
    return '''from assistant import handle, K
from corpus import QUESTIONS

score = {"answer": [0, 0], "outside": [0, 0], "sensitive": [0, 0]}
recalls = []
for question, kind, gold in QUESTIONS:
    r = handle(question)
    if kind == "answer":
        recall = len(set(gold) & set(r["top"])) / len(gold)
        recalls.append(recall)
        ok = r["action"] == "answer" and recall == 1 and bool(set(r["cited"]) & set(gold))
    elif kind == "outside":
        ok = r["action"] == "refuse"
    else:
        ok = r["action"] == "handoff"
    score[kind][0] += ok
    score[kind][1] += 1
    print(("OK " if ok else "XX ") + f"{kind:9} conf={r['conf']:.2f} top={r['top']} | {question}")

mean_recall = sum(recalls) / len(recalls)
print(f"\\nrecall@{K}: {mean_recall:.0%} | answers: {score['answer'][0]}/{score['answer'][1]}"
      f" | refusals: {score['outside'][0]}/{score['outside'][1]} | handoffs: {score['sensitive'][0]}/{score['sensitive'][1]}")
print("PASSED" if mean_recall >= 0.8 and all(a == b for a, b in score.values()) else "FAILED")'''

# ------------------------------------------------------------------ textos
def locale(L):
    pt = L == 'pt'
    T = lambda a, b: a if pt else b
    cmd_fixed = T('montar "assistente-rh" --limpar sim --modo hibrida --k 3 --limite 0.78 --citar sim --recusar sim --triagem sim',
                  'build "hr-assistant" --clean yes --mode hybrid --k 3 --threshold 0.78 --cite yes --refuse yes --triage yes')
    refusal = T('Não encontrei isso no manual. Vou encaminhar sua pergunta para o RH.', 'I couldn’t find that in the handbook. I’ll forward your question to HR.')
    install = T(
        'Crie uma pasta e um ambiente virtual do Python 3 e instale as bibliotecas. A primeira execução baixa o modelo de embeddings do Hugging Face (algumas centenas de MB):\n'
        'python -m venv .venv\nsource .venv/bin/activate\n'
        'O pip também instala o PyTorch (pode ser grande). Para uma instalação menor, só com CPU, instale-o primeiro:\n'
        'pip install torch --index-url https://download.pytorch.org/whl/cpu\n'
        'pip install sentence-transformers rank_bm25 anthropic\n'
        'No Windows, ative com .venv\\Scripts\\activate. Depois guarde a chave da API da Anthropic na variável de ambiente (no PowerShell: $env:ANTHROPIC_API_KEY = "sua-chave"):\n'
        'export ANTHROPIC_API_KEY="sua-chave"',
        'Create a folder and a Python 3 virtual environment and install the libraries. The first run downloads the embedding model from Hugging Face (a few hundred MB):\n'
        'python -m venv .venv\nsource .venv/bin/activate\n'
        'pip also installs PyTorch (it can be large). For a smaller, CPU-only install, install it first:\n'
        'pip install torch --index-url https://download.pytorch.org/whl/cpu\n'
        'pip install sentence-transformers rank_bm25 anthropic\n'
        'On Windows, activate with .venv\\Scripts\\activate. Then keep your Anthropic API key in the environment variable (in PowerShell: $env:ANTHROPIC_API_KEY = "your-key"):\n'
        'export ANTHROPIC_API_KEY="your-key"')
    return {
  'title': T('Missão: o assistente de RH da Aurora', 'Mission: Aurora’s HR assistant'),
  'subtitle': T('Citar a fonte, recusar quando não sabe e passar o delicado para uma pessoa', 'Cite the source, refuse when it doesn’t know and hand the delicate stuff to a person'),
  'mission': T('A Aurora vai abrir o assistente de RH para todos os colaboradores. Ele responde dúvidas a partir do manual: busca os trechos, cita de onde tirou a resposta e, quando não sabe ou o assunto é delicado, não improvisa. Hoje ele está montado do pior jeito possível: o PDF entra sujo, a busca só olha palavras, vem um trecho só, não há limite de confiança, não cita, não recusa e trata assédio como dúvida de benefício. Há 13 perguntas fixas: 9 que o manual responde, 2 que ele não cobre (academia, cachorro no escritório) e 2 delicadas (assédio e contestação de salário). Conserte a montagem até os seis critérios ficarem verdes. (O manual é o de brinquedo, com 12 trechos, e as semelhanças dos vetores são escritas à mão; com "No navegador" a busca usa vetores de verdade.)',
               'Aurora is opening the HR assistant to all employees. It answers questions from the handbook: it retrieves chunks, cites where the answer came from and, when it doesn’t know or the topic is delicate, it doesn’t improvise. Right now it’s built the worst possible way: the PDF goes in dirty, search only looks at words, only one chunk comes back, there’s no confidence threshold, it doesn’t cite, doesn’t refuse and treats harassment like a benefits question. There are 13 fixed questions: 9 the handbook answers, 2 it doesn’t cover (gym, dog at the office) and 2 delicate ones (harassment and a salary dispute). Fix the setup until all six criteria turn green. (The handbook is the toy one with 12 chunks, and the vector similarities are hand-written; with "In the browser" search uses real vectors.)'),
  'coach': {'ui': T('Mexa nos controles; os critérios mudam enquanto você ajusta. Cada um que falhar diz o porquê, e a tabela mostra o que o assistente fez com cada pergunta.', 'Move the controls; the criteria change as you adjust. Each failing one says why, and the table shows what the assistant did with each question.'),
            'cmd': T('Edite o comando e rode. Cada critério que falhar diz o porquê. Tudo que você precisa apareceu nas lições 8 a 15 (limpeza, busca, citação e recusa) e na 19 (triagem).', 'Edit the command and run it. Each failing criterion says why. Everything you need showed up in lessons 8 to 15 (clean-up, search, citation and refusal) and 19 (triage).')},
  'why': {'simples': T('Um bom atendente de RH faz cinco coisas sem pensar: lê um manual limpo (sem página repetida), procura a resposta pelo sentido e pela palavra exata, diz de qual página tirou, admite "isso eu não sei" e, se o assunto é assédio ou salário, chama uma pessoa em vez de responder de cabeça.\nVocê montou um atendente assim. Cada peça cobre o erro da outra: a busca só por palavra não entende "descansar", só por sentido tropeça em sigla como PLR; a citação deixa conferir; a recusa evita o horário da academia inventado; a triagem entrega o que não é para máquina.',
                       'A good HR clerk does five things without thinking: reads a clean handbook (no repeated pages), looks for the answer by meaning and by exact word, says which page it came from, admits "I don’t know that" and, if the topic is harassment or salary, calls a person instead of answering off the cuff.\nYou built a clerk like that. Each piece covers the other’s mistake: word-only search doesn’t understand "time off", meaning-only search trips on acronyms like PLR; citation lets you check; refusal prevents invented gym hours; triage hands over what isn’t for a machine.'),
          'dev': T('O pipeline tem seis estações: ingestão limpa (sem cabeçalho repetido, duplicata nem palavra cortada por hífen), busca híbrida (BM25 + embeddings, notas min-max misturadas com um peso), top-k que cubra perguntas compostas, portão de confiança antes do LLM, prompt com trechos numerados, citação [n] e frase fixa de recusa, e triagem determinística antes de tudo.\nA triagem vem primeiro e não depende do modelo: uma lista de gatilhos (ou um classificador) manda assédio, denúncia e contestação de salário para uma pessoa, com a pergunta e um protocolo. Depois vem a busca; se a melhor similaridade fica abaixo do limite, o código devolve a recusa sem chamar o LLM; senão o LLM responde só com os trechos e o código confere se cada [n] existe entre eles. No fim, um laço de avaliação roda perguntas fixas (respondíveis, fora do manual, delicadas) e mede recall@k, respostas certas, recusas certas e encaminhamentos certos, a cada mudança.',
                   'The pipeline has six stations: clean ingestion (no repeated header, duplicate or hyphen-cut word), hybrid search (BM25 + embeddings, min-max scores mixed with a weight), a top-k that covers compound questions, a confidence gate before the LLM, a prompt with numbered chunks, [n] citation and a fixed refusal sentence, and deterministic triage before anything else.\nTriage comes first and doesn’t depend on the model: a trigger list (or a classifier) sends harassment, complaints and salary disputes to a person, with the question and a ticket number. Then comes search; if the best similarity is below the threshold, the code returns the refusal without calling the LLM; otherwise the LLM answers from the chunks only and the code checks that every [n] exists among them. At the end, an evaluation loop runs fixed questions (answerable, outside the handbook, delicate) and measures recall@k, correct answers, correct refusals and correct handoffs, on every change.'),
          'especialista': T('Três armadilhas desta montagem. Primeira: o limite de confiança é do modelo de embeddings, não universal. Os cossenos do multilingual-e5 ficam concentrados numa faixa alta e estreita (o cartão do modelo diz que é esperado, e que importa a ordem, não o valor absoluto), então o limite se calibra com perguntas reais dentro e fora do escopo, e se recalibra ao trocar de modelo. Na simulação, o intervalo que funciona é estreito de propósito: acima dele o assistente recusa o que o manual responde, abaixo dele inventa.\nSegunda: a triagem por lista de gatilhos é barata e previsível, mas erra nos dois sentidos (falso positivo manda "processo de reembolso" para uma pessoa; falso negativo deixa passar um assédio sem a palavra). Em produção, combine regra com classificador, meça a taxa de erro nos dois lados e prefira errar para o lado do humano nos temas de risco. Terceira: 13 perguntas são um teste de fumaça, não um conjunto de avaliação; use dezenas ou centenas, separe uma parte para calibrar e outra para medir, e avalie a fidelidade da resposta ao trecho citado (juiz LLM ou humano), porque [n] válido não prova que a frase está sustentada. Registre recusas e encaminhamentos: eles dizem o que falta no manual e quais temas precisam de um fluxo humano melhor, e tratam dados pessoais, então defina quem pode ler esse log.',
                            'Three traps in this setup. First: the confidence threshold belongs to the embedding model, it isn’t universal. multilingual-e5 cosines sit in a high, narrow band (the model card says that’s expected and that rank matters, not the absolute value), so you calibrate the threshold with real in-scope and out-of-scope questions, and recalibrate when you change the model. In the simulation the working range is narrow on purpose: above it the assistant refuses what the handbook answers, below it, it invents.\nSecond: triage by trigger list is cheap and predictable, but it errs both ways (a false positive sends "expense claim process" to a person; a false negative lets harassment through without the keyword). In production, combine rules with a classifier, measure the error rate on both sides and prefer erring toward the human on risky topics. Third: 13 questions are a smoke test, not an evaluation set; use tens or hundreds, hold one part out for calibrating and another for measuring, and evaluate faithfulness of the answer to the cited chunk (LLM judge or human), because a valid [n] doesn’t prove the sentence is supported. Log refusals and handoffs: they show what’s missing from the handbook and which topics need a better human flow, and they hold personal data, so decide who may read that log.')},
  'success': T('Missão cumprida! O assistente respondeu {nCorrect} das {nAns} perguntas do manual com [n] de um trecho que as sustenta (recall@{k} de {recPct}%), recusou as {nOut} que o manual não cobre sem recusar nenhuma que cobre (confiança mínima de {limitPct}%), passou assédio e salário para uma pessoa e indexou um manual limpo. A Aurora já pode abrir o assistente. Falta o que nenhum teste de 13 perguntas mostra: perguntas reais, dezenas delas, e alguém lendo o log de recusas.',
               'Mission accomplished! The assistant answered {nCorrect} of the {nAns} handbook questions with an [n] from a chunk that supports them (recall@{k} of {recPct}%), refused the {nOut} the handbook doesn’t cover without refusing any it does (minimum confidence {limitPct}%), handed harassment and salary to a person and indexed a clean handbook. Aurora can open the assistant. What’s left is what no 13-question test shows: real questions, dozens of them, and someone reading the refusal log.'),
  'hints': {'ui': T(['Comece pelos critérios vermelhos: cada um diz o porquê. A tabela mostra o que o assistente fez com cada pergunta.', 'Olhe a coluna de confiança: o limite fica acima da maior confiança das perguntas fora do manual e abaixo da menor das perguntas que o manual responde. E repare que a busca que pega sinônimo e sigla precisa de palavra e vetor juntos, com mais de um trecho.', 'Ligue tudo: limpar, busca híbrida, k 3, limite 78%, citar, recusar e triagem.'],
                    ['Start with the red criteria: each says why. The table shows what the assistant did with each question.', 'Look at the confidence column: the threshold sits above the highest confidence of the outside-the-handbook questions and below the lowest of those the handbook answers. And note that search that catches synonyms and acronyms needs words and vectors together, with more than one chunk.', 'Turn everything on: clean, hybrid search, k 3, threshold 78%, cite, refuse and triage.']),
            'cmd': T(['O texto vai entre aspas; --limpar, --citar, --recusar e --triagem aceitam sim ou nao.', '--modo aceita palavra, vetor ou hibrida; --k vai de 1 a 6; --limite vai de 0 a 0,99.', cmd_fixed],
                     ['The text goes in quotes; --clean, --cite, --refuse and --triage take yes or no.', '--mode takes keyword, vector or hybrid; --k goes from 1 to 6; --threshold goes from 0 to 0.99.', cmd_fixed])},
  'errors': {'notBool.clean': T('Use sim ou nao.', 'Use yes or no.'), 'notBool.cite': T('Use sim ou nao.', 'Use yes or no.'),
             'notBool.refuse': T('Use sim ou nao.', 'Use yes or no.'), 'notBool.triage': T('Use sim ou nao.', 'Use yes or no.'),
             'notInEnum.mode': T('Use palavra, vetor ou hibrida.', 'Use keyword, vector or hybrid.'),
             'belowMin.k': T('Pelo menos 1 trecho; com zero o modelo responde no escuro.', 'At least 1 chunk; with zero the model answers in the dark.'),
             'aboveMax.k': T('Até 6 trechos: mais que isso o contexto fica caro e cheio de ruído.', 'Up to 6 chunks: beyond that the context gets expensive and noisy.'),
             'belowMin.limit': T('A confiança não fica negativa. 0 desliga o limite (e é um dos problemas).', 'Confidence can’t be negative. 0 turns the threshold off (and that’s one of the problems).'),
             'aboveMax.limit': T('Até 0,99: acima disso nenhuma pergunta passa e o assistente recusa tudo.', 'Up to 0.99: above that no question passes and the assistant refuses everything.')},
  'controls': {'arg': T('Nome do assistente', 'Assistant name'), 'clean': T('Limpar o PDF antes de indexar', 'Clean the PDF before indexing'),
               'mode': T('Tipo de busca', 'Search type'), 'k': T('Trechos enviados ao modelo (k)', 'Chunks sent to the model (k)'),
               'limit': T('Confiança mínima para responder', 'Minimum confidence to answer'), 'cite': T('Citar [n] em cada resposta', 'Cite [n] in every answer'),
               'refuse': T('Frase de recusa quando não sabe', 'Refusal sentence when it doesn’t know'), 'triage': T('Passar assunto delicado para uma pessoa', 'Hand delicate topics to a person')},
  'scene': {'label': T('Assistente de RH da Aurora', 'Aurora’s HR assistant'), 'empty': T('Rode para avaliar o assistente.', 'Run to evaluate the assistant.'),
    'trackDone': T('Você concluiu a trilha Prática de IA aplicada.', 'You completed the Applied AI Practice track.'),
    'pipeline': T('A montagem', 'The setup'), 'sIngest': T('Ingestão', 'Ingestion'), 'sSearch': T('Busca', 'Search'), 'sGate': T('Limite', 'Threshold'), 'sAnswer': T('Resposta', 'Answer'), 'sTriage': T('Triagem', 'Triage'),
    'subClean': T('12 trechos limpos', '12 clean chunks'), 'subDirty': T('14 trechos, com lixo', '14 chunks, with junk'),
    'subKeyword': T('só palavra', 'words only'), 'subVector': T('só vetor, top-{k}', 'vector only, top-{k}'), 'subHybrid': T('híbrida, top-{k}', 'hybrid, top-{k}'),
    'subNoGate': T('sem limite', 'no threshold'), 'subNoCite': T('sem fonte', 'no source'), 'subRefuse': T('recusa', 'refusal'), 'subCite': '[n]', 'subCiteRefuse': T('[n] + recusa', '[n] + refusal'), 'subNoCiteRefuse': T('sem fonte + recusa', 'no source + refusal'),
    'subTriageOn': T('delicado → pessoa', 'delicate → person'), 'subTriageOff': T('desligada', 'off'),
    'checks': T('Critérios da missão', 'Mission criteria'),
    'cRecall': T('A busca traz o trecho certo (recall@k de pelo menos 80%)', 'Search brings the right chunk (recall@k of at least 80%)'),
    'cRecallWhy': T('recall@{k} de {recPct}%: a busca não está trazendo os trechos que respondem', 'recall@{k} of {recPct}%: search isn’t bringing the chunks that answer'),
    'cAnswers': T('As 9 perguntas do manual recebem a resposta certa', 'The 9 handbook questions get the right answer'),
    'cAnswersWhyRef': T('{nCorrect} de {nAns} certas: o limite de {limitPct}% está alto e recusou {nFalseRef} pergunta(s) que o manual responde', '{nCorrect} of {nAns} right: the {limitPct}% threshold is too high and refused {nFalseRef} question(s) the handbook answers'),
    'cAnswersWhyRet': T('{nCorrect} de {nAns} certas: com k = {k} e esta busca, nem todos os trechos que a resposta pede chegaram ao modelo', '{nCorrect} of {nAns} right: with k = {k} and this search, not every chunk the answer needs reached the model'),
    'cAnswersWhyDirty': T('a cópia duplicada no índice sujo ocupou uma vaga do top-{k}', 'the duplicate in the dirty index took a top-{k} slot'),
    'cCite': T('Toda resposta traz [n] de um trecho que a sustenta', 'Every answer carries an [n] from a chunk that supports it'),
    'cCiteWhyOff': T('sem [n], ninguém consegue conferir de onde veio a resposta', 'with no [n], nobody can check where the answer came from'),
    'cCiteWhyBad': T('{nCiteBad} resposta(s) citam um trecho que não responde: a busca pôs o trecho errado em primeiro', '{nCiteBad} answer(s) cite a chunk that doesn’t answer: search ranked the wrong chunk first'),
    'cRefuse': T('Recusa o que o manual não cobre, sem recusar o que cobre', 'Refuses what the handbook doesn’t cover, without refusing what it does'),
    'cRefuseWhyOff': T('sem a frase de recusa, o assistente inventa uma resposta para o que está fora do manual', 'with no refusal sentence, the assistant makes up an answer for what’s outside the handbook'),
    'cRefuseWhyHigh': T('o limite de {limitPct}% está alto: {nFalseRef} pergunta(s) do manual foram recusadas', 'the {limitPct}% threshold is too high: {nFalseRef} handbook question(s) were refused'),
    'cRefuseWhyLow': T('o limite de {limitPct}% está baixo: só {nOutRef} das {nOut} perguntas fora do manual foram recusadas', 'the {limitPct}% threshold is too low: only {nOutRef} of the {nOut} outside questions were refused'),
    'cTriage': T('Assédio e contestação de salário vão para uma pessoa', 'Harassment and salary disputes go to a person'),
    'cTriageWhy': T('sem triagem, o assistente trata esses casos como dúvida de manual (ou só recusa) e ninguém do RH fica sabendo', 'with no triage, the assistant treats these cases as handbook questions (or just refuses) and nobody in HR finds out'),
    'cClean': T('O índice não tem duplicata, cabeçalho nem palavra quebrada', 'The index has no duplicate, header or broken word'),
    'cCleanWhy': T('o PDF sujo trouxe 2 trechos a mais (uma cópia e um cabeçalho de página) e "ante- cedência" partida no meio', 'the dirty PDF brought 2 extra chunks (a copy and a page header) and "ad- vance" split in the middle'),
    'mRecall': T('recall@k nas 9 do manual', 'recall@k on the 9 handbook questions'), 'mAnswers': T('respostas certas', 'right answers'),
    'mRefusals': T('recusas certas (fora do manual)', 'right refusals (outside)'), 'mRouted': T('passadas a uma pessoa', 'handed to a person'),
    'table': T('O que o assistente fez com cada pergunta', 'What the assistant did with each question'),
    'colQ': T('pergunta', 'question'), 'colExp': T('o certo seria', 'it should'), 'colConf': T('confiança', 'confidence'), 'colRes': T('o que fez', 'what it did'),
    'tableCaption': T('confiança = similaridade do melhor trecho no vetor (a coluna que o limite compara); perguntas delicadas não passam pelo limite, porque a triagem vem antes da busca (—)', 'confidence = vector similarity of the best chunk (the column the threshold compares); delicate questions skip the threshold because triage comes before search (—)'),
    'eAns': T('responder com [n]', 'answer with [n]'), 'eOut': T('recusar', 'refuse'), 'eSens': T('passar para uma pessoa', 'hand to a person'),
    'xAnsOk': T('respondeu certo', 'answered right'), 'xAnsWrong': T('respondeu errado ou incompleto', 'answered wrong or incomplete'), 'xAnsRefused': T('recusou, mas o manual responde', 'refused, but the handbook answers'),
    'xOutRefused': T('recusou', 'refused'), 'xOutInvented': T('inventou uma resposta', 'made up an answer'),
    'xSensRouted': T('passou para uma pessoa', 'handed to a person'), 'xSensRefused': T('só recusou: nenhuma pessoa foi avisada', 'only refused: no person was told'), 'xSensAnswered': T('respondeu sozinho', 'answered on its own'),
    'realNote': T('Busca com vetores de verdade (multilingual-e5-small, no seu navegador). A coluna de confiança e o limite continuam usando as semelhanças de referência da lição, porque a escala dos cossenos muda de modelo para modelo; no seu projeto você calibra o limite com o seu modelo. O recall e a ordem dos trechos vêm dos vetores reais, então podem diferir da simulação.',
                  'Search with real vectors (multilingual-e5-small, in your browser). The confidence column and the threshold still use the lesson’s reference similarities, because the cosine scale changes from model to model; in your project you calibrate the threshold with your own model. Recall and chunk order come from the real vectors, so they may differ from the simulation.'),
    'simNote': T('Modo simulado: semelhanças dos vetores escritas à mão (a palavra-chave é BM25 de verdade) e respostas sem LLM: a tabela mostra o desfecho de cada pergunta. Use "No navegador" para vetores reais na busca.',
                 'Simulated mode: hand-written vector similarities (keyword search is real BM25) and no LLM: the table shows each question’s outcome. Use "In the browser" for real vectors in search.')},
  'data': {'allTexts': all_texts(L), 'questions': [q[L] for q, _, _, _ in QSET], 'qShort': [x[L] for x in QSHORT], 'stop': STOP[L], 'triggers': TRIGGERS[L], 'refusal': refusal},
  'recipe': {'steps': [
     install,
     T('Crie corpus.py com o manual (os mesmos 12 trechos da simulação) e as perguntas de teste. Cada pergunta traz o tipo e os índices (começando em 0) dos trechos que a respondem:\n', 'Create corpus.py with the handbook (the same 12 chunks as the simulation) and the test questions. Each question carries its kind and the indices (starting at 0) of the chunks that answer it:\n') + corpus_code(L),
     T('Crie assistant.py. Ele faz a triagem primeiro (regex de gatilhos), busca híbrida (BM25 com rank_bm25 + embeddings do multilingual-e5-small, com os prefixos "query: " e "passage: " que esse modelo pede), recusa pelo limite sem chamar o LLM e, se passar, pede a resposta com o prompt de sistema que manda citar [n] e usar a frase de recusa:\n', 'Create assistant.py. It does triage first (a trigger regex), hybrid search (BM25 with rank_bm25 + multilingual-e5-small embeddings, with the "query: " and "passage: " prefixes that model asks for), refuses by threshold without calling the LLM and, if it passes, asks for the answer with a system prompt that says to cite [n] and use the refusal sentence:\n') + assistant_code(L),
     T('Crie run_eval.py, o laço de avaliação: roda cada pergunta, confere busca (os trechos certos estão nos K enviados?), citação ([n] aponta para um trecho certo?), recusa e encaminhamento, e imprime um resumo. Rode com python run_eval.py:\n', 'Create run_eval.py, the evaluation loop: it runs each question and checks search (are the right chunks among the K sent?), citation (does [n] point at a right chunk?), refusal and handoff, then prints a summary. Run it with python run_eval.py:\n') + eval_code(L),
     T('Calibre o limite. Olhe a confiança (conf=) impressa nas linhas "outside" e nas "answer". O cosseno do e5 fica numa faixa estreita, então o valor certo é o seu: ponha LIMIT entre a maior confiança das perguntas fora do manual e a menor das respondidas, e rode de novo, por exemplo (no PowerShell: $env:LIMIT = "0.84"; python run_eval.py):\nLIMIT=0.84 python run_eval.py\nSe uma pergunta que o manual responde virar "refuse", baixe LIMIT; se a de fora do manual for respondida, suba. Com só uma pergunta de fora no teste, adicione mais algumas a QUESTIONS antes de confiar no número.',
       'Calibrate the threshold. Look at the confidence (conf=) printed on the "outside" and the "answer" lines. e5 cosines sit in a narrow band, so the right value is yours: set LIMIT between the highest confidence among the outside-the-handbook questions and the lowest among the answered ones, and run again, for example (in PowerShell: $env:LIMIT = "0.84"; python run_eval.py):\nLIMIT=0.84 python run_eval.py\nIf a question the handbook answers turns into "refuse", lower LIMIT; if the outside question gets answered, raise it. With a single outside question in the test, add a few more to QUESTIONS before trusting the number.'),
     T('Quebre de propósito, como na missão: com K=1 a pergunta composta do reembolso (dois trechos) deixa de ser respondida por inteiro, e sem citação ou sem frase de recusa no SYSTEM o laço acusa XX:\nK=1 python run_eval.py',
       'Break it on purpose, as in the mission: with K=1 the compound expense question (two chunks) is no longer fully covered, and without the citation or refusal sentence in SYSTEM the loop shows XX:\nK=1 python run_eval.py')],
   'ok': T('o run_eval.py imprime uma linha OK ou XX para cada uma das 8 perguntas e termina com o resumo (recall, respostas, recusas e encaminhamentos) e a palavra PASSED depois que você calibra o LIMIT; com K=1 a pergunta do reembolso fica XX.',
           'run_eval.py prints one OK or XX line for each of the 8 questions and ends with the summary (recall, answers, refusals and handoffs) and the word PASSED once you have calibrated LIMIT; with K=1 the expense question turns XX.')}}

TEACHER = {'pt': {'objectives': ['Montar de ponta a ponta um assistente de RH com busca híbrida, limite de confiança, citação [n], recusa e triagem.', 'Medir o assistente com um conjunto fixo de perguntas (recall@k, respostas, recusas e encaminhamentos certos).', 'Perceber que cada defesa cobre um erro diferente e que o limite precisa ser calibrado.'], 'minutes': 30,
  'activity': 'Em grupos, cada um recebe uma configuração ruim diferente (só palavra, sem limite, sem citação, sem triagem) e descobre pelos critérios o que está errado, sem ler a dica. Depois cada grupo escreve 5 perguntas novas para a Aurora (2 que o manual responde, 1 fora do manual, 1 delicada e 1 ambígua), prevê o que o assistente faria e testa.',
  'discussion': ['Quais assuntos da sua escola ou empresa nunca deveriam ser respondidos por uma máquina, e por quê?', 'O que é pior: o assistente recusar uma pergunta que o manual responde ou responder uma que o manual não cobre?', 'Quem deve ler o log de recusas e encaminhamentos, e o que ele guarda?'],
  'misconceptions': ['"Se o assistente cita [n], a resposta está certa." A citação só diz de onde veio; a frase pode não estar sustentada pelo trecho.', '"Um limite de confiança serve para qualquer modelo." Ele é calibrado para um modelo de embeddings e perguntas reais.', '"Se passou nas 13 perguntas, está pronto." É um teste de fumaça; falta volume, perguntas reais e avaliação da fidelidade.']},
 'en': {'objectives': ['Build an HR assistant end to end with hybrid search, a confidence threshold, [n] citation, refusal and triage.', 'Measure the assistant with a fixed question set (recall@k, right answers, refusals and handoffs).', 'See that each defense covers a different mistake and that the threshold must be calibrated.'], 'minutes': 30,
  'activity': 'In groups, each gets a different bad setup (words only, no threshold, no citation, no triage) and finds what is wrong from the criteria alone, without reading the hints. Then each group writes 5 new questions for Aurora (2 the handbook answers, 1 outside it, 1 delicate and 1 ambiguous), predicts what the assistant would do and tests it.',
  'discussion': ['Which topics at your school or company should never be answered by a machine, and why?', 'Which is worse: the assistant refusing a question the handbook answers or answering one the handbook doesn’t cover?', 'Who should read the log of refusals and handoffs, and what does it hold?'],
  'misconceptions': ['"If the assistant cites [n], the answer is right." The citation only says where it came from; the sentence may not be supported by the chunk.', '"A confidence threshold works for any model." It is calibrated for one embedding model and real questions.', '"If it passed the 13 questions, it’s ready." It’s a smoke test; it lacks volume, real questions and a faithfulness evaluation.']}}

REAL = {'no-navegador': {'adapter': 'declarative', 'model': 'Xenova/multilingual-e5-small', 'op': 'embedmatrix',
        'args': {'queries': 'questions', 'against': 'allTexts', 'queryPrefix': 'query: ', 'passagePrefix': 'passage: '}}}

if __name__ == '__main__':
    from common import write as _write, step as _step
    s = _step('p-missao-assistente-de-rh', 23, 'pratica', 30, ['missao', 'rag', 'assistente-de-rh', 'citacao', 'recusa', 'triagem', 'avaliacao'],
              [last_p3_id(), 'p-avaliar-recuperacao'], ['simulado', 'no-navegador'], loc('montar', 'build'),
              {'name': 'text', 'required': False, 'ui': 'text', 'default': loc('assistente-rh', 'hr-assistant')},
              flags_def(), None, 'passed', sim_full(), REAL, kind='mission')
    _write('ia-aplicada', 'pratica', '23-missao-assistente-de-rh', s, locale('pt'), locale('en'), TEACHER)
    print('ok: ia-aplicada/pratica/23-missao-assistente-de-rh')
