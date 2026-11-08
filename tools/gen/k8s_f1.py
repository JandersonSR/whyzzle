"""Contêineres e Kubernetes · Fundamentos F1 · Do programa ao contêiner (6 lições + missão).
Gera content/conteineres-e-kubernetes/fundamentos/NN-slug/{step,pt,en,teacher}.json. Rode com python3."""
import sys, os, hashlib; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write as _write, flag, step

TOPIC, TRACK = 'conteineres-e-kubernetes', 'fundamentos'
def write(folder, s, pt, en, teacher): _write(TOPIC, TRACK, folder, s, pt, en, teacher)
def opt(id, pt, en): return {'id': id, 'pt': pt, 'en': en}
def loc(pt, en): return {'pt': pt, 'en': en}
SIM = ['simulado']

# ---------------------------------------------------------------- shared recipe snippets (real files, multi-line)
def server_js(pt):
  hello = 'Olá da marmitaria!' if pt else 'Hello from the lunchbox kitchen!'
  listen = 'ouvindo na porta 3000' if pt else 'listening on port 3000'
  return ('const express = require("express");\n'
          'const app = express();\n'
          f'app.get("/", (req, res) => res.send("{hello}\\n"));\n'
          f'app.listen(3000, () => console.log("{listen}"));')

def server_js_secret(pt):
  hello = 'Olá da marmitaria! Senha recebida: ' if pt else 'Hello from the lunchbox kitchen! Password received: '
  listen = 'ouvindo na porta 3000' if pt else 'listening on port 3000'
  return ('const express = require("express");\n'
          'const app = express();\n'
          'const hasPassword = Boolean(process.env.DB_PASSWORD);\n'
          f'app.get("/", (req, res) => res.send("{hello}" + hasPassword + "\\n"));\n'
          f'app.listen(3000, () => console.log("{listen}"));')

DOCKERFILE_L3 = ('FROM node:24-slim\n'
                 'WORKDIR /app\n'
                 'COPY package.json package-lock.json ./\n'
                 'RUN npm ci --omit=dev\n'
                 'COPY . .\n'
                 'CMD ["node", "server.js"]')
DOCKERIGNORE_L3 = 'node_modules\n.git'
KIND_YAML = ('kind: Cluster\n'
             'apiVersion: kind.x-k8s.io/v1alpha4\n'
             'nodes:\n'
             '- role: control-plane\n'
             '- role: worker\n'
             '- role: worker')
NPM_IN_DOCKER = 'docker run --rm -v "${PWD}:/app" -w /app node:24-slim sh -c "npm init -y && npm install express"'
NODE_MAJOR = 'node -p "process.versions.node.split(\'.\')[0]"'

def fake_digest(seed): return hashlib.sha256(seed.encode()).hexdigest()

# ================================================================== 1 · processo × contêiner × VM
APPS = [('api-pedidos', 'Node 24'), ('painel-antigo', 'Node 18'), ('relatorio', 'Python 3.12')]
def app_name(i):
  n, rt = APPS[i % 3]
  return (n if i < 3 else f'{n}-{i // 3 + 1}') + f' · {rt}'
PODS_OK = [{'name': app_name(i), 'status': 'Running'} for i in range(20)]
PODS_CLASH = [{'name': app_name(i), 'status': 'Error' if i % 3 == 1 else 'Running'} for i in range(20)]
PODS_WAIT = [{'name': app_name(i), 'status': 'Pending'} for i in range(20)]

s1 = step('k8s-processo-conteiner-vm', 1, TRACK, 15, ['conteiner', 'vm', 'processo', 'kernel', 'isolamento'], [], SIM,
  loc('hospedar', 'host'),
  {'name': 'text', 'required': False, 'default': loc('servidor-da-cozinha', 'kitchen-server'), 'ui': 'text'},
  [flag('isolation', 'isolamento', 'isolation', 'enum',
        options=[opt('container', 'conteiner', 'container'), opt('process', 'processo', 'process'), opt('vm', 'vm', 'vm')],
        default='container', ui='select'),
   flag('apps', 'apps', 'apps', 'int', min=1, max=20, default=3, ui='slider')],
  {'options': ['ownKernel', 'sharedKernel', 'noIsolation'], 'answer': 'sharedKernel'}, 'versionClash',
  {'live': True,
   'consts': {'hostMB': 16384, 'hostOsMB': 2048, 'appMB': 200,
              'overheadMB': {'process': 0, 'container': 10, 'vm': 1024},
              'startSec': {'process': 0.1, 'container': 1, 'vm': 40},
              'podsOk': PODS_OK, 'podsClash': PODS_CLASH, 'podsWait': PODS_WAIT},
   'compute': {
     'isProc': "isolation == 'process'",
     'isVm': "isolation == 'vm'",
     'ovh': 'lookup(overheadMB, isolation, 0)',
     'perApp': 'appMB + ovh',
     'maxApps': 'floor((hostMB - hostOsMB) / perApp)',
     'fits': 'apps <= maxApps',
     'upApps': 'min(apps, maxApps)',
     'kernels': 'isVm ? upApps + 1 : 1',
     'usedMB': 'hostOsMB + upApps * perApp',
     'startS': 'lookup(startSec, isolation, 0)',
     'clash': 'isProc && apps >= 2',
     'brokenApps': 'clash ? floor((apps + 1) / 3) : 0',
     'running': 'upApps - brokenApps',
     'pods': 'slice(concat(slice(clash ? podsClash : podsOk, 0, upApps), slice(podsWait, upApps, apps)), 0, 12)'},
   'cases': [
     {'when': 'clash', 'flags': ['versionClash']},
     {'when': '!fits', 'flags': ['noRoom']},
     {'when': 'true', 'vars': {'kernels': 'kernels', 'usedMB': 'usedMB', 'brokenApps': 'brokenApps', 'maxApps': 'maxApps', 'running': 'running'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@kernelsM', 'value': '=kernels', 'format': 'int', 'tone': "=isVm ? 'warn' : 'ok'"},
       {'label': '@ramM', 'value': '=usedMB', 'format': 'int', 'tone': "=fits ? 'ok' : 'bad'"},
       {'label': '@bootM', 'value': '=startS', 'tone': "=isVm ? 'warn' : 'ok'"},
       {'label': '@brokenM', 'value': '=brokenApps', 'format': 'int', 'tone': "=brokenApps > 0 ? 'bad' : 'dim'"}]},
     {'type': 'cluster', 'label': '@clusterLabel', 'nodes': [
       {'name': '=text', 'status': "=isVm ? '@stVm' : (isProc ? '@stProc' : '@stCtr')",
        'tone': "=fits ? (clash ? 'warn' : 'ok') : 'bad'", 'pods': '=pods'}]},
     {'type': 'terminal', 'when': '=isProc', 'label': '@termProc', 'lines': [
       '$ ' + NODE_MAJOR, '24', "=clash ? '@clashLine' : '@soloLine'"]},
     {'type': 'terminal', 'when': "=isolation == 'container'", 'label': '@termCtr', 'lines': [
       '$ docker run --rm node:18-alpine ' + NODE_MAJOR, '18',
       '$ docker run --rm node:24-alpine ' + NODE_MAJOR, '24']},
     {'type': 'terminal', 'when': '=isVm', 'label': '@termVm', 'lines': ['@vmLine1', '@vmLine2']},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['@colAspect', '@colProc', '@colCtr', '@colVm'],
      'rows': [['@rKernel', '@no', '@no', '@yes'], ['@rFiles', '@no', '@yes', '@yes'],
               ['@rBoot', '@bootProc', '@bootCtr', '@bootVm'], ['@rRam', '0 MB', '10 MB', '@ramVm']],
      'caption': '@tableCap'},
     {'type': 'note', 'when': '=clash', 'tone': 'bad', 'text': '@clashNote'},
     {'type': 'note', 'when': '=!fits', 'tone': 'bad', 'text': '@roomNote'},
     {'type': 'note', 'when': "=isolation == 'container'", 'tone': 'ok', 'text': '@ctrNote'},
     {'type': 'note', 'when': '=isVm && fits', 'tone': 'info', 'text': '@vmNote'}]})

def loc1(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Processo × contêiner × VM', 'Process vs container vs VM'),
  'subtitle': T('Três cozinheiros, uma cozinha só: dividir o pote de sal, ganhar um food truck ou construir um restaurante?', 'Three cooks, one kitchen: share the salt jar, get a food truck each, or build a whole restaurant?'),
  'mission': T('A Marmitaria da Tia Cida tem três programas para rodar num servidor de 16 GB: a api-pedidos (Node 24), o painel-antigo (só funciona no Node 18) e o relatório (Python 3.12). Compare rodar tudo como processo comum, em contêineres e em máquinas virtuais. Olhe quantos kernels ficam ligados, quanta memória vai embora e quem quebra.',
               'Aunt Cida’s Lunchbox Co. has three programs to run on a 16 GB server: api-pedidos (Node 24), painel-antigo (only works on Node 18) and relatorio (Python 3.12). Compare running everything as plain processes, in containers and in virtual machines. Watch how many kernels are running, how much memory goes away and who breaks.'),
  'predict': {'question': T('com contêineres, cada app leva um sistema operacional inteiro, com kernel próprio?', 'with containers, does each app carry a whole operating system, with its own kernel?'),
    'options': {'ownKernel': T('Sim: cada contêiner liga o próprio kernel', 'Yes: each container boots its own kernel'),
                'sharedKernel': T('Não: todos usam o kernel da máquina, cada um com seus arquivos', 'No: they all use the machine’s kernel, each with its own files'),
                'noIsolation': T('Não, e por isso não existe isolamento nenhum', 'No, and that’s why there’s no isolation at all')}},
  'feedback': {'right': T('isso! Contêiner é um processo comum, só que fechado numa caixa: enxerga só os próprios arquivos, processos e rede. O kernel é o da máquina, um só para todo mundo. Por isso sobe em segundos e gasta pouca memória.',
                          'right! A container is a regular process, just boxed in: it only sees its own files, processes and network. The kernel is the machine’s, one for everybody. That’s why it starts in seconds and uses little memory.'),
               'wrong': T('olhe o contador de kernels: com contêineres ele fica em 1, não importa quantos apps. Cada contêiner tem seus próprios arquivos (o Node 18 de um, o Node 24 do outro), mas todos usam o mesmo kernel. Kernel próprio é coisa de VM.',
                          'look at the kernel counter: with containers it stays at 1, however many apps. Each container has its own files (Node 18 in one, Node 24 in the other), but they all use the same kernel. Your own kernel is a VM thing.'),
               'skipped': T('sem palpite? Rode e olhe o contador de kernels. Depois troque para vm e compare.', 'no guess? Run it and look at the kernel counter. Then switch to vm and compare.')},
  'coach': {'ui': T('palpite anotado. Rode com contêiner, depois troque para vm. Compare "kernels ligados".', 'guess noted. Run with container, then switch to vm. Compare "kernels running".'),
            'cmd': T('palpite anotado. Rode hospedar e depois hospedar --isolamento vm. Compare "kernels ligados".', 'guess noted. Run host and then host --isolation vm. Compare "kernels running".')},
  'tryNext': {'ui': T('Agora escolha vm com 20 apps: veja quantas máquinas virtuais cabem nos 16 GB.', 'Now pick vm with 20 apps: see how many virtual machines fit in 16 GB.'),
              'cmd': T('Rode hospedar --isolamento vm --apps 20 e veja quantas VMs cabem nos 16 GB.', 'Run host --isolation vm --apps 20 and see how many VMs fit in 16 GB.')},
  'why': {'simples': T('Pense na cozinha da Tia Cida. Processo comum é todo mundo cozinhando na mesma bancada, com o mesmo pote de sal: se um cozinheiro precisa de sal grosso e o outro de sal fino, dá briga. Foi o que aconteceu com o painel-antigo, que queria o Node 18 numa máquina que só tem o 24.\nContêiner é dar a cada cozinheiro um food truck fechado, com os temperos dele lá dentro. Os trucks ficam estacionados na mesma rua e usam a mesma rede de água e luz: essa rua é o kernel. VM é construir um restaurante inteiro, com encanamento próprio, para cada cozinheiro: isola muito, mas custa caro e demora para abrir.',
                       'Think of Aunt Cida’s kitchen. Plain processes are everyone cooking at the same counter, with the same salt jar: if one cook needs coarse salt and another needs fine salt, there’s a fight. That’s what happened to painel-antigo, which wanted Node 18 on a machine that only has 24.\nA container is giving each cook a closed food truck, with their own spices inside. The trucks are parked on the same street and share the same water and power lines: that street is the kernel. A VM is building a whole restaurant, with its own plumbing, for each cook: lots of isolation, but expensive and slow to open.'),
          'dev': T('Um contêiner é um processo do Linux com isolamento: namespaces fazem ele enxergar só os próprios processos, rede, pontos de montagem e hostname, e cgroups limitam CPU e memória. Os arquivos que ele vê vêm de uma imagem, então cada um pode ter o seu Node. Não há sistema para dar boot, por isso sobe rápido e gasta pouco.\nA VM emula hardware em cima de um hypervisor e roda um sistema operacional inteiro, com kernel próprio. No Windows e no Mac, o Docker Desktop mantém uma VM Linux leve por baixo, e os contêineres rodam dentro dela: é por isso que imagem Linux funciona nessas máquinas.',
                   'A container is a Linux process with isolation: namespaces make it see only its own processes, network, mount points and hostname, and cgroups limit CPU and memory. The files it sees come from an image, so each one can have its own Node. There’s no system to boot, so it starts fast and uses little.\nA VM emulates hardware on top of a hypervisor and runs a whole operating system, with its own kernel. On Windows and Mac, Docker Desktop keeps a lightweight Linux VM underneath, and containers run inside it: that’s why Linux images work on those machines.'),
          'especialista': T('O preço do kernel compartilhado é a fronteira de segurança. Uma falha no kernel ou uma configuração frouxa (contêiner --privileged, montar /var/run/docker.sock lá dentro, rodar como root sem user namespaces) pode deixar um contêiner mexer na máquina. Para código que você não confia, use isolamento mais forte: sandboxes como gVisor, microVMs (Firecracker, Kata Containers) ou VMs mesmo.\nO kernel compartilhado também explica por que uma imagem Linux não roda nativamente num kernel Windows e por que uma imagem arm64 precisa de emulação numa máquina amd64. O que deixa as peças intercambiáveis é a OCI (Open Container Initiative): a especificação de runtime descreve como executar o contêiner, e o runc, implementação de referência, é o que o containerd usa por baixo do Docker e de muitos clusters Kubernetes.',
                            'The price of a shared kernel is the security boundary. A kernel bug or a loose setting (a --privileged container, mounting /var/run/docker.sock inside, running as root without user namespaces) can let a container touch the machine. For code you don’t trust, use stronger isolation: sandboxes like gVisor, microVMs (Firecracker, Kata Containers) or plain VMs.\nThe shared kernel also explains why a Linux image doesn’t run natively on a Windows kernel and why an arm64 image needs emulation on an amd64 machine. What makes the pieces interchangeable is the OCI (Open Container Initiative): the runtime spec describes how to run a container, and runc, the reference implementation, is what containerd uses under Docker and many Kubernetes clusters.')},
  'break': {'mission': {'ui': T('hora de quebrar: escolha "processo" e rode os 3 apps sem isolamento nenhum.', 'time to break it: pick "process" and run the 3 apps with no isolation at all.'),
                        'cmd': T('hora de quebrar: rode hospedar --isolamento processo', 'time to break it: run host --isolation process')},
            'success': T('Quebrou: sem isolamento, {brokenApps} app(s) que precisam do Node 18 não subiram, porque a máquina compartilhada só tem o Node 24 no PATH. Mesmo código, mesma máquina: faltou cada um levar a própria cozinha.',
                         'Broken: with no isolation, {brokenApps} app(s) that need Node 18 didn’t start, because the shared machine only has Node 24 on the PATH. Same code, same machine: what was missing was each one bringing its own kitchen.'),
            'calm': T('{running} app(s) no ar com {kernels} kernel(s) e {usedMB} MB de memória usados. Para quebrar, rode tudo como processo comum, sem isolamento.',
                      '{running} app(s) up with {kernels} kernel(s) and {usedMB} MB of memory used. To break it, run everything as a plain process, with no isolation.')},
  'hints': {'ui': T(['Escolha o isolamento e quantos apps quer hospedar; a cena muda sozinha.', 'Sem isolamento, os apps dividem o mesmo Node instalado na máquina.', 'Escolha "processo" com 3 apps.'],
                    ['Pick the isolation and how many apps to host; the scene updates by itself.', 'With no isolation, the apps share the same Node installed on the machine.', 'Pick "process" with 3 apps.']),
            'cmd': T(['O nome do servidor vai entre aspas; --isolamento e --apps são opcionais.', '--isolamento aceita conteiner, processo ou vm.', 'hospedar --isolamento processo'],
                     ['The server name goes in quotes; --isolation and --apps are optional.', '--isolation takes container, process or vm.', 'host --isolation process'])},
  'errors': {'notInEnum.isolation': T('Use conteiner, processo ou vm.', 'Use container, process or vm.'),
             'belowMin.apps': T('Pelo menos 1 app, senão o servidor fica só esquentando a sala.', 'At least 1 app, or the server just heats the room.'),
             'aboveMax.apps': T('Até 20 apps nesta simulação: a Tia Cida tem um servidor só.', 'Up to 20 apps in this simulation: Aunt Cida has a single server.')},
  'controls': {'arg': T('Nome do servidor', 'Server name'), 'isolation': T('Isolamento', 'Isolation'), 'apps': T('Quantos apps', 'How many apps')},
  'scene': {'label': T('Um servidor, três programas', 'One server, three programs'), 'empty': T('Rode para ligar o servidor.', 'Run to switch the server on.'),
    'kernelsM': T('kernels ligados (host + VMs)', 'kernels running (host + VMs)'), 'ramM': T('memória usada (MB, de 16.384)', 'memory used (MB, out of 16,384)'),
    'bootM': T('segundos para subir cada app', 'seconds to start each app'), 'brokenM': T('apps que não sobem', 'apps that won’t start'),
    'clusterLabel': T('O servidor e os apps (simulado)', 'The server and its apps (simulated)'),
    'stVm': T('{running} VMs, {kernels} kernels (host + {running})', '{running} VMs, {kernels} kernels (host + {running})'),
    'stProc': T('1 kernel (o do host), tudo na mesma bancada', '1 kernel (the host’s), everything on one counter'),
    'stCtr': T('1 kernel, cada app no seu contêiner', '1 kernel, each app in its own container'),
    'termProc': T('Terminal do servidor (sem isolamento)', 'Server terminal (no isolation)'),
    'termCtr': T('Terminal: cada contêiner traz o próprio Node', 'Terminal: each container brings its own Node'),
    'termVm': T('Com máquinas virtuais', 'With virtual machines'),
    'clashLine': T('! painel-antigo precisa do Node 18, mas a máquina tem o 24 no PATH', '! painel-antigo needs Node 18, but the machine has 24 on the PATH'),
    'soloLine': T('+ um app só: nenhuma briga de versões (por enquanto)', '+ a single app: no version fight (for now)'),
    'vmLine1': T('~ cada VM dá boot no próprio sistema: {kernels} kernels (1 do host + {running} das VMs) para {running} app(s) no ar', '~ each VM boots its own system: {kernels} kernels (1 from the host + {running} from the VMs) for {running} app(s) up'),
    'vmLine2': T('? 1.224 MB por app, dos quais 1.024 MB são o sistema convidado', '? 1,224 MB per app, of which 1,024 MB is the guest system'),
    'tableLabel': T('As três opções lado a lado', 'The three options side by side'),
    'colAspect': T('aspecto', 'aspect'), 'colProc': T('processo', 'process'), 'colCtr': T('contêiner', 'container'), 'colVm': T('VM', 'VM'),
    'rKernel': T('kernel próprio', 'own kernel'), 'rFiles': T('arquivos e versões separados', 'separate files and versions'),
    'rBoot': T('tempo para subir', 'time to start'), 'rRam': T('memória extra por app', 'extra memory per app'),
    'yes': T('sim', 'yes'), 'no': T('não', 'no'),
    'bootProc': T('0,1 s', '0.1 s'), 'bootCtr': T('~1 s', '~1 s'), 'bootVm': T('~40 s', '~40 s'), 'ramVm': T('1.024 MB', '1,024 MB'),
    'tableCap': T('Números da simulação, para comparar ordens de grandeza; na vida real variam com a máquina e a imagem.', 'Simulation numbers, to compare orders of magnitude; in real life they depend on the machine and the image.'),
    'clashNote': T('{brokenApps} app(s) com Node 18 não sobem: na bancada compartilhada só existe um Node no PATH, e ele é o 24. É o famoso “na minha máquina funciona”.', '{brokenApps} app(s) on Node 18 won’t start: on the shared counter there’s only one Node on the PATH, and it’s 24. The classic “works on my machine”.'),
    'roomNote': T('Não cabe: cada VM carrega um sistema inteiro além do app. Nesta máquina cabem {maxApps} VMs; as outras ficaram esperando.', 'It doesn’t fit: each VM carries a whole system on top of the app. This machine fits {maxApps} VMs; the rest are left waiting.'),
    'ctrNote': T('{running} app(s), cada um com o seu Node, dividindo 1 kernel (o do host). Cada contêiner custou só 10 MB a mais que o app sozinho.', '{running} app(s), each with its own Node, sharing 1 kernel (the host’s). Each container cost only 10 MB more than the bare app.'),
    'vmNote': T('Isolamento máximo, mas cada app paga um sistema inteiro: {kernels} kernels ligados (o do host mais um por VM) e uns 40 s para subir cada um.', 'Maximum isolation, but each app pays for a whole system: {kernels} kernels running (the host’s plus one per VM) and about 40 s to start each one.')},
  'data': {},
  'recipe': {'steps': [
     T('Instale o Docker (Docker Desktop no Windows ou Mac, Docker Engine no Linux) e rode:\ndocker run --rm alpine:3.24 cat /etc/os-release\nAparece Alpine Linux, seja qual for o sistema da sua máquina: os arquivos que o contêiner vê são os da imagem.',
       'Install Docker (Docker Desktop on Windows or Mac, Docker Engine on Linux) and run:\ndocker run --rm alpine:3.24 cat /etc/os-release\nIt shows Alpine Linux, whatever your machine runs: the files the container sees are the image’s.'),
     T('Compare o kernel de dentro e de fora:\ndocker run --rm alpine:3.24 uname -r\nNo Linux, rode também uname -r no seu terminal: os dois são iguais. No Docker Desktop (Windows ou Mac) aparece o kernel da VM Linux leve que ele mantém por baixo, e não o do seu sistema.',
       'Compare the kernel inside and outside:\ndocker run --rm alpine:3.24 uname -r\nOn Linux, also run uname -r in your terminal: both match. On Docker Desktop (Windows or Mac) you see the kernel of the lightweight Linux VM it keeps underneath, not your system’s.'),
     T('Suba um contêiner que só dorme e olhe o processo de dentro e de fora:\ndocker run -d --name dorminhoco alpine:3.24 sleep 300\ndocker exec dorminhoco ps\ndocker top dorminhoco',
       'Start a container that just sleeps and look at the process from inside and outside:\ndocker run -d --name dorminhoco alpine:3.24 sleep 300\ndocker exec dorminhoco ps\ndocker top dorminhoco'),
     T('Limpe a bancada: docker rm -f dorminhoco', 'Clean the counter: docker rm -f dorminhoco')],
   'ok': T('dentro do contêiner, o ps mostra o sleep 300 como PID 1; o docker top mostra o mesmo processo visto pela máquina; e o uname -r dá o mesmo kernel dentro e fora (no Linux). É um processo isolado, não um computador novo.',
           'inside the container, ps shows sleep 300 as PID 1; docker top shows the same process as the machine sees it; and uname -r gives the same kernel inside and out (on Linux). It’s an isolated process, not a new computer.')}}

