"""R2 · 11 · dados pessoais e LGPD (minimização, retenção, base legal)."""
import json
from r2_common import *

M1 = LQ('Meu CPF é 123.456.789-09 e meu e-mail é ana.souza@aurora.example. Pode atualizar meu cadastro?', 'My CPF is 123.456.789-09 and my e-mail is ana.souza@aurora.example. Can you update my record?')
M2 = LQ('Me liga no (15) 99876-5432 sobre o atestado do meu filho.', 'Call me at (15) 99876-5432 about my son’s medical certificate.')
M3 = LQ('Quantos dias de férias eu tenho?', 'How many vacation days do I have?')

TYPES = ['cpf', 'email', 'phone', 'health']
SHARES = [SHARE_PII['cpf'], SHARE_PII['email'], SHARE_PII['phone'], SHARE_HEALTH]   # % das conversas
POLICY_DAYS = 90        # prazo que a Aurora definiu para os logs de auditoria (decisão da empresa, não da lei)
RISK_LIMIT = 1000       # conversas com dado pessoal que o encarregado aceita ver num vazamento
assert sum(SHARES) == 21 and round(WEEKLY * 90 / 7) == 25714 and round(round(WEEKLY * 730 / 7) * 21 / 100) == 43800
assert round(round(WEEKLY * 90 / 7) * 3 / 100) == 771 and round(round(WEEKLY * 30 / 7) * 3 / 100) == 257

# o que cada exemplo contém (cpf, email, phone, health) e o que sobra depois de cada redação
HAS = {M1['pt']: [1, 1, 0, 0], M2['pt']: [0, 0, 1, 1], M3['pt']: [0, 0, 0, 0]}
REPL = {  # tipo -> (trecho original, marcador), por idioma
    'pt': {M1['pt']: {'cpf': ('123.456.789-09', '[CPF]'), 'email': ('ana.souza@aurora.example', '[EMAIL]')},
           M2['pt']: {'phone': ('(15) 99876-5432', '[TELEFONE]'), 'health': ('atestado do meu filho', '[SAÚDE]')}, M3['pt']: {}},
    'en': {M1['en']: {'cpf': ('123.456.789-09', '[CPF]'), 'email': ('ana.souza@aurora.example', '[EMAIL]')},
           M2['en']: {'phone': ('(15) 99876-5432', '[PHONE]'), 'health': ('son’s medical certificate', '[HEALTH]')}, M3['en']: {}}}


def redactions(L, example):
    out = {}
    for bits in range(16):
        key = ''.join('1' if bits & (8 >> i) else '0' for i in range(4))
        t = example
        for i, ty in enumerate(TYPES):
            if key[i] == '1' and ty in REPL[L][example]:
                old, new = REPL[L][example][ty]
                t = t.replace(old, new)
        out[key] = t
    return out


