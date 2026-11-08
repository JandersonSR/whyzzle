"""R2 · 13 · auditoria e rastreabilidade."""
import json
from r2_common import *

I1 = LQ('Por que o assistente disse que dá para vender metade das férias?', 'Why did the assistant say you can sell half of your vacation?')
I2 = LQ('Quem viu a tabela salarial da diretoria na semana passada?', 'Who saw the executive salary table last week?')
I3 = LQ('Quanto o assistente custou na quarta?', 'How much did the assistant cost on Wednesday?')
I4 = LQ('O assistente barrou a tentativa de injeção de ontem?', 'Did the assistant block yesterday’s injection attempt?')

FIELDS = ['ts', 'user', 'prompt_v', 'model', 'docs', 'guard', 'tokens']
ALL = FIELDS + ['text']
NEED = {I1['pt']: ['ts', 'prompt_v', 'model', 'docs', 'text'], I2['pt']: ['ts', 'user', 'docs'], I3['pt']: ['ts', 'tokens'], I4['pt']: ['ts', 'guard', 'text']}
READERS = 12                              # pessoas com acesso de leitura ao log (lição)
PII_WEEK = round(WEEKLY * 21 / 100)       # conversas por semana com CPF, e-mail, telefone ou saúde (lição 11)
assert PII_WEEK == 420

s = step('r-auditoria-e-rastreabilidade', 13, 20, ['governanca', 'auditoria', 'logs', 'lgpd', 'rastreabilidade'],
 ['r-jailbreak-e-red-teaming'], ['simulado'], LQ('auditar', 'audit'),
 {'name': 'text', 'required': False, 'ui': 'examples', 'default': I1, 'examples': ex(I1, I2, I3, I4)},
 [flag('fields', 'campos', 'fields', 'list', options=[opt('ts', 'quando', 'when'), opt('user', 'quem', 'who'), opt('prompt_v', 'prompt', 'prompt'), opt('model', 'modelo', 'model'),
                                                     opt('docs', 'docs', 'docs'), opt('guard', 'guardrails', 'guards'), opt('tokens', 'tokens', 'tokens')], default=FIELDS, ui='checkboxes'),
  flag('body', 'texto', 'content', 'enum', options=[opt('none', 'nenhum', 'none'), opt('redacted', 'redigido', 'redacted'), opt('raw', 'bruto', 'raw')], default='redacted', ui='select'),
  flag('integrity', 'integridade', 'integrity', 'enum', options=[opt('plain', 'comum', 'plain'), opt('chain', 'encadeado', 'chain')], default='chain', ui='select')],
 {'options': ['yes', 'no'], 'answer': 'no'}, 'overlog',
 {'live': False,
  'consts': {'allIds': ALL, 'readers': READERS, 'piiWeek': PII_WEEK, 'toneMap': {'0': 'dim', '1': 'dim', '2': 'bad', '3': 'ok'}},
  'compute': {
   'rec': 'lookup(incidents, text, unknownInc)',
   'known': 'rec.known',
   'need': 'rec.need',
   'have': "concat(fields, body != 'none' ? ['text'] : [])",
   'haveMask': 'memberall(need, have)',
   'nMissing': 'len(need) - sum(haveMask)',
   'answerable': 'nMissing == 0',
   'missingIds': 'maskfilter(need, affine(haveMask, 1, -1))',
   'missingNames': "join(lookupall(fieldNames, missingIds), ', ')",
   'loggedArr': 'memberall(allIds, have)',
   'neededArr': 'memberall(allIds, need)',
   'tonesKey': 'addall(scale(neededArr, 2), loggedArr)',
   'rowTones': 'lookupall(toneMap, tonesKey)',
   'loggedCol': 'lookupall(yesNoL, loggedArr)',
   'neededCol': 'lookupall(yesNoL, neededArr)',
   'nFields': 'sum(loggedArr)',
   'piiNow': "body == 'raw' ? piiWeek : 0",
   'verifyLines': "integrity == 'chain' ? chainLines : plainLines"},
  'cases': [
   {'when': '!known', 'error': 'unknownInc'},
   {'when': "body == 'raw'", 'flags': ['overlog']},
   {'when': 'answerable', 'flags': ['traceable']},
   {'when': '!answerable', 'flags': ['gap']},
   {'when': "integrity == 'plain'", 'flags': ['forgeable']},
   {'when': "integrity == 'chain'", 'flags': ['sealed']},
   {'when': 'true', 'vars': {'piiNow': 'piiNow', 'readers': 'readers', 'nMissing': 'nMissing', 'missingNames': 'missingNames', 'nFields': 'nFields'}}],
  'widgets': [
   {'type': 'flow', 'label': '@flowLabel', 'steps': [
     {'label': '@sQuestion', 'sub': '=text', 'tone': 'info'},
     {'label': '@sNeeds', 'sub': '@subNeeds', 'tone': 'neutral'},
     {'label': '@sAnswer', 'sub': "=answerable ? '@subYes' : '@subNo'", 'tone': "=answerable ? 'ok' : 'bad'"}]},
   {'type': 'table', 'label': '@tableLabel', 'columns': ['@colField', '@colLogged', '@colNeeded', '@colUse'], 'rows': '=zip(fieldLabels, loggedCol, neededCol, fieldUse)', 'tones': '=rowTones', 'caption': '@tableCaption'},
   {'type': 'terminal', 'label': '@verifyLabel', 'lines': '=verifyLines'},
   {'type': 'metrics', 'items': [
     {'label': '@mFields', 'value': "=nFields + ' / 8'", 'tone': 'info'},
     {'label': '@mPii', 'value': '=piiNow', 'format': 'int', 'tone': "=piiNow > 0 ? 'bad' : 'ok'"}]},
   {'type': 'checks', 'items': [{'label': '@chkAnswer', 'ok': '=answerable', 'why': '@whyAnswer'}, {'label': '@chkRaw', 'ok': "=body != 'raw'", 'why': '@whyRaw'}, {'label': '@chkChain', 'ok': "=integrity == 'chain'", 'why': '@whyChain'}]},
   {'type': 'note', 'when': '=!answerable', 'tone': 'warn', 'text': '@gapNote'},
   {'type': 'note', 'when': "=body == 'raw'", 'tone': 'bad', 'text': '@rawNote'},
   {'type': 'note', 'when': '=true', 'tone': 'info', 'text': '@simNote'}]})