t1 = {'pt': {'objectives': ['Diferenciar processo comum, contêiner e máquina virtual.', 'Entender que contêineres compartilham o kernel da máquina.', 'Comparar custo e isolamento das três opções.'], 'minutes': 15,
  'activity': 'Teatro da cozinha: três alunos são cozinheiros e precisam de temperos diferentes. Rodada 1: um pote de sal para todos (processo). Rodada 2: cada um ganha uma caixa de temperos própria, mas a mesma mesa (contêiner). Rodada 3: cada um vai para uma sala separada, e leva um tempo para "abrir" a sala (VM). Anotem o que deu briga e o que custou mais.',
  'discussion': ['Onde você já ouviu “na minha máquina funciona”? O que estava diferente?', 'Quando vale pagar o preço de uma VM em vez de um contêiner?'],
  'misconceptions': ['"Contêiner é uma VM pequena." Contêiner é um processo isolado que usa o kernel da máquina; VM tem kernel e sistema próprios.', '"Contêiner é tão isolado quanto VM." O kernel compartilhado é uma fronteira mais fina; para código não confiável, use isolamento mais forte.']},
 'en': {'objectives': ['Tell a plain process, a container and a virtual machine apart.', 'Understand that containers share the machine’s kernel.', 'Compare cost and isolation across the three options.'], 'minutes': 15,
  'activity': 'Kitchen play: three students are cooks who need different spices. Round 1: one salt jar for everyone (process). Round 2: each gets their own spice box, but the same table (container). Round 3: each goes to a separate room, which takes a while to "open" (VM). Write down what caused fights and what cost more.',
  'discussion': ['Where have you heard “works on my machine”? What was different?', 'When is it worth paying for a VM instead of a container?'],
  'misconceptions': ['"A container is a small VM." A container is an isolated process using the machine’s kernel; a VM has its own kernel and system.', '"A container is as isolated as a VM." The shared kernel is a thinner boundary; for untrusted code, use stronger isolation.']}}
write('01-processo-conteiner-vm', s1, loc1('pt'), loc1('en'), t1)

# ================================================================== 2 · imagem e camadas
LAYER_IDS = ['3f8a1c2b9d04', 'a71e5d0c6b13', '5c2d9e8f7a60', 'e94b0a3d1f27', '0d6c4b8e2a95']
DIGESTS2 = {f'{c}-{k}': fake_digest(f'api-pedidos:1.1 {c} {k}') for c in ('code', 'deps', 'base') for k in ('same', 'separate')}
s2 = step('k8s-imagem-e-camadas', 2, TRACK, 15, ['imagem', 'camadas', 'oci', 'docker-pull', 'cache'], ['k8s-processo-conteiner-vm'], SIM,
  loc('puxar', 'pull'),
  {'name': 'text', 'required': False, 'default': loc('localhost:5000/api-pedidos:1.1', 'localhost:5000/api-pedidos:1.1'), 'ui': 'text'},
  [flag('changed', 'mudou', 'changed', 'enum',
        options=[opt('code', 'codigo', 'code'), opt('deps', 'dependencias', 'deps'), opt('base', 'base', 'base')], default='code', ui='select'),
   flag('cleanup', 'limpeza', 'cleanup', 'enum',
        options=[opt('same', 'mesmo-run', 'same-run'), opt('separate', 'run-separado', 'separate-run')], default='same', ui='select'),
   flag('apps', 'apps', 'apps', 'int', min=1, max=10, default=3, ui='slider')],
  {'options': ['all', 'code', 'zero'], 'answer': 'code'}, 'ghostBytes',
  {'live': True,
   'consts': {'baseMB': 75, 'runtimeMB': 45, 'depsMB': 60, 'toolsMB': 180, 'codeMB': 2,
              'iFrom': 'FROM node:24-slim', 'iDepsGood': 'RUN install && npm ci && purge',
              'iDepsBad': 'RUN install && npm ci', 'iRm': 'RUN purge', 'iCode': 'COPY . .',
              'ids': LAYER_IDS, 'digests': DIGESTS2},
   'compute': {
     'bad': "cleanup == 'separate'",
     'depsLayer': 'bad ? depsMB + toolsMB : depsMB',
     'imageMB': 'baseMB + runtimeMB + depsLayer + codeMB',
     'pullMB': "changed == 'code' ? codeMB : (changed == 'deps' ? depsLayer + codeMB : imageMB)",
     'layersN': 'bad ? 5 : 4',
     'newLayers': "changed == 'code' ? 1 : (changed == 'deps' ? (bad ? 3 : 2) : layersN)",
     'diskMB': 'baseMB + runtimeMB + apps * (depsLayer + codeMB)',
     'naiveMB': 'apps * imageMB',
     'savedMB': 'naiveMB - diskMB',
     'stBase': "changed == 'base' ? 'Pull complete' : 'Already exists'",
     'stDeps': "changed == 'code' ? 'Already exists' : 'Pull complete'",
     'tBase': "changed == 'base' ? 'info' : 'dim'",
     'tDeps': "changed == 'code' ? 'dim' : 'info'",
     'mark': "changed == 'base' ? '+' : '~'",
     'markD': "changed == 'code' ? '~' : '+'",
     'rows': "concat([[1, '@lOs', iFrom, baseMB + ' MB', stBase]], [[2, '@lRt', iFrom, runtimeMB + ' MB', stBase]], "
             "[[3, '@lDeps', bad ? iDepsBad : iDepsGood, depsLayer + ' MB', stDeps]], bad ? [[4, '@lRm', iRm, '0 MB', stDeps]] : [], "
             "[[layersN, '@lCode', iCode, codeMB + ' MB', 'Pull complete']])",
     'tones': "concat([tBase, tBase], [bad ? 'bad' : tDeps], bad ? ['warn'] : [], ['info'])",
     'pullLines': "concat(['$ docker pull ' + text, '1.1: Pulling from api-pedidos'], [mark + ids[0] + ': ' + stBase, mark + ids[1] + ': ' + stBase, markD + ids[2] + ': ' + stDeps], "
                  "bad ? [markD + ids[3] + ': ' + stDeps] : [], ['+' + ids[4] + ': Pull complete', "
                  "'Digest: sha256:' + lookup(digests, changed + '-' + cleanup, ''), 'Status: Downloaded newer image for ' + text])"},
   'cases': [
     {'when': 'bad', 'flags': ['ghostBytes']},
     {'when': "changed == 'base'", 'flags': ['fullPull']},
     {'when': 'true', 'vars': {'pullMB': 'pullMB', 'imageMB': 'imageMB', 'newLayers': 'newLayers', 'diskMB': 'diskMB', 'savedMB': 'savedMB'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@pullM', 'value': '=pullMB', 'format': 'int', 'tone': "=pullMB > 100 ? 'warn' : 'ok'"},
       {'label': '@imageM', 'value': '=imageMB', 'format': 'int', 'tone': "=bad ? 'bad' : 'ok'"},
       {'label': '@diskM', 'value': '=diskMB', 'format': 'int', 'tone': 'info'},
       {'label': '@savedM', 'value': '=savedMB', 'format': 'int', 'tone': "=savedMB > 0 ? 'ok' : 'dim'"}]},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['#', '@colLayer', '@colInstr', '@colSize', '@colPull'],
      'rows': '=rows', 'tones': '=tones', 'caption': '@tableCap'},
     {'type': 'terminal', 'label': '@termLabel', 'lines': '=pullLines'},
     {'type': 'note', 'when': '=bad', 'tone': 'bad', 'text': '@ghostNote'},
     {'type': 'note', 'when': "=changed == 'base'", 'tone': 'warn', 'text': '@fullNote'},
     {'type': 'note', 'when': "=!bad && changed != 'base'", 'tone': 'ok', 'text': '@shareNote'}]})

def loc2(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Imagem e camadas', 'Images and layers'),
  'subtitle': T('Uma imagem é uma lasanha: camada por camada, e não dá para tirar a cebola do meio colando um bilhete em cima', 'An image is a lasagna: layer by layer, and you can’t remove the onion from the middle by sticking a note on top'),
  'mission': T('A api-pedidos da Tia Cida saiu na versão 1.1, e três servidores precisam puxá-la do registro. A imagem tem camadas: o sistema, o Node, as dependências (que precisam de ferramentas de compilação, depois removidas) e o código. Descubra o que viaja no docker pull quando muda o código, as dependências ou a base, e o que acontece quando as ferramentas são removidas num RUN separado.',
               'Aunt Cida’s api-pedidos shipped version 1.1, and three servers need to pull it from the registry. The image has layers: the system, Node, the dependencies (which need build tools, removed afterwards) and the code. Find out what travels in docker pull when the code, the dependencies or the base change, and what happens when the tools are removed in a separate RUN.'),
  'predict': {'question': T('a versão 1.1 só mudou o código (2 MB). Quanto um servidor que já tem a 1.0 baixa no docker pull?', 'version 1.1 only changed the code (2 MB). How much does a server that already has 1.0 download in docker pull?'),
    'options': {'all': T('A imagem inteira de novo, uns 182 MB', 'The whole image again, about 182 MB'),
                'code': T('Só a camada do código, uns 2 MB', 'Only the code layer, about 2 MB'),
                'zero': T('Nada: o Docker copia só os arquivos alterados depois', 'Nothing: Docker copies only changed files later')}},
  'feedback': {'right': T('isso! Camadas são identificadas pelo conteúdo. O servidor já tem o sistema, o Node e as dependências; só a camada do código é nova, e só ela viaja.',
                          'right! Layers are identified by their content. The server already has the system, Node and the dependencies; only the code layer is new, and only it travels.'),
               'wrong': T('olhe a coluna "no pull": as camadas que o servidor já tem aparecem como Already exists. Só a camada do código, que mudou, vem como Pull complete: uns 2 MB.',
                          'look at the "on pull" column: the layers the server already has show as Already exists. Only the code layer, which changed, comes as Pull complete: about 2 MB.'),
               'skipped': T('sem palpite? Rode e olhe quais linhas do terminal dizem Already exists.', 'no guess? Run it and see which terminal lines say Already exists.')},
  'coach': {'ui': T('palpite anotado. Rode com "mudou: código" e depois troque para "base". Compare "baixado no pull".', 'guess noted. Run with "changed: code", then switch to "base". Compare "downloaded on pull".'),
            'cmd': T('palpite anotado. Rode puxar e depois puxar --mudou base. Compare "baixado no pull".', 'guess noted. Run pull and then pull --changed base. Compare "downloaded on pull".')},
  'tryNext': {'ui': T('Troque "mudou" para base: trocar a imagem base faz o Docker reconstruir todas as camadas de cima, e o pull vira a imagem inteira.', 'Switch "changed" to base: changing the base image makes Docker rebuild every layer above it, and the pull becomes the whole image.'),
              'cmd': T('Rode puxar --mudou base e veja o pull virar a imagem inteira.', 'Run pull --changed base and watch the pull become the whole image.')},
  'why': {'simples': T('Uma imagem é como uma lasanha congelada: massa (o sistema), molho (o Node), recheio (as dependências) e queijo por cima (o seu código). Cada camada fica pronta e lacrada. Quando só o queijo muda, quem já tem a lasanha recebe só a camada nova de queijo.\nAgora a pegadinha: se você põe no topo um bilhete dizendo “ignore a cebola lá do meio”, a cebola continua lá, pesando na marmita. Para tirar de verdade, ela nunca pode ter entrado naquela camada.',
                       'An image is like a frozen lasagna: pasta (the system), sauce (Node), filling (the dependencies) and cheese on top (your code). Each layer is finished and sealed. When only the cheese changes, whoever already has the lasagna gets just the new cheese layer.\nNow the catch: if you put a note on top saying “ignore the onion in the middle”, the onion is still there, weighing down the lunchbox. To really remove it, it must never have gone into that layer.'),
          'dev': T('Cada instrução que mexe em arquivos (RUN, COPY, ADD) gera uma camada: um pacote só com as diferenças em relação à camada de baixo. As camadas são somente leitura e identificadas pelo hash do conteúdo, então imagens com a mesma base guardam essas camadas uma vez só no disco, e o docker pull baixa só as que faltam. Ao rodar, o contêiner ganha uma camada fina gravável por cima (copy-on-write), que some quando o contêiner é removido.\nApagar um arquivo numa camada nova só registra que ele foi apagado: ele some da vista, mas os bytes continuam na camada de baixo e contam no tamanho da imagem. Por isso instalar, usar e remover ferramentas precisa acontecer no mesmo RUN, ou num estágio separado de um multi-stage build.',
                   'Each instruction that touches files (RUN, COPY, ADD) creates a layer: a package with only the differences from the layer below. Layers are read-only and identified by a hash of their content, so images sharing a base store those layers only once on disk, and docker pull downloads only the missing ones. When it runs, the container gets a thin writable layer on top (copy-on-write), which goes away when the container is removed.\nDeleting a file in a new layer only records that it was deleted: it disappears from view, but the bytes stay in the layer below and count toward the image size. That’s why installing, using and removing tools must happen in the same RUN, or in a separate stage of a multi-stage build.'),
          'especialista': T('No formato OCI, uma imagem é um manifesto que aponta, por digest, para um config (JSON com variáveis de ambiente, usuário, comando e histórico) e para a lista ordenada de camadas, da base para o topo. Para várias arquiteturas existe um índice que aponta para um manifesto por plataforma. Tudo é endereçado por conteúdo (sha256): deduplicação e verificação de integridade vêm de brinde.\nCamadas reconstruídas costumam ganhar digests novos mesmo com o mesmo conteúdo lógico, porque datas e metadados dos arquivos entram no pacote; builds reprodutíveis (por exemplo, fixando SOURCE_DATE_EPOCH) atacam isso. Ordene as camadas da que menos muda para a que mais muda, e use docker image history (ou uma ferramenta como o dive) para caçar camadas gordas.',
                            'In the OCI format, an image is a manifest that points, by digest, to a config (JSON with environment variables, user, command and history) and to the ordered list of layers, from base to top. For several architectures there’s an index pointing to one manifest per platform. Everything is content-addressed (sha256): deduplication and integrity checks come for free.\nRebuilt layers often get new digests even with the same logical content, because file dates and metadata go into the package; reproducible builds (for example, pinning SOURCE_DATE_EPOCH) tackle that. Order layers from least to most frequently changing, and use docker image history (or a tool like dive) to hunt fat layers.')},
  'break': {'mission': {'ui': T('hora de quebrar: escolha a limpeza "run-separado".', 'time to break it: pick the "separate-run" cleanup.'),
                        'cmd': T('hora de quebrar: rode puxar --limpeza run-separado', 'time to break it: run pull --cleanup separate-run')},
            'success': T('Quebrou: a imagem ficou com {imageMB} MB. O apt-get purge num RUN separado só escondeu as ferramentas de compilação: os bytes continuam guardados na camada das dependências e viajam em todo pull que precisar dela.',
                         'Broken: the image ended up at {imageMB} MB. The apt-get purge in a separate RUN only hid the build tools: the bytes are still stored in the dependencies layer and travel in every pull that needs it.'),
            'calm': T('Imagem de {imageMB} MB; neste pull vieram {pullMB} MB em {newLayers} camada(s). Para quebrar, remova as ferramentas de compilação num RUN separado.',
                      'A {imageMB} MB image; this pull brought {pullMB} MB in {newLayers} layer(s). To break it, remove the build tools in a separate RUN.')},
  'hints': {'ui': T(['Escolha o que mudou e como as ferramentas foram limpas; a tabela mostra cada camada.', 'Apagar numa camada nova não diminui a camada de baixo.', 'Escolha a limpeza "run-separado".'],
                    ['Pick what changed and how the tools were cleaned up; the table shows each layer.', 'Deleting in a new layer doesn’t shrink the layer below.', 'Pick the "separate-run" cleanup.']),
            'cmd': T(['A imagem vai entre aspas; --mudou, --limpeza e --apps são opcionais.', '--limpeza aceita mesmo-run ou run-separado.', 'puxar --limpeza run-separado'],
                     ['The image goes in quotes; --changed, --cleanup and --apps are optional.', '--cleanup takes same-run or separate-run.', 'pull --cleanup separate-run'])},
  'errors': {'notInEnum.changed': T('Use codigo, dependencias ou base.', 'Use code, deps or base.'),
             'notInEnum.cleanup': T('Use mesmo-run ou run-separado.', 'Use same-run or separate-run.'),
             'belowMin.apps': T('Pelo menos 1 servidor com a imagem.', 'At least 1 server with the image.'),
             'aboveMax.apps': T('Até 10 servidores nesta simulação.', 'Up to 10 servers in this simulation.')},
  'controls': {'arg': T('Imagem', 'Image'), 'changed': T('O que mudou da 1.0 para a 1.1', 'What changed from 1.0 to 1.1'),
               'cleanup': T('Onde as ferramentas de compilação são removidas', 'Where the build tools are removed'), 'apps': T('Servidores com a imagem', 'Servers with the image')},
  'scene': {'label': T('A lasanha em camadas', 'The layered lasagna'), 'empty': T('Rode para puxar a imagem.', 'Run to pull the image.'),
    'pullM': T('baixado no pull da 1.1 (MB)', 'downloaded on the 1.1 pull (MB)'), 'imageM': T('tamanho da imagem (MB)', 'image size (MB)'),
    'diskM': T('disco usado nos servidores (MB)', 'disk used across servers (MB)'), 'savedM': T('MB poupados por compartilhar camadas', 'MB saved by sharing layers'),
    'tableLabel': T('Camadas da api-pedidos:1.1, da base para o topo', 'api-pedidos:1.1 layers, from base to top'),
    'colLayer': T('camada', 'layer'), 'colInstr': T('instrução', 'instruction'), 'colSize': T('tamanho', 'size'), 'colPull': T('no pull', 'on pull'),
    'lOs': T('sistema (Debian slim)', 'system (Debian slim)'), 'lRt': T('Node.js 24', 'Node.js 24'),
    'lDeps': T('dependências', 'dependencies'), 'lRm': T('remoção das ferramentas', 'tool removal'), 'lCode': T('seu código', 'your code'),
    'tableCap': T('Tamanhos simulados. A base node:24-slim, na vida real, tem algumas camadas; aqui viraram duas para caber na tela.', 'Simulated sizes. The real node:24-slim base has a few layers; here they’re two to fit the screen.'),
    'termLabel': T('Terminal do servidor (simulado)', 'Server terminal (simulated)'),
    'ghostNote': T('A camada das dependências guarda os 180 MB das ferramentas de compilação, e a camada de cima só marca os arquivos como apagados. Resultado: {imageMB} MB, quando dava para ter 182.', 'The dependencies layer keeps the 180 MB of build tools, and the layer above only marks the files as deleted. Result: {imageMB} MB, when it could have been 182.'),
    'fullNote': T('Trocou a base: tudo que vem em cima foi reconstruído e ganhou camadas novas. Vieram {pullMB} MB, a imagem inteira.', 'The base changed: everything on top was rebuilt and got new layers. {pullMB} MB came down, the whole image.'),
    'shareNote': T('Vieram só {pullMB} MB. E os {apps} servidores guardam o sistema e o Node uma vez só: {savedMB} MB poupados de disco.', 'Only {pullMB} MB came down. And the {apps} servers store the system and Node only once: {savedMB} MB of disk saved.')},
  'data': {},
  'recipe': {'steps': [
     T('Puxe uma imagem e veja as camadas dela, com a instrução que criou cada uma e o tamanho:\ndocker pull node:24-slim\ndocker image history node:24-slim',
       'Pull an image and look at its layers, with the instruction that created each one and its size:\ndocker pull node:24-slim\ndocker image history node:24-slim'),
     T('Numa pasta vazia, crie Dockerfile.gordo:\nFROM alpine:3.24\nRUN dd if=/dev/urandom of=/lixo bs=1048576 count=50\nRUN rm /lixo',
       'In an empty folder, create Dockerfile.gordo:\nFROM alpine:3.24\nRUN dd if=/dev/urandom of=/lixo bs=1048576 count=50\nRUN rm /lixo'),
     T('Na mesma pasta, crie Dockerfile.magro, que cria e apaga no mesmo RUN:\nFROM alpine:3.24\nRUN dd if=/dev/urandom of=/lixo bs=1048576 count=50 && rm /lixo',
       'In the same folder, create Dockerfile.magro, which creates and deletes in the same RUN:\nFROM alpine:3.24\nRUN dd if=/dev/urandom of=/lixo bs=1048576 count=50 && rm /lixo'),
     T('Construa as duas e compare:\ndocker build -t gordo -f Dockerfile.gordo .\ndocker build -t magro -f Dockerfile.magro .\ndocker image ls gordo\ndocker image ls magro\ndocker image history gordo',
       'Build both and compare:\ndocker build -t gordo -f Dockerfile.gordo .\ndocker build -t magro -f Dockerfile.magro .\ndocker image ls gordo\ndocker image ls magro\ndocker image history gordo')],
   'ok': T('a gordo aparece uns 50 MB maior que a magro, e o history da gordo mostra uma camada de cerca de 52 MB (os 50 MiB do dd, contados em MB decimais) com uma camada de 0 B (ou quase 0) do rm em cima: apagar depois não devolveu o espaço.',
           'gordo shows up about 50 MB bigger than magro, and gordo’s history shows a layer of about 52 MB (the dd’s 50 MiB, counted in decimal MB) with a 0 B (or almost 0) rm layer on top: deleting later didn’t give the space back.')}}