s = step('r-dados-pessoais-e-lgpd', 11, 20, ['seguranca', 'privacidade', 'lgpd', 'minimizacao', 'retencao', 'base-legal'],
 ['r-vazamento-de-dados-e-permissoes'], ['simulado', 'no-navegador', 'sua-chave'], LQ('minimizar', 'minimize'),
 {'name': 'text', 'required': False, 'ui': 'examples', 'default': M1, 'examples': ex(M1, M2, M3)},
 [flag('redact', 'redigir', 'redact', 'list', options=[opt('cpf', 'cpf', 'cpf'), opt('email', 'email', 'email'), opt('phone', 'telefone', 'phone'), opt('health', 'saude', 'health')], default=TYPES, ui='checkboxes'),
  flag('retention', 'retencao', 'retention', 'int', min=1, max=730, default=POLICY_DAYS, ui='slider'),
  flag('basis', 'base', 'basis', 'enum', options=[opt('consent', 'consentimento', 'consent'), opt('contract', 'contrato', 'contract'), opt('interest', 'interesse', 'interest'), opt('none', 'nenhuma', 'none')], default='interest', ui='select')],
 {'options': ['few', 'many'], 'answer': 'many'}, 'excess',
 {'live': True,
  'consts': {'real': False, 'realFields': {}, 'realValid': False, 'weekly': WEEKLY, 'typeIds': TYPES, 'shareArr': SHARES, 'policyDays': POLICY_DAYS, 'riskLimit': RISK_LIMIT,
             'yesNo': {'1': 'yes', '0': 'no'}, 'toneMap': {'0': 'dim', '1': 'dim', '2': 'bad', '3': 'ok'}},
  'compute': {
   'rec': 'lookup(msgs, text, unknownMsg)',
   'known': 'rec.known',
   'mask': "(includes(redact, 'cpf') ? '1' : '0') + (includes(redact, 'email') ? '1' : '0') + (includes(redact, 'phone') ? '1' : '0') + (includes(redact, 'health') ? '1' : '0')",
   'redArr': 'memberall(typeIds, redact)',
   'notRed': 'affine(redArr, 1, -1)',
   'hasArr': 'real ? (realValid ? [realFields.cpf ? 1 : 0, realFields.email ? 1 : 0, realFields.phone ? 1 : 0, realFields.health ? 1 : 0] : fill(4, 0)) : rec.has',
   'exposedNow': 'sum(mul(hasArr, notRed))',
   'shown': "known ? lookup(rec.red, mask, text) : ''",
   'retained': 'round(weekly * retention / 7)',
   'keptPct': 'sum(mul(shareArr, notRed))',
   'records': 'round(retained * keptPct / 100)',
   'sensKept': "!includes(redact, 'health')",
   'retainedS': 'fmt(retained, 0, lang)',
   'recordsS': 'fmt(records, 0, lang)',
   'limitS': 'fmt(riskLimit, 0, lang)',
   'tonesKey': 'addall(scale(hasArr, 2), redArr)',
   'rowTones': 'lookupall(toneMap, tonesKey)',
   'hasCol': 'lookupall(yesNoL, hasArr)',
   'redCol': 'lookupall(yesNoL, redArr)',
   'basisL': 'lookup(basisNames, basis, basis)',
   'sensOk': "!sensKept || basis == 'consent'"},
  'cases': [
   {'when': '!known && !real', 'error': 'unknownMsg'},
   {'when': 'records > riskLimit', 'flags': ['excess']},
   {'when': 'records <= riskLimit && sensKept', 'flags': ['sensitive']},
   {'when': 'retention > policyDays', 'flags': ['longRetention']},
   {'when': "basis == 'none'", 'flags': ['noBasis']},
   {'when': 'records == 0', 'flags': ['minimal']},
   {'when': 'real && !realValid', 'flags': ['invalidJson']},
   {'when': 'true', 'vars': {'retained': 'retained', 'retainedS': 'retainedS', 'records': 'records', 'recordsS': 'recordsS', 'keptPct': 'keptPct', 'retention': 'retention', 'limitS': 'limitS', 'riskLimit': 'riskLimit', 'basisL': 'basisL', 'policyDays': 'policyDays'}}],
  'widgets': [
   {'type': 'flow', 'label': '@flowLabel', 'steps': [
     {'label': '@sOrig', 'sub': '=text', 'tone': 'info'},
     {'label': '@sRedact', 'sub': "=known ? shown : (exposedNow > 0 ? '@subRealExposed' : '@subRealClean')", 'tone': "=exposedNow > 0 ? 'bad' : 'ok'"},
     {'label': '@sStore', 'sub': '@subStore', 'tone': "=retention > policyDays ? 'warn' : 'neutral'"}]},
   {'type': 'table', 'label': '@tableLabel', 'columns': ['@colType', '@colHas', '@colRedacted', '@colShare'], 'rows': '=zip(typeLabels, hasCol, redCol, shareLabels)', 'tones': '=rowTones', 'caption': '@tableCaption'},
   {'type': 'metrics', 'items': [
     {'label': '@mRetained', 'value': '=retainedS', 'tone': "=retention > policyDays ? 'warn' : 'info'"},
     {'label': '@mKept', 'value': "=keptPct + '%'", 'tone': "=keptPct == 0 ? 'ok' : 'warn'"},
     {'label': '@mRecords', 'value': '=recordsS', 'tone': "=records > riskLimit ? 'bad' : (records == 0 ? 'ok' : 'warn')"}]},
   {'type': 'checks', 'items': [{'label': '@chkMin', 'ok': '=records <= riskLimit', 'why': '@whyMin'},
                                {'label': '@chkRet', 'ok': '=retention <= policyDays', 'why': '@whyRet'},
                                {'label': '@chkBasis', 'ok': "=basis != 'none'", 'why': '@whyBasis'},
                                {'label': '@chkSens', 'ok': '=sensOk', 'why': '@whySens'}]},
   {'type': 'note', 'when': '=records <= riskLimit && sensKept', 'tone': 'warn', 'text': '@sensNote'},
   {'type': 'note', 'when': '=real', 'tone': 'info', 'text': '@realNote'},
   {'type': 'note', 'when': '=!real', 'tone': 'info', 'text': '@simNote'}]},
 real_chat('json', {'system': '{detectorSys}', 'user': '{text}', 'schema': {'cpf': 'boolean', 'email': 'boolean', 'phone': 'boolean', 'health': 'boolean'}}))

