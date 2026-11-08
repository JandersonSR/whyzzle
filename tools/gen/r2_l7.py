"""R2 · 14 · política de uso de IA na empresa."""
import json
from r2_common import *

U1 = LQ('Resumir o manual de RH para uma pessoa nova.', 'Summarize the HR handbook for a new hire.')
U2 = LQ('Colar o código-fonte do sistema de folha para achar um bug.', 'Paste the payroll system source code to find a bug.')
U3 = LQ('Escrever um e-mail de cobrança com o nome e o CPF do cliente.', 'Write a collection e-mail with the customer’s name and CPF.')
U4 = LQ('Triar currículos e rejeitar candidatos automaticamente.', 'Screen résumés and reject candidates automatically.')
U5 = LQ('Escrever um post de blog sobre férias.', 'Write a blog post about vacation.')
# classe do dado: 0 público, 1 interno, 2 dados pessoais, 3 confidencial; decide sobre pessoas?
CASES = [(U1, 1, False), (U2, 3, False), (U3, 2, False), (U4, 2, True), (U5, 0, False)]

POLICIES = ['ban', 'green', 'tiers', 'open']
TOOLS = ['corp', 'api', 'public']
A, C, D = 'allow', 'cond', 'deny'
MATRIX = {'ban': {t: [D] * 4 for t in TOOLS},
          'green': {'corp': [A, D, D, D], 'api': [A, D, D, D], 'public': [D] * 4},
          'tiers': {'corp': [A, A, C, D], 'api': [A, A, C, D], 'public': [A, D, D, D]},
          'open': {t: [A] * 4 for t in TOOLS}}
MATRIX_FLAT = {p + t + str(i): MATRIX[p][t][i] for p in POLICIES for t in TOOLS for i in range(4)}
MIX = [40, 35, 18, 7]            # % dos pedidos por classe de dado (números da lição)
PATH = {'ban': [0, 0, 0, 0], 'green': [1, 0, 0, 0], 'tiers': [1, 1, 1, 0], 'open': [1, 1, 1, 1]}   # classes com caminho aprovado na ferramenta corporativa
SHADOW = 0.7                     # premissa da lição: 7 em cada 10 pedidos sem caminho aprovado vão para ferramentas pessoais
def pct(p):
    allowed = sum(m * x for m, x in zip(MIX, PATH[p])); return allowed, int(100 - allowed), int((100 - allowed) * SHADOW + .5)
assert [pct(p) for p in POLICIES] == [(0, 100, 70), (40, 60, 42), (93, 7, 5), (100, 0, 0)]

