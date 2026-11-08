"""R1 · 05 · testes A/B de prompt (tamanho de amostra, significância e espiar o resultado)."""
import math
from r1_common import *

PER_DAY = 200  # conversas por braço por dia (400 por dia, 50/50)
LIFTS = [8, 9, 6, 3.5, 2.5, 2.8, 3.2, 3.5, 3.7, 3.8, 3.9, 4.0, 4.0, 4.0, 4.1, 4.0, 4.0, 3.9, 4.0, 4.0, 4.0, 4.1, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0]
PA = [0.59, 0.60, 0.61, 0.615] + [0.62] * 24
DAYS = len(LIFTS)
rows = []
for d in range(1, DAYS + 1):
    n = PER_DAY * d
    sa = round(n * PA[d - 1]); sb = round(n * (PA[d - 1] + LIFTS[d - 1] / 100))
    p1, p2 = sa / n, sb / n
    pp = (sa + sb) / (2 * n)
    z = (p2 - p1) / math.sqrt(pp * (1 - pp) * 2 / n)
    p = math.erfc(abs(z) / math.sqrt(2))
    rows.append({'n': n, 'sa': sa, 'sb': sb, 'lift': round((p2 - p1) * 100, 1), 'z': round(z, 2), 'p': p})
FIRST_SIG = next(i + 1 for i, r in enumerate(rows) if r['p'] < 0.05)
za, zb = 1.959964, 0.841621
NEED = math.ceil((za + zb) ** 2 * (0.62 * 0.38 + 0.66 * 0.34) / 0.04 ** 2)
MIN_DAYS = math.ceil(NEED / PER_DAY)
assert FIRST_SIG == 2 and rows[1]['lift'] == 9.0 and rows[13]['lift'] == 4.0 and rows[13]['p'] < 0.01
assert NEED == 2257 and MIN_DAYS == 12
assert all(rows[i]['p'] >= 0.05 for i in (3, 4, 5, 6)) and all(r['p'] < 0.05 for r in rows[MIN_DAYS - 1:])