PII_PY = '''import hashlib
import hmac
import os
import re

CPF_RE = re.compile(r"\\b\\d{3}\\.?\\d{3}\\.?\\d{3}-?\\d{2}\\b")
EMAIL_RE = re.compile(r"\\b[\\w.+-]+@[\\w-]+\\.[\\w.-]+\\b")
PHONE_RE = re.compile(r"(?:\\(\\d{2}\\)\\s?)?9?\\d{4}-?\\d{4}\\b")


def valid_cpf(raw):
    """Confere os dois dígitos verificadores; evita redigir qualquer número de 11 dígitos."""
    d = [int(c) for c in re.sub(r"\\D", "", raw)]
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for n in (9, 10):
        total = sum(d[i] * (n + 1 - i) for i in range(n))
        if (total * 10 % 11) % 10 != d[n]:
            return False
    return True


def redact(text, kinds=("cpf", "email", "phone")):
    if "cpf" in kinds:
        text = CPF_RE.sub(lambda m: "[CPF]" if valid_cpf(m.group()) else m.group(), text)
    if "email" in kinds:
        text = EMAIL_RE.sub("[EMAIL]", text)
    if "phone" in kinds:
        text = PHONE_RE.sub("[TELEFONE]", text)
    return text


def pseudonym(user_id):
    """O mesmo colaborador sempre vira o mesmo código, o que permite achar e apagar os dados dele (art. 18), mas sem o nome no log."""
    return hmac.new(os.environ["LOG_KEY"].encode(), user_id.encode(), hashlib.sha256).hexdigest()[:16]'''

PII_TEST = '''if __name__ == "__main__":
    os.environ.setdefault("LOG_KEY", "chave-de-teste")
    for msg in [{m1}, {m2}, {m3}]:
        print(redact(msg))
    print(pseudonym("ana.souza"))'''

PURGE = '''import json
import pathlib
import time

from pii import pseudonym, redact

RETENTION_DAYS = 90  # a política da Aurora para logs de auditoria; registre o motivo e quem aprovou


def log_conversation(user_id, question, answer, day):
    """Grava só texto redigido e o código do colaborador, num arquivo por dia."""
    path = pathlib.Path("logs") / f"{{day}}.jsonl"
    path.parent.mkdir(exist_ok=True)
    row = {{"user": pseudonym(user_id), "question": redact(question), "answer": redact(answer)}}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\\n")


def purge_old_logs(now=None):
    """Roda todo dia (cron): apaga o que passou do prazo. Retenção que ninguém executa não existe."""
    limit = (now or time.time()) - RETENTION_DAYS * 86400
    removed = 0
    for f in pathlib.Path("logs").glob("*.jsonl"):
        if f.stat().st_mtime < limit:
            f.unlink()
            removed += 1
    return removed


def erase_person(user_id):
    """Pedido de eliminação do titular (art. 18, VI): reescreve os arquivos sem as linhas dele."""
    code = pseudonym(user_id)
    for f in pathlib.Path("logs").glob("*.jsonl"):
        rows = [r for r in f.read_text(encoding="utf-8").splitlines() if json.loads(r)["user"] != code]
        f.write_text("\\n".join(rows) + ("\\n" if rows else ""), encoding="utf-8")'''