s = step('r-politica-de-uso-de-ia', 14, 20, ['governanca', 'politica', 'shadow-ai', 'lgpd', 'nist', 'iso-42001'],
 ['r-auditoria-e-rastreabilidade'], ['simulado', 'no-navegador', 'sua-chave'], LQ('decidir', 'decide'),
 {'name': 'text', 'required': False, 'ui': 'examples', 'default': U1, 'examples': ex(*[c[0] for c in CASES])},
 [flag('policy', 'politica', 'policy', 'enum', options=[opt('ban', 'proibir', 'ban'), opt('green', 'publico', 'public'), opt('tiers', 'niveis', 'tiers'), opt('open', 'liberar', 'open')], default='tiers', ui='select'),
  flag('tool', 'ferramenta', 'tool', 'enum', options=[opt('corp', 'corporativa', 'corporate'), opt('api', 'api', 'api'), opt('public', 'publica', 'consumer')], default='corp', ui='select'),
  flag('review', 'revisao', 'review', 'bool', default=True, ui='switch')],
 {'options': ['none', 'many'], 'answer': 'many'}, 'shadow',
 {'live': False,
  'consts': {'real': False, 'realFields': {}, 'realValid': False, 'matrix': MATRIX_FLAT, 'mixArr': MIX, 'pathMap': PATH, 'zeros4': [0] * 4, 'shadowRate': SHADOW,
             'clsMap': {'public': 0, 'internal': 1, 'personal': 2, 'confidential': 3}},
  'compute': {
   'rec': 'lookup(cases, text, unknownCase)',
   'known': 'rec.known',
   'cls': "real ? (realValid ? lookup(clsMap, realFields.data_class, 3) : 3) : rec.cls",
   'decides': 'real ? (!realValid || realFields.decides_people == true) : rec.people',
   'v0': "lookup(matrix, policy + tool + cls, 'deny')",
   'noHuman': "decides && v0 != 'deny' && !review",
   'verdict': "noHuman ? 'deny' : (decides && v0 == 'allow' ? 'cond' : v0)",
   'whyKey': "policy == 'ban' ? 'ban' : (noHuman ? 'nohuman' : (verdict == 'deny' ? 'deny' + cls : (verdict == 'cond' ? 'cond' + cls + (decides ? 'p' : '') : 'allow')))",
   'why': "lookup(reasons, whyKey, '')",
   'verdictL': 'lookup(verdictNames, verdict, verdict)',
   'clsL': 'lookup(classNames, str(cls), str(cls))',
   'toolL': 'lookup(toolNames, tool, tool)',
   'allowedPct': 'sum(mul(mixArr, lookup(pathMap, policy, zeros4)))',
   'deniedPct': '100 - allowedPct',
   'shadowPct': 'round(deniedPct * shadowRate)',
   'abandonedPct': 'deniedPct - shadowPct',
   'uncontrolled': "policy == 'open' ? 25 : 0",
   'rows': 'lookup(policyRows, policy, [])',
   'rowTones': 'mark(4, cls, "info", "dim")'},
  'cases': [
   {'when': '!known && !real', 'error': 'unknownCase'},
   {'when': "verdict == 'allow'", 'flags': ['allowed']},
   {'when': "verdict == 'cond'", 'flags': ['conditional']},
   {'when': "verdict == 'deny'", 'flags': ['denied']},
   {'when': 'shadowPct >= 30', 'flags': ['shadow']},
   {'when': "policy == 'open'", 'flags': ['permissive']},
   {'when': 'real && !realValid', 'flags': ['invalidJson']},
   {'when': 'true', 'vars': {'allowedPct': 'allowedPct', 'shadowPct': 'shadowPct', 'abandonedPct': 'abandonedPct', 'uncontrolled': 'uncontrolled', 'verdictL': 'verdictL', 'clsL': 'clsL', 'toolL': 'toolL'}}],
  'widgets': [
   {'type': 'flow', 'label': '@flowLabel', 'steps': [
     {'label': '@sCase', 'sub': '=text', 'tone': 'info'},
     {'label': '@sClass', 'sub': '=clsL', 'tone': "=cls >= 2 ? 'warn' : 'neutral'"},
     {'label': '@sTool', 'sub': '=toolL', 'tone': "=tool == 'public' ? 'warn' : 'neutral'"},
     {'label': '@sVerdict', 'sub': '=verdictL', 'tone': "=verdict == 'deny' ? 'bad' : (verdict == 'cond' ? 'warn' : 'ok')"}]},
   {'type': 'note', 'when': '=why != ""', 'tone': "=verdict == 'deny' ? 'bad' : (verdict == 'cond' ? 'warn' : 'ok')", 'text': '=why'},
   {'type': 'table', 'label': '@tableLabel', 'columns': ['@colClass', '@colCorp', '@colApi', '@colPublic'], 'rows': '=rows', 'tones': '=rowTones', 'caption': '@tableCaption'},
   {'type': 'metrics', 'label': '@metricsLabel', 'items': [
     {'label': '@mAllowed', 'value': '=allowedPct', 'format': 'pct', 'tone': '=allowedPct >= 80 ? "ok" : "warn"'},
     {'label': '@mShadow', 'value': '=shadowPct', 'format': 'pct', 'tone': '=shadowPct >= 30 ? "bad" : (shadowPct > 0 ? "warn" : "ok")'},
     {'label': '@mUncontrolled', 'value': '=uncontrolled', 'format': 'pct', 'tone': '=uncontrolled > 0 ? "bad" : "ok"'}]},
   {'type': 'checks', 'items': [{'label': '@chkPath', 'ok': '=allowedPct >= 80', 'why': '@whyPath'}, {'label': '@chkClosed', 'ok': "=policy != 'open'", 'why': '@whyClosed'}, {'label': '@chkReview', 'ok': '=review', 'why': '@whyReview'}]},
   {'type': 'note', 'when': '=real', 'tone': 'info', 'text': '@realNote'},
   {'type': 'note', 'when': '=!real', 'tone': 'info', 'text': '@simNote'}]},
 real_chat('json', {'system': '{classifierSys}', 'user': '{text}', 'schema': {'data_class': 'enum:public|internal|personal|confidential', 'decides_people': 'boolean'}}))