AUDIT_PY = '''import hashlib
import json
import pathlib
import time
import uuid

LOG = pathlib.Path("audit.jsonl")


def _hash(prev, record):
    body = json.dumps(record, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256((prev + body).encode("utf-8")).hexdigest()


def _last_hash():
    if not LOG.exists():
        return "0" * 64
    lines = LOG.read_text(encoding="utf-8").splitlines()
    return json.loads(lines[-1])["hash"] if lines else "0" * 64


def write_event(user_code, prompt_v, model, docs, guards, tokens, question, answer):
    """Um evento por resposta. question e answer chegam JÁ redigidos (veja a lição de LGPD)."""
    record = {
        "id": str(uuid.uuid4()),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "user": user_code,            # pseudônimo, nunca o nome
        "prompt_v": prompt_v,         # ex.: "rh-v3"
        "model": model,               # ex.: "claude-sonnet-5-5"
        "docs": docs,                 # ids (e versões) dos documentos que entraram no contexto
        "guards": guards,             # ex.: {"input": "allow", "output": "allow"}
        "tokens": tokens,             # {"in": 812, "out": 96}
        "question": question,
        "answer": answer,
        "prev": _last_hash(),
    }
    record["hash"] = _hash(record["prev"], {k: v for k, v in record.items() if k != "hash"})
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\\n")
    return record["id"]


def verify():
    """Devolve None se a cadeia está íntegra, ou o número da primeira linha adulterada."""
    prev = "0" * 64
    for n, line in enumerate(LOG.read_text(encoding="utf-8").splitlines(), start=1):
        record = json.loads(line)
        body = {k: v for k, v in record.items() if k != "hash"}
        if record["prev"] != prev or record["hash"] != _hash(prev, body):
            return n
        prev = record["hash"]
    return None'''