def loc(L):
    pt = L == 'pt'; T = lambda a, b: a if pt else b
    cheat = T('minimizar --redigir nenhum --retencao 730', 'minimize --redact none --retention 730')
    msgs = {e[L]: {'known': True, 'has': HAS[e['pt']], 'red': redactions(L, e[L])} for e in (M1, M2, M3)}
    detector = T('Você detecta dados pessoais em mensagens ao assistente de RH da Aurora. Para cada tipo, diga true se aparece na mensagem e false se não: cpf, email, phone (telefone) e health (qualquer informação de saúde: atestado, doença, remédio, consulta). Responda só com JSON: {"cpf":false,"email":false,"phone":false,"health":false}.',
                 'You detect personal data in messages to Aurora’s HR assistant. For each type, say true if it appears in the message and false if not: cpf, email, phone and health (any health information: medical certificate, illness, medicine, appointment). Reply only with JSON: {"cpf":false,"email":false,"phone":false,"health":false}.')
    return {
  'title': T('Dados pessoais e LGPD', 'Personal data and LGPD'),
  'subtitle': T('Guardar só o necessário, por pouco tempo e com um motivo escrito: minimização, retenção e base legal', 'Keep only what is needed, for a short time and with a written reason: minimization, retention and legal basis'),
  'mission': T('O assistente da Aurora grava todas as conversas para auditar e melhorar. Cerca de 2.000 por semana, e em torno de 21% carregam dado pessoal: CPF em 7%, e-mail em 6%, telefone em 5% e dado de saúde em 3% (atestado, remédio, consulta). O encarregado de dados (DPO) aceita no máximo 1.000 conversas com dado pessoal expostas num vazamento do banco de logs. Escolha o que redigir antes de gravar, por quantos dias guardar e qual base legal justifica a guarda, e veja o tamanho do estrago possível.',
               'Aurora’s assistant records every conversation to audit and improve. About 2,000 a week, and around 21% carry personal data: CPF in 7%, e-mail in 6%, phone in 5% and health data in 3% (medical certificate, medicine, appointment). The data protection officer (DPO) accepts at most 1,000 conversations with personal data exposed in a breach of the log database. Choose what to redact before recording, how many days to keep and which legal basis justifies keeping, and see the size of the possible damage.'),
  'predict': {'question': T('a equipe quer guardar tudo por 730 dias "por garantia", sem redigir nada. Se o banco de logs vazar, quantas conversas com dado pessoal saem?',
                            'the team wants to keep everything for 730 days "just in case", redacting nothing. If the log database leaks, how many conversations with personal data come out?'),
              'options': {'few': T('Algumas centenas', 'A few hundred'), 'many': T('Dezenas de milhares', 'Tens of thousands')}},
  'feedback': {'right': T('isso: 730 dias são cerca de 208.571 conversas guardadas, e 21% carregam dado pessoal, o que dá 43.800. Cada dia a mais de retenção e cada tipo de dado sem redigir multiplicam o estrago.',
                          'right: 730 days is about 208,571 conversations kept, and 21% carry personal data, which makes 43,800. Every extra day of retention and every type of data left unredacted multiplies the damage.'),
               'wrong': T('dezenas de milhares: 730 dias são cerca de 208.571 conversas guardadas, e 21% carregam dado pessoal, o que dá 43.800. Cada dia a mais de retenção e cada tipo de dado sem redigir multiplicam o estrago.',
                          'tens of thousands: 730 days is about 208,571 conversations kept, and 21% carry personal data, which makes 43,800. Every extra day of retention and every type of data left unredacted multiplies the damage.'),
               'skipped': T('sem palpite? Mexa no controle de dias e nas caixas de redação e veja o número de conversas expostas mudar.', 'no guess? Move the days control and the redaction boxes and watch the number of exposed conversations change.')},
  'coach': {'ui': T('palpite anotado. Rode com a política da Aurora (redigir tudo, 90 dias) e leia a tabela e as verificações.', 'guess noted. Run with Aurora’s policy (redact everything, 90 days) and read the table and the checks.'),
            'cmd': T('palpite anotado. Rode minimizar e leia a tabela e as verificações.', 'guess noted. Run minimize and read the table and the checks.')},
  'tryNext': {'ui': T('Agora tire a redação de saúde: o número ainda cabe no limite do DPO, mas esse 3% de conversas é dado sensível.', 'Now take health redaction away: the number still fits the DPO’s limit, but that 3% of conversations is sensitive data.'),
              'cmd': T('Rode minimizar --redigir cpf,email,telefone e olhe a verificação do dado sensível.', 'Run minimize --redact cpf,email,phone and look at the sensitive data check.')},
  'why': {'simples': T('A melhor forma de não vazar um dado é não ter o dado. Se a conversa for gravada com o CPF trocado por [CPF], quem roubar o arquivo leva só um monte de colchetes. E o que você grava, guarda por quanto tempo? Como a geladeira: tudo tem prazo, e quem esquece o prazo acaba com um problema no fundo da prateleira.\nA lei brasileira pede, em resumo, três coisas: ter um motivo claro para guardar (a base legal), guardar só o necessário para esse motivo e apagar quando o motivo acabar. E a pessoa pode pedir para ver, corrigir ou apagar o que você tem dela.',
                       'The best way not to leak a piece of data is not to have it. If the conversation is recorded with the CPF replaced by [CPF], whoever steals the file takes only a pile of brackets. And what you do record, how long do you keep it? Like the fridge: everything has a shelf life, and whoever forgets ends up with a problem at the back of the shelf.\nBrazilian law asks, in short, for three things: a clear reason to keep (the legal basis), keeping only what is necessary for that reason and deleting when the reason ends. And the person may ask to see, correct or delete what you hold about them.'),
          'dev': T('Minimização no código: redija antes de gravar (log, trace, conjunto de avaliação, analytics), não depois. Regex resolve formatos fixos: CPF (confira os dígitos verificadores para não redigir qualquer número de 11 dígitos), e-mail e telefone. Dado de saúde, nome e endereço em texto livre exigem um detector com modelo (a opção "saúde" da lição usa um classificador); esse detector também erra, então redija em dois passos e meça nos casos reais.\nRetenção: defina o prazo por finalidade (auditoria, qualidade, segurança), grave o motivo e execute com um job que apaga (o código da receita). Identificação: grave um código no lugar do nome (pseudônimo com chave guardada à parte) para conseguir achar e apagar os dados de uma pessoa quando ela pedir. Pseudonimizar não é anonimizar: se dá para reverter com meios razoáveis, continua sendo dado pessoal.\nO que vai para a API de um provedor também conta: envie só o necessário e, se o provedor estiver fora do Brasil, confira com o jurídico se há transferência internacional. Registre com quem os dados são compartilhados.',
                   'Minimization in code: redact before recording (log, trace, evaluation set, analytics), not after. Regex handles fixed formats: CPF (check the verification digits so you do not redact any 11-digit number), e-mail and phone. Health data, names and addresses in free text need a model-based detector (the lesson’s "health" option uses a classifier); that detector also errs, so redact in two passes and measure on real cases.\nRetention: define the period per purpose (audit, quality, security), record the reason and enforce it with a job that deletes (the recipe’s code). Identification: record a code instead of the name (a pseudonym with a key kept apart) so you can find and delete one person’s data when they ask. Pseudonymizing is not anonymizing: if it can be reversed with reasonable means, it is still personal data.\nWhat goes to a provider’s API counts too: send only what is needed and, if the provider is outside Brazil, check with legal whether there is an international transfer. Record who the data is shared with.'),
          'especialista': T('Esta lição é informação geral sobre a lei, não é aconselhamento jurídico: valide cada decisão com o jurídico e o encarregado da sua empresa.\nLei 13.709/2018 (LGPD). O art. 6º exige boa-fé e dez princípios (finalidade, adequação, necessidade, livre acesso, qualidade dos dados, transparência, segurança, prevenção, não discriminação, responsabilização e prestação de contas); a minimização é o princípio da necessidade, limitar o tratamento ao mínimo necessário. O art. 7º lista dez hipóteses (bases legais) para dados pessoais, entre elas consentimento, cumprimento de obrigação legal, execução de contrato e legítimo interesse; o art. 5º, XII define consentimento como manifestação livre, informada e inequívoca para uma finalidade determinada, o que merece cuidado quando quem pede é o empregador. Dados sobre saúde, origem racial ou étnica, convicção religiosa, opinião política, filiação sindical e dados genéticos ou biométricos são sensíveis (art. 5º, II) e só podem ser tratados nas hipóteses do art. 11, uma lista própria: consentimento específico e destacado, ou casos como obrigação legal, exercício regular de direitos e tutela da saúde. O legítimo interesse não está nessa lista.\nO término do tratamento e a eliminação estão nos arts. 15 e 16 (com exceções, como cumprimento de obrigação legal). Os direitos do titular estão no art. 18: confirmação do tratamento, acesso, correção, anonimização, bloqueio ou eliminação de dados desnecessários, portabilidade, eliminação dos dados tratados com consentimento, informação sobre compartilhamento e revogação do consentimento. O art. 46 exige medidas de segurança, técnicas e administrativas, e o art. 48 manda comunicar incidentes à ANPD e ao titular; a Resolução CD/ANPD nº 15/2024 fixa três dias úteis a partir do conhecimento de que o incidente afetou dados pessoais. O art. 33 limita a transferência internacional (a ANPD aprovou o regulamento na Resolução nº 19/2024, com cláusulas-padrão contratuais). Multa simples pode chegar a 2% do faturamento (art. 52, II).\nA ANPD já agiu sobre IA: em julho de 2024 determinou a suspensão da nova política de privacidade da Meta no Brasil, que permitiria usar dados de usuários para treinar IA generativa, e em 30 de agosto de 2024 suspendeu a medida após aprovar um plano de conformidade, com aviso individual e opção de recusa.',
                            'This lesson is general information about the law, not legal advice: validate each decision with your company’s legal team and data protection officer.\nLaw 13,709/2018 (LGPD). Art. 6 requires good faith and ten principles (purpose, adequacy, necessity, free access, data quality, transparency, security, prevention, non-discrimination, accountability); minimization is the necessity principle, limiting processing to the minimum necessary. Art. 7 lists ten grounds (legal bases) for personal data, among them consent, compliance with a legal obligation, performance of a contract and legitimate interest; art. 5, XII defines consent as a free, informed and unambiguous manifestation for a specific purpose, which deserves care when the one asking is the employer. Data about health, racial or ethnic origin, religious belief, political opinion, union membership and genetic or biometric data are sensitive (art. 5, II) and may only be processed under the hypotheses of art. 11, a list of its own: specific and prominent consent, or cases such as legal obligation, regular exercise of rights and health protection. Legitimate interest is not on that list.\nEnd of processing and deletion are in arts. 15 and 16 (with exceptions, such as compliance with a legal obligation). The data subject’s rights are in art. 18: confirmation of processing, access, correction, anonymization, blocking or deletion of unnecessary data, portability, deletion of data processed with consent, information about sharing and withdrawal of consent. Art. 46 requires technical and administrative security measures, and art. 48 requires notifying incidents to the ANPD and the data subject; Resolution CD/ANPD 15/2024 sets three business days from the moment of knowing the incident affected personal data. Art. 33 limits international transfers (the ANPD approved the regulation in Resolution 19/2024, with standard contractual clauses). A simple fine can reach 2% of revenue (art. 52, II).\nThe ANPD has already acted on AI: in July 2024 it ordered the suspension of Meta’s new privacy policy in Brazil, which would have allowed using users’ data to train generative AI, and on 30 August 2024 it suspended the measure after approving a compliance plan, with individual notice and an opt-out.')},
  'break': {'mission': {'ui': T('hora de quebrar: não redija nada e guarde as conversas por 730 dias.', 'time to break it: redact nothing and keep the conversations for 730 days.'),
                        'cmd': T(f'hora de quebrar: rode {cheat}', f'time to break it: run {cheat}')},
            'success': T('Quebrou: um vazamento do banco de logs exporia {recordsS} conversas com dado pessoal (o limite aceito pelo DPO era {limitS}). Cada dia a mais de retenção e cada tipo de dado sem redigir multiplicam o estrago.',
                         'Broken: a breach of the log database would expose {recordsS} conversations with personal data (the limit accepted by the DPO was {limitS}). Every extra day of retention and every type of data left unredacted multiplies the damage.'),
            'calm': T('Um vazamento do banco de logs exporia {recordsS} conversas com dado pessoal ({retention} dias, base "{basisL}"), dentro do limite de {limitS}. Para quebrar, guarde por muito tempo e sem redigir.',
                      'A breach of the log database would expose {recordsS} conversations with personal data ({retention} days, "{basisL}" basis), within the limit of {limitS}. To break it, keep for a long time and without redacting.')},
  'hints': {'ui': T(['Marque o que é redigido, escolha os dias de retenção e a base legal, e rode.', 'O estrago é: conversas guardadas × fatia que ainda carrega dado pessoal. Os dois controles mexem no número.', 'Redigir: nenhum. Retenção: 730 dias.'],
                    ['Check what is redacted, choose the retention days and the legal basis, and run.', 'The damage is: conversations kept × the share that still carries personal data. Both controls move the number.', 'Redact: none. Retention: 730 days.']),
            'cmd': T(['A mensagem vai entre aspas, depois de minimizar.', '--redigir cpf,email,telefone,saude (ou nenhum); --retencao de 1 a 730 dias; --base consentimento, contrato, interesse ou nenhuma.', cheat],
                     ['The message goes in quotes, after minimize.', '--redact cpf,email,phone,health (or none); --retention from 1 to 730 days; --basis consent, contract, interest or none.', cheat])},
  'errors': {'notInEnum.redact': T('"{value}" não é um tipo de dado. Use: {options}.', '"{value}" is not a data type. Use: {options}.'),
             'notInEnum.basis': T('"{value}" não é uma base. Use: {options}.', '"{value}" is not a basis. Use: {options}.'),
             'belowMin.retention': T('A retenção vai de 1 a 730 dias.', 'Retention goes from 1 to 730 days.'), 'aboveMax.retention': T('A retenção vai de 1 a 730 dias.', 'Retention goes from 1 to 730 days.'),
             'notInteger.retention': T('Dias inteiros, por favor.', 'Whole days, please.'), 'notNumber.retention': T('A retenção é um número de dias.', 'Retention is a number of days.'),
             'model.unknownMsg': T('No modo simulado, use uma das três mensagens de exemplo. Com "Sua chave" ou "No navegador", qualquer mensagem passa pelo detector real.', 'In simulated mode, use one of the three example messages. With "Your key" or "In the browser", any message goes through the real detector.')},
  'controls': {'arg': T('Mensagem do colaborador', 'Employee message'), 'redact': T('Redigir antes de gravar', 'Redact before recording'), 'retention': T('Dias que o log fica guardado', 'Days the log is kept'), 'basis': T('Base legal declarada', 'Declared legal basis')},
  'scene': {'flowLabel': T('Do que o colaborador escreveu ao que fica no log', 'From what the employee wrote to what stays in the log'), 'sOrig': T('Mensagem', 'Message'), 'sRedact': T('Depois da redação', 'After redaction'), 'sStore': T('Guardado', 'Stored'),
    'subRealExposed': T('ainda há dado pessoal no que vai para o log', 'there is still personal data in what goes to the log'), 'subRealClean': T('nada a redigir ou tudo redigido', 'nothing to redact, or all redacted'),
    'subStore': T('{retention} dias · base: {basisL}', '{retention} days · basis: {basisL}'),
    'tableLabel': T('Tipos de dado nas conversas', 'Types of data in the conversations'), 'colType': T('tipo', 'type'), 'colHas': T('nesta mensagem', 'in this message'), 'colRedacted': T('redigido', 'redacted'), 'colShare': T('das conversas', 'of conversations'),
    'tableCaption': T('as fatias de 7%, 6%, 5% e 3% são números da lição para 2.000 conversas por semana', 'the 7%, 6%, 5% and 3% shares are lesson numbers for 2,000 conversations a week'),
    'mRetained': T('conversas guardadas', 'conversations kept'), 'mKept': T('com dado pessoal sem redigir', 'with unredacted personal data'), 'mRecords': T('expostas num vazamento', 'exposed in a breach'),
    'chkMin': T('Estrago possível dentro do limite do DPO', 'Possible damage within the DPO’s limit'), 'whyMin': T('Necessidade: guardar o mínimo para o fim declarado (art. 6º, III).', 'Necessity: keep the minimum for the stated purpose (art. 6, III).'),
    'chkRet': T('Retenção dentro da política (90 dias)', 'Retention within policy (90 days)'), 'whyRet': T('O prazo é decisão da empresa, com motivo escrito; acabado o fim, elimina-se (arts. 15 e 16).', 'The period is the company’s decision, with a written reason; when the purpose ends, delete (arts. 15 and 16).'),
    'chkBasis': T('Base legal declarada', 'Legal basis declared'), 'whyBasis': T('Todo tratamento precisa de uma hipótese do art. 7º.', 'Every processing needs a ground from art. 7.'),
    'chkSens': T('Dado de saúde: redigido ou com hipótese do art. 11', 'Health data: redacted or with an art. 11 ground'), 'whySens': T('Sensível tem lista própria de hipóteses (art. 11); o legítimo interesse não está nela. Confirme com o jurídico.', 'Sensitive data has its own list of grounds (art. 11); legitimate interest is not on it. Confirm with legal.'),
    'sensNote': T('Ainda sobra dado de saúde nas conversas guardadas. Pode caber no limite de risco e mesmo assim exigir uma hipótese do art. 11.', 'Health data is still left in the stored conversations. It may fit the risk limit and still require an art. 11 ground.'),
    'realNote': T('Modo real: o modelo detecta que tipos de dado a sua mensagem contém, em JSON. A lição só mostra o texto redigido para os exemplos; os números continuam sendo os da lição.', 'Real mode: the model detects which types of data your message contains, in JSON. The lesson only shows the redacted text for the examples; the numbers stay the lesson’s.'),
    'simNote': T('Modo simulado: o texto redigido segue as regras de CPF, e-mail, telefone e saúde da lição. Use "Sua chave" ou "No navegador" para ver um modelo de verdade detectar os tipos de dado em qualquer mensagem.', 'Simulated mode: the redacted text follows the lesson’s CPF, e-mail, phone and health rules. Use "Your key" or "In the browser" to see a real model detect the data types in any message.')},
  'data': {'msgs': msgs, 'unknownMsg': {'known': False, 'has': [0, 0, 0, 0], 'red': {}},
           'typeLabels': ['CPF', T('E-mail', 'E-mail'), T('Telefone', 'Phone'), T('Saúde (sensível)', 'Health (sensitive)')], 'shareLabels': [f'{x}%' for x in SHARES],
           'yesNoL': {'1': T('sim', 'yes'), '0': T('não', 'no')}, 'basisNames': {'consent': T('consentimento', 'consent'), 'contract': T('contrato', 'contract'), 'interest': T('legítimo interesse', 'legitimate interest'), 'none': T('nenhuma', 'none')},
           'detectorSys': detector},
  'recipe': {'steps': [
     T('Crie pii.py: a redação por regex (com a conferência dos dígitos do CPF) e o pseudônimo do colaborador:\n', 'Create pii.py: regex redaction (with the CPF digit check) and the employee pseudonym:\n') + PII_PY + '\n\n' + PII_TEST.format(m1=json.dumps(M1[L], ensure_ascii=False), m2=json.dumps(M2[L], ensure_ascii=False), m3=json.dumps(M3[L], ensure_ascii=False)),
     T('Rode:\npython pii.py\nO CPF e o e-mail da primeira mensagem e o telefone da segunda saem como [CPF], [EMAIL] e [TELEFONE]. O "atestado do meu filho" continua lá: dado de saúde em texto livre precisa de um classificador, como o da lição.', 'Run:\npython pii.py\nThe CPF and e-mail of the first message and the phone of the second come out as [CPF], [EMAIL] and [TELEFONE]. The "son’s medical certificate" is still there: free-text health data needs a classifier, like the lesson’s.'),
     T('Crie log_store.py: grava só o texto redigido, executa a retenção e atende o pedido de eliminação de uma pessoa (agende purge_old_logs() num cron diário):\n', 'Create log_store.py: records only the redacted text, enforces retention and handles one person’s deletion request (schedule purge_old_logs() in a daily cron):\n') + PURGE.format(),
     T('Escreva num documento curto, para o encarregado revisar: finalidade do log, base legal escolhida e quem aprovou, prazo de 90 dias e por quê, tipos de dado que ainda podem aparecer e com quem os dados são compartilhados (incluindo o provedor do modelo).', 'Write a short document for the data protection officer to review: purpose of the log, chosen legal basis and who approved it, the 90-day period and why, types of data that may still appear and who the data is shared with (including the model provider).')],
   'ok': T('pii.py imprime as três mensagens com [CPF], [EMAIL] e [TELEFONE] no lugar dos dados e um código de 16 caracteres para o colaborador; log_store.py grava só texto redigido em logs/AAAA-MM-DD.jsonl, apaga arquivos com mais de 90 dias e remove as linhas de uma pessoa com erase_person().',
           'pii.py prints the three messages with [CPF], [EMAIL] and [TELEFONE] in place of the data and a 16-character code for the employee; log_store.py records only redacted text in logs/YYYY-MM-DD.jsonl, deletes files older than 90 days and removes one person’s rows with erase_person().')}}