s = step('r-testes-ab-de-prompt', 5, 20, ['avaliacao', 'ab-test', 'estatistica', 'significancia', 'experimentos'],
 ['r-testes-de-regressao-no-ci'], ['simulado'], LQ('ab', 'ab'),
 {'name': 'text', 'required': False, 'ui': 'text', 'default': LQ('B: passos numerados', 'B: numbered steps'), 'examples': []},
 [flag('days', 'dias', 'days', 'int', min=1, max=DAYS, default=14, ui='slider'),
  flag('peek', 'espiar', 'peek', 'bool', default=False, ui='switch')],
 {'options': ['holds', 'shrinks', 'flips'], 'answer': 'shrinks'}, 'peeked',
 {'live': True,
  'consts': {'nArr': [r['n'] for r in rows], 'sA': [r['sa'] for r in rows], 'sB': [r['sb'] for r in rows], 'zArr': [r['z'] for r in rows],
             'sigArr': [r['p'] < 0.05 for r in rows], 'firstSig': FIRST_SIG, 'minDays': MIN_DAYS, 'needPerArm': NEED, 'refDay': 14,
             'dayLabels': [f'{d}' for d in range(1, DAYS + 1)]},
  'compute': {
   'stopDay': 'peek && firstSig <= days ? firstSig : days',
   'i': 'stopDay - 1',
   'sig': 'sigArr[i]',
   'early': 'stopDay < minDays',
   'liftS': 'liftStr[i]',
   'pS': 'pStr[i]',
   'nS': 'nStr[i]',
   'rateA': 'round(sA[i] / nArr[i] * 100)',
   'rateB': 'round(sB[i] / nArr[i] * 100)',
   'trueLiftS': 'liftStr[refDay - 1]'},
  'cases': [
   {'when': 'peek && firstSig <= days && firstSig < minDays', 'flags': ['peeked']},
   {'when': 'sig', 'flags': ['significant']},
   {'when': '!sig', 'flags': ['inconclusive']},
   {'when': '!peek && days < minDays', 'flags': ['underpowered']},
   {'when': 'true', 'vars': {'stopDay': 'stopDay', 'liftS': 'liftS', 'pS': 'pS', 'nS': 'nS', 'trueLiftS': 'trueLiftS', 'minDays': 'minDays',
                             'refDay': 'refDay', 'rateA': 'rateA', 'rateB': 'rateB', 'days': 'days'}}],
  'widgets': [
   {'type': 'metrics', 'items': [
     {'label': '@mDay', 'value': '=stopDay', 'format': 'int', 'tone': "=early ? 'warn' : 'ok'"},
     {'label': '@mA', 'value': '=rateA', 'format': 'pct', 'tone': 'neutral'},
     {'label': '@mB', 'value': '=rateB', 'format': 'pct', 'tone': 'neutral'},
     {'label': '@mLift', 'value': '=liftS', 'tone': "=sig ? 'ok' : 'warn'"},
     {'label': '@mP', 'value': '=pS', 'tone': "=sig ? 'ok' : 'warn'"}]},
   {'type': 'chart', 'label': '@chart', 'kind': 'line', 'labels': '=slice(dayLabels, 0, stopDay)',
    'series': [{'label': '@zSeries', 'values': '=slice(zArr, 0, stopDay)'}], 'threshold': {'value': 1.96, 'label': '@zLine'}},
   {'type': 'checks', 'label': '@checks', 'items': [
     {'label': '@chkSize', 'ok': '=!early', 'why': '@whySize'},
     {'label': '@chkSig', 'ok': '=sig', 'why': '@whySig'},
     {'label': '@chkPlan', 'ok': '=!(peek && firstSig <= days)', 'why': '@whyPlan'}]},
   {'type': 'note', 'when': '=peek && firstSig <= days && early', 'tone': 'bad', 'text': '@peekNote'},
   {'type': 'note', 'when': '=!peek && early', 'tone': 'warn', 'text': '@smallNote'},
   {'type': 'note', 'when': '=!early && sig', 'tone': 'ok', 'text': '@okNote'},
   {'type': 'note', 'tone': 'info', 'text': '@simNote'}]})

AB_CODE = '''import math
import sys
from statistics import NormalDist


def sample_size(p_a, lift, alpha=0.05, power=0.8):
    p_b = p_a + lift
    z = NormalDist().inv_cdf(1 - alpha / 2) + NormalDist().inv_cdf(power)
    return math.ceil(z ** 2 * (p_a * (1 - p_a) + p_b * (1 - p_b)) / lift ** 2)


def two_proportions(s_a, n_a, s_b, n_b):
    p_a = s_a / n_a
    p_b = s_b / n_b
    pooled = (s_a + s_b) / (n_a + n_b)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    z = (p_b - p_a) / se
    return p_b - p_a, z, 2 * (1 - NormalDist().cdf(abs(z)))


print("per arm:", sample_size(0.62, 0.04))
if len(sys.argv) == 5:
    s_a, n_a, s_b, n_b = map(int, sys.argv[1:5])
    lift, z, p = two_proportions(s_a, n_a, s_b, n_b)
    print(f"lift {lift * 100:+.1f} points | z {z:.2f} | p {p:.4f}")'''