AUDIT_TEST = '''if __name__ == "__main__":
    pathlib.Path("audit.jsonl").unlink(missing_ok=True)
    for i in range(3):
        write_event("u-9f3a", "rh-v3", "claude-sonnet-5-5", ["manual-ferias@2026-10"], {"input": "allow", "output": "allow"},
                    {"in": 800 + i, "out": 90}, @Q, @A)
    print("cadeia íntegra?", verify() is None)
    lines = LOG.read_text(encoding="utf-8").splitlines()
    lines[1] = lines[1].replace("@OLD", "@NEW")        # alguém "arruma" a evidência
    LOG.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    print("primeira linha adulterada:", verify())'''


def loc(L):
    pt = L == 'pt'; T = lambda a, b: a if pt else b
    cheat = T('auditar --texto bruto', 'audit --content raw')
    names = {'ts': T('quando', 'when'), 'user': T('quem (pseudônimo)', 'who (pseudonym)'), 'prompt_v': T('versão do prompt', 'prompt version'), 'model': T('modelo', 'model'), 'docs': T('documentos no contexto', 'documents in context'),
             'guard': T('decisões dos guardrails', 'guardrail decisions'), 'tokens': T('tokens e custo', 'tokens and cost'), 'text': T('texto da conversa', 'conversation text')}
    use = [T('ordenar e filtrar', 'sort and filter'), T('quem fez a pergunta', 'who asked'), T('reproduzir a resposta', 'reproduce the answer'), T('reproduzir a resposta', 'reproduce the answer'), T('o que a resposta usou', 'what the answer used'),
           T('o que foi barrado', 'what was blocked'), T('custo e abuso', 'cost and abuse'), T('o que foi dito', 'what was said')]
    inc = lambda e: {'known': True, 'need': NEED[e['pt']]}
    chain = [T('$ python verify_chain.py audit-2026-W45.jsonl', '$ python verify_chain.py audit-2026-W45.jsonl'), T('+ 412 linhas, cadeia de hashes íntegra', '+ 412 lines, hash chain intact'),
             T('$ editar a linha 207 (teste de adulteração)', '$ edit line 207 (tampering test)'), T('! o hash da linha 207 não confere: adulteração detectada', '! line 207 hash does not match: tampering detected')]
    plain = [T('$ wc -l audit-2026-W45.jsonl', '$ wc -l audit-2026-W45.jsonl'), T('~ 412 linhas', '~ 412 lines'), T('? nada prova que a linha 207 não foi editada depois', '? nothing proves line 207 was not edited afterwards')]
    return {
  'title': T('Auditoria e rastreabilidade', 'Audit and traceability'),
  'subtitle': T('Registrar o suficiente para reconstruir o que o assistente fez, sem que o registro vire um novo problema', 'Record enough to reconstruct what the assistant did, without the record becoming a new problem'),
  'mission': T('Numa quinta, uma pessoa afirma que o assistente disse que dava para vender metade das férias. Para investigar, o time precisa reconstruir aquela resposta: quando foi, que versão do prompt e que modelo estavam no ar, que documentos entraram no contexto. A trilha de auditoria da Aurora registra um evento por resposta. Escolha os campos, o que fazer com o texto da conversa e como proteger o arquivo contra edição, e veja que perguntas de incidente a trilha consegue responder.',
               'On a Thursday, a person claims the assistant said you could sell half of your vacation. To investigate, the team must reconstruct that answer: when it was, which prompt version and model were live, which documents entered the context. Aurora’s audit trail records one event per answer. Choose the fields, what to do with the conversation text and how to protect the file against editing, and see which incident questions the trail can answer.'),
  'predict': {'question': T('para ser completa, a trilha deveria guardar o texto bruto de cada conversa, com tudo que a pessoa digitou?', 'to be complete, should the trail keep the raw text of every conversation, with everything the person typed?'),
              'options': {'yes': T('Sim: sem o texto bruto não há auditoria', 'Yes: without raw text there is no audit'), 'no': T('Não: o redigido basta e o bruto vira outro risco', 'No: redacted is enough and raw becomes another risk')}},
  'feedback': {'right': T('isso: o texto redigido responde às perguntas de incidente, e o bruto guardaria cerca de 420 conversas por semana com CPF, e-mail, telefone ou saúde, legíveis por quem tem acesso ao log. A auditoria não pode virar vazamento.',
                          'right: redacted text answers the incident questions, and raw would keep about 420 conversations a week with CPF, e-mail, phone or health data, readable by whoever has log access. The audit must not become a leak.'),
               'wrong': T('não: o texto redigido responde às perguntas de incidente, e o bruto guardaria cerca de 420 conversas por semana com CPF, e-mail, telefone ou saúde, legíveis por quem tem acesso ao log. A auditoria não pode virar vazamento.',
                          'no: redacted text answers the incident questions, and raw would keep about 420 conversations a week with CPF, e-mail, phone or health data, readable by whoever has log access. The audit must not become a leak.'),
               'skipped': T('sem palpite? Rode com o texto redigido e depois com o bruto e compare a coluna de dados pessoais.', 'no guess? Run with redacted text and then with raw and compare the personal data metric.')},
  'coach': {'ui': T('palpite anotado. Rode com a trilha padrão (todos os campos, texto redigido, hash encadeado) e leia a tabela.', 'guess noted. Run with the default trail (all fields, redacted text, hash chain) and read the table.'),
            'cmd': T('palpite anotado. Rode auditar e leia a tabela de campos.', 'guess noted. Run audit and read the field table.')},
  'tryNext': {'ui': T('Agora pergunte quem viu a tabela salarial e registre só quando e documentos: sem "quem", a trilha não responde.', 'Now ask who saw the salary table and record only when and documents: without "who", the trail cannot answer.'),
              'cmd': T(f'Rode auditar "{I2[L]}" --campos quando,docs e veja o campo que falta.', f'Run audit "{I2[L]}" --fields when,docs and see the missing field.')},
  'why': {'simples': T('Uma trilha de auditoria é a caixa-preta do avião: não evita o acidente, mas permite descobrir o que aconteceu e consertar. Para isso ela precisa guardar o suficiente (quem, quando, o que foi usado) e estar protegida contra edição, senão qualquer um "arruma" a história depois.\nE tem a outra ponta: se a caixa-preta grava tudo que todo passageiro disse, inclusive o que era íntimo, ela mesma vira um perigo. A regra é registrar o que explica a decisão, não o que for possível.',
                       'An audit trail is the airplane’s black box: it does not prevent the accident, but it lets you find out what happened and fix it. For that it must keep enough (who, when, what was used) and be protected against editing, otherwise anyone "tidies up" the story afterwards.\nAnd there is the other end: if the black box records everything every passenger said, including what was private, it becomes a danger itself. The rule is to record what explains the decision, not whatever is possible.'),
          'dev': T('Um evento por resposta, em JSON, com campos fixos: id, data e hora, código do usuário (pseudônimo), versão do prompt, id do modelo (como claude-sonnet-5-5), ids e versões dos documentos que entraram no contexto, decisões de cada guardrail, tokens e custo, e a pergunta e a resposta já redigidas. Com isso se reconstrói uma resposta: mesmo prompt, mesmos documentos, mesmo modelo. Sem a versão do prompt e dos documentos, não dá para reproduzir; sem o usuário, não se responde "quem viu isso"; sem as decisões dos guardrails, não se prova que o ataque foi barrado.\nIntegridade: encadeie os eventos com hash (cada linha guarda o hash da anterior). Editar uma linha quebra a cadeia dali em diante. Quem controla o arquivo ainda pode recalcular tudo, então publique o hash mais recente num sistema separado, de tempos em tempos, e grave em armazenamento só de acréscimo quando o provedor oferecer.\nPrivacidade: texto redigido (lição anterior), acesso por papel com registro de quem leu o log, prazo de retenção e identificação por pseudônimo, para atender a pedidos de uma pessoa. Se o log também alimenta o conjunto de avaliação, redija antes de copiar.',
                   'One event per answer, in JSON, with fixed fields: id, date and time, user code (pseudonym), prompt version, model id (such as claude-sonnet-5-5), ids and versions of the documents that entered the context, each guardrail’s decisions, tokens and cost, and the already redacted question and answer. With that you reconstruct an answer: same prompt, same documents, same model. Without the prompt and document versions, you cannot reproduce it; without the user, you cannot answer "who saw this"; without the guardrail decisions, you cannot prove the attack was blocked.\nIntegrity: chain the events with a hash (each line stores the previous line’s hash). Editing a line breaks the chain from there on. Whoever controls the file can still recompute everything, so publish the latest hash on a separate system from time to time, and write to append-only storage when the provider offers it.\nPrivacy: redacted text (previous lesson), role-based access with a record of who read the log, a retention period and pseudonym identification, to handle one person’s requests. If the log also feeds the evaluation set, redact before copying.'),
          'especialista': T('Registro e prestação de contas aparecem na lei e nos modelos de gestão. Na LGPD, o art. 37 manda controlador e operador manter registro das operações de tratamento de dados pessoais, o art. 6º, X, pede responsabilização e prestação de contas (demonstrar medidas eficazes) e o art. 48 exige comunicar incidentes de segurança à ANPD e ao titular; pela Resolução CD/ANPD nº 15/2024, o prazo é de três dias úteis do conhecimento do incidente, e sem trilha você não consegue dizer em três dias quem foi afetado. O art. 20 dá ao titular o direito de pedir revisão de decisões tomadas unicamente com base em tratamento automatizado, o que exige conseguir explicar como a decisão foi produzida.\nO NIST AI RMF 1.0 (janeiro de 2023) organiza o gerenciamento de risco de IA em quatro funções, Govern, Map, Measure e Manage, e o perfil de IA generativa NIST AI 600-1 (julho de 2024) aplica isso a 12 riscos. A ISO/IEC 42001:2023, publicada em dezembro de 2023, define requisitos para um sistema de gestão de IA numa organização. Em qualquer auditoria baseada nesse tipo de referência, os registros do que o sistema fez são a evidência natural.\nO equilíbrio é difícil: a trilha precisa de detalhe para provar algo e de contenção para não ser um segundo repositório de dados pessoais. Decida, por escrito, quem pode ler a trilha, por quanto tempo ela fica e o que é redigido, e revise com o encarregado.',
                            'Recording and accountability show up in the law and in management frameworks. In LGPD, art. 37 requires controller and operator to keep a record of personal data processing operations, art. 6, X asks for accountability (showing effective measures) and art. 48 requires notifying security incidents to the ANPD and the data subject; under Resolution CD/ANPD 15/2024, the deadline is three business days from knowing about the incident, and without a trail you cannot say in three days who was affected. Art. 20 gives data subjects the right to request review of decisions made solely on automated processing, which requires being able to explain how the decision was produced.\nNIST AI RMF 1.0 (January 2023) organizes AI risk management in four functions, Govern, Map, Measure and Manage, and the generative AI profile NIST AI 600-1 (July 2024) applies it to 12 risks. ISO/IEC 42001:2023, published in December 2023, defines requirements for an AI management system in an organization. In any audit based on this kind of reference, records of what the system did are the natural evidence.\nThe balance is hard: the trail needs detail to prove something and restraint not to be a second repository of personal data. Decide, in writing, who may read the trail, for how long it stays and what is redacted, and review it with the data protection officer.')},
  'break': {'mission': {'ui': T('hora de quebrar: grave o texto bruto das conversas na trilha.', 'time to break it: record the raw conversation text in the trail.'),
                        'cmd': T(f'hora de quebrar: rode {cheat}', f'time to break it: run {cheat}')},
            'success': T('Quebrou: com o texto bruto, a trilha passa a guardar cerca de {piiNow} conversas por semana com CPF, e-mail, telefone ou dado de saúde, legíveis por {readers} pessoas com acesso ao log. A trilha de auditoria virou um novo vazamento à espera de acontecer.',
                         'Broken: with raw text, the trail starts keeping about {piiNow} conversations a week with CPF, e-mail, phone or health data, readable by {readers} people with log access. The audit trail became a new leak waiting to happen.'),
            'calm': T('A trilha tem {nFields} de 8 campos e {piiNow} conversas por semana com dado pessoal bruto. Para quebrar, grave o texto bruto.',
                      'The trail has {nFields} of 8 fields and {piiNow} conversations a week with raw personal data. To break it, record the raw text.')},
  'hints': {'ui': T(['Marque os campos, escolha o tratamento do texto e a proteção do arquivo, e rode para ver se a pergunta tem resposta.', 'Linhas vermelhas são campos de que a pergunta precisa e que você não registrou. O texto bruto responde tudo, mas guarda dado pessoal.', 'Texto da conversa: bruto.'],
                    ['Check the fields, choose the text handling and the file protection, and run to see whether the question has an answer.', 'Red rows are fields the question needs and you did not record. Raw text answers everything, but keeps personal data.', 'Conversation text: raw.']),
            'cmd': T(['A pergunta do incidente vai entre aspas, depois de auditar.', '--campos quando,quem,prompt,modelo,docs,guardrails,tokens; --texto nenhum, redigido ou bruto; --integridade comum ou encadeado.', cheat],
                     ['The incident question goes in quotes, after audit.', '--fields when,who,prompt,model,docs,guards,tokens; --content none, redacted or raw; --integrity plain or chain.', cheat])},
  'errors': {'notInEnum.fields': T('"{value}" não é um campo. Use: {options}.', '"{value}" is not a field. Use: {options}.'),
             'notInEnum.body': T('"{value}" não é um tratamento. Use: {options}.', '"{value}" is not a handling. Use: {options}.'),
             'notInEnum.integrity': T('"{value}" não é uma proteção. Use: {options}.', '"{value}" is not a protection. Use: {options}.'),
             'model.unknownInc': T('Use uma das quatro perguntas de incidente de exemplo.', 'Use one of the four example incident questions.')},
  'controls': {'arg': T('Pergunta do incidente', 'Incident question'), 'fields': T('Campos registrados', 'Recorded fields'), 'body': T('Texto da conversa', 'Conversation text'), 'integrity': T('Proteção do arquivo', 'File protection')},
  'scene': {'flowLabel': T('Da pergunta à resposta da auditoria', 'From question to audit answer'), 'sQuestion': T('Pergunta', 'Question'), 'sNeeds': T('Precisa de', 'Needs'), 'subNeeds': T('os campos marcados em azul ou vermelho na tabela', 'the fields marked in the table'), 'sAnswer': T('A trilha responde?', 'Can the trail answer?'),
    'subYes': T('sim, dá para reconstruir', 'yes, it can be reconstructed'), 'subNo': T('não: faltam {nMissing} campo(s) ({missingNames})', 'no: {nMissing} field(s) missing ({missingNames})'),
    'tableLabel': T('Campos do evento de auditoria', 'Audit event fields'), 'colField': T('campo', 'field'), 'colLogged': T('registrado', 'recorded'), 'colNeeded': T('a pergunta precisa', 'question needs'), 'colUse': T('serve para', 'used for'),
    'tableCaption': T('vermelho: a pergunta precisa e você não registrou', 'red: the question needs it and you did not record it'),
    'verifyLabel': T('Verificação da integridade', 'Integrity check'),
    'mFields': T('campos registrados', 'fields recorded'), 'mPii': T('conversas por semana com dado pessoal bruto', 'conversations a week with raw personal data'),
    'chkAnswer': T('A pergunta do incidente tem resposta', 'The incident question has an answer'), 'whyAnswer': T('Sem os campos certos, a investigação vira palpite.', 'Without the right fields, the investigation becomes guesswork.'),
    'chkRaw': T('Sem texto bruto com dado pessoal', 'No raw text with personal data'), 'whyRaw': T('Registre o que explica a decisão, não tudo que é possível (necessidade, art. 6º, III).', 'Record what explains the decision, not everything possible (necessity, art. 6, III).'),
    'chkChain': T('Arquivo à prova de adulteração', 'Tamper-evident file'), 'whyChain': T('Hash encadeado mostra se alguém editou uma linha.', 'A hash chain shows whether someone edited a line.'),
    'gapNote': T('Faltam {nMissing} campo(s): {missingNames}. Sem eles esta pergunta fica sem resposta.', '{nMissing} field(s) missing: {missingNames}. Without them this question stays unanswered.'),
    'rawNote': T('O texto bruto responde qualquer pergunta, mas guarda CPF, e-mail, telefone e saúde no log. Prefira o texto redigido.', 'Raw text answers any question, but keeps CPF, e-mail, phone and health in the log. Prefer redacted text.'),
    'simNote': T('Lição só simulada: as perguntas de incidente e os campos de que cada uma precisa são fixos, e 412 linhas e 420 conversas por semana são números da lição.', 'Simulated-only lesson: the incident questions and the fields each one needs are fixed, and 412 lines and 420 conversations a week are lesson numbers.')},
  'data': {'incidents': {e[L]: inc(e) for e in (I1, I2, I3, I4)}, 'unknownInc': {'known': False, 'need': []},
           'fieldNames': names, 'fieldLabels': [names[k] for k in ALL], 'fieldUse': use, 'yesNoL': {'1': T('sim', 'yes'), '0': T('não', 'no')}, 'chainLines': chain, 'plainLines': plain},
  'recipe': {'steps': [
     T('Defina o evento de auditoria. Um exemplo de linha de audit.jsonl (os dados vêm redigidos):\n', 'Define the audit event. An example line of audit.jsonl (data comes redacted):\n')
     + json.dumps({'id': 'a1c0…', 'ts': '2026-11-05T17:42:10Z', 'user': 'u-9f3a', 'prompt_v': 'rh-v3', 'model': MODEL_SMART, 'docs': ['manual-ferias@2026-10'], 'guards': {'input': 'allow', 'output': 'allow'}, 'tokens': {'in': 812, 'out': 96},
                   'question': I1[L], 'answer': T('Até metade das férias.', 'Up to half your vacation.'), 'prev': '0' * 8 + '…', 'hash': '5be1…'}, ensure_ascii=False, indent=2),
     T('Crie audit.py: grava um evento por resposta com hash encadeado e verifica a cadeia inteira:\n', 'Create audit.py: records one event per answer with a chained hash and verifies the whole chain:\n') + AUDIT_PY,
     T('Acrescente um teste de adulteração ao fim do arquivo e rode:\n', 'Add a tampering test to the end of the file and run it:\n') + AUDIT_TEST.replace('@Q', json.dumps(I1[L], ensure_ascii=False)).replace('@A', json.dumps(T('Até um terço das férias.', 'Up to one third of your vacation.'), ensure_ascii=False)).replace('@OLD', T('um terço', 'one third')).replace('@NEW', T('metade', 'half')) + '\npython audit.py',
     T('Chame write_event() no mesmo ponto do código em que a resposta é devolvida, com o texto já redigido. Agende uma verificação diária (verify()) e envie o último hash para um sistema separado. Defina por escrito quem lê a trilha e por quanto tempo ela fica.', 'Call write_event() at the same point in the code where the answer is returned, with the text already redacted. Schedule a daily check (verify()) and send the latest hash to a separate system. Define in writing who reads the trail and how long it stays.')],
   'ok': T('o teste imprime "cadeia íntegra? True" e depois "primeira linha adulterada: 2": a edição de uma palavra na segunda linha quebra o hash dela e o encadeamento das seguintes.',
           'the test prints "cadeia íntegra? True" and then "primeira linha adulterada: 2": editing one word in the second line breaks its hash and the chaining of the following ones.')}}


