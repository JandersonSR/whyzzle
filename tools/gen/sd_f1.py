"""System design · Fundamentos F1 · Como sistemas grandes funcionam (6 lições + missão).
Gera content/system-design/fundamentos/NN-slug/{step,pt,en,teacher}.json. Rode com python3.

Todos os números das cenas são simulados e determinísticos. Onde há fila, a latência usa a aproximação
do p95 de uma fila M/M/1: p95 ≈ 3 × tempo de serviço / (1 − utilização) (ln 20 ≈ 3), com corte num tempo-limite."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write as _write, flag, step

TOPIC, TRACK = 'system-design', 'fundamentos'
def write(folder, s, pt, en, teacher): _write(TOPIC, TRACK, folder, s, pt, en, teacher)
def opt(id, pt, en): return {'id': id, 'pt': pt, 'en': en}
def loc(pt, en): return {'pt': pt, 'en': en}
SIM = ['simulado']

def p95_expr(load, cap, s, timeout=5000):
  """M/M/1-style p95 in ms, capped at the timeout when the server is (almost) full."""
  rho = f'(({load}) / ({cap}))'
  return f'{rho} >= 0.98 ? {timeout} : min({timeout}, round(3 * {s} / (1 - {rho})))'

def served_expr(load, cap):
  """Fraction of the requests a server can answer (1 when it keeps up)."""
  return f'(({load}) <= 0 ? 1 : min(1, ({cap}) / ({load})))'

# ---------------------------------------------------------------- shared recipe snippets (real files, multi-line)
NGINX_IMG = 'nginx:1.30'
WHOAMI = 'traefik/whoami'
REDIS_IMG = 'redis:8'
PG_IMG = 'postgres:18'

def compose_scale():
  return ('name: escola\n'
          'services:\n'
          '  app:\n'
          f'    image: {WHOAMI}\n'
          '  lb:\n'
          f'    image: {NGINX_IMG}\n'
          '    ports:\n'
          '      - "8080:80"\n'
          '    volumes:\n'
          '      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro\n'
          '    depends_on:\n'
          '      - app')

NGINX_SCALE = ('upstream app {\n'
               '    server app:80;\n'
               '}\n'
               'server {\n'
               '    listen 80;\n'
               '    location / {\n'
               '        proxy_pass http://app;\n'
               '    }\n'
               '}')

def compose_lb():
  return ('name: escola\n'
          'services:\n'
          '  app1:\n'
          f'    image: {WHOAMI}\n'
          '  app2:\n'
          f'    image: {WHOAMI}\n'
          '  lb:\n'
          f'    image: {NGINX_IMG}\n'
          '    ports:\n'
          '      - "8080:80"\n'
          '    volumes:\n'
          '      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro\n'
          '    depends_on:\n'
          '      - app1\n'
          '      - app2')

NGINX_LB = ('upstream cantina {\n'
            '    server app1:80 max_fails=1 fail_timeout=10s;\n'
            '    server app2:80 max_fails=1 fail_timeout=10s;\n'
            '}\n'
            'server {\n'
            '    listen 80;\n'
            '    location / {\n'
            '        proxy_pass http://cantina;\n'
            '        proxy_connect_timeout 2s;\n'
            '    }\n'
            '}')

REPL_SH = ('#!/bin/bash\n'
           '# libera conexões de replicação vindas da rede do compose\n'
           'echo "host replication all all scram-sha-256" >> "$PGDATA/pg_hba.conf"')
REPL_SH_EN = ('#!/bin/bash\n'
              '# allow replication connections from the compose network\n'
              'echo "host replication all all scram-sha-256" >> "$PGDATA/pg_hba.conf"')

def compose_pg():
  return ('name: escola-banco\n'
          'services:\n'
          '  primary:\n'
          f'    image: {PG_IMG}\n'
          '    environment:\n'
          '      POSTGRES_PASSWORD: segredo\n'
          '    volumes:\n'
          '      - ./replicacao.sh:/docker-entrypoint-initdb.d/replicacao.sh:ro\n'
          '  replica:\n'
          f'    image: {PG_IMG}\n'
          '    user: postgres\n'
          '    environment:\n'
          '      PGPASSWORD: segredo\n'
          '    depends_on:\n'
          '      - primary\n'
          '    command:\n'
          '      - bash\n'
          '      - -c\n'
          '      - |\n'
          '        until pg_basebackup -h primary -U postgres -D /tmp/replica -R -X stream; do\n'
          '          rm -rf /tmp/replica\n'
          '          sleep 2\n'
          '        done\n'
          '        exec postgres -D /tmp/replica')

# ================================================================== 1 · cliente e servidor
RTT = {'near': 20, 'far': 150}
s1 = step('sd-cliente-servidor', 1, TRACK, 15, ['cliente-servidor', 'http', 'latencia', 'sessao', 'stateless'], [], SIM,
  loc('pedir', 'request'),
  {'name': 'text', 'required': False, 'default': loc('/cardapio', '/menu'), 'ui': 'text'},
  [flag('distance', 'distancia', 'distance', 'enum', options=[opt('near', 'perto', 'near'), opt('far', 'longe', 'far')], default='far', ui='select'),
   flag('trips', 'idas', 'trips', 'int', min=1, max=20, default=3, ui='slider'),
   flag('session', 'sessao', 'session', 'enum',
        options=[opt('store', 'loja', 'store'), opt('memory', 'memoria', 'memory'), opt('token', 'token', 'token')], default='store', ui='select'),
   flag('restart', 'reinicio', 'restart', 'bool', default=True, ui='switch')],
  {'options': ['serverOnly', 'oneTrip', 'threeTrips'], 'answer': 'threeTrips'}, 'sessionsLost',
  {'live': True,
   'consts': {'rtts': RTT, 'serverMs': 20, 'loggedIn': 120, 'paths': ['/precos', '/saldo', '/fotos', '/avisos']},
   'compute': {
     'rtt': 'lookup(rtts, distance, 150)',
     'per': 'rtt + serverMs',
     'pageMs': 'trips * per',
     'isMem': "session == 'memory'",
     'lost': 'isMem && restart ? loggedIn : 0',
     'kept': 'loggedIn - lost',
     'rows': ('slice([[1, text, per], [2, paths[0], 2 * per], [3, paths[1], 3 * per], [4, paths[2], 4 * per], '
              '[5, paths[3], 5 * per]], 0, min(trips, 5))')},
   'cases': [
     {'when': 'lost > 0', 'flags': ['sessionsLost']},
     {'when': 'pageMs > 1000', 'flags': ['slowPage']},
     {'when': 'true', 'vars': {'pageMs': 'pageMs', 'per': 'per', 'lost': 'lost', 'kept': 'kept', 'rtt': 'rtt'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@pageM', 'value': '=pageMs', 'format': 'ms', 'tone': "=pageMs > 1000 ? 'bad' : (pageMs > 300 ? 'warn' : 'ok')"},
       {'label': '@tripsM', 'value': '=trips', 'format': 'int', 'tone': 'info'},
       {'label': '@rttM', 'value': '=rtt', 'format': 'ms', 'tone': "=rtt > 100 ? 'warn' : 'ok'"},
       {'label': '@lostM', 'value': '=lost', 'format': 'int', 'tone': "=lost > 0 ? 'bad' : 'ok'"}]},
     {'type': 'flow', 'label': '@flowLabel', 'steps': [
       {'label': '@client', 'sub': '@clientSub', 'tone': 'info'},
       {'label': '@net', 'sub': '@netSub', 'tone': "=rtt > 100 ? 'warn' : 'ok'"},
       {'label': '@server', 'sub': '@serverSub', 'tone': "=lost > 0 ? 'bad' : 'ok'"},
       {'label': '@sessions', 'sub': "=isMem ? '@sessMem' : (session == 'token' ? '@sessToken' : '@sessStore')",
        'tone': "=isMem ? (restart ? 'bad' : 'warn') : 'ok'"}]},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['#', '@colReq', '@colEnds'], 'rows': '=rows', 'caption': '@tableCap'},
     {'type': 'terminal', 'label': '@termLabel', 'lines': [
       "='$ curl -i https://cantina.example' + text",
       'HTTP/1.1 200 OK',
       'Content-Type: application/json',
       "=session == 'token' ? 'Set-Cookie: token=eyJhbGciOi...; HttpOnly; Secure' : 'Set-Cookie: sessao=8f3a91c2...; HttpOnly; Secure'",
       "=lost > 0 ? '@termLost' : '@termKept'"]},
     {'type': 'note', 'when': '=lost > 0', 'tone': 'bad', 'text': '@lostNote'},
     {'type': 'note', 'when': '=isMem && !restart', 'tone': 'warn', 'text': '@memNote'},
     {'type': 'note', 'when': '=pageMs > 1000', 'tone': 'warn', 'text': '@slowNote'},
     {'type': 'note', 'when': '=!isMem && pageMs <= 1000', 'tone': 'ok', 'text': '@okNote'}]})

def loc1(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Cliente e servidor', 'Client and server'),
  'subtitle': T('O aluno pede no balcão, a cantina entrega: e cada ida e volta custa tempo', 'The student orders at the counter, the canteen delivers: and every round trip costs time'),
  'mission': T('A Cantina do Seu Zé ganhou um app: o aluno pede o lanche pelo celular (o cliente) e o servidor da cantina responde. O servidor responde em 20 ms, mas está hospedado longe, a 150 ms de ida e volta, e a página precisa de 3 pedidos em sequência. Descubra quanto tempo a página leva para aparecer e o que acontece com quem está logado quando o servidor reinicia no meio do recreio.',
               'Mr. Zé’s Canteen got an app: the student orders a snack on their phone (the client) and the canteen’s server answers. The server answers in 20 ms, but it is hosted far away, 150 ms per round trip, and the page needs 3 requests in sequence. Find out how long the page takes to show up and what happens to logged-in students when the server restarts in the middle of recess.'),
  'formula': T('tempo da página ≈ pedidos em sequência × (ida e volta pela rede + tempo do servidor)', 'page time ≈ requests in sequence × (network round trip + server time)'),
  'predict': {'question': T('o servidor responde em 20 ms e fica a 150 ms de ida e volta. Uma página que precisa de 3 pedidos, um depois do outro, leva quanto tempo?', 'the server answers in 20 ms and is 150 ms away per round trip. A page that needs 3 requests, one after the other, takes how long?'),
    'options': {'serverOnly': T('Uns 20 ms: o servidor é rápido', 'About 20 ms: the server is fast'),
                'oneTrip': T('Uns 170 ms: uma ida e volta mais o servidor', 'About 170 ms: one round trip plus the server'),
                'threeTrips': T('Uns 510 ms: três idas e voltas, cada uma com o servidor', 'About 510 ms: three round trips, each with the server')}},
  'feedback': {'right': T('isso! Cada pedido paga a viagem inteira: 150 ms de rede + 20 ms de servidor = 170 ms. Três em sequência são 510 ms. O servidor rápido quase não aparece na conta; quem manda é a distância e a quantidade de idas e voltas.',
                          'right! Each request pays the whole trip: 150 ms of network + 20 ms of server = 170 ms. Three in sequence is 510 ms. The fast server barely shows up in the sum; distance and the number of round trips are what matter.'),
               'wrong': T('olhe a tabela: cada pedido só começa quando o anterior volta, e cada um paga 150 ms de rede + 20 ms de servidor. 3 × 170 = 510 ms. O servidor rápido não salva quem está longe.',
                          'look at the table: each request only starts when the previous one comes back, and each pays 150 ms of network + 20 ms of server. 3 × 170 = 510 ms. A fast server doesn’t save you when it’s far away.'),
               'skipped': T('sem palpite? Rode e olhe a tabela: cada linha é um pedido e quando ele termina.', 'no guess? Run it and look at the table: each row is a request and when it finishes.')},
  'coach': {'ui': T('palpite anotado. Rode e compare o tempo da página com o tempo do servidor (20 ms).', 'guess noted. Run it and compare the page time with the server time (20 ms).'),
            'cmd': T('palpite anotado. Rode pedir /cardapio e olhe a tabela de pedidos.', 'guess noted. Run request /menu and look at the requests table.')},
  'tryNext': {'ui': T('Agora mude a distância para perto, e depois suba os pedidos para 10: veja o que pesa mais.', 'Now set the distance to near, then raise the requests to 10: see which weighs more.'),
              'cmd': T('Rode pedir /cardapio --distancia perto e depois pedir /cardapio --idas 10.', 'Run request /menu --distance near and then request /menu --trips 10.')},
  'why': {'simples': T('Na cantina, o aluno é o cliente: ele pede. O balcão é o servidor: ele responde. Na internet é igual: o celular manda um pedido (request) e o servidor devolve uma resposta (response).\nO tempo que você sente não é só o do cozinheiro. É a caminhada até o balcão e de volta, a cada pedido. Se o app pede o cardápio, espera, depois pede os preços, espera, depois o saldo… são três caminhadas. Por isso servidor longe ou página que faz muitos pedidos em fila ficam lentos, mesmo com um servidor rapidíssimo.\nE tem a memória do balcão: se o Seu Zé guarda de cabeça quem já pagou e vai ao banheiro, o substituto não sabe de nada. Melhor anotar num caderno que todo mundo enxerga.',
                       'At the canteen, the student is the client: they ask. The counter is the server: it answers. The internet works the same way: the phone sends a request and the server sends back a response.\nThe time you feel isn’t just the cook’s. It’s the walk to the counter and back, for every request. If the app asks for the menu, waits, then asks for prices, waits, then the balance… that’s three walks. That’s why a faraway server or a page that makes many requests in a row is slow, even with a lightning-fast server.\nAnd there’s the counter’s memory: if Mr. Zé keeps in his head who already paid and steps out, his replacement knows nothing. Better to write it in a notebook everybody can see.'),
          'dev': T('Cada pedido HTTP paga pelo menos uma ida e volta (RTT) da rede, mais o tempo do servidor. Abrir conexão nova custa mais idas e voltas (TCP e TLS), por isso reaproveitar conexões (keep-alive, HTTP/2) ajuda. Pedidos em sequência somam; pedidos independentes podem ir em paralelo, ou virar um pedido só.\nServidor stateless (sem estado) é o que não guarda nada importante na própria memória entre um pedido e outro. A sessão fica fora dele: numa loja compartilhada (Redis, banco) ou num token assinado que o próprio cliente carrega (cookie com JWT, por exemplo). Assim, qualquer servidor atende qualquer pedido, e reiniciar ou trocar o servidor não desloga ninguém. Sessão na memória do processo funciona até o primeiro reinício ou até existir um segundo servidor.',
                   'Every HTTP request pays at least one network round trip (RTT), plus the server time. Opening a new connection costs extra round trips (TCP and TLS), which is why reusing connections (keep-alive, HTTP/2) helps. Requests in sequence add up; independent requests can go in parallel, or become a single request.\nA stateless server keeps nothing important in its own memory between requests. The session lives outside it: in a shared store (Redis, a database) or in a signed token the client carries (a cookie with a JWT, for example). That way any server can answer any request, and restarting or replacing a server logs nobody out. A session in process memory works until the first restart, or until there is a second server.'),
          'especialista': T('Não dá para vencer a velocidade da luz: na fibra, o sinal anda a uns dois terços da velocidade da luz no vácuo, então distância vira um piso de latência que nenhuma otimização de código derruba. As saídas são chegar perto do usuário (CDN, borda, região mais próxima) e cortar idas e voltas: juntar pedidos, mandar junto o que vai ser pedido em seguida, cachear no cliente, evitar cascatas de chamadas.\nSobre sessão: token assinado tira o estado do servidor, mas revogar fica difícil (o token vale até expirar), então use validade curta e um jeito de renovar. Loja de sessão compartilhada permite revogar na hora, mas vira uma dependência que precisa ser rápida e redundante. Sticky session (prender o usuário a um servidor) esconde o problema e volta a morder no reinício e no escalonamento.',
                            'You can’t beat the speed of light: in fiber, the signal travels at about two thirds of the speed of light in a vacuum, so distance becomes a latency floor no code optimization removes. The ways out are getting close to the user (CDN, edge, nearest region) and cutting round trips: batching requests, sending along what will be asked next, caching on the client, avoiding chains of calls.\nOn sessions: a signed token removes state from the server, but revoking it is hard (the token is valid until it expires), so use short lifetimes and a way to refresh. A shared session store allows instant revocation, but it becomes a dependency that must be fast and redundant. Sticky sessions (pinning a user to one server) hide the problem and bite back on restarts and scaling.')},
  'break': {'mission': {'ui': T('hora de quebrar: guarde as sessões na memória do servidor e deixe ele reiniciar.', 'time to break it: keep sessions in the server’s memory and let it restart.'),
                        'cmd': T('hora de quebrar: rode pedir /cardapio --sessao memoria', 'time to break it: run request /menu --session memory')},
            'success': T('Quebrou: o servidor reiniciou e levou junto as sessões que moravam na memória dele. {lost} alunos foram deslogados no meio do pedido e o carrinho sumiu. Servidor bom é servidor que esquece: o que importa fica fora dele.',
                         'Broken: the server restarted and took with it the sessions living in its memory. {lost} students were logged out mid-order and their carts vanished. A good server is a forgetful server: what matters lives outside it.'),
            'calm': T('Página em {pageMs} ms ({trips} pedido(s) de {per} ms cada) e {kept} alunos continuam logados. Para quebrar, guarde as sessões na memória do servidor e deixe ele reiniciar.',
                      'Page in {pageMs} ms ({trips} request(s) of {per} ms each) and {kept} students stay logged in. To break it, keep sessions in the server’s memory and let it restart.')},
  'hints': {'ui': T(['Escolha a distância, quantos pedidos a página faz e onde a sessão fica guardada.', 'Pense no Seu Zé guardando de cabeça quem já pagou.', 'Escolha a sessão "memoria" com o reinício ligado.'],
                    ['Pick the distance, how many requests the page makes and where the session is kept.', 'Think of Mr. Zé keeping in his head who already paid.', 'Pick the "memory" session with restart on.']),
            'cmd': T(['O caminho é opcional; --distancia, --idas, --sessao e --reinicio também.', '--sessao aceita loja, memoria ou token.', 'pedir /cardapio --sessao memoria'],
                     ['The path is optional; so are --distance, --trips, --session and --restart.', '--session takes store, memory or token.', 'request /menu --session memory'])},
  'errors': {'notInEnum.distance': T('Use perto ou longe.', 'Use near or far.'),
             'belowMin.trips': T('Pelo menos 1 pedido, senão a página nem existe.', 'At least 1 request, or the page doesn’t exist.'),
             'aboveMax.trips': T('Até 20 pedidos nesta simulação (e já é muita caminhada até o balcão).', 'Up to 20 requests in this simulation (and that’s already a lot of walking to the counter).'),
             'notInEnum.session': T('Use loja, memoria ou token.', 'Use store, memory or token.'),
             'notBool.restart': T('Use sim ou nao.', 'Use yes or no.')},
  'controls': {'arg': T('Caminho pedido', 'Requested path'), 'distance': T('Distância até o servidor', 'Distance to the server'),
               'trips': T('Pedidos em sequência na página', 'Requests in sequence on the page'), 'session': T('Onde a sessão fica', 'Where the session lives'),
               'restart': T('O servidor reinicia no recreio', 'The server restarts at recess')},
  'scene': {'label': T('O app da cantina', 'The canteen app'), 'empty': T('Rode para fazer o pedido.', 'Run to place the order.'),
    'pageM': T('tempo até a página aparecer', 'time until the page shows'), 'tripsM': T('pedidos em sequência', 'requests in sequence'),
    'rttM': T('ida e volta pela rede', 'network round trip'), 'lostM': T('alunos deslogados', 'students logged out'),
    'flowLabel': T('O caminho de um pedido (simulado)', 'The path of one request (simulated)'),
    'client': T('Cliente', 'Client'), 'clientSub': T('celular do aluno', 'student’s phone'),
    'net': T('Rede', 'Network'), 'netSub': T('{rtt} ms ida e volta', '{rtt} ms round trip'),
    'server': T('Servidor', 'Server'), 'serverSub': T('20 ms para responder', '20 ms to answer'),
    'sessions': T('Sessões', 'Sessions'), 'sessMem': T('na memória do servidor', 'in the server’s memory'),
    'sessStore': T('numa loja compartilhada', 'in a shared store'), 'sessToken': T('num token assinado, com o cliente', 'in a signed token, with the client'),
    'tableLabel': T('Os pedidos da página, um depois do outro', 'The page’s requests, one after the other'),
    'colReq': T('pedido', 'request'), 'colEnds': T('termina em (ms)', 'ends at (ms)'),
    'tableCap': T('Mostra até 5 pedidos. Cada um só começa quando o anterior volta. Números simulados.', 'Shows up to 5 requests. Each one only starts when the previous one is back. Simulated numbers.'),
    'termLabel': T('Terminal (resposta simulada)', 'Terminal (simulated response)'),
    'termLost': T('! 10:00 servidor reiniciado: sessões da memória apagadas', '! 10:00 server restarted: in-memory sessions wiped'),
    'termKept': T('~ a sessão não depende da memória deste servidor', '~ the session doesn’t depend on this server’s memory'),
    'lostNote': T('{lost} alunos deslogados: a sessão morava na memória do servidor e o reinício apagou tudo. Com dois servidores seria pior: metade dos pedidos cairia no servidor que não conhece o aluno.', '{lost} students logged out: the session lived in the server’s memory and the restart wiped it. With two servers it would be worse: half the requests would land on the server that doesn’t know the student.'),
    'memNote': T('Funciona hoje, mas a sessão está na memória do servidor: some no primeiro reinício, e um segundo servidor não enxerga ninguém.', 'It works today, but the session is in the server’s memory: it vanishes on the first restart, and a second server can’t see anybody.'),
    'slowNote': T('Mais de 1 segundo para abrir a página: são {trips} idas e voltas em fila. Junte pedidos ou peça em paralelo.', 'Over 1 second to open the page: that’s {trips} round trips in a row. Batch requests or ask in parallel.'),
    'okNote': T('Ninguém foi deslogado: a sessão não depende da memória do servidor, então ele pode reiniciar ou ganhar irmãos.', 'Nobody was logged out: the session doesn’t depend on the server’s memory, so it can restart or get siblings.')},
  'data': {},
  'recipe': {'steps': [
     T('Com o Docker instalado, suba um servidor que devolve tudo o que recebeu:\ndocker run -d --name balcao -p 8080:80 ' + WHOAMI,
       'With Docker installed, start a server that sends back everything it received:\ndocker run -d --name balcao -p 8080:80 ' + WHOAMI),
     T('Faça um pedido e veja a resposta inteira (no Windows PowerShell, digite curl.exe em vez de curl):\ncurl -i http://localhost:8080/cardapio\nA primeira linha é o status da resposta. No corpo, o servidor mostra o pedido que você mandou: o método, o caminho e os cabeçalhos.',
       'Send a request and look at the whole response (in Windows PowerShell, type curl.exe instead of curl):\ncurl -i http://localhost:8080/menu\nThe first line is the response status. In the body, the server shows the request you sent: the method, the path and the headers.'),
     T('Agora finja que o servidor está longe: o parâmetro wait faz ele esperar antes de responder. Meça o tempo total:\ncurl -s -o /dev/null -w "%{time_total}\\n" "http://localhost:8080/?wait=150ms"\nRode três vezes seguidas e some: é a página com três pedidos em sequência. (No PowerShell, troque /dev/null por NUL.)',
       'Now pretend the server is far away: the wait parameter makes it wait before answering. Measure the total time:\ncurl -s -o /dev/null -w "%{time_total}\\n" "http://localhost:8080/?wait=150ms"\nRun it three times in a row and add them up: that’s the page with three requests in sequence. (In PowerShell, replace /dev/null with NUL.)'),
     T('Desligue o balcão: docker rm -f balcao', 'Close the counter: docker rm -f balcao')],
   'ok': T('o curl -i começa com HTTP/1.1 200 OK e o corpo repete o seu pedido (GET /cardapio HTTP/1.1, Host: localhost:8080, User-Agent: curl/…); com ?wait=150ms, cada time_total fica um pouco acima de 0.15, e três seguidos passam de 0,45 s.',
           'curl -i starts with HTTP/1.1 200 OK and the body echoes your request (GET /menu HTTP/1.1, Host: localhost:8080, User-Agent: curl/…); with ?wait=150ms, each time_total is a little above 0.15, and three in a row add up to more than 0.45 s.')}}

t1 = {'pt': {'objectives': ['Explicar o modelo pedido e resposta entre cliente e servidor.', 'Calcular o tempo de uma página a partir das idas e voltas.', 'Entender por que um servidor sem estado é mais fácil de reiniciar e multiplicar.'], 'minutes': 15,
  'activity': 'Teatro da cantina: um aluno é o servidor no fundo da sala, outro é o cliente na porta. Cada pedido exige caminhar até o servidor e voltar. Cronometrem uma "página" com 3 pedidos em sequência, depois com o servidor no meio da sala. Na segunda rodada, o servidor guarda de cabeça quem pagou; troquem o servidor no meio e vejam o que se perde.',
  'discussion': ['Por que um servidor muito rápido não salva uma página que faz muitos pedidos em fila?', 'Onde você guardaria a informação de quem está logado, se a escola tivesse dois servidores?'],
  'misconceptions': ['"Se o servidor é rápido, o app é rápido." A rede e o número de idas e voltas costumam pesar mais.', '"Guardar a sessão na memória é mais simples e pronto." Funciona só até o primeiro reinício ou o segundo servidor.']},
 'en': {'objectives': ['Explain the request and response model between client and server.', 'Work out a page’s time from its round trips.', 'Understand why a stateless server is easier to restart and multiply.'], 'minutes': 15,
  'activity': 'Canteen play: one student is the server at the back of the room, another is the client at the door. Each request means walking to the server and back. Time a "page" with 3 requests in sequence, then with the server in the middle of the room. In round two, the server keeps in their head who paid; swap the server midway and see what gets lost.',
  'discussion': ['Why doesn’t a very fast server save a page that makes many requests in a row?', 'Where would you keep who is logged in if the school had two servers?'],
  'misconceptions': ['"If the server is fast, the app is fast." The network and the number of round trips usually weigh more.', '"Keeping the session in memory is simpler, done." It only works until the first restart or the second server.']}}
write('01-cliente-servidor', s1, loc1('pt'), loc1('en'), t1)

# ================================================================== 2 · escalar vertical × horizontal
MULT = {'s': 1, 'm': 2, 'l': 4, 'xl': 8}
SIZE_KEY = "size == 's' ? '@szS' : (size == 'm' ? '@szM' : (size == 'l' ? '@szL' : '@szXL'))"
ROWS2 = '[' + ', '.join(
  f"[text + '-{i + 1}', {SIZE_KEY}, capEach, " + ("failure ? '@down' : '@up'" if i == 0 else "'@up'") + ']' for i in range(10)) + ']'
s2 = step('sd-escalar-vertical-horizontal', 2, TRACK, 15, ['escalabilidade', 'vertical', 'horizontal', 'ponto-unico-de-falha', 'gargalo'],
  ['sd-cliente-servidor'], SIM,
  loc('escalar', 'scale'),
  {'name': 'text', 'required': False, 'default': loc('sorveteria', 'ice-cream-shop'), 'ui': 'text'},
  [flag('machines', 'maquinas', 'machines', 'int', min=1, max=10, default=4, ui='slider'),
   flag('size', 'tamanho', 'size', 'enum', options=[opt('s', 'p', 's'), opt('m', 'm', 'm'), opt('l', 'g', 'l'), opt('xl', 'gg', 'xl')], default='m', ui='select'),
   flag('peak', 'pico', 'peak', 'int', min=500, max=8000, step=100, default=2000, ui='slider'),
   flag('failure', 'falha', 'failure', 'bool', default=True, ui='switch')],
  {'options': ['giant', 'four', 'both'], 'answer': 'four'}, 'outage',
  {'live': True,
   'consts': {'mult': MULT, 'perUnit': 400, 'pricePerUnit': 100, 'dbCap': 3000},
   'compute': {
     'capEach': 'perUnit * lookup(mult, size, 1)',
     'cap': 'machines * capEach',
     'capAfter': 'failure ? (machines - 1) * capEach : cap',
     'servedBefore': 'min(peak, cap, dbCap)',
     'served': 'min(peak, capAfter, dbCap)',
     'errPct': 'round((1 - served / peak) * 100, 1)',
     'cost': 'machines * pricePerUnit * lookup(mult, size, 1)',
     'dbLimit': 'dbCap < min(peak, capAfter)',
     'rows': f'slice({ROWS2}, 0, machines)',
     'tones': "concat([failure ? 'bad' : 'neutral'], fill(machines - 1, 'neutral'))"},
   'cases': [
     {'when': 'capAfter == 0', 'flags': ['outage']},
     {'when': 'errPct > 0 && capAfter > 0', 'flags': ['degraded']},
     {'when': 'dbLimit', 'flags': ['dbBound']},
     {'when': 'true', 'vars': {'cap': 'cap', 'capAfter': 'capAfter', 'errPct': 'errPct', 'cost': 'cost', 'served': 'served'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@capM', 'value': '=cap', 'format': 'int', 'tone': "=cap >= peak ? 'ok' : 'warn'"},
       {'label': '@afterM', 'value': '=capAfter', 'format': 'int', 'tone': "=capAfter >= peak ? 'ok' : (capAfter == 0 ? 'bad' : 'warn')"},
       {'label': '@errM', 'value': '=errPct', 'format': 'pct', 'tone': "=errPct > 0 ? 'bad' : 'ok'"},
       {'label': '@costM', 'value': '=cost', 'format': 'int', 'tone': 'info'}]},
     {'type': 'chart', 'label': '@chartLabel', 'kind': 'line', 'labels': ['13h', '14h', '15h', '16h', '17h'],
      'series': [{'label': '@series', 'values': '=[servedBefore, servedBefore, served, served, served]'}],
      'threshold': {'value': '=peak', 'label': '@peakLine'}},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['@colMachine', '@colSize', '@colCap', '@colState'],
      'rows': '=rows', 'tones': '=tones', 'caption': '@tableCap'},
     {'type': 'note', 'when': '=capAfter == 0', 'tone': 'bad', 'text': '@outageNote'},
     {'type': 'note', 'when': '=dbLimit', 'tone': 'warn', 'text': '@dbNote'},
     {'type': 'note', 'when': '=errPct > 0 && capAfter > 0 && !dbLimit', 'tone': 'warn', 'text': '@shortNote'},
     {'type': 'note', 'when': '=errPct == 0', 'tone': 'ok', 'text': '@okNote'}]})

def loc2(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Escalar vertical × horizontal', 'Scaling up vs scaling out'),
  'subtitle': T('Dia de calor na sorveteria: um atendente gigante ou vários atendentes normais?', 'A hot day at the ice-cream shop: one giant server or several regular ones?'),
  'mission': T('A sorveteria da escola vende pelo app e o pico do calor (15h) chega a 2.000 pedidos por segundo. Com o mesmo dinheiro (R$ 800 por mês), dá para alugar 1 máquina gg ou 4 máquinas m. Às 15h, uma máquina queima. Compare as duas escolhas e descubra também quando comprar mais máquinas deixa de ajudar.',
               'The school’s ice-cream shop sells through the app, and the heat peak (3 pm) reaches 2,000 orders per second. With the same money (R$ 800 a month), you can rent 1 xl machine or 4 m machines. At 3 pm, one machine burns out. Compare both choices and also find out when buying more machines stops helping.'),
  'predict': {'question': T('mesmo custo: 1 máquina gg (8 vezes mais forte) ou 4 máquinas m. Às 15h uma máquina queima. Quem continua vendendo sorvete?', 'same cost: 1 xl machine (8 times stronger) or 4 m machines. At 3 pm one machine burns out. Who keeps selling ice cream?'),
    'options': {'giant': T('A gg: ela é muito mais forte', 'The xl: it’s much stronger'),
                'four': T('As 4 m: perder uma ainda deixa três', 'The 4 m: losing one still leaves three'),
                'both': T('As duas, porque custam o mesmo', 'Both, since they cost the same')}},
  'feedback': {'right': T('isso! Com 4 máquinas, perder uma derruba a capacidade de 3.200 para 2.400 pedidos/s, ainda acima do pico de 2.000. A máquina gg sozinha é um ponto único de falha: quando ela queima, a capacidade vai a zero.',
                          'right! With 4 machines, losing one drops capacity from 3,200 to 2,400 orders/s, still above the 2,000 peak. The lone xl machine is a single point of failure: when it burns out, capacity goes to zero.'),
               'wrong': T('olhe o gráfico: as 4 máquinas m caem de 3.200 para 2.400 pedidos/s às 15h e ainda cobrem o pico de 2.000. A gg sozinha tem a mesma força no total, mas quando queima não sobra ninguém.',
                          'look at the chart: the 4 m machines drop from 3,200 to 2,400 orders/s at 3 pm and still cover the 2,000 peak. The lone xl has the same total power, but when it burns out there’s nobody left.'),
               'skipped': T('sem palpite? Rode e olhe a capacidade depois da falha.', 'no guess? Run it and look at the capacity after the failure.')},
  'coach': {'ui': T('palpite anotado. Rode com 4 máquinas m e olhe a linha depois das 15h.', 'guess noted. Run with 4 m machines and look at the line after 3 pm.'),
            'cmd': T('palpite anotado. Rode escalar e olhe a capacidade depois da falha.', 'guess noted. Run scale and look at the capacity after the failure.')},
  'tryNext': {'ui': T('Agora coloque 10 máquinas gg e suba o pico para 8.000: veja quem vira o gargalo.', 'Now use 10 xl machines and raise the peak to 8,000: see what becomes the bottleneck.'),
              'cmd': T('Rode escalar --maquinas 10 --tamanho gg --pico 8000 e veja quem vira o gargalo.', 'Run scale --machines 10 --size xl --peak 8000 and see what becomes the bottleneck.')},
  'why': {'simples': T('Escalar vertical é trocar o atendente por um super-atendente: uma máquina maior, com mais processador e memória. É simples, o código nem percebe. Mas tem teto (não existe atendente infinito) e, se ele passar mal, a sorveteria fecha.\nEscalar horizontal é contratar mais atendentes iguais e dividir a fila entre eles. Se um sai, os outros continuam. Dá para crescer quase sem teto, mas precisa de alguém organizando a fila (o balanceador, próxima lição) e de atendentes que não guardam nada de cabeça (servidores sem estado, lição 1).\nE cuidado: se todos os atendentes pegam sorvete do mesmo freezer, contratar mais gente não adianta quando o freezer é o mais lento. O gargalo muda de lugar.',
                       'Scaling up (vertical) is swapping the server for a super-server: a bigger machine, with more CPU and memory. It’s simple, the code doesn’t even notice. But it has a ceiling (there’s no infinite server) and, if it gets sick, the shop closes.\nScaling out (horizontal) is hiring more identical servers and splitting the line among them. If one leaves, the others keep going. You can grow with almost no ceiling, but you need someone organizing the line (the load balancer, next lesson) and servers that keep nothing in their heads (stateless servers, lesson 1).\nAnd careful: if every server scoops from the same freezer, hiring more people doesn’t help once the freezer is the slowest part. The bottleneck moves.'),
          'dev': T('Na nuvem, escalar vertical costuma exigir reiniciar a máquina com outro tamanho (minutos fora do ar, a não ser que haja outra cobrindo), e os tamanhos têm limite. Escalar horizontal exige que a aplicação seja sem estado: sessão, arquivos enviados e filas de trabalho ficam fora do servidor.\nO autoscaling liga máquinas sozinho olhando uma métrica (CPU, pedidos por segundo, tamanho da fila), mas ele demora: precisa perceber a subida, ligar a máquina, a aplicação aquecer e passar na checagem de saúde. Pico que chega em segundos (como um link viral) passa antes da ajuda chegar, então mantenha folga ou agende o aumento antes de eventos conhecidos. E regra de bolso: tenha N+1, capacidade para aguentar a perda de uma máquina no pico.',
                   'In the cloud, scaling up usually means restarting the machine at another size (minutes offline, unless another one covers), and sizes have a limit. Scaling out requires a stateless app: sessions, uploaded files and work queues live outside the server.\nAutoscaling turns machines on by itself based on a metric (CPU, requests per second, queue length), but it takes time: it has to notice the rise, boot the machine, warm the app up and pass the health check. A peak that arrives in seconds (like a viral link) is over before help arrives, so keep headroom or schedule the increase before known events. And a rule of thumb: have N+1, enough capacity to survive losing one machine at peak.'),
          'especialista': T('Escalar horizontal não é linear para sempre. Tudo que é compartilhado (banco, cache, um lock, uma fila única) vira o novo gargalo, e coordenação entre nós custa: modelos como a Lei de Amdahl e a Universal Scalability Law mostram a curva achatando, e às vezes descendo, quando a contenção cresce. Por isso o passo seguinte é dividir o estado: réplicas de leitura, cache, particionamento (sharding) por chave.\nAutoscaling também tem armadilhas: oscilação (liga e desliga sem parar, resolvida com janelas de estabilização), limites de cota da conta, partida a frio, e o escalonamento que piora o gargalo de baixo (mais servidores = mais conexões no mesmo banco). Escale olhando a métrica que realmente satura, e teste o pico antes do dia.',
                            'Scaling out isn’t linear forever. Everything shared (database, cache, a lock, a single queue) becomes the new bottleneck, and coordination between nodes costs: models like Amdahl’s Law and the Universal Scalability Law show the curve flattening, and sometimes going down, as contention grows. That’s why the next step is splitting state: read replicas, caches, partitioning (sharding) by key.\nAutoscaling has traps too: flapping (scaling up and down nonstop, fixed with stabilization windows), account quota limits, cold starts, and scaling that worsens the bottleneck below (more servers = more connections to the same database). Scale on the metric that actually saturates, and test the peak before the day.')},
  'break': {'mission': {'ui': T('hora de quebrar: gaste o mesmo dinheiro numa máquina só, gg, e deixe ela queimar às 15h.', 'time to break it: spend the same money on a single xl machine and let it burn out at 3 pm.'),
                        'cmd': T('hora de quebrar: rode escalar --maquinas 1 --tamanho gg', 'time to break it: run scale --machines 1 --size xl')},
            'success': T('Quebrou: tudo dependia de uma máquina só. Quando ela queimou às 15h, a capacidade foi a zero e {errPct}% dos pedidos do pico ficaram sem sorvete. Gastar R$ {cost} por mês numa máquina gigante comprou força, não resistência.',
                         'Broken: everything depended on a single machine. When it burned out at 3 pm, capacity went to zero and {errPct}% of the peak orders got no ice cream. Spending R$ {cost} a month on a giant machine bought strength, not resilience.'),
            'calm': T('Capacidade de {cap} pedidos/s, {capAfter}/s depois da falha, {errPct}% dos pedidos perdidos, por R$ {cost} por mês. Para quebrar, gaste o mesmo numa máquina gg só e deixe ela queimar.',
                      'Capacity of {cap} orders/s, {capAfter}/s after the failure, {errPct}% of orders lost, for R$ {cost} a month. To break it, spend the same on a single xl machine and let it burn out.')},
  'hints': {'ui': T(['Escolha quantas máquinas, o tamanho de cada uma e o pico de pedidos.', 'Uma máquina só, por maior que seja, é um ponto único de falha.', 'Escolha 1 máquina gg, com a falha ligada.'],
                    ['Pick how many machines, the size of each and the order peak.', 'A single machine, however big, is a single point of failure.', 'Pick 1 xl machine, with the failure on.']),
            'cmd': T(['O nome é opcional; --maquinas, --tamanho, --pico e --falha também.', '--tamanho aceita p, m, g ou gg (1, 2, 4 ou 8 vezes a força da p).', 'escalar --maquinas 1 --tamanho gg'],
                     ['The name is optional; so are --machines, --size, --peak and --failure.', '--size takes s, m, l or xl (1, 2, 4 or 8 times the strength of s).', 'scale --machines 1 --size xl'])},
  'errors': {'belowMin.machines': T('Pelo menos 1 máquina, senão nem a sorveteria abre.', 'At least 1 machine, or the shop doesn’t even open.'),
             'aboveMax.machines': T('Até 10 máquinas nesta simulação.', 'Up to 10 machines in this simulation.'),
             'notInEnum.size': T('Use p, m, g ou gg.', 'Use s, m, l or xl.'),
             'belowMin.peak': T('O pico vai de 500 a 8.000 pedidos por segundo.', 'The peak goes from 500 to 8,000 orders per second.'),
             'aboveMax.peak': T('O pico vai de 500 a 8.000 pedidos por segundo.', 'The peak goes from 500 to 8,000 orders per second.'),
             'notBool.failure': T('Use sim ou nao.', 'Use yes or no.')},
  'controls': {'arg': T('Nome da loja', 'Shop name'), 'machines': T('Quantas máquinas', 'How many machines'), 'size': T('Tamanho de cada máquina', 'Size of each machine'),
               'peak': T('Pico de pedidos por segundo', 'Peak orders per second'), 'failure': T('Uma máquina queima às 15h', 'A machine burns out at 3 pm')},
  'scene': {'label': T('A sorveteria no dia mais quente', 'The ice-cream shop on the hottest day'), 'empty': T('Rode para abrir a sorveteria.', 'Run to open the shop.'),
    'capM': T('capacidade (pedidos/s)', 'capacity (orders/s)'), 'afterM': T('capacidade depois da falha', 'capacity after the failure'),
    'errM': T('pedidos perdidos no pico', 'orders lost at peak'), 'costM': T('custo por mês (R$, simulado)', 'cost per month (R$, simulated)'),
    'chartLabel': T('Pedidos atendidos por segundo (simulado)', 'Orders served per second (simulated)'),
    'series': T('atendidos/s', 'served/s'), 'peakLine': T('pico: {peak}/s', 'peak: {peak}/s'),
    'tableLabel': T('As máquinas', 'The machines'),
    'colMachine': T('máquina', 'machine'), 'colSize': T('tamanho', 'size'), 'colCap': T('pedidos/s', 'orders/s'), 'colState': T('estado', 'state'),
    'szS': T('p', 's'), 'szM': T('m', 'm'), 'szL': T('g', 'l'), 'szXL': T('gg', 'xl'),
    'up': T('no ar', 'up'), 'down': T('queimou às 15h', 'burned out at 3 pm'),
    'tableCap': T('Cada tamanho dobra a força e o preço do anterior. O banco atrás de todas aguenta 3.000 pedidos/s. Números simulados.', 'Each size doubles the strength and the price of the previous one. The database behind them all handles 3,000 orders/s. Simulated numbers.'),
    'outageNote': T('Fechou tudo: a única máquina queimou e não sobrou ninguém para atender. Isso é um ponto único de falha.', 'Everything closed: the only machine burned out and nobody was left to serve. That’s a single point of failure.'),
    'dbNote': T('Máquinas sobrando, sorvete faltando: o banco aguenta só 3.000 pedidos/s, e mais máquinas na frente dele não mudam isso. O gargalo mudou de lugar.', 'Plenty of machines, not enough ice cream: the database only handles 3,000 orders/s, and more machines in front of it don’t change that. The bottleneck moved.'),
    'shortNote': T('Depois da falha, sobraram {capAfter} pedidos/s para um pico de {peak}/s: faltou folga para perder uma máquina (N+1).', 'After the failure, {capAfter} orders/s were left for a {peak}/s peak: not enough headroom to lose a machine (N+1).'),
    'okNote': T('Nenhum pedido perdido: mesmo sem uma máquina, sobram {capAfter} pedidos/s para um pico de {peak}/s.', 'No orders lost: even without one machine, {capAfter} orders/s are left for a {peak}/s peak.')},
  'data': {},
  'recipe': {'steps': [
     T('Crie uma pasta escola-escala com dois arquivos. O compose.yaml:\n' + compose_scale(),
       'Create a folder escola-escala with two files. The compose.yaml:\n' + compose_scale()),
     T('E o nginx.conf, que manda os pedidos para o serviço app (um nome que pode valer vários contêineres):\n' + NGINX_SCALE,
       'And the nginx.conf, which sends requests to the app service (a name that can stand for several containers):\n' + NGINX_SCALE),
     T('Suba com três réplicas do app (escalar horizontal):\ndocker compose up -d --scale app=3\nRepita várias vezes curl http://localhost:8080 (no Windows PowerShell, curl.exe) e olhe a linha Hostname.',
       'Start it with three replicas of app (scaling out):\ndocker compose up -d --scale app=3\nRepeat curl http://localhost:8080 several times (in Windows PowerShell, curl.exe) and look at the Hostname line.'),
     T('Volte para uma réplica. O nginx descobre os endereços do app quando liga, então reinicie ele:\ndocker compose up -d --scale app=1\ndocker compose restart lb\nRepita o curl: agora o Hostname é sempre o mesmo.',
       'Go back to one replica. nginx looks up app’s addresses when it starts, so restart it:\ndocker compose up -d --scale app=1\ndocker compose restart lb\nRepeat the curl: now the Hostname is always the same.'),
     T('Desligue tudo: docker compose down', 'Shut everything down: docker compose down')],
   'ok': T('com 3 réplicas, o Hostname alterna entre três valores diferentes (são os ids curtos dos contêineres do app); com 1 réplica e o lb reiniciado, o Hostname não muda mais.',
           'with 3 replicas, the Hostname alternates among three different values (the short ids of the app containers); with 1 replica and lb restarted, the Hostname no longer changes.')}}

t2 = {'pt': {'objectives': ['Diferenciar escalar vertical (máquina maior) de horizontal (mais máquinas).', 'Reconhecer um ponto único de falha e a regra N+1.', 'Perceber que o gargalo muda de lugar quando uma parte cresce.'], 'minutes': 15,
  'activity': 'Sorveteria na sala: a turma tem 40 "pedidos" (papeizinhos) para atender em 1 minuto. Rodada 1: um aluno muito rápido atende sozinho, e no meio da rodada ele "queima" (senta). Rodada 2: quatro alunos normais dividem a fila e um deles senta no meio. Rodada 3: oito alunos, mas todos precisam pegar o sorvete na mesma caixa, uma pessoa por vez.',
  'discussion': ['Que coisas da escola são um ponto único de falha (só uma chave, só uma pessoa sabe a senha)?', 'Por que contratar mais atendentes não adiantou na rodada 3?'],
  'misconceptions': ['"Máquina maior resolve tudo." Ela tem teto e continua sendo uma só.', '"Dobrar as máquinas dobra a capacidade." Só até a parte compartilhada (banco, freezer) virar o gargalo.']},
 'en': {'objectives': ['Tell scaling up (a bigger machine) from scaling out (more machines).', 'Recognize a single point of failure and the N+1 rule.', 'Notice that the bottleneck moves when one part grows.'], 'minutes': 15,
  'activity': 'Ice-cream shop in the classroom: the class has 40 "orders" (slips of paper) to serve in 1 minute. Round 1: one very fast student serves alone, and halfway through they "burn out" (sit down). Round 2: four regular students split the line and one sits down midway. Round 3: eight students, but all must take the ice cream from the same box, one person at a time.',
  'discussion': ['Which things at school are a single point of failure (only one key, only one person knows the password)?', 'Why didn’t hiring more servers help in round 3?'],
  'misconceptions': ['"A bigger machine solves everything." It has a ceiling and is still just one.', '"Doubling the machines doubles capacity." Only until the shared part (database, freezer) becomes the bottleneck.']}}
write('02-escalar-vertical-horizontal', s2, loc2('pt'), loc2('en'), t2)

# ================================================================== 3 · balanceador
LB_RPS, LB_DUR, LB_WIN = 300, 600, 10
LB_CAP, LB_S, LB_SLOW_CAP, LB_SLOW_S = 200, 20, 70, 60
def lb_outcome(algo, prob, check):
  failing = prob in ('dead', 'err500')
  detects = (prob == 'dead' and check != 'none') or (prob == 'err500' and check == 'http')
  if algo == 'hash': shares = [1, 0, 0]
  elif failing and detects: shares = [0.5, 0, 0.5]
  elif algo == 'lc' and failing: shares = [0.25, 0.5, 0.25]
  elif algo == 'lc' and prob == 'slow': shares = [LB_CAP / 470, LB_SLOW_CAP / 470, LB_CAP / 470]
  else: shares = [1 / 3] * 3
  win_share = (1 / 3 if algo == 'rr' else 0.5) if (detects and algo != 'hash') else 0
  failed = LB_WIN * LB_RPS * win_share
  steady = LB_DUR - (LB_WIN if win_share else 0)
  if failing and not detects and shares[1] > 0: failed += shares[1] * LB_RPS * LB_DUR
  p95s, states, over = [], [], False
  for i in range(3):
    slow = i == 1 and prob == 'slow'
    cap, s = (LB_SLOW_CAP, LB_SLOW_S) if slow else (LB_CAP, LB_S)
    load = shares[i] * LB_RPS
    bad = i == 1 and failing
    if bad:
      p95s.append(None); states.append('@stOut' if detects else ('@stDead' if prob == 'dead' else '@st500')); continue
    if load > cap:
      failed += (load - cap) * steady; over = True
    rho = load / cap
    p = 5000 if rho >= 0.98 else round(3 * s / (1 - rho))
    p95s.append(p if load > 0 else None)
    states.append('@stOver' if load > cap else ('@stIdle' if load == 0 else ('@stSlow' if slow else '@stOk')))
  p95 = max([p for p, sh in zip(p95s, shares) if p is not None and sh >= 0.05] or [0])
  err = round(failed / (LB_RPS * LB_DUR) * 100, 2)
  rows = [[f'app-{i + 1}', f'{round(shares[i] * 100)}%', states[i], '@dash' if p95s[i] is None else f'{p95s[i]} ms'] for i in range(3)]
  tones = ['bad' if st in ('@stDead', '@st500', '@stOver') else ('dim' if st in ('@stOut', '@stIdle') else ('warn' if st == '@stSlow' else 'ok')) for st in states]
  term = ['@tNoCheck' if check == 'none' else ('@tTcp' if check == 'tcp' else '@tHttp')]
  if check == 'none': term.append('@tNoCheckFail' if failing else ('@tNoCheckSlow' if prob == 'slow' else '@tAllOk'))
  elif prob == 'dead': term.append('@tDeadOut')
  elif prob == 'err500': term.append('@t500Http' if check == 'http' else '@t500Tcp')
  elif prob == 'slow': term.append('@tSlowPass')
  else: term.append('@tAllOk')
  if algo == 'hash': term.append('@tHash')
  return {'errPct': err, 'failed': round(failed), 'p95': p95, 'detects': detects, 'share2': round(shares[1] * 100),
          'shares': [round(x * 100) for x in shares], 'rows': rows, 'tones': tones, 'term': term,
          'blackhole': failing and not detects and shares[1] > 0, 'hotspot': algo == 'hash', 'over': over}
LB = {f'{a}-{p}-{c}': lb_outcome(a, p, c) for a in ('rr', 'lc', 'hash') for p in ('none', 'dead', 'err500', 'slow') for c in ('none', 'tcp', 'http')}

s3 = step('sd-balanceador', 3, TRACK, 20, ['balanceador', 'load-balancer', 'health-check', 'l4', 'l7', 'round-robin'],
  ['sd-escalar-vertical-horizontal'], SIM,
  loc('balancear', 'balance'),
  {'name': 'text', 'required': False, 'default': loc('cantina-online', 'canteen-online'), 'ui': 'text'},
  [flag('algo', 'algoritmo', 'algorithm', 'enum',
        options=[opt('rr', 'round-robin', 'round-robin'), opt('lc', 'menos-conexoes', 'least-conn'), opt('hash', 'ip-hash', 'ip-hash')], default='rr', ui='select'),
   flag('problem', 'problema', 'problem', 'enum',
        options=[opt('none', 'nenhum', 'none'), opt('dead', 'morto', 'dead'), opt('err500', 'erro500', 'error500'), opt('slow', 'lento', 'slow')], default='dead', ui='select'),
   flag('check', 'checagem', 'check', 'enum',
        options=[opt('none', 'nenhuma', 'none'), opt('tcp', 'tcp', 'tcp'), opt('http', 'http', 'http')], default='http', ui='select')],
  {'options': ['zero', 'few', 'third'], 'answer': 'few'}, 'blackhole',
  {'live': True,
   'consts': {'lb': LB},
   'compute': {
     'r': "lookup(lb, algo + '-' + problem + '-' + check, 0)",
     'errPct': 'r.errPct', 'failed': 'r.failed', 'p95': 'r.p95', 'detects': 'r.detects', 'share2': 'r.share2',
     'isHot': 'r.hotspot', 'isHole': 'r.blackhole', 'isOver': 'r.over'},
   'cases': [
     {'when': 'isHole', 'flags': ['blackhole']},
     {'when': 'isHot', 'flags': ['hotspot']},
     {'when': 'isOver', 'flags': ['overload']},
     {'when': 'detects', 'flags': ['detected']},
     {'when': 'true', 'vars': {'errPct': 'errPct', 'failed': 'failed', 'p95': 'p95', 'share2': 'share2',
                               'probTxt': "lookup(probTexts, problem, '')", 'checkTxt': "lookup(checkTexts, check, '')"}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@errM', 'value': '=errPct', 'format': 'pct', 'tone': "=errPct >= 5 ? 'bad' : (errPct > 0 ? 'warn' : 'ok')"},
       {'label': '@failedM', 'value': '=failed', 'format': 'int', 'tone': "=failed > 5000 ? 'bad' : (failed > 0 ? 'warn' : 'ok')"},
       {'label': '@p95M', 'value': '=p95', 'format': 'ms', 'tone': "=p95 > 1000 ? 'bad' : (p95 > 300 ? 'warn' : 'ok')"},
       {'label': '@outM', 'value': "=detects ? 10 : (problem == 'dead' || problem == 'err500' ? '@never' : '@dash')", 'tone': "=detects ? 'ok' : (problem == 'dead' || problem == 'err500' ? 'bad' : 'dim')"}]},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['@colServer', '@colShare', '@colState', 'p95'], 'rows': '=r.rows', 'tones': '=r.tones', 'caption': '@tableCap'},
     {'type': 'chart', 'label': '@chartLabel', 'kind': 'bar', 'labels': ['app-1', 'app-2', 'app-3'],
      'series': [{'label': '@series', 'values': '=r.shares'}], 'max': 100},
     {'type': 'terminal', 'label': '@termLabel', 'lines': '=r.term'},
     {'type': 'note', 'when': '=isHole', 'tone': 'bad', 'text': '@holeNote'},
     {'type': 'note', 'when': '=isHole && algo == \'lc\'', 'tone': 'warn', 'text': '@lcHoleNote'},
     {'type': 'note', 'when': '=isHot', 'tone': 'warn', 'text': '@hashNote'},
     {'type': 'note', 'when': "=problem == 'slow' && algo == 'rr'", 'tone': 'warn', 'text': '@slowRrNote'},
     {'type': 'note', 'when': '=detects && !isHot', 'tone': 'ok', 'text': '@detectNote'},
     {'type': 'note', 'when': "=problem == 'none' && !isHot", 'tone': 'ok', 'text': '@calmNote'}]})

def loc3(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Balanceador de carga', 'Load balancer'),
  'subtitle': T('O fiscal da fila da cantina: divide os alunos entre os caixas e tira da roda o caixa que parou', 'The canteen line monitor: splits students among the registers and pulls the register that stopped'),
  'mission': T('No recreio, o app da cantina recebe 300 pedidos por segundo durante 10 minutos, divididos por um balanceador entre três servidores (app-1, app-2 e app-3). Hoje o app-2 morreu logo no começo. O balanceador faz uma checagem de saúde a cada 5 segundos e tira da roda quem falha 2 vezes seguidas. Descubra quantos pedidos dão erro, e depois teste outros problemas, outras checagens e outros algoritmos.',
               'At recess, the canteen app gets 300 requests per second for 10 minutes, split by a load balancer among three servers (app-1, app-2 and app-3). Today app-2 died right at the start. The balancer runs a health check every 5 seconds and pulls whoever fails twice in a row. Find out how many requests fail, then try other problems, other checks and other algorithms.'),
  'predict': {'question': T('o app-2 morreu e a checagem de saúde HTTP está ligada. Quantos pedidos do recreio dão erro?', 'app-2 died and the HTTP health check is on. How many recess requests fail?'),
    'options': {'zero': T('Nenhum: o balanceador já sabe na hora', 'None: the balancer knows right away'),
                'few': T('Quase nenhum: só os que chegam até ele perceber', 'Almost none: only those that arrive before it notices'),
                'third': T('Um terço: cada servidor recebe um terço', 'A third: each server gets a third')}},
  'feedback': {'right': T('isso! Durante os 10 segundos que a checagem leva para ter certeza (2 falhas, uma a cada 5 s), o app-2 ainda recebe um terço dos pedidos: 10 s × 100 pedidos/s = 1.000 erros, ou 0,56% do recreio. Depois disso, ele sai da roda e os outros dois dividem tudo.',
                          'right! During the 10 seconds the check needs to be sure (2 failures, one every 5 s), app-2 still gets a third of the requests: 10 s × 100 requests/s = 1,000 errors, or 0.56% of recess. After that, it leaves the rotation and the other two split everything.'),
               'wrong': T('olhe a tabela e a métrica de erros: a checagem não é instantânea. Por 10 segundos (2 falhas seguidas, a cada 5 s), o app-2 ainda recebe um terço: 1.000 erros, 0,56% do recreio. Depois ele sai da roda e não erra mais ninguém.',
                          'look at the table and the error metric: the check isn’t instant. For 10 seconds (2 failures in a row, every 5 s), app-2 still gets a third: 1,000 errors, 0.56% of recess. Then it leaves the rotation and nobody else fails.'),
               'skipped': T('sem palpite? Rode e olhe quantos pedidos falharam e por quanto tempo o app-2 ficou na roda.', 'no guess? Run it and look at how many requests failed and how long app-2 stayed in the rotation.')},
  'coach': {'ui': T('palpite anotado. Rode e olhe os pedidos com erro e o tempo até tirar o app-2 da roda.', 'guess noted. Run it and look at the failed requests and the time to pull app-2.'),
            'cmd': T('palpite anotado. Rode balancear e olhe a tabela dos servidores.', 'guess noted. Run balance and look at the servers table.')},
  'tryNext': {'ui': T('Agora escolha o problema erro500 com a checagem tcp. Depois troque o algoritmo para ip-hash.', 'Now pick the error500 problem with the tcp check. Then switch the algorithm to ip-hash.'),
              'cmd': T('Rode balancear --problema erro500 --checagem tcp e depois balancear --algoritmo ip-hash.', 'Run balance --problem error500 --check tcp and then balance --algorithm ip-hash.')},
  'why': {'simples': T('O balanceador é o fiscal da fila da cantina: ele fica na porta e manda cada aluno para um caixa. No round-robin, é um para cada, em rodízio. No menos-conexões, vai para o caixa com menos gente.\nMas o fiscal só é bom se olha os caixas. A checagem de saúde é ele perguntando a cada 5 segundos: "tudo certo aí?". Se o caixa não responde duas vezes, ele para de mandar gente para lá. Sem checagem, o fiscal continua mandando um terço dos alunos para um caixa fechado.\nE existe checagem rasa e checagem de verdade: ver se a luz do caixa está acesa (TCP) é diferente de pedir um lanche de teste (HTTP). Um caixa com a luz acesa e a máquina de cartão quebrada passa na primeira e falha na segunda.',
                       'The load balancer is the canteen line monitor: it stands at the door and sends each student to a register. With round-robin, it’s one each, in turn. With least-connections, it goes to the register with the fewest people.\nBut the monitor is only good if it watches the registers. The health check is the monitor asking every 5 seconds: "all good there?". If a register doesn’t answer twice, it stops sending people there. Without a check, the monitor keeps sending a third of the students to a closed register.\nAnd there are shallow checks and real checks: seeing whether the register’s light is on (TCP) is different from ordering a test snack (HTTP). A register with its light on and a broken card machine passes the first and fails the second.'),
          'dev': T('Um balanceador de camada 4 (L4) olha conexões TCP/UDP: endereço e porta. Ele é rápido e não abre o conteúdo. Um de camada 7 (L7) entende HTTP: pode rotear por caminho ou cabeçalho, terminar TLS, repetir um pedido em outro servidor e checar a saúde com um GET /health que espera 200.\nChecagem ativa é o balanceador perguntando de tempos em tempos (intervalo, tempo-limite, quantas falhas para tirar e quantos acertos para devolver). Checagem passiva é ele notar falhas nos pedidos de verdade: no nginx open source, max_fails e fail_timeout fazem isso (o padrão é 1 falha em 10 s tira o servidor por 10 s); a checagem ativa do nginx é do NGINX Plus, e HAProxy e Envoy têm as duas.\nUm /health bom testa o que o servidor precisa para atender (o banco responde?), mas sem ser pesado nem derrubar todos os servidores juntos quando uma dependência opcional cai.',
                   'A layer 4 (L4) balancer looks at TCP/UDP connections: address and port. It’s fast and doesn’t open the content. A layer 7 (L7) one understands HTTP: it can route by path or header, terminate TLS, retry a request on another server and check health with a GET /health that expects 200.\nActive checks are the balancer asking from time to time (interval, timeout, how many failures to pull and how many successes to bring back). Passive checks are it noticing failures in real requests: in open-source nginx, max_fails and fail_timeout do this (the default is 1 failure in 10 s pulls the server for 10 s); nginx’s active check is an NGINX Plus feature, and HAProxy and Envoy have both.\nA good /health tests what the server needs to serve (does the database answer?), without being heavy or taking every server down together when an optional dependency fails.'),
          'especialista': T('Algoritmos têm efeitos colaterais. Menos-conexões favorece o servidor que responde mais rápido, o que é ótimo até ele responder rápido porque está devolvendo erro: o servidor quebrado atrai mais tráfego (o efeito buraco negro). ip-hash prende cada cliente a um servidor, mas atrás de NAT (uma escola, uma empresa, uma operadora móvel) milhares de pessoas saem pelo mesmo IP e tudo cai num servidor só. Afinidade por cookie e hash consistente (que move poucas chaves quando um servidor entra ou sai) são alternativas.\nRepetir pedidos em outro servidor esconde falhas, mas só é seguro em operações idempotentes (GET, ou POST com chave de idempotência), e repetição sem limite multiplica a carga justamente no pior momento: use orçamento de repetições. Por fim, o balanceador também é uma peça que falha: em produção ele é redundante (par ativo-passivo, IP virtual, anycast ou o serviço gerenciado da nuvem).',
                            'Algorithms have side effects. Least-connections favors the server that answers fastest, which is great until it answers fast because it’s returning errors: the broken server attracts more traffic (the black hole effect). ip-hash pins each client to a server, but behind NAT (a school, a company, a mobile carrier) thousands of people share one IP and everything lands on a single server. Cookie affinity and consistent hashing (which moves few keys when a server joins or leaves) are alternatives.\nRetrying on another server hides failures, but it’s only safe for idempotent operations (GET, or POST with an idempotency key), and unlimited retries multiply load at exactly the worst moment: use a retry budget. Finally, the balancer is also a part that fails: in production it’s redundant (active-passive pair, virtual IP, anycast or the cloud’s managed service).')},
  'break': {'mission': {'ui': T('hora de quebrar: desligue a checagem de saúde com o app-2 morto.', 'time to break it: turn off the health check with app-2 dead.'),
                        'cmd': T('hora de quebrar: rode balancear --checagem nenhuma', 'time to break it: run balance --check none')},
            'success': T('Quebrou: o app-2 {probTxt}, e {checkTxt}. O balanceador continuou mandando {share2}% dos pedidos para ele: {errPct}% de erro no recreio, {failed} pedidos perdidos. Fiscal que não olha os caixas manda aluno para caixa fechado.',
                         'Broken: app-2 {probTxt}, and {checkTxt}. The balancer kept sending {share2}% of the requests to it: {errPct}% errors at recess, {failed} requests lost. A monitor who doesn’t watch the registers sends students to a closed one.'),
            'calm': T('{errPct}% de erro ({failed} pedidos em 10 minutos de recreio) e p95 de {p95} ms. Para quebrar, desligue a checagem de saúde com o app-2 morto.',
                      '{errPct}% errors ({failed} requests in 10 minutes of recess) and a p95 of {p95} ms. To break it, turn off the health check with app-2 dead.')},
  'hints': {'ui': T(['Escolha o algoritmo, o problema do app-2 e o tipo de checagem de saúde.', 'Sem ninguém olhando, o balanceador não sabe que um servidor parou.', 'Escolha a checagem "nenhuma", com o problema "morto".'],
                    ['Pick the algorithm, app-2’s problem and the kind of health check.', 'With nobody watching, the balancer doesn’t know a server stopped.', 'Pick the "none" check, with the "dead" problem.']),
            'cmd': T(['O nome é opcional; --algoritmo, --problema e --checagem também.', '--checagem aceita nenhuma, tcp ou http.', 'balancear --checagem nenhuma'],
                     ['The name is optional; so are --algorithm, --problem and --check.', '--check takes none, tcp or http.', 'balance --check none'])},
  'errors': {'notInEnum.algo': T('Use round-robin, menos-conexoes ou ip-hash.', 'Use round-robin, least-conn or ip-hash.'),
             'notInEnum.problem': T('Use nenhum, morto, erro500 ou lento.', 'Use none, dead, error500 or slow.'),
             'notInEnum.check': T('Use nenhuma, tcp ou http.', 'Use none, tcp or http.')},
  'controls': {'arg': T('Nome do serviço', 'Service name'), 'algo': T('Algoritmo', 'Algorithm'), 'problem': T('O que aconteceu com o app-2', 'What happened to app-2'),
               'check': T('Checagem de saúde', 'Health check')},
  'scene': {'label': T('O recreio no balanceador', 'Recess at the load balancer'), 'empty': T('Rode para abrir a cantina.', 'Run to open the canteen.'),
    'errM': T('pedidos com erro', 'failed requests'), 'failedM': T('pedidos perdidos em 10 min', 'requests lost in 10 min'),
    'p95M': T('p95 dos que deram certo', 'p95 of the successful ones'), 'outM': T('segundos até tirar o app-2', 'seconds to pull app-2'),
    'never': T('nunca', 'never'),
    'tableLabel': T('Os servidores atrás do balanceador', 'The servers behind the balancer'),
    'colServer': T('servidor', 'server'), 'colShare': T('recebe', 'gets'), 'colState': T('estado', 'state'),
    'stOk': T('ok', 'ok'), 'stDead': T('morto', 'dead'), 'st500': T('responde 500', 'answers 500'), 'stOut': T('fora da roda', 'pulled'),
    'stSlow': T('lento', 'slow'), 'stOver': T('sobrecarregado', 'overloaded'), 'stIdle': T('parado', 'idle'), 'dash': '—',
    'tableCap': T('300 pedidos/s por 10 minutos. Cada servidor aguenta 200/s; o lento, 70/s. Números simulados.', '300 requests/s for 10 minutes. Each server handles 200/s; the slow one, 70/s. Simulated numbers.'),
    'chartLabel': T('Parte do tráfego que cada servidor recebe (%)', 'Share of traffic each server gets (%)'), 'series': T('% dos pedidos', '% of requests'),
    'termLabel': T('Registro do balanceador (simulado)', 'Balancer log (simulated)'),
    'tNoCheck': T('~ checagem de saúde: desligada', '~ health check: off'),
    'tTcp': T('~ checagem TCP na porta 80 a cada 5 s; 2 falhas = fora', '~ TCP check on port 80 every 5 s; 2 failures = pulled'),
    'tHttp': T('~ checagem GET /health a cada 5 s, espera 200; 2 falhas = fora', '~ GET /health check every 5 s, expects 200; 2 failures = pulled'),
    'tNoCheckFail': T('! app-2 continua na roda: ninguém está olhando', '! app-2 stays in the rotation: nobody is watching'),
    'tNoCheckSlow': T('? app-2 lento, mas ninguém está medindo', '? app-2 is slow, but nobody is measuring'),
    'tAllOk': T('+ app-1, app-2 e app-3 saudáveis', '+ app-1, app-2 and app-3 healthy'),
    'tDeadOut': T('! app-2: conexão recusada 2 vezes: fora da roda em 10 s', '! app-2: connection refused twice: pulled in 10 s'),
    't500Tcp': T('? app-2: a porta 80 abre, então a checagem TCP passa (mas todo pedido recebe 500)', '? app-2: port 80 opens, so the TCP check passes (but every request gets a 500)'),
    't500Http': T('! app-2: GET /health → 500 duas vezes: fora da roda em 10 s', '! app-2: GET /health → 500 twice: pulled in 10 s'),
    'tSlowPass': T('? app-2 responde a checagem em 60 ms: está "saudável", só que lento', '? app-2 answers the check in 60 ms: it’s "healthy", just slow'),
    'tHash': T('? ip-hash: todo mundo sai pelo IP da escola, então tudo vai para o app-1', '? ip-hash: everyone leaves through the school’s IP, so everything goes to app-1'),
    'holeNote': T('O app-2 {probTxt} e continua recebendo {share2}% dos pedidos: {errPct}% de erro. É um buraco negro: o pedido entra e não volta.', 'app-2 {probTxt} and still gets {share2}% of the requests: {errPct}% errors. It’s a black hole: requests go in and don’t come back.'),
    'lcHoleNote': T('Pior com menos-conexões: o servidor quebrado responde (com erro) mais rápido que os outros, fica sempre com menos conexões abertas e atrai metade do tráfego.', 'Worse with least-connections: the broken server answers (with an error) faster than the others, always has fewer open connections and attracts half the traffic.'),
    'hashNote': T('ip-hash numa escola: os alunos saem todos pelo mesmo IP público (NAT), então o hash manda 100% para o app-1. Ele recebe 300/s e aguenta 200/s.', 'ip-hash at a school: all students leave through the same public IP (NAT), so the hash sends 100% to app-1. It gets 300/s and handles 200/s.'),
    'slowRrNote': T('Round-robin não olha a velocidade: o app-2 lento recebe a mesma parte que os outros e afoga. Menos-conexões manda menos para ele.', 'Round-robin ignores speed: the slow app-2 gets the same share as the others and drowns. Least-connections sends it less.'),
    'detectNote': T('A checagem tirou o app-2 da roda em 10 s. Só os pedidos desse intervalo deram erro; depois, app-1 e app-3 dividem tudo.', 'The check pulled app-2 in 10 s. Only the requests in that window failed; afterwards, app-1 and app-3 split everything.'),
    'calmNote': T('Dia tranquilo: três servidores saudáveis, cada um com uma parte do recreio.', 'A quiet day: three healthy servers, each with a share of recess.')},
  'data': {'probTexts': {'none': T('estava saudável', 'was healthy'), 'dead': T('morreu', 'died'), 'err500': T('respondia 500 em todo pedido', 'answered 500 to every request'), 'slow': T('estava lento', 'was slow')},
           'checkTexts': {'none': T('não havia checagem de saúde', 'there was no health check'), 'tcp': T('a checagem TCP só via a porta aberta', 'the TCP check only saw the open port'), 'http': T('a checagem HTTP não percebeu', 'the HTTP check didn’t notice')}},
  'recipe': {'steps': [
     T('Crie uma pasta escola-lb com dois arquivos. O compose.yaml (dois servidores e um nginx na frente):\n' + compose_lb(),
       'Create a folder escola-lb with two files. The compose.yaml (two servers and an nginx in front):\n' + compose_lb()),
     T('E o nginx.conf. max_fails e fail_timeout são a checagem passiva do nginx; proxy_connect_timeout evita esperar demais por um servidor que sumiu:\n' + NGINX_LB,
       'And the nginx.conf. max_fails and fail_timeout are nginx’s passive check; proxy_connect_timeout avoids waiting too long for a server that vanished:\n' + NGINX_LB),
     T('Suba e repita algumas vezes o curl, olhando a linha Hostname (no Windows PowerShell, curl.exe):\ndocker compose up -d\ncurl http://localhost:8080',
       'Start it and repeat the curl a few times, looking at the Hostname line (in Windows PowerShell, curl.exe):\ndocker compose up -d\ncurl http://localhost:8080'),
     T('Faça um recreio de mentira com o ab, que vem na imagem oficial do Apache, rodando dentro da rede do compose (-l aceita respostas de tamanhos diferentes):\ndocker run --rm --network escola_default httpd:2.4 ab -l -n 2000 -c 20 http://lb/\nOlhe as linhas Failed requests e 95%.',
       'Run a fake recess with ab, which ships in the official Apache image, inside the compose network (-l accepts responses of different lengths):\ndocker run --rm --network escola_default httpd:2.4 ab -l -n 2000 -c 20 http://lb/\nLook at the Failed requests and 95% lines.'),
     T('Mate um servidor e continue pedindo:\ndocker compose stop app1\ncurl http://localhost:8080\nO primeiro pedido pode demorar até 2 s (o nginx tenta o app1, desiste e vai para o app2); os seguintes vão direto para o app2. Se o app1 voltar com outro IP, o nginx só o reencontra depois de docker compose restart lb.',
       'Kill a server and keep asking:\ndocker compose stop app1\ncurl http://localhost:8080\nThe first request may take up to 2 s (nginx tries app1, gives up and goes to app2); the next ones go straight to app2. If app1 comes back with another IP, nginx only finds it again after docker compose restart lb.'),
     T('Desligue tudo: docker compose down', 'Shut everything down: docker compose down')],
   'ok': T('com os dois no ar, o Hostname alterna entre dois valores; o ab termina com Failed requests: 0 e mostra o tempo da linha 95%; com o app1 parado, todas as respostas vêm do mesmo Hostname e nenhuma dá erro.',
           'with both up, the Hostname alternates between two values; ab ends with Failed requests: 0 and shows the 95% line’s time; with app1 stopped, every response comes from the same Hostname and none fails.')}}

t3 = {'pt': {'objectives': ['Explicar o que um balanceador faz e por que ele precisa de checagem de saúde.', 'Diferenciar checagem TCP (L4) de checagem HTTP (L7).', 'Reconhecer efeitos colaterais de round-robin, menos-conexões e ip-hash.'], 'minutes': 20,
  'activity': 'Fiscal da cantina: um aluno é o balanceador na porta e três são caixas. O fiscal manda os "pedidos" em rodízio. No meio, um caixa fecha sem avisar (vira de costas). Rodada 1: o fiscal não olha. Rodada 2: a cada 5 segundos ele pergunta "tudo certo?". Rodada 3: o caixa continua de frente, mas responde "não tenho troco" para todos; o fiscal só checa se ele está de frente.',
  'discussion': ['Que pergunta o fiscal deveria fazer para descobrir o caixa sem troco?', 'Por que mandar todos da mesma "casa" para o mesmo caixa dá problema numa escola?'],
  'misconceptions': ['"O balanceador sabe na hora que um servidor caiu." Ele só sabe pelo que checa, e checar leva tempo.', '"Porta aberta é servidor saudável." Um servidor pode aceitar a conexão e responder erro em tudo.']},
 'en': {'objectives': ['Explain what a load balancer does and why it needs a health check.', 'Tell a TCP (L4) check from an HTTP (L7) check.', 'Recognize side effects of round-robin, least-connections and ip-hash.'], 'minutes': 20,
  'activity': 'Canteen monitor: one student is the balancer at the door and three are registers. The monitor sends "orders" in turn. Midway, a register closes without warning (turns their back). Round 1: the monitor doesn’t look. Round 2: every 5 seconds they ask "all good?". Round 3: the register keeps facing forward but says "no change" to everybody; the monitor only checks whether they’re facing forward.',
  'discussion': ['What question should the monitor ask to find the register with no change?', 'Why does sending everyone from the same "house" to the same register cause trouble at a school?'],
  'misconceptions': ['"The balancer knows instantly that a server went down." It only knows what it checks, and checking takes time.', '"An open port means a healthy server." A server can accept the connection and answer errors to everything.']}}
write('03-balanceador', s3, loc3('pt'), loc3('en'), t3)

# ================================================================== 4 · cache
BIN_VALUES = '[' + ', '.join(f'ttl == 0 ? 400 : ((floor({t + 5} / T) - floor({t} / T)) > 0 ? burstTotal : 0)' for t in range(0, 60, 5)) + ']'
s4 = step('sd-cache', 4, TRACK, 20, ['cache', 'ttl', 'cache-aside', 'invalidacao', 'stampede', 'redis'],
  ['sd-escalar-vertical-horizontal'], SIM,
  loc('cachear', 'cache'),
  {'name': 'text', 'required': False, 'default': loc('cardapio-do-dia', 'todays-menu'), 'ui': 'text'},
  [flag('ttl', 'ttl', 'ttl', 'int', min=0, max=3600, uiMax=600, step=5, default=30, ui='slider'),
   flag('invalidate', 'invalidar', 'invalidate', 'bool', default=True, ui='switch'),
   flag('lock', 'trava', 'lock', 'bool', default=True, ui='switch')],
  {'options': ['half', 'ten', 'lessThanOne'], 'answer': 'lessThanOne'}, 'stale',
  {'live': True,
   'consts': {'reads': 2000, 'keys': 20, 'queryMs': 200, 'appMs': 10, 'cacheMs': 1, 'pool': 100, 'dbCap': 500},
   'compute': {
     'T': 'max(ttl, 1)',
     'perKey': 'reads / keys',
     'perExpiry': 'lock ? 1 : perKey * queryMs / 1000',
     'burstTotal': 'keys * perExpiry',
     'dbQps': 'ttl == 0 ? reads : round(keys * perExpiry / ttl, 2)',
     'missPct': 'round(dbQps / reads * 100, 2)',
     'worstMs': 'ttl == 0 ? 5000 : (lock ? appMs + cacheMs + queryMs : appMs + queryMs * ceil(burstTotal / pool))',
     'staleS': 'invalidate ? 0 : ttl',
     'staleMin': 'round(staleS / 60, 1)',
     'errPct': 'ttl == 0 ? round((1 - dbCap / reads) * 100, 1) : 0',
     'bins': BIN_VALUES},
   'cases': [
     {'when': '!invalidate && ttl > 300', 'flags': ['stale']},
     {'when': '!invalidate && ttl > 0 && ttl <= 300', 'flags': ['staleShort']},
     {'when': '!lock && ttl > 0', 'flags': ['stampede']},
     {'when': 'ttl == 0', 'flags': ['dbMelt']},
     {'when': 'true', 'vars': {'missPct': 'missPct', 'dbQps': 'dbQps', 'worstMs': 'worstMs', 'staleS': 'staleS', 'staleMin': 'staleMin', 'errPct': 'errPct'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@missM', 'value': '=missPct', 'format': 'pct', 'tone': "=missPct >= 5 ? 'bad' : 'ok'"},
       {'label': '@dbM', 'value': '=dbQps', 'format': 'num', 'tone': "=dbQps > dbCap ? 'bad' : 'ok'"},
       {'label': '@worstM', 'value': '=worstMs', 'format': 'ms', 'tone': "=worstMs > 500 ? 'bad' : 'ok'"},
       {'label': '@staleM', 'value': '=staleS', 'format': 'int', 'tone': "=staleS > 300 ? 'bad' : (staleS > 0 ? 'warn' : 'ok')"}]},
     {'type': 'flow', 'label': '@flowLabel', 'steps': [
       {'label': '@student', 'tone': 'info'},
       {'label': 'App', 'sub': '10 ms', 'tone': 'ok'},
       {'label': 'Cache', 'sub': "=ttl > 0 ? '@ttlSub' : '@off'", 'tone': "=ttl > 0 ? 'ok' : 'dim'"},
       {'label': '@db', 'sub': '@dbSub', 'tone': "=dbQps > dbCap ? 'bad' : 'ok'"}]},
     {'type': 'chart', 'label': '@chartLabel', 'kind': 'bar',
      'labels': ['0s', '5s', '10s', '15s', '20s', '25s', '30s', '35s', '40s', '45s', '50s', '55s'],
      'series': [{'label': '@series', 'values': '=bins'}], 'threshold': {'value': '=pool', 'label': '@poolLine'}},
     {'type': 'terminal', 'label': '@termLabel',
      'lines': "=ttl > 0 ? ['$ redis-cli SET ' + text + ' \"pastel 6,00\" EX ' + ttl, 'OK', '$ redis-cli TTL ' + text, '(integer) ' + ttl, invalidate ? '@tInval' : '@tNoInval'] : ['@tNoCache']"},
     {'type': 'note', 'when': '=!invalidate && ttl > 300', 'tone': 'bad', 'text': '@staleNote'},
     {'type': 'note', 'when': '=!invalidate && ttl > 0 && ttl <= 300', 'tone': 'warn', 'text': '@staleShortNote'},
     {'type': 'note', 'when': '=!lock && ttl > 0', 'tone': 'warn', 'text': '@stampedeNote'},
     {'type': 'note', 'when': '=ttl == 0', 'tone': 'bad', 'text': '@meltNote'},
     {'type': 'note', 'when': '=ttl > 0 && invalidate && lock', 'tone': 'ok', 'text': '@okNote'}]})

def loc4(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Cache', 'Cache'),
  'subtitle': T('O cardápio pregado na parede: ninguém precisa perguntar para a cozinha, até o preço mudar', 'The menu pinned on the wall: nobody has to ask the kitchen, until the price changes'),
  'mission': T('Na hora do almoço, o app da cantina recebe 2.000 leituras por segundo, espalhadas por 20 páginas (cardápio do dia, preços, alergênicos…). Montar cada página no banco leva 200 ms, e o banco aguenta 500 consultas por segundo (um pool de 100 conexões). Às 10h o preço do pastel muda. Ajuste o cache: por quanto tempo guardar (TTL), se apaga a cópia quando o preço muda, e se só um pedido vai buscar no banco quando a cópia vence.',
               'At lunchtime, the canteen app gets 2,000 reads per second, spread over 20 pages (today’s menu, prices, allergens…). Building each page in the database takes 200 ms, and the database handles 500 queries per second (a pool of 100 connections). At 10 am the price of the pastel changes. Tune the cache: how long to keep it (TTL), whether to delete the copy when the price changes, and whether only one request goes to the database when the copy expires.'),
  'predict': {'question': T('com um cache de 30 segundos, de cada 100 pedidos de cardápio, quantos ainda vão até o banco?', 'with a 30-second cache, out of every 100 menu requests, how many still go to the database?'),
    'options': {'half': T('Uns 50: o cache ajuda pela metade', 'About 50: the cache helps by half'),
                'ten': T('Uns 10', 'About 10'),
                'lessThanOne': T('Menos de 1', 'Less than 1')}},
  'feedback': {'right': T('isso! Cada página é pedida 100 vezes por segundo, mas só vai ao banco uma vez a cada 30 segundos: 20 páginas ÷ 30 s ≈ 0,67 consulta por segundo, contra 2.000 leituras. É 0,03%: três em cada 10 mil.',
                          'right! Each page is requested 100 times per second, but only goes to the database once every 30 seconds: 20 pages ÷ 30 s ≈ 0.67 queries per second, against 2,000 reads. That’s 0.03%: three in every 10,000.'),
               'wrong': T('olhe a métrica de pedidos que vão ao banco: 0,03%. Cada página é pedida 100 vezes por segundo, mas só é montada de novo quando a cópia vence, a cada 30 s. Com dados muito pedidos, até um TTL curto corta quase tudo.',
                          'look at the metric for requests that reach the database: 0.03%. Each page is requested 100 times per second, but only rebuilt when the copy expires, every 30 s. With heavily read data, even a short TTL cuts almost everything.'),
               'skipped': T('sem palpite? Rode e olhe quantos pedidos chegam ao banco.', 'no guess? Run it and see how many requests reach the database.')},
  'coach': {'ui': T('palpite anotado. Rode e olhe a porcentagem que vai ao banco e as consultas por segundo.', 'guess noted. Run it and look at the share that reaches the database and the queries per second.'),
            'cmd': T('palpite anotado. Rode cachear e olhe a primeira métrica.', 'guess noted. Run cache and look at the first metric.')},
  'tryNext': {'ui': T('Agora coloque o TTL em 0 (sem cache). Depois volte para 30 e desligue a trava.', 'Now set the TTL to 0 (no cache). Then go back to 30 and turn the lock off.'),
              'cmd': T('Rode cachear --ttl 0 e depois cachear --trava nao.', 'Run cache --ttl 0 and then cache --lock no.')},
  'why': {'simples': T('Cache é guardar perto uma cópia do que todo mundo pergunta. Em vez de cada aluno ir até a cozinha perguntar o cardápio, a tia prega o cardápio na parede. A cozinha responde uma vez, a parede responde mil.\nO TTL é a validade da cópia: depois de 30 segundos, alguém busca na cozinha de novo. O problema é quando a cozinha muda o preço e a parede continua com o antigo. Por isso, quando o preço muda, o certo é arrancar o papel da parede (invalidar), e não esperar ele vencer.\nE tem a corrida: se o papel cai e 20 alunos correm juntos para a cozinha perguntar a mesma coisa, a cozinha trava. A trava é combinar que só um vai perguntar e os outros esperam ele voltar.',
                       'A cache is keeping a nearby copy of what everybody asks. Instead of every student walking to the kitchen to ask for the menu, the cook pins the menu on the wall. The kitchen answers once, the wall answers a thousand times.\nThe TTL is the copy’s expiry: after 30 seconds, someone fetches from the kitchen again. The problem is when the kitchen changes the price and the wall still shows the old one. So when the price changes, the right move is to tear the paper off the wall (invalidate), not wait for it to expire.\nAnd there’s the stampede: if the paper falls and 20 students run to the kitchen together to ask the same thing, the kitchen jams. The lock is agreeing that only one goes to ask and the others wait for them to come back.'),
          'dev': T('O padrão mais comum é o cache-aside: a aplicação procura no cache; se não acha (miss), lê do banco, grava no cache com TTL e responde. Na escrita, atualiza o banco e apaga a chave (DEL), para a próxima leitura buscar o dado novo. Apagar costuma ser mais seguro que regravar o valor, porque duas escritas concorrentes podem gravar no cache na ordem errada.\nO TTL é o limite de quanto tempo um dado velho pode viver se a invalidação falhar, então use os dois: invalidação na escrita e TTL como rede de segurança. Para evitar que todas as chaves vençam juntas, some um pequeno sorteio ao TTL (jitter). E só cacheie o que é lido muito mais do que muda; dado por usuário e com permissão pede chave que inclua o usuário.',
                   'The most common pattern is cache-aside: the app looks in the cache; on a miss, it reads from the database, stores it in the cache with a TTL and answers. On writes, it updates the database and deletes the key (DEL), so the next read fetches fresh data. Deleting is usually safer than rewriting the value, because two concurrent writes can store into the cache in the wrong order.\nThe TTL bounds how long stale data can live if invalidation fails, so use both: invalidation on write and TTL as a safety net. To keep all keys from expiring together, add a small random amount to the TTL (jitter). And only cache what is read far more than it changes; per-user, permission-bound data needs a key that includes the user.'),
          'especialista': T('O estouro de cache (cache stampede, ou dogpile) acontece quando uma chave quente vence e todos os pedidos daquele instante vão ao banco ao mesmo tempo. Defesas: single-flight ou trava por chave (no Redis, SET chave valor NX PX 5000 para só um reconstruir), servir o valor velho enquanto um reconstrói em segundo plano (stale-while-revalidate), renovar antes de vencer com uma probabilidade que sobe perto do fim (expiração antecipada probabilística) e jitter no TTL.\nOutros cuidados: o cache vazio depois de um reinício (cache frio) pode derrubar o banco, então aqueça ou limite a reconstrução; política de despejo quando a memória enche (no Redis, maxmemory-policy, como allkeys-lru); chaves inexistentes também podem ser cacheadas por pouco tempo, para um robô não martelar o banco pedindo ids que não existem; e cache não é fonte da verdade: o sistema precisa funcionar, mais lento, sem ele.',
                            'A cache stampede (or dogpile) happens when a hot key expires and every request at that instant goes to the database at once. Defenses: single-flight or a per-key lock (in Redis, SET key value NX PX 5000 so only one rebuilds), serving the stale value while one rebuilds in the background (stale-while-revalidate), refreshing before expiry with a probability that rises near the end (probabilistic early expiration) and TTL jitter.\nOther concerns: an empty cache after a restart (cold cache) can knock the database over, so warm it up or throttle rebuilds; an eviction policy for when memory fills up (in Redis, maxmemory-policy, such as allkeys-lru); missing keys can be cached briefly too, so a bot can’t hammer the database asking for ids that don’t exist; and the cache isn’t the source of truth: the system must work, slower, without it.')},
  'break': {'mission': {'ui': T('hora de quebrar: guarde o cardápio por 1 hora e não apague a cópia quando o preço mudar.', 'time to break it: keep the menu for 1 hour and don’t delete the copy when the price changes.'),
                        'cmd': T('hora de quebrar: rode cachear --ttl 3600 --invalidar nao', 'time to break it: run cache --ttl 3600 --invalidate no')},
            'success': T('Quebrou: o preço do pastel mudou às 10h, mas a cópia no cache não foi apagada e vale por {staleS} s. Por até {staleMin} minutos, os alunos veem o preço velho no app e o novo no caixa. Cache rápido e errado é só um erro rápido.',
                         'Broken: the pastel’s price changed at 10 am, but the cached copy wasn’t deleted and is valid for {staleS} s. For up to {staleMin} minutes, students see the old price in the app and the new one at the register. A fast, wrong cache is just a fast mistake.'),
            'calm': T('{missPct}% dos pedidos vão ao banco ({dbQps} consultas/s), o pior momento espera {worstMs} ms e o preço velho dura no máximo {staleS} s. Para quebrar, guarde o cardápio por 1 hora sem invalidar.',
                      '{missPct}% of requests reach the database ({dbQps} queries/s), the worst moment waits {worstMs} ms and the old price lasts at most {staleS} s. To break it, keep the menu for 1 hour without invalidating.')},
  'hints': {'ui': T(['Escolha o TTL, se a cópia é apagada quando o dado muda e se existe trava.', 'TTL longo sem invalidação deixa o dado velho vivo por muito tempo.', 'Coloque o TTL em 3600 e desligue invalidar.'],
                    ['Pick the TTL, whether the copy is deleted when data changes and whether there is a lock.', 'A long TTL without invalidation keeps stale data alive for a long time.', 'Set the TTL to 3600 and turn invalidate off.']),
            'cmd': T(['O nome da chave é opcional; --ttl (segundos), --invalidar e --trava também.', '--invalidar e --trava aceitam sim ou nao.', 'cachear --ttl 3600 --invalidar nao'],
                     ['The key name is optional; so are --ttl (seconds), --invalidate and --lock.', '--invalidate and --lock take yes or no.', 'cache --ttl 3600 --invalidate no'])},
  'errors': {'belowMin.ttl': T('O TTL não fica negativo. 0 é sem cache.', 'The TTL can’t be negative. 0 means no cache.'),
             'aboveMax.ttl': T('Até 3600 segundos (1 hora) nesta simulação.', 'Up to 3600 seconds (1 hour) in this simulation.'),
             'notBool.invalidate': T('Use sim ou nao.', 'Use yes or no.'), 'notBool.lock': T('Use sim ou nao.', 'Use yes or no.')},
  'controls': {'arg': T('Chave no cache', 'Cache key'), 'ttl': T('TTL (segundos; 0 = sem cache)', 'TTL (seconds; 0 = no cache)'),
               'invalidate': T('Apagar a cópia quando o preço muda', 'Delete the copy when the price changes'), 'lock': T('Só um pedido reconstrói (trava)', 'Only one request rebuilds (lock)')},
  'scene': {'label': T('O cardápio no horário de almoço', 'The menu at lunchtime'), 'empty': T('Rode para abrir o cardápio.', 'Run to open the menu.'),
    'missM': T('pedidos que vão ao banco', 'requests that reach the database'), 'dbM': T('consultas ao banco por segundo', 'database queries per second'),
    'worstM': T('pior espera, quando a cópia vence', 'worst wait, when the copy expires'), 'staleM': T('segundos com preço velho', 'seconds with the old price'),
    'flowLabel': T('O caminho de uma leitura (simulado)', 'The path of a read (simulated)'),
    'student': T('Aluno', 'Student'), 'db': T('Banco', 'Database'),
    'ttlSub': T('TTL {ttl} s', 'TTL {ttl} s'), 'off': T('desligado', 'off'), 'dbSub': T('{dbQps} consultas/s', '{dbQps} queries/s'),
    'chartLabel': T('Consultas abertas no banco ao mesmo tempo, no primeiro minuto (simulado)', 'Queries open in the database at once, during the first minute (simulated)'),
    'series': T('consultas simultâneas', 'concurrent queries'), 'poolLine': T('pool do banco: 100 conexões', 'database pool: 100 connections'),
    'termLabel': T('Terminal (simulado)', 'Terminal (simulated)'),
    'tInval': T('~ 10:00 o preço mudou → DEL na chave; o próximo pedido busca no banco', '~ 10:00 the price changed → DEL on the key; the next request goes to the database'),
    'tNoInval': T('? 10:00 o preço mudou no banco, mas a chave continua lá até o TTL acabar', '? 10:00 the price changed in the database, but the key stays until the TTL runs out'),
    'tNoCache': T('! sem cache: todo pedido monta a página no banco', '! no cache: every request builds the page in the database'),
    'staleNote': T('Preço velho no ar por até {staleMin} minutos: o cache não sabe que o banco mudou, e ninguém avisou.', 'Old price live for up to {staleMin} minutes: the cache doesn’t know the database changed, and nobody told it.'),
    'staleShortNote': T('Sem invalidação, o preço velho pode durar até {staleS} s. Às vezes isso é aceitável (um placar, um contador de visitas); preço no caixa geralmente não é.', 'Without invalidation, the old price can last up to {staleS} s. Sometimes that’s acceptable (a scoreboard, a visit counter); a price at the register usually isn’t.'),
    'stampedeNote': T('Estouro de cache: quando as 20 páginas vencem juntas, uns 400 pedidos vão ao banco no mesmo instante, contra um pool de 100 conexões. O pior pedido espera {worstMs} ms.', 'Cache stampede: when the 20 pages expire together, about 400 requests hit the database at the same instant, against a pool of 100 connections. The worst request waits {worstMs} ms.'),
    'meltNote': T('Sem cache, 2.000 consultas/s num banco que aguenta 500: {errPct}% dos pedidos dão erro e o resto espera na fila.', 'Without a cache, 2,000 queries/s on a database that handles 500: {errPct}% of requests fail and the rest wait in line.'),
    'okNote': T('Cópia curta, apagada quando o preço muda e reconstruída por um pedido só: o banco quase nem percebe o almoço.', 'A short-lived copy, deleted when the price changes and rebuilt by a single request: the database barely notices lunch.')},
  'data': {},
  'recipe': {'steps': [
     T('Suba um Redis e abra o cliente dele:\ndocker run -d --name cache ' + REDIS_IMG + '\ndocker exec -it cache redis-cli',
       'Start Redis and open its client:\ndocker run -d --name cache ' + REDIS_IMG + '\ndocker exec -it cache redis-cli'),
     T('Grave o cardápio com validade de 30 segundos e leia de volta:\nSET cardapio:hoje "pastel 6,00" EX 30\nGET cardapio:hoje\nTTL cardapio:hoje\nRepita o TTL algumas vezes: o número desce. Depois de 30 s, o GET devolve (nil).',
       'Store the menu with a 30-second expiry and read it back:\nSET cardapio:hoje "pastel 6,00" EX 30\nGET cardapio:hoje\nTTL cardapio:hoje\nRepeat TTL a few times: the number goes down. After 30 s, GET returns (nil).'),
     T('Agora a invalidação: grave por 1 hora e apague quando o "preço mudar":\nSET cardapio:hoje "pastel 6,00" EX 3600\nDEL cardapio:hoje\nGET cardapio:hoje',
       'Now invalidation: store it for 1 hour and delete it when the "price changes":\nSET cardapio:hoje "pastel 6,00" EX 3600\nDEL cardapio:hoje\nGET cardapio:hoje'),
     T('Veja a contagem de acertos e erros do cache:\nINFO stats\nProcure as linhas keyspace_hits e keyspace_misses. Saia com exit e limpe: docker rm -f cache',
       'See the cache’s hit and miss counters:\nINFO stats\nLook for the keyspace_hits and keyspace_misses lines. Leave with exit and clean up: docker rm -f cache')],
   'ok': T('o GET devolve "pastel 6,00", o TTL desce a cada vez e, depois de 30 s, o GET devolve (nil); o DEL responde (integer) 1 e o GET seguinte dá (nil); no INFO stats, keyspace_hits e keyspace_misses contam os seus acertos e erros.',
           'GET returns "pastel 6,00", TTL goes down each time and, after 30 s, GET returns (nil); DEL answers (integer) 1 and the next GET gives (nil); in INFO stats, keyspace_hits and keyspace_misses count your hits and misses.')}}

t4 = {'pt': {'objectives': ['Explicar o que é cache e por que ele alivia o banco.', 'Usar TTL e invalidação para controlar dado velho.', 'Reconhecer o estouro de cache e uma defesa (trava).'], 'minutes': 20,
  'activity': 'Cardápio na parede: um aluno é a cozinha (demora 10 segundos para responder) e a turma pergunta o cardápio. Rodada 1: todo mundo pergunta à cozinha. Rodada 2: a cozinha escreve no quadro, com validade de 1 minuto. Rodada 3: o preço muda e ninguém apaga o quadro. Rodada 4: o quadro é apagado e todos correm juntos à cozinha.',
  'discussion': ['Que informações da escola poderiam ficar "na parede" por um dia inteiro? E quais nunca?', 'O que é pior: o cardápio velho por 1 minuto ou a cozinha travada por 1 minuto?'],
  'misconceptions': ['"Cache sempre deixa tudo certo e mais rápido." Ele deixa mais rápido e pode deixar errado, se não for invalidado.', '"TTL curto resolve dado velho." Ajuda, mas o certo é apagar a cópia quando o dado muda.']},
 'en': {'objectives': ['Explain what a cache is and why it relieves the database.', 'Use TTL and invalidation to control stale data.', 'Recognize a cache stampede and one defense (a lock).'], 'minutes': 20,
  'activity': 'Menu on the wall: one student is the kitchen (takes 10 seconds to answer) and the class asks for the menu. Round 1: everybody asks the kitchen. Round 2: the kitchen writes it on the board, valid for 1 minute. Round 3: the price changes and nobody erases the board. Round 4: the board is erased and everyone runs to the kitchen together.',
  'discussion': ['Which school information could stay "on the wall" for a whole day? And which never?', 'What’s worse: an old menu for 1 minute or a jammed kitchen for 1 minute?'],
  'misconceptions': ['"A cache always makes everything correct and faster." It makes things faster and can make them wrong, if not invalidated.', '"A short TTL solves stale data." It helps, but the right thing is deleting the copy when the data changes.']}}
write('04-cache', s4, loc4('pt'), loc4('en'), t4)

# ================================================================== 5 · banco e réplica
def busiest(k):
  if k == 0: return 'writes + reads'
  return f"max(writes + (rywRead == 'primary' ? ryw : 0), (reads - (rywRead == 'primary' ? ryw : 0)) / {k})"
ROWS5 = '[' + ', '.join(f"[{k}, round({busiest(k)}), {busiest(k)} > nodeCap ? '@stOver' : '@stOk']" for k in range(4)) + ']'
TONES5 = '[' + ', '.join(f"replicas == {k} ? ({busiest(k)} > nodeCap ? 'bad' : 'info') : 'neutral'" for k in range(4)) + ']'
REPL_ROWS = [f' 172.18.0.{i + 3}  | streaming' for i in range(5)]
s5 = step('sd-banco-replica', 5, TRACK, 20, ['banco-de-dados', 'replicacao', 'replica-de-leitura', 'lag', 'read-your-writes', 'postgres'],
  ['sd-cache'], SIM,
  loc('replicar', 'replicate'),
  {'name': 'text', 'required': False, 'default': loc('secretaria', 'school-office'), 'ui': 'text'},
  [flag('replicas', 'replicas', 'replicas', 'int', min=0, max=5, default=2, ui='slider'),
   flag('lag', 'atraso', 'lag', 'int', min=0, max=5000, step=50, default=500, ui='slider'),
   flag('rywRead', 'ler-apos-escrita', 'read-after-write', 'enum',
        options=[opt('primary', 'primario', 'primary'), opt('replica', 'replica', 'replica')], default='primary', ui='select')],
  {'options': ['one', 'two', 'three'], 'answer': 'two'}, 'staleRead',
  {'live': True,
   'consts': {'reads': 1500, 'writes': 100, 'ryw': 100, 'nodeCap': 1000, 'svcMs': 5, 'reloadMs': 300, 'replRows': REPL_ROWS},
   'compute': {
     'toPrimary': "replicas == 0 ? reads : (rywRead == 'primary' ? ryw : 0)",
     'replicaReads': 'reads - toPrimary',
     'perReplica': 'replicas == 0 ? 0 : round(replicaReads / replicas)',
     'primaryLoad': 'writes + toPrimary',
     'readNode': 'replicas == 0 ? primaryLoad : max(perReplica, primaryLoad)',
     'p95Read': p95_expr('readNode', 'nodeCap', 'svcMs'),
     'errPct': 'round((1 - min(1, nodeCap / readNode)) * 100, 1)',
     'isStale': "rywRead == 'replica' && replicas > 0 && lag > reloadMs",
     'isFragile': "rywRead == 'replica' && replicas > 0 && lag <= reloadMs",
     'rows': ROWS5, 'tones': TONES5,
     'psql': ("concat(['$ psql -c \"SELECT client_addr, state FROM pg_stat_replication;\"', ' client_addr |   state', '-------------+-----------'], "
              "slice(replRows, 0, replicas), ['(' + replicas + (replicas == 1 ? ' row)' : ' rows)')], "
              "[rywRead == 'primary' || replicas == 0 ? '@tPrimary' : (isStale ? '@tStale' : '@tFresh')])")},
   'cases': [
     {'when': 'isStale', 'flags': ['staleRead']},
     {'when': 'readNode > nodeCap', 'flags': ['overload']},
     {'when': 'replicas == 0', 'flags': ['noReplica']},
     {'when': 'isFragile', 'flags': ['fragile']},
     {'when': 'true', 'vars': {'p95Read': 'p95Read', 'errPct': 'errPct', 'perReplica': 'perReplica', 'primaryLoad': 'primaryLoad', 'readNode': 'readNode'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@p95M', 'value': '=p95Read', 'format': 'ms', 'tone': "=p95Read > 300 ? 'bad' : 'ok'"},
       {'label': '@errM', 'value': '=errPct', 'format': 'pct', 'tone': "=errPct > 0 ? 'bad' : 'ok'"},
       {'label': '@busyM', 'value': '=readNode', 'format': 'int', 'tone': "=readNode > nodeCap ? 'bad' : (readNode > 800 ? 'warn' : 'ok')"},
       {'label': '@lagM', 'value': "=replicas > 0 ? lag : '@dash'", 'format': 'ms', 'tone': "=isStale ? 'bad' : 'info'"}]},
     {'type': 'flow', 'label': '@flowLabel', 'steps': [
       {'label': '@write', 'sub': '@writeSub', 'tone': 'info'},
       {'label': '@primary', 'sub': '@primarySub', 'tone': "=primaryLoad > nodeCap ? 'bad' : 'ok'"},
       {'label': '@replicasL', 'sub': "=replicas > 0 ? '@replSub' : '@noRepl'", 'tone': "=replicas == 0 ? 'dim' : (perReplica > nodeCap ? 'bad' : 'ok')"},
       {'label': '@reread', 'sub': "=rywRead == 'primary' || replicas == 0 ? '@readPrimary' : '@readReplica'", 'tone': "=isStale ? 'bad' : (isFragile ? 'warn' : 'ok')"}]},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['@colReplicas', '@colBusiest', '@colState'], 'rows': '=rows', 'tones': '=tones', 'caption': '@tableCap'},
     {'type': 'terminal', 'label': '@termLabel', 'lines': '=psql'},
     {'type': 'note', 'when': '=isStale', 'tone': 'bad', 'text': '@staleNote'},
     {'type': 'note', 'when': '=isFragile', 'tone': 'warn', 'text': '@fragileNote'},
     {'type': 'note', 'when': '=readNode > nodeCap', 'tone': 'bad', 'text': '@overNote'},
     {'type': 'note', 'when': '=!isStale && !isFragile && readNode <= nodeCap', 'tone': 'ok', 'text': '@okNote'}]})

def loc5(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Banco e réplica', 'Database and replica'),
  'subtitle': T('O caderno oficial da secretaria e as fotocópias espalhadas pela escola: rápidas de ler, mas sempre um pouco atrasadas', 'The school office’s official notebook and the photocopies around the school: quick to read, but always a little behind'),
  'mission': T('Semana de matrícula: o sistema da secretaria recebe 1.500 leituras por segundo (boletim, horário, cadastro) e 100 escritas por segundo. Cada servidor de banco aguenta 1.000 operações por segundo. As escritas vão sempre para o banco principal (primário); as leituras podem ir para réplicas, que recebem as mudanças com um pouco de atraso. A Ana salva o telefone novo e recarrega a página 300 ms depois. Escolha quantas réplicas usar e de onde vem a leitura logo depois de uma escrita.',
               'Enrollment week: the school office system gets 1,500 reads per second (report cards, timetables, records) and 100 writes per second. Each database server handles 1,000 operations per second. Writes always go to the main database (the primary); reads can go to replicas, which receive changes with a little delay. Ana saves her new phone number and reloads the page 300 ms later. Choose how many replicas to use and where the read right after a write comes from.'),
  'predict': {'question': T('cada banco aguenta 1.000 operações/s. Com 1.500 leituras/s, qual é o mínimo de réplicas de leitura para ninguém ficar sem resposta?', 'each database handles 1,000 operations/s. With 1,500 reads/s, what’s the minimum number of read replicas so nobody goes unanswered?'),
    'options': {'one': T('1 réplica: ela tira as leituras do primário', '1 replica: it takes the reads off the primary'),
                'two': T('2 réplicas: as leituras precisam ser divididas', '2 replicas: the reads need to be split'),
                'three': T('3 réplicas, para garantir', '3 replicas, to be safe')}},
  'feedback': {'right': T('isso! Com 1 réplica, ela recebe 1.400 leituras/s (as outras 100 são de quem acabou de salvar e vão ao primário) e aguenta 1.000. Com 2, cada uma fica com 700/s, 70% da capacidade, e o p95 cai para 50 ms. A tabela mostra cada caso.',
                          'right! With 1 replica, it gets 1,400 reads/s (the other 100 belong to people who just saved and go to the primary) and handles 1,000. With 2, each gets 700/s, 70% of capacity, and p95 drops to 50 ms. The table shows each case.'),
               'wrong': T('olhe a tabela: com 1 réplica, ela recebe 1.400 leituras/s e aguenta 1.000, então estoura. Com 2, cada uma fica com 700/s. Mais réplicas dão folga, mas o mínimo é 2.',
                          'look at the table: with 1 replica, it gets 1,400 reads/s and handles 1,000, so it overflows. With 2, each gets 700/s. More replicas give headroom, but the minimum is 2.'),
               'skipped': T('sem palpite? Rode e olhe a tabela de réplicas.', 'no guess? Run it and look at the replicas table.')},
  'coach': {'ui': T('palpite anotado. Rode com 2 réplicas e olhe a tabela: ela mostra também 0, 1 e 3.', 'guess noted. Run with 2 replicas and look at the table: it also shows 0, 1 and 3.'),
            'cmd': T('palpite anotado. Rode replicar e olhe a tabela de réplicas.', 'guess noted. Run replicate and look at the replicas table.')},
  'tryNext': {'ui': T('Agora deixe só 1 réplica. Depois volte para 2, leia da réplica e baixe o atraso para 100 ms.', 'Now keep only 1 replica. Then go back to 2, read from the replica and lower the lag to 100 ms.'),
              'cmd': T('Rode replicar --replicas 1 e depois replicar --ler-apos-escrita replica --atraso 100.', 'Run replicate --replicas 1 and then replicate --read-after-write replica --lag 100.')},
  'why': {'simples': T('O primário é o caderno oficial da secretaria: só ele recebe as mudanças, para não existirem dois cadernos discordando. As réplicas são fotocópias que ficam nas outras salas. Muita gente consulta ao mesmo tempo e ninguém precisa fazer fila na secretaria.\nSó que a fotocópia é atualizada depois: existe um atraso entre escrever no caderno e a cópia mudar. Para quase tudo, tudo bem: o horário da semana pode estar meio segundo atrasado. Mas se a Ana acabou de mudar o telefone e vai conferir, ela precisa ler no caderno oficial. Senão ela vê o número velho, acha que não salvou e salva de novo.\nE repare: fotocópia ajuda quem lê. Quem escreve continua indo ao mesmo caderno.',
                       'The primary is the school office’s official notebook: only it receives changes, so there are never two notebooks disagreeing. Replicas are photocopies kept in other rooms. Lots of people can look things up at once and nobody has to line up at the office.\nBut the photocopy is updated afterwards: there’s a delay between writing in the notebook and the copy changing. For almost everything, that’s fine: the weekly timetable can be half a second behind. But if Ana just changed her phone number and goes to check, she needs to read the official notebook. Otherwise she sees the old number, thinks it didn’t save and saves again.\nAnd notice: photocopies help readers. Writers still go to the same notebook.'),
          'dev': T('Na replicação primário-réplica, o primário grava cada mudança no seu log (no PostgreSQL, o WAL) e as réplicas aplicam esse log. Na replicação assíncrona, o primário confirma a escrita sem esperar as réplicas, então elas ficam um pouco atrás (o lag): milissegundos num dia calmo, segundos ou mais sob carga ou rede ruim.\nPara não ler o próprio dado velho (read-your-writes): mande ao primário as leituras de quem acabou de escrever (por alguns segundos, ou na mesma sessão), ou leia da réplica só depois que ela alcançou a posição do log da sua escrita. Réplica não escala escrita: para isso existem particionamento (sharding) e filas. E acompanhe o lag (no PostgreSQL, a view pg_stat_replication mostra replay_lag) com alerta.',
                   'In primary-replica replication, the primary writes every change to its log (in PostgreSQL, the WAL) and replicas apply that log. With asynchronous replication, the primary confirms the write without waiting for replicas, so they fall a little behind (the lag): milliseconds on a calm day, seconds or more under load or a bad network.\nTo avoid reading your own stale data (read-your-writes): send reads from whoever just wrote to the primary (for a few seconds, or within the same session), or read from the replica only after it has reached your write’s log position. Replicas don’t scale writes: that’s what partitioning (sharding) and queues are for. And track the lag (in PostgreSQL, the pg_stat_replication view shows replay_lag) with an alert.'),
          'especialista': T('Replicação síncrona elimina o lag para quem confirma (o primário espera ao menos uma réplica gravar), mas cada escrita fica mais lenta e, se a réplica síncrona some, as escritas podem parar: é uma troca entre durabilidade, latência e disponibilidade. Com assíncrona, um failover pode perder as últimas escritas confirmadas que ainda não tinham chegado à réplica promovida.\nFailover tem suas próprias armadilhas: detectar a queda sem falso positivo, promover uma réplica só (evitar dois primários, o split-brain), redirecionar as conexões e reconstruir o antigo primário como réplica. Ferramentas como Patroni e os bancos gerenciados da nuvem cuidam disso. Outras garantias que importam para o usuário: leituras monotônicas (não voltar no tempo ao trocar de réplica) e ordem causal. Lembre também que réplicas não protegem contra erro humano: um DELETE errado é replicado fielmente, então backup e recuperação até um ponto no tempo continuam necessários.',
                            'Synchronous replication removes the lag for confirmed writes (the primary waits for at least one replica to store them), but every write gets slower and, if the synchronous replica disappears, writes can stall: it’s a trade between durability, latency and availability. With asynchronous replication, a failover can lose the last confirmed writes that hadn’t reached the promoted replica yet.\nFailover has its own traps: detecting the outage without false positives, promoting only one replica (avoiding two primaries, the split-brain), redirecting connections and rebuilding the old primary as a replica. Tools like Patroni and the cloud’s managed databases handle this. Other guarantees that matter to users: monotonic reads (not going back in time when switching replicas) and causal ordering. Also remember replicas don’t protect against human error: a wrong DELETE is faithfully replicated, so backups and point-in-time recovery are still needed.')},
  'break': {'mission': {'ui': T('hora de quebrar: leia da réplica logo depois de salvar.', 'time to break it: read from the replica right after saving.'),
                        'cmd': T('hora de quebrar: rode replicar --ler-apos-escrita replica', 'time to break it: run replicate --read-after-write replica')},
            'success': T('Quebrou: a Ana salvou o telefone novo no primário e, 300 ms depois, recarregou a página lendo de uma réplica que estava {lag} ms atrasada. Ela viu o número antigo, achou que não tinha salvado e salvou de novo. Quem acabou de escrever precisa ler do caderno oficial.',
                         'Broken: Ana saved her new number on the primary and, 300 ms later, reloaded the page reading from a replica that was {lag} ms behind. She saw the old number, thought it hadn’t saved and saved again. Whoever just wrote needs to read from the official notebook.'),
            'calm': T('Leituras com p95 de {p95Read} ms, {errPct}% de erro e o banco mais ocupado com {readNode} operações/s. Para quebrar, leia da réplica logo depois de salvar.',
                      'Reads with a p95 of {p95Read} ms, {errPct}% errors and the busiest database at {readNode} operations/s. To break it, read from the replica right after saving.')},
  'hints': {'ui': T(['Escolha quantas réplicas, o atraso delas e de onde vem a leitura logo depois de salvar.', 'A réplica recebe a mudança depois do primário.', 'Escolha ler após escrita na "replica", com o atraso de 500 ms.'],
                    ['Pick how many replicas, their lag and where the read right after saving comes from.', 'The replica gets the change after the primary.', 'Pick read-after-write on the "replica", with the 500 ms lag.']),
            'cmd': T(['O nome é opcional; --replicas, --atraso (ms) e --ler-apos-escrita também.', '--ler-apos-escrita aceita primario ou replica.', 'replicar --ler-apos-escrita replica'],
                     ['The name is optional; so are --replicas, --lag (ms) and --read-after-write.', '--read-after-write takes primary or replica.', 'replicate --read-after-write replica'])},
  'errors': {'belowMin.replicas': T('Não existe réplica negativa. 0 é só o primário.', 'There’s no negative replica. 0 is the primary alone.'),
             'aboveMax.replicas': T('Até 5 réplicas nesta simulação.', 'Up to 5 replicas in this simulation.'),
             'belowMin.lag': T('O atraso não fica negativo: a réplica não lê o futuro.', 'The lag can’t be negative: replicas don’t read the future.'),
             'aboveMax.lag': T('Até 5000 ms nesta simulação.', 'Up to 5000 ms in this simulation.'),
             'notInEnum.rywRead': T('Use primario ou replica.', 'Use primary or replica.')},
  'controls': {'arg': T('Sistema', 'System'), 'replicas': T('Réplicas de leitura', 'Read replicas'), 'lag': T('Atraso da réplica (ms)', 'Replica lag (ms)'),
               'rywRead': T('Leitura logo depois de salvar vem do', 'Read right after saving comes from the')},
  'scene': {'label': T('A secretaria na semana de matrícula', 'The school office during enrollment week'), 'empty': T('Rode para abrir a matrícula.', 'Run to open enrollment.'),
    'p95M': T('p95 das leituras', 'read p95'), 'errM': T('leituras sem resposta', 'unanswered reads'),
    'busyM': T('banco mais ocupado (operações/s, de 1.000)', 'busiest database (operations/s, of 1,000)'), 'lagM': T('atraso da réplica', 'replica lag'), 'dash': '—',
    'flowLabel': T('Salvar e conferir (simulado)', 'Save and check (simulated)'),
    'write': T('Ana salva', 'Ana saves'), 'writeSub': T('telefone novo', 'new phone number'),
    'primary': T('Primário', 'Primary'), 'primarySub': T('{primaryLoad} operações/s', '{primaryLoad} operations/s'),
    'replicasL': T('Réplicas', 'Replicas'), 'replSub': T('{replicas} × {perReplica} leituras/s, {lag} ms atrás', '{replicas} × {perReplica} reads/s, {lag} ms behind'),
    'noRepl': T('nenhuma', 'none'), 'reread': T('Ana recarrega', 'Ana reloads'),
    'readPrimary': T('300 ms depois, lê do primário', '300 ms later, reads from the primary'), 'readReplica': T('300 ms depois, lê de uma réplica', '300 ms later, reads from a replica'),
    'tableLabel': T('Quantas réplicas aguentam a semana?', 'How many replicas survive the week?'),
    'colReplicas': T('réplicas', 'replicas'), 'colBusiest': T('mais ocupado (ops/s)', 'busiest (ops/s)'), 'colState': T('estado', 'state'),
    'stOk': T('aguenta', 'holds'), 'stOver': T('estoura', 'overflows'),
    'tableCap': T('Cada banco aguenta 1.000 operações/s. Com 0 réplicas, o primário faz tudo. Números simulados.', 'Each database handles 1,000 operations/s. With 0 replicas, the primary does everything. Simulated numbers.'),
    'termLabel': T('No primário (simulado)', 'On the primary (simulated)'),
    'tPrimary': T('+ Ana relê do primário: telefone novo', '+ Ana rereads from the primary: new number'),
    'tStale': T('! Ana relê da réplica, que ainda não recebeu a mudança: telefone antigo', '! Ana rereads from the replica, which hasn’t got the change yet: old number'),
    'tFresh': T('? Ana relê da réplica e, desta vez, a mudança já chegou', '? Ana rereads from the replica and, this time, the change has arrived'),
    'staleNote': T('A réplica está {lag} ms atrás e a Ana relê em 300 ms: ela vê o telefone antigo. Leia do primário logo depois de escrever.', 'The replica is {lag} ms behind and Ana rereads in 300 ms: she sees the old number. Read from the primary right after writing.'),
    'fragileNote': T('Funcionou porque o atraso ({lag} ms) está abaixo dos 300 ms da Ana. No primeiro pico, o atraso sobe e o número antigo volta a aparecer.', 'It worked because the lag ({lag} ms) is below Ana’s 300 ms. At the first peak, the lag rises and the old number shows up again.'),
    'overNote': T('O banco mais ocupado recebe {readNode} operações/s e aguenta 1.000: {errPct}% das leituras ficam sem resposta.', 'The busiest database gets {readNode} operations/s and handles 1,000: {errPct}% of reads go unanswered.'),
    'okNote': T('As leituras estão divididas e a Ana confere o próprio dado no primário: rápido e certo.', 'Reads are split and Ana checks her own data on the primary: fast and correct.')},
  'data': {},
  'recipe': {'steps': [
     T('Crie uma pasta escola-banco com dois arquivos. O replicacao.sh roda uma vez, quando o primário é criado:\n' + REPL_SH,
       'Create a folder escola-banco with two files. replicacao.sh runs once, when the primary is created:\n' + REPL_SH_EN),
     T('E o compose.yaml. A réplica copia o primário com pg_basebackup (-R deixa ela configurada como réplica) e depois liga em modo só leitura:\n' + compose_pg(),
       'And the compose.yaml. The replica copies the primary with pg_basebackup (-R leaves it configured as a replica) and then starts in read-only mode:\n' + compose_pg()),
     T('Suba e espere a réplica ficar pronta:\ndocker compose up -d\ndocker compose logs -f replica\nQuando aparecer database system is ready to accept read-only connections, saia com Ctrl+C.',
       'Start it and wait for the replica to be ready:\ndocker compose up -d\ndocker compose logs -f replica\nWhen database system is ready to accept read-only connections shows up, leave with Ctrl+C.'),
     T('No primário, veja a réplica conectada e grave um dado:\ndocker compose exec primary psql -U postgres -c "SELECT client_addr, state FROM pg_stat_replication;"\ndocker compose exec primary psql -U postgres -c "CREATE TABLE alunos (id int PRIMARY KEY, telefone text); INSERT INTO alunos VALUES (42, \'15 99999-0000\');"',
       'On the primary, see the connected replica and write some data:\ndocker compose exec primary psql -U postgres -c "SELECT client_addr, state FROM pg_stat_replication;"\ndocker compose exec primary psql -U postgres -c "CREATE TABLE alunos (id int PRIMARY KEY, telefone text); INSERT INTO alunos VALUES (42, \'15 99999-0000\');"'),
     T('Na réplica, leia o dado e tente escrever:\ndocker compose exec replica psql -U postgres -c "SELECT * FROM alunos;"\ndocker compose exec replica psql -U postgres -c "INSERT INTO alunos VALUES (43, \'15 98888-0000\');"',
       'On the replica, read the data and try to write:\ndocker compose exec replica psql -U postgres -c "SELECT * FROM alunos;"\ndocker compose exec replica psql -U postgres -c "INSERT INTO alunos VALUES (43, \'15 98888-0000\');"'),
     T('Desligue tudo: docker compose down', 'Shut everything down: docker compose down')],
   'ok': T('o pg_stat_replication do primário mostra uma linha com state streaming; o SELECT na réplica devolve o aluno 42; e o INSERT na réplica falha com ERROR: cannot execute INSERT in a read-only transaction.',
           'the primary’s pg_stat_replication shows one row with state streaming; the SELECT on the replica returns student 42; and the INSERT on the replica fails with ERROR: cannot execute INSERT in a read-only transaction.')}}

t5 = {'pt': {'objectives': ['Explicar o papel do primário e das réplicas de leitura.', 'Calcular quantas réplicas uma carga de leitura precisa.', 'Reconhecer o atraso de replicação e garantir que quem escreveu leia o próprio dado.'], 'minutes': 20,
  'activity': 'Caderno e fotocópias: um aluno é a secretaria com o caderno oficial; três têm "fotocópias" que só são atualizadas quando um mensageiro leva o recado (contem 5 segundos). A turma consulta as cópias. Um aluno muda um dado no caderno e corre para conferir numa cópia antes do mensageiro chegar.',
  'discussion': ['Que dados da escola podem ser lidos de uma cópia atrasada? Quais precisam vir do caderno oficial?', 'Por que mais fotocópias não ajudam a secretaria a escrever mais rápido?'],
  'misconceptions': ['"A réplica é igual ao primário a todo instante." Ela fica um pouco atrás, e às vezes bem atrás.', '"Réplica também serve de backup." Ela copia os erros também; backup é outra coisa.']},
 'en': {'objectives': ['Explain the role of the primary and of read replicas.', 'Work out how many replicas a read load needs.', 'Recognize replication lag and make sure whoever wrote reads their own data.'], 'minutes': 20,
  'activity': 'Notebook and photocopies: one student is the office with the official notebook; three have "photocopies" that are only updated when a messenger carries the note (count 5 seconds). The class looks things up in the copies. One student changes something in the notebook and runs to check a copy before the messenger arrives.',
  'discussion': ['Which school data can be read from a lagging copy? Which must come from the official notebook?', 'Why don’t more photocopies help the office write faster?'],
  'misconceptions': ['"The replica equals the primary at every moment." It lags a little, and sometimes a lot.', '"A replica also works as a backup." It copies the mistakes too; backup is something else.']}}
write('05-banco-e-replica', s5, loc5('pt'), loc5('en'), t5)

# ================================================================== 6 · fila
CHART6 = '[' + ', '.join(
  (f'min(qcap, growth * 60 * {t})' if t <= 10 else f'max(0, backlog - kRate * 60 * {t - 10})') for t in range(0, 16, 2)) + ']'
s6 = step('sd-fila', 6, TRACK, 20, ['fila', 'assincrono', 'back-pressure', 'idempotencia', 'desacoplamento'],
  ['sd-escalar-vertical-horizontal'], SIM,
  loc('atender', 'serve'),
  {'name': 'text', 'required': False, 'default': loc('pedidos-do-recreio', 'recess-orders'), 'ui': 'text'},
  [flag('mode', 'modo', 'mode', 'enum', options=[opt('queue', 'fila', 'queue'), opt('sync', 'sincrono', 'sync')], default='queue', ui='select'),
   flag('workers', 'cozinheiros', 'cooks', 'int', min=1, max=10, default=3, ui='slider'),
   flag('maxQueue', 'limite-fila', 'queue-limit', 'int', min=0, max=5000, step=50, default=0, ui='slider'),
   flag('idem', 'idempotente', 'idempotent', 'bool', default=True, ui='switch')],
  {'options': ['error', 'ticket', 'instant'], 'answer': 'ticket'}, 'counterJam',
  {'live': True,
   'consts': {'arrival': 9, 'durS': 600, 'perCook': 2, 'held': 4},
   'compute': {
     'isQueue': "mode == 'queue'",
     'kRate': 'workers * perCook',
     'growth': 'max(0, arrival - kRate)',
     'backlogRaw': 'growth * durS',
     'limited': 'maxQueue > 0 && backlogRaw > maxQueue',
     'qcap': 'maxQueue > 0 ? maxQueue : 1000000',
     'backlog': 'isQueue ? (limited ? maxQueue : backlogRaw) : 0',
     'rejected': 'isQueue && limited ? backlogRaw - maxQueue : 0',
     'rejectPct': 'round(rejected / (arrival * durS) * 100, 1)',
     'waitMin': 'isQueue ? round(backlog / kRate / 60, 1) : 0',
     'counterMs': 'isQueue ? 20 : (kRate > arrival ? round(1000 * max(0.5, 3 / (kRate - arrival))) : 30000)',
     'errPct': '!isQueue && kRate < arrival ? round((arrival - kRate) / arrival * 100, 1) : 0',
     'isJam': '!isQueue && kRate < arrival',
     'dups': 'isQueue && !idem ? held : 0',
     'series6': CHART6},
   'cases': [
     {'when': 'isJam', 'flags': ['counterJam']},
     {'when': 'backlog > 0', 'flags': ['queueGrew']},
     {'when': 'rejected > 0', 'flags': ['shedLoad']},
     {'when': 'dups > 0', 'flags': ['duplicates']},
     {'when': 'true', 'vars': {'kRate': 'kRate', 'backlog': 'backlog', 'waitMin': 'waitMin', 'errPct': 'errPct', 'rejected': 'rejected', 'rejectPct': 'rejectPct', 'counterMs': 'counterMs', 'dups': 'dups'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@counterM', 'value': '=counterMs', 'format': 'ms', 'tone': "=counterMs > 2000 ? 'bad' : (counterMs > 500 ? 'warn' : 'ok')"},
       {'label': '@errM', 'value': '=errPct', 'format': 'pct', 'tone': "=errPct > 0 ? 'bad' : 'ok'"},
       {'label': '@backlogM', 'value': '=backlog', 'format': 'int', 'tone': "=backlog > 0 ? 'warn' : 'ok'"},
       {'label': '@waitM', 'value': '=waitMin', 'format': 'min', 'tone': "=waitMin > 3 ? 'warn' : 'ok'"}]},
     {'type': 'queue', 'when': '=isQueue', 'label': '@queueLabel', 'producer': '@counter', 'empty': '@emptyQueue', 'messages': '=backlog',
      'consumers': [{'label': '@kitchen', 'note': '@kitchenRate', 'tone': "=growth > 0 ? 'warn' : 'ok'"},
                    {'label': '@restart', 'note': "=idem ? '@idemOn' : '@idemOff'", 'tone': "=idem ? 'ok' : 'bad'"}]},
     {'type': 'chart', 'when': '=isQueue', 'label': '@chartLabel', 'kind': 'line',
      'labels': ['0', '2', '4', '6', '8', '10', '12', '14'], 'series': [{'label': '@series', 'values': '=series6'}]},
     {'type': 'flow', 'when': '=!isQueue', 'label': '@flowLabel', 'steps': [
       {'label': '@student', 'tone': 'info'},
       {'label': '@counterL', 'sub': '@threadsSub', 'tone': "=isJam ? 'bad' : 'warn'"},
       {'label': '@kitchenL', 'sub': '@kitchenRate', 'tone': "=isJam ? 'bad' : 'ok'"}]},
     {'type': 'note', 'when': '=isJam', 'tone': 'bad', 'text': '@jamNote'},
     {'type': 'note', 'when': '=!isQueue && !isJam', 'tone': 'warn', 'text': '@syncSlowNote'},
     {'type': 'note', 'when': '=isQueue && backlog > 0 && !limited', 'tone': 'warn', 'text': '@backlogNote'},
     {'type': 'note', 'when': '=limited', 'tone': 'info', 'text': '@limitNote'},
     {'type': 'note', 'when': '=dups > 0', 'tone': 'bad', 'text': '@dupNote'},
     {'type': 'note', 'when': '=isQueue && backlog == 0 && dups == 0', 'tone': 'ok', 'text': '@okNote'}]})

def loc6(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Fila', 'Queue'),
  'subtitle': T('Pegue a senha e vá sentar: a cozinha trabalha no ritmo dela e o balcão continua livre', 'Take a ticket and go sit down: the kitchen works at its own pace and the counter stays free'),
  'mission': T('No recreio de 10 minutos, chegam 9 pedidos de lanche por segundo. Cada cozinheiro faz 2 lanches por segundo, e hoje são 3. No modo fila, o balcão anota o pedido, entrega uma senha e a cozinha vai tirando os pedidos da fila. No modo síncrono, o aluno fica parado no balcão até o lanche sair. No meio do recreio, um cozinheiro sai e volta (reinicia), e os 4 pedidos que estavam com ele voltam para a fila. Compare os dois modos, a quantidade de cozinheiros e um limite para a fila.',
               'During the 10-minute recess, 9 snack orders arrive per second. Each cook makes 2 snacks per second, and today there are 3. In queue mode, the counter writes down the order, hands out a ticket and the kitchen takes orders from the queue. In sync mode, the student stands at the counter until the snack comes out. Halfway through recess, a cook steps out and comes back (restarts), and the 4 orders they were holding go back to the queue. Compare both modes, the number of cooks and a limit for the queue.'),
  'predict': {'question': T('chegam 9 pedidos por segundo e a cozinha faz 6. Com fila, o que acontece com quem pede?', '9 orders arrive per second and the kitchen makes 6. With a queue, what happens to whoever orders?'),
    'options': {'error': T('Recebe um erro: a cozinha não dá conta', 'Gets an error: the kitchen can’t keep up'),
                'ticket': T('Recebe a senha na hora, mas o lanche demora mais', 'Gets the ticket right away, but the snack takes longer'),
                'instant': T('Recebe o lanche na hora: a fila resolve tudo', 'Gets the snack right away: the queue solves everything')}},
  'feedback': {'right': T('isso! O balcão responde em 20 ms, porque só anota e entrega a senha. Mas a fila cresce 3 pedidos por segundo: no fim do recreio são 1.800 esperando, e o último lanche sai uns 5 minutos depois. A fila absorve o pico; ela não cria cozinheiros.',
                          'right! The counter answers in 20 ms, because it only writes down the order and hands out the ticket. But the queue grows 3 orders per second: at the end of recess 1,800 are waiting, and the last snack comes out about 5 minutes later. The queue absorbs the peak; it doesn’t create cooks.'),
               'wrong': T('olhe as métricas: o balcão responde em 20 ms e ninguém recebe erro, mas 1.800 pedidos ficam esperando no fim do recreio e o último espera uns 5 minutos. Fila não faz a cozinha mais rápida; ela só impede o balcão de travar.',
                          'look at the metrics: the counter answers in 20 ms and nobody gets an error, but 1,800 orders are waiting at the end of recess and the last one waits about 5 minutes. A queue doesn’t make the kitchen faster; it only keeps the counter from jamming.'),
               'skipped': T('sem palpite? Rode e compare a resposta do balcão com a espera do último lanche.', 'no guess? Run it and compare the counter’s answer with the last snack’s wait.')},
  'coach': {'ui': T('palpite anotado. Rode e olhe a resposta do balcão, os pedidos na fila e o gráfico.', 'guess noted. Run it and look at the counter’s answer, the orders in the queue and the chart.'),
            'cmd': T('palpite anotado. Rode atender e olhe as métricas e o gráfico da fila.', 'guess noted. Run serve and look at the metrics and the queue chart.')},
  'tryNext': {'ui': T('Agora coloque 5 cozinheiros. Depois volte para 3 e limite a fila em 300 pedidos.', 'Now use 5 cooks. Then go back to 3 and limit the queue to 300 orders.'),
              'cmd': T('Rode atender --cozinheiros 5 e depois atender --limite-fila 300.', 'Run serve --cooks 5 and then serve --queue-limit 300.')},
  'why': {'simples': T('Sem fila, o aluno fica parado no balcão esperando o lanche. Se a cozinha é mais lenta que os pedidos, o balcão enche de gente parada, e até quem só queria olhar o cardápio não consegue chegar perto. O problema da cozinha vira problema do balcão.\nCom fila, o balcão só anota, entrega a senha e libera o aluno. A cozinha tira os pedidos na ordem, no ritmo dela. O pico do recreio vira uma fila que cresce e depois esvazia.\nMas fila não é mágica: se chegam 9 e saem 6 por segundo, ela cresce sem parar enquanto durar o pico. Às vezes o mais honesto é dizer "volte daqui a pouco" quando ela passa do limite, em vez de prometer um lanche que vai chegar frio.',
                       'Without a queue, the student stands at the counter waiting for the snack. If the kitchen is slower than the orders, the counter fills with people standing around, and even those who just wanted to look at the menu can’t get close. The kitchen’s problem becomes the counter’s problem.\nWith a queue, the counter just writes it down, hands out the ticket and frees the student. The kitchen takes orders in sequence, at its own pace. The recess peak becomes a queue that grows and then empties.\nBut a queue isn’t magic: if 9 come in and 6 go out per second, it keeps growing as long as the peak lasts. Sometimes the most honest thing is saying "come back in a bit" once it passes a limit, instead of promising a snack that will arrive cold.'),
          'dev': T('Uma fila desacopla quem produz de quem consome: a API grava a mensagem e responde 202 (aceito) ou devolve um número de acompanhamento, e workers processam depois. Isso protege a API de picos e de dependências lentas, e permite escalar os workers separadamente (aqui, 5 cozinheiros = 10 lanches/s, mais que os 9 que chegam).\nTrês cuidados: 1) back-pressure, ou seja, um limite de fila com rejeição educada (429, "tente de novo em X segundos") ou com o produtor desacelerando, para a espera não crescer sem fim; 2) idempotência, porque a maioria das filas entrega pelo menos uma vez: se o worker cai depois de fazer o lanche e antes de confirmar (ack), a mensagem volta e o lanche sai em dobro, a não ser que o worker reconheça o número do pedido; 3) monitorar a profundidade e a idade da mensagem mais velha, não só se a fila está no ar.',
                   'A queue decouples producers from consumers: the API stores the message and answers 202 (accepted) or returns a tracking number, and workers process it later. That protects the API from peaks and slow dependencies, and lets you scale workers separately (here, 5 cooks = 10 snacks/s, more than the 9 arriving).\nThree concerns: 1) back-pressure, meaning a queue limit with a polite rejection (429, "try again in X seconds") or with the producer slowing down, so the wait doesn’t grow forever; 2) idempotency, because most queues deliver at least once: if a worker crashes after making the snack and before confirming (ack), the message comes back and the snack is made twice, unless the worker recognizes the order number; 3) monitoring depth and the age of the oldest message, not just whether the queue is up.'),
          'especialista': T('A conta da fila é a Lei de Little: itens na fila = taxa de chegada × tempo de espera. Se a taxa de chegada passa da capacidade, a fila cresce linearmente e a espera junto, até o pico acabar ou a memória acabar. Por isso dimensione os consumidores pela taxa de pico e pelo tempo aceitável de esvaziar o atraso acumulado, e escale pelos sinais certos (profundidade e idade da mensagem mais velha, não CPU).\nNo modo síncrono, o recurso que acaba primeiro costuma ser o pool de threads ou de conexões do servidor: pedidos lentos seguram threads, e pedidos rápidos e sem relação passam a falhar (é a falha em cascata). Defesas: tempos-limite curtos, bulkheads (pools separados por dependência), circuit breaker e shedding de carga.\nEm filas reais, prefira um broker com confirmação (RabbitMQ, SQS, Kafka, Redis Streams com XACK): um simples POP remove a mensagem na leitura e ela some se o worker cair no meio. E mensagens que sempre falham vão para uma DLQ, para não travar a fila.',
                            'The queue math is Little’s Law: items in the queue = arrival rate × waiting time. If the arrival rate exceeds capacity, the queue grows linearly and so does the wait, until the peak ends or memory does. So size consumers by peak rate and by an acceptable time to drain the accumulated backlog, and scale on the right signals (depth and age of the oldest message, not CPU).\nIn sync mode, the resource that runs out first is usually the server’s thread or connection pool: slow requests hold threads, and fast, unrelated requests start failing (a cascading failure). Defenses: short timeouts, bulkheads (separate pools per dependency), circuit breakers and load shedding.\nWith real queues, prefer a broker with acknowledgements (RabbitMQ, SQS, Kafka, Redis Streams with XACK): a plain POP removes the message on read, and it’s gone if the worker crashes midway. And messages that always fail go to a DLQ, so they don’t jam the queue.')},
  'break': {'mission': {'ui': T('hora de quebrar: troque a fila pelo modo síncrono, com o aluno esperando no balcão.', 'time to break it: swap the queue for sync mode, with the student waiting at the counter.'),
                        'cmd': T('hora de quebrar: rode atender --modo sincrono', 'time to break it: run serve --mode sync')},
            'success': T('Quebrou: sem fila, cada aluno fica preso no balcão até o lanche sair. A cozinha faz {kRate} lanches/s e chegam 9: os atendentes do balcão ficaram todos ocupados esperando, {errPct}% dos pedidos estouraram o tempo-limite e até quem só queria ver o cardápio levou erro.',
                         'Broken: without a queue, each student is stuck at the counter until the snack comes out. The kitchen makes {kRate} snacks/s and 9 arrive: every counter clerk got stuck waiting, {errPct}% of orders hit the timeout and even those who only wanted to see the menu got an error.'),
            'calm': T('Balcão respondendo em {counterMs} ms, {errPct}% de erro, {backlog} pedidos na fila no fim do recreio e o último esperando {waitMin} min. Para quebrar, troque a fila pelo modo síncrono.',
                      'Counter answering in {counterMs} ms, {errPct}% errors, {backlog} orders in the queue at the end of recess and the last one waiting {waitMin} min. To break it, swap the queue for sync mode.')},
  'hints': {'ui': T(['Escolha o modo, quantos cozinheiros, o limite da fila e se o cozinheiro reconhece pedido repetido.', 'Sem fila, quem espera a cozinha ocupa o balcão.', 'Escolha o modo "sincrono" com 3 cozinheiros.'],
                    ['Pick the mode, how many cooks, the queue limit and whether the cook recognizes a repeated order.', 'Without a queue, whoever waits for the kitchen takes up the counter.', 'Pick "sync" mode with 3 cooks.']),
            'cmd': T(['O nome é opcional; --modo, --cozinheiros, --limite-fila e --idempotente também.', '--modo aceita fila ou sincrono.', 'atender --modo sincrono'],
                     ['The name is optional; so are --mode, --cooks, --queue-limit and --idempotent.', '--mode takes queue or sync.', 'serve --mode sync'])},
  'errors': {'notInEnum.mode': T('Use fila ou sincrono.', 'Use queue or sync.'),
             'belowMin.workers': T('Pelo menos 1 cozinheiro, senão ninguém come.', 'At least 1 cook, or nobody eats.'),
             'aboveMax.workers': T('Até 10 cozinheiros: a cozinha da escola é pequena.', 'Up to 10 cooks: the school kitchen is small.'),
             'belowMin.maxQueue': T('O limite não fica negativo. 0 é sem limite.', 'The limit can’t be negative. 0 means no limit.'),
             'aboveMax.maxQueue': T('Até 5000 pedidos nesta simulação.', 'Up to 5000 orders in this simulation.'),
             'notBool.idem': T('Use sim ou nao.', 'Use yes or no.')},
  'controls': {'arg': T('Nome da fila', 'Queue name'), 'mode': T('Modo', 'Mode'), 'workers': T('Cozinheiros', 'Cooks'),
               'maxQueue': T('Limite da fila (0 = sem limite)', 'Queue limit (0 = no limit)'), 'idem': T('Cozinheiro reconhece pedido repetido', 'Cook recognizes a repeated order')},
  'scene': {'label': T('O recreio na cantina', 'Recess at the canteen'), 'empty': T('Rode para abrir o recreio.', 'Run to start recess.'),
    'counterM': T('resposta do balcão (p95)', 'counter response (p95)'), 'errM': T('pedidos com erro', 'orders with errors'),
    'backlogM': T('pedidos na fila no fim do recreio', 'orders queued at the end of recess'), 'waitM': T('espera do último pedido', 'wait of the last order'),
    'queueLabel': T('Fila de pedidos (simulado)', 'Order queue (simulated)'), 'counter': T('balcão', 'counter'), 'emptyQueue': T('fila vazia', 'empty queue'),
    'kitchen': T('cozinha: {workers} cozinheiro(s)', 'kitchen: {workers} cook(s)'), 'kitchenRate': T('{kRate} lanches/s', '{kRate} snacks/s'),
    'restart': T('cozinheiro que reiniciou', 'cook who restarted'), 'idemOn': T('reconhece o número do pedido', 'recognizes the order number'), 'idemOff': T('faz de novo o que voltou', 'remakes what came back'),
    'chartLabel': T('Pedidos esperando na fila, minuto a minuto (o recreio acaba no minuto 10)', 'Orders waiting in the queue, minute by minute (recess ends at minute 10)'),
    'series': T('na fila', 'queued'),
    'flowLabel': T('Modo síncrono: o aluno espera no balcão (simulado)', 'Sync mode: the student waits at the counter (simulated)'),
    'student': T('Aluno', 'Student'), 'counterL': T('Balcão', 'Counter'), 'threadsSub': T('50 atendentes, cada um preso até o lanche sair', '50 clerks, each stuck until the snack comes out'),
    'kitchenL': T('Cozinha', 'Kitchen'),
    'jamNote': T('Balcão travado: chegam 9 pedidos/s e saem {kRate}. Os atendentes ficam todos esperando a cozinha, {errPct}% dos pedidos estouram o tempo-limite e qualquer outro pedido, até "ver cardápio", também falha.', 'Counter jammed: 9 orders/s come in and {kRate} go out. Every clerk is stuck waiting for the kitchen, {errPct}% of orders hit the timeout and any other request, even "see menu", fails too.'),
    'syncSlowNote': T('Sem erro, porque a cozinha ({kRate}/s) é mais rápida que os pedidos. Mas cada aluno fica até {counterMs} ms parado no balcão, e qualquer lentidão da cozinha vira fila no balcão.', 'No errors, because the kitchen ({kRate}/s) is faster than the orders. But each student stands at the counter for up to {counterMs} ms, and any kitchen slowdown becomes a line at the counter.'),
    'backlogNote': T('Ninguém recebeu erro, mas a fila cresceu até {backlog} pedidos: o último lanche sai {waitMin} min depois do fim do recreio. A fila absorveu o pico; faltaram cozinheiros.', 'Nobody got an error, but the queue grew to {backlog} orders: the last snack comes out {waitMin} min after recess ends. The queue absorbed the peak; there weren’t enough cooks.'),
    'limitNote': T('Back-pressure: com a fila no limite, {rejected} pedidos ({rejectPct}%) ouviram "volte em 1 minuto" (429) em vez de esperar um lanche que chegaria frio. A espera máxima caiu para {waitMin} min.', 'Back-pressure: with the queue at its limit, {rejected} orders ({rejectPct}%) heard "come back in 1 minute" (429) instead of waiting for a snack that would arrive cold. The longest wait dropped to {waitMin} min.'),
    'dupNote': T('O cozinheiro reiniciou e os {dups} pedidos que estavam com ele voltaram para a fila. Como ninguém confere o número do pedido, eles foram feitos (e cobrados) duas vezes.', 'The cook restarted and the {dups} orders they were holding went back to the queue. Since nobody checks the order number, they were made (and charged) twice.'),
    'okNote': T('A cozinha dá conta do pico: a fila não acumula e o pedido repetido do cozinheiro que reiniciou foi reconhecido.', 'The kitchen keeps up with the peak: the queue doesn’t pile up and the repeated orders from the cook who restarted were recognized.')},
  'data': {},
  'recipe': {'steps': [
     T('Suba um Redis para servir de fila:\ndocker run -d --name fila ' + REDIS_IMG, 'Start Redis to act as a queue:\ndocker run -d --name fila ' + REDIS_IMG),
     T('Num terminal, seja a cozinha: espere o próximo pedido (o 0 é esperar para sempre):\ndocker exec -it fila redis-cli BRPOP pedidos 0',
       'In one terminal, be the kitchen: wait for the next order (0 means wait forever):\ndocker exec -it fila redis-cli BRPOP pedidos 0'),
     T('Em outro terminal, seja o balcão: anote um pedido e veja a cozinha recebê-lo na hora:\ndocker exec fila redis-cli LPUSH pedidos pastel',
       'In another terminal, be the counter: write down an order and watch the kitchen receive it right away:\ndocker exec fila redis-cli LPUSH pedidos pastel'),
     T('Agora sem cozinha ligada, anote três pedidos, conte a fila e tire o primeiro:\ndocker exec fila redis-cli LPUSH pedidos coxinha suco bolo\ndocker exec fila redis-cli LLEN pedidos\ndocker exec fila redis-cli RPOP pedidos',
       'Now with no kitchen running, write down three orders, count the queue and take the first one:\ndocker exec fila redis-cli LPUSH pedidos coxinha suco bolo\ndocker exec fila redis-cli LLEN pedidos\ndocker exec fila redis-cli RPOP pedidos'),
     T('Repare: o RPOP tira o pedido da fila no momento da leitura. Se a cozinha caísse logo depois, o pedido sumiria. Por isso filas de verdade têm confirmação (ack). Limpe: docker rm -f fila',
       'Notice: RPOP removes the order from the queue at read time. If the kitchen crashed right after, the order would vanish. That’s why real queues have acknowledgements (ack). Clean up: docker rm -f fila')],
   'ok': T('a cozinha imprime 1) "pedidos" e 2) "pastel" assim que o balcão faz o LPUSH; depois o LLEN responde (integer) 3 e o RPOP devolve "coxinha", o primeiro que entrou.',
           'the kitchen prints 1) "pedidos" and 2) "pastel" as soon as the counter runs LPUSH; then LLEN answers (integer) 3 and RPOP returns "coxinha", the first one in.')}}

t6 = {'pt': {'objectives': ['Explicar como uma fila desacopla quem pede de quem faz.', 'Prever o crescimento da fila quando a chegada passa da capacidade.', 'Reconhecer back-pressure e idempotência como cuidados obrigatórios.'], 'minutes': 20,
  'activity': 'Senha da cantina: metade da turma faz pedidos em papeizinhos, três alunos são cozinheiros (cada um "faz" um pedido a cada 5 segundos). Rodada 1: quem pede fica em pé esperando o lanche. Rodada 2: quem pede deixa o papel numa caixa (a fila) e volta a sentar. Contem quantos estão em pé em cada rodada e quantos papéis sobram na caixa.',
  'discussion': ['O que a escola deveria fazer quando a caixa de pedidos fica cheia demais?', 'Como o cozinheiro sabe que um pedido repetido já foi feito?'],
  'misconceptions': ['"Fila deixa tudo mais rápido." Ela deixa a resposta rápida; o trabalho continua levando o mesmo tempo, ou mais.', '"Se está na fila, não se perde." Depende de confirmação: um POP simples some com o pedido se o worker cair.']},
 'en': {'objectives': ['Explain how a queue decouples who asks from who does the work.', 'Predict queue growth when arrivals exceed capacity.', 'Recognize back-pressure and idempotency as must-haves.'], 'minutes': 20,
  'activity': 'Canteen ticket: half the class writes orders on slips, three students are cooks (each "makes" one order every 5 seconds). Round 1: whoever orders stands waiting for the snack. Round 2: whoever orders drops the slip in a box (the queue) and sits back down. Count how many are standing in each round and how many slips are left in the box.',
  'discussion': ['What should the school do when the order box gets too full?', 'How does the cook know a repeated order was already made?'],
  'misconceptions': ['"A queue makes everything faster." It makes the response fast; the work still takes the same time, or more.', '"If it’s in the queue, it can’t get lost." That depends on acknowledgements: a plain POP loses the order if the worker crashes.']}}
write('06-fila', s6, loc6('pt'), loc6('en'), t6)

# ================================================================== 7 · missão: encurtador de links
s7 = step('sd-missao-encurtador', 7, TRACK, 30, ['missao', 'capacidade', 'cache', 'replica', 'rate-limit', 'fila', 'encurtador'],
  ['sd-balanceador', 'sd-cache', 'sd-banco-replica', 'sd-fila'], SIM,
  loc('desenhar', 'design'),
  {'name': 'text', 'required': False, 'default': loc('encurtador-da-escola', 'school-shortener'), 'ui': 'text'},
  [flag('servers', 'servidores', 'servers', 'int', min=1, max=8, default=1, ui='slider'),
   flag('cache', 'cache', 'cache', 'bool', default=False, ui='switch'),
   flag('replica', 'replica', 'replica', 'bool', default=False, ui='switch'),
   flag('ids', 'ids', 'ids', 'enum', options=[opt('seq', 'sequencial', 'sequential'), opt('random', 'aleatorio', 'random')], default='seq', ui='select'),
   flag('rateLimit', 'limite', 'limit', 'int', min=0, max=20000, uiMax=6000, step=100, default=0, ui='slider'),
   flag('clicks', 'cliques', 'clicks', 'enum', options=[opt('sync', 'sincrono', 'sync'), opt('queue', 'fila', 'queue')], default='sync', ui='select')],
  None, 'passed',
  {'live': True,
   'consts': {'R': 3000, 'bot': 400, 'lab': 600, 'newW': 5, 'capApp': 800, 'sApp': 20, 'capDb': 900, 'sDb': 10, 'hitRate': 0.75,
              'batch': 100, 'budget': 3500, 'maxLimit': 3000, 'pServer': 300, 'pLb': 100, 'pCache': 150, 'pDb': 400, 'pReplica': 400, 'pQueue': 80},
   'compute': {
     'botAllowed': 'rateLimit == 0 ? bot : min(bot, rateLimit / 60)',
     'labBlocked': 'rateLimit > 0 && rateLimit < lab ? (lab - rateLimit) / 60 : 0',
     'A': 'round(R + botAllowed + newW)',
     'hit': 'cache ? hitRate : 0',
     'miss': '1 - hit',
     'readsDb': 'R * miss + botAllowed',
     'isSync': "clicks == 'sync'",
     'writesDb': '(isSync ? R : R / batch) + newW',
     'primLoad': 'writesDb + (replica ? readsDb / 2 : readsDb)',
     'repLoad': 'replica ? readsDb / 2 : 0',
     'appCap': 'servers * capApp',
     'pApp': p95_expr('A', 'appCap', 'sApp'),
     'pPrim': p95_expr('primLoad', 'capDb', 'sDb'),
     'pRead': f"replica ? max({p95_expr('repLoad', 'capDb', 'sDb')}, pPrim) : pPrim",
     'okApp': served_expr('A', 'appCap'),
     'okPrim': served_expr('primLoad', 'capDb'),
     'okRead': f"replica ? min({served_expr('repLoad', 'capDb')}, okPrim) : okPrim",
     'p95': 'min(5000, pApp + (cache ? 2 : 0) + (miss > 0.05 ? pRead : 0) + (isSync ? pPrim : 0))',
     'okFrac': 'okApp * (cache ? hit + miss * okRead : okRead) * (isSync ? okPrim : 1) * (1 - labBlocked / R)',
     'errPct': 'round((1 - okFrac) * 100, 2)',
     'cost': 'servers * pServer + (servers >= 2 ? pLb : 0) + (cache ? pCache : 0) + pDb + (replica ? pReplica : 0) + (isSync ? 0 : pQueue)',
     'found': "ids == 'seq' ? round(botAllowed * 3600 * 0.9) : 0",
     'uApp': 'round(A / appCap * 100)', 'uPrim': 'round(primLoad / capDb * 100)', 'uRep': 'round(repLoad / capDb * 100)',
     'okP95': 'p95 <= 300',
     'okErr': 'errPct <= 0.5',
     'n1Cap': '(servers - 1) * capApp',
     'okN1': 'servers >= 2 && n1Cap >= A',
     'okIds': "ids == 'random'",
     'okLimit': 'rateLimit >= lab && rateLimit <= maxLimit',
     'okCost': 'cost <= budget',
     'okCount': '(okP95 ? 1 : 0) + (okErr ? 1 : 0) + (okN1 ? 1 : 0) + (okIds ? 1 : 0) + (okLimit ? 1 : 0) + (okCost ? 1 : 0)'},
   'cases': [
     {'when': 'okCount == 6', 'flags': ['passed']},
     {'when': '!okErr', 'flags': ['overloaded']},
     {'when': '!okIds', 'flags': ['guessable']},
     {'when': 'servers < 2', 'flags': ['spof']},
     {'when': 'true', 'vars': {'A': 'A', 'p95': 'p95', 'errPct': 'errPct', 'cost': 'cost', 'found': 'found', 'ok': 'okCount', 'botNow': 'round(botAllowed)'}}],
   'widgets': [
     {'type': 'checks', 'label': '@checks', 'items': [
       {'label': '@cP95', 'ok': '=okP95', 'why': '@cP95Why'},
       {'label': '@cErr', 'ok': '=okErr', 'why': '@cErrWhy'},
       {'label': '@cN1', 'ok': '=okN1', 'why': "=servers < 2 ? '@cN1WhyOne' : '@cN1Why'"},
       {'label': '@cIds', 'ok': '=okIds', 'why': '@cIdsWhy'},
       {'label': '@cLimit', 'ok': '=okLimit', 'why': "=rateLimit == 0 ? '@cLimitWhy0' : (rateLimit < lab ? '@cLimitWhyLow' : '@cLimitWhyHigh')"},
       {'label': '@cCost', 'ok': '=okCost', 'why': '@cCostWhy'}]},
     {'type': 'metrics', 'items': [
       {'label': '@rpsM', 'value': '=A', 'format': 'int', 'tone': 'info'},
       {'label': '@p95M', 'value': '=p95', 'format': 'ms', 'tone': "=okP95 ? 'ok' : 'bad'"},
       {'label': '@errM', 'value': '=errPct', 'format': 'pct', 'tone': "=okErr ? 'ok' : 'bad'"},
       {'label': '@costM', 'value': '=cost', 'format': 'int', 'tone': "=okCost ? 'ok' : 'bad'"},
       {'label': '@foundM', 'value': '=found', 'format': 'int', 'tone': "=found > 0 ? 'bad' : 'ok'"}]},
     {'type': 'flow', 'label': '@flowLabel', 'steps': [
       {'label': '@fUsers', 'sub': '@fUsersSub', 'tone': 'info'},
       {'label': '@fLimit', 'sub': "=rateLimit > 0 ? '@fLimitOn' : '@fOff'", 'tone': "=okLimit ? 'ok' : 'bad'"},
       {'label': '@fApps', 'sub': "=servers >= 2 ? '@fAppsLb' : '@fAppsOne'", 'tone': "=uApp >= 100 ? 'bad' : (okN1 ? 'ok' : 'warn')"},
       {'label': 'Cache', 'sub': "=cache ? '@fCacheOn' : '@fOff'", 'tone': "=cache ? 'ok' : 'dim'"},
       {'label': '@fDb', 'sub': "=replica ? '@fDbRep' : '@fDbOne'", 'tone': "=uPrim >= 100 || uRep >= 100 ? 'bad' : 'ok'"},
       {'label': '@fClicks', 'sub': "=isSync ? '@fClicksSync' : '@fClicksQueue'", 'tone': "=isSync ? 'bad' : 'ok'"}]},
     {'type': 'chart', 'label': '@chartLabel', 'kind': 'bar', 'labels': ['@uAppL', '@uPrimL', '@uRepL'],
      'series': [{'label': '@series', 'values': '=[uApp, uPrim, uRep]'}], 'threshold': {'value': 80, 'label': '@uLine'}},
     {'type': 'terminal', 'label': '@terminal', 'lines': [
       "=servers >= 2 ? '@tServersOk' : '@tServersOne'",
       "=cache ? '@tCacheOn' : '@tCacheOff'",
       "=replica ? '@tReplicaOn' : '@tReplicaOff'",
       "=okIds ? '@tIdsOk' : '@tIdsSeq'",
       "=rateLimit == 0 ? '@tLimitOff' : (okLimit ? '@tLimitOk' : (rateLimit < lab ? '@tLimitLow' : '@tLimitHigh'))",
       "=isSync ? '@tClicksSync' : '@tClicksQueue'"]}]},
  kind='mission')

def loc7(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Missão: um encurtador de links para o dia da matrícula', 'Mission: a link shortener for enrollment day'),
  'subtitle': T('Um link viral, um robô curioso, o laboratório inteiro num IP só e um orçamento de escola pública', 'A viral link, a nosy bot, the whole computer lab on one IP and a public-school budget'),
  'mission': T('A escola criou um encurtador de links (lnk.example/…) para tudo: matrícula, boletos, formulários. No dia da matrícula, o link do formulário vai para todos os grupos de pais e o pico chega a 3.000 redirecionamentos por segundo, mais 5 links novos por segundo. Um robô tenta adivinhar links a partir de um só IP, 400 vezes por segundo. E a escola inteira sai pela mesma internet: no pico, 600 pedidos por minuto vêm do IP da escola. O estagiário entregou o desenho mais barato possível: 1 servidor, sem cache, sem réplica, ids em sequência (1, 2, 3…), sem limite por IP e cada clique gravado no banco na hora do redirecionamento. Conserte até os seis critérios ficarem verdes. Cada servidor aguenta 800 pedidos/s; cada banco, 900 operações/s; o cache acerta 75% das leituras.',
               'The school created a link shortener (lnk.example/…) for everything: enrollment, payment slips, forms. On enrollment day, the form link goes to every parents’ group and the peak reaches 3,000 redirects per second, plus 5 new links per second. A bot tries to guess links from a single IP, 400 times per second. And the whole school shares one internet connection: at peak, 600 requests per minute come from the school’s IP. The intern delivered the cheapest possible design: 1 server, no cache, no replica, sequential ids (1, 2, 3…), no per-IP limit and every click written to the database during the redirect. Fix it until all six criteria turn green. Each server handles 800 requests/s; each database, 900 operations/s; the cache hits 75% of reads.'),
  'coach': {'ui': T('Mexa nos controles; os critérios mudam enquanto você ajusta. Cada um que falhar diz o porquê. Os números são simulados.', 'Move the controls; the criteria change as you adjust. Each failing one says why. The numbers are simulated.'),
            'cmd': T('Edite o comando e rode. Cada critério que falhar diz o porquê. Tudo o que você precisa apareceu nas lições 2 a 6.', 'Edit the command and run it. Each failing criterion says why. Everything you need showed up in lessons 2 to 6.')},
  'why': {'simples': T('Você desenhou um sistema grande de verdade, peça por peça. Vários servidores atrás de um balanceador, com um de folga, para o link não cair se um deles queimar. Um cache na frente do banco, porque quase todo mundo pede o mesmo link. Uma réplica para dividir as leituras que o cache não pega. Ids sorteados, para ninguém achar o formulário dos outros chutando números. Um limite por IP que barra o robô sem barrar a escola. E os cliques contados por uma fila, fora do caminho de quem só quer ser redirecionado.\nRepare que nenhuma peça resolveu tudo sozinha: cache sem réplica ainda deixa o banco lento, mais servidores não salvam um banco afogado em cliques, e o desenho mais barato foi o que mais custou em erros.',
                       'You designed a real large system, piece by piece. Several servers behind a load balancer, with one spare, so the link doesn’t go down if one burns out. A cache in front of the database, because almost everybody asks for the same link. A replica to split the reads the cache misses. Random ids, so nobody finds other people’s forms by guessing numbers. A per-IP limit that stops the bot without blocking the school. And clicks counted through a queue, out of the way of people who just want to be redirected.\nNotice that no piece solved everything on its own: a cache without a replica still leaves the database slow, more servers don’t save a database drowning in clicks, and the cheapest design was the one that cost the most in errors.'),
          'dev': T('A estimativa de guardanapo que guia o desenho: 3.055 pedidos/s ÷ 800 por servidor = 3,8 servidores no limite; mas a latência explode perto de 100% de uso (p95 ≈ 3 × tempo de serviço ÷ (1 − uso)), então mire uns 65%: 3.055 ÷ (800 × 0,65) ≈ 5,9 → 6 servidores, e confira o N+1 (5 × 800 = 4.000 ≥ 3.055). No banco: sem fila, cada clique é um UPDATE, 3.000 escritas/s num banco de 900; com a fila juntando cliques em lotes de 100, viram 30.\nIds: 7 caracteres de [a-zA-Z0-9] dão 62^7 ≈ 3,5 trilhões de combinações; sorteie com um gerador criptográfico e trate colisão com uma restrição de unicidade (tenta de novo). Limite por IP: janela de um minuto com INCR e EXPIRE no Redis, respondendo 429 com Retry-After. E o redirecionamento: 302 (ou 307) não é guardado pelo navegador por padrão, então todo clique chega até você; 301 é permanente e pode ser guardado, e aí os próximos cliques nem passam pelo encurtador.',
                   'The back-of-the-envelope estimate that guides the design: 3,055 requests/s ÷ 800 per server = 3.8 servers at the limit; but latency explodes near 100% utilization (p95 ≈ 3 × service time ÷ (1 − utilization)), so aim for about 65%: 3,055 ÷ (800 × 0.65) ≈ 5.9 → 6 servers, and check N+1 (5 × 800 = 4,000 ≥ 3,055). In the database: without a queue, each click is an UPDATE, 3,000 writes/s on a 900-op database; with the queue batching clicks in groups of 100, they become 30.\nIds: 7 characters from [a-zA-Z0-9] give 62^7 ≈ 3.5 trillion combinations; draw them with a cryptographic generator and handle collisions with a uniqueness constraint (retry). Per-IP limit: a one-minute window with INCR and EXPIRE in Redis, answering 429 with Retry-After. And the redirect: 302 (or 307) isn’t stored by the browser by default, so every click reaches you; 301 is permanent and can be stored, and then later clicks don’t even pass through the shortener.'),
          'especialista': T('Para produção ainda faltam peças: o banco primário continua sendo um ponto único de falha (failover automático, réplica em outra zona), o cache precisa de proteção contra estouro quando o link viral expira (trava ou valor velho enquanto renova), e limite por IP sozinho é fraco contra quem usa muitos IPs, então combine com limite por link, desafio para tráfego suspeito e, para links privados, autenticação: id difícil de adivinhar não é controle de acesso.\nPense também em: CDN ou borda servindo o redirecionamento do link quente, pré-aquecimento antes de um evento conhecido (o dia da matrícula tem data), links com validade, contagem de cliques aproximada aceitável (a fila pode atrasar segundos), filtro de bots na contagem, e testes de carga com o perfil real do pico antes do dia. E registre o desenho com números: as premissas (taxa de acerto, capacidade por servidor) são exatamente o que muda quando o sistema cresce.',
                            'For production there are still missing pieces: the primary database is still a single point of failure (automatic failover, a replica in another zone), the cache needs stampede protection when the viral link expires (a lock or a stale value while refreshing), and a per-IP limit alone is weak against someone using many IPs, so combine it with per-link limits, challenges for suspicious traffic and, for private links, authentication: a hard-to-guess id isn’t access control.\nAlso think about: a CDN or edge serving the hot link’s redirect, pre-warming before a known event (enrollment day has a date), expiring links, approximate click counts being acceptable (the queue can lag by seconds), bot filtering in the counts, and load tests with the real peak profile before the day. And write the design down with numbers: the assumptions (hit rate, capacity per server) are exactly what changes as the system grows.')},
  'success': T('Missão cumprida! No pico da matrícula, {A} pedidos/s com p95 de {p95} ms e {errPct}% de erro, por R$ {cost} por mês. Perder um servidor não derruba o link, o robô não acha os formulários de ninguém, o laboratório da escola não é bloqueado e cada clique é contado sem atrasar ninguém. Pode mandar o link no grupo dos pais.',
               'Mission accomplished! At the enrollment peak, {A} requests/s with a p95 of {p95} ms and {errPct}% errors, for R$ {cost} a month. Losing a server doesn’t take the link down, the bot can’t find anyone’s forms, the school lab isn’t blocked and every click is counted without slowing anyone down. Go ahead and post the link in the parents’ group.'),
  'errors': {'belowMin.servers': T('Pelo menos 1 servidor.', 'At least 1 server.'), 'aboveMax.servers': T('Até 8 servidores nesta simulação.', 'Up to 8 servers in this simulation.'),
             'notBool.cache': T('Use sim ou nao.', 'Use yes or no.'), 'notBool.replica': T('Use sim ou nao.', 'Use yes or no.'),
             'notInEnum.ids': T('Use sequencial ou aleatorio.', 'Use sequential or random.'),
             'belowMin.rateLimit': T('O limite não fica negativo. 0 é sem limite (e é um dos problemas).', 'The limit can’t be negative. 0 means no limit (and that’s one of the problems).'),
             'aboveMax.rateLimit': T('Até 20.000 pedidos por minuto nesta simulação.', 'Up to 20,000 requests per minute in this simulation.'),
             'notInEnum.clicks': T('Use sincrono ou fila.', 'Use sync or queue.')},
  'controls': {'arg': T('Sistema', 'System'), 'servers': T('Servidores de aplicação', 'Application servers'), 'cache': T('Cache dos links', 'Link cache'),
               'replica': T('Réplica de leitura', 'Read replica'), 'ids': T('Como os ids são gerados', 'How ids are generated'),
               'rateLimit': T('Limite por IP (pedidos/min; 0 = sem limite)', 'Per-IP limit (requests/min; 0 = no limit)'), 'clicks': T('Contagem de cliques', 'Click counting')},
  'scene': {'label': T('O encurtador no dia da matrícula', 'The shortener on enrollment day'), 'empty': T('Rode para abrir a matrícula.', 'Run to open enrollment.'),
    'trackDone': T('Você concluiu a trilha Fundamentos de System design.', 'You completed the System design Foundations track.'),
    'checks': T('Critérios da missão', 'Mission criteria'),
    'cP95': T('p95 até 300 ms', 'p95 up to 300 ms'), 'cP95Why': T('p95 em {p95} ms (servidores, cache, banco e cliques somados)', 'p95 at {p95} ms (servers, cache, database and clicks added up)'),
    'cErr': T('No máximo 0,5% de erro', 'At most 0.5% errors'), 'cErrWhy': T('{errPct}% dos pedidos falham: alguma peça está acima de 100% de uso (veja o gráfico)', '{errPct}% of requests fail: some piece is above 100% utilization (see the chart)'),
    'cN1': T('Aguenta perder 1 servidor (N+1)', 'Survives losing 1 server (N+1)'),
    'cN1WhyOne': T('com um servidor só, a queda dele derruba o link', 'with a single server, its failure takes the link down'),
    'cN1Why': T('sem 1 servidor, sobram {n1Cap} pedidos/s para {A}', 'without 1 server, {n1Cap} requests/s are left for {A}'),
    'cIds': T('Links não podem ser adivinhados', 'Links can’t be guessed'), 'cIdsWhy': T('com ids em sequência, o robô acha uns {found} links por hora, inclusive formulários com dados de alunos', 'with sequential ids, the bot finds about {found} links an hour, including forms with student data'),
    'cLimit': T('Limite por IP barra o robô sem barrar a escola', 'Per-IP limit stops the bot without blocking the school'),
    'cLimitWhy0': T('sem limite, o robô faz 400 pedidos/s à vontade', 'with no limit, the bot makes 400 requests/s freely'),
    'cLimitWhyLow': T('{rateLimit}/min bloqueia o laboratório, que faz 600/min pelo IP da escola', '{rateLimit}/min blocks the lab, which makes 600/min through the school’s IP'),
    'cLimitWhyHigh': T('{rateLimit}/min ainda deixa o robô fazer {botNow} pedidos/s; fique entre 600 e 3.000', '{rateLimit}/min still lets the bot make {botNow} requests/s; stay between 600 and 3,000'),
    'cCost': T('Custo até R$ 3.500 por mês', 'Cost up to R$ 3,500 a month'), 'cCostWhy': T('R$ {cost} por mês', 'R$ {cost} a month'),
    'rpsM': T('pedidos/s no pico', 'requests/s at peak'), 'p95M': T('p95 do redirecionamento', 'redirect p95'), 'errM': T('pedidos com erro', 'failed requests'),
    'costM': T('custo por mês (R$, simulado)', 'cost per month (R$, simulated)'), 'foundM': T('links achados pelo robô por hora', 'links found by the bot per hour'),
    'flowLabel': T('O caminho de um clique (simulado)', 'The path of a click (simulated)'),
    'fUsers': T('Pais e alunos', 'Parents and students'), 'fUsersSub': T('{A} pedidos/s', '{A} requests/s'),
    'fLimit': T('Limite por IP', 'Per-IP limit'), 'fLimitOn': T('{rateLimit}/min', '{rateLimit}/min'), 'fOff': T('desligado', 'off'),
    'fApps': T('Aplicação', 'Application'), 'fAppsLb': T('balanceador + {servers} servidores', 'balancer + {servers} servers'), 'fAppsOne': T('1 servidor, sem balanceador', '1 server, no balancer'),
    'fCacheOn': T('acerta 75%', 'hits 75%'),
    'fDb': T('Banco', 'Database'), 'fDbRep': T('primário + réplica', 'primary + replica'), 'fDbOne': T('só o primário', 'primary only'),
    'fClicks': T('Cliques', 'Clicks'), 'fClicksSync': T('UPDATE a cada clique', 'UPDATE on every click'), 'fClicksQueue': T('fila, lotes de 100', 'queue, batches of 100'),
    'chartLabel': T('Uso de cada peça no pico (%)', 'Utilization of each piece at peak (%)'), 'series': T('uso', 'utilization'),
    'uAppL': T('servidores', 'servers'), 'uPrimL': T('primário', 'primary'), 'uRepL': T('réplica', 'replica'), 'uLine': T('80%: hora de crescer', '80%: time to grow'),
    'terminal': T('Revisão do desenho', 'Design review'),
    'tServersOk': T('+ {servers} servidores atrás de um balanceador com checagem de saúde', '+ {servers} servers behind a load balancer with health checks'),
    'tServersOne': T('! 1 servidor: ponto único de falha', '! 1 server: single point of failure'),
    'tCacheOn': T('+ cache dos links mais pedidos (75% de acerto)', '+ cache for the most requested links (75% hits)'),
    'tCacheOff': T('! sem cache: todo redirecionamento consulta o banco', '! no cache: every redirect queries the database'),
    'tReplicaOn': T('+ réplica de leitura dividindo o que o cache não pega', '+ read replica splitting what the cache misses'),
    'tReplicaOff': T('? só o primário: leituras e escritas no mesmo banco', '? primary only: reads and writes on the same database'),
    'tIdsOk': T('+ ids de 7 caracteres sorteados (62^7 ≈ 3,5 trilhões)', '+ random 7-character ids (62^7 ≈ 3.5 trillion)'),
    'tIdsSeq': T('! ids em sequência: lnk.example/1, /2, /3… qualquer um adivinha', '! sequential ids: lnk.example/1, /2, /3… anyone can guess'),
    'tLimitOff': T('! sem limite por IP', '! no per-IP limit'),
    'tLimitOk': T('+ limite de {rateLimit} pedidos/min por IP, com 429 e Retry-After', '+ limit of {rateLimit} requests/min per IP, with 429 and Retry-After'),
    'tLimitLow': T('! limite de {rateLimit}/min: a escola inteira leva 429', '! limit of {rateLimit}/min: the whole school gets 429'),
    'tLimitHigh': T('? limite de {rateLimit}/min: frouxo demais para o robô', '? limit of {rateLimit}/min: too loose for the bot'),
    'tClicksSync': T('! cada clique faz um UPDATE no banco antes de redirecionar', '! each click runs an UPDATE on the database before redirecting'),
    'tClicksQueue': T('+ cliques vão para uma fila; um worker grava em lotes', '+ clicks go to a queue; a worker writes them in batches')},
  'data': {},
  'recipe': {'steps': [
     T('Faça a folha de estimativa num papel ou planilha, com estas linhas: pico de pedidos/s (3.000 + 5 de criação + o que o robô passar); capacidade por servidor (800/s); servidores = pico ÷ (800 × 0,65), arredondado para cima; N+1 = (servidores − 1) × 800 ≥ pico?; escritas no banco com e sem lote (3.000 ou 3.000 ÷ 100); leituras que o cache não pega (25% de 3.000).',
       'Build the estimate sheet on paper or in a spreadsheet, with these rows: peak requests/s (3,000 + 5 for creation + whatever the bot gets through); capacity per server (800/s); servers = peak ÷ (800 × 0.65), rounded up; N+1 = (servers − 1) × 800 ≥ peak?; database writes with and without batching (3,000 or 3,000 ÷ 100); reads the cache misses (25% of 3,000).'),
     T('Gere ids como o encurtador faria e confira o tamanho do espaço de ids:\ndocker run --rm python:3.14-slim python -c "import secrets, string; a = string.ascii_letters + string.digits; print(\'\'.join(secrets.choice(a) for _ in range(7)))"\ndocker run --rm python:3.14-slim python -c "print(62**7)"',
       'Generate ids the way the shortener would and check the size of the id space:\ndocker run --rm python:3.14-slim python -c "import secrets, string; a = string.ascii_letters + string.digits; print(\'\'.join(secrets.choice(a) for _ in range(7)))"\ndocker run --rm python:3.14-slim python -c "print(62**7)"'),
     T('Teste um limite por IP de janela fixa no Redis:\ndocker run -d --name limite ' + REDIS_IMG + '\ndocker exec -it limite redis-cli\nDentro do redis-cli, rode algumas vezes:\nINCR limite:203.0.113.7\nEXPIRE limite:203.0.113.7 60 NX\nTTL limite:203.0.113.7\nO contador é o número de pedidos desse IP no minuto; acima do limite, a aplicação responde 429. O NX só põe a validade na primeira vez.',
       'Try a fixed-window per-IP limit in Redis:\ndocker run -d --name limite ' + REDIS_IMG + '\ndocker exec -it limite redis-cli\nInside redis-cli, run these a few times:\nINCR limite:203.0.113.7\nEXPIRE limite:203.0.113.7 60 NX\nTTL limite:203.0.113.7\nThe counter is this IP’s number of requests in the minute; above the limit, the app answers 429. NX only sets the expiry the first time.'),
     T('Saia com exit e limpe: docker rm -f limite', 'Leave with exit and clean up: docker rm -f limite')],
   'ok': T('a folha fecha em 6 servidores com N+1 e 30 escritas/s com a fila; o primeiro comando Python imprime um id de 7 letras e números diferente a cada vez e o segundo imprime 3521614606208; no Redis, INCR responde 1, 2, 3… e o TTL desce a partir de 60 até a chave sumir.',
           'the sheet comes out at 6 servers with N+1 and 30 writes/s with the queue; the first Python command prints a 7-character id of letters and digits that changes every time and the second prints 3521614606208; in Redis, INCR answers 1, 2, 3… and TTL counts down from 60 until the key disappears.')}}

t7 = {'pt': {'objectives': ['Combinar escala horizontal, balanceador, cache, réplica e fila num desenho só.', 'Fazer uma estimativa de capacidade com números.', 'Justificar cada peça com o problema que ela resolve e o que ela custa.'], 'minutes': 30,
  'activity': 'Em grupos, consertem o desenho e depois apresentem em 3 minutos, no quadro, o caminho de um clique: do celular do pai até o formulário, dizendo o número de cada etapa (pedidos/s, uso, custo). Bônus: cada grupo escolhe uma peça e conta o que aconteceria se ela caísse no meio do pico.',
  'discussion': ['Qual peça do desenho é o novo ponto único de falha?', 'Por que o desenho mais barato acabou sendo o mais caro?'],
  'misconceptions': ['"Mais servidores resolvem qualquer lentidão." Se o banco é o gargalo, servidores a mais só mandam mais pedidos para ele.', '"Id difícil de adivinhar protege dado privado." Ajuda contra curiosos; dado privado precisa de login e permissão.']},
 'en': {'objectives': ['Combine scaling out, load balancing, caching, replication and queues in a single design.', 'Build a capacity estimate with numbers.', 'Justify each piece by the problem it solves and what it costs.'], 'minutes': 30,
  'activity': 'In groups, fix the design and then present, in 3 minutes on the board, the path of one click: from a parent’s phone to the form, giving each step’s number (requests/s, utilization, cost). Bonus: each group picks a piece and tells what would happen if it failed mid-peak.',
  'discussion': ['Which piece of the design is the new single point of failure?', 'Why did the cheapest design end up being the most expensive?'],
  'misconceptions': ['"More servers fix any slowness." If the database is the bottleneck, extra servers just send it more requests.', '"A hard-to-guess id protects private data." It helps against the curious; private data needs login and permissions.']}}
write('07-missao-encurtador-de-links', s7, loc7('pt'), loc7('en'), t7)
print('ok: system-design/fundamentos (6 passos + missão)')
