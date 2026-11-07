# Shared corpus for IA aplicada · Prática · P2 (RAG de verdade). Fictional company "Aurora".
CHUNKS={'pt':[
 ('Férias','As férias devem ser solicitadas pelo portal do colaborador com 30 dias de antecedência e dependem da aprovação do gestor.'),
 ('Férias','É possível dividir as férias em até três períodos: um deles com pelo menos 14 dias e os demais com pelo menos 5 dias cada.'),
 ('Férias','O colaborador pode vender até um terço das férias (abono pecuniário), pedindo junto com a solicitação das férias.'),
 ('Benefícios','O vale-refeição (VR) é de R$ 45 por dia útil; quem preferir pode trocar pelo vale-alimentação (VA) de mesmo valor.'),
 ('Benefícios','O plano de saúde cobre cônjuge e filhos até 24 anos como dependentes, com coparticipação nas consultas.'),
 ('Benefícios','A PLR é paga em março, proporcional ao atingimento das metas da empresa e da equipe no ano anterior.'),
 ('Trabalho remoto','O trabalho remoto é permitido até 2 dias por semana, combinados com o gestor no início de cada mês.'),
 ('Trabalho remoto','Quem tem dias de trabalho remoto recebe um auxílio home office de R$ 120 por mês, pago junto com o salário.'),
 ('Reembolso','Despesas de trabalho são reembolsadas com nota fiscal enviada pelo app de despesas em até 30 dias.'),
 ('Reembolso','Internet e energia de casa não são reembolsáveis: esses custos já são cobertos pelo auxílio home office.'),
 ('TI','Para trocar a senha do portal, use Meu perfil > Segurança ou ligue no ramal 4000 da TI.'),
 ('TI','Para acessar a VPN, instale o app corporativo e selecione o perfil AUR-VPN-02.')],
'en':[
 ('Vacation','Vacation must be requested through the employee portal 30 days in advance and needs the manager’s approval.'),
 ('Vacation','Vacation can be split into up to three periods: one of at least 14 days and the others of at least 5 days each.'),
 ('Vacation','Employees can sell up to one third of their vacation (cash allowance), asking together with the vacation request.'),
 ('Benefits','The meal allowance (VR) is R$ 45 per working day; anyone may swap it for the grocery allowance (VA) of the same value.'),
 ('Benefits','The health plan covers spouses and children up to 24 as dependents, with co-payment on appointments.'),
 ('Benefits','The PLR profit share is paid in March, proportional to how well company and team goals were met the previous year.'),
 ('Remote work','Remote work is allowed up to 2 days a week, agreed with the manager at the start of each month.'),
 ('Remote work','Anyone with remote days gets a R$ 120 monthly home office allowance, paid with the salary.'),
 ('Expenses','Work expenses are reimbursed with an invoice uploaded in the expenses app within 30 days.'),
 ('Expenses','Home internet and electricity aren’t reimbursable: those costs are already covered by the home office allowance.'),
 ('IT','To change your portal password, go to My profile > Security or call IT extension 4000.'),
 ('IT','To use the VPN, install the corporate app and select the AUR-VPN-02 profile.')]}

# Questions: text per language, gold chunk indices (0-based), and hand-made "semantic" similarities for simulated mode.
# Vectors are good at synonyms and weak at rare codes and acronyms (PLR, AUR-VPN-02) — on purpose.
BASE=[0.72,0.71,0.71,0.72,0.71,0.71,0.72,0.71,0.71,0.71,0.71,0.71]
def sem(over):
    v=list(BASE)
    for i,x in over.items(): v[i]=x
    return v