t2 = {'pt': {'objectives': ['Explicar que uma imagem é uma pilha de camadas somente leitura.', 'Prever o que viaja num docker pull.', 'Entender por que apagar numa camada nova não diminui a imagem.'], 'minutes': 15,
  'activity': 'Lasanha de papel: cada grupo empilha folhas coloridas (sistema, Node, dependências, código). Para "atualizar", só pode trocar a folha de cima. Depois tentem "remover" uma folha do meio só escrevendo um bilhete na de cima: a pilha ficou mais leve?',
  'discussion': ['Por que faz sentido o código ser a última camada?', 'O que acontece com o disco de um servidor que roda dez apps com a mesma base?'],
  'misconceptions': ['"RUN rm diminui a imagem." Ele só esconde o arquivo; os bytes continuam na camada anterior.', '"Todo pull baixa a imagem inteira." Só viajam as camadas que o destino ainda não tem.']},
 'en': {'objectives': ['Explain that an image is a stack of read-only layers.', 'Predict what travels in a docker pull.', 'Understand why deleting in a new layer doesn’t shrink the image.'], 'minutes': 15,
  'activity': 'Paper lasagna: each group stacks colored sheets (system, Node, dependencies, code). To "update", they may only swap the top sheet. Then try to "remove" a sheet from the middle by writing a note on the top one: did the stack get lighter?',
  'discussion': ['Why does it make sense for the code to be the last layer?', 'What happens to the disk of a server running ten apps on the same base?'],
  'misconceptions': ['"RUN rm shrinks the image." It only hides the file; the bytes stay in the earlier layer.', '"Every pull downloads the whole image." Only the layers the target doesn’t have yet travel.']}}
write('02-imagem-e-camadas', s2, loc2('pt'), loc2('en'), t2)

# ================================================================== 3 · Dockerfile
L3_STEPS = {
  'depsFirst': [('FROM node:24-slim', 'from'), ('WORKDIR /app', 'work'), ('COPY package.json package-lock.json ./', 'pkg'), ('RUN npm ci --omit=dev', 'npm'), ('COPY . .', 'copy')],
  'copyAll': [('FROM node:24-slim', 'from'), ('WORKDIR /app', 'work'), ('COPY . .', 'copy'), ('RUN npm ci --omit=dev', 'npm')]}
def l3_build(order, changed, ignore):
  ctx, ctx_s, copy_t = (2, 0.1, 1.0) if ignore else (380, 4.0, 3.0)
  steps = L3_STEPS[order]; n = len(steps)
  invalid = False; rows, tones, lines = [], [], []
  lines.append(f'=> [internal] load build context   {ctx_s:.1f}s')
  lines.append(f'=> => transferring context: {ctx}MB')
  total, reran = ctx_s, 0
  for i, (instr, kind) in enumerate(steps, 1):
    if kind == 'from':
      rows.append([i, instr, '@stBase', 0]); tones.append('dim'); lines.append(f'~=> [{i}/{n}] FROM docker.io/library/node:24-slim'); continue
    if kind == 'pkg' and changed == 'deps': invalid = True
    if kind == 'copy' and changed != 'nothing': invalid = True
    if invalid and kind != 'work':
      t = {'pkg': 0.2, 'npm': 84.0, 'copy': copy_t}[kind]
      total += t; reran += 1
      rows.append([i, instr, '@stRan', t])
      bust = kind == 'npm' and order == 'copyAll' and changed == 'code'
      tones.append('bad' if bust else ('warn' if kind == 'npm' else 'info'))
      lines.append(('?' if kind == 'npm' else '') + f'=> [{i}/{n}] {instr}   {t:.1f}s')
    else:
      rows.append([i, instr, '@stCached', 0]); tones.append('dim'); lines.append(f'~=> CACHED [{i}/{n}] {instr}   0.0s')
  rows.append(['', 'CMD ["node", "server.js"]', '@stMeta', 0]); tones.append('neutral')
  export = 1.0 if reran else 0.0
  total += export
  lines.append(('' if reran else '~') + f'=> exporting to image   {export:.1f}s')
  return {'rows': rows, 'tones': tones, 'lines': lines, 'secs': round(total, 1), 'reran': reran, 'ctx': ctx}
L3_TABLE = {f'{o}-{c}-{"y" if g else "n"}': l3_build(o, c, g) for o in L3_STEPS for c in ('code', 'deps', 'nothing') for g in (True, False)}

s3 = step('k8s-dockerfile', 3, TRACK, 20, ['dockerfile', 'build', 'cache', 'dockerignore'], ['k8s-imagem-e-camadas'], SIM,
  loc('construir', 'build'),
  {'name': 'text', 'required': False, 'default': loc('api-pedidos:1.0', 'api-pedidos:1.0'), 'ui': 'text'},
  [flag('order', 'ordem', 'order', 'enum',
        options=[opt('depsFirst', 'deps-primeiro', 'deps-first'), opt('copyAll', 'copia-tudo', 'copy-all')], default='depsFirst', ui='select'),
   flag('changed', 'mudou', 'changed', 'enum',
        options=[opt('code', 'codigo', 'code'), opt('deps', 'dependencias', 'deps'), opt('nothing', 'nada', 'nothing')], default='code', ui='select'),
   flag('ignore', 'dockerignore', 'dockerignore', 'bool', default=True, ui='switch')],
  {'options': ['full', 'fast', 'zero'], 'answer': 'fast'}, 'cacheBusted',
  {'live': True,
   'consts': {'builds': L3_TABLE, 'npmS': 84},
   'compute': {
     'b': "lookup(builds, order + '-' + changed + '-' + (ignore ? 'y' : 'n'), null)",
     'secs': 'b.secs', 'reran': 'b.reran', 'ctxMB': 'b.ctx',
     'buildLines': "concat(['$ docker build -t ' + text + ' .'], b.lines)",
     'busted': "order == 'copyAll' && changed == 'code'"},
   'cases': [
     {'when': 'busted', 'flags': ['cacheBusted']},
     {'when': '!ignore', 'flags': ['fatContext']},
     {'when': 'true', 'vars': {'secs': 'round(secs)', 'reran': 'reran', 'ctxMB': 'ctxMB'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@secsM', 'value': '=secs', 'tone': "=secs > 30 ? 'bad' : 'ok'"},
       {'label': '@reranM', 'value': '=reran', 'format': 'int', 'tone': "=busted ? 'bad' : 'info'"},
       {'label': '@ctxM', 'value': '=ctxMB', 'format': 'int', 'tone': "=ignore ? 'ok' : 'warn'"}]},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['#', '@colInstr', '@colStatus', '@colTime'], 'rows': '=b.rows', 'tones': '=b.tones', 'caption': '@tableCap'},
     {'type': 'terminal', 'label': '@termLabel', 'lines': '=buildLines'},
     {'type': 'note', 'when': '=busted', 'tone': 'bad', 'text': '@bustNote'},
     {'type': 'note', 'when': "=!ignore && order == 'depsFirst'", 'tone': 'warn', 'text': '@ctxNote'},
     {'type': 'note', 'when': "=!ignore && order == 'copyAll'", 'tone': 'warn', 'text': '@ctxNoteAll'},
     {'type': 'note', 'when': "=!busted && ignore && changed == 'deps'", 'tone': 'info', 'text': '@depsNote'},
     {'type': 'note', 'when': "=!busted && ignore && changed != 'deps'", 'tone': 'ok', 'text': '@okNote'}]})

def loc3(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Dockerfile', 'Dockerfile'),
  'subtitle': T('A ficha da receita: primeiro o feijão que demora, por último o tempero do dia', 'The recipe card: the slow beans first, today’s seasoning last'),
  'mission': T('A api-pedidos tem um Dockerfile de seis linhas. Instalar as dependências (npm ci) leva 84 segundos; copiar o código, 1. Mude o código, as dependências ou nada, troque a ordem das linhas e ligue ou desligue o .dockerignore. Descubra quantos passos o Docker reaproveita do cache e quanto tempo leva cada build.',
               'api-pedidos has a six-line Dockerfile. Installing dependencies (npm ci) takes 84 seconds; copying the code, 1. Change the code, the dependencies or nothing, swap the order of the lines and turn the .dockerignore on or off. Find out how many steps Docker reuses from cache and how long each build takes.'),
  'predict': {'question': T('na ordem certa (dependências primeiro), você mudou uma linha do server.js. Quanto tempo leva o novo build?', 'in the right order (dependencies first), you changed one line of server.js. How long does the new build take?'),
    'options': {'full': T('Uns 86 s: o build inteiro de novo', 'About 86 s: the whole build again'),
                'fast': T('Uns 2 s: só o COPY do código roda de novo', 'About 2 s: only the code COPY runs again'),
                'zero': T('0 s: o Docker nem precisa rodar nada', '0 s: Docker doesn’t need to run anything')}},
  'feedback': {'right': T('isso! O COPY package.json package-lock.json ./ não mudou, então o RUN npm ci também fica em CACHED. Só o COPY . . roda de novo, porque o server.js mudou.',
                          'right! COPY package.json package-lock.json ./ didn’t change, so RUN npm ci stays CACHED too. Only COPY . . runs again, because server.js changed.'),
               'wrong': T('olhe a tabela: WORKDIR, a cópia do package.json e o npm ci aparecem como CACHED. Só o COPY . . roda, e o build leva uns 2 segundos.',
                          'look at the table: WORKDIR, the package.json copy and npm ci show as CACHED. Only COPY . . runs, and the build takes about 2 seconds.'),
               'skipped': T('sem palpite? Rode e conte as linhas CACHED no terminal.', 'no guess? Run it and count the CACHED lines in the terminal.')},
  'coach': {'ui': T('palpite anotado. Rode com a ordem deps-primeiro e depois copia-tudo. Compare "segundos de build".', 'guess noted. Run with deps-first, then copy-all. Compare "build seconds".'),
            'cmd': T('palpite anotado. Rode construir e depois construir --ordem copia-tudo. Compare "segundos de build".', 'guess noted. Run build and then build --order copy-all. Compare "build seconds".')},
  'tryNext': {'ui': T('Agora mude as dependências na ordem certa (aí sim o npm ci precisa rodar) e depois desligue o .dockerignore para ver o contexto inchar.', 'Now change the dependencies in the right order (then npm ci really has to run) and then turn off the .dockerignore to see the context swell.'),
              'cmd': T('Rode construir --mudou dependencias (aí sim o npm ci precisa rodar) e depois construir --dockerignore nao para ver o contexto inchar.', 'Run build --changed deps (then npm ci really has to run) and then build --dockerignore no to see the context swell.')},
  'why': {'simples': T('O Dockerfile é a ficha da receita da marmita, lida de cima para baixo, e o Docker guarda o resultado de cada passo. Se um passo não mudou e nada antes dele mudou, ele reaproveita o que já está pronto: é o cache.\nRegra de ouro da cozinha: o que demora e muda pouco vem primeiro (cozinhar o feijão é instalar as dependências); o que muda toda hora vem por último (o tempero do dia é o seu código). Se você mistura o tempero antes de cozinhar o feijão, cada troca de tempero obriga a cozinhar o feijão inteiro de novo.',
                       'The Dockerfile is the lunchbox recipe card, read top to bottom, and Docker keeps the result of each step. If a step didn’t change and nothing before it changed, it reuses what’s already done: that’s the cache.\nGolden kitchen rule: what’s slow and rarely changes goes first (cooking the beans is installing dependencies); what changes all the time goes last (today’s seasoning is your code). If you mix in the seasoning before cooking the beans, every seasoning change forces you to cook all the beans again.'),
          'dev': T('As linhas: FROM escolhe a base; WORKDIR define a pasta de trabalho; COPY traz arquivos do contexto; RUN executa um comando e grava o resultado numa camada; CMD diz o que rodar quando o contêiner sobe. O cache vale por instrução: um RUN é invalidado quando o texto do comando muda; COPY e ADD, quando os arquivos copiados mudam (conteúdo ou propriedades, como permissões). Depois que uma camada é invalidada, todas as seguintes também são.\nDaí o padrão para Node: COPY package.json package-lock.json ./, depois RUN npm ci --omit=dev, depois COPY . .: as dependências só reinstalam quando o lock muda. O .dockerignore tira do contexto o que não deve ir para o builder (node_modules, .git, .env): o build fica mais rápido e você não leva lixo nem segredos para dentro. Prefira o CMD em formato JSON, ["node", "server.js"], para o processo receber os sinais do sistema diretamente.',
                   'The lines: FROM picks the base; WORKDIR sets the working folder; COPY brings files from the context; RUN executes a command and stores the result in a layer; CMD says what to run when the container starts. The cache works per instruction: a RUN is invalidated when the command text changes; COPY and ADD, when the copied files change (content or properties such as permissions). Once a layer is invalidated, all following ones are too.\nHence the Node pattern: COPY package.json package-lock.json ./, then RUN npm ci --omit=dev, then COPY . .: dependencies only reinstall when the lock file changes. The .dockerignore keeps out of the context what shouldn’t go to the builder (node_modules, .git, .env): the build gets faster and you don’t carry junk or secrets inside. Prefer CMD in JSON form, ["node", "server.js"], so the process gets system signals directly.'),
          'especialista': T('Com o BuildKit, o builder padrão do Docker atual, dá para ir além: cache mounts (RUN --mount=type=cache,target=/root/.npm npm ci) guardam o cache do npm entre builds mesmo quando a camada é refeita; secret mounts (RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci) usam um token sem gravá-lo na imagem; multi-stage builds separam o estágio que compila do estágio que roda.\nEm CI, o cache local some a cada máquina nova: exporte e importe o cache (--cache-to e --cache-from do docker buildx, guardando no registro ou no cache do GitHub Actions). E, para builds repetíveis, fixe a base por digest (FROM node:24-slim@sha256:…) com uma ferramenta como Renovate ou Dependabot abrindo PRs de atualização.',
                            'With BuildKit, the default builder in current Docker, you can go further: cache mounts (RUN --mount=type=cache,target=/root/.npm npm ci) keep npm’s cache between builds even when the layer is rebuilt; secret mounts (RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci) use a token without writing it into the image; multi-stage builds separate the stage that compiles from the stage that runs.\nIn CI, the local cache disappears with every fresh machine: export and import the cache (docker buildx --cache-to and --cache-from, stored in the registry or in the GitHub Actions cache). And, for repeatable builds, pin the base by digest (FROM node:24-slim@sha256:…) with a tool like Renovate or Dependabot opening update PRs.')},
  'break': {'mission': {'ui': T('hora de quebrar: troque a ordem para copia-tudo, mudando só o código.', 'time to break it: switch the order to copy-all, changing only the code.'),
                        'cmd': T('hora de quebrar: rode construir --ordem copia-tudo', 'time to break it: run build --order copy-all')},
            'success': T('Quebrou: com o COPY . . antes do npm ci, mudar uma linha do código fez {reran} passos rodarem de novo e o build levou {secs} s, quase tudo reinstalando dependências que nem mudaram.',
                         'Broken: with COPY . . before npm ci, changing one line of code made {reran} steps run again and the build took {secs} s, almost all of it reinstalling dependencies that didn’t even change.'),
            'calm': T('Build em {secs} s, com {reran} passo(s) refeito(s). Para quebrar, copie tudo antes de instalar as dependências.',
                      'Build in {secs} s, with {reran} step(s) redone. To break it, copy everything before installing the dependencies.')},
  'hints': {'ui': T(['Escolha a ordem, o que mudou e se há .dockerignore; a tabela marca o que veio do cache.', 'Se o COPY . . vem antes do npm ci, qualquer mudança no código invalida o npm ci.', 'Escolha a ordem copia-tudo, mudando só o código.'],
                    ['Pick the order, what changed and whether there’s a .dockerignore; the table marks what came from cache.', 'If COPY . . comes before npm ci, any code change invalidates npm ci.', 'Pick the copy-all order, changing only the code.']),
            'cmd': T(['A tag vai entre aspas; --ordem, --mudou e --dockerignore são opcionais.', '--ordem aceita deps-primeiro ou copia-tudo.', 'construir --ordem copia-tudo'],
                     ['The tag goes in quotes; --order, --changed and --dockerignore are optional.', '--order takes deps-first or copy-all.', 'build --order copy-all'])},
  'errors': {'notInEnum.order': T('Use deps-primeiro ou copia-tudo.', 'Use deps-first or copy-all.'),
             'notInEnum.changed': T('Use codigo, dependencias ou nada.', 'Use code, deps or nothing.'),
             'notBool.ignore': T('Use sim ou nao.', 'Use yes or no.')},
  'controls': {'arg': T('Tag da imagem', 'Image tag'), 'order': T('Ordem das linhas', 'Line order'), 'changed': T('O que mudou desde o último build', 'What changed since the last build'), 'ignore': T('Tem .dockerignore?', 'Has a .dockerignore?')},
  'scene': {'label': T('O build da api-pedidos', 'The api-pedidos build'), 'empty': T('Rode para construir a imagem.', 'Run to build the image.'),
    'secsM': T('segundos de build', 'build seconds'), 'reranM': T('passos refeitos', 'steps redone'), 'ctxM': T('contexto enviado ao builder (MB)', 'context sent to the builder (MB)'),
    'tableLabel': T('Dockerfile, linha a linha', 'Dockerfile, line by line'), 'colInstr': T('instrução', 'instruction'), 'colStatus': T('neste build', 'in this build'), 'colTime': T('segundos', 'seconds'),
    'stBase': T('base já baixada', 'base already pulled'), 'stCached': T('CACHED: reaproveitado', 'CACHED: reused'), 'stRan': T('rodou de novo', 'ran again'), 'stMeta': T('só metadado', 'metadata only'),
    'tableCap': T('Tempos da simulação. O primeiro build, sem cache, levaria uns 86 s.', 'Simulated times. The first build, with no cache, would take about 86 s.'),
    'termLabel': T('Saída do docker build (simulada)', 'docker build output (simulated)'),
    'bustNote': T('O COPY . . vem antes do npm ci: mudar uma linha do server.js invalidou o cache e o npm ci rodou de novo por 84 s, para instalar exatamente as mesmas dependências.', 'COPY . . comes before npm ci: changing one line of server.js invalidated the cache and npm ci ran again for 84 s, to install exactly the same dependencies.'),
    'ctxNote': T('Sem .dockerignore, {ctxMB} MB (node_modules e .git) viajam até o builder a cada build, e o COPY . . leva o node_modules da sua máquina para dentro da imagem, por cima do que o npm ci instalou.', 'Without .dockerignore, {ctxMB} MB (node_modules and .git) travel to the builder on every build, and COPY . . carries your machine’s node_modules into the image, on top of what npm ci installed.'),
    'ctxNoteAll': T('Sem .dockerignore, {ctxMB} MB (node_modules e .git) viajam até o builder a cada build, e o COPY . . leva o node_modules da sua máquina para dentro da imagem. Como o npm ci vem depois, ele troca o node_modules, mas os bytes copiados continuam guardados na camada do COPY.', 'Without .dockerignore, {ctxMB} MB (node_modules and .git) travel to the builder on every build, and COPY . . carries your machine’s node_modules into the image. Since npm ci comes after, it replaces node_modules, but the copied bytes stay stored in the COPY layer.'),
    'depsNote': T('Mudou o package-lock.json: aí o npm ci precisa rodar mesmo. O cache acerta quando você muda dependência, não quando muda o código.', 'package-lock.json changed: now npm ci really has to run. The cache pays off when you change code, not dependencies.'),
    'okNote': T('{reran} passo(s) refeito(s) e {secs} s de build. As dependências ficaram no cache, como devem.', '{reran} step(s) redone and {secs} s of build. The dependencies stayed cached, as they should.')},
  'data': {},
  'recipe': {'steps': [
     T('Crie uma pasta api-pedidos com este server.js:\n' + server_js(True), 'Create an api-pedidos folder with this server.js:\n' + server_js(False)),
     T('Gere o package.json e o package-lock.json com o Express. Com o Node instalado:\nnpm init -y && npm install express\nSem Node, use um contêiner (bash, zsh ou PowerShell):\n' + NPM_IN_DOCKER,
       'Generate package.json and package-lock.json with Express. With Node installed:\nnpm init -y && npm install express\nWithout Node, use a container (bash, zsh or PowerShell):\n' + NPM_IN_DOCKER),
     T('Crie o Dockerfile:\n' + DOCKERFILE_L3 + '\nE o .dockerignore:\n' + DOCKERIGNORE_L3,
       'Create the Dockerfile:\n' + DOCKERFILE_L3 + '\nAnd the .dockerignore:\n' + DOCKERIGNORE_L3),
     T('Construa, rode e teste:\ndocker build -t api-pedidos:1.0 .\ndocker run -d --name api -p 3000:3000 api-pedidos:1.0\ncurl http://localhost:3000\n(ou abra o endereço no navegador). Depois: docker rm -f api',
       'Build, run and test:\ndocker build -t api-pedidos:1.0 .\ndocker run -d --name api -p 3000:3000 api-pedidos:1.0\ncurl http://localhost:3000\n(or open the address in a browser). Then: docker rm -f api'),
     T('Mude o texto da resposta no server.js e rode de novo:\ndocker build -t api-pedidos:1.0 .', 'Change the response text in server.js and run again:\ndocker build -t api-pedidos:1.0 .')],
   'ok': T('o curl responde com a mensagem da marmitaria, e no segundo build as linhas do WORKDIR, da cópia do package.json e do RUN npm ci aparecem como CACHED: só o COPY . . roda de novo.',
           'curl answers with the kitchen’s message, and in the second build the WORKDIR, package.json copy and RUN npm ci lines show as CACHED: only COPY . . runs again.')}}