POLICY_PY = '''POLICY = {{
    "version": "2026-11",
    "owner": "seguranca@aurora.example",   # quem aprova ferramentas novas e exceções
    "review_every_months": 6,
    # classe do dado x ferramenta -> allow | conditions | deny
    "matrix": {{
        "corporate": {{"public": "allow", "internal": "allow", "personal": "conditions", "confidential": "deny"}},
        "api":       {{"public": "allow", "internal": "allow", "personal": "conditions", "confidential": "deny"}},
        "consumer":  {{"public": "allow", "internal": "deny",  "personal": "deny",       "confidential": "deny"}},
    }},
    "conditions": [{conds}],
}}


def decide(data_class, tool, decides_people=False, human_review=True):
    verdict = POLICY["matrix"][tool][data_class]
    if decides_people and verdict != "deny":
        if not human_review:
            return "deny"          # decisão sobre pessoas só com revisão humana (LGPD, art. 20)
        return "conditions"
    return verdict'''

POLICY_TEST = '''CASES = [  # (classe, ferramenta, decide sobre pessoas?, esperado)
    ("internal", "corporate", False, "allow"),
    ("confidential", "consumer", False, "deny"),
    ("confidential", "corporate", False, "deny"),
    ("personal", "corporate", False, "conditions"),
    ("personal", "corporate", True, "conditions"),
    ("public", "consumer", False, "allow"),
]
for data_class, tool, people, expected in CASES:
    got = decide(data_class, tool, people)
    print("OK  " if got == expected else "ERRO", data_class, tool, people, "->", got)
assert decide("personal", "corporate", True, human_review=False) == "deny"'''