def tch():
    return teacher(
 {'objectives': ['Aplicar minimização, retenção e base legal a um caso concreto.', 'Distinguir dado pessoal de dado sensível.', 'Saber que a pessoa pode pedir acesso e eliminação, e o que isso exige do sistema.'], 'minutes': 20,
  'activity': 'Cada grupo recebe 6 mensagens de um log fictício e sublinha todo dado pessoal. Depois decidem o que guardar, por quanto tempo e por quê, e escrevem o motivo em uma frase para o encarregado.',
  'discussion': ['Para que o log da sua empresa serve de fato, e quanto tempo esse fim exige?', 'Como você acharia e apagaria os dados de uma pessoa específica nos seus logs hoje?'],
  'misconceptions': ['"Guardar tudo é mais seguro." Quanto mais se guarda, maior o estrago possível.', '"Trocar o nome por um código anonimiza." Pseudonimizar não é anonimizar: se dá para reverter, continua sendo dado pessoal.']},
 {'objectives': ['Apply minimization, retention and legal basis to a concrete case.', 'Tell personal data from sensitive data.', 'Know that people may ask for access and deletion, and what that requires of the system.'], 'minutes': 20,
  'activity': 'Each group gets 6 messages from a fictional log and underlines all personal data. Then they decide what to keep, for how long and why, and write the reason in one sentence for the data protection officer.',
  'discussion': ['What is your company’s log actually for, and how long does that purpose require?', 'How would you find and delete one specific person’s data in your logs today?'],
  'misconceptions': ['"Keeping everything is safer." The more you keep, the bigger the possible damage.', '"Replacing the name with a code anonymizes." Pseudonymizing is not anonymizing: if it can be reversed, it is still personal data.']})


def build():
    write('11-dados-pessoais-e-lgpd', s, loc('pt'), loc('en'), tch())