def tch():
    return teacher(
 {'objectives': ['Definir os campos de um evento de auditoria.', 'Proteger a trilha contra edição com hash encadeado.', 'Equilibrar rastreabilidade e privacidade.'], 'minutes': 20,
  'activity': 'Entregue um "incidente" fictício (uma resposta errada do assistente). Cada grupo lista que informações precisaria para reconstruí-lo e depois corta o que não explica nada e é dado pessoal. Compare as listas.',
  'discussion': ['Quem deveria poder ler a trilha de auditoria na sua empresa?', 'Que decisão do assistente você teria de explicar a uma pessoa que pedisse revisão?'],
  'misconceptions': ['"Guardar tudo é auditar bem." Guardar tudo cria outro risco.', '"Um log em arquivo já é prova." Sem integridade, qualquer pessoa com acesso pode editá-lo.']},
 {'objectives': ['Define the fields of an audit event.', 'Protect the trail against editing with a chained hash.', 'Balance traceability and privacy.'], 'minutes': 20,
  'activity': 'Hand out a fictional "incident" (a wrong answer from the assistant). Each group lists the information it would need to reconstruct it and then cuts what explains nothing and is personal data. Compare the lists.',
  'discussion': ['Who should be able to read the audit trail in your company?', 'Which assistant decision would you have to explain to a person asking for review?'],
  'misconceptions': ['"Keeping everything is auditing well." Keeping everything creates another risk.', '"A log file is already proof." Without integrity, anyone with access can edit it.']})


def build():
    write('13-auditoria-e-rastreabilidade', s, loc('pt'), loc('en'), tch())