def loc(L):
    pt = L == 'pt'; T = lambda a, b: a if pt else b
    cheat = T('decidir --politica proibir', 'decide --policy ban')
    classes = [T('Público', 'Public'), T('Interno', 'Internal'), T('Dados pessoais', 'Personal data'), T('Confidencial', 'Confidential')]
    vn = {A: T('permitido', 'allowed'), C: T('com condições', 'with conditions'), D: T('proibido', 'forbidden')}
    verdict_names = {A: T('permitido', 'allowed'), C: T('permitido com condições', 'allowed with conditions'), D: T('proibido', 'forbidden')}
    base_cond = [T('', ''), T('', ''), T(' Redigir CPF e nomes antes de enviar, usar só ferramenta com contrato que proíba treino com os seus dados e registrar o uso.', ' Redact CPF and names before sending, use only a tool with a contract that forbids training on your data and log the use.'),
                 T(' Exige aprovação da segurança.', ' Requires approval from security.')]
    people = T(' Uma pessoa revisa antes de qualquer decisão sobre alguém.', ' A person reviews before any decision about someone.')
    reasons = {'ban': T('A política proíbe qualquer uso de IA generativa.', 'The policy forbids any use of generative AI.'),
               'nohuman': T('Decisão sobre pessoas sem revisão humana não passa: a pessoa pode pedir revisão de decisões tomadas só por tratamento automatizado (LGPD, art. 20).', 'A decision about people without human review does not pass: the person may ask for review of decisions made only by automated processing (LGPD, art. 20).'),
               'allow': T('Permitido: o dado cabe nesta ferramenta pela política.', 'Allowed: the data fits this tool under the policy.')}
    deny_txt = [T('Esta ferramenta não é aprovada pela política, nem para dado público.', 'This tool is not approved by the policy, not even for public data.'),
                T('Dado interno só vai para ferramenta aprovada pela empresa.', 'Internal data only goes to a company-approved tool.'),
                T('Dado pessoal não pode ir para esta ferramenta nesta política.', 'Personal data cannot go to this tool under this policy.'),
                T('Dado confidencial (código-fonte, contratos) não vai para ferramenta de IA externa.', 'Confidential data (source code, contracts) does not go to an external AI tool.')]
    for i in range(4):
        reasons[f'deny{i}'] = deny_txt[i]
        reasons[f'cond{i}'] = T('Permitido com condições:', 'Allowed with conditions:') + base_cond[i]
        reasons[f'cond{i}p'] = T('Permitido com condições:', 'Allowed with conditions:') + base_cond[i] + people
    rows = {p: [[classes[i]] + [vn[MATRIX[p][t][i]] for t in TOOLS] for i in range(4)] for p in POLICIES}
    cases = {c[0][L]: {'known': True, 'cls': c[1], 'people': c[2]} for c in CASES}
    classifier = T('Você classifica pedidos de uso de IA na Aurora. data_class é o dado mais sensível envolvido: public (nada interno), internal (documentos internos), personal (dados de pessoas, como nome, CPF, currículo) ou confidential (código-fonte, contratos, segredos). decides_people é true se a IA decidiria algo sobre pessoas (contratar, rejeitar, punir, avaliar). Responda só com JSON: {"data_class":"internal","decides_people":false}.',
                   'You classify requests to use AI at Aurora. data_class is the most sensitive data involved: public (nothing internal), internal (internal documents), personal (data about people, like name, CPF, résumé) or confidential (source code, contracts, secrets). decides_people is true if the AI would decide something about people (hire, reject, punish, evaluate). Reply only with JSON: {"data_class":"internal","decides_people":false}.')
    conds = ', '.join(json.dumps(x.strip(), ensure_ascii=False) for x in [base_cond[2], base_cond[3]] if x.strip())
    return {
  'title': T('Política de uso de IA na empresa', 'AI use policy in the company'),
  'subtitle': T('Uma política que as pessoas conseguem cumprir: níveis de dado, ferramentas aprovadas e revisão humana', 'A policy people can actually follow: data levels, approved tools and human review'),
  'mission': T('A Aurora tem um assistente seguro, testado e auditável. Mas as pessoas também usam IA por conta própria, e alguém precisa escrever a regra. Uma política vira uma tabela: de um lado, a classe do dado (público, interno, dados pessoais, confidencial); do outro, a ferramenta (corporativa, API da empresa, serviço de consumo). Escolha o tipo de política e uma ferramenta, veja a decisão para cinco pedidos reais e o que a política faz com o uso no dia a dia: quantos pedidos têm caminho aprovado e quantos vão para fora do controle.',
               'Aurora has an assistant that is safe, tested and auditable. But people also use AI on their own, and someone has to write the rule. A policy becomes a table: on one side, the data class (public, internal, personal data, confidential); on the other, the tool (corporate, company API, consumer service). Choose the policy type and a tool, see the decision for five real requests and what the policy does to everyday use: how many requests have an approved path and how many go beyond control.'),
  'predict': {'question': T('para evitar riscos, a Aurora proíbe todo uso de IA generativa no trabalho. Dos pedidos que as pessoas teriam, quantos passam a acontecer fora das ferramentas da empresa, na premissa da lição de que 7 em cada 10 pessoas sem caminho aprovado usam por conta própria?',
                            'to avoid risks, Aurora forbids all use of generative AI at work. Of the requests people would have, how many end up happening outside company tools, under the lesson’s assumption that 7 in 10 people without an approved path use it on their own?'),
              'options': {'none': T('Nenhum: proibido é proibido', 'None: forbidden is forbidden'), 'many': T('Boa parte: o uso continua, escondido', 'A large part: use continues, hidden')}},
  'feedback': {'right': T('isso: sem nenhum caminho aprovado, 100% dos pedidos ficam sem opção e, na premissa da lição, 70% vão para ferramentas pessoais, fora de qualquer controle. A proibição não acabou com o uso, só tirou o uso da vista. A premissa é da lição, não uma medição.',
                          'right: with no approved path, 100% of requests are left without an option and, under the lesson’s assumption, 70% go to personal tools, outside any control. The ban did not end the use, it only took it out of sight. The assumption is the lesson’s, not a measurement.'),
               'wrong': T('boa parte: sem nenhum caminho aprovado, 100% dos pedidos ficam sem opção e, na premissa da lição, 70% vão para ferramentas pessoais, fora de qualquer controle. A premissa é da lição, não uma medição.',
                          'a large part: with no approved path, 100% of requests are left without an option and, under the lesson’s assumption, 70% go to personal tools, outside any control. The assumption is the lesson’s, not a measurement.'),
               'skipped': T('sem palpite? Rode a política por níveis e depois a que proíbe tudo e compare o uso fora do controle.', 'no guess? Run the tiered policy and then the ban-everything one and compare the use beyond control.')},
  'coach': {'ui': T('palpite anotado. Rode com a política por níveis e a ferramenta corporativa e leia a decisão e a tabela.', 'guess noted. Run with the tiered policy and the corporate tool and read the decision and the table.'),
            'cmd': T('palpite anotado. Rode decidir e leia a decisão, a tabela e as métricas.', 'guess noted. Run decide and read the decision, the table and the metrics.')},
  'tryNext': {'ui': T('Agora escolha o caso do código-fonte e a ferramenta de consumo: é o tipo de situação que fez empresas restringirem o uso de IA.', 'Now pick the source code case and the consumer tool: it is the kind of situation that made companies restrict AI use.'),
              'cmd': T(f'Rode decidir "{U2[L]}" --ferramenta publica e leia o motivo.', f'Run decide "{U2[L]}" --tool consumer and read the reason.')},
  'why': {'simples': T('Regra que ninguém consegue cumprir não é regra: é decoração. Se a política diz "não use IA" e o trabalho fica mais difícil sem ela, as pessoas usam do mesmo jeito, só que escondidas e sem ajuda. Se diz "use o que quiser", qualquer um cola o contrato do cliente num site qualquer.\nO meio-termo é um semáforo: dado público e interno vai nas ferramentas aprovadas; dado de pessoas vai com cuidados; segredo da empresa não sai. E quem decide sobre uma pessoa (contratar, rejeitar) sempre tem uma pessoa revisando.',
                       'A rule nobody can follow is not a rule: it is decoration. If the policy says "do not use AI" and work gets harder without it, people use it anyway, just hidden and without help. If it says "use whatever you like", anyone pastes the customer’s contract into some random site.\nThe middle ground is a traffic light: public and internal data go to approved tools; people’s data goes with care; company secrets do not leave. And whoever decides about a person (hiring, rejecting) always has a person reviewing.'),
          'dev': T('Uma boa política cabe numa página e num arquivo executável. Partes: (1) escopo e glossário; (2) lista de ferramentas aprovadas e por quê (contrato, onde os dados ficam, se o provedor treina com eles, retenção); (3) a matriz classe do dado × ferramenta, com as condições (por exemplo, redigir CPF e nomes antes de enviar); (4) regras para decisões sobre pessoas, sempre com revisão humana; (5) quem aprova ferramentas novas e exceções, e em quanto tempo; (6) onde reportar um incidente; (7) treinamento curto e revisão periódica.\nTransforme a matriz em código (o POLICY da receita), teste com casos reais e use a mesma tabela no gateway de IA da empresa e no manual. Ofereça um caminho aprovado melhor do que o atalho pessoal: se o assistente corporativo é lento ou não faz o que a pessoa precisa, o uso migra. Meça isso: quantas pedidos têm caminho aprovado e quantos usuários usam ferramentas não aprovadas (por pesquisa ou pelo tráfego de rede).',
                   'A good policy fits on one page and in one executable file. Parts: (1) scope and glossary; (2) a list of approved tools and why (contract, where data stays, whether the provider trains on it, retention); (3) the data class × tool matrix, with conditions (for example, redact CPF and names before sending); (4) rules for decisions about people, always with human review; (5) who approves new tools and exceptions, and how fast; (6) where to report an incident; (7) short training and periodic review.\nTurn the matrix into code (the recipe’s POLICY), test it with real cases and use the same table in the company’s AI gateway and in the handbook. Offer an approved path that is better than the personal shortcut: if the corporate assistant is slow or does not do what the person needs, use migrates. Measure it: how many requests have an approved path and how many users use unapproved tools (by survey or by network traffic).'),
          'especialista': T('Caso público: em maio de 2023, a Samsung proibiu o uso de IA generativa em computadores, tablets, celulares e redes internas da empresa depois de um vazamento acidental, em abril, em que engenheiros enviaram código-fonte interno ao ChatGPT, segundo um memorando revisto pela Bloomberg. A empresa disse que a restrição era temporária, enquanto criava ferramentas internas e trabalhava em bloquear o envio de dados sensíveis a serviços externos. A proibição resolve o incidente do dia, e a pergunta da política é o que vem depois.\nReferências: o NIST AI RMF 1.0 (janeiro de 2023) tem a função Govern para cultura, papéis e políticas, e o perfil NIST AI 600-1 (julho de 2024) detalha riscos de IA generativa; a ISO/IEC 42001:2023, de dezembro de 2023, especifica requisitos de um sistema de gestão de IA para qualquer organização que forneça ou use produtos e serviços com IA.\nNa LGPD, a política precisa conversar com: o encarregado (art. 41: o controlador indica e divulga a identidade e o contato), o art. 20 (revisão de decisões automatizadas), o art. 33 (transferência internacional: um provedor fora do Brasil pode configurar uma, com as hipóteses do art. 33, e a ANPD aprovou o regulamento em 2024) e o art. 6º, X (prestação de contas). A regulação específica de IA está em movimento: em dezembro de 2025, o PL 2338/2023 estava em comissão especial na Câmara, com votação adiada para fevereiro de 2026; confira a situação atual. Revise a política por calendário e a cada incidente.',
                            'Public case: in May 2023, Samsung banned the use of generative AI on company computers, tablets, phones and internal networks after an accidental leak in April in which engineers uploaded internal source code to ChatGPT, according to a memo reviewed by Bloomberg. The company said the restriction was temporary, while it built internal tools and worked on blocking uploads of sensitive data to external services. A ban solves the day’s incident, and the policy question is what comes next.\nReferences: NIST AI RMF 1.0 (January 2023) has the Govern function for culture, roles and policies, and the NIST AI 600-1 profile (July 2024) details generative AI risks; ISO/IEC 42001:2023, from December 2023, specifies requirements for an AI management system for any organization that provides or uses products and services with AI.\nUnder LGPD, the policy must talk to: the data protection officer (art. 41: the controller appoints and publishes identity and contact), art. 20 (review of automated decisions), art. 33 (international transfer: a provider outside Brazil may amount to one, with the grounds of art. 33, and the ANPD approved the regulation in 2024) and art. 6, X (accountability). AI-specific regulation is moving: in December 2025, bill PL 2338/2023 was in a special committee in the Chamber of Deputies, with the vote postponed to February 2026; check the current status. Review the policy on a calendar and after every incident.')},
  'break': {'mission': {'ui': T('hora de quebrar: escolha a política que proíbe todo uso de IA.', 'time to break it: choose the policy that forbids all AI use.'),
                        'cmd': T(f'hora de quebrar: rode {cheat}', f'time to break it: run {cheat}')},
            'success': T('Quebrou: só {allowedPct}% dos pedidos têm caminho aprovado e {shadowPct}% acabam em ferramentas fora do controle da empresa (premissa da lição). Uma política que as pessoas não conseguem cumprir só tira o uso da vista.',
                         'Broken: only {allowedPct}% of requests have an approved path and {shadowPct}% end up in tools beyond the company’s control (the lesson’s assumption). A policy people cannot follow only takes the use out of sight.'),
            'calm': T('{allowedPct}% dos pedidos têm caminho aprovado e {shadowPct}% vão para fora do controle. Decisão para este caso: {verdictL}. Para quebrar, proíba todo uso.',
                      '{allowedPct}% of requests have an approved path and {shadowPct}% go beyond control. Decision for this case: {verdictL}. To break it, forbid all use.')},
  'hints': {'ui': T(['Escolha o pedido, o tipo de política e a ferramenta, e rode.', 'A tabela mostra a regra da política por classe de dado e ferramenta; a linha destacada é a do seu pedido. As métricas valem para a política inteira.', 'Política: proibir.'],
                    ['Choose the request, the policy type and the tool, and run.', 'The table shows the policy rule per data class and tool; the highlighted row is your request’s. The metrics apply to the whole policy.', 'Policy: ban.']),
            'cmd': T(['O pedido vai entre aspas, depois de decidir.', '--politica proibir, publico, niveis ou liberar; --ferramenta corporativa, api ou publica; --revisao sim ou nao.', cheat],
                     ['The request goes in quotes, after decide.', '--policy ban, public, tiers or open; --tool corporate, api or consumer; --review yes or no.', cheat])},
  'errors': {'notInEnum.policy': T('"{value}" não é um tipo de política. Use: {options}.', '"{value}" is not a policy type. Use: {options}.'),
             'notInEnum.tool': T('"{value}" não é uma ferramenta. Use: {options}.', '"{value}" is not a tool. Use: {options}.'), 'notBool.review': yn(T),
             'model.unknownCase': T('No modo simulado, use um dos cinco pedidos de exemplo. Com "Sua chave" ou "No navegador", um modelo real classifica qualquer pedido.', 'In simulated mode, use one of the five example requests. With "Your key" or "In the browser", a real model classifies any request.')},
  'controls': {'arg': T('Pedido de uso de IA', 'AI use request'), 'policy': T('Tipo de política', 'Policy type'), 'tool': T('Ferramenta', 'Tool'), 'review': T('Revisão humana em decisões sobre pessoas', 'Human review for decisions about people')},
  'scene': {'flowLabel': T('Do pedido à decisão', 'From request to decision'), 'sCase': T('Pedido', 'Request'), 'sClass': T('Classe do dado', 'Data class'), 'sTool': T('Ferramenta', 'Tool'), 'sVerdict': T('Decisão', 'Decision'),
    'tableLabel': T('A regra desta política', 'This policy’s rule'), 'colClass': T('dado', 'data'), 'colCorp': T('corporativa', 'corporate'), 'colApi': 'API', 'colPublic': T('consumo', 'consumer'),
    'tableCaption': T('a linha destacada é a classe do seu pedido', 'the highlighted row is your request’s class'),
    'metricsLabel': T('A política no dia a dia (mistura de 100 pedidos da lição)', 'The policy day to day (lesson mix of 100 requests)'),
    'mAllowed': T('com caminho aprovado', 'with an approved path'), 'mShadow': T('fora do controle', 'beyond control'), 'mUncontrolled': T('sem proteção nenhuma', 'with no protection at all'),
    'chkPath': T('Pelo menos 80% dos pedidos têm caminho aprovado', 'At least 80% of requests have an approved path'), 'whyPath': T('Quem não tem caminho aprovado cria o próprio.', 'Whoever has no approved path makes their own.'),
    'chkClosed': T('Dado confidencial não fica livre', 'Confidential data is not left open'), 'whyClosed': T('"Liberar tudo" também é uma política, e a pior para código e contratos.', '"Allow everything" is also a policy, and the worst for code and contracts.'),
    'chkReview': T('Decisão sobre pessoas com revisão humana', 'Decisions about people with human review'), 'whyReview': T('O titular pode pedir revisão de decisões só automatizadas (LGPD, art. 20).', 'The data subject may ask for review of fully automated decisions (LGPD, art. 20).'),
    'realNote': T('Modo real: o modelo classifica o pedido em classe de dado e se decide sobre pessoas, em JSON; a decisão sai da tabela da política. Se o JSON vier inválido, a lição assume o pior caso (confidencial, decide sobre pessoas).', 'Real mode: the model classifies the request by data class and whether it decides about people, in JSON; the decision comes from the policy table. If the JSON is invalid, the lesson assumes the worst case (confidential, decides about people).'),
    'simNote': T('Modo simulado: 40/35/18/7% de pedidos por classe e a premissa de que 70% dos sem caminho aprovado usam por conta própria são da lição, não medições. Use "Sua chave" ou "No navegador" para classificar qualquer pedido.', 'Simulated mode: 40/35/18/7% of requests per class and the assumption that 70% of those without an approved path use it on their own are the lesson’s, not measurements. Use "Your key" or "In the browser" to classify any request.')},
  'data': {'cases': cases, 'unknownCase': {'known': False, 'cls': 3, 'people': True}, 'reasons': reasons, 'verdictNames': verdict_names,
           'classNames': {str(i): classes[i] for i in range(4)}, 'toolNames': {'corp': T('ferramenta corporativa', 'corporate tool'), 'api': T('API da empresa', 'company API'), 'public': T('serviço de consumo', 'consumer service')},
           'policyRows': rows, 'classifierSys': classifier},
  'recipe': {'steps': [
     T('Escreva a política numa página (escopo, ferramentas aprovadas e por quê, matriz de dados, regras para decisões sobre pessoas, quem aprova exceções, onde reportar incidentes, revisão a cada 6 meses) e peça a revisão do jurídico e do encarregado.', 'Write the policy on one page (scope, approved tools and why, data matrix, rules for decisions about people, who approves exceptions, where to report incidents, review every 6 months) and ask legal and the data protection officer to review it.'),
     T('Crie policy.py, a mesma matriz em código, para o gateway de IA e os testes usarem:\n', 'Create policy.py, the same matrix as code, for the AI gateway and the tests to use:\n') + POLICY_PY.format(conds=conds),
     T('Acrescente os casos da política ao fim e rode:\n', 'Add the policy cases at the end and run:\n') + POLICY_TEST + '\npython policy.py',
     T('Publique a política junto com um caminho aprovado que funcione (o assistente corporativo), um canal para pedir exceção e um treinamento curto. Revise o arquivo e a página a cada incidente.', 'Publish the policy together with an approved path that works (the corporate assistant), a channel to request exceptions and short training. Review the file and the page after every incident.')],
   'ok': T('o script imprime uma linha por caso com OK (nenhum ERRO) e termina sem exceção: confidencial nunca vai para ferramenta de consumo, dado pessoal só com condições, e decisão sobre pessoas sem revisão humana é negada.',
           'the script prints one line per case with OK (no ERRO) and ends without an exception: confidential data never goes to a consumer tool, personal data only with conditions, and a decision about people without human review is denied.')}}