def loc(L):
    pt = L == 'pt'; T = lambda a, b: a if pt else b
    cheat = T('ab --espiar sim', 'ab --peek yes')
    dec = (lambda x: f'{x:.1f}'.replace('.', ',')) if pt else (lambda x: f'{x:.1f}')
    def pfmt(p):
        if p < 0.001:
            return '< 0,001' if pt else '< 0.001'
        v = f'{p:.3f}'
        return v.replace('.', ',') if pt else v
    lift_str = [('+' if r['lift'] > 0 else '') + dec(r['lift']) for r in rows]
    n_str = [f"{r['n']:,}".replace(',', '.') if pt else f"{r['n']:,}" for r in rows]
    return {
  'title': T('Teste A/B de prompt', 'A/B testing a prompt'),
  'subtitle': T('Tamanho de amostra, significância e o perigo de espiar o placar', 'Sample size, significance and the danger of peeking at the score'),
  'mission': T('O conjunto de avaliação diz que o prompt B (respostas em passos numerados) não piora nada. Falta saber se ele ajuda gente de verdade. A Aurora divide as conversas 50/50: a métrica é a taxa de dúvidas resolvidas, sem chamado aberto no RH em 48 horas. São 400 conversas por dia. Rode o experimento pelo tempo certo e decida com números.',
               'The evaluation set says prompt B (answers in numbered steps) doesn’t make anything worse. What’s left is whether it helps real people. Aurora splits conversations 50/50: the metric is the rate of questions resolved, with no HR ticket opened within 48 hours. There are 400 conversations a day. Run the experiment for the right time and decide with numbers.'),
  'predict': {'question': T('no dia 2, B está 9 pontos à frente com p = 0,008. Se o teste rodar 14 dias, a vantagem de B…', 'on day 2, B is 9 points ahead with p = 0.008. If the test runs 14 days, B’s lead…'),
              'options': {'holds': T('Fica em uns 9 pontos', 'Stays around 9 points'), 'shrinks': T('Encolhe, mas B continua melhor', 'Shrinks, but B stays better'), 'flips': T('Vira: A ganha', 'Flips: A wins')}},
  'feedback': {'right': T('isso: no dia 14 a vantagem é de 4 pontos (62% contra 66%), com p de 0,002. Os 9 pontos do dia 2 eram 4 de efeito e o resto de sorte com amostra pequena.',
                          'right: on day 14 the lead is 4 points (62% against 66%), with p of 0.002. Day 2’s 9 points were 4 of real effect and the rest luck with a small sample.'),
               'wrong': T('ela encolhe: no dia 14 a vantagem é de 4 pontos (62% contra 66%), com p de 0,002. Os 9 pontos do dia 2 eram 4 de efeito e o resto de sorte com amostra pequena.',
                          'it shrinks: on day 14 the lead is 4 points (62% against 66%), with p of 0.002. Day 2’s 9 points were 4 of real effect and the rest luck with a small sample.'),
               'skipped': T('sem palpite? Rode os 14 dias e compare com o dia 2 no gráfico.', 'no guess? Run the 14 days and compare with day 2 on the chart.')},
  'coach': {'ui': T('palpite anotado. Rode com 14 dias e sem espiar; o gráfico mostra o placar dia a dia.', 'guess noted. Run with 14 days and no peeking; the chart shows the score day by day.'),
            'cmd': T('palpite anotado. Rode ab --dias 14 e olhe o gráfico.', 'guess noted. Run ab --days 14 and look at the chart.')},
  'tryNext': {'ui': T('Agora pare no dia 5, sem espiar: a diferença parece ter sumido. Amostra pequena engana para os dois lados.', 'Now stop at day 5, no peeking: the difference seems to have vanished. Small samples fool you both ways.'),
              'cmd': T('Rode ab --dias 5 e leia o p.', 'Run ab --days 5 and read the p.')},
  'why': {'simples': T('Jogue uma moeda 10 vezes e talvez saiam 7 caras; isso não prova que a moeda é viciada. Com poucas conversas, um prompt pode parecer muito melhor só por sorte.\nPor isso o teste A/B tem duas regras: decidir antes quantas conversas olhar, e só olhar o resultado no fim. Quem espia todo dia e para no primeiro dia bonito está escolhendo a sorte.',
                       'Flip a coin 10 times and maybe you get 7 heads; that doesn’t prove the coin is loaded. With few conversations, a prompt can look much better just by luck.\nThat’s why an A/B test has two rules: decide beforehand how many conversations to look at, and only read the result at the end. Whoever peeks every day and stops on the first pretty day is picking luck.'),
          'dev': T('Antes de começar, fixe a métrica, o efeito mínimo que vale a pena (aqui, 4 pontos sobre 62%), α = 0,05 e poder de 80%. A conta de tamanho de amostra para duas proporções dá cerca de 2.257 conversas por braço: com 200 por braço por dia, 12 dias; a Aurora arredonda para 14, duas semanas cheias, porque segunda-feira não é igual a sábado.\nNo fim, um teste z para duas proporções: z = (p_B − p_A) ÷ √(p(1 − p)(1/n_A + 1/n_B)), com p combinado. |z| ≥ 1,96 equivale a p < 0,05. Sorteie por pessoa, não por mensagem (a mesma pessoa fica sempre no mesmo braço), registre o braço em cada conversa e acompanhe métricas de guarda (recusas, chamados ao RH, custo) que não podem piorar.',
                   'Before starting, fix the metric, the minimum effect worth having (here, 4 points over 62%), α = 0.05 and 80% power. The two-proportion sample size formula gives about 2,257 conversations per arm: at 200 per arm per day, 12 days; Aurora rounds up to 14, two full weeks, because Monday isn’t like Saturday.\nAt the end, a two-proportion z test: z = (p_B − p_A) ÷ √(p(1 − p)(1/n_A + 1/n_B)), with pooled p. |z| ≥ 1.96 is p < 0.05. Randomize by person, not by message (the same person always stays in the same arm), log the arm on every conversation and track guardrail metrics (refusals, HR tickets, cost) that must not get worse.'),
          'especialista': T('Espiar todo dia e parar no primeiro p < 0,05 aumenta muito a chance de falso positivo: cada olhada é uma nova chance de a sorte cruzar a linha. Se o time precisa olhar no meio, use um método feito para isso (testes sequenciais ou com correção para olhadas intermediárias), não o teste z repetido. E mesmo quando o efeito é real, parar cedo superestima o tamanho dele (aqui, 9 pontos contra 4): é a "maldição do vencedor".\nA/B mede o que a métrica mede, e só isso. Em abril de 2025, a OpenAI reverteu uma atualização do GPT-4o que deixou o modelo bajulador demais; segundo a própria empresa, as avaliações offline pareciam boas e os testes A/B indicavam que os poucos usuários que provaram gostaram. Ponha métricas de guarda que pegam o que o usuário não percebe na hora (respostas erradas confirmadas pelo RH, recusas certas) e leia uma amostra de conversas de cada braço antes de declarar vitória.',
                            'Peeking every day and stopping at the first p < 0.05 greatly increases the chance of a false positive: every look is another chance for luck to cross the line. If the team must look midway, use a method built for that (sequential tests or tests corrected for interim looks), not the repeated z test. And even when the effect is real, stopping early overestimates its size (here, 9 points against 4): the "winner’s curse".\nA/B measures what the metric measures, and nothing else. In April 2025, OpenAI rolled back a GPT-4o update that made the model too sycophantic; by the company’s own account, offline evaluations looked good and A/B tests suggested the few users who tried it liked it. Add guardrail metrics that catch what users don’t notice right away (wrong answers confirmed by HR, correct refusals) and read a sample of conversations from each arm before declaring victory.')},
  'break': {'mission': {'ui': T('hora de quebrar: ligue "espiar" e deixe o teste parar no primeiro dia com p < 0,05.', 'time to break it: turn on "peek" and let the test stop on the first day with p < 0.05.'),
                        'cmd': T(f'hora de quebrar: rode {cheat}', f'time to break it: run {cheat}')},
            'success': T('Quebrou: espiando todo dia, o teste parou no dia {stopDay} com B {liftS} pontos à frente (p = {pS}), com {nS} conversas por braço, bem abaixo do planejado para {minDays} dias. No dia {refDay}, a vantagem é de {trueLiftS} pontos. Espiar trouxe o anúncio cedo e o número errado.',
                         'Broken: peeking every day, the test stopped on day {stopDay} with B {liftS} points ahead (p = {pS}), with {nS} conversations per arm, well below what was planned for {minDays} days. On day {refDay}, the lead is {trueLiftS} points. Peeking brought an early announcement and the wrong number.'),
            'calm': T('Dia {stopDay}: A {rateA}%, B {rateB}% ({liftS} pontos, p = {pS}). Para quebrar, espie o placar e pare no primeiro resultado bonito.',
                      'Day {stopDay}: A {rateA}%, B {rateB}% ({liftS} points, p = {pS}). To break it, peek at the score and stop at the first pretty result.')},
  'hints': {'ui': T(['Escolha quantos dias o teste roda e aperte Rodar.', '"Espiar" olha o placar todo dia e para no primeiro p < 0,05. A conta de amostra pede pelo menos 12 dias.', 'Espiar ligado, 14 dias.'],
                    ['Pick how many days the test runs and hit Run.', '"Peek" checks the score every day and stops at the first p < 0.05. The sample size formula asks for at least 12 days.', 'Peek on, 14 days.']),
            'cmd': T(['O nome do experimento vai entre aspas (opcional).', f'--dias de 1 a {DAYS}; --espiar sim ou nao.', cheat],
                     ['The experiment name goes in quotes (optional).', f'--days from 1 to {DAYS}; --peek yes or no.', cheat])},
  'errors': {'belowMin.days': T('Pelo menos 1 dia.', 'At least 1 day.'), 'aboveMax.days': T(f'Esta lição tem dados de {DAYS} dias.', f'This lesson has {DAYS} days of data.'),
             'notInteger.days': T('Dias inteiros, por favor.', 'Whole days, please.'), 'notBool.peek': yn(T)},
  'controls': {'arg': T('Nome do experimento', 'Experiment name'), 'days': T('Dias de teste', 'Test days'), 'peek': T('Espiar e parar no primeiro p < 0,05', 'Peek and stop at the first p < 0.05')},
  'scene': {'label': T('Teste A/B: A (atual) contra B (passos numerados)', 'A/B test: A (current) against B (numbered steps)'), 'empty': T('Rode para começar o teste.', 'Run to start the test.'),
    'mDay': T('dia em que parou', 'stopped on day'), 'mA': T('A resolvidas', 'A resolved'), 'mB': T('B resolvidas', 'B resolved'), 'mLift': T('B − A (pontos)', 'B − A (points)'), 'mP': 'p',
    'chart': T('Estatística z, dia a dia', 'z statistic, day by day'), 'zSeries': T('z de B contra A', 'z of B against A'), 'zLine': T('z = 1,96 (p = 0,05)', 'z = 1.96 (p = 0.05)'),
    'checks': T('Dá para decidir?', 'Can we decide?'),
    'chkSize': T('Amostra planejada atingida (12 dias)', 'Planned sample reached (12 days)'), 'whySize': T('parou no dia {stopDay}, com {nS} conversas por braço', 'stopped on day {stopDay}, with {nS} conversations per arm'),
    'chkSig': T('p < 0,05', 'p < 0.05'), 'whySig': T('p = {pS}: a diferença ainda cabe no acaso', 'p = {pS}: the difference still fits chance'),
    'chkPlan': T('Sem parada por espiadela', 'No stop from peeking'), 'whyPlan': T('o teste parou porque alguém espiou no dia {stopDay}', 'the test stopped because someone peeked on day {stopDay}'),
    'peekNote': T('Parou no dia {stopDay} com {liftS} pontos. Com o tempo planejado, o efeito é {trueLiftS} no dia {refDay}.', 'Stopped on day {stopDay} with {liftS} points. With the planned time, the effect is {trueLiftS} on day {refDay}.'),
    'smallNote': T('Só {days} dia(s): menos que os {minDays} que a conta de amostra pede. Um p alto aqui quer dizer "não deu para ver", não "não tem diferença".', 'Only {days} day(s): fewer than the {minDays} the sample size formula asks for. A high p here means "couldn’t tell", not "no difference".'),
    'okNote': T('Amostra completa e p = {pS}: B resolve {liftS} pontos a mais. Antes de virar 100%, confira as métricas de guarda e leia conversas dos dois braços.', 'Full sample and p = {pS}: B resolves {liftS} more points. Before going to 100%, check the guardrail metrics and read conversations from both arms.'),
    'simNote': T('Dados da lição: 200 conversas por braço por dia, com A perto de 62% e B perto de 66% e o ruído do começo escrito à mão. O z e o p são calculados com a fórmula de duas proporções.', 'Lesson data: 200 conversations per arm per day, with A near 62% and B near 66% and the early noise hand-written. z and p are computed with the two-proportion formula.')},
  'data': {'liftStr': lift_str, 'pStr': [pfmt(r['p']) for r in rows], 'nStr': n_str},
  'recipe': {'steps': [
     T('Antes de ligar o teste, escreva o plano: métrica (dúvida resolvida sem chamado em 48 h), efeito mínimo (4 pontos), α = 0,05, poder de 80%, sorteio por pessoa e métricas de guarda. Crie ab_check.py, só com a biblioteca padrão do Python:\n',
       'Before turning the test on, write the plan: metric (question resolved with no ticket in 48 h), minimum effect (4 points), α = 0.05, 80% power, randomization per person and guardrail metrics. Create ab_check.py, with Python’s standard library only:\n') + AB_CODE,
     T('Calcule a amostra por braço (com 200 conversas por braço por dia, divida por 200 para ter os dias):\npython ab_check.py', 'Compute the sample per arm (with 200 conversations per arm per day, divide by 200 to get the days):\npython ab_check.py'),
     T('No fim do prazo, passe sucessos e totais de A e de B. Com os números do dia 14 da lição:\npython ab_check.py 1736 2800 1848 2800\nCompare com os do dia 2:\npython ab_check.py 240 400 276 400',
       'At the end of the period, pass successes and totals for A and B. With the lesson’s day 14 numbers:\npython ab_check.py 1736 2800 1848 2800\nCompare with day 2’s:\npython ab_check.py 240 400 276 400')],
   'ok': T('o script imprime "per arm: 2257"; com os números do dia 14 sai lift +4.0 points, z 3.12 e p perto de 0,002; com os do dia 2 sai lift +9.0 e p perto de 0,008, a vantagem inflada de quem parou cedo.',
           'the script prints "per arm: 2257"; with day 14’s numbers it shows lift +4.0 points, z 3.12 and p near 0.002; with day 2’s it shows lift +9.0 and p near 0.008, the inflated lead of stopping early.')}}