QUESTIONS=[
 ({'pt':'Com quanta antecedência eu peço férias?','en':'How far in advance do I request vacation?'},[0],sem({0:0.89,1:0.81,2:0.80})),
 ({'pt':'Posso dividir minhas férias?','en':'Can I split my vacation?'},[1],sem({1:0.88,0:0.82,2:0.81})),
 ({'pt':'Quando sai a PLR?','en':'When is the PLR paid?'},[5],sem({5:0.78,3:0.80,4:0.79,7:0.78})),
 ({'pt':'Qual perfil de VPN eu uso?','en':'Which VPN profile do I use?'},[11],sem({11:0.79,10:0.82})),
 ({'pt':'Quem pode ser dependente no plano de saúde?','en':'Who can be a dependent on the health plan?'},[4],sem({4:0.90,3:0.76})),
 ({'pt':'Posso pedir reembolso da internet de casa?','en':'Can I claim my home internet?'},[9,7],sem({8:0.86,9:0.83,7:0.80})),
 ({'pt':'Quanto tempo antes devo avisar que vou descansar?','en':'How long before should I tell them I’ll take time off?'},[0],sem({0:0.86,1:0.80,2:0.79})),
 ({'pt':'Posso vender parte das férias e quanto recebo de VR por dia?','en':'Can I sell part of my vacation and how much VR do I get per day?'},[2,3],sem({2:0.84,0:0.82,1:0.81,3:0.79})),
 ({'pt':'Esqueci minha senha, o que faço?','en':'I forgot my password, what do I do?'},[10],sem({10:0.89,11:0.80}))]

RAW={'pt':"""AURORA TECNOLOGIA LTDA · CONFIDENCIAL
Manual do Colaborador · Página 1 de 2
POLÍTICA DE FÉRIAS
As férias devem ser solicitadas pelo portal do colaborador com 30 dias de ante-
cedência e dependem da aprovação do gestor.
É possível dividir as férias em até três períodos: um deles com pelo menos 14 dias e os demais com pelo menos 5 dias cada.
É possível dividir as férias em até três períodos: um deles com pelo menos 14 dias e os demais com pelo menos 5 dias cada.
AURORA TECNOLOGIA LTDA · CONFIDENCIAL
Manual do Colaborador · Página 2 de 2
BENEFÍCIOS
O vale-refeição (VR) é de R$ 45 por dia útil; quem preferir pode trocar pelo vale-alimentação (VA) de mesmo valor.
A PLR é paga em março, proporcional ao atingimento das metas da empresa e da equipe no ano anterior.""",
'en':"""AURORA TECNOLOGIA LTDA · CONFIDENTIAL
Employee Handbook · Page 1 of 2
VACATION POLICY
Vacation must be requested through the employee portal 30 days in ad-
vance and needs the manager’s approval.
Vacation can be split into up to three periods: one of at least 14 days and the others of at least 5 days each.
Vacation can be split into up to three periods: one of at least 14 days and the others of at least 5 days each.
AURORA TECNOLOGIA LTDA · CONFIDENTIAL
Employee Handbook · Page 2 of 2
BENEFITS
The meal allowance (VR) is R$ 45 per working day; anyone may swap it for the grocery allowance (VA) of the same value.
The PLR profit share is paid in March, proportional to how well company and team goals were met the previous year."""}

STOP={'pt':['qual','quais','como','quando','quanto','quantos','quanta','onde','posso','pode','para','por','pro','com','minha','minhas','meu','meus','sua','seu','que','uma','uns','umas','tem','faco','fazer','devo','eu','de','do','da','das','dos','no','na','nos','nas','o','a','os','as','e','ou','em','ao','se','sai','vou'],
      'en':['what','which','how','when','where','can','could','the','for','with','does','did','was','my','your','that','this','get','have','has','and','you','do','to','of','in','is','an','on','a','i','it','me','long','far','far','should','tell','them','ll']}

def data_for(lang):
    ch=CHUNKS[lang]
    return {'chunkTexts':[t for _,t in ch],'chunkSources':[s for s,_ in ch],
            'questions':[q[lang] for q,_,_ in QUESTIONS],'golds':[g for _,g,_ in QUESTIONS],
            'semSims':{q[lang]:sims for q,_,sims in QUESTIONS},'goldMap':{q[lang]:g for q,g,_ in QUESTIONS},
            'stop':STOP[lang]}
