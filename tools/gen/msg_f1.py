"""Mensageria e streaming · Fundamentos F1 · Por que filas existem (7 lições + missão).
Gera content/mensageria-e-streaming/fundamentos/NN-slug/{step,pt,en,teacher}.json. Rode com python3."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write as _write, flag, step

TOPIC, TRACK = 'mensageria-e-streaming', 'fundamentos'
def write(folder, s, pt, en, teacher): _write(TOPIC, TRACK, folder, s, pt, en, teacher)
def opt(id, pt, en): return {'id': id, 'pt': pt, 'en': en}
def loc(pt, en): return {'pt': pt, 'en': en}
SIM = ['simulado']
DOCKER = 'docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4-management'
def rabbit_steps(T):
  return [T(f'Com o Docker instalado, suba um RabbitMQ com o painel de gestão: {DOCKER}',
            f'With Docker installed, start RabbitMQ with the management UI: {DOCKER}'),
          T('Abra http://localhost:15672 no navegador e entre com guest / guest (esse usuário só funciona a partir da sua própria máquina, e é só para estudo).',
            'Open http://localhost:15672 in your browser and log in with guest / guest (that user only works from your own machine, and is for study only).')]
SLOTS = ['19:00', '19:10', '19:20', '19:30', '19:40', '19:50']

# ================================================================== 1 · síncrono × assíncrono
q = lambda i: f'q{i}'
s1 = step('msg-sincrono-assincrono', 1, TRACK, 15, ['mensageria', 'fila', 'assincrono', 'pico'], [], SIM,
  loc('atender', 'serve'),
  {'name': 'text', 'required': False, 'default': loc('1 calabresa grande', '1 large pepperoni'), 'ui': 'text'},
  [flag('mode', 'modo', 'mode', 'enum', options=[opt('async', 'assincrono', 'async'), opt('sync', 'sincrono', 'sync')], default='async', ui='select'),
   flag('peak', 'pico', 'peak', 'int', min=0, max=60, default=20, ui='slider'),
   flag('cooks', 'pizzaiolos', 'cooks', 'int', min=1, max=10, default=3, ui='slider')],
  {'options': ['lost', 'wait', 'faster'], 'answer': 'wait'}, 'ordersLost',
  {'live': True,
   'consts': {'calm': 4, 'prepMin': 15},
   'compute': {
     'cap': 'cooks * 4',
     'isAsync': "mode == 'async'",
     'q1': 'isAsync ? max(0, peak - cap) : 0',
     'q2': 'isAsync ? max(0, q1 + peak - cap) : 0',
     'q3': 'isAsync ? max(0, q2 + peak - cap) : 0',
     'q4': 'isAsync ? max(0, q3 + calm - cap) : 0',
     'q5': 'isAsync ? max(0, q4 + calm - cap) : 0',
     'q6': 'isAsync ? max(0, q5 + calm - cap) : 0',
     'x1': 'isAsync ? 0 : max(0, peak - cap)',
     'x4': 'isAsync ? 0 : max(0, calm - cap)',
     'lostN': '3 * x1 + 3 * x4',
     'maxQ': 'max(q1, q2, q3, q4, q5, q6)',
     'waitMin': 'isAsync ? ceil(maxQ / cap * 10) : 0',
     'answerText': "isAsync ? '2 s' : prepMin + ' min'"},
   'cases': [
     {'when': 'lostN > 0', 'flags': ['ordersLost']},
     {'when': 'isAsync && maxQ > 0', 'flags': ['queued']},
     {'when': 'q6 > 0', 'flags': ['neverDrains']},
     {'when': 'true', 'vars': {'lost': 'lostN', 'maxq': 'maxQ', 'wait': 'waitMin', 'cap': 'cap', 'left': 'q6'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@answer', 'value': '=answerText', 'tone': "=isAsync ? 'ok' : 'warn'"},
       {'label': '@lostM', 'value': '=lostN', 'format': 'int', 'tone': "=lostN > 0 ? 'bad' : 'dim'"},
       {'label': '@maxqM', 'value': '=maxQ', 'format': 'int', 'tone': "=maxQ > 0 ? 'info' : 'dim'"},
       {'label': '@waitM', 'value': '=waitMin', 'format': 'min', 'tone': "=waitMin > 30 ? 'warn' : 'dim'"}]},
     {'type': 'queue', 'when': '=isAsync', 'label': '@queueLabel', 'producer': '@phone', 'empty': '@emptyQueue',
      'messages': "=fill(q3, '#')",
      'consumers': [{'label': '@kitchen', 'note': '@capNote', 'tone': 'ok'}]},
     {'type': 'queue', 'when': '=!isAsync', 'label': '@lineLabel', 'producer': '@phone', 'empty': '@noQueue',
      'messages': [],
      'consumers': [{'label': '@kitchen', 'note': '@capNote', 'tone': "=lostN > 0 ? 'warn' : 'ok'"}],
      'dlq': "=fill(min(lostN, 30), '#')", 'dlqLabel': '@lostLabel'},
     {'type': 'chart', 'label': '@chart', 'kind': 'line', 'labels': SLOTS,
      'series': [{'label': '@chartQueue', 'values': '=[q1, q2, q3, q4, q5, q6]'},
                 {'label': '@chartLost', 'values': '=[x1, x1, x1, x4, x4, x4]'}]},
     {'type': 'note', 'when': '=lostN > 0', 'tone': 'bad', 'text': '@syncNote'},
     {'type': 'note', 'when': '=q6 > 0', 'tone': 'warn', 'text': '@drainNote'},
     {'type': 'note', 'when': '=isAsync && maxQ > 0 && q6 == 0', 'tone': 'ok', 'text': '@asyncNote'}]})

def loc1(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Síncrono × assíncrono', 'Sync vs async'),
  'subtitle': T('A pizzaria na sexta à noite: segurar o cliente no telefone ou anotar e avisar depois?', 'The pizzeria on Friday night: keep the customer on the phone, or write it down and call back?'),
  'mission': T('A Pizzaria da Nona recebe um pico de pedidos às 19h. A cozinha faz 4 pizzas a cada 10 minutos por pizzaiolo. Compare o atendimento síncrono (o cliente fica na linha até a pizza ficar pronta) com o assíncrono (anota o pedido numa fila e responde na hora).',
               'Nona’s Pizzeria gets a rush of orders at 7 pm. The kitchen makes 4 pizzas every 10 minutes per cook. Compare synchronous service (the customer stays on the line until the pizza is ready) with asynchronous (write the order into a queue and answer right away).'),
  'predict': {'question': T('no modo fila (assíncrono), com 20 pedidos a cada 10 minutos e uma cozinha que só faz 12, o que acontece com os pedidos que sobram?',
                            'in queue mode (async), with 20 orders every 10 minutes and a kitchen that only makes 12, what happens to the extra orders?'),
    'options': {'lost': T('Somem: a cozinha não dá conta', 'They vanish: the kitchen can’t keep up'),
                'wait': T('Esperam na fila e saem um pouco mais tarde', 'They wait in the queue and come out a bit later'),
                'faster': T('A cozinha fica mais rápida', 'The kitchen gets faster')}},
  'feedback': {'right': T('isso! A fila não faz a cozinha mais rápida: ela guarda o excesso do pico e a cozinha vai tirando no ritmo dela. Ninguém foi embora, só esperou mais um pouco.',
                          'right! The queue doesn’t make the kitchen faster: it holds the rush overflow and the kitchen works through it at its own pace. Nobody left, they just waited a bit more.'),
               'wrong': T('olhe o gráfico: a fila sobe no pico e desce quando o movimento acalma. A cozinha continua com o mesmo ritmo; a fila só guarda o que não coube.',
                          'look at the chart: the queue grows during the rush and shrinks when it calms down. The kitchen keeps the same pace; the queue only holds what didn’t fit.'),
               'skipped': T('sem palpite? Rode e olhe a linha da fila no gráfico: ela sobe e desce, e o contador de perdidos fica em zero.',
                            'no guess? Run it and watch the queue line in the chart: it rises and falls, and the lost counter stays at zero.')},
  'coach': {'ui': T('palpite anotado. Rode no modo assíncrono e depois troque para síncrono. Compare "pedidos perdidos".', 'guess noted. Run in async mode, then switch to sync. Compare "lost orders".'),
            'cmd': T('palpite anotado. Rode atender e depois atender --modo sincrono. Compare "pedidos perdidos".', 'guess noted. Run serve, then serve --mode sync. Compare "lost orders".')},
  'tryNext': {'ui': T('Agora deixe 2 pizzaiolos no modo assíncrono. A fila não zera até as 20h: fila guarda pico, mas não resolve falta de capacidade.',
                      'Now set 2 cooks in async mode. The queue doesn’t empty by 8 pm: a queue absorbs a peak, but it can’t fix missing capacity.'),
              'cmd': T('Rode atender --pizzaiolos 2 e veja o aviso de fila que não esvazia.', 'Run serve --cooks 2 and see the warning about a queue that never empties.')},
  'why': {'simples': T('Síncrono é o telefone: você liga, pede e fica esperando na linha até alguém resolver. Se a linha está ocupada, você desiste e liga para outra pizzaria.\nAssíncrono é a comanda: o atendente anota, diz "anotado, já sai!" e pendura o papel no varal da cozinha. O varal é a fila. Na hora do rush ele enche, mas nenhum pedido cai no chão, e a cozinha vai pegando um de cada vez.',
                       'Synchronous is the phone: you call, order and hold the line until someone sorts it out. If the line is busy, you give up and call another pizzeria.\nAsynchronous is the order ticket: the server writes it down, says "got it, coming up!" and clips the paper onto the kitchen rail. The rail is the queue. During the rush it fills up, but no order falls on the floor, and the kitchen takes one at a time.'),
          'dev': T('Numa chamada síncrona (HTTP, gRPC) quem chama fica esperando a resposta e depende de o outro lado estar de pé e com folga naquele instante. Se ele demora, os timeouts estouram em cascata.\nCom uma fila, o produtor publica a mensagem num broker (RabbitMQ, Kafka, Azure Service Bus, SQS) e segue a vida; o consumidor processa no ritmo dele. Você ganha três coisas: amortecer picos, isolar falhas (o consumidor pode cair e voltar) e escalar consumidores separado do produtor. O preço: a resposta vira "aceito, processando", e alguém precisa acompanhar o tamanho da fila.',
                   'In a synchronous call (HTTP, gRPC) the caller waits for the answer and depends on the other side being up and with room right at that moment. If it’s slow, timeouts cascade.\nWith a queue, the producer publishes a message to a broker (RabbitMQ, Kafka, Azure Service Bus, SQS) and moves on; the consumer processes at its own pace. You gain three things: absorbing peaks, isolating failures (the consumer can go down and come back) and scaling consumers apart from the producer. The price: the answer becomes "accepted, processing", and someone has to watch the queue length.'),
          'especialista': T('Fila é um amortecedor, não um multiplicador de capacidade: se a taxa média de chegada passa da taxa média de processamento, a fila cresce sem limite (é a lição do "--pizzaiolos 2"). Pela Lei de Little, itens na fila = taxa de chegada × tempo de espera; monitore profundidade e idade da mensagem mais velha, não só "a fila existe".\nDefina o que acontece quando a fila enche (limite de tamanho, rejeitar publicação, descartar a mais antiga) e o contrato com o usuário: um 202 Accepted com id para consultar o status, ou uma notificação quando terminar. Assíncrono também muda o modelo mental do time: erros deixam de aparecer na tela de quem pediu e passam a aparecer em métricas e alertas.',
                            'A queue is a shock absorber, not a capacity multiplier: if the average arrival rate exceeds the average processing rate, the queue grows without bound (that’s the "--cooks 2" lesson). By Little’s Law, items in the queue = arrival rate × waiting time; monitor depth and the age of the oldest message, not just "the queue exists".\nDecide what happens when the queue is full (length limit, reject publishes, drop the oldest) and the contract with the user: a 202 Accepted with an id to poll for status, or a notification when done. Async also changes the team’s mental model: errors stop showing up on the requester’s screen and start showing up in metrics and alerts.')},
  'break': {'mission': {'ui': T('hora de quebrar: troque o modo para síncrono e rode com o pico de 20 pedidos.', 'time to break it: switch the mode to sync and run with the rush of 20 orders.'),
                        'cmd': T('hora de quebrar: rode atender --modo sincrono', 'time to break it: run serve --mode sync')},
            'success': T('Quebrou: sem fila, a linha só aguenta {cap} pedidos a cada 10 minutos e {lost} clientes ouviram "ocupado" e foram pedir em outro lugar. A cozinha era a mesma; o que faltou foi onde esperar.',
                         'Broken: without a queue, the line only handles {cap} orders every 10 minutes and {lost} customers heard a busy signal and ordered somewhere else. Same kitchen; what was missing was a place to wait.'),
            'calm': T('Nenhum pedido perdido: no pico a fila chegou a {maxq} pedidos e a pior espera extra foi de {wait} min. Para quebrar, atenda sem fila.',
                      'No order lost: at the peak the queue reached {maxq} orders and the worst extra wait was {wait} min. To break it, serve without a queue.')},
  'hints': {'ui': T(['Mexa nos controles; a cena muda sozinha.', 'No modo síncrono, quem não cabe na capacidade da cozinha fica sem atendimento.', 'Escolha o modo síncrono com pico de 20 e 3 pizzaiolos.'],
                    ['Move the controls; the scene updates by itself.', 'In sync mode, whoever doesn’t fit in the kitchen’s capacity goes unserved.', 'Pick sync mode with a rush of 20 and 3 cooks.']),
            'cmd': T(['O pedido vai entre aspas; --modo, --pico e --pizzaiolos são opcionais.', '--modo aceita sincrono ou assincrono.', 'atender --modo sincrono'],
                     ['The order goes in quotes; --mode, --peak and --cooks are optional.', '--mode takes sync or async.', 'serve --mode sync'])},
  'errors': {'notInEnum.mode': T('Use sincrono ou assincrono.', 'Use sync or async.'),
             'aboveMax.peak': T('Até 60 pedidos a cada 10 minutos: mais que isso nem a Nona aguenta.', 'Up to 60 orders every 10 minutes: beyond that not even Nona can cope.'),
             'belowMin.peak': T('Pico negativo não existe (infelizmente para a cozinha).', 'There’s no negative rush (sadly for the kitchen).'),
             'belowMin.cooks': T('Sem pizzaiolo não sai pizza. Pelo menos 1.', 'No cook, no pizza. At least 1.'),
             'aboveMax.cooks': T('Até 10 pizzaiolos: a cozinha é pequena.', 'Up to 10 cooks: it’s a small kitchen.')},
  'controls': {'arg': T('Pedido de exemplo', 'Sample order'), 'mode': T('Modo de atendimento', 'Service mode'), 'peak': T('Pedidos a cada 10 min no pico', 'Orders per 10 min at the peak'), 'cooks': T('Pizzaiolos', 'Cooks')},
  'scene': {'label': T('Pizzaria da Nona, 19h às 20h', 'Nona’s Pizzeria, 7 to 8 pm'), 'empty': T('Rode para abrir a pizzaria.', 'Run to open the pizzeria.'),
    'answer': T('tempo até o cliente ouvir uma resposta', 'time until the customer hears back'), 'lostM': T('pedidos perdidos', 'lost orders'),
    'maxqM': T('pedidos na fila no pico', 'orders queued at the peak'), 'waitM': T('pior espera extra', 'worst extra wait'),
    'queueLabel': T('Varal de comandas (a fila)', 'Order rail (the queue)'), 'lineLabel': T('Telefone, sem fila', 'Phone, no queue'),
    'phone': T('telefone e app', 'phone and app'), 'kitchen': T('cozinha', 'kitchen'), 'capNote': T('{cap} pizzas / 10 min', '{cap} pizzas / 10 min'),
    'emptyQueue': T('fila vazia', 'empty queue'), 'noQueue': T('ninguém espera: ou atende, ou dá ocupado', 'nobody waits: either served or busy signal'),
    'lostLabel': T('desistiram', 'gave up'), 'chart': T('Fila e perdas a cada 10 minutos', 'Queue and losses every 10 minutes'),
    'chartQueue': T('pedidos esperando', 'orders waiting'), 'chartLost': T('pedidos perdidos', 'orders lost'),
    'syncNote': T('{lost} clientes ouviram "ocupado". No síncrono, capacidade que falta vira cliente perdido na hora.', '{lost} customers got a busy signal. In sync mode, missing capacity turns into lost customers on the spot.'),
    'drainNote': T('A fila não esvaziou até as 20h: ainda tem {left} pedidos esperando. Fila guarda pico, mas não cria capacidade.', 'The queue didn’t empty by 8 pm: {left} orders are still waiting. A queue holds a peak, but it doesn’t create capacity.'),
    'asyncNote': T('Todo mundo ouviu "anotado!" em 2 segundos. No pico a fila chegou a {maxq} e zerou quando o movimento acalmou.', 'Everyone heard "got it!" within 2 seconds. At the peak the queue reached {maxq} and drained when things calmed down.')},
  'data': {},
  'recipe': {'steps': rabbit_steps(T) + [
     T('Na aba Queues and Streams (nas versões mais antigas, só Queues), crie uma fila chamada pedidos. Abra a fila e use "Publish message" para publicar 5 mensagens, como "1 calabresa".', 'In the Queues and Streams tab (just Queues in older versions), create a queue named pedidos. Open it and use "Publish message" to publish 5 messages, like "1 pepperoni".'),
     T('Repare que ninguém está consumindo e mesmo assim os 5 pedidos foram aceitos. Depois abra "Get messages", em Ack Mode escolha "Automatic ack" e clique em "Get Message(s)": a fila cai para 4. (O padrão, "Nack message requeue true", devolve a mensagem para a fila, então o contador não mudaria.)', 'Notice nobody is consuming and the 5 orders were still accepted. Then open "Get messages", pick "Automatic ack" in Ack Mode and click "Get Message(s)": the queue drops to 4. (The default, "Nack message requeue true", puts the message back, so the counter wouldn’t change.)')],
   'ok': T('a fila pedidos mostra 5 mensagens prontas (Ready) sem nenhum consumidor ligado: o pedido foi aceito sem precisar da cozinha naquele instante.', 'the pedidos queue shows 5 ready messages with no consumer attached: the order was accepted without needing the kitchen at that moment.')}}

t1 = {'pt': {'objectives': ['Diferenciar chamada síncrona de mensagem assíncrona.', 'Ver a fila absorvendo um pico.', 'Entender que fila não cria capacidade.'], 'minutes': 15,
  'activity': 'Simulação na sala: um aluno é a cozinha e só "faz" uma pizza a cada 10 segundos. Primeiro os colegas fazem pedidos falando direto com ele (síncrono); depois, deixando papéis numa caixa (fila). Contem quantos pedidos se perdem em cada rodada.',
  'discussion': ['Onde você já esperou "na linha" quando podia ter recebido um aviso depois?', 'O que o cliente precisa saber quando o pedido foi só aceito, e não concluído?'],
  'misconceptions': ['"Fila deixa o sistema mais rápido." Ela deixa o sistema mais resistente a picos; a velocidade continua sendo a do consumidor.']},
 'en': {'objectives': ['Tell a synchronous call from an asynchronous message.', 'See a queue absorbing a peak.', 'Understand that a queue doesn’t create capacity.'], 'minutes': 15,
  'activity': 'Classroom simulation: one student is the kitchen and "makes" only one pizza every 10 seconds. First classmates order by talking to them directly (sync); then by dropping slips into a box (queue). Count how many orders are lost in each round.',
  'discussion': ['Where have you waited "on the line" when you could have been notified later?', 'What does a customer need to know when the order was only accepted, not finished?'],
  'misconceptions': ['"A queue makes the system faster." It makes the system resilient to peaks; speed is still the consumer’s.']}}
write('01-sincrono-e-assincrono', s1, loc1('pt'), loc1('en'), t1)

# ================================================================== 2 · comando × evento
SVC = [('kitchen', 'cozinha', 'kitchen'), ('invoice', 'nota', 'invoice'), ('loyalty', 'fidelidade', 'loyalty'), ('delivery', 'entrega', 'delivery')]
s2 = step('msg-comando-evento', 2, TRACK, 15, ['mensageria', 'evento', 'comando', 'acoplamento'], ['msg-sincrono-assincrono'], SIM,
  loc('anunciar', 'announce'),
  {'name': 'text', 'required': False, 'default': loc('PedidoPago', 'OrderPaid'), 'ui': 'examples',
   'examples': [loc('PedidoPago', 'OrderPaid'), loc('FazerPizza', 'MakePizza'), loc('EmitirNota', 'IssueInvoice')]},
  [flag('style', 'estilo', 'style', 'enum', options=[opt('event', 'evento', 'event'), opt('command', 'comando', 'command')], default='event', ui='select'),
   flag('services', 'servicos', 'services', 'list', options=[opt(a, b, c) for a, b, c in SVC], default=['kitchen', 'invoice'], ui='checkboxes')],
  {'options': ['zero', 'one', 'all'], 'answer': 'zero'}, 'coupled',
  {'live': True,
   'compute': {
     'n': 'len(services)',
     'isEvent': "style == 'event'",
     'sent': 'isEvent ? (n > 0 ? 1 : 0) : n',
     'knows': 'isEvent ? 0 : n',
     'changeNew': 'isEvent ? 0 : 1',
     'pastName': 'endsany(lower(text), pastEnds)',
     'nameMismatch': '(isEvent && !pastName) || (!isEvent && pastName)'},
   'cases': [
     {'when': 'n == 0', 'error': 'noServices'},
     {'when': '!isEvent && n >= 3', 'flags': ['coupled']},
     {'when': 'isEvent', 'flags': ['decoupled']},
     {'when': 'nameMismatch', 'flags': ['badName']},
     {'when': 'true', 'vars': {'n': 'n', 'sent': 'sent', 'knows': 'knows', 'change': 'changeNew'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@sentM', 'value': '=sent', 'format': 'int', 'tone': 'info'},
       {'label': '@knowsM', 'value': '=knows', 'format': 'int', 'tone': "=knows >= 3 ? 'bad' : (knows > 0 ? 'warn' : 'ok')"},
       {'label': '@changeM', 'value': '=changeNew', 'format': 'int', 'tone': "=changeNew > 0 ? 'warn' : 'ok'"}]},
     {'type': 'queue', 'label': "=isEvent ? '@busLabel' : '@directLabel'", 'producer': '@cashier',
      'messages': "=fill(sent, (isEvent ? '+' : '?') + text)",
      'consumers': [{'label': '@' + a, 'note': f"=includes(services, '{a}') ? (isEvent ? '@listens' : '@ordered') : '@off'",
                     'tone': f"=includes(services, '{a}') ? 'ok' : 'dim'"} for a, _, _ in SVC]},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['@aspect', '@command', '@event'],
      'rows': [['@rWho', '@cWho', '@eWho'], ['@rName', '@cName', '@eName'], ['@rTo', '@cTo', '@eTo'], ['@rNo', '@cNo', '@eNo']],
      'tones': ['neutral', 'neutral', "=isEvent ? 'ok' : 'warn'", 'neutral']},
     {'type': 'note', 'when': '=nameMismatch', 'tone': 'warn', 'text': "=isEvent ? '@nameEvent' : '@nameCommand'"},
     {'type': 'note', 'when': '=!isEvent && n >= 3', 'tone': 'bad', 'text': '@coupledNote'}]})

def loc2(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Comando × evento', 'Command vs event'),
  'subtitle': T('"Faça a pizza!" ou "o pedido foi pago"? A diferença muda quem manda em quem', '"Make the pizza!" or "the order was paid"? The difference changes who depends on whom'),
  'mission': T('Quando um pedido é pago, o caixa da Nona precisa avisar a cozinha, a nota fiscal e, em breve, o programa de fidelidade. Compare mandar uma ordem para cada um (comando) com anunciar o que aconteceu (evento) e ver quantas vezes o caixa precisa mudar.',
               'When an order is paid, Nona’s cashier has to tell the kitchen, invoicing and, soon, the loyalty program. Compare sending an order to each one (command) with announcing what happened (event) and see how often the cashier has to change.'),
  'predict': {'question': T('no estilo evento, se a pizzaria ligar o programa de fidelidade, quantas mudanças o código do caixa precisa?', 'in event style, if the pizzeria turns on the loyalty program, how many changes does the cashier’s code need?'),
    'options': {'zero': T('Nenhuma', 'None'), 'one': T('Uma', 'One'), 'all': T('Uma por serviço que já existia', 'One per service that already existed')}},
  'feedback': {'right': T('isso: o caixa só anuncia "PedidoPago". Quem quiser saber se inscreve. A fidelidade chega, se inscreve, e o caixa nem fica sabendo.', 'right: the cashier just announces "OrderPaid". Whoever cares subscribes. Loyalty shows up, subscribes, and the cashier never even finds out.'),
               'wrong': T('é nenhuma. Com evento, o caixa não conhece quem escuta: a fidelidade se inscreve sozinha. Com comando, aí sim, o caixa precisa ser alterado para mandar mais uma ordem.', 'it’s none. With an event, the cashier doesn’t know who listens: loyalty subscribes on its own. With commands, then yes, the cashier must be changed to send one more order.'),
               'skipped': T('sem palpite? Marque fidelidade no estilo evento e olhe "mudanças no caixa".', 'no guess? Tick loyalty in event style and look at "changes to the cashier".')},
  'coach': {'ui': T('palpite anotado. Marque fidelidade e alterne entre evento e comando.', 'guess noted. Tick loyalty and switch between event and command.'),
            'cmd': T('palpite anotado. Rode anunciar --servicos cozinha,nota,fidelidade e depois o mesmo com --estilo comando.', 'guess noted. Run announce --services kitchen,invoice,loyalty and then the same with --style command.')},
  'tryNext': {'ui': T('Troque o nome para "FazerPizza" no estilo evento: o aviso diz que isso tem cara de ordem, não de fato.', 'Change the name to "MakePizza" in event style: the warning says it looks like an order, not a fact.'),
              'cmd': T('Rode anunciar "FazerPizza" e leia o aviso sobre o nome.', 'Run announce "MakePizza" and read the warning about the name.')},
  'why': {'simples': T('Comando é uma ordem para alguém específico: "Zé, faz uma calabresa!". O Zé pode fazer ou dizer que acabou a calabresa.\nEvento é uma notícia: "o pedido 42 foi pago!", gritada para a pizzaria toda. Quem se importa reage: a cozinha começa a pizza, a nota fiscal é emitida, o cartão fidelidade ganha um carimbo. Quem gritou não precisa saber quem ouviu.',
                       'A command is an order to someone specific: "Joe, make a pepperoni!". Joe can do it or say they’re out of pepperoni.\nAn event is news: "order 42 was paid!", shouted to the whole pizzeria. Whoever cares reacts: the kitchen starts the pizza, the invoice is issued, the loyalty card gets a stamp. Whoever shouted doesn’t need to know who heard.'),
          'dev': T('Comando: verbo no imperativo (EmitirNota), um destinatário que é dono da decisão, pode ser recusado e normalmente vai para uma fila daquele serviço. Evento: fato no passado (PedidoPago), imutável, publicado por quem é dono do fato e entregue a zero ou mais assinantes.\nUse comando quando você precisa que uma coisa específica seja feita; use evento quando outros podem querer reagir a algo que já aconteceu. Misturar os dois ("evento" PedidoPagoEnviarEmail) recria o acoplamento que você tentou evitar.',
                   'Command: imperative verb (IssueInvoice), one recipient that owns the decision, can be rejected and usually goes to that service’s queue. Event: a past-tense fact (OrderPaid), immutable, published by whoever owns the fact and delivered to zero or more subscribers.\nUse a command when you need one specific thing done; use an event when others may want to react to something that already happened. Mixing both (an "event" called OrderPaidSendEmail) brings back the coupling you were trying to avoid.'),
          'especialista': T('Evento desacopla no tempo e na dependência, mas não no contrato: o formato do PedidoPago vira API pública, com versionamento e compatibilidade (adicionar campo opcional é seguro; renomear quebra todos os assinantes). Decida entre evento "magro" (só ids, quem precisa consulta) e "gordo" (carrega o estado; menos chamadas, mais acoplamento ao formato).\nComo ninguém orquestra, o fluxo fica implícito: rastreie com id de correlação e tracing distribuído. Quando o processo precisa de ordem e compensação (pagar, reservar, entregar), compare coreografia por eventos com orquestração por comandos (saga), assunto da trilha Prática.',
                            'An event decouples in time and dependency, but not in contract: the OrderPaid format becomes a public API, with versioning and compatibility (adding an optional field is safe; renaming breaks every subscriber). Choose between "thin" events (ids only, whoever needs more queries) and "fat" ones (carry state; fewer calls, more coupling to the format).\nSince nobody orchestrates, the flow becomes implicit: trace it with a correlation id and distributed tracing. When the process needs ordering and compensation (pay, reserve, deliver), compare choreography with events against orchestration with commands (saga), a Practice track topic.')},
  'break': {'mission': {'ui': T('hora de quebrar: estilo comando com cozinha, nota e fidelidade marcadas.', 'time to break it: command style with kitchen, invoice and loyalty ticked.'),
                        'cmd': T('hora de quebrar: rode anunciar --estilo comando --servicos cozinha,nota,fidelidade', 'time to break it: run announce --style command --services kitchen,invoice,loyalty')},
            'success': T('Quebrou: o caixa agora conhece {knows} serviços pelo nome e manda {sent} mensagens. Cada serviço novo é mais uma mudança no caixa, e se um deles estiver fora, o caixa precisa decidir o que fazer.',
                         'Broken: the cashier now knows {knows} services by name and sends {sent} messages. Every new service is one more change to the cashier, and if one of them is down, the cashier has to decide what to do.'),
            'calm': T('{n} serviços atendidos com {sent} mensagem(ns), e o caixa conhece {knows} deles pelo nome. Para quebrar, mande comandos para 3 serviços.',
                      '{n} services served with {sent} message(s), and the cashier knows {knows} of them by name. To break it, send commands to 3 services.')},
  'hints': {'ui': T(['Escolha o estilo e marque os serviços interessados.', 'Olhe "serviços que o caixa conhece": é o acoplamento.', 'Estilo comando, com cozinha, nota e fidelidade.'],
                    ['Pick the style and tick the interested services.', 'Watch "services the cashier knows": that’s the coupling.', 'Command style, with kitchen, invoice and loyalty.']),
            'cmd': T(['O nome da mensagem vai entre aspas; --estilo e --servicos são opcionais.', '--servicos aceita uma lista separada por vírgula: cozinha,nota,fidelidade,entrega.', 'anunciar --estilo comando --servicos cozinha,nota,fidelidade'],
                     ['The message name goes in quotes; --style and --services are optional.', '--services takes a comma-separated list: kitchen,invoice,loyalty,delivery.', 'announce --style command --services kitchen,invoice,loyalty'])},
  'errors': {'notInEnum.style': T('Use evento ou comando.', 'Use event or command.'),
             'notInEnum.services': T('Os serviços são cozinha, nota, fidelidade e entrega.', 'The services are kitchen, invoice, loyalty and delivery.'),
             'model.noServices': T('Ninguém interessado? Então nem precisa de mensagem. Marque pelo menos um serviço.', 'Nobody interested? Then you don’t even need a message. Tick at least one service.')},
  'controls': {'arg': T('Nome da mensagem', 'Message name'), 'style': T('Estilo', 'Style'), 'services': T('Serviços interessados', 'Interested services')},
  'scene': {'label': T('Caixa da Nona', 'Nona’s cashier'), 'empty': T('Rode para anunciar.', 'Run to announce.'),
    'sentM': T('mensagens que o caixa envia', 'messages the cashier sends'), 'knowsM': T('serviços que o caixa conhece', 'services the cashier knows'), 'changeM': T('mudanças no caixa por serviço novo', 'cashier changes per new service'),
    'busLabel': T('Evento publicado uma vez, entregue a quem assinou', 'Event published once, delivered to subscribers'), 'directLabel': T('Um comando para cada serviço', 'One command per service'),
    'cashier': T('caixa', 'cashier'), 'kitchen': T('cozinha', 'kitchen'), 'invoice': T('nota fiscal', 'invoicing'), 'loyalty': T('fidelidade', 'loyalty'), 'delivery': T('entrega', 'delivery'),
    'listens': T('assinou o evento', 'subscribed'), 'ordered': T('recebe ordem do caixa', 'gets an order from the cashier'), 'off': T('não participa', 'not involved'),
    'tableLabel': T('Comando × evento', 'Command vs event'), 'aspect': T('aspecto', 'aspect'), 'command': T('comando', 'command'), 'event': T('evento', 'event'),
    'rWho': T('quem decide', 'who decides'), 'cWho': T('quem envia manda fazer', 'the sender asks for it'), 'eWho': T('cada assinante decide o que fazer', 'each subscriber decides'),
    'rName': T('nome', 'name'), 'cName': T('verbo no imperativo: EmitirNota', 'imperative verb: IssueInvoice'), 'eName': T('fato no passado: PedidoPago', 'past-tense fact: OrderPaid'),
    'rTo': T('destinatários', 'recipients'), 'cTo': T('exatamente um', 'exactly one'), 'eTo': T('zero, um ou muitos', 'zero, one or many'),
    'rNo': T('pode ser recusado?', 'can it be refused?'), 'cNo': T('sim ("acabou a calabresa")', 'yes ("out of pepperoni")'), 'eNo': T('não: já aconteceu', 'no: it already happened'),
    'nameEvent': T('"{text}" soa como ordem. Evento é fato no passado: PedidoPago, PizzaSaiuDoForno.', '"{text}" sounds like an order. An event is a past-tense fact: OrderPaid, PizzaLeftTheOven.'),
    'nameCommand': T('"{text}" soa como fato. Comando é um pedido no imperativo: FazerPizza, EmitirNota.', '"{text}" sounds like a fact. A command is an imperative request: MakePizza, IssueInvoice.'),
    'coupledNote': T('O caixa virou o "chefe de todo mundo": conhece {knows} serviços e quebra se qualquer um mudar de endereço ou de formato.', 'The cashier became "everyone’s boss": it knows {knows} services and breaks if any of them changes address or format.')},
  'data': {'pastEnds': ['ado', 'ido', 'pago', 'feito', 'aceito', 'emitida', 'emitido', 'entregue'] if pt else ['ed', 'paid', 'done', 'sent', 'made', 'shipped']},
  'recipe': {'steps': [
     T('Pegue um sistema que você conhece (o da escola, da loja, do trabalho) e liste 6 mensagens que ele troca ou poderia trocar.', 'Take a system you know (school, shop, work) and list 6 messages it exchanges or could exchange.'),
     T('Para cada uma, escreva: é comando ou evento? Quem é o dono? Quantos interessados tem?', 'For each one, write: command or event? Who owns it? How many interested parties?'),
     T('Renomeie: comandos no imperativo (EmitirNota), eventos no passado (PedidoPago). Se algum "evento" tem um único interessado e manda ele fazer algo, provavelmente é um comando disfarçado.', 'Rename: commands in the imperative (IssueInvoice), events in the past tense (OrderPaid). If some "event" has a single interested party and tells it to do something, it’s probably a disguised command.')],
   'ok': T('cada mensagem da lista tem um nome que já diz se é ordem ou fato, e os eventos não citam quem vai recebê-los.', 'every message on the list has a name that already says whether it’s an order or a fact, and the events don’t mention who will receive them.')}}

t2 = {'pt': {'objectives': ['Diferenciar comando de evento.', 'Ver como evento reduz o acoplamento do produtor.', 'Dar nomes que deixam a intenção clara.'], 'minutes': 15,
  'activity': 'Um aluno é o caixa. Rodada 1: ele entrega um bilhete com ordem para cada colega-serviço. Rodada 2: ele escreve o fato no quadro e cada um decide o que fazer. Entra um "serviço novo" no meio: em qual rodada o caixa precisou mudar?',
  'discussion': ['Que eventos a sua escola ou empresa "grita" sem saber quem escuta?', 'Quando é melhor um comando, mesmo com o acoplamento?'],
  'misconceptions': ['"Evento e mensagem são a mesma coisa." Mensagem é o envelope; comando e evento são intenções diferentes que viajam nele.']},
 'en': {'objectives': ['Tell a command from an event.', 'See how events reduce producer coupling.', 'Pick names that make intent clear.'], 'minutes': 15,
  'activity': 'One student is the cashier. Round 1: they hand an order slip to each classmate-service. Round 2: they write the fact on the board and everyone decides what to do. A "new service" joins halfway: in which round did the cashier have to change?',
  'discussion': ['What events does your school or company "shout" without knowing who listens?', 'When is a command better, coupling and all?'],
  'misconceptions': ['"Event and message are the same thing." The message is the envelope; command and event are different intents that travel in it.']}}
write('02-comando-e-evento', s2, loc2('pt'), loc2('en'), t2)

# ================================================================== 3 · garantias de entrega e ack
s3 = step('msg-ack-e-garantias', 3, TRACK, 20, ['mensageria', 'ack', 'at-least-once', 'at-most-once', 'rabbitmq'], ['msg-sincrono-assincrono'], SIM,
  loc('cozinhar', 'cook'),
  {'name': 'text', 'required': False, 'default': loc('pedidos', 'pedidos'), 'ui': 'text'},
  [flag('ack', 'ack', 'ack', 'enum', options=[opt('manual', 'manual', 'manual'), opt('auto', 'auto', 'auto')], default='manual', ui='select'),
   flag('crash', 'falha', 'crash', 'int', min=1, max=10, default=4, ui='slider')],
  {'options': ['lost', 'back', 'stuck'], 'answer': 'back'}, 'ordersLost',
  {'live': True,
   'consts': {'taken': 10, 'queued': 20},
   'compute': {
     'crashed': 'crash < 10',
     'isManual': "ack == 'manual'",
     'lostN': '!isManual && crashed ? taken - crash : 0',
     'backN': 'isManual && crashed ? taken - crash + 1 : 0',
     'dupN': 'isManual && crashed ? 1 : 0',
     'ackedN': 'isManual ? (crashed ? crash - 1 : taken) : taken',
     'unackedBefore': 'isManual ? taken : 0',
     'readyAfter': 'queued + backN'},
   'cases': [
     {'when': 'lostN > 0', 'flags': ['ordersLost']},
     {'when': 'backN > 0', 'flags': ['redelivered']},
     {'when': 'dupN > 0', 'flags': ['duplicate']},
     {'when': 'true', 'vars': {'lost': 'lostN', 'back': 'backN', 'dup': 'dupN', 'k': 'crash', 'acked': 'ackedN', 'queue': 'text'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@lostM', 'value': '=lostN', 'format': 'int', 'tone': "=lostN > 0 ? 'bad' : 'dim'"},
       {'label': '@backM', 'value': '=backN', 'format': 'int', 'tone': "=backN > 0 ? 'warn' : 'dim'"},
       {'label': '@dupM', 'value': '=dupN', 'format': 'int', 'tone': "=dupN > 0 ? 'warn' : 'dim'"},
       {'label': '@ackedM', 'value': '=ackedN', 'format': 'int', 'tone': 'info'}]},
     {'type': 'queue', 'label': '@queueLabel', 'producer': '@counter',
      'messages': "=concat(fill(backN, '?↺'), fill(queued, '#'))",
      'consumers': [{'label': 'worker-1', 'note': "=crashed ? '@crashedNote' : '@fineNote'", 'tone': "=crashed ? 'bad' : 'ok'"},
                    {'label': 'worker-2', 'note': "=backN > 0 ? '@takesOver' : '@waiting'", 'tone': 'ok'}],
      'dlq': "=fill(lostN, '#')", 'dlqLabel': '@lostLabel'},
     {'type': 'terminal', 'label': '@terminal', 'lines': [
       '$ rabbitmqctl list_queues name messages_ready messages_unacknowledged',
       'Listing queues for vhost / ...',
       'name   messages_ready   messages_unacknowledged',
       '@before',
       "='  ' + text + '   ' + queued + '   ' + unackedBefore",
       "=crashed ? '@after' : '@noCrash'",
       "=(lostN > 0 ? '!' : '+') + ' ' + text + '   ' + readyAfter + '   0'"]},
     {'type': 'note', 'when': '=lostN > 0', 'tone': 'bad', 'text': '@lostNote'},
     {'type': 'note', 'when': '=dupN > 0', 'tone': 'warn', 'text': '@dupNote'}]})

def loc3(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Garantias de entrega e ack', 'Delivery guarantees and acks'),
  'subtitle': T('O "ok, terminei" que decide se um pedido some ou volta para a fila', 'The "ok, done" that decides whether an order vanishes or goes back to the queue'),
  'mission': T('O worker-1 da cozinha pegou 10 comandas de uma vez e caiu no meio do serviço (alguém tropeçou no cabo). Descubra o que acontece com as comandas que estavam na mão dele quando o "ok" (ack) é automático e quando é manual.',
               'Kitchen worker-1 grabbed 10 tickets at once and crashed mid-shift (someone tripped over the cable). Find out what happens to the tickets in its hands when the "ok" (ack) is automatic and when it’s manual.'),
  'predict': {'question': T('com ack manual, o worker-1 cai depois de terminar a pizza 4. O que acontece com as comandas que ele tinha pegado e não confirmou?', 'with manual ack, worker-1 crashes right after finishing pizza 4. What happens to the tickets it had taken and not confirmed?'),
    'options': {'lost': T('Somem junto com o worker', 'They vanish with the worker'), 'back': T('Voltam para a fila, e uma pode sair repetida', 'They go back to the queue, and one may be made twice'), 'stuck': T('Ficam presas para sempre', 'They’re stuck forever')}},
  'feedback': {'right': T('na mosca: o broker só apaga a mensagem quando recebe o ack. O worker caiu, a conexão fechou, e as 7 sem ack voltaram para a fila. A pizza 4 já tinha saído do forno mas o "ok" não chegou: ela vai ser feita de novo.', 'spot on: the broker only deletes a message when it gets the ack. The worker crashed, the connection closed, and the 7 unacked ones went back to the queue. Pizza 4 had left the oven but its "ok" never arrived: it will be made again.'),
               'wrong': T('elas voltam: com ack manual, mensagem sem confirmação continua sendo do broker. Quando a conexão do worker cai, o RabbitMQ devolve todas para a fila, marcadas como reentrega. Nada se perde, mas a pizza 4 sai em dobro.', 'they go back: with manual ack, an unconfirmed message still belongs to the broker. When the worker’s connection drops, RabbitMQ requeues them all, flagged as redelivered. Nothing is lost, but pizza 4 is made twice.'),
               'skipped': T('sem palpite? Rode e olhe a fila: as comandas com ↺ são as que voltaram.', 'no guess? Run it and look at the queue: tickets marked ↺ are the ones that came back.')},
  'coach': {'ui': T('palpite anotado. Rode com ack manual, depois troque para automático e compare "comandas perdidas".', 'guess noted. Run with manual ack, then switch to automatic and compare "lost tickets".'),
            'cmd': T('palpite anotado. Rode cozinhar e depois cozinhar --ack auto. Compare "comandas perdidas".', 'guess noted. Run cook and then cook --ack auto. Compare "lost tickets".')},
  'tryNext': {'ui': T('Leve a falha para 10 (o worker não cai): os dois modos empatam. A diferença só aparece quando algo dá errado, e é por isso que ela engana.', 'Move the crash to 10 (the worker doesn’t crash): both modes tie. The difference only shows when something goes wrong, which is why it fools people.'),
              'cmd': T('Rode cozinhar --ack auto --falha 10 e compare com --falha 4.', 'Run cook --ack auto --crash 10 and compare with --crash 4.')},
  'why': {'simples': T('Quando a cozinha pega uma comanda, ela pode avisar "peguei" na hora (ack automático) ou só "terminei" quando a pizza sai (ack manual).\nSe o pizzaiolo desmaia com 10 comandas no bolso: no automático, o balcão acha que estava tudo certo e esses pedidos somem. No manual, o balcão percebe que ninguém disse "terminei" e devolve as comandas para o varal. O efeito colateral: a pizza que ficou pronta bem na hora do desmaio vai ser feita de novo.',
                       'When the kitchen takes a ticket, it can say "got it" right away (automatic ack) or "done" only when the pizza is out (manual ack).\nIf the cook faints with 10 tickets in their pocket: with automatic, the counter thinks everything was fine and those orders vanish. With manual, the counter notices nobody said "done" and puts the tickets back on the rail. The side effect: the pizza that was finished right at the moment of fainting gets made again.'),
          'dev': T('No RabbitMQ (AMQP 0-9-1), o consumidor escolhe o modo. Automático: a mensagem conta como entregue assim que sai do broker; a documentação chama isso de inseguro, porque se a conexão cair antes de você processar, perdeu. Manual: você chama basic.ack depois de processar; basic.nack ou basic.reject devolvem (requeue=true) ou descartam/mandam para DLX (requeue=false).\nSe o canal ou a conexão fecham com mensagens sem ack, elas voltam para a fila e são reentregues com a marca redelivered. Isso dá as famosas garantias: ack antes de processar (ou automático) = no máximo uma vez (at-most-once, pode perder); ack depois de processar = pelo menos uma vez (at-least-once, pode repetir).',
                   'In RabbitMQ (AMQP 0-9-1) the consumer picks the mode. Automatic: the message counts as delivered as soon as it leaves the broker; the docs call this unsafe, because if the connection drops before you process it, it’s gone. Manual: you call basic.ack after processing; basic.nack or basic.reject either requeue (requeue=true) or discard/dead-letter (requeue=false).\nIf the channel or connection closes with unacked messages, they go back to the queue and are redelivered with the redelivered flag. That gives the famous guarantees: ack before processing (or automatic) = at-most-once (may lose); ack after processing = at-least-once (may repeat).'),
          'especialista': T('Ack do consumidor é metade da história. A outra é o produtor: sem publisher confirms, uma mensagem persistente pode se perder se o broker cair antes de gravá-la; com confirms, o broker responde basic.ack quando todas as filas de destino aceitaram (para quorum queues, quando a maioria das réplicas aceitou). E fila durável não torna a mensagem persistente: isso é por mensagem.\nO RabbitMQ também tem um tempo limite de ack (consumer_timeout, 30 minutos por padrão): um consumidor que segura uma mensagem sem confirmar por mais que isso tem o canal fechado. No Kafka a mesma escolha aparece como "quando fazer commit do offset": antes de processar dá at-most-once, depois dá at-least-once, e a documentação diz que o padrão do Kafka é at-least-once. "Exactly-once" de ponta a ponta exige que o efeito e o progresso sejam gravados juntos, assunto das próximas lições.',
                            'Consumer acks are half the story. The other half is the producer: without publisher confirms, a persistent message can be lost if the broker fails before writing it; with confirms, the broker replies basic.ack once all target queues accepted it (for quorum queues, once a majority of replicas did). And a durable queue doesn’t make messages persistent: that’s per message.\nRabbitMQ also has an ack timeout (consumer_timeout, 30 minutes by default): a consumer that holds a message unacked longer than that gets its channel closed. In Kafka the same choice shows up as "when to commit the offset": before processing gives at-most-once, after gives at-least-once, and the docs say Kafka’s default is at-least-once. End-to-end "exactly-once" requires the effect and the progress to be stored together, the subject of the next lessons.')},
  'break': {'mission': {'ui': T('hora de quebrar: troque o ack para automático com a falha em 4.', 'time to break it: switch the ack to automatic with the crash at 4.'),
                        'cmd': T('hora de quebrar: rode cozinhar --ack auto', 'time to break it: run cook --ack auto')},
            'success': T('Quebrou: no ack automático o broker já tinha dado as 10 comandas como entregues. O worker caiu depois da pizza {k} e {lost} pedidos sumiram sem deixar rastro: nem na fila, nem em lugar nenhum.',
                         'Broken: with automatic ack the broker had already marked all 10 tickets as delivered. The worker crashed after pizza {k} and {lost} orders vanished without a trace: not in the queue, not anywhere.'),
            'calm': T('Nenhuma comanda perdida: {back} voltaram para a fila e {dup} vai sair repetida. Isso é at-least-once. Para quebrar, use ack automático.',
                      'No ticket lost: {back} went back to the queue and {dup} will be made twice. That’s at-least-once. To break it, use automatic ack.')},
  'hints': {'ui': T(['Escolha o modo de ack e em que pizza o worker cai.', '"Comandas perdidas" só passa de zero num dos modos.', 'Ack automático, falha em 4.'],
                    ['Pick the ack mode and at which pizza the worker crashes.', '"Lost tickets" only goes above zero in one of the modes.', 'Automatic ack, crash at 4.']),
            'cmd': T(['O nome da fila vai entre aspas; --ack e --falha são opcionais.', '--ack aceita manual ou auto; --falha vai de 1 a 10 (10 = não cai).', 'cozinhar --ack auto'],
                     ['The queue name goes in quotes; --ack and --crash are optional.', '--ack takes manual or auto; --crash goes from 1 to 10 (10 = no crash).', 'cook --ack auto'])},
  'errors': {'notInEnum.ack': T('Use manual ou auto.', 'Use manual or auto.'),
             'belowMin.crash': T('O worker termina pelo menos a primeira pizza antes de cair. Use de 1 a 10.', 'The worker finishes at least the first pizza before crashing. Use 1 to 10.'),
             'aboveMax.crash': T('Ele só pegou 10 comandas. Use 10 para "não cai".', 'It only took 10 tickets. Use 10 for "no crash".')},
  'controls': {'arg': T('Fila', 'Queue'), 'ack': T('Modo de ack', 'Ack mode'), 'crash': T('Worker cai depois da pizza nº (10 = não cai)', 'Worker crashes after pizza no. (10 = no crash)')},
  'scene': {'label': T('Cozinha com 2 workers', 'Kitchen with 2 workers'), 'empty': T('Rode para abrir a cozinha.', 'Run to open the kitchen.'),
    'lostM': T('comandas perdidas', 'lost tickets'), 'backM': T('voltaram para a fila', 'back in the queue'), 'dupM': T('pizzas que saem em dobro', 'pizzas made twice'), 'ackedM': T('acks registrados', 'acks recorded'),
    'queueLabel': T('Fila depois da queda (↺ = reentrega)', 'Queue after the crash (↺ = redelivery)'), 'counter': T('balcão', 'counter'),
    'crashedNote': T('caiu depois da pizza {k}', 'crashed after pizza {k}'), 'fineNote': T('fez as 10 e confirmou', 'made all 10 and acked'),
    'takesOver': T('pega as devolvidas', 'picks up the returned ones'), 'waiting': T('esperando', 'waiting'), 'lostLabel': T('perdidas', 'lost'),
    'terminal': T('O que o broker mostra', 'What the broker shows'), 'before': T('~# com o worker-1 segurando 10 comandas', '~# with worker-1 holding 10 tickets'),
    'after': T('~# depois da queda do worker-1', '~# after worker-1 crashed'), 'noCrash': T('~# depois que o worker-1 terminou', '~# after worker-1 finished'),
    'lostNote': T('No ack automático o broker não guarda nada do que entregou: {lost} pedidos sumiram. Ninguém vai perceber até o cliente ligar bravo.', 'With automatic ack the broker keeps nothing it delivered: {lost} orders vanished. Nobody will notice until an angry customer calls.'),
    'dupNote': T('A pizza {k} saiu do forno, mas o worker caiu antes de dizer "terminei". Ela volta para a fila e vai ser feita de novo. Na próxima lição a gente resolve isso.', 'Pizza {k} left the oven, but the worker crashed before saying "done". It goes back to the queue and will be made again. Next lesson we fix that.')},
  'data': {},
  'recipe': {'steps': rabbit_steps(T) + [
     T('Crie a fila pedidos e publique 10 mensagens pelo painel. Instale o cliente Python: pip install pika', 'Create the pedidos queue and publish 10 messages from the UI. Install the Python client: pip install pika'),
     T('Crie o arquivo worker.py com exatamente este conteúdo (o corpo do callback tem 4 espaços de indentação; o basic_consume fica fora dele, sem indentação):\nimport pika, time\nconn = pika.BlockingConnection(pika.ConnectionParameters("localhost"))\nch = conn.channel()\nch.basic_qos(prefetch_count=10)\ndef faz(ch, m, p, body):\n    print("fazendo", body)\n    time.sleep(3)\n    ch.basic_ack(delivery_tag=m.delivery_tag)\nch.basic_consume(queue="pedidos", on_message_callback=faz, auto_ack=False)\nch.start_consuming()',
       'Create a file worker.py with exactly this content (the callback body is indented 4 spaces; basic_consume sits outside it, unindented):\nimport pika, time\nconn = pika.BlockingConnection(pika.ConnectionParameters("localhost"))\nch = conn.channel()\nch.basic_qos(prefetch_count=10)\ndef work(ch, m, p, body):\n    print("making", body)\n    time.sleep(3)\n    ch.basic_ack(delivery_tag=m.delivery_tag)\nch.basic_consume(queue="pedidos", on_message_callback=work, auto_ack=False)\nch.start_consuming()'),
     T('Rode python worker.py e, no meio, aperte Ctrl+C. Olhe a fila no painel. Depois repita com auto_ack=True (tirando a linha do basic_ack).', 'Run python worker.py and press Ctrl+C halfway. Look at the queue in the UI. Then repeat with auto_ack=True (removing the basic_ack line).')],
   'ok': T('com auto_ack=False, as mensagens que estavam em "Unacked" voltam para "Ready" quando o worker morre; com auto_ack=True, elas somem da fila.', 'with auto_ack=False, the messages in "Unacked" go back to "Ready" when the worker dies; with auto_ack=True, they disappear from the queue.')}}

t3 = {'pt': {'objectives': ['Explicar o que é um ack.', 'Diferenciar at-most-once de at-least-once.', 'Prever perda ou duplicata a partir do momento do ack.'], 'minutes': 20,
  'activity': 'Jogo da comanda: um aluno é o broker e guarda uma cópia de cada comanda até ouvir "terminei". Outro é o pizzaiolo e "desmaia" quando o professor bater palma. Rodem com e sem cópia e contem perdas e repetições.',
  'discussion': ['Em que sistema é melhor perder do que repetir? E repetir do que perder?', 'Por que o "exactly-once" de fábrica é uma promessa difícil?'],
  'misconceptions': ['"Se a fila é durável, nada se perde." Durabilidade não ajuda se o consumidor confirmou antes de processar.']},
 'en': {'objectives': ['Explain what an ack is.', 'Tell at-most-once from at-least-once.', 'Predict loss or duplicates from when the ack happens.'], 'minutes': 20,
  'activity': 'Ticket game: one student is the broker and keeps a copy of each ticket until they hear "done". Another is the cook and "faints" when the teacher claps. Play with and without copies and count losses and repeats.',
  'discussion': ['In which system is it better to lose than to repeat? And to repeat than to lose?', 'Why is out-of-the-box "exactly-once" a hard promise?'],
  'misconceptions': ['"If the queue is durable, nothing is lost." Durability doesn’t help if the consumer acked before processing.']}}
write('03-garantias-e-ack', s3, loc3('pt'), loc3('en'), t3)

# ================================================================== 4 · consumidor idempotente
DELIV = [('m1', 'P101', 'first'), ('m2', 'P102', 'first'), ('m3', 'P103', 'first'), ('m2', 'P102', 'redelivery'), ('m4', 'P104', 'first'), ('m5', 'P105', 'first'),
         ('m9', 'P105', 'resend'), ('m6', 'P106', 'first'), ('m7', 'P107', 'first'), ('m7', 'P107', 'redelivery'), ('m8', 'P108', 'first')]
CRASH_ROW = 1  # sem transação: credita P102 e cai antes de guardar a chave
def dedup(key, tx):
  seen, res, tones = set(), [], []
  for i, (mid, oid, kind) in enumerate(DELIV):
    k = None if key == 'none' else (mid if key == 'message' else oid)
    if k is not None and k in seen: res.append('@skipped'); tones.append('dim'); continue
    res.append('@credited'); tones.append('neutral' if kind == 'first' else 'bad')
    if k is not None and (tx or i != CRASH_ROW): seen.add(k)
  return res, tones
RES, TONES = {}, {}
for key in ('none', 'message', 'order'):
  for tx in (True, False):
    r, t = dedup(key, tx); RES[f'{key}-{"tx" if tx else "notx"}'] = r; TONES[f'{key}-{"tx" if tx else "notx"}'] = t
s4 = step('msg-consumidor-idempotente', 4, TRACK, 20, ['mensageria', 'idempotencia', 'deduplicacao', 'at-least-once'], ['msg-ack-e-garantias'], SIM,
  loc('consumir', 'consume'),
  {'name': 'text', 'required': False, 'default': loc('fidelidade', 'loyalty'), 'ui': 'text'},
  [flag('key', 'chave', 'key', 'enum', options=[opt('order', 'pedido', 'order'), opt('message', 'mensagem', 'message'), opt('none', 'nenhuma', 'none')], default='order', ui='select'),
   flag('tx', 'transacao', 'transaction', 'bool', default=True, ui='switch')],
  {'options': ['zero', 'one', 'three'], 'answer': 'one'}, 'doubleCredit',
  {'live': True,
   'consts': {'msgIds': [d[0] for d in DELIV], 'orderIds': [d[1] for d in DELIV], 'kinds': ['@' + d[2] for d in DELIV], 'results': RES, 'toneMap': TONES, 'orders': 8, 'perOrder': 10},
   'compute': {
     'combo': "key + (tx ? '-tx' : '-notx')",
     'res': 'lookup(results, combo, [])',
     'rowTones': 'lookup(toneMap, combo, [])',
     'creditedN': "count(res, '@credited')",
     'extraN': 'creditedN - orders',
     'pointsN': 'creditedN * perOrder'},
   'cases': [
     {'when': 'extraN > 0', 'flags': ['doubleCredit']},
     {'when': 'extraN == 0', 'flags': ['onceEffect']},
     {'when': 'true', 'vars': {'extra': 'extraN', 'points': 'pointsN', 'credited': 'creditedN'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@deliveriesM', 'value': '=len(res)', 'format': 'int', 'tone': 'info'},
       {'label': '@creditedM', 'value': '=creditedN', 'format': 'int', 'tone': 'neutral'},
       {'label': '@extraM', 'value': '=extraN', 'format': 'int', 'tone': "=extraN > 0 ? 'bad' : 'ok'"},
       {'label': '@pointsM', 'value': '=pointsN', 'format': 'int', 'tone': "=extraN > 0 ? 'warn' : 'ok'"}]},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['@msgid', '@order', '@kind', '@result'],
      'rows': '=zip(msgIds, orderIds, kinds, res)', 'tones': '=rowTones', 'caption': '@caption'},
     {'type': 'note', 'when': "=key == 'message' && extraN > 0", 'tone': 'warn', 'text': '@msgNote'},
     {'type': 'note', 'when': "=key == 'order' && !tx", 'tone': 'warn', 'text': '@txNote'},
     {'type': 'note', 'when': "=key == 'none'", 'tone': 'bad', 'text': '@noneNote'},
     {'type': 'note', 'when': '=extraN == 0', 'tone': 'ok', 'text': '@okNote'}]})

def loc4(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Consumidor idempotente', 'Idempotent consumer'),
  'subtitle': T('Se a mensagem vai chegar repetida, o jeito é fazer a segunda vez não contar', 'If the message will arrive twice, make the second time not count'),
  'mission': T('O cartão fidelidade da Nona dá 10 pontos por pedido pago. Chegaram 11 entregas para 8 pedidos: 2 reentregas do broker (lembra do ack?) e 1 reenvio do caixa, que achou que a primeira tinha falhado. Escolha a chave de deduplicação para que cada pedido dê pontos uma vez só.',
               'Nona’s loyalty card gives 10 points per paid order. 11 deliveries arrived for 8 orders: 2 redeliveries from the broker (remember acks?) and 1 resend from the cashier, which thought the first one had failed. Pick the dedup key so each order gives points only once.'),
  'predict': {'question': T('se você deduplicar pelo id da mensagem, dos 3 repetidos (2 reentregas + 1 reenvio), quantos ainda dão pontos em dobro?', 'if you dedup by message id, out of the 3 repeats (2 redeliveries + 1 resend), how many still give double points?'),
    'options': {'zero': T('Nenhum', 'None'), 'one': T('Um', 'One'), 'three': T('Os três', 'All three')}},
  'feedback': {'right': T('isso: a reentrega do broker traz o mesmo id e é barrada. Mas o caixa, ao reenviar, criou uma mensagem nova com id novo (m9) para o mesmo pedido P105. Para o consumidor, parece outro pedido.', 'right: the broker’s redelivery carries the same id and is blocked. But the cashier, when resending, created a new message with a new id (m9) for the same order P105. To the consumer it looks like another order.'),
               'wrong': T('é um: reentregas trazem o mesmo id da mensagem, mas o reenvio do caixa nasceu com id novo (m9). Só uma chave do negócio, o número do pedido, pega os dois casos.', 'it’s one: redeliveries carry the same message id, but the cashier’s resend was born with a new id (m9). Only a business key, the order number, catches both cases.'),
               'skipped': T('sem palpite? Rode consumir --chave mensagem e procure a linha vermelha da m9.', 'no guess? Run consume --key message and look for m9’s red row.')},
  'coach': {'ui': T('palpite anotado. Troque a chave para "mensagem" e procure as linhas vermelhas na tabela.', 'guess noted. Switch the key to "message" and look for red rows in the table.'),
            'cmd': T('palpite anotado. Rode consumir --chave mensagem e procure as linhas vermelhas na tabela.', 'guess noted. Run consume --key message and look for red rows in the table.')},
  'tryNext': {'ui': T('Agora volte para "pedido" e desligue "na mesma transação": o worker creditou P102 e caiu antes de anotar a chave. A reentrega passa.', 'Now go back to "order" and turn off "in the same transaction": the worker credited P102 and crashed before writing the key down. The redelivery gets through.'),
              'cmd': T('Rode consumir --transacao nao e veja a linha da reentrega de P102.', 'Run consume --transaction no and look at P102’s redelivery row.')},
  'why': {'simples': T('Idempotente é a operação que, feita duas vezes, dá o mesmo resultado que feita uma. Apertar o botão do elevador cinco vezes não chama cinco elevadores.\nComo a fila às vezes entrega repetido, o consumidor guarda um caderninho com os pedidos que já deram pontos. Chegou de novo o P102? Já está no caderno, ignora. O truque é anotar o número do pedido (que não muda), e não o número do envelope (que muda se alguém mandar de novo).',
                       'Idempotent means doing it twice gives the same result as doing it once. Pressing the elevator button five times doesn’t call five elevators.\nSince the queue sometimes delivers twice, the consumer keeps a notebook of orders that already got points. P102 again? It’s in the notebook, skip it. The trick is to write down the order number (which never changes), not the envelope number (which changes if someone sends it again).'),
          'dev': T('Com at-least-once, duplicata é normal, não bug. A defesa é no consumidor: uma tabela de "já processados" com restrição de unicidade na chave de idempotência, e o efeito (creditar pontos) e o registro da chave gravados na mesma transação do banco. Um INSERT com ON CONFLICT DO NOTHING (Postgres, SQLite) que não insere nada diz "já vi, ignora".\nA chave precisa identificar a intenção do negócio: id do pedido, ou uma chave de idempotência (idempotency key) gerada uma vez pelo cliente e reaproveitada em todo reenvio. O id da mensagem (gerado pelo produtor a cada publicação; o RabbitMQ não atribui um e ele é opcional) só pega reentregas, porque um novo publish gera uma mensagem nova, com id novo.',
                   'With at-least-once, duplicates are normal, not a bug. The defense lives in the consumer: a "processed" table with a unique constraint on the idempotency key, and the effect (crediting points) and the key record written in the same database transaction. An INSERT with ON CONFLICT DO NOTHING (Postgres, SQLite) that inserts nothing means "seen it, skip".\nThe key must identify the business intent: the order id, or an idempotency key generated once by the client and reused on every resend. The message id (set by the producer on each publish; RabbitMQ doesn’t assign one and it’s optional) only catches redeliveries, because a new publish creates a new message with a new id.'),
          'especialista': T('Às vezes dá para tornar o próprio efeito idempotente sem tabela extra: "definir status = PAGO" em vez de "somar 10 pontos", ou upsert por chave natural. Quando o efeito sai do seu banco (cobrar um cartão, mandar e-mail), passe a chave de idempotência adiante: gateways de pagamento costumam aceitar uma no cabeçalho da requisição.\nNo Kafka, o produtor idempotente (ativado por padrão desde que não haja configuração conflitante) evita duplicatas no log causadas por retry do produtor, e transações dão exactly-once entre tópicos; mas o efeito externo do consumidor continua precisando de idempotência. Defina por quanto tempo guardar as chaves (janela de deduplicação) olhando por quanto tempo uma mensagem pode ser reentregue.',
                            'Sometimes you can make the effect itself idempotent with no extra table: "set status = PAID" instead of "add 10 points", or upsert by natural key. When the effect leaves your database (charging a card, sending an email), pass the idempotency key along: payment gateways commonly accept one in a request header.\nIn Kafka, the idempotent producer (on by default when no conflicting settings are present) prevents log duplicates caused by producer retries, and transactions give exactly-once between topics; but the consumer’s external effect still needs idempotency. Decide how long to keep keys (dedup window) based on how long a message can be redelivered.')},
  'break': {'mission': {'ui': T('hora de quebrar: escolha a chave "nenhuma".', 'time to break it: pick the key "none".'),
                        'cmd': T('hora de quebrar: rode consumir --chave nenhuma', 'time to break it: run consume --key none')},
            'success': T('Quebrou: sem chave, cada entrega vira pontos. {credited} créditos para 8 pedidos, {extra} a mais: {points} pontos distribuídos. No cartão fidelidade é prejuízo pequeno; num pagamento, é cliente cobrado em dobro.',
                         'Broken: with no key, every delivery becomes points. {credited} credits for 8 orders, {extra} too many: {points} points handed out. On a loyalty card that’s a small loss; on a payment, it’s a customer charged twice.'),
            'calm': T('{credited} créditos para 8 pedidos, {extra} a mais. Para quebrar, consuma sem chave nenhuma.', '{credited} credits for 8 orders, {extra} too many. To break it, consume with no key at all.')},
  'hints': {'ui': T(['Escolha a chave de deduplicação e veja a tabela.', 'Linha vermelha = repetição que deu pontos de novo.', 'Escolha a chave "nenhuma".'],
                    ['Pick the dedup key and watch the table.', 'Red row = a repeat that gave points again.', 'Pick the key "none".']),
            'cmd': T(['O nome do consumidor vai entre aspas; --chave e --transacao são opcionais.', '--chave aceita pedido, mensagem ou nenhuma.', 'consumir --chave nenhuma'],
                     ['The consumer name goes in quotes; --key and --transaction are optional.', '--key takes order, message or none.', 'consume --key none'])},
  'errors': {'notInEnum.key': T('Use pedido, mensagem ou nenhuma.', 'Use order, message or none.'), 'notBool.tx': T('Use sim ou nao.', 'Use yes or no.')},
  'controls': {'arg': T('Consumidor', 'Consumer'), 'key': T('Chave de deduplicação', 'Dedup key'), 'tx': T('Pontos e chave na mesma transação', 'Points and key in the same transaction')},
  'scene': {'label': T('Consumidor do cartão fidelidade', 'Loyalty card consumer'), 'empty': T('Rode para consumir.', 'Run to consume.'),
    'deliveriesM': T('entregas recebidas', 'deliveries received'), 'creditedM': T('vezes que deu pontos', 'times points were given'), 'extraM': T('créditos em dobro', 'double credits'), 'pointsM': T('pontos distribuídos', 'points handed out'),
    'tableLabel': T('Entregas na ordem em que chegaram', 'Deliveries in arrival order'), 'msgid': T('id da mensagem', 'message id'), 'order': T('pedido', 'order'), 'kind': T('o que é', 'what it is'), 'result': T('resultado', 'result'),
    'first': T('primeira entrega', 'first delivery'), 'redelivery': T('reentrega do broker', 'broker redelivery'), 'resend': T('reenvio do caixa (id novo)', 'cashier resend (new id)'),
    'credited': T('+10 pontos', '+10 points'), 'skipped': T('já visto, ignorado', 'seen, skipped'),
    'caption': T('8 pedidos, 11 entregas. O certo são 80 pontos.', '8 orders, 11 deliveries. The right total is 80 points.'),
    'msgNote': T('O id da mensagem barrou as reentregas, mas o reenvio do caixa veio como m9, uma mensagem nova para o mesmo P105.', 'The message id blocked the redeliveries, but the cashier’s resend came as m9, a new message for the same P105.'),
    'txNote': T('Sem transação, o worker creditou P102 e caiu antes de anotar a chave. Na reentrega, o caderno não tinha P102.', 'Without a transaction, the worker credited P102 and crashed before writing the key down. On redelivery, the notebook had no P102.'),
    'noneNote': T('Sem chave, o consumidor não tem memória: toda entrega é tratada como nova.', 'With no key, the consumer has no memory: every delivery is treated as new.'),
    'okNote': T('Cada pedido deu pontos uma vez só: {points} pontos, como devia. As mensagens chegaram repetidas, mas o efeito aconteceu uma vez.', 'Each order gave points exactly once: {points} points, as it should. Messages arrived twice, but the effect happened once.')},
  'data': {},
  'recipe': {'steps': [
     T('Instale o SQLite (sudo apt install sqlite3 no Linux/WSL; winget install SQLite.SQLite no Windows) ou, com Python 3.12+, use o módulo que já vem nele (python3 -m sqlite3 teste.db). Abra um terminal com SQLite (sqlite3 teste.db) e crie a tabela: CREATE TABLE processados (chave TEXT PRIMARY KEY);', 'Install SQLite (sudo apt install sqlite3 on Linux/WSL; winget install SQLite.SQLite on Windows) or, with Python 3.12+, use the module that ships with it (python3 -m sqlite3 test.db). Open a terminal with SQLite (sqlite3 test.db) and create the table: CREATE TABLE processados (chave TEXT PRIMARY KEY);'),
     T("Rode duas vezes: INSERT INTO processados VALUES ('P102') ON CONFLICT DO NOTHING; SELECT changes();", "Run twice: INSERT INTO processados VALUES ('P102') ON CONFLICT DO NOTHING; SELECT changes();"),
     T('No seu consumidor, faça o efeito (creditar pontos) só quando changes() for 1, dentro da mesma transação (BEGIN … COMMIT).', 'In your consumer, apply the effect (credit points) only when changes() is 1, inside the same transaction (BEGIN … COMMIT).')],
   'ok': T('a primeira vez changes() mostra 1 e a segunda mostra 0: o banco diz sozinho se aquele pedido já foi processado.', 'the first time changes() shows 1 and the second shows 0: the database itself tells you whether that order was already processed.')}}

t4 = {'pt': {'objectives': ['Definir idempotência com exemplos do dia a dia.', 'Escolher uma chave de deduplicação de negócio.', 'Entender por que efeito e chave vão na mesma transação.'], 'minutes': 20,
  'activity': 'Cada grupo recebe 11 papeizinhos de "pedido pago" (alguns repetidos, um reenviado com número de envelope diferente) e precisa dar carimbos num cartão fidelidade sem carimbar duas vezes o mesmo pedido.',
  'discussion': ['Que botões do dia a dia são idempotentes e quais não são?', 'Por quanto tempo vale guardar as chaves já vistas?'],
  'misconceptions': ['"O broker garante que não repete." Com at-least-once, repetir faz parte do contrato; quem garante o efeito único é o consumidor.']},
 'en': {'objectives': ['Define idempotency with everyday examples.', 'Pick a business dedup key.', 'Understand why the effect and the key go in the same transaction.'], 'minutes': 20,
  'activity': 'Each group gets 11 "order paid" slips (some repeated, one resent with a different envelope number) and must stamp a loyalty card without stamping the same order twice.',
  'discussion': ['Which everyday buttons are idempotent and which aren’t?', 'How long is it worth keeping the keys you’ve seen?'],
  'misconceptions': ['"The broker guarantees no repeats." With at-least-once, repeats are part of the contract; the consumer is what guarantees a single effect.']}}
write('04-consumidor-idempotente', s4, loc4('pt'), loc4('en'), t4)

# ================================================================== 5 · ordem, DLQ e prefetch
def dispatch(p, sac, n=12, speeds=(1, 3)):
  if sac: speeds = (speeds[0],)
  cap = [p if p > 0 else 10 ** 9 for _ in speeds]
  queue = list(range(1, n + 1)); buf = [[] for _ in speeds]; moved = True
  while queue and moved:
    moved = False
    for i in range(len(speeds)):
      if queue and len(buf[i]) < cap[i]: buf[i].append(queue.pop(0)); moved = True
  busy = [None] * len(speeds); done = []; cnt = [0] * len(speeds)
  def start(i, now): busy[i] = (now + speeds[i], buf[i][0]) if buf[i] else None
  for i in range(len(speeds)): start(i, 0)
  while any(busy):
    i = min((k for k in range(len(speeds)) if busy[k]), key=lambda k: (busy[k][0], k))
    now, m = busy[i]; buf[i].pop(0); done.append((now, m)); cnt[i] += 1
    if queue: buf[i].append(queue.pop(0))
    start(i, now)
  fin = {m: t for t, m in done}
  ooo = sum(1 for m in range(2, n + 1) if fin[m] < max(fin[j] for j in range(1, m)))
  return [max(fin.values()), cnt[0], cnt[1] if len(cnt) > 1 else 0, ooo]
RR = {str(p): dispatch(p, False) for p in range(0, 13)}
SAC = {str(p): dispatch(p, True) for p in range(0, 13)}
assert RR['1'][0] < RR['10'][0]
s5 = step('msg-ordem-dlq-prefetch', 5, TRACK, 20, ['mensageria', 'prefetch', 'dlq', 'ordem', 'rabbitmq'], ['msg-ack-e-garantias'], SIM,
  loc('distribuir', 'dispatch'),
  {'name': 'text', 'required': False, 'default': loc('pedidos', 'pedidos'), 'ui': 'text'},
  [flag('prefetch', 'prefetch', 'prefetch', 'int', min=0, max=1000, uiMax=12, default=1, ui='slider'),
   flag('dlq', 'dlq', 'dlq', 'bool', default=True, ui='switch'),
   flag('sac', 'unico', 'single', 'bool', default=False, ui='switch')],
  {'options': ['faster', 'same', 'slower'], 'answer': 'slower'}, 'poisonLoop',
  {'live': True,
   'consts': {'rrTab': RR, 'sacTab': SAC, 'limit': 3},
   'compute': {
     'pk': "prefetch == 0 || prefetch > 12 ? '0' : str(prefetch)",
     'row': 'lookup(sac ? sacTab : rrTab, pk, [0, 0, 0, 0])',
     'finishMin': 'row[0]', 'fastN': 'row[1]', 'slowN': 'row[2]', 'oooN': 'row[3]',
     'triesText': "dlq ? str(limit) : '∞'"},
   'cases': [
     {'when': '!dlq', 'flags': ['poisonLoop']},
     {'when': 'dlq', 'flags': ['parked']},
     {'when': 'oooN > 0', 'flags': ['outOfOrder']},
     {'when': '!sac && slowN >= fastN', 'flags': ['hoarding']},
     {'when': 'true', 'vars': {'finish': 'finishMin', 'fast': 'fastN', 'slow': 'slowN', 'ooo': 'oooN', 'p': 'prefetch'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@finishM', 'value': '=finishMin', 'format': 'min', 'tone': "=finishMin > 12 ? 'warn' : 'ok'"},
       {'label': '@oooM', 'value': '=oooN', 'format': 'int', 'tone': "=oooN > 0 ? 'warn' : 'ok'"},
       {'label': '@triesM', 'value': '=triesText', 'tone': "=dlq ? 'ok' : 'bad'"}]},
     {'type': 'queue', 'label': '@queueLabel', 'producer': '@counter', 'empty': '@emptyQueue',
      'messages': "=dlq ? [] : ['!☠ #13']",
      'consumers': [{'label': '@fastW', 'note': '@fastNote', 'tone': "=dlq ? 'ok' : 'bad'"},
                    {'label': '@slowW', 'note': "=sac ? '@standby' : '@slowNote'", 'tone': "=sac ? 'dim' : 'ok'"}],
      'dlq': "=dlq ? ['☠ #13'] : []", 'dlqLabel': 'DLQ'},
     {'type': 'chart', 'label': '@chart', 'kind': 'bar', 'labels': ['@fastW', '@slowW'],
      'series': [{'label': '@ordersS', 'values': '=[fastN, slowN]'}]},
     {'type': 'terminal', 'label': '@terminal', 'lines': "=dlq ? ['@t1', '@t2', '@t3', '@tDlq'] : ['@t1', '@t2', '@t3', '@tLoop1', '@tLoop2']"},
     {'type': 'note', 'when': '=!dlq', 'tone': 'bad', 'text': '@loopNote'},
     {'type': 'note', 'when': '=!sac && slowN >= fastN', 'tone': 'warn', 'text': '@hoardNote'},
     {'type': 'note', 'when': '=oooN > 0', 'tone': 'info', 'text': '@oooNote'}]})

def loc5(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Ordem, DLQ e prefetch', 'Ordering, DLQ and prefetch'),
  'subtitle': T('O pizzaiolo lento que pega comanda demais e a comanda envenenada que ninguém consegue fazer', 'The slow cook who grabs too many tickets and the poisoned ticket nobody can make'),
  'mission': T('Na cozinha, o Zé é rápido (1 min por pizza) e o Beto é novato (3 min). São 12 comandas e uma 13ª envenenada: "pizza de sabor inexistente", que faz qualquer um travar. Ajuste o prefetch (quantas comandas cada um segura de uma vez), a DLQ (a gaveta das comandas problemáticas) e veja o que acontece com a ordem.',
               'In the kitchen, Zé is fast (1 min per pizza) and Beto is a rookie (3 min). There are 12 tickets plus a poisoned 13th: "a flavor that doesn’t exist", which makes anyone choke. Tune the prefetch (how many tickets each one holds at once), the DLQ (the drawer for problem tickets) and see what happens to ordering.'),
  'predict': {'question': T('se você subir o prefetch de 1 para 10, as 12 pizzas ficam prontas…', 'if you raise prefetch from 1 to 10, the 12 pizzas are done…'),
    'options': {'faster': T('Mais rápido: menos idas ao balcão', 'Faster: fewer trips to the counter'), 'same': T('No mesmo tempo', 'In the same time'), 'slower': T('Mais devagar', 'Slower')}},
  'feedback': {'right': T('isso: com prefetch 10, o broker reparte meio a meio e o Beto fica com 6 comandas na mão. O Zé termina as dele e fica parado enquanto o Beto sua. Com prefetch 1, quem termina pega a próxima, e o Zé faz a maioria.', 'right: with prefetch 10, the broker splits them evenly and Beto ends up holding 6 tickets. Zé finishes his and stands idle while Beto sweats. With prefetch 1, whoever finishes takes the next one, and Zé does most of them.'),
               'wrong': T('fica mais devagar: o prefetch alto faz o broker entregar 6 comandas para cada um logo de cara. O Beto, lento, segura as dele, e o Zé fica de braços cruzados. Prefetch baixo deixa o trabalho ir para quem está livre.', 'it gets slower: high prefetch makes the broker hand 6 tickets to each one right away. Slow Beto holds on to his, and Zé stands around. Low prefetch lets work go to whoever is free.'),
               'skipped': T('sem palpite? Compare o tempo total com prefetch 1 e com 10.', 'no guess? Compare the total time with prefetch 1 and 10.')},
  'coach': {'ui': T('palpite anotado. Leve o prefetch de 1 para 10 e olhe o tempo total e as barras.', 'guess noted. Move prefetch from 1 to 10 and watch the total time and the bars.'),
            'cmd': T('palpite anotado. Rode distribuir e depois distribuir --prefetch 10.', 'guess noted. Run dispatch and then dispatch --prefetch 10.')},
  'tryNext': {'ui': T('Ligue "consumidor único": só o Zé trabalha, nada sai fora de ordem, mas leva 12 minutos. Ordem estrita custa paralelismo.', 'Turn on "single active consumer": only Zé works, nothing comes out of order, but it takes 12 minutes. Strict ordering costs parallelism.'),
              'cmd': T('Rode distribuir --unico sim e compare "fora de ordem" e o tempo.', 'Run dispatch --single yes and compare "out of order" and the time.')},
  'why': {'simples': T('Prefetch é quantas comandas cada pizzaiolo pode segurar antes de terminar alguma. Se o novato pega muitas, elas ficam paradas no bolso dele enquanto o rápido está livre.\nDLQ (fila de mensagens mortas) é a gaveta das comandas que ninguém consegue fazer. Sem ela, a comanda envenenada volta para o varal, alguém pega, trava, devolve, outro pega… para sempre. Com ela, depois de algumas tentativas, vai para a gaveta e um humano olha com calma.\nE com dois pizzaiolos de velocidades diferentes, a pizza 3 pode ficar pronta antes da 2. Se a ordem importa, só um pode trabalhar por vez.',
                       'Prefetch is how many tickets each cook may hold before finishing any. If the rookie grabs many, they sit in his pocket while the fast one is free.\nThe DLQ (dead letter queue) is the drawer for tickets nobody can make. Without it, the poisoned ticket goes back on the rail, someone takes it, chokes, puts it back, someone else takes it… forever. With it, after a few tries it goes to the drawer and a human looks at it calmly.\nAnd with two cooks at different speeds, pizza 3 can be ready before pizza 2. If order matters, only one can work at a time.'),
          'dev': T('No RabbitMQ, prefetch (basic.qos) limita quantas entregas sem ack podem estar em andamento; com global=false (o padrão dos clientes) o limite vale por consumidor, não por canal; 0 é sem limite. A documentação diz que valores entre 100 e 300 costumam dar a melhor vazão sem sobrecarregar consumidores, e que 1 é o mais conservador e reduz bastante a vazão. Esse conselho vale para mensagens rápidas (milissegundos); quando cada mensagem leva minutos, como aqui, prefetch baixo distribui melhor.\nDLQ: configure um dead letter exchange (de preferência por política, não fixo no código). A mensagem vai para lá quando é rejeitada sem requeue, expira por TTL, estoura o limite de tamanho da fila ou passa do limite de entregas de uma quorum queue (20 por padrão desde o RabbitMQ 4.0; nesta simulação, 3).',
                   'In RabbitMQ, prefetch (basic.qos) caps how many unacked deliveries can be in flight; with global=false (the client default) the limit applies per consumer, not per channel; 0 means unlimited. The docs say values from 100 to 300 usually give the best throughput without overwhelming consumers, and that 1 is the most conservative and significantly reduces throughput. That advice is for fast messages (milliseconds); when each message takes minutes, like here, low prefetch spreads work better.\nDLQ: configure a dead letter exchange (preferably via policy, not hardcoded). A message goes there when rejected without requeue, expired by TTL, dropped by a queue length limit, or past a quorum queue’s delivery limit (20 by default since RabbitMQ 4.0; 3 in this simulation).'),
          'especialista': T('Ordem numa fila só existe com um consumidor por vez: com vários, o despacho é round-robin e a ordem entre consumidores se perde, e reentregas também embaralham. O RabbitMQ oferece single active consumer (argumento x-single-active-consumer na declaração da fila) para ter um ativo e outros de reserva. No Kafka a ordem é por partição: mensagens com a mesma chave caem na mesma partição, e o paralelismo é o número de partições.\nSem limite de entregas, uma poison message com requeue=true vira um laço quente que consome CPU e esconde o problema. Isso vale para filas clássicas; numa quorum queue do RabbitMQ 4 o limite existe (delivery-limit, 20 por padrão) e, sem DLX configurado, a mensagem é descartada em silêncio ao atingi-lo: outro problema, mais difícil de notar. Monitore a DLQ (profundidade e idade), guarde o motivo (o cabeçalho x-death traz reason, como rejected, expired, maxlen ou delivery_limit) e tenha um caminho de reprocessamento. Lembre que o dead-lettering padrão não usa confirmação interna; quorum queues oferecem a estratégia at-least-once, com custo de memória e CPU.',
                            'Ordering in a queue only exists with one consumer at a time: with several, dispatch is round-robin and order across consumers is lost, and redeliveries shuffle it too. RabbitMQ offers single active consumer (the x-single-active-consumer argument when declaring the queue) to have one active and others on standby. In Kafka, ordering is per partition: messages with the same key land in the same partition, and parallelism is the number of partitions.\nWithout a delivery limit, a poison message with requeue=true becomes a hot loop that burns CPU and hides the problem. That holds for classic queues; on a RabbitMQ 4 quorum queue the limit exists (delivery-limit, 20 by default) and, with no DLX configured, the message is silently dropped when it is reached: a different problem, harder to notice. Monitor the DLQ (depth and age), keep the reason (the x-death header carries a reason such as rejected, expired, maxlen or delivery_limit) and have a reprocessing path. Note that default dead-lettering uses no internal confirms; quorum queues offer an at-least-once strategy, at a memory and CPU cost.')},
  'break': {'mission': {'ui': T('hora de quebrar: desligue a DLQ.', 'time to break it: turn off the DLQ.'),
                        'cmd': T('hora de quebrar: rode distribuir --dlq nao', 'time to break it: run dispatch --dlq no')},
            'success': T('Quebrou: sem DLQ, a comanda #13 volta para a fila toda vez que trava alguém. Numa fila clássica, ela nunca zera, o painel mostra "1 mensagem" para sempre e os logs enchem de erro igual. As outras 12 até saem em {finish} min, mas a cozinha nunca fica em paz. (Numa quorum queue do RabbitMQ 4 sem DLX seria outro problema: após 20 tentativas de entrega, o limite padrão, a mensagem seria descartada em silêncio.)',
                         'Broken: without a DLQ, ticket #13 goes back to the queue every time it chokes someone. On a classic queue it never empties, the dashboard shows "1 message" forever and the logs fill with the same error. The other 12 still come out in {finish} min, but the kitchen never gets peace. (On a RabbitMQ 4 quorum queue without a DLX it would be a different problem: after 20 delivery attempts, the default limit, the message would be silently dropped.)'),
            'calm': T('Com prefetch {p}: 12 pizzas em {finish} min (Zé {fast}, Beto {slow}), e a #13 foi para a DLQ depois de 3 tentativas. Para quebrar, desligue a DLQ.',
                      'With prefetch {p}: 12 pizzas in {finish} min (Zé {fast}, Beto {slow}), and #13 went to the DLQ after 3 tries. To break it, turn off the DLQ.')},
  'hints': {'ui': T(['Mexa no prefetch, na DLQ e no consumidor único.', 'A comanda ☠ é a envenenada: veja para onde ela vai.', 'Desligue a DLQ.'],
                    ['Move prefetch, DLQ and single consumer.', 'The ☠ ticket is the poisoned one: see where it goes.', 'Turn off the DLQ.']),
            'cmd': T(['O nome da fila vai entre aspas; --prefetch, --dlq e --unico são opcionais.', '--prefetch 0 é sem limite; --dlq e --unico aceitam sim ou nao.', 'distribuir --dlq nao'],
                     ['The queue name goes in quotes; --prefetch, --dlq and --single are optional.', '--prefetch 0 means unlimited; --dlq and --single take yes or no.', 'dispatch --dlq no'])},
  'errors': {'belowMin.prefetch': T('Prefetch não fica negativo. Use 0 para "sem limite".', 'Prefetch can’t be negative. Use 0 for "unlimited".'),
             'aboveMax.prefetch': T('Até 1000 nesta simulação.', 'Up to 1000 in this simulation.'),
             'notBool.dlq': T('Use sim ou nao.', 'Use yes or no.'), 'notBool.sac': T('Use sim ou nao.', 'Use yes or no.')},
  'controls': {'arg': T('Fila', 'Queue'), 'prefetch': T('Prefetch (comandas na mão; 0 = sem limite)', 'Prefetch (tickets in hand; 0 = unlimited)'), 'dlq': T('DLQ para comandas problemáticas', 'DLQ for problem tickets'), 'sac': T('Consumidor único (ordem estrita)', 'Single active consumer (strict order)')},
  'scene': {'label': T('Despacho de comandas', 'Ticket dispatch'), 'empty': T('Rode para distribuir.', 'Run to dispatch.'),
    'finishM': T('tempo para as 12 pizzas', 'time for the 12 pizzas'), 'oooM': T('pizzas fora de ordem', 'pizzas out of order'), 'triesM': T('tentativas da comanda ☠', 'tries of the ☠ ticket'),
    'queueLabel': T('Fila depois do serviço', 'Queue after service'), 'counter': T('balcão', 'counter'), 'emptyQueue': T('fila vazia', 'empty queue'),
    'fastW': T('Zé (rápido)', 'Zé (fast)'), 'slowW': T('Beto (novato)', 'Beto (rookie)'), 'fastNote': T('{fast} pizzas', '{fast} pizzas'), 'slowNote': T('{slow} pizzas', '{slow} pizzas'), 'standby': T('de reserva', 'on standby'),
    'chart': T('Pizzas feitas por cada um', 'Pizzas made by each'), 'ordersS': T('pizzas', 'pizzas'),
    'terminal': T('Log da comanda #13', 'Ticket #13 log'),
    't1': T('! #13 tentativa 1: sabor inexistente, nack', '! #13 try 1: unknown flavor, nack'), 't2': T('! #13 tentativa 2: sabor inexistente, nack', '! #13 try 2: unknown flavor, nack'),
    't3': T('! #13 tentativa 3: sabor inexistente, nack', '! #13 try 3: unknown flavor, nack'), 'tDlq': T('+ #13 → pedidos.dlq (limite de entregas)', '+ #13 → pedidos.dlq (delivery limit)'),
    'tLoop1': T('! #13 tentativa 4, 5, 6, … de volta para a fila', '! #13 try 4, 5, 6, … back to the queue'), 'tLoop2': T('? a fila nunca zera', '? the queue never empties'),
    'loopNote': T('Sem DLQ, numa fila clássica a mensagem envenenada fica em laço: volta para a fila, trava alguém, volta de novo. Ninguém percebe até a conta de CPU chegar. Numa quorum queue do RabbitMQ 4 sem DLX, após 20 entregas (delivery-limit padrão) ela seria descartada em silêncio: outro problema.', 'Without a DLQ, on a classic queue the poison message loops: back to the queue, chokes someone, back again. Nobody notices until the CPU bill arrives. On a RabbitMQ 4 quorum queue without a DLX, after 20 deliveries (default delivery-limit) it would be silently dropped: a different problem.'),
    'hoardNote': T('O Beto segurou {slow} comandas e o Zé ficou parado esperando. Prefetch alto com trabalho lento concentra a fila em quem é mais devagar.', 'Beto held {slow} tickets and Zé stood idle. High prefetch with slow work piles the queue onto the slowest worker.'),
    'oooNote': T('{ooo} pizzas ficaram prontas antes de uma comanda mais antiga. Se a ordem importa (criar e depois cancelar o mesmo pedido), use um consumidor por vez ou uma chave por cliente.', '{ooo} pizzas were ready before an older ticket. If order matters (create then cancel the same order), use one consumer at a time or a key per customer.')},
  'data': {},
  'recipe': {'steps': rabbit_steps(T) + [
     T('Na aba Exchanges, crie uma exchange pedidos.dlx (tipo fanout). Na aba Queues and Streams, crie a fila pedidos.dlq e ligue-a a essa exchange (Bindings). Depois crie a fila pedidos do tipo Quorum com o argumento x-dead-letter-exchange = pedidos.dlx (em produção, prefira uma política).', 'In the Exchanges tab, create an exchange pedidos.dlx (type fanout). In the Queues and Streams tab, create a queue pedidos.dlq and bind it to that exchange (Bindings). Then create the pedidos queue of type Quorum with the argument x-dead-letter-exchange = pedidos.dlx (in production, prefer a policy).'),
     T('Publique uma mensagem em pedidos. Em "Get messages", escolha em Ack Mode "Reject requeue false" e clique em "Get Message(s)".', 'Publish a message to pedidos. In "Get messages", choose Ack Mode "Reject requeue false" and click "Get Message(s)".')],
   'ok': T('a mensagem sai de pedidos e aparece em pedidos.dlq: a comanda problemática foi para a gaveta em vez de voltar para o varal.', 'the message leaves pedidos and shows up in pedidos.dlq: the problem ticket went to the drawer instead of back on the rail.')}}

t5 = {'pt': {'objectives': ['Explicar prefetch e seu efeito com consumidores de velocidades diferentes.', 'Usar DLQ para isolar mensagens envenenadas.', 'Reconhecer quando a ordem se perde.'], 'minutes': 20,
  'activity': 'Dois alunos fazem "pizzas" (dobrar papéis), um rápido e um que só pode usar uma mão. Joguem com "pegue 6 de uma vez" e com "pegue 1 por vez" e cronometrem. Inclua um papel impossível de dobrar e combinem uma gaveta para ele.',
  'discussion': ['Que mensagem "envenenada" pode aparecer num sistema que você conhece?', 'Quando a ordem importa de verdade, e quando é só costume?'],
  'misconceptions': ['"Prefetch alto é sempre mais rápido." Para trabalho lento e desigual, ele concentra a fila em quem é mais devagar.']},
 'en': {'objectives': ['Explain prefetch and its effect with consumers of different speeds.', 'Use a DLQ to isolate poison messages.', 'Recognize when ordering is lost.'], 'minutes': 20,
  'activity': 'Two students make "pizzas" (folding paper), one fast and one allowed to use only one hand. Play with "take 6 at once" and "take 1 at a time" and time it. Include a paper that can’t be folded and agree on a drawer for it.',
  'discussion': ['What "poison" message could show up in a system you know?', 'When does order really matter, and when is it just habit?'],
  'misconceptions': ['"Higher prefetch is always faster." For slow, uneven work, it piles the queue onto the slowest worker.']}}
write('05-ordem-dlq-e-prefetch', s5, loc5('pt'), loc5('en'), t5)

# ================================================================== 6 · pub/sub
s6 = step('msg-pub-sub', 6, TRACK, 20, ['mensageria', 'pub-sub', 'fanout', 'consumer-group', 'kafka'], ['msg-comando-evento'], SIM,
  loc('publicar', 'publish'),
  {'name': 'text', 'required': False, 'default': loc('PedidoPago', 'OrderPaid'), 'ui': 'text'},
  [flag('queues', 'filas', 'queues', 'enum', options=[opt('perService', 'por-servico', 'per-service'), opt('shared', 'compartilhada', 'shared')], default='perService', ui='select'),
   flag('log', 'log', 'log', 'bool', default=False, ui='switch')],
  {'options': ['nine', 'three', 'zero'], 'answer': 'three'}, 'missedEvents',
  {'live': True,
   'consts': {'total': 9},
   'compute': {
     'shared': "queues == 'shared'",
     'kitchenN': 'shared ? 3 : 9', 'invoiceN': 'shared ? 3 : 9', 'loyaltyN': 'shared ? 2 : 9',
     'analyticsN': 'shared ? 1 : (log ? 9 : 3)'},
   'cases': [
     {'when': 'kitchenN < total || invoiceN < total || loyaltyN < total', 'flags': ['missedEvents']},
     {'when': '!shared && !log', 'flags': ['lateNoHistory']},
     {'when': '!shared && log', 'flags': ['replayed']},
     {'when': 'true', 'vars': {'kitchen': 'kitchenN', 'invoice': 'invoiceN', 'loyalty': 'loyaltyN', 'analytics': 'analyticsN'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@kitchen', 'value': "=kitchenN + '/9'", 'tone': "=kitchenN < 9 ? 'bad' : 'ok'"},
       {'label': '@invoice', 'value': "=invoiceN + '/9'", 'tone': "=invoiceN < 9 ? 'bad' : 'ok'"},
       {'label': '@loyalty', 'value': "=loyaltyN + '/9'", 'tone': "=loyaltyN < 9 ? 'bad' : 'ok'"},
       {'label': '@analytics', 'value': "=analyticsN + '/9'", 'tone': "=analyticsN < 9 ? 'warn' : 'ok'"}]},
     {'type': 'flow', 'steps': [
       {'label': '@cashier', 'sub': '=text', 'tone': 'info'},
       {'label': "=shared ? '@oneQueue' : (log ? '@topic' : '@fanout')", 'sub': "=shared ? '@oneQueueSub' : (log ? '@topicSub' : '@fanoutSub')", 'tone': "=shared ? 'warn' : 'ok'"},
       {'label': '@services', 'sub': "=shared ? '@splitSub' : '@copySub'", 'tone': "=shared ? 'bad' : 'ok'"}]},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['@service', '@where', '@got'],
      'rows': ["=['@kitchen', shared ? '@sharedName' : (log ? '@gKitchen' : '@qKitchen'), kitchenN + '/9']",
               "=['@invoice', shared ? '@sharedName' : (log ? '@gInvoice' : '@qInvoice'), invoiceN + '/9']",
               "=['@loyalty', shared ? '@sharedName' : (log ? '@gLoyalty' : '@qLoyalty'), loyaltyN + '/9']",
               "=['@analytics', shared ? '@sharedName' : (log ? '@gAnalytics' : '@qAnalytics'), analyticsN + '/9']"],
      'tones': ["=kitchenN < 9 ? 'bad' : 'neutral'", "=invoiceN < 9 ? 'bad' : 'neutral'", "=loyaltyN < 9 ? 'bad' : 'neutral'", "=analyticsN < 9 ? 'warn' : 'neutral'"],
      'caption': '@caption'},
     {'type': 'note', 'when': '=shared', 'tone': 'bad', 'text': '@sharedNote'},
     {'type': 'note', 'when': '=!shared && !log', 'tone': 'info', 'text': '@lateNote'},
     {'type': 'note', 'when': '=!shared && log', 'tone': 'ok', 'text': '@replayNote'}]})

def loc6(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Pub/sub', 'Pub/sub'),
  'subtitle': T('Uma fila para dividir trabalho, uma fila por interessado para todo mundo ouvir', 'One queue to split work, one queue per subscriber so everyone hears'),
  'mission': T('O caixa publicou 9 eventos "PedidoPago". Cozinha, nota fiscal e fidelidade precisam de todos. O analytics só chegou depois do 6º. Ligue os serviços numa fila compartilhada ou numa fila por serviço, e veja quem recebeu o quê. Depois teste o modo log, que guarda o histórico.',
               'The cashier published 9 "OrderPaid" events. Kitchen, invoicing and loyalty need all of them. Analytics only showed up after the 6th. Wire the services to a shared queue or to one queue per service, and see who got what. Then try log mode, which keeps history.'),
  'predict': {'question': T('se cozinha, nota e fidelidade lerem da MESMA fila, cada um recebe quantos dos 9 eventos?', 'if kitchen, invoicing and loyalty read from the SAME queue, how many of the 9 events does each get?'),
    'options': {'nine': T('Todos os 9', 'All 9'), 'three': T('Uns 3 cada', 'About 3 each'), 'zero': T('Nenhum', 'None')}},
  'feedback': {'right': T('isso: numa fila, cada mensagem vai para um consumidor só. Os serviços viram "concorrentes" e dividem os eventos como se fossem pizzaiolos repartindo comandas. Ótimo para dividir trabalho, péssimo para avisar todo mundo.', 'right: in a queue, each message goes to one consumer only. The services become "competitors" and split the events like cooks sharing tickets. Great for splitting work, terrible for telling everyone.'),
               'wrong': T('cada um recebe uns 3: numa fila, cada mensagem é entregue a um consumidor só. Para cada serviço receber tudo, cada um precisa da sua fila ligada a uma exchange fanout (ou, no Kafka, do seu consumer group).', 'each gets about 3: in a queue, each message is delivered to just one consumer. For every service to get everything, each needs its own queue bound to a fanout exchange (or, in Kafka, its own consumer group).'),
               'skipped': T('sem palpite? Rode publicar --filas compartilhada e olhe a tabela.', 'no guess? Run publish --queues shared and look at the table.')},
  'coach': {'ui': T('palpite anotado. Troque para fila compartilhada e compare a tabela.', 'guess noted. Switch to the shared queue and compare the table.'),
            'cmd': T('palpite anotado. Rode publicar e depois publicar --filas compartilhada.', 'guess noted. Run publish and then publish --queues shared.')},
  'tryNext': {'ui': T('Volte para "uma por serviço" e ligue o modo log: o analytics, que chegou atrasado, lê desde o começo. (No Kafka, um grupo novo começa no fim por padrão, com auto.offset.reset=latest; para ler do offset 0 é preciso auto.offset.reset=earliest.)', 'Go back to "per service" and turn on log mode: analytics, which arrived late, reads from the start. (In Kafka a new group starts at the end by default, with auto.offset.reset=latest; reading from offset 0 needs auto.offset.reset=earliest.)'),
              'cmd': T('Rode publicar --log sim e olhe a linha do analytics (no Kafka, ler do offset 0 exige auto.offset.reset=earliest; o padrão é latest).', 'Run publish --log yes and look at the analytics row (in Kafka, reading from offset 0 needs auto.offset.reset=earliest; the default is latest).')},
  'why': {'simples': T('Fila compartilhada é a pilha de comandas da cozinha: cada comanda vai para um pizzaiolo só. Serve para dividir trabalho.\nPub/sub é o grupo da família no celular: uma mensagem, e cada um recebe a sua cópia. Quem publica não sabe quantos estão ouvindo.\nE tem a diferença entre caixa de correio e mural: na fila, a carta lida sai da caixa; no log (como o Kafka), o recado fica no mural e quem chega depois ainda pode ler.',
                       'A shared queue is the kitchen’s ticket pile: each ticket goes to one cook only. It’s for splitting work.\nPub/sub is the family group chat: one message, and everyone gets their own copy. The publisher doesn’t know how many are listening.\nAnd there’s the mailbox versus the bulletin board: in a queue, a read letter leaves the box; in a log (like Kafka), the note stays on the board and latecomers can still read it.'),
          'dev': T('No RabbitMQ (AMQP 0-9-1), o produtor publica numa exchange, e bindings decidem para quais filas vai. Tipos: direct (chave exata), fanout (copia para todas as filas ligadas), topic (padrão na chave, como pedido.*) e headers. Pub/sub = uma exchange fanout ou topic, com uma fila por serviço; vários consumidores na mesma fila = competing consumers.\nNo Kafka a ideia aparece como consumer groups: cada grupo recebe todas as mensagens do tópico, e dentro do grupo as partições são repartidas entre os consumidores. Mesmo grupo divide; grupos diferentes copiam.',
                   'In RabbitMQ (AMQP 0-9-1), the producer publishes to an exchange, and bindings decide which queues get it. Types: direct (exact key), fanout (copies to every bound queue), topic (key pattern, like order.*) and headers. Pub/sub = a fanout or topic exchange with one queue per service; several consumers on the same queue = competing consumers.\nIn Kafka the same idea shows up as consumer groups: each group gets every message in the topic, and within a group the partitions are split among consumers. Same group splits; different groups copy.'),
          'especialista': T('Fila e log têm modelos de retenção diferentes. Numa fila, a mensagem confirmada é apagada; um serviço novo só vê o que chegar depois de a fila dele existir. Num log (Kafka, ou streams do RabbitMQ), as mensagens ficam pelo tempo ou tamanho de retenção, e cada leitor guarda seu offset: dá para reprocessar e para um serviço novo ler o histórico. Atenção: um consumer group novo do Kafka começa no fim do tópico por padrão (auto.offset.reset=latest); para ler desde o offset 0 é preciso auto.offset.reset=earliest.\nIsso muda decisões de arquitetura: reconstruir um read model a partir de eventos, auditar, depurar um bug reprocessando. Em troca, você cuida de retenção, compactação, partições e lag por grupo. Uma fila por assinante também multiplica armazenamento: muitos assinantes em fanout grande é um sinal para considerar um stream.',
                            'Queues and logs have different retention models. In a queue, an acked message is deleted; a new service only sees what arrives after its queue exists. In a log (Kafka, or RabbitMQ streams), messages stay for the retention time or size, and each reader keeps its offset: you can reprocess, and a new service can read history. Note: a new Kafka consumer group starts at the end of the topic by default (auto.offset.reset=latest); reading from offset 0 needs auto.offset.reset=earliest.\nThat changes architecture decisions: rebuilding a read model from events, auditing, debugging by replaying. In exchange, you manage retention, compaction, partitions and per-group lag. One queue per subscriber also multiplies storage: many subscribers on a big fanout is a sign to consider a stream.')},
  'break': {'mission': {'ui': T('hora de quebrar: ligue todo mundo na fila compartilhada.', 'time to break it: put everyone on the shared queue.'),
                        'cmd': T('hora de quebrar: rode publicar --filas compartilhada', 'time to break it: run publish --queues shared')},
            'success': T('Quebrou: na mesma fila, cada evento foi para um serviço só. A cozinha viu {kitchen} de 9, a nota {invoice} e a fidelidade {loyalty}. Teve pizza paga que não foi feita e pedido sem nota fiscal.',
                         'Broken: on the same queue, each event went to just one service. The kitchen saw {kitchen} of 9, invoicing {invoice} and loyalty {loyalty}. Some paid pizzas were never made and some orders got no invoice.'),
            'calm': T('Cada serviço com a sua fila recebeu os 9 eventos. O analytics recebeu {analytics}. Para quebrar, coloque todos na mesma fila.',
                      'Each service with its own queue got all 9 events. Analytics got {analytics}. To break it, put everyone on the same queue.')},
  'hints': {'ui': T(['Escolha como ligar os serviços e se o histórico fica guardado.', 'Na mesma fila, cada mensagem tem um único destino.', 'Escolha "compartilhada".'],
                    ['Choose how to wire the services and whether history is kept.', 'On the same queue, each message has a single destination.', 'Pick "shared".']),
            'cmd': T(['O nome do evento vai entre aspas; --filas e --log são opcionais.', '--filas aceita por-servico ou compartilhada.', 'publicar --filas compartilhada'],
                     ['The event name goes in quotes; --queues and --log are optional.', '--queues takes per-service or shared.', 'publish --queues shared'])},
  'errors': {'notInEnum.queues': T('Use por-servico ou compartilhada.', 'Use per-service or shared.'), 'notBool.log': T('Use sim ou nao.', 'Use yes or no.')},
  'controls': {'arg': T('Evento', 'Event'), 'queues': T('Como ligar os serviços', 'How to wire the services'), 'log': T('Modo log (guarda histórico, como Kafka)', 'Log mode (keeps history, like Kafka)')},
  'scene': {'label': T('Quem recebeu os 9 eventos', 'Who got the 9 events'), 'empty': T('Rode para publicar.', 'Run to publish.'),
    'kitchen': T('cozinha', 'kitchen'), 'invoice': T('nota fiscal', 'invoicing'), 'loyalty': T('fidelidade', 'loyalty'), 'analytics': T('analytics (chegou depois)', 'analytics (late)'),
    'cashier': T('caixa', 'cashier'), 'oneQueue': T('uma fila só', 'a single queue'), 'oneQueueSub': T('consumidores competem', 'consumers compete'),
    'fanout': T('exchange fanout', 'fanout exchange'), 'fanoutSub': T('uma cópia por fila', 'one copy per queue'), 'topic': T('tópico (log)', 'topic (log)'), 'topicSub': T('cada grupo com seu offset', 'each group with its offset'),
    'services': T('serviços', 'services'), 'splitSub': T('cada evento para um só', 'each event to just one'), 'copySub': T('todo mundo recebe', 'everyone receives'),
    'tableLabel': T('Entregas por serviço', 'Deliveries per service'), 'service': T('serviço', 'service'), 'where': T('lê de', 'reads from'), 'got': T('recebeu', 'received'),
    'sharedName': T('fila pedidos (compartilhada)', 'pedidos queue (shared)'), 'gKitchen': T('grupo cozinha', 'kitchen group'), 'gInvoice': T('grupo nota', 'invoicing group'), 'gLoyalty': T('grupo fidelidade', 'loyalty group'), 'gAnalytics': T('grupo analytics, desde o início', 'analytics group, from the start'),
    'qKitchen': T('cozinha.pedidos', 'kitchen.orders'), 'qInvoice': T('nota.pedidos', 'invoice.orders'), 'qLoyalty': T('fidelidade.pedidos', 'loyalty.orders'), 'qAnalytics': T('analytics.pedidos', 'analytics.orders'),
    'caption': T('9 eventos publicados; o analytics se inscreveu depois do 6º.', '9 events published; analytics subscribed after the 6th.'),
    'sharedNote': T('Fila compartilhada é para dividir trabalho entre cópias do MESMO serviço, não para avisar serviços diferentes.', 'A shared queue is for splitting work among copies of the SAME service, not for notifying different services.'),
    'lateNote': T('Com filas, quem chega atrasado só vê o que veio depois: o analytics recebeu {analytics} de 9. O histórico já tinha sido apagado.', 'With queues, latecomers only see what comes after: analytics got {analytics} of 9. History was already deleted.'),
    'replayNote': T('No log, as mensagens ficam guardadas pelo tempo de retenção. O analytics começou do offset 0 e leu os 9. (No Kafka isso exige auto.offset.reset=earliest: por padrão, um consumer group novo começa no fim, com latest.)', 'In a log, messages stay for the retention period. Analytics started from offset 0 and read all 9. (In Kafka that needs auto.offset.reset=earliest: by default a new consumer group starts at the end, with latest.)')},
  'data': {},
  'recipe': {'steps': rabbit_steps(T) + [
     T('Crie uma exchange eventos do tipo fanout e duas filas, cozinha e nota. Em cada fila, faça o binding com a exchange eventos.', 'Create an exchange eventos of type fanout and two queues, cozinha and nota. On each queue, bind it to the eventos exchange.'),
     T('Na página da exchange eventos, publique 3 mensagens. Depois olhe a contagem das duas filas.', 'On the eventos exchange page, publish 3 messages. Then look at both queues’ counts.'),
     T('Para ver o outro lado, publique 6 mensagens na fila pedidos (a da lição 1). No worker.py da lição de ack, troque para basic_qos(prefetch_count=1) (senão o primeiro worker pega as 6 de uma vez) e rode duas cópias, em dois terminais, lendo da mesma fila pedidos: elas dividem as mensagens.', 'To see the other side, publish 6 messages to the pedidos queue (the one from lesson 1). In worker.py from the ack lesson, change to basic_qos(prefetch_count=1) (otherwise the first worker grabs all 6 at once) and run two copies, in two terminals, reading the same pedidos queue: they split the messages.')],
   'ok': T('as filas cozinha e nota mostram 3 mensagens cada, a partir de uma única publicação por mensagem; e as duas cópias do worker na mesma fila imprimem mensagens diferentes.', 'the cozinha and nota queues show 3 messages each, from a single publish per message; and the two worker copies on the same queue print different messages.')}}

t6 = {'pt': {'objectives': ['Diferenciar competing consumers de pub/sub.', 'Ler exchange, binding e fila no RabbitMQ.', 'Entender a diferença entre fila e log.'], 'minutes': 20,
  'activity': 'O professor "publica" 9 cartões. Rodada 1: um monte só, três alunos-serviço pegam do mesmo monte. Rodada 2: o professor faz 3 cópias de cada cartão, uma por aluno. Um quarto aluno chega no meio: o que ele consegue ler em cada rodada? E se os cartões ficassem colados no quadro?',
  'discussion': ['Em que caso você quer que cada mensagem vá para um só?', 'Para que serve poder reler eventos antigos?'],
  'misconceptions': ['"Mais consumidores na fila = mais serviços avisados." Na mesma fila, mais consumidores só dividem o trabalho.']},
 'en': {'objectives': ['Tell competing consumers from pub/sub.', 'Read exchange, binding and queue in RabbitMQ.', 'Understand the difference between a queue and a log.'], 'minutes': 20,
  'activity': 'The teacher "publishes" 9 cards. Round 1: one pile, three student-services take from the same pile. Round 2: the teacher makes 3 copies of each card, one per student. A fourth student arrives halfway: what can they read in each round? What if the cards stayed pinned on the board?',
  'discussion': ['When do you want each message to go to just one consumer?', 'What is replaying old events good for?'],
  'misconceptions': ['"More consumers on the queue = more services notified." On the same queue, more consumers only split the work.']}}
write('06-pub-sub', s6, loc6('pt'), loc6('en'), t6)

# ================================================================== 7 · quando não usar fila
CASES = {'price': {'work': 30, 'needs': True, 'flaky': False}, 'coupon': {'work': 80, 'needs': True, 'flaky': False},
         'email': {'work': 1200, 'needs': False, 'flaky': True}, 'invoice': {'work': 3000, 'needs': False, 'flaky': True},
         'report': {'work': 90000, 'needs': False, 'flaky': False}}
s7 = step('msg-quando-nao-usar-fila', 7, TRACK, 15, ['mensageria', 'arquitetura', 'trade-offs'], ['msg-sincrono-assincrono', 'msg-pub-sub'], SIM,
  loc('decidir', 'decide'),
  {'name': 'text', 'required': False, 'default': loc('app da pizzaria', 'pizzeria app'), 'ui': 'text'},
  [flag('case', 'caso', 'case', 'enum', options=[opt('email', 'email', 'email'), opt('price', 'preco', 'price'), opt('coupon', 'cupom', 'coupon'), opt('invoice', 'nota', 'invoice'), opt('report', 'relatorio', 'report')], default='email', ui='select'),
   flag('mode', 'modo', 'mode', 'enum', options=[opt('queue', 'fila', 'queue'), opt('direct', 'direto', 'direct')], default='queue', ui='select')],
  {'options': ['yes', 'no', 'always'], 'answer': 'no'}, 'wrongTool',
  {'live': True,
   'consts': {'caseInfo': CASES, 'pollMs': 2000, 'ackMs': 50},
   'compute': {
     'info': 'lookup(caseInfo, case, null)',
     'work': 'info.work', 'needs': 'info.needs', 'flaky': 'info.flaky',
     'isQueue': "mode == 'queue'",
     'userMs': 'isQueue ? (needs ? work + pollMs : ackMs) : work',
     'parts': 'isQueue ? 4 : 0',
     'wrongQ': 'isQueue && needs',
     'wrongD': '!isQueue && !needs',
     'rightT': '!wrongQ && !wrongD',
     'caseName': 'lookup(caseNames, case, case)'},
   'cases': [
     {'when': 'wrongQ', 'flags': ['wrongTool']},
     {'when': 'wrongD', 'flags': ['fragile']},
     {'when': 'rightT', 'flags': ['rightTool']},
     {'when': 'true', 'vars': {'ms': 'userMs', 'parts': 'parts', 'name': 'caseName'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@userM', 'value': '=userMs', 'format': 'ms', 'tone': "=userMs > 1000 ? 'warn' : 'ok'"},
       {'label': '@partsM', 'value': '=parts', 'format': 'int', 'tone': "=parts > 0 ? 'info' : 'dim'"},
       {'label': '@downM', 'value': "=isQueue ? '@waitsRetry' : '@errorScreen'", 'tone': "=isQueue ? 'ok' : (flaky ? 'bad' : 'warn')"}]},
     {'type': 'flow', 'steps': [
       {'label': '@app', 'sub': '=text', 'tone': 'info'},
       {'label': "=isQueue ? '@broker' : '@call'", 'sub': "=isQueue ? '@brokerSub' : '@callSub'", 'tone': "=wrongQ ? 'bad' : 'neutral'"},
       {'label': '=caseName', 'sub': "=work + ' ms'", 'tone': "=rightT ? 'ok' : 'warn'"}]},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['@question', '@answer'],
      'rows': [['@q1', "=needs ? '@yes' : '@no'"], ['@q2', "=work >= 1000 ? '@yes' : '@no'"], ['@q3', "=flaky ? '@yes' : '@no'"]],
      'caption': "=needs ? '@capDirect' : '@capQueue'"},
     {'type': 'note', 'tone': "=rightT ? 'ok' : 'bad'", 'text': "=rightT ? '@rightNote' : (wrongQ ? '@wrongQNote' : '@wrongDNote')"}]})

def loc7(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Quando não usar fila', 'When not to use a queue'),
  'subtitle': T('Fila é ótima até alguém perguntar o preço da pizza e ouvir "anotado, depois te aviso"', 'Queues are great until someone asks the price of a pizza and hears "noted, I’ll get back to you"'),
  'mission': T('O app da Nona tem cinco tarefas: consultar preço, validar cupom no pagamento, mandar e-mail de confirmação, emitir nota fiscal e gerar o relatório do mês. Para cada uma, decida: fila ou chamada direta? Ache o caso em que a fila só atrapalha. Cada fila acrescenta 4 peças para operar: broker, worker, DLQ e monitoramento.',
               'Nona’s app has five tasks: checking a price, validating a coupon at checkout, sending a confirmation email, issuing an invoice and building the monthly report. For each one, decide: queue or direct call? Find the case where the queue only gets in the way. A queue adds 4 parts to operate: broker, worker, DLQ and monitoring.'),
  'predict': {'question': T('para o app mostrar o preço de uma pizza, vale colocar uma fila no meio?', 'for the app to show the price of a pizza, is it worth putting a queue in between?'),
    'options': {'yes': T('Sim, fila deixa tudo mais robusto', 'Yes, a queue makes everything more robust'), 'no': T('Não, a pessoa precisa da resposta agora', 'No, the person needs the answer now'), 'always': T('Sempre: tudo deveria passar por fila', 'Always: everything should go through a queue')}},
  'feedback': {'right': T('isso: a consulta leva 30 ms e a pessoa não consegue seguir sem a resposta. Com fila, ela recebe "anotado" e o app fica perguntando "já tem?" de tempos em tempos. Mais peças, mais demora, nenhum ganho.', 'right: the lookup takes 30 ms and the person can’t move on without the answer. With a queue, they get "noted" and the app keeps asking "is it ready?" every so often. More parts, more delay, no gain.'),
               'wrong': T('não vale: a resposta é rápida e a pessoa precisa dela para continuar. A fila só acrescenta espera, uma consulta repetida e quatro peças para operar. Fila brilha quando o trabalho é lento, instável ou pode ser feito depois.', 'it isn’t: the answer is fast and the person needs it to continue. The queue only adds waiting, repeated polling and four parts to operate. Queues shine when work is slow, flaky or can happen later.'),
               'skipped': T('sem palpite? Rode decidir --caso preco e compare fila com direto.', 'no guess? Run decide --case price and compare queue with direct.')},
  'coach': {'ui': T('palpite anotado. Escolha "preço" e alterne entre fila e direto.', 'guess noted. Pick "price" and switch between queue and direct.'),
            'cmd': T('palpite anotado. Rode decidir --caso preco e depois decidir --caso preco --modo direto.', 'guess noted. Run decide --case price and then decide --case price --mode direct.')},
  'tryNext': {'ui': T('Agora "nota fiscal" no modo direto: 3 segundos com a pessoa olhando a tela, e se o serviço da nota cair, erro na cara do cliente.', 'Now "invoice" in direct mode: 3 seconds with the person staring at the screen, and if the invoicing service goes down, an error in the customer’s face.'),
              'cmd': T('Rode decidir --caso nota --modo direto e leia o aviso.', 'Run decide --case invoice --mode direct and read the warning.')},
  'why': {'simples': T('Antes de pôr fila, faça três perguntas. A pessoa precisa da resposta agora para continuar? O trabalho é lento? O serviço do outro lado cai de vez em quando?\nSe precisa da resposta agora e é rápido (preço, cupom, login), chame direto. Se pode ser feito depois, é lento ou instável (e-mail, nota fiscal, relatório), fila. Fila não é enfeite: é mais uma coisa para ligar, vigiar e consertar.',
                       'Before adding a queue, ask three questions. Does the person need the answer now to continue? Is the work slow? Does the service on the other side go down now and then?\nIf the answer is needed now and it’s fast (price, coupon, login), call directly. If it can happen later, is slow or flaky (email, invoice, report), use a queue. A queue isn’t decoration: it’s one more thing to run, watch and fix.'),
          'dev': T('Fila traz custos fixos: broker para operar e atualizar, consumidor para implantar, DLQ, monitoramento de profundidade e idade, idempotência, rastreamento entre processos e testes mais difíceis. Vale quando há pico, trabalho lento, dependência instável, ou vários interessados no mesmo fato.\nNão vale para leituras que o usuário espera (consultas, validações), quando você precisa da resposta para decidir o próximo passo na mesma requisição, ou quando o volume é pequeno e um retry simples resolve. Request/reply por cima de fila existe, mas só se justifica quando o broker já está lá por outros motivos.',
                   'A queue has fixed costs: a broker to run and upgrade, a consumer to deploy, a DLQ, depth and age monitoring, idempotency, cross-process tracing and harder tests. It pays off with peaks, slow work, flaky dependencies, or several parties interested in the same fact.\nIt doesn’t pay off for reads the user is waiting on (queries, validations), when you need the answer to decide the next step in the same request, or when volume is low and a simple retry does the job. Request/reply over a queue exists, but it’s only justified when the broker is already there for other reasons.'),
          'especialista': T('Alternativas mais simples costumam vencer: retry com backoff e jitter mais circuit breaker numa chamada direta; um job agendado lendo uma tabela de pendências; ou a própria tabela como fila (SELECT … FOR UPDATE SKIP LOCKED no Postgres) quando o volume é modesto e você quer a mesma transação do banco.\nCuidado também com "fila como banco de dados": consultar o estado de um pedido varrendo mensagens não funciona; o estado mora num banco e a fila só transporta mudanças. E fila não resolve consistência entre dois sistemas sozinha: se você grava no banco e publica a mensagem em passos separados, um deles pode falhar. Para isso existe o padrão outbox, que a trilha Prática detalha.',
                            'Simpler alternatives often win: retry with backoff and jitter plus a circuit breaker on a direct call; a scheduled job reading a pending table; or the table itself as a queue (SELECT … FOR UPDATE SKIP LOCKED in Postgres) when volume is modest and you want the same database transaction.\nAlso beware of "the queue as a database": looking up an order’s state by scanning messages doesn’t work; state lives in a database and the queue only carries changes. And a queue doesn’t solve consistency between two systems by itself: if you write to the database and publish the message in separate steps, one of them can fail. That’s what the outbox pattern is for, covered in the Practice track.')},
  'break': {'mission': {'ui': T('hora de quebrar: escolha "preço" com fila.', 'time to break it: pick "price" with a queue.'),
                        'cmd': T('hora de quebrar: rode decidir --caso preco --modo fila', 'time to break it: run decide --case price --mode queue')},
            'success': T('Quebrou: para mostrar {name}, a pessoa esperou {ms} ms em vez de 30, e o time ganhou {parts} peças para operar. A fila resolveu um problema que não existia.',
                         'Broken: to show {name}, the person waited {ms} ms instead of 30, and the team got {parts} parts to operate. The queue solved a problem that didn’t exist.'),
            'calm': T('{name}: escolha certa, resposta para a pessoa em {ms} ms. Para quebrar, coloque uma fila onde a pessoa precisa da resposta na hora.',
                      '{name}: right choice, answer to the person in {ms} ms. To break it, put a queue where the person needs the answer right away.')},
  'hints': {'ui': T(['Escolha um caso e um modo; a tabela mostra as três perguntas.', 'Fila atrapalha quando a resposta é rápida e a pessoa precisa dela agora.', 'Escolha "preço" com fila.'],
                    ['Pick a case and a mode; the table shows the three questions.', 'A queue gets in the way when the answer is fast and the person needs it now.', 'Pick "price" with a queue.']),
            'cmd': T(['--caso aceita email, preco, cupom, nota ou relatorio.', '--modo aceita fila ou direto.', 'decidir --caso preco --modo fila'],
                     ['--case takes email, price, coupon, invoice or report.', '--mode takes queue or direct.', 'decide --case price --mode queue'])},
  'errors': {'notInEnum.case': T('Os casos são email, preco, cupom, nota e relatorio.', 'The cases are email, price, coupon, invoice and report.'), 'notInEnum.mode': T('Use fila ou direto.', 'Use queue or direct.')},
  'controls': {'arg': T('Sistema', 'System'), 'case': T('Tarefa', 'Task'), 'mode': T('Como fazer', 'How to do it')},
  'scene': {'label': T('Fila ou chamada direta?', 'Queue or direct call?'), 'empty': T('Rode para decidir.', 'Run to decide.'),
    'userM': T('tempo até a pessoa ver o resultado', 'time until the person sees the result'), 'partsM': T('peças a mais para operar', 'extra parts to operate'), 'downM': T('se o serviço de destino cair', 'if the target service goes down'),
    'waitsRetry': T('espera e tenta de novo', 'waits and retries'), 'errorScreen': T('erro na tela', 'error on screen'),
    'app': T('app', 'app'), 'broker': T('fila + worker', 'queue + worker'), 'brokerSub': T('"anotado", resultado depois', '"noted", result later'), 'call': T('chamada direta', 'direct call'), 'callSub': T('espera a resposta', 'waits for the answer'),
    'tableLabel': T('As três perguntas', 'The three questions'), 'question': T('pergunta', 'question'), 'answer': T('resposta', 'answer'),
    'q1': T('A pessoa precisa do resultado agora para continuar?', 'Does the person need the result now to continue?'), 'q2': T('O trabalho leva 1 segundo ou mais?', 'Does the work take 1 second or more?'), 'q3': T('O serviço de destino costuma falhar?', 'Does the target service fail now and then?'),
    'yes': T('sim', 'yes'), 'no': T('não', 'no'),
    'capDirect': T('Precisa da resposta agora: chamada direta, com timeout e retry curto.', 'Needs the answer now: direct call, with a timeout and a short retry.'), 'capQueue': T('Pode ficar para depois: fila, com DLQ e consumidor idempotente.', 'Can happen later: queue, with a DLQ and an idempotent consumer.'),
    'rightNote': T('Boa escolha para {name}.', 'Good choice for {name}.'),
    'wrongQNote': T('Fila para {name}? A pessoa fica esperando, o app fica perguntando "já tem?", e o time ganha {parts} peças para cuidar.', 'A queue for {name}? The person waits, the app keeps asking "is it ready?", and the team gets {parts} parts to look after.'),
    'wrongDNote': T('Direto para {name}: a pessoa fica {ms} ms olhando a tela, e se o serviço cair, o erro vai parar na cara dela. Aqui a fila vale a pena.', 'Direct for {name}: the person stares at the screen for {ms} ms, and if the service goes down, the error lands in their face. Here the queue is worth it.')},
  'data': {'caseNames': {'price': 'o preço', 'coupon': 'o cupom', 'email': 'o e-mail de confirmação', 'invoice': 'a nota fiscal', 'report': 'o relatório do mês'} if pt else
                        {'price': 'the price', 'coupon': 'the coupon', 'email': 'the confirmation email', 'invoice': 'the invoice', 'report': 'the monthly report'}},
  'recipe': {'steps': [
     T('Liste 5 funcionalidades de um sistema que você usa ou constrói (no trabalho, na escola, num app).', 'List 5 features of a system you use or build (at work, at school, in an app).'),
     T('Para cada uma, responda as três perguntas da cena: precisa da resposta agora? leva 1 s ou mais? o destino falha às vezes?', 'For each one, answer the scene’s three questions: is the answer needed now? does it take 1 s or more? does the target fail sometimes?'),
     T('Marque "fila" só onde a primeira resposta for não e pelo menos uma das outras for sim. Para o resto, escreva qual timeout e quantas tentativas usaria na chamada direta.', 'Mark "queue" only where the first answer is no and at least one of the others is yes. For the rest, write which timeout and how many retries you’d use on the direct call.')],
   'ok': T('cada funcionalidade tem uma escolha com justificativa, e pelo menos uma ficou como chamada direta. Se todas viraram fila, revise a primeira pergunta.', 'every feature has a choice with a reason, and at least one stayed a direct call. If all became queues, review the first question.')}}

t7 = {'pt': {'objectives': ['Aplicar três perguntas para decidir entre fila e chamada direta.', 'Reconhecer o custo operacional de uma fila.', 'Conhecer alternativas mais simples.'], 'minutes': 15,
  'activity': 'Debate em duplas: cada dupla recebe 3 funcionalidades de um app conhecido (banco, delivery, rede social) e defende "fila" ou "direto" para cada uma em 1 minuto. A turma vota.',
  'discussion': ['Que funcionalidade você já viu ficar mais lenta por estar "assíncrona demais"?', 'Quem paga o custo de operar uma fila na sua equipe?'],
  'misconceptions': ['"Arquitetura moderna é tudo por fila." Fila é ferramenta para um tipo de problema; para consultas rápidas, ela só acrescenta espera.']},
 'en': {'objectives': ['Apply three questions to choose between a queue and a direct call.', 'Recognize a queue’s operating cost.', 'Know simpler alternatives.'], 'minutes': 15,
  'activity': 'Pair debate: each pair gets 3 features of a well-known app (bank, delivery, social network) and argues "queue" or "direct" for each one in 1 minute. The class votes.',
  'discussion': ['Which feature have you seen get slower for being "too async"?', 'Who pays the cost of running a queue on your team?'],
  'misconceptions': ['"Modern architecture means everything goes through a queue." A queue is a tool for one kind of problem; for fast lookups it only adds waiting.']}}
write('07-quando-nao-usar-fila', s7, loc7('pt'), loc7('en'), t7)

# ================================================================== 8 · missão: Black Friday
s8 = step('msg-missao-black-friday', 8, TRACK, 25, ['missao', 'mensageria', 'pagamentos', 'idempotencia', 'dlq', 'prefetch'],
  ['msg-ack-e-garantias', 'msg-consumidor-idempotente', 'msg-ordem-dlq-prefetch'], SIM,
  loc('configurar', 'configure'),
  {'name': 'text', 'required': False, 'default': loc('pagamentos', 'payments'), 'ui': 'text'},
  [flag('ack', 'ack', 'ack', 'enum', options=[opt('auto', 'auto', 'auto'), opt('manual', 'manual', 'manual')], default='auto', ui='select'),
   flag('key', 'chave', 'key', 'enum', options=[opt('none', 'nenhuma', 'none'), opt('message', 'mensagem', 'message'), opt('order', 'pedido', 'order')], default='none', ui='select'),
   flag('dlq', 'dlq', 'dlq', 'bool', default=False, ui='switch'),
   flag('prefetch', 'prefetch', 'prefetch', 'int', min=0, max=1000, uiMax=300, default=0, ui='slider'),
   flag('confirms', 'confirmacao', 'confirms', 'bool', default=False, ui='switch')],
  None, 'passed',
  {'live': True,
   'consts': {'payments': 20000, 'crashes': 3, 'unlimitedGrab': 2500, 'poisonN': 5, 'resendN': 12, 'unconfirmedLost': 37, 'maxPrefetch': 50, 'gatewaySec': 0.8},
   'compute': {
     'inflight': 'prefetch == 0 ? unlimitedGrab : prefetch',
     'isManual': "ack == 'manual'",
     'lostAck': 'isManual ? 0 : crashes * inflight',
     'lostPub': 'confirms ? 0 : unconfirmedLost',
     'lostN': 'lostAck + lostPub',
     'redeliveredN': 'isManual ? crashes * inflight : 0',
     'brokerDups': 'isManual ? crashes : 0',
     'resends': 'confirms ? resendN : 0',
     'dupsN': "key == 'none' ? brokerDups + resends : (key == 'message' ? resends : 0)",
     'prefOk': 'prefetch >= 1 && prefetch <= maxPrefetch',
     'holdSec': 'round(inflight * gatewaySec)',
     'okCount': '(lostN == 0 ? 1 : 0) + (dupsN == 0 ? 1 : 0) + (dlq ? 1 : 0) + (prefOk ? 1 : 0)',
     'allOk': 'okCount == 4'},
   'cases': [
     {'when': 'allOk', 'flags': ['passed']},
     {'when': 'lostN > 0', 'flags': ['salesLost']},
     {'when': 'dupsN > 0', 'flags': ['doubleCharge']},
     {'when': 'true', 'vars': {'lost': 'lostN', 'dups': 'dupsN', 'redelivered': 'redeliveredN', 'inflight': 'inflight', 'p': 'prefetch', 'ok': 'okCount'}}],
   'widgets': [
     {'type': 'checks', 'label': '@checks', 'items': [
       {'label': '@cLost', 'ok': '=lostN == 0', 'why': '@cLostWhy'},
       {'label': '@cDup', 'ok': '=dupsN == 0', 'why': "=key == 'message' ? '@cDupWhyMsg' : '@cDupWhy'"},
       {'label': '@cPoison', 'ok': '=dlq', 'why': '@cPoisonWhy'},
       {'label': '@cPrefetch', 'ok': '=prefOk', 'why': "=prefetch == 0 ? '@cPrefetchWhy0' : '@cPrefetchWhy'"}]},
     {'type': 'metrics', 'items': [
       {'label': '@lostM', 'value': '=lostN', 'format': 'int', 'tone': "=lostN > 0 ? 'bad' : 'ok'"},
       {'label': '@dupM', 'value': '=dupsN', 'format': 'int', 'tone': "=dupsN > 0 ? 'bad' : 'ok'"},
       {'label': '@redelM', 'value': '=redeliveredN', 'format': 'int', 'tone': "=redeliveredN > 300 ? 'warn' : 'dim'"},
       {'label': '@holdM', 'value': '=holdSec', 'format': 'int', 'tone': "=prefOk ? 'ok' : 'warn'"}]},
     {'type': 'queue', 'label': '@queueLabel', 'producer': '@checkout', 'empty': '@emptyQueue',
      'messages': "=dlq ? fill(12, '#') : concat(['!☠', '!☠'], fill(10, '#'))",
      'consumers': [{'label': 'pay-worker-1', 'note': "=prefetch == 0 ? '@grabsAll' : '@holding'", 'tone': "=prefOk ? 'ok' : 'warn'"},
                    {'label': 'pay-worker-2', 'note': "=prefetch == 0 ? '@starved' : '@holding'", 'tone': "=prefOk ? 'ok' : 'dim'"},
                    {'label': '@gateway', 'note': "=key == 'order' ? '@idemOn' : '@idemOff'", 'tone': "=key == 'order' ? 'ok' : 'bad'"}],
      'dlq': "=dlq ? fill(poisonN, '☠') : []", 'dlqLabel': 'DLQ'},
     {'type': 'terminal', 'label': '@terminal', 'lines': [
       "=isManual ? '@tAckManual' : '@tAckAuto'",
       "=confirms ? '@tConfirmOn' : '@tConfirmOff'",
       "=key == 'order' ? '@tKeyOrder' : (key == 'message' ? '@tKeyMsg' : '@tKeyNone')",
       "=dlq ? '@tDlqOn' : '@tDlqOff'",
       "=prefOk ? '@tPrefOk' : '@tPrefBad'"]}]},
  kind='mission')

def loc8(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Missão: Black Friday sem venda perdida nem cobrança duplicada', 'Mission: Black Friday with no lost sale and no double charge'),
  'subtitle': T('20 mil pagamentos em uma hora, workers que caem e um gateway lento', '20 thousand payments in an hour, workers that crash and a slow gateway'),
  'mission': T('Na Black Friday, a Nona vende vale-pizza pelo site: 20.000 pagamentos numa hora. O checkout publica cada pagamento numa fila e dois workers cobram no gateway (0,8 s por cobrança). Durante o pico, os workers vão cair 3 vezes, o broker vai trocar de nó uma vez e 5 pagamentos chegam com dados de cartão inválidos. A configuração atual é a pior possível. Conserte até os quatro critérios ficarem verdes. (Capacidade é outro assunto: 20.000 × 0,8 s são 16.000 s de trabalho, mais do que dois workers fazem numa hora; a simulação não mede isso, mas em produção você precisaria de mais consumidores.)',
               'On Black Friday, Nona sells pizza vouchers online: 20,000 payments in one hour. Checkout publishes each payment to a queue and two workers charge the gateway (0.8 s per charge). During the peak, workers will crash 3 times, the broker will fail over once and 5 payments arrive with invalid card data. The current setup is the worst possible. Fix it until all four criteria turn green. (Capacity is a separate matter: 20,000 × 0.8 s is 16,000 s of work, more than two workers can do in an hour; the simulation doesn’t measure that, but in production you would need more consumers.)'),
  'coach': {'ui': T('Mexa nos controles; os critérios mudam enquanto você ajusta. Cada um que falhar diz o porquê.', 'Move the controls; the criteria change as you adjust. Each failing one says why.'),
            'cmd': T('Edite o comando e rode. Cada critério que falhar diz o porquê. Tudo que você precisa apareceu nas lições 3, 4 e 5.', 'Edit the command and run it. Each failing criterion says why. Everything you need showed up in lessons 3, 4 and 5.')},
  'why': {'simples': T('Você montou o caminho seguro de um pagamento: o broker confirma que guardou (confirmação do produtor), o worker só diz "terminei" depois de cobrar (ack manual), a cobrança repetida é barrada pelo número do pedido (idempotência), o pagamento impossível vai para a gaveta (DLQ) e ninguém segura mais trabalho do que consegue fazer (prefetch).\nRepare no efeito dominó: ligar a confirmação faz o checkout reenviar quando fica em dúvida, e o ack manual faz o broker reentregar quando um worker cai. As duas coisas evitam perder venda, mas criam repetições, e é a chave do pedido que impede a cobrança dupla.',
                       'You built the safe path for a payment: the broker confirms it stored it (publisher confirms), the worker only says "done" after charging (manual ack), a repeated charge is blocked by the order number (idempotency), the impossible payment goes to the drawer (DLQ) and nobody holds more work than they can do (prefetch).\nNotice the domino effect: turning on confirms makes checkout resend when in doubt, and manual ack makes the broker redeliver when a worker crashes. Both prevent lost sales but create repeats, and the order key is what stops the double charge.'),
          'dev': T('A receita: publisher confirms no produtor (e reenvio com a mesma chave de idempotência quando a confirmação não vem), mensagens persistentes numa quorum queue, ack manual depois de gravar o resultado, prefetch dimensionado pelo tempo de processamento (aqui, cada mensagem segura 0,8 s, então 50 na mão são 40 s de trabalho que voltam para a fila se o worker cair), DLX por política e um limite de entregas.\nNo consumidor: tabela de chaves processadas com unicidade, mesma transação do efeito, e a chave do pedido repassada ao gateway, que também deve ser idempotente.',
                   'The recipe: publisher confirms on the producer (and resend with the same idempotency key when the confirm doesn’t come), persistent messages on a quorum queue, manual ack after storing the result, prefetch sized by processing time (here each message takes 0.8 s, so 50 in hand is 40 s of work that goes back to the queue if the worker crashes), a DLX via policy and a delivery limit.\nOn the consumer: a processed-keys table with a uniqueness constraint, in the same transaction as the effect, and the order key passed to the gateway, which should be idempotent too.'),
          'especialista': T('Para produção ainda faltam: o padrão outbox no checkout (gravar o pedido e a mensagem na mesma transação e publicar depois, para não existir "pedido salvo sem mensagem"), alertas de profundidade e idade da fila e da DLQ, um processo para reprocessar a DLQ, testes de caos (derrubar worker e nó no meio do pico), e capacidade calculada antes: 20.000 cobranças × 0,8 s são 16.000 s de trabalho, então dois workers sequenciais não terminam numa hora; você precisa de mais consumidores ou de concorrência dentro deles.\nNo Kafka, o desenho equivalente é commit de offset depois de processar, produtor idempotente, chave do pedido como chave da mensagem para manter a ordem por pedido, um tópico de erro como DLQ, e a mesma idempotência no efeito externo.',
                            'For production you still need: the outbox pattern on checkout (write the order and the message in the same transaction and publish afterwards, so "order saved without a message" can’t happen), depth and age alerts on the queue and the DLQ, a DLQ reprocessing process, chaos tests (kill a worker and a node mid-peak), and capacity worked out up front: 20,000 charges × 0.8 s is 16,000 s of work, so two sequential workers can’t finish in an hour; you need more consumers or concurrency inside them.\nIn Kafka, the equivalent design is committing offsets after processing, an idempotent producer, the order id as the message key to keep per-order ordering, an error topic as the DLQ, and the same idempotency on the external effect.')},
  'success': T('Missão cumprida! Nenhuma venda perdida, nenhuma cobrança em dobro: {redelivered} reentregas e os reenvios do checkout foram barrados pela chave do pedido, os 5 cartões inválidos estão na DLQ esperando um humano, e cada worker segura no máximo {p} pagamentos. A Nona pode dormir na Black Friday.',
               'Mission accomplished! No lost sale, no double charge: {redelivered} redeliveries and checkout’s resends were blocked by the order key, the 5 invalid cards are in the DLQ waiting for a human, and each worker holds at most {p} payments. Nona can sleep through Black Friday.'),
  'errors': {'notInEnum.ack': T('Use auto ou manual.', 'Use auto or manual.'), 'notInEnum.key': T('Use nenhuma, mensagem ou pedido.', 'Use none, message or order.'),
             'notBool.dlq': T('Use sim ou nao.', 'Use yes or no.'), 'notBool.confirms': T('Use sim ou nao.', 'Use yes or no.'),
             'belowMin.prefetch': T('Prefetch não fica negativo. 0 é sem limite (e é um dos problemas).', 'Prefetch can’t be negative. 0 means unlimited (and that’s one of the problems).'),
             'aboveMax.prefetch': T('Até 1000 nesta simulação.', 'Up to 1000 in this simulation.')},
  'controls': {'arg': T('Fila', 'Queue'), 'ack': T('Ack do worker', 'Worker ack'), 'key': T('Chave de idempotência', 'Idempotency key'), 'dlq': T('DLQ para pagamentos impossíveis', 'DLQ for impossible payments'),
               'prefetch': T('Prefetch por worker (0 = sem limite)', 'Prefetch per worker (0 = unlimited)'), 'confirms': T('Confirmação do broker ao checkout', 'Broker confirms to checkout')},
  'scene': {'label': T('Pagamentos da Black Friday', 'Black Friday payments'), 'empty': T('Rode para abrir as vendas.', 'Run to open sales.'),
    'trackDone': T('Você concluiu a trilha Fundamentos de Mensageria e streaming.', 'You completed the Messaging and streaming Foundations track.'),
    'checks': T('Critérios da missão', 'Mission criteria'),
    'cLost': T('Nenhuma venda perdida', 'No lost sale'), 'cLostWhy': T('{lostAck} perdidas com ack automático quando os workers caíram + {lostPub} que o broker nunca confirmou na troca de nó', '{lostAck} lost to automatic ack when workers crashed + {lostPub} the broker never confirmed during failover'),
    'cDup': T('Nenhuma cobrança em dobro', 'No double charge'), 'cDupWhy': T('{dupsN} clientes cobrados duas vezes: reentregas e reenvios passaram sem chave', '{dupsN} customers charged twice: redeliveries and resends got through with no key'),
    'cDupWhyMsg': T('{dupsN} cobranças em dobro: o reenvio do checkout chega com id de mensagem novo', '{dupsN} double charges: checkout’s resend arrives with a new message id'),
    'cPoison': T('Cartões inválidos não travam a fila', 'Invalid cards don’t jam the queue'), 'cPoisonWhy': T('sem DLQ, os 5 pagamentos inválidos voltam para a fila sem parar', 'without a DLQ, the 5 invalid payments keep going back to the queue'),
    'cPrefetch': T('Prefetch entre 1 e 50', 'Prefetch between 1 and 50'), 'cPrefetchWhy': T('com {inflight} na mão, cada worker segura uns {holdSec} s de cobranças que voltam todas se ele cair', 'with {inflight} in hand, each worker holds about {holdSec} s of charges that all come back if it crashes'),
    'cPrefetchWhy0': T('sem limite, um worker puxa {inflight} pagamentos e o outro fica sem nada', 'unlimited, one worker pulls {inflight} payments and the other gets nothing'),
    'lostM': T('vendas perdidas', 'lost sales'), 'dupM': T('cobranças em dobro', 'double charges'), 'redelM': T('reentregas', 'redeliveries'), 'holdM': T('segundos de trabalho na mão de cada worker', 'seconds of work in each worker’s hand'),
    'queueLabel': T('Fila pagamentos', 'Payments queue'), 'checkout': T('checkout', 'checkout'), 'emptyQueue': T('fila vazia', 'empty queue'),
    'grabsAll': T('puxou tudo que pôde', 'grabbed all it could'), 'starved': T('sem trabalho', 'no work'), 'holding': T('segura até {p}', 'holds up to {p}'),
    'gateway': T('gateway de pagamento', 'payment gateway'), 'idemOn': T('recebe a chave do pedido', 'gets the order key'), 'idemOff': T('cobra tudo que chega', 'charges whatever arrives'),
    'terminal': T('Revisão da configuração', 'Configuration review'),
    'tAckManual': T('+ ack manual depois de cobrar', '+ manual ack after charging'), 'tAckAuto': T('! ack automático: pagamento some se o worker cair', '! automatic ack: payment vanishes if the worker crashes'),
    'tConfirmOn': T('+ publisher confirms ligado no checkout', '+ publisher confirms on at checkout'), 'tConfirmOff': T('! checkout publica sem saber se o broker guardou', '! checkout publishes without knowing if the broker stored it'),
    'tKeyOrder': T('+ idempotência pelo número do pedido', '+ idempotency by order number'), 'tKeyMsg': T('? idempotência pelo id da mensagem: reenvio passa', '? idempotency by message id: resends get through'), 'tKeyNone': T('! sem idempotência', '! no idempotency'),
    'tDlqOn': T('+ DLQ por política, com limite de entregas', '+ DLQ via policy, with a delivery limit'), 'tDlqOff': T('! sem DLQ: mensagem envenenada em laço', '! no DLQ: poison message loops'),
    'tPrefOk': T('+ prefetch {p}', '+ prefetch {p}'), 'tPrefBad': T('! prefetch {p}: fora da faixa segura para cobranças de 0,8 s', '! prefetch {p}: outside the safe range for 0.8 s charges')},
  'data': {},
  'recipe': {'steps': [
     T('Pegue um fluxo de pagamento ou pedido que você conhece e responda por escrito: o produtor sabe se o broker guardou a mensagem? O consumidor confirma antes ou depois do efeito? Qual é a chave de idempotência? Para onde vai a mensagem que sempre falha? Quantas mensagens cada consumidor segura?', 'Take a payment or order flow you know and answer in writing: does the producer know whether the broker stored the message? Does the consumer ack before or after the effect? What is the idempotency key? Where does the always-failing message go? How many messages does each consumer hold?'),
     T('Suba o RabbitMQ como na lição 1 (' + DOCKER + '). Em outro terminal, aplique uma DLX por política: docker exec rabbitmq rabbitmqctl set_policy DLX "^pagamentos$" \'{"dead-letter-exchange":"pagamentos.dlx"}\' --apply-to queues (o JSON entre aspas simples funciona no bash/zsh, não no PowerShell nem no cmd; lá, use o WSL ou escape as aspas duplas). Confira em Admin → Policies.',
       'Start RabbitMQ as in lesson 1 (' + DOCKER + '). In another terminal, apply a DLX via policy: docker exec rabbitmq rabbitmqctl set_policy DLX "^pagamentos$" \'{"dead-letter-exchange":"pagamentos.dlx"}\' --apply-to queues (the single-quoted JSON works in bash/zsh, not in PowerShell or cmd; there, use WSL or escape the double quotes). Check it under Admin → Policies.'),
     T('Instale o cliente (pip install pika) e crie setup.py, que declara a exchange pagamentos.dlx, a fila pagamentos.dlq ligada a ela e a fila pagamentos (a política já a manda para a DLX):\nimport pika\nch = pika.BlockingConnection(pika.ConnectionParameters("localhost")).channel()\nch.exchange_declare("pagamentos.dlx", "fanout")\nch.queue_declare("pagamentos.dlq", durable=True)\nch.queue_bind("pagamentos.dlq", "pagamentos.dlx")\nch.queue_declare("pagamentos", durable=True)\nRode python setup.py uma vez.',
       'Install the client (pip install pika) and create setup.py, which declares the pagamentos.dlx exchange, the pagamentos.dlq queue bound to it and the pagamentos queue (the policy already points it at the DLX):\nimport pika\nch = pika.BlockingConnection(pika.ConnectionParameters("localhost")).channel()\nch.exchange_declare("pagamentos.dlx", "fanout")\nch.queue_declare("pagamentos.dlq", durable=True)\nch.queue_bind("pagamentos.dlq", "pagamentos.dlx")\nch.queue_declare("pagamentos", durable=True)\nRun python setup.py once.'),
     T('Crie consumer.py: é o worker da lição de ack (ack manual) com a tabela processados da lição de idempotência e um pagamento "invalido" que ele rejeita sem recolocar na fila:\nimport pika, sqlite3, time\ndb = sqlite3.connect("pagamentos.db")\ndb.execute("CREATE TABLE IF NOT EXISTS processados (chave TEXT PRIMARY KEY)")\nch = pika.BlockingConnection(pika.ConnectionParameters("localhost")).channel()\nch.basic_qos(prefetch_count=5)\ndef cobra(ch, m, p, body):\n    pedido = body.decode()\n    if pedido == "invalido":\n        ch.basic_reject(delivery_tag=m.delivery_tag, requeue=False)\n        return\n    with db:\n        novo = db.execute("INSERT OR IGNORE INTO processados VALUES (?)", (pedido,)).rowcount\n        if novo:\n            time.sleep(0.2)  # aqui entraria a cobrança no gateway\n    ch.basic_ack(delivery_tag=m.delivery_tag)\nch.basic_consume(queue="pagamentos", on_message_callback=cobra, auto_ack=False)\nch.start_consuming()\nRode python consumer.py (ele fica esperando mensagens).',
       'Create consumer.py: it is the worker from the ack lesson (manual ack) plus the processed table from the idempotency lesson, and it rejects an "invalido" payment without requeueing:\nimport pika, sqlite3, time\ndb = sqlite3.connect("pagamentos.db")\ndb.execute("CREATE TABLE IF NOT EXISTS processados (chave TEXT PRIMARY KEY)")\nch = pika.BlockingConnection(pika.ConnectionParameters("localhost")).channel()\nch.basic_qos(prefetch_count=5)\ndef cobra(ch, m, p, body):\n    pedido = body.decode()\n    if pedido == "invalido":\n        ch.basic_reject(delivery_tag=m.delivery_tag, requeue=False)\n        return\n    with db:\n        novo = db.execute("INSERT OR IGNORE INTO processados VALUES (?)", (pedido,)).rowcount\n        if novo:\n            time.sleep(0.2)  # the gateway charge would go here\n    ch.basic_ack(delivery_tag=m.delivery_tag)\nch.basic_consume(queue="pagamentos", on_message_callback=cobra, auto_ack=False)\nch.start_consuming()\nRun python consumer.py (it waits for messages).'),
     T('Em outro terminal, crie publish.py, que publica 100 pagamentos (com confirmação do broker) e 1 inválido, e rode python publish.py:\nimport pika\nch = pika.BlockingConnection(pika.ConnectionParameters("localhost")).channel()\nch.confirm_delivery()\nfor i in range(1, 101):\n    ch.basic_publish("", "pagamentos", f"P{i}", pika.BasicProperties(delivery_mode=2))\nch.basic_publish("", "pagamentos", "invalido")',
       'In another terminal, create publish.py, which publishes 100 payments (with broker confirms) and 1 invalid one, and run python publish.py:\nimport pika\nch = pika.BlockingConnection(pika.ConnectionParameters("localhost")).channel()\nch.confirm_delivery()\nfor i in range(1, 101):\n    ch.basic_publish("", "pagamentos", f"P{i}", pika.BasicProperties(delivery_mode=2))\nch.basic_publish("", "pagamentos", "invalido")'),
     T('Faça o teste de caos: rode publish.py de novo com o consumidor ligado, derrube o consumidor no meio (Ctrl+C), suba de novo e conte as chaves: python3 -c "import sqlite3; print(sqlite3.connect(\'pagamentos.db\').execute(\'select count(*) from processados\').fetchone())"',
       'Run the chaos test: run publish.py again with the consumer up, kill the consumer halfway (Ctrl+C), start it again and count the keys: python3 -c "import sqlite3; print(sqlite3.connect(\'pagamentos.db\').execute(\'select count(*) from processados\').fetchone())"')],
   'ok': T('em Admin → Policies aparece a política DLX; depois de derrubar e religar o consumidor, a tabela de processados tem exatamente 100 chaves, a fila pagamentos zerou e a mensagem "invalido" está em pagamentos.dlq.', 'under Admin → Policies you see the DLX policy; after killing and restarting the consumer, the processed table has exactly 100 keys, the pagamentos queue is empty and the "invalido" message is in pagamentos.dlq.')}}

t8 = {'pt': {'objectives': ['Combinar ack, confirmação, idempotência, DLQ e prefetch num fluxo real.', 'Perceber como uma correção cria o próximo problema.', 'Justificar cada configuração.'], 'minutes': 25,
  'activity': 'Em grupos, consertem a configuração e depois expliquem para a turma, em 2 minutos, por que ligar a confirmação sem chave de idempotência piora a cobrança em dobro.',
  'discussion': ['Qual dos quatro critérios seria o mais caro de descobrir em produção?', 'O que mais você monitoraria na noite da Black Friday?'],
  'misconceptions': ['"Exactly-once é uma opção do broker." O efeito único vem da combinação de entrega pelo menos uma vez com consumidor idempotente.']},
 'en': {'objectives': ['Combine ack, confirms, idempotency, DLQ and prefetch in a real flow.', 'Notice how one fix creates the next problem.', 'Justify each setting.'], 'minutes': 25,
  'activity': 'In groups, fix the configuration and then explain to the class, in 2 minutes, why turning on confirms without an idempotency key makes double charges worse.',
  'discussion': ['Which of the four criteria would be the most expensive to discover in production?', 'What else would you monitor on Black Friday night?'],
  'misconceptions': ['"Exactly-once is a broker setting." A single effect comes from combining at-least-once delivery with an idempotent consumer.']}}
write('08-missao-black-friday', s8, loc8('pt'), loc8('en'), t8)
print('ok: mensageria-e-streaming/fundamentos (8 passos)')