t3 = {'pt': {'objectives': ['Ler um Dockerfile linha a linha.', 'Ordenar instruções para aproveitar o cache.', 'Usar .dockerignore para encolher o contexto.'], 'minutes': 20,
  'activity': 'Receita embaralhada: cada grupo recebe as seis linhas do Dockerfile em tiras de papel e precisa ordená-las para que mudar o código seja rápido. Depois, o professor "muda" uma linha e os grupos riscam os passos que precisariam rodar de novo.',
  'discussion': ['Que outro passo lento do seu projeto mereceria ficar mais em cima no Dockerfile?', 'O que mais você colocaria no .dockerignore?'],
  'misconceptions': ['"O Docker sabe que o npm ci não mudou." Ele só sabe que a camada de baixo mudou; a ordem das linhas é que protege o cache.', '"O .dockerignore é só para deixar o build rápido." Ele também impede que .env e .git entrem na imagem.']},
 'en': {'objectives': ['Read a Dockerfile line by line.', 'Order instructions to take advantage of the cache.', 'Use .dockerignore to shrink the context.'], 'minutes': 20,
  'activity': 'Shuffled recipe: each group gets the six Dockerfile lines on paper strips and must order them so changing the code is fast. Then the teacher "changes" a line and the groups cross out the steps that would have to run again.',
  'discussion': ['What other slow step in your project deserves to move up in the Dockerfile?', 'What else would you put in .dockerignore?'],
  'misconceptions': ['"Docker knows npm ci didn’t change." It only knows the layer below changed; the line order is what protects the cache.', '"The .dockerignore is only about build speed." It also keeps .env and .git out of the image.']}}
write('03-dockerfile', s3, loc3('pt'), loc3('en'), t3)

# ================================================================== 4 · registro
D4 = {k: fake_digest(f'api-pedidos {k}') for k in ('A', 'B', 'C')}
s4 = step('k8s-registro', 4, TRACK, 15, ['registro', 'tag', 'digest', 'docker-hub', 'ghcr', 'acr'], ['k8s-dockerfile'], SIM,
  loc('implantar', 'deploy'),
  {'name': 'text', 'required': False, 'default': loc('api-pedidos', 'api-pedidos'), 'ui': 'text'},
  [flag('ref', 'referencia', 'ref', 'enum',
        options=[opt('version', 'versao', 'version'), opt('latest', 'latest', 'latest'), opt('digest', 'digest', 'digest')], default='version', ui='select'),
   flag('registry', 'registro', 'registry', 'enum',
        options=[opt('ghcr', 'ghcr', 'ghcr'), opt('hub', 'dockerhub', 'dockerhub'), opt('acr', 'acr', 'acr'), opt('local', 'local', 'local')], default='ghcr', ui='select'),
   flag('overwrite', 'sobrescreveu', 'overwritten', 'bool', default=False, ui='switch')],
  {'options': ['v14', 'v15', 'error'], 'answer': 'v14'}, 'drift',
  {'live': True,
   'consts': {'prefixes': {'ghcr': 'ghcr.io/escola/', 'hub': 'docker.io/escola/', 'acr': 'escola.azurecr.io/', 'local': 'localhost:5000/'},
              'digests': D4, 'short': {k: v[:7] for k, v in D4.items()}},
   'compute': {
     'pfx': "lookup(prefixes, registry, '')",
     'refPart': "ref == 'latest' ? ':latest' : (ref == 'version' ? ':1.4' : '@sha256:' + digests.A)",
     'fullRef': 'pfx + text + refPart',
     'bKey': "ref == 'latest' ? 'C' : (ref == 'version' ? (overwrite ? 'B' : 'A') : 'A')",
     'drifted': "bKey != 'A'",
     'aVer': "lookup(verNames, 'A', '')", 'bVer': "lookup(verNames, bKey, '')",
     'sA': 'short.A', 'sC': 'short.C', 'bShort': "lookup(short, bKey, '')",
     'tag14': 'overwrite ? short.B : short.A',
     'loginLine': "'$ ' + lookup(logins, registry, '')",
     'timeline': "[['@mon', '@evMon', sA, sA, '—'], ['@tue', overwrite ? '@evTueOver' : '@evTue', sC, tag14, sC]]"},
   'cases': [
     {'when': 'drifted', 'flags': ['drift']},
     {'when': "ref == 'latest'", 'flags': ['floatingTag']},
     {'when': "ref == 'digest'", 'flags': ['pinned']},
     {'when': 'true', 'vars': {'a': 'aVer', 'b': 'bVer', 'fullRef': 'fullRef'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@aM', 'value': '=aVer', 'tone': 'info'},
       {'label': '@bM', 'value': '=bVer', 'tone': "=drifted ? 'bad' : 'ok'"},
       {'label': '@sameM', 'value': "=drifted ? '@no' : '@yes'", 'tone': "=drifted ? 'bad' : 'ok'"}]},
     {'type': 'cluster', 'label': '@clusterLabel', 'nodes': [
       {'name': '@srvA', 'status': '@pulledMon', 'tone': 'ok', 'pods': [{'name': "='api-pedidos · ' + sA", 'status': 'Running'}]},
       {'name': '@srvB', 'status': '@pulledWed', 'tone': "=drifted ? 'warn' : 'ok'", 'pods': [{'name': "='api-pedidos · ' + bShort", 'status': 'Running'}]}]},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['@colWhen', '@colEvent', 'latest', '1.4', '1.5'], 'rows': '=timeline',
      'tones': "=['neutral', overwrite ? 'warn' : 'neutral']", 'caption': '@tableCap'},
     {'type': 'terminal', 'label': '@termLabel', 'lines': [
       '=loginLine', "='$ docker pull ' + fullRef", "=(drifted ? '?' : '+') + 'Digest: sha256:' + lookup(digests, bKey, '')",
       "='Status: Downloaded newer image for ' + fullRef"]},
     {'type': 'note', 'when': "=drifted && ref == 'latest'", 'tone': 'bad', 'text': '@driftLatest'},
     {'type': 'note', 'when': "=drifted && ref == 'version'", 'tone': 'bad', 'text': '@driftOver'},
     {'type': 'note', 'when': "=ref == 'digest'", 'tone': 'ok', 'text': '@pinNote'},
     {'type': 'note', 'when': "=ref == 'version' && !overwrite", 'tone': 'info', 'text': '@versionNote'}]})

def loc4(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Registro', 'Registry'),
  'subtitle': T('O freezer central da marmitaria: etiqueta escrita a lápis × impressão digital', 'The kitchen’s central freezer: a pencil label vs a fingerprint'),
  'mission': T('Na segunda, a Tia Cida publicou a api-pedidos 1.4 no registro, e o servidor A puxou. Na terça, um colega publicou a 1.5 (e a tag latest foi junto). Na quarta, nasce o servidor B e puxa a mesma referência que o A usou. Compare implantar pela tag de versão, pela latest e pelo digest; e veja o que acontece se alguém republicar a tag 1.4 por cima.',
               'On Monday, Aunt Cida pushed api-pedidos 1.4 to the registry, and server A pulled it. On Tuesday, a teammate pushed 1.5 (and the latest tag moved with it). On Wednesday, server B is born and pulls the same reference A used. Compare deploying by version tag, by latest and by digest; and see what happens if someone re-pushes the 1.4 tag over the old one.'),
  'predict': {'question': T('o servidor A puxou api-pedidos:1.4 na segunda. Na quarta, o B puxa api-pedidos:1.4 também, depois de o colega publicar a 1.5. O que o B roda?', 'server A pulled api-pedidos:1.4 on Monday. On Wednesday, B pulls api-pedidos:1.4 too, after the teammate pushed 1.5. What does B run?'),
    'options': {'v14': T('A 1.4, igual ao A', '1.4, same as A'), 'v15': T('A 1.5, a mais nova', '1.5, the newest'), 'error': T('Erro: a 1.4 ficou velha', 'An error: 1.4 is stale')}},
  'feedback': {'right': T('isso: publicar a 1.5 não mexe na etiqueta 1.4, que continua apontando para o mesmo conteúdo. Desde que ninguém republique por cima dela… e isso, spoiler, dá para fazer.',
                          'right: pushing 1.5 doesn’t touch the 1.4 label, which still points to the same content. As long as nobody re-pushes over it… which, spoiler, is possible.'),
               'wrong': T('é a 1.4. Cada tag é uma etiqueta separada: publicar a 1.5 move a latest, mas não a 1.4. Os dois servidores rodam o mesmo digest.',
                          'it’s 1.4. Each tag is a separate label: pushing 1.5 moves latest, but not 1.4. Both servers run the same digest.'),
               'skipped': T('sem palpite? Rode e compare o digest dos dois servidores.', 'no guess? Run it and compare both servers’ digests.')},
  'coach': {'ui': T('palpite anotado. Rode com a tag de versão e depois troque para latest. Compare as versões dos dois servidores.', 'guess noted. Run with the version tag, then switch to latest. Compare both servers’ versions.'),
            'cmd': T('palpite anotado. Rode implantar e compare as versões dos servidores A e B.', 'guess noted. Run deploy and compare the versions on servers A and B.')},
  'tryNext': {'ui': T('Ligue "um colega republicou a 1.4": até tag de versão é só etiqueta. Depois troque a referência para digest com a republicação ligada.', 'Turn on "a teammate re-pushed 1.4": even a version tag is just a label. Then switch the reference to digest with the re-push still on.'),
              'cmd': T('Rode implantar --sobrescreveu sim (até tag de versão é só etiqueta) e depois implantar --referencia digest --sobrescreveu sim.', 'Run deploy --overwritten yes (even a version tag is just a label) and then deploy --ref digest --overwritten yes.')},
  'why': {'simples': T('O registro é o freezer central da marmitaria: você guarda as marmitas lá e qualquer filial retira. A etiqueta (tag) é escrita a lápis: “lasanha da semana” hoje é uma, semana que vem é outra, e alguém pode apagar e escrever de novo. O digest é a impressão digital da marmita: se o conteúdo for diferente, a impressão é diferente.\nlatest não tem nada de mágico: é só uma etiqueta que costuma ser colada na marmita mais nova. Pedir “a latest” é pedir “a que estiver com essa etiqueta na hora”.',
                       'The registry is the kitchen’s central freezer: you store lunchboxes there and any branch picks them up. The label (tag) is written in pencil: “lasagna of the week” is one today and another next week, and someone can erase it and write again. The digest is the lunchbox’s fingerprint: if the content is different, the fingerprint is different.\nlatest is nothing magical: it’s just a label people usually stick on the newest lunchbox. Asking for “latest” means asking for “whichever has that label right now”.'),
          'dev': T('Nome completo de uma imagem: registro/caminho/repositório:tag, como ghcr.io/escola/api-pedidos:1.4. Sem registro no nome, o Docker usa o Docker Hub (docker.io), e as imagens oficiais ficam em library/: node:24-slim é docker.io/library/node:24-slim. No GHCR o nome é ghcr.io/DONO/IMAGEM, e o login usa um token pessoal (docker login ghcr.io). No ACR o nome usa o servidor de login do registro (algo como meuregistro.azurecr.io; o az acr create mostra o loginServer exato), e o login é az acr login --name meuregistro.\nTag é um ponteiro que pode mudar: docker push com uma tag que já existe move o ponteiro. Digest (sha256:…) é o hash do manifesto e nunca muda: nome@sha256:… sempre traz exatamente a mesma imagem.',
                   'An image’s full name: registry/path/repository:tag, like ghcr.io/escola/api-pedidos:1.4. With no registry in the name, Docker uses Docker Hub (docker.io), and official images live under library/: node:24-slim is docker.io/library/node:24-slim. On GHCR the name is ghcr.io/OWNER/IMAGE, and login uses a personal token (docker login ghcr.io). On ACR the name uses the registry’s login server (something like myregistry.azurecr.io; az acr create shows the exact loginServer), and login is az acr login --name myregistry.\nA tag is a pointer that can move: docker push with an existing tag moves the pointer. A digest (sha256:…) is the manifest’s hash and never changes: name@sha256:… always brings exactly the same image.'),
          'especialista': T('Em produção: publique tags que não se repetem (versão semântica ou o SHA do commit), nunca reaproveite uma tag de versão e implante por digest. Vários registros permitem travar tags contra sobrescrita (no ACR, bloqueando a imagem; no ECR, com tags imutáveis). latest serve para experimentar, não para implantar; no Kubernetes ela ainda muda o padrão do imagePullPolicy para Always.\nUma tag pode apontar para um índice multiplataforma (amd64 e arm64), e o digest do índice é diferente do digest de cada manifesto. O registro também é superfície de segurança: assine as imagens (cosign, Notation), gere SBOM, escaneie vulnerabilidades e use credenciais de máquina (identidade gerenciada no Azure, o GITHUB_TOKEN no Actions) em vez de senhas pessoais.',
                            'In production: push tags that never repeat (semantic version or the commit SHA), never reuse a version tag and deploy by digest. Several registries let you lock tags against overwrites (on ACR, by locking the image; on ECR, with immutable tags). latest is for experimenting, not deploying; in Kubernetes it also flips the imagePullPolicy default to Always.\nA tag can point to a multi-platform index (amd64 and arm64), and the index digest differs from each manifest’s digest. The registry is also a security surface: sign images (cosign, Notation), generate an SBOM, scan for vulnerabilities and use machine credentials (managed identity on Azure, GITHUB_TOKEN in Actions) instead of personal passwords.')},
  'break': {'mission': {'ui': T('hora de quebrar: implante pela tag latest.', 'time to break it: deploy by the latest tag.'),
                        'cmd': T('hora de quebrar: rode implantar --referencia latest', 'time to break it: run deploy --ref latest')},
            'success': T('Quebrou: os dois servidores pediram {fullRef}, mas o A roda {a} e o B roda {b}. Etiqueta que se move não garante que todo mundo roda o mesmo código, e o bug que só aparece “em alguns servidores” nasce assim.',
                         'Broken: both servers asked for {fullRef}, but A runs {a} and B runs {b}. A label that moves doesn’t guarantee everyone runs the same code, and the bug that only shows up “on some servers” is born like this.'),
            'calm': T('A e B rodam {b}, pedindo {fullRef}. Para quebrar, implante pela tag latest.', 'A and B run {b}, asking for {fullRef}. To break it, deploy by the latest tag.')},
  'hints': {'ui': T(['Escolha a referência, o registro e se alguém republicou a 1.4; a tabela mostra para onde cada tag aponta.', 'Uma tag que se move faz o servidor novo puxar outra coisa.', 'Escolha a referência latest.'],
                    ['Pick the reference, the registry and whether someone re-pushed 1.4; the table shows where each tag points.', 'A tag that moves makes the new server pull something else.', 'Pick the latest reference.']),
            'cmd': T(['O repositório vai entre aspas; --referencia, --registro e --sobrescreveu são opcionais.', '--referencia aceita versao, latest ou digest.', 'implantar --referencia latest'],
                     ['The repository goes in quotes; --ref, --registry and --overwritten are optional.', '--ref takes version, latest or digest.', 'deploy --ref latest'])},
  'errors': {'notInEnum.ref': T('Use versao, latest ou digest.', 'Use version, latest or digest.'),
             'notInEnum.registry': T('Use ghcr, dockerhub, acr ou local.', 'Use ghcr, dockerhub, acr or local.'),
             'notBool.overwrite': T('Use sim ou nao.', 'Use yes or no.')},
  'controls': {'arg': T('Repositório', 'Repository'), 'ref': T('Como o servidor pede a imagem', 'How the server asks for the image'), 'registry': T('Registro', 'Registry'),
               'overwrite': T('Um colega republicou a tag 1.4 na terça', 'A teammate re-pushed the 1.4 tag on Tuesday')},
  'scene': {'label': T('Segunda, terça e quarta no registro', 'Monday, Tuesday and Wednesday at the registry'), 'empty': T('Rode para implantar.', 'Run to deploy.'),
    'aM': T('versão no servidor A (segunda)', 'version on server A (Monday)'), 'bM': T('versão no servidor B (quarta)', 'version on server B (Wednesday)'), 'sameM': T('mesmo código nos dois?', 'same code on both?'),
    'yes': T('sim', 'yes'), 'no': T('não', 'no'),
    'clusterLabel': T('Servidores e o digest que cada um roda', 'Servers and the digest each one runs'),
    'srvA': T('servidor-a', 'server-a'), 'srvB': T('servidor-b', 'server-b'), 'pulledMon': T('puxou na segunda', 'pulled on Monday'), 'pulledWed': T('puxou na quarta', 'pulled on Wednesday'),
    'tableLabel': T('Para onde cada tag aponta (início do digest)', 'Where each tag points (digest prefix)'),
    'colWhen': T('quando', 'when'), 'colEvent': T('o que aconteceu', 'what happened'),
    'mon': T('segunda', 'Monday'), 'tue': T('terça', 'Tuesday'),
    'evMon': T('push da 1.4 (e da latest)', 'push of 1.4 (and latest)'), 'evTue': T('push da 1.5 (e da latest)', 'push of 1.5 (and latest)'),
    'evTueOver': T('1.5 + latest + 1.4 refeita', '1.5 + latest + rebuilt 1.4'),
    'tableCap': T('Digests da simulação. Tag é ponteiro; o digest é o conteúdo.', 'Simulated digests. A tag is a pointer; the digest is the content.'),
    'termLabel': T('Terminal do servidor B (simulado)', 'Server B terminal (simulated)'),
    'driftLatest': T('A latest andou da 1.4 para a 1.5 na terça. O A roda {a}, o B roda {b}: mesmo nome, código diferente.', 'latest moved from 1.4 to 1.5 on Tuesday. A runs {a}, B runs {b}: same name, different code.'),
    'driftOver': T('Alguém republicou a 1.4 por cima. O A roda {a}, o B roda {b}: até a tag de versão é só uma etiqueta a lápis.', 'Someone re-pushed 1.4 over the old one. A runs {a}, B runs {b}: even a version tag is just a pencil label.'),
    'pinNote': T('Pedindo pelo digest, o B roda exatamente o que o A roda, aconteça o que acontecer com as etiquetas.', 'Asking by digest, B runs exactly what A runs, whatever happens to the labels.'),
    'versionNote': T('A tag 1.4 ficou parada e os dois rodam {b}. Funciona enquanto ninguém republicar a mesma tag.', 'The 1.4 tag stayed put and both run {b}. It works as long as nobody re-pushes the same tag.')},
  'data': {'verNames': {'A': '1.4', 'B': '1.4 (refeita)' if pt else '1.4 (rebuilt)', 'C': '1.5'},
           'logins': {'ghcr': 'echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin', 'hub': 'docker login',
                      'acr': 'az acr login --name escola', 'local': T('# localhost: sem login', '# localhost: no login')}},
  'recipe': {'steps': [
     T('Suba um registro local de estudo (sem TLS, só para a sua máquina):\ndocker run -d -p 5000:5000 --name registry registry:3\nNo macOS a porta 5000 pode estar ocupada pelo AirPlay; nesse caso use -p 5001:5000 e troque localhost:5000 por localhost:5001 nos passos seguintes.',
       'Start a local study registry (no TLS, for your machine only):\ndocker run -d -p 5000:5000 --name registry registry:3\nOn macOS port 5000 may be taken by AirPlay; in that case use -p 5001:5000 and replace localhost:5000 with localhost:5001 in the next steps.'),
     T('Dê um nome com endereço à imagem da lição 3 e envie (a última linha do push mostra o digest, sha256:…):\ndocker tag api-pedidos:1.0 localhost:5000/api-pedidos:1.0\ndocker push localhost:5000/api-pedidos:1.0',
       'Give lesson 3’s image a name with an address and push it (the last push line shows the digest, sha256:…):\ndocker tag api-pedidos:1.0 localhost:5000/api-pedidos:1.0\ndocker push localhost:5000/api-pedidos:1.0'),
     T('Pergunte ao registro o que ele guarda; é uma API HTTP:\ncurl http://localhost:5000/v2/_catalog\ncurl http://localhost:5000/v2/api-pedidos/tags/list',
       'Ask the registry what it stores; it’s an HTTP API:\ncurl http://localhost:5000/v2/_catalog\ncurl http://localhost:5000/v2/api-pedidos/tags/list'),
     T('Apague a etiqueta local e puxe pelo digest do passo 2:\ndocker image rm localhost:5000/api-pedidos:1.0\ndocker pull localhost:5000/api-pedidos@sha256:COLE_O_DIGEST_AQUI\ndocker image ls --digests localhost:5000/api-pedidos',
       'Delete the local label and pull by the digest from step 2:\ndocker image rm localhost:5000/api-pedidos:1.0\ndocker pull localhost:5000/api-pedidos@sha256:PASTE_THE_DIGEST_HERE\ndocker image ls --digests localhost:5000/api-pedidos')],
   'ok': T('o _catalog lista api-pedidos, a lista de tags mostra 1.0, o pull pelo digest termina sem erro e o docker image ls --digests mostra o mesmo sha256 que apareceu no push.',
           '_catalog lists api-pedidos, the tag list shows 1.0, the pull by digest finishes without errors and docker image ls --digests shows the same sha256 that appeared on push.')}}