def tch():
    return teacher(
 {'objectives': ['Escrever uma política como matriz de dado × ferramenta.', 'Ver como uma política impossível de cumprir empurra o uso para fora do controle.', 'Incluir revisão humana e responsáveis na política.'], 'minutes': 20,
  'activity': 'Em grupos, listem 10 usos reais de IA na empresa, classifiquem o dado de cada um (público, interno, pessoal, confidencial) e preencham a matriz com permitido, condições ou proibido. Depois troquem as matrizes e tentem achar um caso que a matriz do outro grupo não cobre.',
  'discussion': ['Que ferramenta aprovada a sua empresa oferece hoje, e ela é boa o bastante para as pessoas preferirem usá-la?', 'Quem aprova exceções e em quanto tempo?'],
  'misconceptions': ['"Proibir tudo é o mais seguro." Sem caminho aprovado, o uso migra para ferramentas fora do controle.', '"A política é um texto, não precisa de teste." Uma matriz em código pode ser testada com casos reais.']},
 {'objectives': ['Write a policy as a data × tool matrix.', 'See how an impossible-to-follow policy pushes use beyond control.', 'Include human review and owners in the policy.'], 'minutes': 20,
  'activity': 'In groups, list 10 real AI uses in the company, classify each one’s data (public, internal, personal, confidential) and fill the matrix with allowed, conditions or forbidden. Then swap matrices and try to find a case the other group’s matrix does not cover.',
  'discussion': ['Which approved tool does your company offer today, and is it good enough for people to prefer using it?', 'Who approves exceptions and how fast?'],
  'misconceptions': ['"Banning everything is the safest." Without an approved path, use migrates to tools beyond control.', '"A policy is a text, it needs no test." A matrix in code can be tested with real cases.']})


def build():
    write('14-politica-de-uso-de-ia', s, loc('pt'), loc('en'), tch())