def tch():
    return teacher(
 {'objectives': ['Calcular tamanho de amostra antes do teste.', 'Ler z e p de duas proporções.', 'Explicar por que espiar e parar cedo engana.'], 'minutes': 25,
  'activity': 'Cada grupo joga uma moeda 10 vezes e anota caras; depois junta os resultados da turma toda. Compare a proporção de cada grupo com a da turma e discuta qual grupo "parou cedo".',
  'discussion': ['Que métrica de guarda o assistente de RH não pode piorar?', 'Quem decide o efeito mínimo que vale a pena, e com que argumento?'],
  'misconceptions': ['"Deu p < 0,05 no segundo dia, já podemos parar." Parar na primeira olhada boa infla o falso positivo e o efeito.', '"p alto prova que não há diferença." Pode ser só amostra pequena.']},
 {'objectives': ['Compute sample size before the test.', 'Read z and p for two proportions.', 'Explain why peeking and stopping early misleads.'], 'minutes': 25,
  'activity': 'Each group flips a coin 10 times and writes down heads; then pool the whole class’s results. Compare each group’s proportion with the class’s and discuss which group "stopped early".',
  'discussion': ['Which guardrail metric must the HR assistant not make worse?', 'Who decides the minimum effect worth having, and with what argument?'],
  'misconceptions': ['"We got p < 0.05 on day two, we can stop." Stopping at the first good look inflates false positives and the effect.', '"A high p proves there’s no difference." It may just be a small sample.']})


def build():
    write('05-testes-ab-de-prompt', s, loc('pt'), loc('en'), tch())