t4 = {'pt': {'objectives': ['Ler o nome completo de uma imagem (registro, repositório, tag).', 'Diferenciar tag mutável de digest imutável.', 'Explicar por que latest não serve para implantar.'], 'minutes': 15,
  'activity': 'Freezer de etiquetas: o professor cola etiquetas de papel (latest, 1.4, 1.5) em caixas numeradas (os digests). Durante a aula, ele move a etiqueta latest e reescreve a 1.4. Dois alunos "servidores" pegam a caixa pela etiqueta em momentos diferentes: pegaram a mesma caixa?',
  'discussion': ['Onde no seu trabalho ou projeto algo é referenciado por um nome que pode mudar de conteúdo?', 'Quem deveria poder sobrescrever uma tag de versão?'],
  'misconceptions': ['"latest é a versão mais nova." É só uma etiqueta; aponta para onde a última pessoa que publicou deixou.', '"Tag de versão é imutável." Só se o registro travar; por padrão, um push com a mesma tag move o ponteiro.']},
 'en': {'objectives': ['Read an image’s full name (registry, repository, tag).', 'Tell a mutable tag from an immutable digest.', 'Explain why latest isn’t fit for deploying.'], 'minutes': 15,
  'activity': 'Label freezer: the teacher sticks paper labels (latest, 1.4, 1.5) on numbered boxes (the digests). During class, they move the latest label and rewrite 1.4. Two "server" students fetch the box by label at different moments: did they get the same box?',
  'discussion': ['Where in your work or project is something referenced by a name whose content can change?', 'Who should be allowed to overwrite a version tag?'],
  'misconceptions': ['"latest is the newest version." It’s just a label; it points wherever the last person who pushed left it.', '"A version tag is immutable." Only if the registry locks it; by default, a push with the same tag moves the pointer.']}}
write('04-registro', s4, loc4('pt'), loc4('en'), t4)

# ================================================================== 5 · por que orquestrar
CAP = 4
SUF = ['x2k9p', 'm4q7z', 'b8n3r', 't6w1c', 'h9j5d', 'p3v8s', 'k7r2f', 'z1m6q', 'c5d4w']
def l5_scenario(way, event, s):
  orch = way == 'orchestrator'
  nodes = [{'name': f'@srv{i + 1}', 'status': 'Ready', 'pods': []} for i in range(s)]
  old = [f'api-7c9d-{SUF[j]}' for j in range(3)]
  for j in range(3): nodes[j % s]['pods'].append({'name': old[j], 'status': 'Running'})
  need, down, humans, auto, ready, cmds, cause, short = 3, 0, 0, 0, 3, 0, '', False
  def least(skip=None):
    cands = [n for k, n in enumerate(nodes) if k != skip and n['status'] == 'Ready' and sum(p['status'] == 'Running' for p in n['pods']) < CAP]
    return min(cands, key=lambda n: sum(p['status'] == 'Running' for p in n['pods'])) if cands else None
  if event == 'crash':
    dead = nodes[0]; dead['status'] = 'NotReady'; on_dead = len(dead['pods'])
    if orch:
      for p in dead['pods']: p['status'] = 'Terminating'
      if s >= 2:
        for j in range(on_dead):
          least(0)['pods'].append({'name': f'api-7c9d-{SUF[3 + j]}', 'status': 'Running'})
        down, auto = 6, on_dead
      else:
        nodes.append({'name': '@noNode', 'status': '', 'tone': 'warn', 'pods': [{'name': f'api-7c9d-{SUF[3 + j]}', 'status': 'Pending'} for j in range(3)]})
        down, humans, cmds, ready, cause, short = 45, 1, 2, 0, 'oneServer', True
    else:
      for p in dead['pods']: p.update({'status': 'Unknown', 'tone': 'bad'})
      down, humans, cmds, ready, cause = 40, 1, 3, 3 - on_dead, 'manual'
  elif event == 'peak':
    need = 6
    if orch:
      placed, pend = 0, []
      for j in range(3):
        n = least()
        if n: n['pods'].append({'name': f'api-7c9d-{SUF[3 + j]}', 'status': 'Running'}); placed += 1
        else: pend.append({'name': f'api-7c9d-{SUF[3 + j]}', 'status': 'Pending'})
      if pend: nodes.append({'name': '@noNode', 'status': '', 'tone': 'warn', 'pods': pend})
      ready, auto = 3 + placed, placed
      if pend: down, humans, cmds, cause, short = 60, 1, 2, 'noRoom', True
      else: down = 2
    else:
      down, humans, cmds, ready, cause = 35, 1, 3, 3, 'manual'
  else:  # release
    for n in nodes:
      for k, p in enumerate(n['pods']): n['pods'][k] = {'name': p['name'].replace('7c9d', '5b2e'), 'status': 'Running'}
    if orch: auto = 3
    else: down, humans, cmds, ready, cause = 6, 1, 6, 2, 'manual'
  time = {'crash': '03:00', 'peak': '12:00', 'release': '15:00'}[event]
  return {'nodes': nodes, 'down': down, 'humans': humans, 'auto': auto, 'ready': ready, 'need': need, 'cmds': cmds,
          'cause': cause, 'time': time, 'flow': f'{way}-{event}' + ('-short' if short else '')}
L5_TABLE = {f'{w}-{e}-{s}': l5_scenario(w, e, s) for w in ('manual', 'orchestrator') for e in ('crash', 'peak', 'release') for s in range(1, 6)}

s5 = step('k8s-por-que-orquestrar', 5, TRACK, 20, ['orquestracao', 'kubernetes', 'auto-recuperacao', 'rolling-update', 'escala'], ['k8s-registro'], SIM,
  loc('operar', 'operate'),
  {'name': 'text', 'required': False, 'default': loc('api-pedidos', 'api-pedidos'), 'ui': 'text'},
  [flag('way', 'jeito', 'way', 'enum',
        options=[opt('orchestrator', 'orquestrador', 'orchestrator'), opt('manual', 'manual', 'manual')], default='orchestrator', ui='select'),
   flag('event', 'evento', 'event', 'enum',
        options=[opt('crash', 'queda', 'crash'), opt('peak', 'pico', 'peak'), opt('release', 'versao', 'release')], default='crash', ui='select'),
   flag('servers', 'servidores', 'servers', 'int', min=1, max=5, default=3, ui='slider')],
  {'options': ['rescheduled', 'waits', 'gone'], 'answer': 'rescheduled'}, 'humanNeeded',
  {'live': True,
   'consts': {'scenarios': L5_TABLE},
   'compute': {
     'sc': "lookup(scenarios, way + '-' + event + '-' + servers, null)",
     'downMin': 'sc.down', 'humansN': 'sc.humans', 'autoN': 'sc.auto', 'readyN': 'sc.ready', 'needN': 'sc.need', 'cmdsN': 'sc.cmds',
     'atTime': 'sc.time', 'causeText': "lookup(causes, sc.cause, '')", 'flowSteps': 'lookup(flows, sc.flow, [])',
     'isOrch': "way == 'orchestrator'"},
   'cases': [
     {'when': 'humansN > 0', 'flags': ['humanNeeded']},
     {'when': 'humansN == 0', 'flags': ['selfHealed']},
     {'when': 'true', 'vars': {'downMin': 'downMin', 'humansN': 'humansN', 'autoN': 'autoN', 'readyN': 'readyN', 'needN': 'needN', 'atTime': 'atTime', 'causeText': 'causeText'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@readyM', 'value': "=readyN + ' / ' + needN", 'tone': "=readyN < needN ? 'warn' : 'ok'"},
       {'label': '@downM', 'value': '=downMin', 'format': 'min', 'tone': "=downMin > 10 ? 'bad' : (downMin > 0 ? 'warn' : 'ok')"},
       {'label': '@humansM', 'value': '=humansN', 'format': 'int', 'tone': "=humansN > 0 ? 'bad' : 'ok'"},
       {'label': '@cmdsM', 'value': '=cmdsN', 'format': 'int', 'tone': "=cmdsN > 0 ? 'warn' : 'dim'"}]},
     {'type': 'cluster', 'label': '@clusterLabel', 'nodes': '=sc.nodes'},
     {'type': 'flow', 'label': '@flowLabel', 'steps': '=flowSteps'},
     {'type': 'note', 'when': '=humansN > 0', 'tone': 'bad', 'text': '@humanNote'},
     {'type': 'note', 'when': '=humansN == 0', 'tone': 'ok', 'text': '@healNote'}]})

def flows(pt):
  T = lambda a, b: a if pt else b
  f = lambda label, sub, tone: {'label': label, 'sub': sub, 'tone': tone}
  return {
   'manual-crash': [f('03:00', T('servidor-1 apaga', 'server-1 goes dark'), 'bad'), f('03:25', T('o alerta acorda alguém', 'the alert wakes someone up'), 'warn'),
                    f('03:35', T('ssh + docker run em outro servidor', 'ssh + docker run on another server'), 'warn'), f('03:40', T('de volta, 40 min depois', 'back, 40 min later'), 'ok')],
   'orchestrator-crash': [f('03:00', T('servidor-1 apaga', 'server-1 goes dark'), 'bad'), f('~03:01', T('o nó vira NotReady', 'the node turns NotReady'), 'warn'),
                          f('~03:06', T('acaba a tolerância padrão de 5 min: pods despejados', 'the default 5 min toleration ends: pods evicted'), 'info'),
                          f('~03:06', T('réplicas novas Running nos outros servidores', 'new replicas Running on the other servers'), 'ok')],
   'orchestrator-crash-short': [f('03:00', T('servidor-1 apaga', 'server-1 goes dark'), 'bad'), f('~03:01', T('o nó vira NotReady', 'the node turns NotReady'), 'warn'),
                                f('~03:06', T('pods novos ficam Pending: não há outro servidor', 'new pods stay Pending: there’s no other server'), 'bad'),
                                f('03:45', T('alguém conserta o servidor', 'someone fixes the server'), 'warn')],
   'manual-peak': [f('12:00', T('o movimento triplica', 'traffic triples'), 'bad'), f('12:20', T('alguém percebe a lentidão', 'someone notices the slowness'), 'warn'),
                   f('12:35', T('docker run de mais 3 contêineres, à mão', 'docker run of 3 more containers, by hand'), 'ok')],
   'orchestrator-peak': [f('12:00', T('o movimento triplica', 'traffic triples'), 'bad'), f('12:00', T('o HPA vê a CPU alta e pede 6 réplicas', 'the HPA sees high CPU and asks for 6 replicas'), 'info'),
                         f('~12:02', T('6 réplicas Running', '6 replicas Running'), 'ok')],
   'orchestrator-peak-short': [f('12:00', T('o movimento triplica', 'traffic triples'), 'bad'), f('12:00', T('o HPA pede 6 réplicas', 'the HPA asks for 6 replicas'), 'info'),
                               f('~12:01', T('não cabe tudo: parte fica Pending', 'not everything fits: some stay Pending'), 'bad'),
                               f('13:00', T('alguém adiciona servidores', 'someone adds servers'), 'warn')],
   'manual-release': [f('15:00', T('docker stop na versão velha', 'docker stop on the old version'), 'warn'), f('15:01', T('docker run na nova, uma por uma', 'docker run on the new one, one by one'), 'warn'),
                      f('15:06', T('pronto, com erros no meio do caminho', 'done, with errors along the way'), 'ok')],
   'orchestrator-release': [f('15:00', 'kubectl set image', 'info'), f('15:00', T('sobe 1 pod novo antes de tirar 1 velho', 'starts 1 new pod before removing 1 old one'), 'info'),
                            f('~15:02', T('3 réplicas da versão nova, sem queda', '3 new-version replicas, no downtime'), 'ok')]}

def loc5(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('Por que orquestrar', 'Why orchestrate'),
  'subtitle': T('Um food truck você toca sozinho; uma frota precisa de uma gerente que nunca dorme', 'You can run one food truck alone; a fleet needs a manager who never sleeps'),
  'mission': T('A api-pedidos roda com 3 réplicas espalhadas em alguns servidores. Três coisas vão acontecer: um servidor cai às 3h da manhã, o movimento triplica ao meio-dia e sai uma versão nova às 15h. Compare cuidar disso no braço (docker run em cada servidor) com um orquestrador como o Kubernetes (com um autoscaler configurado para o pico). Conte quanto tempo o serviço fica abaixo do pedido e quantas pessoas precisam largar tudo.',
               'api-pedidos runs 3 replicas spread over a few servers. Three things will happen: a server dies at 3 am, traffic triples at noon and a new version ships at 3 pm. Compare handling it by hand (docker run on each server) with an orchestrator like Kubernetes (with an autoscaler set up for the peak). Count how long the service stays below what was asked and how many people have to drop everything.'),
  'predict': {'question': T('com orquestrador e 3 servidores, às 3h o servidor-1 cai. O que acontece com a réplica que estava nele?', 'with an orchestrator and 3 servers, at 3 am server-1 dies. What happens to the replica that was on it?'),
    'options': {'rescheduled': T('O orquestrador cria outra num servidor que sobrou', 'The orchestrator creates another one on a remaining server'),
                'waits': T('Fica fora até alguém acordar e subir de novo', 'It stays down until someone wakes up and restarts it'),
                'gone': T('Some para sempre: agora são só 2', 'It’s gone for good: now there are only 2')}},
  'feedback': {'right': T('isso! Você pediu 3 réplicas, então o orquestrador corre atrás de ter 3. Quando o nó some, ele espera a tolerância padrão (uns 5 minutos no Kubernetes), despeja os pods dele e recria as réplicas nos servidores que sobraram. Ninguém acordou.',
                          'right! You asked for 3 replicas, so the orchestrator works to keep 3. When the node disappears, it waits out the default toleration (about 5 minutes in Kubernetes), evicts its pods and recreates the replicas on the remaining servers. Nobody woke up.'),
               'wrong': T('olhe o cluster: o pod do servidor-1 ficou Terminating e um novo apareceu Running em outro servidor, sem ninguém digitar nada. Você declara "quero 3"; o orquestrador corrige a diferença.',
                          'look at the cluster: the pod on server-1 went Terminating and a new one showed up Running on another server, with nobody typing anything. You declare "I want 3"; the orchestrator fixes the difference.'),
               'skipped': T('sem palpite? Rode e procure, no cluster, o pod novo que apareceu sozinho.', 'no guess? Run it and look in the cluster for the new pod that showed up by itself.')},
  'coach': {'ui': T('palpite anotado. Rode com orquestrador e depois troque para manual. Compare "pessoas acordadas".', 'guess noted. Run with orchestrator, then switch to manual. Compare "people woken up".'),
            'cmd': T('palpite anotado. Rode operar e depois operar --jeito manual. Compare "pessoas acordadas".', 'guess noted. Run operate and then operate --way manual. Compare "people woken up".')},
  'tryNext': {'ui': T('Agora deixe 1 servidor só: nem orquestrador faz milagre sem outro lugar para mandar as réplicas. Depois teste o evento "versão".', 'Now leave a single server: not even an orchestrator works miracles with nowhere to send the replicas. Then try the "release" event.'),
              'cmd': T('Rode operar --servidores 1 (nem orquestrador faz milagre sem outro servidor) e depois operar --evento versao.', 'Run operate --servers 1 (not even an orchestrator works miracles without another server) and then operate --event release.')},
  'why': {'simples': T('Com um food truck, você mesmo dá conta: abre, cozinha, fecha. Com vinte trucks espalhados pela cidade, alguém precisa coordenar: quando um quebra às 3 da manhã, mandar outro; no almoço, pôr mais trucks na rua; trocar o cardápio sem fechar todos de uma vez.\nO orquestrador é essa gerente que nunca dorme. Você não diz “ligue o truck 3”; você diz “quero sempre 3 trucks servindo”, e ela corre atrás para que isso continue verdade.',
                       'With one food truck, you handle it yourself: open, cook, close. With twenty trucks spread around town, someone has to coordinate: when one breaks down at 3 am, send another; at lunchtime, put more trucks on the street; change the menu without closing them all at once.\nThe orchestrator is that manager who never sleeps. You don’t say “start truck 3”; you say “I always want 3 trucks serving”, and she works to keep that true.'),
          'dev': T('docker run resolve uma máquina. Com várias, aparecem perguntas que ele não responde: em qual servidor cada contêiner roda? Quem recria o que morreu? Como trocar de versão sem derrubar o serviço? Como os contêineres se acham na rede?\nO Kubernetes responde com estado desejado: você declara (um Deployment com replicas: 3) e controladores comparam o desejado com o real o tempo todo, corrigindo a diferença. Pod que morre é recriado; nó que cai tem os pods recriados em outros nós (por padrão, depois de uns 5 minutos de tolerância); a atualização é gradual (rolling update, que por padrão sobe pods novos antes de tirar todos os velhos) e dá para voltar com rollback. Escalar com a carga exige configurar, por exemplo, um HorizontalPodAutoscaler: não vem ligado sozinho.',
                   'docker run handles one machine. With several, questions appear that it doesn’t answer: which server does each container run on? Who recreates what died? How do you change versions without taking the service down? How do containers find each other on the network?\nKubernetes answers with desired state: you declare it (a Deployment with replicas: 3) and controllers compare desired with actual all the time, fixing the difference. A pod that dies is recreated; a node that goes down has its pods recreated on other nodes (by default, after about 5 minutes of toleration); updates are gradual (a rolling update, which by default starts new pods before removing all the old ones) and you can go back with a rollback. Scaling with load needs setting up, for example, a HorizontalPodAutoscaler: it isn’t on by default.'),
          'especialista': T('Orquestração tem custo: um control plane para manter (ou pagar, como no AKS, EKS e GKE), rede, armazenamento, atualizações de versão algumas vezes por ano, RBAC, políticas e observabilidade. Para um app pequeno, um PaaS de contêineres (Azure Container Apps, Cloud Run) ou um servidor com docker compose pode sair mais barato e mais simples.\nOs tempos padrão entram no desenho: um nó sem notícias vira NotReady depois de um período de carência, e os pods dele só são despejados quando acaba o tolerationSeconds de 300 s que o Kubernetes adiciona por padrão. Para reagir mais rápido, ajuste as tolerâncias por pod; para não depender disso, espalhe réplicas por nós e zonas (topologySpreadConstraints) e proteja-as em manutenções (PodDisruptionBudget). E auto-recuperação não é alta disponibilidade: com uma réplica só, todo reinício é queda.',
                            'Orchestration has a cost: a control plane to maintain (or pay for, as on AKS, EKS and GKE), networking, storage, version upgrades a few times a year, RBAC, policies and observability. For a small app, a container PaaS (Azure Container Apps, Cloud Run) or one server with docker compose can be cheaper and simpler.\nThe default timings shape the design: a node with no news turns NotReady after a grace period, and its pods are only evicted when the 300 s tolerationSeconds Kubernetes adds by default runs out. To react faster, tune tolerations per pod; to not depend on it, spread replicas across nodes and zones (topologySpreadConstraints) and protect them during maintenance (PodDisruptionBudget). And self-healing isn’t high availability: with a single replica, every restart is an outage.')},
  'break': {'mission': {'ui': T('hora de quebrar: troque para o jeito manual.', 'time to break it: switch to the manual way.'),
                        'cmd': T('hora de quebrar: rode operar --jeito manual', 'time to break it: run operate --way manual')},
            'success': T('Quebrou: {downMin} minutos com menos réplicas do que o pedido e {humansN} pessoa precisou largar tudo às {atTime}. Motivo: {causeText}.',
                         'Broken: {downMin} minutes with fewer replicas than asked and {humansN} person had to drop everything at {atTime}. Reason: {causeText}.'),
            'calm': T('Ninguém precisou intervir: o orquestrador voltou às {needN} réplicas pedidas em {downMin} min, criando {autoN} pod(s) sozinho. Para quebrar, opere no braço.',
                      'Nobody had to step in: the orchestrator got back to the {needN} requested replicas in {downMin} min, creating {autoN} pod(s) on its own. To break it, operate by hand.')},
  'hints': {'ui': T(['Escolha o jeito, o evento e quantos servidores; o cluster mostra onde ficou cada réplica.', 'No jeito manual, tudo espera alguém ver o alerta e digitar comandos.', 'Escolha o jeito manual.'],
                    ['Pick the way, the event and how many servers; the cluster shows where each replica ended up.', 'The manual way waits for someone to see the alert and type commands.', 'Pick the manual way.']),
            'cmd': T(['O app vai entre aspas; --jeito, --evento e --servidores são opcionais.', '--jeito aceita orquestrador ou manual; --evento aceita queda, pico ou versao.', 'operar --jeito manual'],
                     ['The app goes in quotes; --way, --event and --servers are optional.', '--way takes orchestrator or manual; --event takes crash, peak or release.', 'operate --way manual'])},
  'errors': {'notInEnum.way': T('Use orquestrador ou manual.', 'Use orchestrator or manual.'),
             'notInEnum.event': T('Use queda, pico ou versao.', 'Use crash, peak or release.'),
             'belowMin.servers': T('Pelo menos 1 servidor: sem nenhum, nem o orquestrador acha onde cozinhar.', 'At least 1 server: with none, not even the orchestrator finds a place to cook.'),
             'aboveMax.servers': T('Até 5 servidores nesta simulação.', 'Up to 5 servers in this simulation.')},
  'controls': {'arg': T('App', 'App'), 'way': T('Quem cuida', 'Who takes care'), 'event': T('O que acontece', 'What happens'), 'servers': T('Servidores', 'Servers')},
  'scene': {'label': T('Um dia na vida da api-pedidos', 'A day in the life of api-pedidos'), 'empty': T('Rode para começar o dia.', 'Run to start the day.'),
    'readyM': T('réplicas prontas no fim do evento', 'replicas ready after the event'), 'downM': T('tempo abaixo do pedido', 'time below what was asked'),
    'humansM': T('pessoas que largaram tudo', 'people who dropped everything'), 'cmdsM': T('comandos digitados à mão', 'commands typed by hand'),
    'srv1': T('servidor-1', 'server-1'), 'srv2': T('servidor-2', 'server-2'), 'srv3': T('servidor-3', 'server-3'), 'srv4': T('servidor-4', 'server-4'), 'srv5': T('servidor-5', 'server-5'),
    'clusterLabel': T('Servidores depois do evento (simulado)', 'Servers after the event (simulated)'), 'noNode': T('sem servidor (Pending)', 'no server (Pending)'),
    'flowLabel': T('Linha do tempo', 'Timeline'),
    'humanNote': T('{humansN} pessoa precisou agir às {atTime}: {causeText}.', '{humansN} person had to act at {atTime}: {causeText}.'),
    'healNote': T('Ninguém precisou agir: {autoN} pod(s) criado(s) pelo orquestrador e {downMin} min abaixo do pedido.', 'Nobody had to act: {autoN} pod(s) created by the orchestrator and {downMin} min below what was asked.')},
  'data': {'flows': flows(pt),
           'causes': {'manual': 'tudo dependia de alguém ver o alerta e digitar comandos' if pt else 'everything depended on someone seeing the alert and typing commands',
                      'oneServer': 'com um servidor só, não há para onde mandar as réplicas' if pt else 'with a single server, there’s nowhere to send the replicas',
                      'noRoom': 'não há espaço nos servidores para todas as réplicas' if pt else 'there’s no room on the servers for all the replicas'}},
  'recipe': {'steps': [
     T('Instale o kind (kind.sigs.k8s.io) e o kubectl (kubernetes.io/docs/tasks/tools). Eles usam o Docker que você já tem. Crie o arquivo kind.yaml:\n' + KIND_YAML,
       'Install kind (kind.sigs.k8s.io) and kubectl (kubernetes.io/docs/tasks/tools). They use the Docker you already have. Create the file kind.yaml:\n' + KIND_YAML),
     T('Crie um cluster com 1 nó de controle e 2 workers. Cada nó é um contêiner, como o docker ps mostra:\nkind create cluster --name escola --config kind.yaml\ndocker ps',
       'Create a cluster with 1 control-plane node and 2 workers. Each node is a container, as docker ps shows:\nkind create cluster --name escola --config kind.yaml\ndocker ps'),
     T('Leve a imagem da lição 3 para dentro do cluster e peça 3 réplicas (pulou a lição 3? use --image=nginx:alpine e pule o kind load):\nkind load docker-image api-pedidos:1.0 --name escola\nkubectl create deployment api --image=api-pedidos:1.0 --replicas=3\nkubectl get pods -o wide\nSe o kind load falhar (acontece com o image store do containerd, o padrão do Docker Engine 29), use o arquivo tar no lugar:\ndocker save --platform linux/amd64 -o api.tar api-pedidos:1.0\nkind load image-archive api.tar --name escola\n(troque por linux/arm64 em Macs com Apple Silicon). Outra saída é usar --image=nginx:alpine no kubectl create deployment, que o cluster baixa sozinho.',
       'Load lesson 3’s image into the cluster and ask for 3 replicas (skipped lesson 3? use --image=nginx:alpine and skip kind load):\nkind load docker-image api-pedidos:1.0 --name escola\nkubectl create deployment api --image=api-pedidos:1.0 --replicas=3\nkubectl get pods -o wide\nIf kind load fails (it happens with the containerd image store, the Docker Engine 29 default), use a tar file instead:\ndocker save --platform linux/amd64 -o api.tar api-pedidos:1.0\nkind load image-archive api.tar --name escola\n(use linux/arm64 on Apple Silicon Macs). Another way out is --image=nginx:alpine in kubectl create deployment, which the cluster pulls by itself.'),
     T('Apague um pod e veja outro ocupar o lugar:\nkubectl delete pod NOME-DE-UM-POD\nkubectl get pods',
       'Delete a pod and watch another take its place:\nkubectl delete pod NAME-OF-A-POD\nkubectl get pods'),
     T('Agora derrube um nó inteiro (é só um contêiner) e acompanhe por uns 6 minutos; Ctrl+C sai do -w:\ndocker stop escola-worker\nkubectl get nodes\nkubectl get pods -o wide -w\nQuando terminar: docker start escola-worker\nSe o escola-worker não voltar a Ready, recrie o cluster: kind delete cluster --name escola e crie de novo como no passo 1 (a lição 6 usa este cluster).',
       'Now take down a whole node (it’s just a container) and watch for about 6 minutes; Ctrl+C exits -w:\ndocker stop escola-worker\nkubectl get nodes\nkubectl get pods -o wide -w\nWhen done: docker start escola-worker\nIf escola-worker doesn’t come back to Ready, recreate the cluster: kind delete cluster --name escola and create it again as in step 1 (lesson 6 uses this cluster).')],
   'ok': T('o pod apagado é substituído em segundos; com o escola-worker parado, ele aparece como NotReady e, depois de uns 5 minutos (a tolerância padrão), as réplicas que estavam nele são recriadas no nó que sobrou, e você volta a ter 3 Running (as antigas podem ficar como Terminating até o nó voltar).',
           'the deleted pod is replaced within seconds; with escola-worker stopped, it shows as NotReady and, after about 5 minutes (the default toleration), the replicas that were on it are recreated on the remaining node, and you’re back to 3 Running (the old ones may stay Terminating until the node returns).')}}

t5 = {'pt': {'objectives': ['Listar o que muda quando se passa de uma máquina para várias.', 'Entender estado desejado e reconciliação.', 'Reconhecer limites e custos de um orquestrador.'], 'minutes': 20,
  'activity': 'Gerente de frota: um aluno é o orquestrador e tem um cartaz "quero 3 trucks servindo". Outros três são trucks. O professor "quebra" um truck, depois pede o triplo de clientes, depois troca o cardápio. O orquestrador só pode dar ordens olhando o cartaz e a sala. Na segunda rodada, sem orquestrador, o professor precisa ir pessoalmente até cada truck.',
  'discussion': ['Que tarefas manuais da sua equipe seguem o padrão "alguém percebe e conserta"?', 'Quando um orquestrador é exagero para o tamanho do problema?'],
  'misconceptions': ['"Kubernetes escala sozinho." Ele recria o que morreu; escalar com a carga precisa de um autoscaler configurado.', '"Com Kubernetes nunca cai." Com uma réplica ou um nó só, ainda cai; o orquestrador só corrige mais rápido.']},
 'en': {'objectives': ['List what changes when going from one machine to many.', 'Understand desired state and reconciliation.', 'Recognize an orchestrator’s limits and costs.'], 'minutes': 20,
  'activity': 'Fleet manager: one student is the orchestrator and holds a sign "I want 3 trucks serving". Three others are trucks. The teacher "breaks" a truck, then asks for three times the customers, then changes the menu. The orchestrator can only give orders by looking at the sign and the room. In round two, with no orchestrator, the teacher has to walk to each truck in person.',
  'discussion': ['Which manual tasks on your team follow the "someone notices and fixes it" pattern?', 'When is an orchestrator overkill for the size of the problem?'],
  'misconceptions': ['"Kubernetes scales by itself." It recreates what died; scaling with load needs a configured autoscaler.', '"With Kubernetes nothing goes down." With one replica or one node, it still goes down; the orchestrator just fixes it faster.']}}
write('05-por-que-orquestrar', s5, loc5('pt'), loc5('en'), t5)

# ================================================================== 6 · o que é um cluster
COMPS = ['apiserver', 'etcd', 'controllers', 'scheduler', 'kubelet']
CP_PODS = [('kube-apiserver', 'apiserver'), ('etcd', 'etcd'), ('kube-controller-manager', 'controllers'), ('kube-scheduler', 'scheduler')]
NEW_SUF = ['b8n3r', 't6w1c', 'h9j5d', 'p3v8s', 'k7r2f', 'z1m6q']
def l6_scenario(stopped, r):
  w1 = {'name': 'escola-worker', 'status': 'Ready', 'pods': [{'name': 'api-7d9f-x2k9p', 'status': 'Running'}]}
  w2 = {'name': 'escola-worker2', 'status': 'Ready', 'pods': [{'name': 'api-7d9f-m4q7z', 'status': 'Running'}]}
  cp = {'name': 'escola-control-plane', 'status': 'Ready',
        'pods': [{'name': n, 'status': 'Stopped', 'tone': 'bad'} if c == stopped else {'name': n, 'status': 'Running'} for n, c in CP_PODS]}
  new_n = r - 2
  new = [f'api-7d9f-{NEW_SUF[j]}' for j in range(new_n)]
  pending, rows = [], []
  if stopped == 'kubelet':
    w2['status'] = 'NotReady'; w2['pods'][0]['tone'] = 'warn'
  if stopped == 'none':
    for j, n in enumerate(new): (w1 if len(w1['pods']) <= len(w2['pods']) else w2)['pods'].append({'name': n, 'status': 'Running'})
  elif stopped == 'scheduler':
    pending = new
  elif stopped == 'kubelet':
    for n in new:
      if len(w1['pods']) < CAP: w1['pods'].append({'name': n, 'status': 'Running'})
      else: pending.append(n)
  nodes = [cp, w1, w2]
  if pending: nodes.append({'name': '@unscheduled', 'status': '', 'tone': 'warn', 'pods': [{'name': n, 'status': 'Pending'} for n in pending]})
  running = sum(1 for nd in (w1, w2) for p in nd['pods'] if p['status'] == 'Running')
  lines = []
  if stopped not in ('apiserver', 'etcd'):
    lines = ['$ kubectl get pods -o wide', '~NAME             READY   STATUS    NODE']
    for nd in (w1, w2):
      for p in nd['pods']: lines.append(f"+{p['name']}   1/1     Running   {nd['name']}")
    for n in pending: lines.append(f'?{n}   0/1     Pending   <none>')
  return {'nodes': nodes, 'running': running, 'pending': len(pending), 'missing': r - running, 'lines': lines}
L6_TABLE = {f'{c}-{r}': l6_scenario(c, r) for c in ['none'] + COMPS for r in range(3, 9)}
STEP_IDX = {'none': 99, 'apiserver': 1, 'etcd': 2, 'controllers': 3, 'scheduler': 4, 'kubelet': 5}
def flow_step(i, label):
  if i == 5:
    return {'label': label, 'sub': f"=stopped == 'kubelet' ? '@subKubeletHalf' : (stopIdx < 5 ? '@subNever' : '@sub5')",
            'tone': "=stopped == 'kubelet' ? 'warn' : (stopIdx < 5 ? 'dim' : 'ok')"}
  return {'label': label, 'sub': f"=stopIdx == {i} ? '@subStopped' : (stopIdx < {i} ? '@subNever' : '@sub{i}')",
          'tone': f"=stopIdx == {i} ? 'bad' : (stopIdx < {i} ? 'dim' : 'ok')"}

s6 = step('k8s-o-que-e-cluster', 6, TRACK, 20, ['cluster', 'control-plane', 'etcd', 'scheduler', 'kubelet', 'apiserver'], ['k8s-por-que-orquestrar'], SIM,
  loc('escalar', 'scale'),
  {'name': 'text', 'required': False, 'default': loc('api', 'api'), 'ui': 'text'},
  [flag('replicas', 'replicas', 'replicas', 'int', min=3, max=8, default=4, ui='slider'),
   flag('stopped', 'parado', 'stopped', 'enum',
        options=[opt('none', 'nenhum', 'none'), opt('apiserver', 'apiserver', 'apiserver'), opt('etcd', 'etcd', 'etcd'),
                 opt('controllers', 'controller-manager', 'controller-manager'), opt('scheduler', 'scheduler', 'scheduler'), opt('kubelet', 'kubelet', 'kubelet')],
        default='none', ui='select')],
  {'options': ['kubectl', 'scheduler', 'kubelet', 'etcd'], 'answer': 'scheduler'}, 'stuck',
  {'live': True,
   'consts': {'scenarios': L6_TABLE, 'stopIndex': STEP_IDX, 'oldPods': 2,
              'compNames': {'none': '', 'apiserver': 'kube-apiserver', 'etcd': 'etcd', 'controllers': 'kube-controller-manager', 'scheduler': 'kube-scheduler', 'kubelet': 'kubelet (escola-worker2)'},
              'refused': '!The connection to the server 127.0.0.1:43215 was refused - did you specify the right host or port?'},
   'compute': {
     'sc': "lookup(scenarios, stopped + '-' + replicas, null)",
     'runningN': 'sc.running', 'pendingN': 'sc.pending', 'missingN': 'sc.missing', 'newN': 'replicas - 2',
     'stopIdx': 'lookup(stopIndex, stopped, 99)',
     'apiDownB': "stopped == 'apiserver' || stopped == 'etcd'",
     'comp': "lookup(compNames, stopped, '')",
     'stuckB': 'missingN > 0',
     'scaleOut': "stopped == 'apiserver' ? refused : (stopped == 'etcd' ? '@etcdErr' : '+deployment.apps/' + text + ' scaled')",
     'termLines': "concat(['$ kubectl scale deployment ' + text + ' --replicas=' + replicas, scaleOut], sc.lines)",
     'noteKey': "'@n_' + stopped"},
   'cases': [
     {'when': 'stuckB', 'flags': ['stuck']},
     {'when': '!stuckB', 'flags': ['scheduled']},
     {'when': 'apiDownB', 'flags': ['apiDown']},
     {'when': "stopped == 'kubelet'", 'flags': ['nodeNotReady']},
     {'when': 'true', 'vars': {'runningN': 'runningN', 'pendingN': 'pendingN', 'missingN': 'missingN', 'newN': 'newN', 'comp': 'comp'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@runningM', 'value': "=runningN + ' / ' + replicas", 'tone': "=stuckB ? 'bad' : 'ok'"},
       {'label': '@missingM', 'value': '=missingN', 'format': 'int', 'tone': "=missingN > 0 ? 'bad' : 'dim'"},
       {'label': '@oldM', 'value': '=oldPods', 'format': 'int', 'tone': 'ok'},
       {'label': '@kubectlM', 'value': "=apiDownB ? '@kErr' : '@kOk'", 'tone': "=apiDownB ? 'bad' : 'ok'"}]},
     {'type': 'flow', 'label': '@flowLabel', 'steps': [
       {'label': 'kubectl', 'sub': "='scale --replicas=' + replicas", 'tone': 'info'},
       flow_step(1, 'kube-apiserver'), flow_step(2, 'etcd'), flow_step(3, 'kube-controller-manager'), flow_step(4, 'kube-scheduler'), flow_step(5, 'kubelet')]},
     {'type': 'cluster', 'label': '@clusterLabel', 'nodes': '=sc.nodes'},
     {'type': 'terminal', 'label': '@termLabel', 'lines': '=termLines'},
     {'type': 'note', 'tone': "=stuckB ? 'bad' : (stopped == 'none' ? 'ok' : 'warn')", 'text': '=noteKey'}]})

def loc6(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  return {
  'title': T('O que é um cluster', 'What a cluster is'),
  'subtitle': T('O escritório central e as cozinhas: quem anota, quem despacha e quem liga o fogão', 'The head office and the kitchens: who writes it down, who dispatches and who lights the stove'),
  'mission': T('O cluster da escola tem um nó de controle (escola-control-plane) e dois workers. O Deployment api já tem 2 pods rodando. Você vai pedir mais réplicas com kubectl scale e seguir o pedido pelo caminho: kube-apiserver, etcd, kube-controller-manager, kube-scheduler e kubelet. Depois, pare um componente de cada vez e veja onde o pedido empaca e o que continua de pé.',
               'The school cluster has a control-plane node (escola-control-plane) and two workers. The api Deployment already has 2 pods running. You’ll ask for more replicas with kubectl scale and follow the request along the path: kube-apiserver, etcd, kube-controller-manager, kube-scheduler and kubelet. Then stop one component at a time and see where the request gets stuck and what keeps running.'),
  'predict': {'question': T('quem decide em qual worker cada pod novo vai rodar?', 'who decides which worker each new pod will run on?'),
    'options': {'kubectl': T('O kubectl, na sua máquina', 'kubectl, on your machine'), 'scheduler': T('O kube-scheduler', 'The kube-scheduler'),
                'kubelet': T('O kubelet de cada worker, disputando', 'Each worker’s kubelet, competing'), 'etcd': T('O etcd', 'etcd')}},
  'feedback': {'right': T('isso! O controller-manager cria os pods sem nó; o kube-scheduler procura pods sem nó e escolhe um worker para cada (olhando recursos, regras e o que já está em cada um). Só depois o kubelet daquele worker liga os contêineres.',
                          'right! The controller-manager creates the pods with no node; the kube-scheduler looks for pods with no node and picks a worker for each (looking at resources, rules and what’s already there). Only then does that worker’s kubelet start the containers.'),
               'wrong': T('é o kube-scheduler. O kubectl só manda o pedido ao apiserver, o etcd só guarda o estado, e o kubelet só liga o que foi atribuído ao nó dele. Escolher o nó é o trabalho do scheduler.',
                          'it’s the kube-scheduler. kubectl only sends the request to the apiserver, etcd only stores the state, and the kubelet only starts what was assigned to its node. Picking the node is the scheduler’s job.'),
               'skipped': T('sem palpite? Rode e leia a linha do tempo, componente por componente.', 'no guess? Run it and read the timeline, component by component.')},
  'coach': {'ui': T('palpite anotado. Rode sem nada parado e leia o caminho do pedido.', 'guess noted. Run with nothing stopped and read the request’s path.'),
            'cmd': T('palpite anotado. Rode escalar e leia o caminho do pedido, componente por componente.', 'guess noted. Run scale and read the request’s path, component by component.')},
  'tryNext': {'ui': T('Pare o kubelet: o cluster contorna o worker doente. Depois pare o controller-manager: o kubectl diz "scaled", mas nada acontece.', 'Stop the kubelet: the cluster works around the sick worker. Then stop the controller-manager: kubectl says "scaled", but nothing happens.'),
              'cmd': T('Rode escalar --parado kubelet (o cluster contorna o worker doente) e depois escalar --parado controller-manager (o kubectl diz scaled, mas nada acontece).', 'Run scale --stopped kubelet (the cluster works around the sick worker) and then scale --stopped controller-manager (kubectl says scaled, but nothing happens).')},
  'why': {'simples': T('O cluster é a marmitaria inteira: o escritório central (o control plane) e as cozinhas (os nós). No escritório tem a recepção que atende todo pedido (kube-apiserver), o caderno oficial onde tudo fica anotado (etcd), os supervisores que conferem se o anotado está acontecendo (controller-manager) e o despachante que decide qual cozinha faz cada marmita (kube-scheduler). Em cada cozinha tem uma chefe (kubelet) que recebe a lista e liga o fogão (o runtime de contêiner).\nSe o escritório fecha por uma hora, as cozinhas continuam cozinhando o que já estava na lista; só não entra pedido novo.',
                       'The cluster is the whole lunchbox business: the head office (the control plane) and the kitchens (the nodes). In the office there’s the front desk that takes every request (kube-apiserver), the official notebook where everything is written down (etcd), the supervisors who check that what’s written is happening (controller-manager) and the dispatcher who decides which kitchen makes each lunchbox (kube-scheduler). In each kitchen there’s a head cook (kubelet) who gets the list and lights the stove (the container runtime).\nIf the office closes for an hour, the kitchens keep cooking what was already on the list; no new orders get in, that’s all.'),
          'dev': T('Tudo passa pelo kube-apiserver: o kubectl, os controladores, o scheduler e os kubelets só conversam com ele, e é ele quem lê e grava no etcd, o banco chave-valor consistente onde mora o estado do cluster.\nO caminho de um kubectl scale: o apiserver valida e grava replicas: 4; o controlador de ReplicaSet, dentro do kube-controller-manager, vê que faltam 2 pods e cria os objetos; o kube-scheduler encontra pods sem nó e escolhe um para cada (recursos pedidos, afinidades, taints); o kubelet daquele nó vê o pod atribuído e pede ao runtime (containerd ou CRI-O, pela interface CRI) para baixar a imagem e subir os contêineres. O kube-proxy, opcional quando o plugin de rede faz esse papel, mantém as regras de rede dos Services.',
                   'Everything goes through the kube-apiserver: kubectl, the controllers, the scheduler and the kubelets only talk to it, and it’s the one that reads and writes etcd, the consistent key-value store where the cluster state lives.\nThe path of a kubectl scale: the apiserver validates and stores replicas: 4; the ReplicaSet controller, inside kube-controller-manager, sees 2 pods missing and creates the objects; the kube-scheduler finds pods with no node and picks one for each (requested resources, affinities, taints); that node’s kubelet sees the assigned pod and asks the runtime (containerd or CRI-O, through the CRI interface) to pull the image and start the containers. kube-proxy, optional when the network plugin takes over that role, keeps the network rules for Services.'),
          'especialista': T('Cada peça é um laço de reconciliação que observa o apiserver e age sobre a diferença; por isso o sistema é eventualmente consistente e tolera reinícios de componentes. O etcd usa Raft e precisa de quórum: com 3 membros aguenta perder 1, com 5 aguenta 2; sem quórum ele não aceita escrita, e o cluster para de mudar.\nEm produção o control plane roda replicado (vários apiservers atrás de um balanceador; scheduler e controller-manager com eleição de líder), e serviços gerenciados como o AKS cuidam disso por você. No kind e no kubeadm, os componentes do control plane são pods estáticos: o kubelet do nó de controle os sobe a partir de /etc/kubernetes/manifests, sem depender do próprio apiserver, e é por isso que dá para desligar o scheduler tirando um arquivo da pasta.',
                            'Each piece is a reconciliation loop that watches the apiserver and acts on the difference; that’s why the system is eventually consistent and tolerates component restarts. etcd uses Raft and needs quorum: with 3 members it survives losing 1, with 5 it survives 2; without quorum it accepts no writes, and the cluster stops changing.\nIn production the control plane runs replicated (several apiservers behind a load balancer; scheduler and controller-manager with leader election), and managed services like AKS handle that for you. In kind and kubeadm, the control-plane components are static pods: the control-plane node’s kubelet starts them from /etc/kubernetes/manifests, without depending on the apiserver itself, which is why you can turn the scheduler off by moving a file out of that folder.')},
  'break': {'mission': {'ui': T('hora de quebrar: pare o kube-scheduler.', 'time to break it: stop the kube-scheduler.'),
                        'cmd': T('hora de quebrar: rode escalar --parado scheduler', 'time to break it: run scale --stopped scheduler')},
            'success': T('Quebrou: você pediu {replicas} réplicas e só {runningN} estão rodando; {missingN} pod(s) novo(s) não chegaram a rodar porque o {comp} está fora. Repare: os 2 pods antigos continuam rodando. O que para é a mudança, não o que já estava de pé.',
                         'Broken: you asked for {replicas} replicas and only {runningN} are running; {missingN} new pod(s) never got to run because {comp} is down. Notice: the 2 old pods keep running. What stops is change, not what was already up.'),
            'calm': T('{runningN} de {replicas} pods rodando. Para quebrar, pare o kube-scheduler.', '{runningN} of {replicas} pods running. To break it, stop the kube-scheduler.')},
  'hints': {'ui': T(['Escolha quantas réplicas quer e que componente parar; a linha do tempo mostra onde o pedido empaca.', 'Sem o scheduler, os pods novos existem mas ninguém escolhe um nó para eles.', 'Pare o scheduler.'],
                    ['Pick how many replicas you want and which component to stop; the timeline shows where the request gets stuck.', 'Without the scheduler, the new pods exist but nobody picks a node for them.', 'Stop the scheduler.']),
            'cmd': T(['O Deployment vai entre aspas; --replicas e --parado são opcionais.', '--parado aceita nenhum, apiserver, etcd, controller-manager, scheduler ou kubelet.', 'escalar --parado scheduler'],
                     ['The Deployment goes in quotes; --replicas and --stopped are optional.', '--stopped takes none, apiserver, etcd, controller-manager, scheduler or kubelet.', 'scale --stopped scheduler'])},
  'errors': {'notInEnum.stopped': T('Use nenhum, apiserver, etcd, controller-manager, scheduler ou kubelet.', 'Use none, apiserver, etcd, controller-manager, scheduler or kubelet.'),
             'belowMin.replicas': T('O api já tem 2 réplicas; nesta lição a gente só aumenta. Peça 3 ou mais.', 'api already has 2 replicas; in this lesson we only scale up. Ask for 3 or more.'),
             'aboveMax.replicas': T('Até 8: nesta simulação cada worker cabe 4 pods.', 'Up to 8: in this simulation each worker fits 4 pods.')},
  'controls': {'arg': T('Deployment', 'Deployment'), 'replicas': T('Réplicas desejadas', 'Desired replicas'), 'stopped': T('Componente parado', 'Stopped component')},
  'scene': {'label': T('Um kubectl scale, do começo ao fim', 'One kubectl scale, end to end'), 'empty': T('Rode para escalar.', 'Run to scale.'),
    'runningM': T('pods rodando / pedidos', 'pods running / requested'), 'missingM': T('pods novos que não rodaram', 'new pods that didn’t run'),
    'oldM': T('pods antigos ainda atendendo', 'old pods still serving'), 'kubectlM': T('o kubectl', 'kubectl'),
    'kOk': T('respondeu', 'answered'), 'kErr': T('deu erro', 'failed'),
    'flowLabel': T('O caminho do pedido', 'The request’s path'),
    'sub1': T('valida e repassa', 'validates and passes it on'), 'sub2': T('grava replicas: {replicas}', 'stores replicas: {replicas}'),
    'sub3': T('cria {newN} pod(s) sem nó', 'creates {newN} pod(s) with no node'), 'sub4': T('escolhe o nó de cada pod', 'picks each pod’s node'),
    'sub5': T('liga os contêineres', 'starts the containers'), 'subKubeletHalf': T('escola-worker2 sem kubelet; o escola-worker assume', 'escola-worker2 has no kubelet; escola-worker takes over'),
    'subStopped': T('PARADO', 'STOPPED'), 'subNever': T('nem ficou sabendo', 'never heard about it'),
    'clusterLabel': T('Nós e pods (simulado)', 'Nodes and pods (simulated)'), 'unscheduled': T('sem nó (Pending)', 'no node (Pending)'),
    'termLabel': T('Terminal (kubectl get pods com colunas resumidas)', 'Terminal (kubectl get pods with trimmed columns)'),
    'etcdErr': T('! erro do servidor: o kube-apiserver não conseguiu gravar no etcd (simulado)', '! server error: kube-apiserver couldn’t write to etcd (simulated)'),
    'n_none': T('Tudo no lugar: {runningN} de {replicas} pods rodando. O kubectl falou só com o apiserver; o resto foi cada componente fazendo a sua parte.', 'Everything in place: {runningN} of {replicas} pods running. kubectl only talked to the apiserver; the rest was each component doing its part.'),
    'n_apiserver': T('Sem o kube-apiserver, ninguém conversa com ninguém: o kubectl leva "connection refused". Os 2 pods antigos seguem atendendo, porque contêiner rodando não depende do control plane.', 'Without kube-apiserver, nobody talks to anybody: kubectl gets "connection refused". The 2 old pods keep serving, because a running container doesn’t depend on the control plane.'),
    'n_etcd': T('O apiserver está de pé, mas não tem onde gravar: sem o etcd, o pedido não vira estado e nada muda. Os pods antigos nem percebem.', 'The apiserver is up, but has nowhere to write: without etcd, the request never becomes state and nothing changes. The old pods don’t even notice.'),
    'n_controllers': T('O kubectl respondeu "scaled" e o etcd guardou replicas: {replicas}, mas sem o controller-manager ninguém criou os {newN} pods. Pedido anotado não é pedido cumprido.', 'kubectl answered "scaled" and etcd stored replicas: {replicas}, but without the controller-manager nobody created the {newN} pods. A request written down isn’t a request fulfilled.'),
    'n_scheduler': T('Os {newN} pods novos existem, mas ficaram Pending, sem nó: ninguém escolheu uma cozinha para eles. Os antigos seguem Running.', 'The {newN} new pods exist, but stayed Pending with no node: nobody picked a kitchen for them. The old ones stay Running.'),
    'n_kubelet': T('O escola-worker2 parou de dar notícias e virou NotReady; o scheduler mandou os pods novos para o escola-worker, e ficaram {runningN} de {replicas} rodando. O pod antigo do worker2 segue rodando, mas sem ninguém confirmando.', 'escola-worker2 stopped reporting and turned NotReady; the scheduler sent the new pods to escola-worker, leaving {runningN} of {replicas} running. The old pod on worker2 keeps running, but with nobody confirming it.')},
  'data': {},
  'recipe': {'steps': [
     T('Use o cluster da lição 5 (ou crie um com kind create cluster --name escola --config kind.yaml e o Deployment com kubectl create deployment api --image=nginx:alpine --replicas=3). Veja os nós e os componentes do control plane:\nkubectl get nodes\nkubectl get pods -n kube-system -o wide',
       'Use the cluster from lesson 5 (or create one with kind create cluster --name escola --config kind.yaml and the Deployment with kubectl create deployment api --image=nginx:alpine --replicas=3). Look at the nodes and the control-plane components:\nkubectl get nodes\nkubectl get pods -n kube-system -o wide'),
     T('Repare nos nomes etcd-escola-control-plane, kube-apiserver-escola-control-plane, kube-controller-manager-… e kube-scheduler-…: são pods estáticos que o kubelet do nó de controle sobe a partir de arquivos. Veja os arquivos dentro do nó (que é um contêiner):\ndocker exec escola-control-plane ls /etc/kubernetes/manifests',
       'Notice the names etcd-escola-control-plane, kube-apiserver-escola-control-plane, kube-controller-manager-… and kube-scheduler-…: they’re static pods the control-plane node’s kubelet starts from files. Look at the files inside the node (which is a container):\ndocker exec escola-control-plane ls /etc/kubernetes/manifests'),
     T('Desligue o scheduler tirando o manifesto da pasta. Espere uns segundos e confira que ele sumiu da lista:\ndocker exec escola-control-plane mv /etc/kubernetes/manifests/kube-scheduler.yaml /root/\nkubectl get pods -n kube-system',
       'Turn the scheduler off by moving its manifest out of the folder. Wait a few seconds and check it’s gone from the list:\ndocker exec escola-control-plane mv /etc/kubernetes/manifests/kube-scheduler.yaml /root/\nkubectl get pods -n kube-system'),
     T('Peça mais réplicas e veja o que acontece:\nkubectl scale deployment api --replicas=5\nkubectl get pods -o wide', 'Ask for more replicas and see what happens:\nkubectl scale deployment api --replicas=5\nkubectl get pods -o wide'),
     T('Devolva o scheduler e olhe de novo:\ndocker exec escola-control-plane mv /root/kube-scheduler.yaml /etc/kubernetes/manifests/\nkubectl get pods -o wide', 'Put the scheduler back and look again:\ndocker exec escola-control-plane mv /root/kube-scheduler.yaml /etc/kubernetes/manifests/\nkubectl get pods -o wide')],
   'ok': T('com o manifesto fora, o kube-scheduler some de kube-system, os pods novos ficam Pending com NODE <none> e os antigos continuam Running; quando o arquivo volta, o scheduler reaparece e os Pending viram Running.',
           'with the manifest out, kube-scheduler disappears from kube-system, the new pods stay Pending with NODE <none> and the old ones keep Running; when the file comes back, the scheduler reappears and the Pending pods turn Running.')}}

t6 = {'pt': {'objectives': ['Nomear os componentes do control plane e dos nós.', 'Seguir um pedido do kubectl até o contêiner rodando.', 'Prever o que para (e o que não para) quando um componente cai.'], 'minutes': 20,
  'activity': 'Escritório da marmitaria: distribua papéis (recepção = apiserver, caderno = etcd, supervisor = controller-manager, despachante = scheduler, chefes de cozinha = kubelets). Um aluno pede "mais 2 marmitas". Rodem a cena; depois tirem um papel de cada vez e vejam onde o pedido empaca.',
  'discussion': ['Por que só o apiserver pode falar com o etcd?', 'O que deveria ser monitorado no control plane para descobrir problemas antes dos usuários?'],
  'misconceptions': ['"Se o control plane cai, os apps caem." Os contêineres que já rodam continuam; param só as mudanças.', '"O kubectl liga os contêineres." Ele só conversa com o apiserver; quem liga é o kubelet de cada nó.']},
 'en': {'objectives': ['Name the control-plane and node components.', 'Follow a request from kubectl to a running container.', 'Predict what stops (and what doesn’t) when a component goes down.'], 'minutes': 20,
  'activity': 'Lunchbox office: hand out roles (front desk = apiserver, notebook = etcd, supervisor = controller-manager, dispatcher = scheduler, head cooks = kubelets). A student asks for "2 more lunchboxes". Play the scene; then remove one role at a time and see where the request gets stuck.',
  'discussion': ['Why may only the apiserver talk to etcd?', 'What should be monitored on the control plane to find problems before users do?'],
  'misconceptions': ['"If the control plane goes down, the apps go down." Containers already running keep going; only changes stop.', '"kubectl starts the containers." It only talks to the apiserver; each node’s kubelet starts them.']}}
write('06-o-que-e-um-cluster', s6, loc6('pt'), loc6('en'), t6)

# ================================================================== 7 · missão: empacotar a API
def concat_rows(items):
  rows = ', '.join(f'[[{l}, {e}]]' if c == 'true' else f'{c} ? [[{l}, {e}]] : []' for c, l, e, t in items)
  tones = ', '.join(f'[{t}]' if c == 'true' else f'{c} ? [{t}] : []' for c, l, e, t in items)
  return f'concat({rows})', f'concat({tones})'
ROWS7 = [
  ('isD', 'lBuild', "'@eBuild'", "'ok'"),
  ('!isD', "lookup(fromL, base, '')", "base == 'latest' ? '@eFromLatest' : (base == 'full' ? '@eFromFull' : '@eFromSlim')", "base == 'slim' ? 'ok' : 'bad'"),
  ('!isD', 'lEnvProd', "'@eEnvProd'", "'neutral'"),
  ("!isD && secret == 'image'", 'lSecret', "'@eSecret'", "'bad'"),
  ('true', 'lWork', "'@eWork'", "'neutral'"),
  ('isDeps', 'lCopyPkg', "'@eCopyPkg'", "'ok'"),
  ('isDeps', 'lNpm', "'@eNpmFirst'", "'ok'"),
  ('true', 'lCopyAll', "isDeps ? (ignore ? '@eCopyLast' : '@eCopyLastNoIgnore') : (ignore ? '@eCopyFirst' : '@eCopyFirstNoIgnore')", "isDeps && ignore ? 'ok' : 'bad'"),
  ('!isDeps', 'lNpm', "'@eNpmAfter'", "'bad'"),
  ('isD', 'isRoot ? lDistroRoot : lDistroNon', "isRoot ? '@eDistroRoot' : '@eDistroNon'", "isRoot ? 'bad' : 'ok'"),
  ('isD', 'lEnvProd', "'@eEnvProd'", "'neutral'"),
  ("isD && secret == 'image'", 'lSecret', "'@eSecret'", "'bad'"),
  ('isD', 'lWork', "'@eWork2'", "'neutral'"),
  ('isD', 'lCopyFrom', "'@eCopyFrom'", "'ok'"),
  ('!isD && !isRoot', 'lUser', "'@eUser'", "'ok'"),
  ('!isD && isRoot', "'@lNoUser'", "'@eNoUser'", "'bad'"),
  ('true', 'lExpose', "'@eExpose'", "'neutral'"),
  ('true', 'isD ? lCmdD : lCmd', "isD ? '@eCmdD' : '@eCmd'", "'neutral'")]
ROWS7_EXPR, TONES7_EXPR = concat_rows(ROWS7)

s7 = step('k8s-missao-empacotar-api', 7, TRACK, 25, ['missao', 'dockerfile', 'seguranca', 'multi-stage', 'distroless', 'cache'],
  ['k8s-imagem-e-camadas', 'k8s-dockerfile', 'k8s-registro'], SIM,
  loc('empacotar', 'package'),
  {'name': 'text', 'required': False, 'default': loc('api-pedidos', 'api-pedidos'), 'ui': 'text'},
  [flag('base', 'base', 'base', 'enum',
        options=[opt('latest', 'node:latest', 'node:latest'), opt('full', 'node:24', 'node:24'), opt('slim', 'node:24-slim', 'node:24-slim'), opt('distroless', 'distroless', 'distroless')],
        default='latest', ui='select'),
   flag('order', 'ordem', 'order', 'enum', options=[opt('copyAll', 'copia-tudo', 'copy-all'), opt('depsFirst', 'deps-primeiro', 'deps-first')], default='copyAll', ui='select'),
   flag('user', 'usuario', 'user', 'enum', options=[opt('root', 'root', 'root'), opt('nonroot', 'nao-root', 'non-root')], default='root', ui='select'),
   flag('secret', 'segredo', 'secret', 'enum', options=[opt('image', 'imagem', 'image'), opt('runtime', 'execucao', 'runtime')], default='image', ui='select'),
   flag('ignore', 'dockerignore', 'dockerignore', 'bool', default=False, ui='switch'),
   flag('tag', 'tag', 'tag', 'enum', options=[opt('latest', 'latest', 'latest'), opt('version', '1.0.0', '1.0.0')], default='latest', ui='select')],
  None, 'packed',
  {'live': True,
   'consts': {'baseSize': {'latest': 1100, 'full': 1100, 'slim': 220, 'distroless': 150}, 'depsMB': 60, 'codeMB': 2, 'nmMB': 300, 'gitMB': 70, 'npmS': 84,
              'fromL': {'latest': 'FROM node:latest', 'full': 'FROM node:24', 'slim': 'FROM node:24-slim'},
              'lBuild': 'FROM node:24-trixie-slim AS build', 'lDistroRoot': 'FROM gcr.io/distroless/nodejs24-debian13',
              'lDistroNon': 'FROM gcr.io/distroless/nodejs24-debian13:nonroot', 'lEnvProd': 'ENV NODE_ENV=production',
              'lSecret': 'ENV DB_PASSWORD=marmita123', 'lWork': 'WORKDIR /app', 'lCopyPkg': 'COPY package.json package-lock.json ./',
              'lNpm': 'RUN npm ci --omit=dev', 'lCopyAll': 'COPY . .', 'lCopyFrom': 'COPY --from=build /app /app', 'lUser': 'USER node',
              'lExpose': 'EXPOSE 3000', 'lCmd': 'CMD ["node", "server.js"]', 'lCmdD': 'CMD ["server.js"]'},
   'compute': {
     'isD': "base == 'distroless'",
     'isDeps': "order == 'depsFirst'",
     'isRoot': "user == 'root'",
     'junkMB': 'ignore ? 0 : (isD && !isDeps ? gitMB : nmMB + gitMB)',
     'imgMB': 'lookup(baseSize, base, 0) + depsMB + codeMB + junkMB',
     'ctxMB': 'ignore ? 2 : 380',
     'rebuildS': 'round((ignore ? 0.1 : 4) + (isDeps ? 0 : npmS) + 2 + (isD ? 1 : 0), 1)',
     'secretsN': "(secret == 'image' ? 1 : 0) + (ignore ? 0 : 1)",
     'tagStr': "tag == 'latest' ? 'latest' : '1.0.0'",
     'okBase': "base == 'slim' || isD",
     'okSize': 'imgMB <= 300', 'okCache': 'isDeps', 'okUser': '!isRoot', 'okSecret': 'secretsN == 0',
     'okPin': "base != 'latest' && tag != 'latest'",
     'okCount': '(okSize ? 1 : 0) + (okCache ? 1 : 0) + (okUser ? 1 : 0) + (okSecret ? 1 : 0) + (okPin ? 1 : 0)',
     'allOk': 'okCount == 5',
     'userName': "isRoot ? 'root' : (isD ? 'nonroot' : 'node')",
     'dfRows': ROWS7_EXPR, 'dfTones': TONES7_EXPR},
   'cases': [
     {'when': 'allOk', 'flags': ['packed']},
     {'when': 'secretsN > 0', 'flags': ['secretLeak']},
     {'when': '!okSize', 'flags': ['fatImage']},
     {'when': 'true', 'vars': {'imgMB': 'imgMB', 'rebuildS': 'round(rebuildS)', 'secretsN': 'secretsN', 'okCount': 'okCount', 'tagStr': 'tagStr'}}],
   'widgets': [
     {'type': 'checks', 'label': '@checks', 'items': [
       {'label': '@cSize', 'ok': '=okSize', 'why': "=okBase ? '@cSizeJunk' : '@cSizeBase'"},
       {'label': '@cCache', 'ok': '=okCache', 'why': '@cCacheWhy'},
       {'label': '@cUser', 'ok': '=okUser', 'why': "=isD ? '@cUserD' : '@cUserN'"},
       {'label': '@cSecret', 'ok': '=okSecret', 'why': "=secret == 'image' ? (ignore ? '@cSecEnv' : '@cSecBoth') : '@cSecFile'"},
       {'label': '@cPin', 'ok': '=okPin', 'why': "=base == 'latest' ? (tag == 'latest' ? '@cPinBoth' : '@cPinBase') : '@cPinTag'"}]},
     {'type': 'metrics', 'items': [
       {'label': '@sizeM', 'value': '=imgMB', 'format': 'int', 'tone': "=okSize ? 'ok' : 'bad'"},
       {'label': '@rebuildM', 'value': '=rebuildS', 'tone': "=okCache ? 'ok' : 'bad'"},
       {'label': '@secretsM', 'value': '=secretsN', 'format': 'int', 'tone': "=okSecret ? 'ok' : 'bad'"},
       {'label': '@userM', 'value': '=userName', 'tone': "=okUser ? 'ok' : 'bad'"}]},
     {'type': 'table', 'label': '@dfLabel', 'columns': ['@colLine', '@colWhy'], 'rows': '=dfRows', 'tones': '=dfTones', 'caption': '@dfCap'},
     {'type': 'terminal', 'label': '@terminal', 'lines': [
       "='$ docker build -t ' + text + ':' + tagStr + ' .'",
       "=ignore ? '@tIgnoreOn' : '@tIgnoreOff'",
       "=okCache ? '@tCacheOk' : '@tCacheBad'",
       "=isRoot ? '@tRoot' : '@tNonroot'",
       "=okSecret ? '@tSecOk' : '@tSecBad'",
       "=okSize ? '@tSizeOk' : '@tSizeBad'",
       "=okPin ? '@tPinOk' : '@tPinBad'"]}]},
  kind='mission')

def loc7(L):
  pt = L == 'pt'; T = lambda a, b: a if pt else b
  df_slim = ('FROM node:24-slim\nENV NODE_ENV=production\nWORKDIR /app\nCOPY package.json package-lock.json ./\n'
             'RUN npm ci --omit=dev\nCOPY . .\nUSER node\nEXPOSE 3000\nCMD ["node", "server.js"]')
  df_distroless = ('FROM node:24-trixie-slim AS build\nWORKDIR /app\nCOPY package.json package-lock.json ./\nRUN npm ci --omit=dev\nCOPY . .\n\n'
                   'FROM gcr.io/distroless/nodejs24-debian13:nonroot\nENV NODE_ENV=production\nWORKDIR /app\nCOPY --from=build /app /app\nEXPOSE 3000\nCMD ["server.js"]')
  ignore = 'node_modules\n.git\n.env\nnpm-debug.log'
  return {
  'title': T('Missão: empacotar a API e explicar cada linha do Dockerfile', 'Mission: package the API and explain every Dockerfile line'),
  'subtitle': T('A marmita vai para o Kubernetes: leve, rápida de refazer, sem root e sem a senha do banco colada na tampa', 'The lunchbox is headed for Kubernetes: light, quick to rebuild, no root and no database password taped to the lid'),
  'mission': T('O estagiário empacotou a api-pedidos com o Dockerfile mais simples que achou: FROM node:latest, COPY . . antes do npm ci, a senha do banco num ENV, sem .dockerignore, sem USER e a imagem publicada como latest. Funciona na máquina dele (claro). Conserte o empacotamento até os cinco critérios ficarem verdes, e use a tabela para explicar o que cada linha do Dockerfile final faz e por quê.',
               'The intern packaged api-pedidos with the simplest Dockerfile they could find: FROM node:latest, COPY . . before npm ci, the database password in an ENV, no .dockerignore, no USER and the image pushed as latest. It works on their machine (of course). Fix the packaging until all five criteria turn green, and use the table to explain what each line of the final Dockerfile does and why.'),
  'coach': {'ui': T('Mexa nos controles; os critérios e o Dockerfile mudam enquanto você ajusta. Cada critério que falhar diz o porquê.', 'Move the controls; the criteria and the Dockerfile change as you adjust. Each failing criterion says why.'),
            'cmd': T('Edite o comando e rode. Cada critério que falhar diz o porquê. Tudo o que você precisa apareceu nas lições 2, 3 e 4.', 'Edit the command and run it. Each failing criterion says why. Everything you need showed up in lessons 2, 3 and 4.')},
  'why': {'simples': T('Você montou a marmita do jeito certo: uma base enxuta com versão fixa (nada de “a mais nova que tiver”), o feijão cozido antes do tempero (dependências antes do código, para o cache funcionar), um .dockerignore que deixa o lixo e o .env de fora, um usuário comum em vez do dono da casa, e a senha entregue na hora de servir, não colada na tampa.\nRepare no efeito dominó: tirar a senha do ENV não basta se o .env entra junto no COPY . .; e a base slim só fica leve se o node_modules da sua máquina não vier de carona.',
                       'You built the lunchbox the right way: a lean base with a pinned version (no “whatever’s newest”), the beans cooked before the seasoning (dependencies before code, so the cache works), a .dockerignore that keeps junk and .env out, a regular user instead of the owner of the house, and the password handed over at serving time, not taped to the lid.\nNotice the domino effect: removing the password from ENV isn’t enough if .env sneaks in with COPY . .; and the slim base only stays light if your machine’s node_modules doesn’t hitch a ride.'),
          'dev': T('Linha a linha: FROM node:24-slim fixa a versão maior e traz só o necessário para rodar Node; ENV NODE_ENV=production liga o modo de produção das bibliotecas; WORKDIR /app define a pasta; COPY dos arquivos de dependências e RUN npm ci --omit=dev instalam só o que roda em produção, numa camada que fica no cache; COPY . . traz o código por último; USER node troca para o usuário comum (uid 1000) que a imagem oficial já traz; EXPOSE 3000 documenta a porta; CMD em JSON roda o node direto.\nNa versão distroless, o multi-stage build instala as dependências num estágio com ferramentas e copia só /app para uma imagem final sem shell nem gerenciador de pacotes; a tag :nonroot já roda como usuário comum, e o ENTRYPOINT da imagem é o node, por isso o CMD é só ["server.js"]. Segredo vai na execução: docker run -e, um Secret do Kubernetes ou um cofre como o Key Vault. Para segredos de build (um token de npm privado), use RUN --mount=type=secret.',
                   'Line by line: FROM node:24-slim pins the major version and brings only what’s needed to run Node; ENV NODE_ENV=production turns on libraries’ production mode; WORKDIR /app sets the folder; COPY of the dependency files and RUN npm ci --omit=dev install only what runs in production, in a layer that stays cached; COPY . . brings the code last; USER node switches to the regular user (uid 1000) the official image already ships; EXPOSE 3000 documents the port; CMD in JSON runs node directly.\nIn the distroless version, the multi-stage build installs dependencies in a stage with tools and copies only /app into a final image with no shell or package manager; the :nonroot tag already runs as a regular user, and the image’s ENTRYPOINT is node, which is why CMD is just ["server.js"]. Secrets go in at run time: docker run -e, a Kubernetes Secret or a vault like Key Vault. For build-time secrets (a private npm token), use RUN --mount=type=secret.'),
          'especialista': T('Para produção, ainda: existem linhas de LTS mais novas do Node (como a 26), mas a 24 segue suportada; ao migrar, troque o FROM. Fixe a base por digest (FROM node:24-slim@sha256:…) com um bot de atualização; rode docker build --check no CI (ele avisa, por exemplo, de segredos em ARG e ENV e de CMD fora do formato JSON); gere SBOM e escaneie a imagem; publique com tag imutável e implante por digest.\nNo Kubernetes, complete com securityContext (runAsNonRoot: true, readOnlyRootFilesystem: true, allowPrivilegeEscalation: false), requests e limits, e probes de liveness e readiness em vez de HEALTHCHECK. E cuide dos sinais: o Node como PID 1 não trata SIGTERM sozinho, então trate o sinal no código (fechando o servidor com calma) ou rode com um init (docker run --init; no Kubernetes, trate no app), para o rolling update não cortar requisições no meio.',
                            'For production, also: newer Node LTS lines exist (such as 26), but 24 is still supported; when migrating, change the FROM. Pin the base by digest (FROM node:24-slim@sha256:…) with an update bot; run docker build --check in CI (it warns, for example, about secrets in ARG and ENV and about CMD outside JSON form); generate an SBOM and scan the image; push with an immutable tag and deploy by digest.\nIn Kubernetes, round it off with securityContext (runAsNonRoot: true, readOnlyRootFilesystem: true, allowPrivilegeEscalation: false), requests and limits, and liveness and readiness probes instead of HEALTHCHECK. And mind the signals: Node as PID 1 doesn’t handle SIGTERM by itself, so handle the signal in code (closing the server gracefully) or run with an init (docker run --init; in Kubernetes, handle it in the app), so a rolling update doesn’t cut requests mid-way.')},
  'success': T('Missão cumprida! A {text}:{tagStr} tem {imgMB} MB, refaz o build em {rebuildS} s quando o código muda, roda sem root e não carrega nenhum segredo. E agora você sabe explicar cada linha do Dockerfile. A marmita está pronta para o Kubernetes.',
               'Mission accomplished! {text}:{tagStr} is {imgMB} MB, rebuilds in {rebuildS} s when the code changes, runs without root and carries no secrets. And now you can explain every line of the Dockerfile. The lunchbox is ready for Kubernetes.'),
  'errors': {'notInEnum.base': T('Use node:latest, node:24, node:24-slim ou distroless.', 'Use node:latest, node:24, node:24-slim or distroless.'),
             'notInEnum.order': T('Use copia-tudo ou deps-primeiro.', 'Use copy-all or deps-first.'),
             'notInEnum.user': T('Use root ou nao-root.', 'Use root or non-root.'),
             'notInEnum.secret': T('Use imagem ou execucao.', 'Use image or runtime.'),
             'notBool.ignore': T('Use sim ou nao.', 'Use yes or no.'),
             'notInEnum.tag': T('Use latest ou 1.0.0.', 'Use latest or 1.0.0.')},
  'controls': {'arg': T('Nome da imagem', 'Image name'), 'base': T('Imagem base', 'Base image'), 'order': T('Ordem das linhas', 'Line order'),
               'user': T('Usuário do processo', 'Process user'), 'secret': T('Onde entra a senha do banco', 'Where the database password goes'),
               'ignore': T('Tem .dockerignore?', 'Has a .dockerignore?'), 'tag': T('Tag publicada', 'Published tag')},
  'scene': {'label': T('Empacotando a api-pedidos', 'Packaging api-pedidos'), 'empty': T('Rode para empacotar.', 'Run to package.'),
    'trackDone': T('Você concluiu a trilha Fundamentos de Contêineres e Kubernetes.', 'You completed the Containers and Kubernetes Foundations track.'),
    'checks': T('Critérios da missão', 'Mission criteria'),
    'cSize': T('Imagem final com até 300 MB', 'Final image at most 300 MB'),
    'cSizeBase': T('{imgMB} MB: a base completa do Node sozinha já passa de 1 GB nesta simulação (compiladores, ferramentas, documentação)', '{imgMB} MB: the full Node base alone is over 1 GB in this simulation (compilers, tools, docs)'),
    'cSizeJunk': T('{imgMB} MB: sem .dockerignore, o COPY . . trouxe {junkMB} MB da sua máquina (node_modules, .git)', '{imgMB} MB: with no .dockerignore, COPY . . brought {junkMB} MB from your machine (node_modules, .git)'),
    'cCache': T('Mudar o código não reinstala as dependências', 'Changing the code doesn’t reinstall dependencies'),
    'cCacheWhy': T('o COPY . . vem antes do npm ci: cada linha alterada custa {rebuildS} s de build', 'COPY . . comes before npm ci: every changed line costs {rebuildS} s of build'),
    'cUser': T('Não roda como root', 'Doesn’t run as root'),
    'cUserN': T('sem USER, o node roda como root (uid 0) dentro do contêiner', 'with no USER, node runs as root (uid 0) inside the container'),
    'cUserD': T('a distroless sem a tag :nonroot roda como root', 'distroless without the :nonroot tag runs as root'),
    'cSecret': T('Nenhum segredo dentro da imagem', 'No secret inside the image'),
    'cSecEnv': T('ENV DB_PASSWORD fica gravado na configuração da imagem: qualquer um com docker image inspect lê', 'ENV DB_PASSWORD is stored in the image config: anyone with docker image inspect can read it'),
    'cSecFile': T('o .env entrou junto no COPY . ., porque não há .dockerignore', '.env came along with COPY . ., because there’s no .dockerignore'),
    'cSecBoth': T('dois vazamentos: o ENV DB_PASSWORD e o .env copiado sem .dockerignore', 'two leaks: ENV DB_PASSWORD and the .env copied without a .dockerignore'),
    'cPin': T('Versões fixas, nada de latest', 'Pinned versions, no latest'),
    'cPinBase': T('FROM node:latest troca de versão sozinho, sem você pedir', 'FROM node:latest changes version on its own, without you asking'),
    'cPinTag': T('a imagem sai como {text}:latest: ninguém sabe qual versão está rodando', 'the image goes out as {text}:latest: nobody knows which version is running'),
    'cPinBoth': T('base e tag em latest: nem o que entra nem o que sai tem versão', 'base and tag on latest: neither what goes in nor what comes out has a version'),
    'sizeM': T('tamanho da imagem (MB)', 'image size (MB)'), 'rebuildM': T('rebuild após mudar o código (s)', 'rebuild after a code change (s)'),
    'secretsM': T('segredos dentro da imagem', 'secrets inside the image'), 'userM': T('usuário do processo', 'process user'),
    'dfLabel': T('O Dockerfile atual, linha a linha', 'The current Dockerfile, line by line'), 'colLine': T('linha', 'line'), 'colWhy': T('o que faz e por quê', 'what it does and why'),
    'dfCap': T('Tamanhos e tempos da simulação; confira os reais com docker image ls e com o docker build da receita.', 'Simulated sizes and times; check the real ones with docker image ls and the recipe’s docker build.'),
    'lNoUser': T('# (nenhuma linha USER)', '# (no USER line)'),
    'eBuild': T('estágio de build: tem npm e ferramentas, mas não vai para a imagem final', 'build stage: has npm and tools, but doesn’t go into the final image'),
    'eFromLatest': T('base sem versão: amanhã pode ser outro Node, e é a imagem completa, enorme', 'unversioned base: tomorrow it may be another Node, and it’s the full, huge image'),
    'eFromFull': T('versão fixa, mas é a imagem completa: compiladores e ferramentas que a API não usa', 'pinned version, but it’s the full image: compilers and tools the API doesn’t use'),
    'eFromSlim': T('Node 24 fixo, só com o necessário para rodar', 'Node 24 pinned, with only what’s needed to run'),
    'eEnvProd': T('liga o modo produção das bibliotecas', 'turns on libraries’ production mode'),
    'eSecret': T('SENHA NA IMAGEM: fica no config, visível no docker image inspect e no history', 'PASSWORD IN THE IMAGE: stays in the config, visible in docker image inspect and history'),
    'eWork': T('pasta de trabalho do app', 'the app’s working folder'),
    'eWork2': T('pasta de trabalho na imagem final', 'working folder in the final image'),
    'eCopyPkg': T('só os arquivos de dependências: esta camada só muda quando o lock muda', 'only the dependency files: this layer only changes when the lock changes'),
    'eNpmFirst': T('instala só as dependências de produção, e fica no cache', 'installs only production dependencies, and stays cached'),
    'eCopyLast': T('o código vem por último: mudar código só refaz daqui para baixo', 'the code comes last: changing code only redoes from here down'),
    'eCopyLastNoIgnore': T('código por último, mas sem .dockerignore traz node_modules, .git e .env da sua máquina', 'code last, but with no .dockerignore it brings node_modules, .git and .env from your machine'),
    'eCopyFirst': T('copia tudo antes de instalar: qualquer mudança no código invalida o npm ci', 'copies everything before installing: any code change invalidates npm ci'),
    'eCopyFirstNoIgnore': T('copia tudo antes de instalar e sem .dockerignore: cache quebrado, lixo e .env dentro', 'copies everything before installing and with no .dockerignore: broken cache, junk and .env inside'),
    'eNpmAfter': T('roda de novo a cada mudança no código (84 s)', 'runs again on every code change (84 s)'),
    'eDistroRoot': T('imagem final sem shell nem npm, mas sem :nonroot roda como root', 'final image with no shell or npm, but without :nonroot it runs as root'),
    'eDistroNon': T('imagem final mínima, sem shell nem npm, e já como usuário comum', 'minimal final image, no shell or npm, already as a regular user'),
    'eCopyFrom': T('leva do estágio de build só a pasta /app pronta', 'takes only the finished /app folder from the build stage'),
    'eUser': T('troca para o usuário comum node (uid 1000) que a imagem oficial já traz', 'switches to the regular node user (uid 1000) the official image ships'),
    'eNoUser': T('sem USER, tudo roda como root dentro do contêiner', 'with no USER, everything runs as root inside the container'),
    'eExpose': T('documenta a porta que a API escuta (não publica nada sozinho)', 'documents the port the API listens on (doesn’t publish anything by itself)'),
    'eCmd': T('formato JSON: o node recebe os sinais do sistema direto', 'JSON form: node gets system signals directly'),
    'eCmdD': T('na distroless o ENTRYPOINT já é o node; aqui vai só o arquivo', 'on distroless the ENTRYPOINT is already node; only the file goes here'),
    'terminal': T('Revisão do pacote (simulada)', 'Package review (simulated)'),
    'tIgnoreOn': T('+ .dockerignore: node_modules, .git, .env, npm-debug.log', '+ .dockerignore: node_modules, .git, .env, npm-debug.log'),
    'tIgnoreOff': T('! sem .dockerignore: {ctxMB} MB de contexto, .env incluído', '! no .dockerignore: {ctxMB} MB of context, .env included'),
    'tCacheOk': T('+ mudar o código: {rebuildS} s de rebuild, npm ci em CACHED', '+ code change: {rebuildS} s rebuild, npm ci CACHED'),
    'tCacheBad': T('! mudar o código: {rebuildS} s de rebuild, npm ci roda de novo', '! code change: {rebuildS} s rebuild, npm ci runs again'),
    'tRoot': T('! o processo roda como root (uid 0)', '! the process runs as root (uid 0)'),
    'tNonroot': T('+ o processo roda como {userName}', '+ the process runs as {userName}'),
    'tSecOk': T('+ nenhum segredo na imagem: a senha chega com docker run -e', '+ no secret in the image: the password arrives with docker run -e'),
    'tSecBad': T('! {secretsN} segredo(s) dentro da imagem', '! {secretsN} secret(s) inside the image'),
    'tSizeOk': T('+ imagem com {imgMB} MB', '+ image at {imgMB} MB'),
    'tSizeBad': T('! imagem com {imgMB} MB', '! image at {imgMB} MB'),
    'tPinOk': T('+ base e tag com versão: {text}:{tagStr}', '+ versioned base and tag: {text}:{tagStr}'),
    'tPinBad': T('? algo ainda em latest: reproduzir este build amanhã não é garantido', '? something is still on latest: reproducing this build tomorrow isn’t guaranteed')},
  'data': {},
  'recipe': {'steps': [
     T('Use a pasta da lição 3. Troque o server.js por esta versão, que só conta se recebeu a senha (sem mostrá-la):\n' + server_js_secret(True) + '\nE crie um .env de mentira, como o do estagiário:\nDB_PASSWORD=marmita123',
       'Use lesson 3’s folder. Replace server.js with this version, which only tells whether it got the password (without showing it):\n' + server_js_secret(False) + '\nAnd create a fake .env, like the intern’s:\nDB_PASSWORD=marmita123'),
     T('Crie o .dockerignore:\n' + ignore, 'Create the .dockerignore:\n' + ignore),
     T('Escreva o Dockerfile consertado e, acima de cada linha, um comentário (# …) dizendo por que ela está ali. Essa é a parte "explicar cada linha" da missão:\n' + df_slim,
       'Write the fixed Dockerfile and, above each line, a comment (# …) saying why it’s there. That’s the "explain every line" part of the mission:\n' + df_slim),
     T('Opcional, versão distroless com multi-stage (num arquivo Dockerfile.distroless):\n' + df_distroless + '\nConstrua com:\ndocker build -f Dockerfile.distroless -t api-pedidos:1.0.0-distroless .',
       'Optional, the distroless multi-stage version (in a Dockerfile.distroless file):\n' + df_distroless + '\nBuild it with:\ndocker build -f Dockerfile.distroless -t api-pedidos:1.0.0-distroless .'),
     T('Verifique, construa e rode, passando a senha só na execução:\ndocker build --check .\ndocker build -t api-pedidos:1.0.0 .\ndocker run -d --name api -p 3000:3000 -e DB_PASSWORD=troque-me api-pedidos:1.0.0\ncurl http://localhost:3000',
       'Check, build and run, passing the password only at run time:\ndocker build --check .\ndocker build -t api-pedidos:1.0.0 .\ndocker run -d --name api -p 3000:3000 -e DB_PASSWORD=change-me api-pedidos:1.0.0\ncurl http://localhost:3000'),
     T('Confira o que está e o que não está na imagem:\ndocker exec api whoami\ndocker exec api ls -a\ndocker image inspect api-pedidos:1.0.0 --format "{{.Config.Env}}"\ndocker image ls api-pedidos\nNa versão distroless não há shell nem whoami; use docker image inspect com --format "{{.Config.User}}". No fim: docker rm -f api',
       'Check what is and isn’t in the image:\ndocker exec api whoami\ndocker exec api ls -a\ndocker image inspect api-pedidos:1.0.0 --format "{{.Config.Env}}"\ndocker image ls api-pedidos\nThe distroless version has no shell or whoami; use docker image inspect with --format "{{.Config.User}}". At the end: docker rm -f api')],
   'ok': T('o docker build --check termina sem avisos; o curl responde com "Senha recebida: true"; o whoami responde node; o ls -a não mostra .env nem .git; e o inspect lista NODE_ENV=production, mas nenhum DB_PASSWORD.',
           'docker build --check finishes with no warnings; curl answers with "Password received: true"; whoami answers node; ls -a shows no .env or .git; and inspect lists NODE_ENV=production but no DB_PASSWORD.')}}

t7 = {'pt': {'objectives': ['Escrever um Dockerfile de produção para uma API Node.', 'Justificar cada linha (base, ordem, usuário, segredos, .dockerignore, tag).', 'Perceber como uma correção depende da outra.'], 'minutes': 25,
  'activity': 'Em duplas, consertem a configuração e depois façam a "leitura dramática" do Dockerfile final: uma pessoa lê a linha, a outra explica em uma frase por que ela está ali. Ganha a dupla que explicar sem dizer "porque sim".',
  'discussion': ['Qual dos cinco problemas seria o mais caro de descobrir em produção?', 'Onde a senha do banco deveria morar no seu projeto?'],
  'misconceptions': ['"Tirei o ENV com a senha, então a imagem está limpa." Sem .dockerignore, o .env entra pelo COPY . ..', '"Imagem pequena é só questão de disco." Menos coisa na imagem também é menos coisa para atacar e para atualizar.']},
 'en': {'objectives': ['Write a production Dockerfile for a Node API.', 'Justify each line (base, order, user, secrets, .dockerignore, tag).', 'Notice how one fix depends on another.'], 'minutes': 25,
  'activity': 'In pairs, fix the configuration and then do a "dramatic reading" of the final Dockerfile: one person reads the line, the other explains in one sentence why it’s there. The pair that explains without saying "just because" wins.',
  'discussion': ['Which of the five problems would be the most expensive to discover in production?', 'Where should the database password live in your project?'],
  'misconceptions': ['"I removed the ENV with the password, so the image is clean." Without .dockerignore, .env comes in through COPY . ..', '"A small image is only about disk." Less stuff in the image also means less to attack and less to update.']}}
write('07-missao-empacotar-api', s7, loc7('pt'), loc7('en'), t7)
print('ok: conteineres-e-kubernetes/fundamentos (7 passos)')
