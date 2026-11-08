"""C# e ASP.NET Core · Fundamentos F1 · C# do zero (7 lições + missão).
Gera content/csharp-e-aspnet/fundamentos/NN-slug/{step,pt,en,teacher}.json. Rode com python3.

Todas as saídas mostradas nas cenas (valores impressos, mensagens de compilador e de exceção, ordem das linhas)
foram conferidas rodando os mesmos trechos com o .NET 10 SDK (dotnet run). Os números com vírgula em PT são
como o .NET imprime quando a cultura do sistema é pt-BR."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write as _write, flag, step

TOPIC, TRACK = 'csharp-e-aspnet', 'fundamentos'
def write(folder, s, pt, en, teacher): _write(TOPIC, TRACK, folder, s, pt, en, teacher)
def opt(id, pt, en): return {'id': id, 'pt': pt, 'en': en}
def loc(pt, en): return {'pt': pt, 'en': en}
def mk(L):
  pt = L == 'pt'
  return pt, (lambda a, b: a if pt else b)
SIM = ['simulado']
NEW = 'dotnet new console -o Cantina'
def comma(s): return s.replace('.', ',')
def both(s): return {'pt': comma(s), 'en': s}
def dotnet_double(x):
  """repr() do Python e o ToString() do .NET Core 3.0+ usam o menor texto que volta ao mesmo double;
  a única diferença aqui é que o .NET escreve 1 (e não 1.0) para números inteiros."""
  r = repr(x)
  return r[:-2] if r.endswith('.0') else r
def sh(*lines): return '\n'.join(lines)

# ================================================================== 1 · tipos e variáveis
QTY = range(1, 21)
def dbl_sum(n):
  t = 0.0
  for _ in range(n): t += 0.10
  return t
DBL = {str(n): dotnet_double(dbl_sum(n)) for n in QTY}
DEC = {str(n): f'{n * 10 // 100}.{n * 10 % 100:02d}' for n in QTY}                      # 0.10m somado: escala 2 (0.30)
DECDIV = {str(n): f'{(n * 10) / 100:g}' for n in QTY}                                    # totalCentavos / 100m: 0.3, 1, 1.5
assert DBL['3'] == '0.30000000000000004' and DBL['10'] == '0.9999999999999999' and DBL['20'] == '2.0000000000000004'
assert DBL['1'] == '0.1' and DEC['3'] == '0.30' and DEC['10'] == '1.00' and DECDIV['3'] == '0.3' and DECDIV['10'] == '1'
DBL_EXACT = {k: (v.rstrip('0') == DEC[k].rstrip('0').rstrip('.') or v == DECDIV[k]) for k, v in DBL.items()}
assert DBL_EXACT['1'] and DBL_EXACT['2'] and not DBL_EXACT['3'] and not DBL_EXACT['10']
TYPES1 = [opt('decimal', 'decimal', 'decimal'), opt('double', 'double', 'double'), opt('int', 'int', 'int')]

s1 = step('cs-tipos-e-variaveis', 1, TRACK, 15, ['csharp', 'tipos', 'decimal', 'double', 'int'], [], SIM,
  loc('somar', 'add'),
  {'name': 'text', 'required': False, 'default': loc('balas de R$ 0,10', 'R$ 0.10 candies'), 'ui': 'text'},
  [flag('kind', 'tipo', 'type', 'enum', options=TYPES1, default='decimal', ui='select'),
   flag('qty', 'qtd', 'qty', 'int', min=1, max=20, default=3, ui='slider')],
  {'options': ['exact', 'drift', 'error'], 'answer': 'drift'}, 'moneyDrift',
  {'live': True,
   'consts': {'dbl': {'pt': {k: comma(v) for k, v in DBL.items()}, 'en': DBL}, 'dblExact': DBL_EXACT,
              'dec': {'pt': {k: comma(v) for k, v in DEC.items()}, 'en': DEC},
              'decDiv': {'pt': {k: comma(v) for k, v in DECDIV.items()}, 'en': DECDIV}},
   'compute': {
     'key': 'str(qty)',
     'isDouble': "kind == 'double'",
     'isInt': "kind == 'int'",
     'cents': 'qty * 10',
     'rightText': "lookup(lang == 'pt' ? dec.pt : dec.en, key, '')",
     'printed': "isDouble ? lookup(lang == 'pt' ? dbl.pt : dbl.en, key, '') : (isInt ? str(cents) : rightText)",
     'exact': '!isDouble || lookup(dblExact, key, false)',
     'intDiv': 'floor(cents / 100)',
     'decDivText': "lookup(lang == 'pt' ? decDiv.pt : decDiv.en, key, '')",
     'bytes': "kind == 'decimal' ? 16 : (isDouble ? 8 : 4)",
     'litType': "kind == 'decimal' ? 'decimal total = 0;' : (isDouble ? 'double total = 0;' : 'int totalCentavos = 0;')",
     'litAdd': "kind == 'decimal' ? '    total += 0.10m;' : (isDouble ? '    total += 0.10;' : '    totalCentavos += 10;')"},
   'cases': [
     {'when': 'isDouble && !exact', 'flags': ['moneyDrift']},
     {'when': 'isDouble && exact', 'flags': ['luckyDouble']},
     {'when': 'isInt', 'flags': ['inCents']},
     {'when': 'true', 'vars': {'printed': 'printed', 'right': 'rightText', 'qty': 'qty', 'bytes': 'bytes', 'cents': 'cents', 'intDiv': 'intDiv', 'decDiv': 'decDivText'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@printedM', 'value': '=printed', 'tone': "=exact ? 'ok' : 'bad'"},
       {'label': '@rightM', 'value': "='R$ ' + rightText", 'tone': 'info'},
       {'label': '@exactM', 'value': "=exact ? '@yes' : '@no'", 'tone': "=exact ? 'ok' : 'bad'"},
       {'label': '@bytesM', 'value': '=bytes', 'format': 'int', 'tone': 'dim'}]},
     {'type': 'terminal', 'label': 'Program.cs', 'lines': [
       '=litType', "='for (int i = 0; i < ' + qty + '; i++)'", '{', '=litAdd', '}',
       "=isInt ? 'Console.WriteLine(totalCentavos);' : 'Console.WriteLine(total);'"]},
     {'type': 'terminal', 'when': '=isInt', 'label': '@divLabel', 'lines': [
       'Console.WriteLine(totalCentavos / 100);', 'Console.WriteLine(totalCentavos / 100m);']},
     {'type': 'terminal', 'label': '@runLabel', 'lines': "=concat(['$ dotnet run'], [(exact ? '+' : '!') + printed], isInt ? ['?' + intDiv, '+' + decDivText] : [])"},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['@cType', '@cBytes', '@cGood', '@cTrap'],
      'rows': [['int', 4, '@gInt', '@tInt'], ['long', 8, '@gLong', '@tLong'], ['double', 8, '@gDouble', '@tDouble'],
               ['decimal', 16, '@gDecimal', '@tDecimal'], ['bool', 1, '@gBool', '@tBool'], ['string', '@ref', '@gString', '@tString']],
      'tones': "=[isInt ? 'info' : 'neutral', 'neutral', isDouble ? (exact ? 'warn' : 'bad') : 'neutral', kind == 'decimal' ? 'ok' : 'neutral', 'neutral', 'neutral']"},
     {'type': 'note', 'when': '=isDouble && !exact', 'tone': 'bad', 'text': '@driftNote'},
     {'type': 'note', 'when': '=isDouble && exact', 'tone': 'warn', 'text': '@luckyNote'},
     {'type': 'note', 'when': "=kind == 'decimal'", 'tone': 'ok', 'text': '@decimalNote'},
     {'type': 'note', 'when': '=isInt', 'tone': 'info', 'text': '@intNote'}]})

def loc1(L):
  pt, T = mk(L)
  return {
  'title': T('Tipos e variáveis', 'Types and variables'),
  'subtitle': T('Por que três balas de 10 centavos não dão 30 centavos (quando você escolhe o tipo errado)', 'Why three 10-cent candies don’t make 30 cents (when you pick the wrong type)'),
  'mission': T('A Dona Cida, da cantina da escola, pediu um caixa novo em C#. Cada bala custa R$ 0,10 e o programa soma uma por uma. Escolha o tipo da variável que guarda o total (decimal, double ou int em centavos) e veja o que o programa imprime. O código usa os nomes em português da cantina.',
               'Dona Cida, who runs the school canteen, asked for a new till in C#. Each candy costs R$ 0.10 and the program adds them one by one. Pick the type of the variable that holds the total (decimal, double or int in cents) and see what the program prints. The code keeps the canteen’s Portuguese names (total is total, centavos means cents).'),
  'predict': {'question': T('com double, somando 3 balas de 0,10 uma de cada vez, o que o programa imprime?', 'with double, adding 3 candies at 0.10 one at a time, what does the program print?'),
    'options': {'exact': T('0,3: conta de criança', '0.3: kid’s math'),
                'drift': T('0,30000000000000004', '0.30000000000000004'),
                'error': T('Dá erro de compilação: double não serve para dinheiro', 'A compile error: double isn’t allowed for money')}},
  'feedback': {'right': T('isso! double guarda números em binário, e 0,1 em binário é uma dízima (como 1/3 em decimal). Cada soma arredonda um tiquinho, e na terceira o erro aparece na tela. O compilador não reclama: o erro é silencioso.',
                          'right! double stores numbers in binary, and 0.1 in binary repeats forever (like 1/3 in decimal). Each addition rounds a tiny bit, and on the third one the error shows up on screen. The compiler doesn’t complain: the error is silent.'),
               'wrong': T('o programa imprime 0,30000000000000004. Compila sem nenhum aviso: double é um tipo válido, só não é exato para centavos. 0,1 em binário é uma dízima, e o arredondamento de cada soma vai se acumulando.',
                          'the program prints 0.30000000000000004. It compiles with no warning at all: double is a valid type, it just isn’t exact for cents. 0.1 in binary repeats forever, and each addition’s rounding piles up.'),
               'skipped': T('sem palpite? Rode somar --tipo double e olhe o valor impresso.', 'no guess? Run add --type double and look at the printed value.')},
  'coach': {'ui': T('palpite anotado. Troque o tipo para double e veja o valor impresso. Depois volte para decimal.', 'guess noted. Switch the type to double and look at the printed value. Then go back to decimal.'),
            'cmd': T('palpite anotado. Rode somar --tipo double e depois somar --tipo decimal.', 'guess noted. Run add --type double and then add --type decimal.')},
  'tryNext': {'ui': T('Agora escolha int e leia a caixa da divisão: totalCentavos / 100 dá 0. Divisão entre dois int joga fora a parte quebrada.', 'Now pick int and read the division box: totalCentavos / 100 gives 0. Dividing two ints throws away the fraction.'),
              'cmd': T('Rode somar --tipo double --qtd 10 e veja dez balas virarem 0,9999999999999999.', 'Run add --type double --qty 10 and watch ten candies become 0.9999999999999999.')},
  'why': {'simples': T('Toda variável em C# tem um tipo, e o tipo é a "caixa" onde o valor mora. int guarda números inteiros (balas, alunos). double guarda números com vírgula de um jeito muito rápido, mas aproximado, porque o computador conta em binário e 0,1 em binário nunca termina, como 1/3 = 0,333… para nós. decimal guarda números com vírgula contando em base 10, do jeito que a gente faz no caderno, então 0,10 é exatamente 0,10.\nRegra da cantina: dinheiro vai em decimal (ou em centavos num int). double fica para medidas, como a temperatura da geladeira.',
                       'Every variable in C# has a type, and the type is the "box" the value lives in. int holds whole numbers (candies, students). double holds numbers with a decimal point very quickly, but approximately, because the computer counts in binary and 0.1 in binary never ends, like 1/3 = 0.333… for us. decimal holds numbers with a decimal point counting in base 10, the way we do on paper, so 0.10 is exactly 0.10.\nCanteen rule: money goes in decimal (or in cents in an int). double is for measurements, like the fridge temperature.'),
          'dev': T('Vindo do JavaScript: lá todo number é um double (IEEE 754 de 64 bits), então 0.1 + 0.2 também dá 0.30000000000000004. Em C# você escolhe: int (32 bits), long (64), double (64, binário), decimal (128 bits, base 10, 28 a 29 dígitos significativos) e o literal diz o tipo: 0.10 é double, 0.10m é decimal, 10 é int.\nvar não é o "any" do JS: var x = 5; faz x ser int para sempre, decidido na compilação. Duas pegadinhas que pegam quem vem do JS: 7 / 2 dá 3 (divisão entre int descarta a fração; use 7 / 2.0 ou 7m / 2) e somar 1 ao int.MaxValue dá -2147483648 sem erro, porque por padrão a conta não é verificada. Repare também que decimal guarda a escala: 0.10m + 0.10m + 0.10m imprime 0.30, com o zero.',
                   'Coming from JavaScript: there every number is a double (64-bit IEEE 754), so 0.1 + 0.2 is 0.30000000000000004 too. In C# you choose: int (32 bits), long (64), double (64, binary), decimal (128 bits, base 10, 28 to 29 significant digits) and the literal says the type: 0.10 is double, 0.10m is decimal, 10 is int.\nvar is not JS’s "any": var x = 5; makes x an int forever, decided at compile time. Two traps that catch people coming from JS: 7 / 2 is 3 (dividing ints drops the fraction; use 7 / 2.0 or 7m / 2) and adding 1 to int.MaxValue gives -2147483648 with no error, because arithmetic is unchecked by default. Also notice decimal keeps its scale: 0.10m + 0.10m + 0.10m prints 0.30, with the zero.'),
          'especialista': T('Tipos de valor (int, double, decimal, bool, struct) são copiados quando você atribui ou passa para um método; tipos de referência (string, classes, arrays) copiam só a referência. Onde cada um mora na memória (pilha ou heap) é detalhe de implementação; o que importa para o seu código é a semântica de cópia.\ndecimal é um ponto flutuante em base 10: um inteiro de 96 bits mais uma escala (a posição da vírgula). Ele é exato para valores decimais como 0,10, mas não para tudo: 1m / 3 continua sendo uma aproximação, e ele é bem mais lento que double porque a conta é feita em software. Para estouro, use checked (ou a opção do projeto CheckForOverflowUnderflow) e ganhe uma OverflowException em vez de um número negativo; com constantes, o compilador já recusa (CS0220). E lembre que ToString usa a cultura atual: num Windows em português, o mesmo programa imprime 0,30000000000000004 com vírgula. Para arquivos e APIs, formate com CultureInfo.InvariantCulture.',
                            'Value types (int, double, decimal, bool, structs) are copied when you assign them or pass them to a method; reference types (string, classes, arrays) copy only the reference. Where each lives in memory (stack or heap) is an implementation detail; what matters to your code is the copy semantics.\ndecimal is base-10 floating point: a 96-bit integer plus a scale (where the decimal point goes). It is exact for decimal values like 0.10, but not for everything: 1m / 3 is still an approximation, and it is much slower than double because the math runs in software. For overflow, use checked (or the project option CheckForOverflowUnderflow) and get an OverflowException instead of a negative number; with constants, the compiler already refuses (CS0220). And remember ToString uses the current culture: on a Windows set to Portuguese, the same program prints 0,30000000000000004 with a comma. For files and APIs, format with CultureInfo.InvariantCulture.')},
  'break': {'mission': {'ui': T('hora de quebrar: escolha double com 3 balas.', 'time to break it: pick double with 3 candies.'),
                        'cmd': T('hora de quebrar: rode somar --tipo double', 'time to break it: run add --type double')},
            'success': T('Quebrou: com double, {qty} balas de R$ 0,10 viraram {printed}, e o certo era {right}. Nenhum aviso, nenhum erro: só um troco errado que ninguém percebe até o fechamento do caixa não bater.',
                         'Broken: with double, {qty} candies at R$ 0.10 became {printed}, when the right answer was {right}. No warning, no error: just wrong change nobody notices until the till doesn’t add up at closing time.'),
            'calm': T('O programa imprimiu {printed} e a conta bate. Para quebrar, guarde o total num double com 3 balas.', 'The program printed {printed} and the math adds up. To break it, store the total in a double with 3 candies.')},
  'hints': {'ui': T(['Escolha o tipo e a quantidade; a cena muda sozinha.', 'Um dos tipos conta em binário e não guarda 0,1 exato.', 'Escolha double com 3 balas.'],
                    ['Pick the type and the quantity; the scene updates by itself.', 'One of the types counts in binary and can’t hold 0.1 exactly.', 'Pick double with 3 candies.']),
            'cmd': T(['--tipo e --qtd são opcionais.', '--tipo aceita decimal, double ou int.', 'somar --tipo double'],
                     ['--type and --qty are optional.', '--type takes decimal, double or int.', 'add --type double'])},
  'errors': {'notInEnum.kind': T('Use decimal, double ou int.', 'Use decimal, double or int.'),
             'belowMin.qty': T('Pelo menos 1 bala, senão não tem o que somar.', 'At least 1 candy, otherwise there’s nothing to add.'),
             'aboveMax.qty': T('Até 20 balas: mais que isso a Dona Cida manda você para o dentista.', 'Up to 20 candies: beyond that Dona Cida sends you to the dentist.')},
  'controls': {'arg': T('O que está sendo somado', 'What is being added'), 'kind': T('Tipo do total', 'Type of the total'), 'qty': T('Quantas balas de R$ 0,10', 'How many R$ 0.10 candies')},
  'scene': {'label': T('Caixa da cantina', 'Canteen till'), 'empty': T('Rode para somar as balas.', 'Run to add up the candies.'),
    'printedM': T('o programa imprime', 'the program prints'), 'rightM': T('o certo seria', 'it should be'), 'exactM': T('conta exata?', 'exact?'), 'bytesM': T('bytes por valor', 'bytes per value'),
    'yes': T('sim', 'yes'), 'no': T('não', 'no'),
    'divLabel': T('E se quiser em reais? (duas divisões)', 'What if you want reais? (two divisions)'), 'runLabel': T('Terminal', 'Terminal'),
    'tableLabel': T('Os tipos mais usados', 'The most common types'), 'cType': T('tipo', 'type'), 'cBytes': T('bytes', 'bytes'), 'cGood': T('bom para', 'good for'), 'cTrap': T('pegadinha', 'gotcha'),
    'gInt': T('contar coisas, centavos', 'counting things, cents'), 'tInt': T('7 / 2 dá 3', '7 / 2 is 3'),
    'gLong': T('números enormes, ids', 'huge numbers, ids'), 'tLong': T('literal precisa de L se passar do int', 'literal needs L beyond int range'),
    'gDouble': T('medidas, física, gráficos', 'measurements, physics, charts'), 'tDouble': T('0,1 não é exato', '0.1 isn’t exact'),
    'gDecimal': T('dinheiro', 'money'), 'tDecimal': T('literal precisa de m (0.10m)', 'literal needs m (0.10m)'),
    'gBool': T('sim ou não', 'yes or no'), 'tBool': T('não vira número como no JS', 'doesn’t turn into a number like in JS'),
    'gString': T('texto', 'text'), 'tString': T('pode ser null (lição 5)', 'can be null (lesson 5)'), 'ref': T('referência', 'reference'),
    'driftNote': T('Cada += 0.10 arredonda um pouquinho em binário. Com {qty} balas, o erro já aparece: {printed}.', 'Each += 0.10 rounds a little in binary. With {qty} candies the error already shows: {printed}.'),
    'luckyNote': T('Desta vez o arredondamento escondeu o erro e saiu {printed}. Sorte não é estratégia: com 3 balas, o mesmo código erra.', 'This time rounding hid the error and it printed {printed}. Luck isn’t a strategy: with 3 candies the same code is wrong.'),
    'decimalNote': T('decimal conta em base 10: {qty} × 0,10 é exatamente {right}, e ele até guarda o zero do fim.', 'decimal counts in base 10: {qty} × 0.10 is exactly {right}, and it even keeps the trailing zero.'),
    'intNote': T('Em centavos, a soma é exata: {cents}. Mas cuidado na hora de virar reais: {cents} / 100 dá {intDiv} (divisão inteira), e {cents} / 100m dá {decDiv}.', 'In cents the sum is exact: {cents}. But watch out when turning it into reais: {cents} / 100 gives {intDiv} (integer division), and {cents} / 100m gives {decDiv}.')},
  'data': {},
  'recipe': {'steps': [
     T(f'Instale o .NET SDK (a versão LTS atual, em dotnet.microsoft.com) e confira com dotnet --version. Depois crie o projeto: {NEW} e entre na pasta: cd Cantina', f'Install the .NET SDK (the current LTS, from dotnet.microsoft.com) and check it with dotnet --version. Then create the project: {NEW} and go into the folder: cd Cantina'),
     T('Troque todo o conteúdo de Program.cs por:\n' + sh(
        'double totalDouble = 0;', 'decimal totalDecimal = 0;', 'for (int i = 0; i < 3; i++)', '{', '    totalDouble += 0.10;', '    totalDecimal += 0.10m;', '}',
        'Console.WriteLine(totalDouble);', 'Console.WriteLine(totalDecimal);', 'Console.WriteLine(7 / 2);', 'Console.WriteLine(7 / 2.0);'),
       'Replace everything in Program.cs with:\n' + sh(
        'double totalDouble = 0;', 'decimal totalDecimal = 0;', 'for (int i = 0; i < 3; i++)', '{', '    totalDouble += 0.10;', '    totalDecimal += 0.10m;', '}',
        'Console.WriteLine(totalDouble);', 'Console.WriteLine(totalDecimal);', 'Console.WriteLine(7 / 2);', 'Console.WriteLine(7 / 2.0);')),
     T('Rode com dotnet run.', 'Run it with dotnet run.')],
   'ok': T('aparecem 4 linhas: 0,30000000000000004, 0,30, 3 e 3,5 (com ponto em vez de vírgula se o seu sistema estiver em inglês).', 'you see 4 lines: 0.30000000000000004, 0.30, 3 and 3.5 (with commas instead of dots if your system is set to Portuguese).')}}

t1 = {'pt': {'objectives': ['Escolher o tipo certo para cada valor (int, double, decimal, bool, string).', 'Explicar por que double não serve para dinheiro.', 'Reconhecer a divisão inteira.'], 'minutes': 15,
  'activity': 'Peça para a turma calcular 1/3 em decimal com 4 casas e depois somar três vezes (0,3333 × 3 = 0,9999). É o mesmo problema que o computador tem com 0,1 em binário. Depois rodem o programa da receita.',
  'discussion': ['Que outros valores da escola precisam ser exatos? E quais podem ser aproximados?', 'Por que o compilador não avisa quando você usa double para dinheiro?'],
  'misconceptions': ['"O computador sempre acerta contas." Ele acerta a conta que você pediu, no tipo que você escolheu; double é aproximado por definição.', '"var deixa a variável sem tipo." var só pede para o compilador deduzir o tipo, que fica fixo.']},
 'en': {'objectives': ['Pick the right type for each value (int, double, decimal, bool, string).', 'Explain why double is wrong for money.', 'Recognize integer division.'], 'minutes': 15,
  'activity': 'Ask the class to compute 1/3 in decimal with 4 places and then add it three times (0.3333 × 3 = 0.9999). It’s the same problem the computer has with 0.1 in binary. Then run the recipe program.',
  'discussion': ['What other school values must be exact? Which can be approximate?', 'Why doesn’t the compiler warn you when you use double for money?'],
  'misconceptions': ['"Computers always get math right." They get right the math you asked for, in the type you chose; double is approximate by design.', '"var makes a variable untyped." var only asks the compiler to infer the type, which stays fixed.']}}
write('01-tipos-e-variaveis', s1, loc1('pt'), loc1('en'), t1)

# ================================================================== 2 · controle de fluxo
SALDOS = [12, 0, -3, 4.5, 20, 7, 2, 0.5]
def lit(v): return f'{v}m'
def status(v): return 'devendo' if v < 0 else 'zerado' if v == 0 else 'quase acabando' if v < 5 else 'liberado'
def fmt_dec(v): return str(v)
LOOPS = [opt('foreach', 'foreach', 'foreach'), opt('lt', 'for-menor', 'for-lt'), opt('le', 'for-menor-igual', 'for-le')]
OUT2 = [f'Aluno {i + 1}: {status(v)}' for i, v in enumerate(SALDOS)]
TONE2 = {'devendo': 'bad', 'zerado': 'warn', 'quase acabando': 'warn', 'liberado': 'ok'}
SW = ['    string situacao = saldo switch', '    {', '        < 0 => "devendo",', '        0 => "zerado",', '        < 5 => "quase acabando",']
CS8509 = "?…/Program.cs(5,29): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern '5.0000000000000000000000000000M' is not covered."
s2 = step('cs-controle-de-fluxo', 2, TRACK, 15, ['csharp', 'if', 'switch', 'for', 'foreach', 'pattern-matching'], ['cs-tipos-e-variaveis'], SIM,
  loc('conferir', 'check'),
  {'name': 'text', 'required': False, 'default': loc('saldos do recreio', 'recess balances'), 'ui': 'text'},
  [flag('loop', 'laco', 'loop', 'enum', options=LOOPS, default='foreach', ui='select'),
   flag('students', 'alunos', 'students', 'int', min=1, max=8, default=5, ui='slider'),
   flag('discard', 'descarte', 'discard', 'bool', default=True, ui='switch')],
  {'options': ['extra', 'crash', 'compile'], 'answer': 'crash'}, 'outOfRange',
  {'live': True,
   'consts': {'lits': [lit(v) for v in SALDOS], 'vals': [fmt_dec(v) for v in SALDOS], 'valsPt': [comma(fmt_dec(v)) for v in SALDOS], 'outs': OUT2,
              'stats': [status(v) for v in SALDOS], 'tones': [TONE2[status(v)] for v in SALDOS], 'firstBig': next(i for i, v in enumerate(SALDOS) if v >= 5)},
   'compute': {
     'n': 'students',
     'isLe': "loop == 'le'",
     'noMatch': '!discard',
     'shown': 'noMatch ? min(firstBig, n) : n',
     'switchBoom': 'noMatch && firstBig < n',
     'indexBoom': 'isLe && !switchBoom',
     'header': "loop == 'foreach' ? 'foreach (decimal saldo in saldos)' : (isLe ? 'for (int i = 0; i <= saldos.Length; i++)' : 'for (int i = 0; i < saldos.Length; i++)')",
     'valsL': "lang == 'pt' ? valsPt : vals",
     'rowsOk': "zip(range(shown, 1), slice(valsL, 0, shown), slice(stats, 0, shown))",
     'boomRow': "indexBoom ? [[n + 1, '—', 'IndexOutOfRangeException']] : (switchBoom ? [[shown + 1, valsL[shown], 'SwitchExpressionException']] : [])",
     'loops': 'shown + (indexBoom || switchBoom ? 1 : 0)'},
   'cases': [
     {'when': 'indexBoom', 'flags': ['outOfRange']},
     {'when': 'noMatch', 'flags': ['notExhaustive']},
     {'when': 'switchBoom', 'flags': ['switchCrash']},
     {'when': 'true', 'vars': {'n': 'n', 'shown': 'shown', 'loops': 'loops', 'last': 'n - 1'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@servedM', 'value': '=shown', 'format': 'int', 'tone': "=shown == n ? 'ok' : 'bad'"},
       {'label': '@turnsM', 'value': '=loops', 'format': 'int', 'tone': "=loops > n ? 'bad' : 'dim'"},
       {'label': '@endM', 'value': "=indexBoom || switchBoom ? '@crashed' : '@finished'", 'tone': "=indexBoom || switchBoom ? 'bad' : 'ok'"}]},
     {'type': 'terminal', 'label': 'Program.cs', 'lines': "=concat(['decimal[] saldos = [' + join(slice(lits, 0, n), ', ') + '];'], loop == 'foreach' ? ['int numero = 1;'] : [], [header, '{'], loop == 'foreach' ? [] : ['    decimal saldo = saldos[i];'], sw, discard ? [swDiscard] : [], ['    };'], loop == 'foreach' ? tailForeach : tailFor, ['}'])"},
     {'type': 'terminal', 'label': '@runLabel', 'lines': "=concat(['$ dotnet run'], noMatch ? [cs8509] : [], slice(outs, 0, shown), indexBoom ? ['!Unhandled exception. System.IndexOutOfRangeException: Index was outside the bounds of the array.', '~   at Program.<Main>$(String[] args) in …/Program.cs:line 4'] : [], switchBoom ? ['!Unhandled exception. System.Runtime.CompilerServices.SwitchExpressionException: Non-exhaustive switch expression failed to match its input.', '!Unmatched value was ' + vals[shown] + '.'] : [])"},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['@cStudent', '@cBalance', '@cStatus'],
      'rows': '=concat(rowsOk, boomRow)', 'tones': "=concat(slice(tones, 0, shown), indexBoom || switchBoom ? ['bad'] : [])"},
     {'type': 'note', 'when': '=indexBoom', 'tone': 'bad', 'text': '@leNote'},
     {'type': 'note', 'when': '=switchBoom', 'tone': 'bad', 'text': '@switchNote'},
     {'type': 'note', 'when': "=!indexBoom && !switchBoom && loop == 'foreach'", 'tone': 'ok', 'text': '@foreachNote'},
     {'type': 'note', 'when': "=!indexBoom && !switchBoom && loop == 'lt'", 'tone': 'info', 'text': '@ltNote'}]})
s2['data']['sim']['consts']['sw'] = SW
s2['data']['sim']['consts']['cs8509'] = CS8509
s2['data']['sim']['consts']['swDiscard'] = '        _ => "liberado",'
s2['data']['sim']['consts']['tailForeach'] = ['    Console.WriteLine($"Aluno {numero}: {situacao}");', '    numero++;']
s2['data']['sim']['consts']['tailFor'] = ['    Console.WriteLine($"Aluno {i + 1}: {situacao}");']

def loc2(L):
  pt, T = mk(L)
  return {
  'title': T('Controle de fluxo', 'Control flow'),
  'subtitle': T('if, switch e laços: o caixa confere o saldo de cada aluno, e um sinal de igual a mais derruba tudo', 'if, switch and loops: the till checks each student’s balance, and one extra equals sign brings it all down'),
  'mission': T('No recreio, o caixa da Dona Cida passa pela lista de saldos dos alunos e diz quem está liberado, quase acabando, zerado ou devendo. Um switch decide a situação e um laço passa por todos. Troque o tipo de laço (foreach, for com < ou for com <=) e veja quem é atendido.',
               'At recess, Dona Cida’s till goes through the list of student balances and says who is cleared (liberado), running low (quase acabando), at zero (zerado) or owing (devendo). A switch decides the status and a loop goes through everyone. Change the loop (foreach, for with < or for with <=) and see who gets served.'),
  'predict': {'question': T('com for (int i = 0; i <= saldos.Length; i++), o que acontece?', 'with for (int i = 0; i <= saldos.Length; i++), what happens?'),
    'options': {'extra': T('Imprime uma linha vazia a mais no fim', 'It prints one extra empty line at the end'),
                'crash': T('Atende todos e depois o programa quebra com uma exceção', 'It serves everyone and then the program crashes with an exception'),
                'compile': T('Nem compila', 'It doesn’t even compile')}},
  'feedback': {'right': T('isso: com 5 alunos, os índices vão de 0 a 4. O <= faz o laço tentar o índice 5, que não existe, e o C# para tudo com IndexOutOfRangeException. O compilador não pega: o erro só aparece rodando.',
                          'right: with 5 students, indexes go from 0 to 4. The <= makes the loop try index 5, which doesn’t exist, and C# stops everything with an IndexOutOfRangeException. The compiler doesn’t catch it: the error only shows up when running.'),
               'wrong': T('compila e atende todos, mas na última volta tenta ler saldos[5] numa lista que vai de 0 a 4, e o programa quebra com IndexOutOfRangeException. No JavaScript, saldos[5] daria undefined em silêncio; o C# prefere gritar.',
                          'it compiles and serves everyone, but on the last turn it tries to read saldos[5] in a list that goes from 0 to 4, and the program crashes with an IndexOutOfRangeException. In JavaScript saldos[5] would quietly be undefined; C# prefers to shout.'),
               'skipped': T('sem palpite? Rode conferir --laco for-menor-igual e olhe a última linha do terminal.', 'no guess? Run check --loop for-le and look at the last terminal line.')},
  'coach': {'ui': T('palpite anotado. Troque o laço para "for-menor-igual" e olhe o fim do terminal.', 'guess noted. Switch the loop to "for-le" and look at the end of the terminal.'),
            'cmd': T('palpite anotado. Rode conferir e depois conferir --laco for-menor-igual.', 'guess noted. Run check and then check --loop for-le.')},
  'tryNext': {'ui': T('Agora volte para foreach e desligue o descarte (_): o compilador avisa que o switch não cobre tudo, e o primeiro aluno com saldo 12 derruba o programa.', 'Now go back to foreach and turn off the discard (_): the compiler warns the switch doesn’t cover everything, and the first student with a balance of 12 brings the program down.'),
              'cmd': T('Rode conferir --descarte nao e leia o aviso CS8509 antes da exceção.', 'Run check --discard no and read the CS8509 warning before the exception.')},
  'why': {'simples': T('Um programa decide e repete. Decidir é o if ("se o saldo for menor que zero, está devendo") e o switch, que é um if com várias saídas organizadas. Repetir é o laço: o for conta voltas com um número (0, 1, 2…), e o foreach diz "para cada aluno da lista", sem você precisar contar.\nComputador começa a contar do zero: numa lista de 5 alunos, o primeiro é o 0 e o último é o 4. Pedir o número 5 é pedir um aluno que não existe, e o C# para o programa para avisar. Por isso o foreach é o amigo de quem está começando: ele não deixa você errar a conta.',
                       'A program decides and repeats. Deciding is the if ("if the balance is below zero, they owe money") and the switch, which is an if with several tidy exits. Repeating is the loop: for counts turns with a number (0, 1, 2…), and foreach says "for each student in the list", with no counting on your part.\nComputers start counting from zero: in a list of 5 students, the first is 0 and the last is 4. Asking for number 5 is asking for a student who doesn’t exist, and C# stops the program to tell you. That’s why foreach is a beginner’s friend: it won’t let you get the count wrong.'),
          'dev': T('Para quem vem do JS: if (x = 5) nem compila (CS0029: não converte int em bool), porque a condição tem que ser bool; não existe "truthy". No switch clássico não há queda de um case para o outro sem break (CS0163). E acesso fora do array lança IndexOutOfRangeException em vez de devolver undefined.\nO switch de expressão (saldo switch { < 0 => …, _ => … }) usa padrões relacionais (< 5), constantes (0) e o descarte _. Se faltar algum caso, o compilador avisa com CS8509 e, se o valor não casar com nada, a execução lança SwitchExpressionException. Prefira foreach para percorrer coleções e for quando você precisa do índice (e use <, nunca <=, com Length ou Count).',
                   'For JS folks: if (x = 5) doesn’t compile (CS0029: can’t convert int to bool), because the condition must be a bool; there is no "truthy". The classic switch doesn’t fall through from one case to the next without a break (CS0163). And reading outside an array throws IndexOutOfRangeException instead of returning undefined.\nThe switch expression (saldo switch { < 0 => …, _ => … }) uses relational patterns (< 5), constants (0) and the discard _. If a case is missing, the compiler warns with CS8509 and, if a value matches nothing, execution throws SwitchExpressionException. Prefer foreach to walk collections and for when you need the index (and use <, never <=, with Length or Count).'),
          'especialista': T('Os padrões vão bem além de números: padrões de tipo (obj is Pedido p), de propriedade (pedido is { Total: > 100 }), de lista ([var primeiro, ..]) e combinadores and, or, not. O compilador confere a exaustividade e também casos inalcançáveis, então trate o aviso CS8509 como erro (TreatWarningsAsErrors ou WarningsAsErrors com a lista de códigos) em código de produção.\nforeach funciona com qualquer coisa que tenha GetEnumerator, não só com IEnumerable; em arrays e List<T> o compilador gera um laço sem alocação. Modificar uma List<T> dentro do foreach que a percorre lança InvalidOperationException ("Collection was modified"). Quando o índice importa, Span<T> e o operador ^1 (último elemento) ajudam a evitar contas de borda à mão.',
                            'Patterns go well beyond numbers: type patterns (obj is Pedido p), property patterns (pedido is { Total: > 100 }), list patterns ([var first, ..]) and the and, or, not combinators. The compiler checks exhaustiveness and also unreachable cases, so treat warning CS8509 as an error (TreatWarningsAsErrors, or WarningsAsErrors with a list of codes) in production code.\nforeach works with anything that has a GetEnumerator, not just IEnumerable; on arrays and List<T> the compiler generates an allocation-free loop. Changing a List<T> inside the foreach that walks it throws InvalidOperationException ("Collection was modified"). When the index matters, Span<T> and the ^1 operator (last element) help you avoid hand-written edge math.')},
  'break': {'mission': {'ui': T('hora de quebrar: escolha o laço "for-menor-igual".', 'time to break it: pick the "for-le" loop.'),
                        'cmd': T('hora de quebrar: rode conferir --laco for-menor-igual', 'time to break it: run check --loop for-le')},
            'success': T('Quebrou: o laço deu {loops} voltas para {n} alunos. Na última, pediu um saldo que não existe, e a fila do recreio parou com IndexOutOfRangeException. Um único = a mais.',
                         'Broken: the loop ran {loops} turns for {n} students. On the last one it asked for a balance that doesn’t exist, and the recess line stopped with an IndexOutOfRangeException. One single extra =.'),
            'calm': T('{shown} de {n} alunos conferidos (voltas do laço: {loops}). Para quebrar, use o for com <= e o descarte ligado.', '{shown} of {n} students checked (loop turns: {loops}). To break it, use the for with <= and the discard on.')},
  'hints': {'ui': T(['Escolha o laço e quantos alunos estão na fila.', 'Os índices vão de 0 até o tamanho menos 1.', 'Escolha o laço "for-menor-igual".'],
                    ['Pick the loop and how many students are in line.', 'Indexes go from 0 up to length minus 1.', 'Pick the "for-le" loop.']),
            'cmd': T(['--laco, --alunos e --descarte são opcionais.', '--laco aceita foreach, for-menor ou for-menor-igual.', 'conferir --laco for-menor-igual'],
                     ['--loop, --students and --discard are optional.', '--loop takes foreach, for-lt or for-le.', 'check --loop for-le'])},
  'errors': {'notInEnum.loop': T('Use foreach, for-menor ou for-menor-igual.', 'Use foreach, for-lt or for-le.'),
             'belowMin.students': T('Pelo menos 1 aluno na fila.', 'At least 1 student in line.'), 'aboveMax.students': T('Até 8 alunos: o recreio dura 15 minutos.', 'Up to 8 students: recess only lasts 15 minutes.'),
             'notBool.discard': T('Use sim ou nao.', 'Use yes or no.')},
  'controls': {'arg': T('Lista', 'List'), 'loop': T('Tipo de laço', 'Loop kind'), 'students': T('Alunos na fila', 'Students in line'), 'discard': T('Caso _ (descarte) no switch', 'Discard case (_) in the switch')},
  'scene': {'label': T('Fila do recreio', 'Recess line'), 'empty': T('Rode para conferir os saldos.', 'Run to check the balances.'),
    'servedM': T('alunos conferidos', 'students checked'), 'turnsM': T('voltas do laço', 'loop turns'), 'endM': T('fim do programa', 'program ending'),
    'crashed': T('quebrou', 'crashed'), 'finished': T('normal', 'normal'), 'runLabel': T('Terminal', 'Terminal'),
    'tableLabel': T('Cada volta do laço', 'Each loop turn'), 'cStudent': T('aluno', 'student'), 'cBalance': T('saldo (R$)', 'balance (R$)'), 'cStatus': T('situação', 'status'),
    'leNote': T('Com <=, a volta {loops} pede saldos[{n}], mas os índices vão de 0 a {last}. No C#, isso é exceção, não undefined.', 'With <=, turn {loops} asks for saldos[{n}], but the indexes go from 0 to {last}. In C# that’s an exception, not undefined.'),
    'switchNote': T('Sem o _, nenhum caso cobre saldos de 5 para cima. O compilador avisou (CS8509) e, rodando, o primeiro saldo assim derrubou o programa.', 'Without the _, no case covers balances of 5 and up. The compiler warned (CS8509) and, at run time, the first such balance brought the program down.'),
    'foreachNote': T('O foreach passa por cada aluno exatamente uma vez: não tem índice para errar.', 'foreach visits each student exactly once: there’s no index to get wrong.'),
    'ltNote': T('O for com < também funciona: {n} voltas, índices de 0 a {last}. É o mesmo resultado do foreach, com mais chance de errar.', 'The for with < works too: {n} turns, indexes 0 to {last}. Same result as foreach, with more room for mistakes.')},
  'data': {},
  'recipe': {'steps': [
     T(f'Crie o projeto (se ainda não criou): {NEW} e entre em Cantina.', f'Create the project (if you haven’t yet): {NEW} and go into Cantina.'),
     T('Troque Program.cs por:\n' + sh('decimal[] saldos = [12m, 0m, -3m, 4.5m, 20m];', 'for (int i = 0; i <= saldos.Length; i++)', '{', '    decimal saldo = saldos[i];', *SW, '        _ => "liberado",', '    };', '    Console.WriteLine($"Aluno {i + 1}: {situacao}");', '}'),
       'Replace Program.cs with:\n' + sh('decimal[] saldos = [12m, 0m, -3m, 4.5m, 20m];', 'for (int i = 0; i <= saldos.Length; i++)', '{', '    decimal saldo = saldos[i];', *SW, '        _ => "liberado",', '    };', '    Console.WriteLine($"Aluno {i + 1}: {situacao}");', '}')),
     T('Rode dotnet run. Depois troque <= por < e rode de novo.', 'Run dotnet run. Then change <= to < and run again.')],
   'ok': T('na primeira vez aparecem os 5 alunos e depois "Unhandled exception. System.IndexOutOfRangeException"; com <, os 5 alunos aparecem e o programa termina sem erro.', 'the first time you see the 5 students and then "Unhandled exception. System.IndexOutOfRangeException"; with <, the 5 students show up and the program ends with no error.')}}

t2 = {'pt': {'objectives': ['Usar if, switch de expressão, for e foreach.', 'Entender por que índices vão de 0 a tamanho menos 1.', 'Ler um aviso do compilador antes de rodar.'], 'minutes': 15,
  'activity': 'Cinco alunos em fila, numerados de 0 a 4. Um "laço humano" chama os números em voz alta seguindo for (i = 0; i <= 5…). Quem é chamado e não existe? Repitam com foreach: "cada um da fila, um passo à frente".',
  'discussion': ['Por que o C# prefere quebrar o programa a devolver undefined?', 'Quando você precisa do índice e quando o foreach basta?'],
  'misconceptions': ['"Se compilou, está certo." O compilador pega o if (x = 5), mas não pega índice fora da lista; isso só aparece rodando (ou num teste).']},
 'en': {'objectives': ['Use if, switch expressions, for and foreach.', 'Understand why indexes go from 0 to length minus 1.', 'Read a compiler warning before running.'], 'minutes': 15,
  'activity': 'Five students in line, numbered 0 to 4. A "human loop" calls the numbers out loud following for (i = 0; i <= 5…). Who is called and doesn’t exist? Repeat with foreach: "everyone in line, one step forward".',
  'discussion': ['Why does C# prefer crashing the program over returning undefined?', 'When do you need the index and when is foreach enough?'],
  'misconceptions': ['"If it compiled, it’s right." The compiler catches if (x = 5), but not an index outside the list; that only shows up when running (or in a test).']}}
write('02-controle-de-fluxo', s2, loc2('pt'), loc2('en'), t2)

# ================================================================== 3 · coleções e LINQ
SNACKS = [('Coxinha', 6), ('Suco', 4), ('Bolo', 7), ('Pão de queijo', 3)]
LATE = ('Pipoca', 3)
def linq_run(mode, late, count_first):
  base = list(SNACKS); out = []; w = s = runs = 0
  def enum(items, show):
    nonlocal w, s, runs
    runs += 1; res = []
    for name, price in items:
      out.append(f'  where  {name}'); w += 1
      if price < 5:
        out.append(f'  select {name}'); s += 1; res.append(name)
        if show: out.append(f'mostra {name}')
    return res
  if mode == 'tolist': mat = enum(base, False)
  if late: base.append(LATE)
  if count_first:
    out.append(f'total: {len(enum(base, False)) if mode == "deferred" else len(mat)}')
  if mode == 'deferred': shown = enum(base, True)
  else:
    shown = mat
    for n in mat: out.append(f'mostra {n}')
  return {'lines': out, 'where': w, 'select': s, 'runs': runs, 'shown': len(shown), 'items': len(base)}
LINQ = {f'{m}|{int(l)}|{int(c)}': linq_run(m, l, c) for m in ('deferred', 'tolist') for l in (0, 1) for c in (0, 1)}
# Conferido com dotnet run (.NET 10): adiado + pipoca + Count() e ToList + pipoca + Count().
assert LINQ['deferred|1|1']['lines'][:9] == ['  where  Coxinha', '  where  Suco', '  select Suco', '  where  Bolo', '  where  Pão de queijo', '  select Pão de queijo', '  where  Pipoca', '  select Pipoca', 'total: 3']
assert LINQ['tolist|1|1']['lines'][-3:] == ['total: 2', 'mostra Suco', 'mostra Pão de queijo']
CODE3_HEAD = ['var lanches = new List<Lanche>', '{', '    new("Coxinha", 6m),', '    new("Suco", 4m),', '    new("Bolo", 7m),', '    new("Pão de queijo", 3m),', '};', '',
              'var baratos = lanches', '    .Where(l =>', '    {', '        Console.WriteLine($"  where  {l.Nome}");', '        return l.Preco < 5m;', '    })',
              '    .Select(l =>', '    {', '        Console.WriteLine($"  select {l.Nome}");', '        return l.Nome;']
CODE3_TAIL = ['foreach (var nome in baratos)', '{', '    Console.WriteLine($"mostra {nome}");', '}', '', 'record Lanche(string Nome, decimal Preco);']
MODES3 = [opt('deferred', 'adiado', 'deferred'), opt('tolist', 'tolist', 'tolist')]
s3 = step('cs-colecoes-e-linq', 3, TRACK, 20, ['csharp', 'list', 'linq', 'execucao-adiada'], ['cs-controle-de-fluxo'], SIM,
  loc('consultar', 'query'),
  {'name': 'text', 'required': False, 'default': loc('lanches abaixo de R$ 5', 'snacks under R$ 5'), 'ui': 'text'},
  [flag('mode', 'modo', 'mode', 'enum', options=MODES3, default='deferred', ui='select'),
   flag('countFirst', 'contar', 'count', 'bool', default=False, ui='switch'),
   flag('late', 'pipoca', 'popcorn', 'bool', default=False, ui='switch')],
  {'options': ['batch', 'interleaved', 'nothing'], 'answer': 'interleaved'}, 'ranTwice',
  {'live': True,
   'consts': {'runsTab': LINQ, 'head': CODE3_HEAD, 'tail': CODE3_TAIL},
   'compute': {
     'isDeferred': "mode == 'deferred'",
     'row': "lookup(runsTab, mode + '|' + (late ? '1' : '0') + '|' + (countFirst ? '1' : '0'), runsTab['deferred|0|0'])",
     'whereN': 'row.where', 'selectN': 'row.select', 'runsN': 'row.runs', 'shownN': 'row.shown', 'itemsN': 'row.items',
     'lateShown': 'late && isDeferred'},
   'cases': [
     {'when': 'isDeferred && countFirst', 'flags': ['ranTwice']},
     {'when': 'lateShown', 'flags': ['sawLate']},
     {'when': 'late && !isDeferred', 'flags': ['missedLate']},
     {'when': 'true', 'vars': {'whereN': 'whereN', 'selectN': 'selectN', 'runs': 'runsN', 'shown': 'shownN', 'items': 'itemsN'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@runsM', 'value': '=runsN', 'format': 'int', 'tone': "=runsN > 1 ? 'bad' : 'ok'"},
       {'label': '@whereM', 'value': '=whereN', 'format': 'int', 'tone': "=runsN > 1 ? 'warn' : 'dim'"},
       {'label': '@selectM', 'value': '=selectN', 'format': 'int', 'tone': 'dim'},
       {'label': '@shownM', 'value': '=shownN', 'format': 'int', 'tone': 'info'}]},
     {'type': 'terminal', 'label': 'Program.cs', 'lines': "=concat(head, isDeferred ? ['    });'] : ['    })', '    .ToList();'], [''], late ? ['lanches.Add(new(\"Pipoca\", 3m));'] : [], countFirst ? ['Console.WriteLine($\"total: {baratos.Count()}\");'] : [], tail)"},
     {'type': 'terminal', 'label': '@runLabel', 'lines': "=concat(['$ dotnet run'], row.lines)"},
     {'type': 'note', 'when': '=isDeferred && !countFirst', 'tone': 'ok', 'text': '@deferredNote'},
     {'type': 'note', 'when': '=isDeferred && countFirst', 'tone': 'bad', 'text': '@twiceNote'},
     {'type': 'note', 'when': '=!isDeferred', 'tone': 'info', 'text': '@tolistNote'},
     {'type': 'note', 'when': '=lateShown', 'tone': 'warn', 'text': '@lateNote'},
     {'type': 'note', 'when': '=late && !isDeferred', 'tone': 'info', 'text': '@lateListNote'}]})

def loc3(L):
  pt, T = mk(L)
  return {
  'title': T('Coleções e LINQ', 'Collections and LINQ'),
  'subtitle': T('A consulta que só trabalha quando alguém pergunta, e trabalha de novo a cada pergunta', 'The query that only works when someone asks, and works again every time you ask'),
  'mission': T('A Dona Cida guarda o cardápio numa List e quer a lista dos lanches abaixo de R$ 5. Com LINQ, é um Where (filtra) seguido de um Select (pega o nome). Para ver quando cada parte roda, cada uma escreve no terminal. Descubra em que ordem as linhas aparecem e o que muda com ToList, com um Count() antes do foreach e com uma pipoca que entra no cardápio depois.',
               'Dona Cida keeps the menu in a List and wants the snacks under R$ 5. With LINQ, that’s a Where (filters) followed by a Select (takes the name). To see when each part runs, each one writes to the terminal. Find out in what order the lines show up and what changes with ToList, with a Count() before the foreach and with popcorn (Pipoca) added to the menu afterwards. The code keeps the Portuguese names: lanches = snacks, baratos = cheap ones, mostra = show.'),
  'predict': {'question': T('sem ToList, em que ordem aparecem as linhas where, select e mostra?', 'without ToList, in what order do the where, select and mostra lines appear?'),
    'options': {'batch': T('Todos os where, depois todos os select, depois todos os mostra', 'All the wheres, then all the selects, then all the mostras'),
                'interleaved': T('Um lanche de cada vez: where, select e mostra desse lanche, depois o próximo', 'One snack at a time: where, select and mostra for that snack, then the next'),
                'nothing': T('Nada aparece: a consulta nunca roda sem ToList', 'Nothing shows up: the query never runs without ToList')}},
  'feedback': {'right': T('isso: o Where e o Select não fazem nada na hora em que você escreve. Quando o foreach pede o próximo item, a consulta puxa um lanche, filtra, transforma e entrega. Um de cada vez, como uma esteira.',
                          'right: Where and Select do nothing at the moment you write them. When the foreach asks for the next item, the query pulls one snack, filters it, transforms it and hands it over. One at a time, like a conveyor belt.'),
               'wrong': T('é um de cada vez. LINQ sobre listas tem execução adiada: a consulta é uma receita, e quem a faz rodar é o foreach, pedindo item por item. Por isso where, select e mostra se intercalam.',
                          'it’s one at a time. LINQ over lists uses deferred execution: the query is a recipe, and what runs it is the foreach, asking item by item. That’s why where, select and mostra interleave.'),
               'skipped': T('sem palpite? Rode consultar e leia o terminal de cima para baixo.', 'no guess? Run query and read the terminal top to bottom.')},
  'coach': {'ui': T('palpite anotado. Leia o terminal de cima para baixo. Depois troque o modo para tolist e compare.', 'guess noted. Read the terminal top to bottom. Then switch the mode to tolist and compare.'),
            'cmd': T('palpite anotado. Rode consultar e depois consultar --modo tolist.', 'guess noted. Run query and then query --mode tolist.')},
  'tryNext': {'ui': T('Ligue a pipoca no modo adiado: ela foi adicionada depois da consulta e mesmo assim aparece. Depois tente no modo tolist.', 'Turn popcorn on in deferred mode: it was added after the query and still shows up. Then try it in tolist mode.'),
              'cmd': T('Rode consultar --pipoca sim e procure a Pipoca no terminal.', 'Run query --popcorn yes and look for Pipoca in the terminal.')},
  'why': {'simples': T('Uma List é uma fila de coisas do mesmo tipo, que cresce quando você adiciona. LINQ é um jeito de fazer perguntas para essa lista: "quais custam menos de 5?" (Where) e "me dê só o nome" (Select).\nO pulo do gato: escrever a pergunta não responde a pergunta. É como deixar um bilhete para a cozinha: "separar os lanches baratos". Nada acontece até alguém ir lá buscar. E se duas pessoas forem buscar, a cozinha separa duas vezes. Se você quer uma resposta guardada, tire uma foto: é o ToList.',
                       'A List is a line of things of the same type that grows when you add to it. LINQ is a way to ask that list questions: "which ones cost less than 5?" (Where) and "just give me the name" (Select).\nThe trick: writing the question doesn’t answer it. It’s like leaving a note for the kitchen: "set aside the cheap snacks". Nothing happens until someone goes to fetch them. And if two people go, the kitchen sorts them out twice. If you want a stored answer, take a photo: that’s ToList.'),
          'dev': T('Para quem vem do JS: arr.filter(...).map(...) cria arrays novos na hora; em C#, lista.Where(...).Select(...) devolve um IEnumerable<T> preguiçoso, mais parecido com um generator. Where, Select, OrderBy, Take e companhia são adiados; ToList, ToArray, Count, First, Sum, Any e o próprio foreach executam.\nConsequências práticas: cada execução percorre a fonte de novo (Count() e depois foreach = dois passeios), e mudanças na lista antes da execução aparecem no resultado. Materialize com ToList() quando for usar o resultado mais de uma vez ou quando precisar de uma "foto" daquele momento. Coleções do dia a dia: List<T> (lista que cresce), Dictionary<TKey,TValue> (busca por chave), HashSet<T> (sem repetidos) e arrays (tamanho fixo).',
                   'For JS folks: arr.filter(...).map(...) builds new arrays right away; in C#, list.Where(...).Select(...) returns a lazy IEnumerable<T>, closer to a generator. Where, Select, OrderBy, Take and friends are deferred; ToList, ToArray, Count, First, Sum, Any and the foreach itself execute.\nPractical consequences: each execution walks the source again (Count() then foreach = two trips), and changes to the list before execution show up in the result. Materialize with ToList() when you’ll use the result more than once or need a "snapshot" of that moment. Everyday collections: List<T> (growable list), Dictionary<TKey,TValue> (lookup by key), HashSet<T> (no duplicates) and arrays (fixed size).'),
          'especialista': T('Execução adiada vira problema sério com IQueryable (Entity Framework Core): a consulta é traduzida para SQL e cada enumeração é uma ida ao banco. Um Count() seguido de foreach são duas consultas; uma consulta enumerada dentro de um laço é o famoso N+1. A regra CA1851 (possíveis enumerações múltiplas de IEnumerable) pode ser ligada no projeto para avisar.\nOs operadores também diferem no "quanto" adiam: Where e Select fazem streaming (um item por vez), enquanto OrderBy e GroupBy precisam ler a fonte inteira na primeira chamada de MoveNext. Lambdas com efeito colateral, como as deste exemplo, são ótimas para aprender e péssimas em produção: o efeito acontece de novo a cada enumeração. E alterar a List enquanto um foreach a percorre lança InvalidOperationException; materialize antes ou percorra uma cópia.',
                            'Deferred execution becomes a serious problem with IQueryable (Entity Framework Core): the query is translated to SQL and each enumeration is a trip to the database. A Count() followed by a foreach is two queries; a query enumerated inside a loop is the famous N+1. Rule CA1851 (possible multiple enumerations of IEnumerable) can be turned on in the project to warn you.\nOperators also differ in "how much" they defer: Where and Select stream (one item at a time), while OrderBy and GroupBy must read the whole source on the first MoveNext. Lambdas with side effects, like the ones here, are great for learning and terrible in production: the effect happens again on every enumeration. And changing the List while a foreach walks it throws InvalidOperationException; materialize first or walk a copy.')},
  'break': {'mission': {'ui': T('hora de quebrar: no modo adiado, ligue "contar antes".', 'time to break it: in deferred mode, turn on "count first".'),
                        'cmd': T('hora de quebrar: rode consultar --contar sim', 'time to break it: run query --count yes')},
            'success': T('Quebrou: a consulta rodou {runs} vezes. O where foi chamado {whereN} vezes para {items} lanches, porque o Count() e o foreach fizeram o filtro cada um do zero. Numa lista é só desperdício; num banco de dados, seriam {runs} consultas.',
                         'Broken: the query ran {runs} times. The where was called {whereN} times for {items} snacks, because Count() and the foreach each filtered from scratch. On a list it’s just waste; on a database it would be {runs} queries.'),
            'calm': T('A consulta rodou {runs} vez: {whereN} chamadas do where e {selectN} do select, {shown} lanches mostrados. Para quebrar, conte antes do foreach no modo adiado.', 'The query ran {runs} time: {whereN} where calls and {selectN} select calls, {shown} snacks shown. To break it, count before the foreach in deferred mode.')},
  'hints': {'ui': T(['Mexa no modo e nas duas chaves; o terminal mostra cada chamada.', 'Cada execução de uma consulta adiada percorre a lista do começo.', 'No modo adiado, ligue "contar antes".'],
                    ['Change the mode and the two switches; the terminal shows each call.', 'Each execution of a deferred query walks the list from the start.', 'In deferred mode, turn on "count first".']),
            'cmd': T(['--modo, --contar e --pipoca são opcionais.', '--modo aceita adiado ou tolist; --contar e --pipoca aceitam sim ou nao.', 'consultar --contar sim'],
                     ['--mode, --count and --popcorn are optional.', '--mode takes deferred or tolist; --count and --popcorn take yes or no.', 'query --count yes'])},
  'errors': {'notInEnum.mode': T('Use adiado ou tolist.', 'Use deferred or tolist.'), 'notBool.countFirst': T('Use sim ou nao.', 'Use yes or no.'), 'notBool.late': T('Use sim ou nao.', 'Use yes or no.')},
  'controls': {'arg': T('Pergunta', 'Question'), 'mode': T('Modo da consulta', 'Query mode'), 'countFirst': T('Contar antes do foreach (Count())', 'Count before the foreach (Count())'), 'late': T('Adicionar pipoca depois da consulta', 'Add popcorn after the query')},
  'scene': {'label': T('Cardápio da cantina', 'Canteen menu'), 'empty': T('Rode para consultar.', 'Run the query.'),
    'runsM': T('vezes que a consulta rodou', 'times the query ran'), 'whereM': T('chamadas do where', 'where calls'), 'selectM': T('chamadas do select', 'select calls'), 'shownM': T('lanches mostrados', 'snacks shown'),
    'runLabel': T('Terminal', 'Terminal'),
    'deferredNote': T('Execução adiada: o foreach pediu um item por vez, e cada lanche passou pelo where e pelo select logo antes de ser mostrado.', 'Deferred execution: the foreach asked for one item at a time, and each snack went through where and select right before being shown.'),
    'twiceNote': T('Count() executou a consulta inteira só para contar, e o foreach executou de novo: {whereN} chamadas do where para {items} lanches.', 'Count() ran the whole query just to count, and the foreach ran it again: {whereN} where calls for {items} snacks.'),
    'tolistNote': T('Com ToList, a consulta roda uma vez na hora, guarda o resultado numa lista nova, e o foreach só lê essa lista.', 'With ToList, the query runs once right away, stores the result in a new list, and the foreach just reads that list.'),
    'lateNote': T('A Pipoca entrou no cardápio depois de a consulta ser escrita e mesmo assim apareceu: a consulta lê a lista no momento em que roda.', 'Pipoca joined the menu after the query was written and still showed up: the query reads the list when it runs.'),
    'lateListNote': T('Com ToList a foto foi tirada antes da Pipoca chegar, então ela não aparece.', 'With ToList the snapshot was taken before Pipoca arrived, so it doesn’t show up.')},
  'data': {},
  'recipe': {'steps': [
     T(f'Crie o projeto (se ainda não criou): {NEW} e entre em Cantina.', f'Create the project (if you haven’t yet): {NEW} and go into Cantina.'),
     T('Troque Program.cs por:\n' + sh(*CODE3_HEAD, '    });', '', 'lanches.Add(new("Pipoca", 3m));', 'Console.WriteLine($"total: {baratos.Count()}");', *CODE3_TAIL),
       'Replace Program.cs with:\n' + sh(*CODE3_HEAD, '    });', '', 'lanches.Add(new("Pipoca", 3m));', 'Console.WriteLine($"total: {baratos.Count()}");', *CODE3_TAIL)),
     T('Rode dotnet run. Depois troque o "    });" do Select por "    })" e uma linha nova "    .ToList();", e rode de novo.', 'Run dotnet run. Then change the Select’s "    });" to "    })" plus a new line "    .ToList();", and run again.')],
   'ok': T('na primeira vez o where aparece duas vezes para cada lanche (uma pelo Count, outra pelo foreach), a Pipoca aparece e o total é 3; com ToList, cada where aparece uma vez só, o total é 2 e a Pipoca some.', 'the first time where shows up twice for each snack (once for Count, once for the foreach), Pipoca shows up and the total is 3; with ToList, each where shows up only once, the total is 2 and Pipoca is gone.')}}

t3 = {'pt': {'objectives': ['Usar List<T> e as consultas Where e Select.', 'Explicar execução adiada.', 'Saber quando materializar com ToList.'], 'minutes': 20,
  'activity': 'Encenação: um aluno é a lista, outro é o Where, outro o Select e um quarto é o foreach. O foreach pede "próximo!" e o lanche passa de mão em mão. Depois, alguém pede um Count antes: quantas vezes o Where trabalhou?',
  'discussion': ['Quando faz sentido guardar uma "foto" do resultado e quando é melhor sempre ler o dado atual?', 'Por que contar e depois percorrer pode ser caro num banco de dados?'],
  'misconceptions': ['"Where filtra na hora, como o filter do JavaScript." Ele só monta a consulta; quem executa é quem percorre o resultado.']},
 'en': {'objectives': ['Use List<T> and the Where and Select queries.', 'Explain deferred execution.', 'Know when to materialize with ToList.'], 'minutes': 20,
  'activity': 'Role play: one student is the list, another the Where, another the Select and a fourth the foreach. The foreach calls "next!" and the snack goes hand to hand. Then someone asks for a Count first: how many times did Where work?',
  'discussion': ['When does it make sense to keep a "snapshot" of the result, and when is it better to always read current data?', 'Why can counting and then iterating be expensive against a database?'],
  'misconceptions': ['"Where filters right away, like JavaScript’s filter." It only builds the query; whoever walks the result runs it.']}}
write('03-colecoes-e-linq', s3, loc3('pt'), loc3('en'), t3)

# ================================================================== 4 · classes e records
KINDS4 = [opt('record', 'record', 'record'), opt('class', 'classe', 'class')]
COPY4 = [opt('with', 'with', 'with'), opt('assign', 'igual', 'assign')]
REC4 = ['record Pedido(string Aluno, string Lanche);']
CLS4 = ['class Pedido(string aluno, string lanche)', '{', '    public string Aluno { get; set; } = aluno;', '    public string Lanche { get; set; } = lanche;', '}']
WITH4 = ['var b = a with { Lanche = "Bolo" };']
ASSIGN4 = ['var b = a;', 'b.Lanche = "Bolo";']
BODY4 = ['var outro = new Pedido("Ana", "Coxinha");', '', 'Console.WriteLine($"a: {a.Lanche}, b: {b.Lanche}");', 'Console.WriteLine(a == outro);', '']
E8852 = "!…/Program.cs(3,1): error CS8852: Init-only property or indexer 'Pedido.Lanche' can only be assigned in an object initializer, or on 'this' or 'base' in an instance constructor or an 'init' accessor."
E8858 = "!…/Program.cs(2,9): error CS8858: The receiver type 'Pedido' is not a valid record type and is not a struct type."
s4 = step('cs-classes-e-records', 4, TRACK, 20, ['csharp', 'class', 'record', 'igualdade', 'referencia'], ['cs-colecoes-e-linq'], SIM,
  loc('copiar', 'copy'),
  {'name': 'text', 'required': False, 'default': loc('pedido da Ana', 'Ana’s order'), 'ui': 'text'},
  [flag('kind', 'tipo', 'kind', 'enum', options=KINDS4, default='record', ui='select'),
   flag('copy', 'copia', 'copy', 'enum', options=COPY4, default='with', ui='select')],
  {'options': ['true', 'false', 'error'], 'answer': 'true'}, 'aliasBug',
  {'live': True,
   'consts': {'rec': REC4, 'cls': CLS4, 'withL': WITH4, 'assignL': ASSIGN4, 'body': BODY4, 'e8852': E8852, 'e8858': E8858},
   'compute': {
     'isRecord': "kind == 'record'",
     'isWith': "copy == 'with'",
     'compiles': 'isRecord == isWith',
     'alias': '!isRecord && !isWith',
     'aText': "alias ? 'Bolo' : 'Coxinha'",
     'equalText': "isRecord ? 'True' : 'False'",
     'errLine': 'isRecord ? e8852 : e8858',
     'calmLead': "compiles ? ((lang == 'pt' ? 'O pedido da Ana continua ' : 'Ana’s order is still ') + aText + '.') : calmFail"},
   'cases': [
     {'when': 'alias', 'flags': ['aliasBug']},
     {'when': '!compiles', 'flags': ['compileError']},
     {'when': 'compiles && isRecord', 'flags': ['valueEquality']},
     {'when': 'true', 'vars': {'aText': 'aText', 'equal': 'equalText', 'calmLead': 'calmLead'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@buildM', 'value': "=compiles ? '@ok' : '@fail'", 'tone': "=compiles ? 'ok' : 'bad'"},
       {'label': '@aM', 'value': "=compiles ? aText : '—'", 'tone': "=alias ? 'bad' : (compiles ? 'ok' : 'dim')"},
       {'label': '@eqM', 'value': "=compiles ? equalText : '—'", 'tone': "=compiles ? 'info' : 'dim'"}]},
     {'type': 'terminal', 'label': 'Program.cs', 'lines': "=concat(['var a = new Pedido(\"Ana\", \"Coxinha\");'], isWith ? withL : assignL, body, isRecord ? rec : cls)"},
     {'type': 'terminal', 'label': '@runLabel', 'lines': "=compiles ? ['$ dotnet run', 'a: ' + aText + ', b: Bolo', equalText] : ['$ dotnet run', errLine, '~The build failed. Fix the build errors and run again.']"},
     {'type': 'table', 'when': '=compiles', 'label': '@memLabel', 'columns': ['@cVar', '@cObj', '@cLanche'],
      'rows': "=alias ? [['a', '#1', 'Bolo'], ['b', '#1', 'Bolo'], ['outro', '#2', 'Coxinha']] : [['a', '#1', 'Coxinha'], ['b', '#2', 'Bolo'], ['outro', '#3', 'Coxinha']]",
      'tones': "=alias ? ['bad', 'bad', 'neutral'] : ['ok', 'neutral', 'ok']", 'caption': "=alias ? '@capAlias' : '@capRecord'"},
     {'type': 'note', 'when': '=alias', 'tone': 'bad', 'text': '@aliasNote'},
     {'type': 'note', 'when': '=compiles && isRecord', 'tone': 'ok', 'text': '@recordNote'},
     {'type': 'note', 'when': '=!compiles && isRecord', 'tone': 'warn', 'text': '@initNote'},
     {'type': 'note', 'when': '=!compiles && !isRecord', 'tone': 'warn', 'text': '@withNote'}]})

def loc4(L):
  pt, T = mk(L)
  return {
  'title': T('Classes e records', 'Classes and records'),
  'subtitle': T('Dois pedidos iguais são o mesmo pedido? E se eu copiar e mudar a cópia, o original muda?', 'Are two identical orders the same order? And if I copy one and change the copy, does the original change?'),
  'mission': T('A Ana pediu uma coxinha. A amiga quer "o mesmo pedido, mas com bolo". O caixa copia o pedido da Ana e troca o lanche. Escolha se Pedido é uma class ou um record, e se a cópia é feita com with ou com um simples sinal de igual, e veja o que acontece com o pedido da Ana.',
               'Ana ordered a coxinha (a Brazilian savory snack). Her friend wants "the same order, but with cake (Bolo)". The till copies Ana’s order and changes the snack. Choose whether Pedido (order) is a class or a record, and whether the copy is made with with or a plain equals sign, and see what happens to Ana’s order.'),
  'predict': {'question': T('com record, dois pedidos criados separadamente com os mesmos dados ("Ana", "Coxinha"): a == outro dá…', 'with a record, two orders created separately with the same data ("Ana", "Coxinha"): a == outro gives…'),
    'options': {'true': T('True: mesmos dados, mesmo pedido', 'True: same data, same order'), 'false': T('False: são dois objetos diferentes', 'False: they’re two different objects'), 'error': T('Erro: não dá para comparar objetos com ==', 'Error: you can’t compare objects with ==')}},
  'feedback': {'right': T('isso! record compara pelo conteúdo: o compilador gera Equals, GetHashCode e o == para olhar campo por campo. Numa class, o == pergunta "é o mesmo objeto?", e aí daria False.',
                          'right! A record compares by content: the compiler generates Equals, GetHashCode and == to look field by field. In a class, == asks "is it the same object?", and that would give False.'),
               'wrong': T('dá True. record compara pelo conteúdo (igualdade de valor). Quem compara pela identidade, "é o mesmo objeto na memória?", é a class: lá o mesmo teste daria False.',
                          'it’s True. A record compares by content (value equality). The one comparing by identity, "is it the same object in memory?", is the class: there the same test would give False.'),
               'skipped': T('sem palpite? Rode copiar e olhe a última linha do terminal; depois tente com --tipo classe --copia igual.', 'no guess? Run copy and look at the last terminal line; then try --kind class --copy assign.')},
  'coach': {'ui': T('palpite anotado. Olhe a última linha do terminal. Depois troque para classe e copia igual.', 'guess noted. Look at the last terminal line. Then switch to class and assign copy.'),
            'cmd': T('palpite anotado. Rode copiar e depois copiar --tipo classe --copia igual.', 'guess noted. Run copy and then copy --kind class --copy assign.')},
  'tryNext': {'ui': T('Escolha classe com with: não compila (CS8858). O with é do record (e de structs); classes não ganham cópia de graça.', 'Pick class with with: it doesn’t compile (CS8858). with belongs to records (and structs); classes don’t get copying for free.'),
              'cmd': T('Rode copiar --tipo classe e leia o erro CS8858.', 'Run copy --kind class and read error CS8858.')},
  'why': {'simples': T('Uma class é a planta de uma casa: com ela você constrói objetos. A variável não guarda a casa, guarda o endereço. Se você escreve var b = a, agora são dois papéis com o mesmo endereço: pintar a casa "do b" pinta a casa "do a", porque é a mesma casa.\nUm record é feito para guardar dados, como uma ficha de pedido. Ele vem pronto para comparar pelo conteúdo (duas fichas com o mesmo texto são iguais) e, em vez de rabiscar a ficha, você tira uma cópia com uma mudança: a with { Lanche = "Bolo" }. A ficha da Ana continua intacta.',
                       'A class is a house blueprint: you build objects with it. The variable doesn’t hold the house, it holds the address. If you write var b = a, you now have two slips of paper with the same address: painting "b’s" house paints "a’s" house, because it’s the same house.\nA record is made to hold data, like an order slip. It comes ready to compare by content (two slips with the same text are equal) and, instead of scribbling on the slip, you make a copy with one change: a with { Lanche = "Bolo" }. Ana’s slip stays intact.'),
          'dev': T('No JS, objetos também são por referência: const b = a; b.lanche = "Bolo" muda a, e {...a, lanche: "Bolo"} é a cópia rasa. Em C#, record Pedido(string Aluno, string Lanche); declara numa linha um tipo com construtor, propriedades init (só podem ser definidas na criação), ToString legível, Equals/GetHashCode por valor e suporte a with, que é o "spread" do C#.\nUse class para coisas com identidade e comportamento que mudam com o tempo (um serviço, uma conta com saldo) e record para dados: DTOs de API, mensagens, valores de domínio. Atenção: record class continua sendo tipo de referência (a == compara valores, mas a variável ainda guarda uma referência); record struct é tipo de valor.',
                   'In JS, objects are by reference too: const b = a; b.snack = "Cake" changes a, and {...a, snack: "Cake"} is the shallow copy. In C#, record Pedido(string Aluno, string Lanche); declares in one line a type with a constructor, init properties (settable only at creation), a readable ToString, value-based Equals/GetHashCode and support for with, which is C#’s "spread".\nUse class for things with identity and behavior that change over time (a service, an account with a balance) and record for data: API DTOs, messages, domain values. Careful: a record class is still a reference type (== compares values, but the variable still holds a reference); a record struct is a value type.'),
          'especialista': T('O with faz cópia rasa: se o record tem uma List<string> Itens, o original e a cópia passam a compartilhar a mesma lista, e adicionar um item numa aparece na outra. Para imutabilidade de verdade, use coleções imutáveis (ImmutableList, ou IReadOnlyList preenchida com uma cópia) e lembre que a igualdade gerada compara a referência da lista, não o conteúdo dela.\nA igualdade de record também considera o tipo em tempo de execução (EqualityContract): um record derivado nunca é igual ao base, mesmo com os mesmos campos. Records funcionam bem como chaves de Dictionary e HashSet porque GetHashCode acompanha os campos, desde que nada mude depois de inserido. E o construtor primário de class (C# 12), usado aqui, só cria parâmetros: quem decide se viram propriedades e se podem mudar é você.',
                            'with makes a shallow copy: if the record has a List<string> Itens, the original and the copy now share the same list, and adding an item to one shows up in the other. For real immutability, use immutable collections (ImmutableList, or an IReadOnlyList filled with a copy) and remember the generated equality compares the list’s reference, not its contents.\nRecord equality also considers the runtime type (EqualityContract): a derived record is never equal to its base, even with the same fields. Records work well as Dictionary and HashSet keys because GetHashCode follows the fields, as long as nothing changes after insertion. And the class primary constructor (C# 12), used here, only creates parameters: you decide whether they become properties and whether they can change.')},
  'break': {'mission': {'ui': T('hora de quebrar: escolha classe e copia igual.', 'time to break it: pick class and assign copy.'),
                        'cmd': T('hora de quebrar: rode copiar --tipo classe --copia igual', 'time to break it: run copy --kind class --copy assign')},
            'success': T('Quebrou: b = a copiou só o endereço. Trocar o lanche da "cópia" trocou o da Ana, que agora vai receber {aText} sem ter pedido. E a == outro deu {equal}: com class, mesmo conteúdo não quer dizer mesmo pedido.',
                         'Broken: b = a copied only the address. Changing the "copy’s" snack changed Ana’s, who will now get {aText} without ordering it. And a == outro gave {equal}: with a class, same content doesn’t mean same order.'),
            'calm': T('{calmLead} Para quebrar, use uma classe e copie com um simples sinal de igual.', '{calmLead} To break it, use a class and copy with a plain equals sign.')},
  'hints': {'ui': T(['Escolha o tipo de Pedido e o jeito de copiar.', 'Com class, a variável guarda um endereço.', 'Escolha classe e copia igual.'],
                    ['Pick Pedido’s kind and how to copy it.', 'With a class, the variable holds an address.', 'Pick class and assign copy.']),
            'cmd': T(['--tipo e --copia são opcionais.', '--tipo aceita record ou classe; --copia aceita with ou igual.', 'copiar --tipo classe --copia igual'],
                     ['--kind and --copy are optional.', '--kind takes record or class; --copy takes with or assign.', 'copy --kind class --copy assign'])},
  'errors': {'notInEnum.kind': T('Use record ou classe.', 'Use record or class.'), 'notInEnum.copy': T('Use with ou igual.', 'Use with or assign.')},
  'controls': {'arg': T('Pedido', 'Order'), 'kind': T('Pedido é um…', 'Pedido is a…'), 'copy': T('Como copiar', 'How to copy')},
  'scene': {'label': T('Pedidos da cantina', 'Canteen orders'), 'empty': T('Rode para copiar o pedido.', 'Run to copy the order.'),
    'buildM': T('compilação', 'build'), 'ok': T('ok', 'ok'), 'fail': T('falhou', 'failed'), 'aM': T('lanche da Ana no fim', 'Ana’s snack at the end'), 'eqM': T('a == outro', 'a == outro'),
    'runLabel': T('Terminal', 'Terminal'), 'memLabel': T('Memória: quem aponta para qual objeto', 'Memory: who points to which object'),
    'cVar': T('variável', 'variable'), 'cObj': T('objeto', 'object'), 'cLanche': T('Lanche', 'Lanche'),
    'capAlias': T('a e b apontam para o mesmo objeto #1', 'a and b point to the same object #1'), 'capRecord': T('três objetos; a e outro são iguais pelo conteúdo', 'three objects; a and outro are equal by content'),
    'aliasNote': T('b não é uma cópia: é outro nome para o mesmo pedido. Mexeu em b, mexeu em a.', 'b isn’t a copy: it’s another name for the same order. Touch b, you touch a.'),
    'recordNote': T('with criou um pedido novo (#2) só com o lanche trocado; o da Ana ficou intacto. E a == outro compara o conteúdo.', 'with created a new order (#2) with only the snack changed; Ana’s stayed intact. And a == outro compares content.'),
    'initNote': T('As propriedades de um record posicional são init: só podem ser definidas na criação. Para "mudar", crie uma cópia com with.', 'A positional record’s properties are init: they can only be set at creation. To "change" one, make a copy with with.'),
    'withNote': T('with só funciona com records, structs e tipos anônimos. Numa class, você teria que escrever a cópia na mão.', 'with only works with records, structs and anonymous types. In a class, you’d have to write the copy by hand.')},
  'data': {'calmFail': T('Nem compilou: o programa não chegou a rodar, então o pedido da Ana nem foi tocado.', 'It didn’t even compile: the program never ran, so Ana’s order wasn’t touched.')},
  'recipe': {'steps': [
     T(f'Crie o projeto (se ainda não criou): {NEW} e entre em Cantina.', f'Create the project (if you haven’t yet): {NEW} and go into Cantina.'),
     T('Troque Program.cs por:\n' + sh('var a = new Pedido("Ana", "Coxinha");', *ASSIGN4, *BODY4, *CLS4),
       'Replace Program.cs with:\n' + sh('var a = new Pedido("Ana", "Coxinha");', *ASSIGN4, *BODY4, *CLS4)),
     T('Rode dotnet run. Depois troque a class pela linha record Pedido(string Aluno, string Lanche); e as duas linhas do b por var b = a with { Lanche = "Bolo" }; e rode de novo.', 'Run dotnet run. Then replace the class with the line record Pedido(string Aluno, string Lanche); and the two b lines with var b = a with { Lanche = "Bolo" }; and run again.')],
   'ok': T('com a class aparecem "a: Bolo, b: Bolo" e False; com o record aparecem "a: Coxinha, b: Bolo" e True.', 'with the class you see "a: Bolo, b: Bolo" and False; with the record you see "a: Coxinha, b: Bolo" and True.')}}

t4 = {'pt': {'objectives': ['Diferenciar class e record.', 'Explicar referência: duas variáveis, um objeto.', 'Usar with para copiar com mudança.'], 'minutes': 20,
  'activity': 'Dois alunos recebem o mesmo "endereço" num papel (o número de uma carteira). Um deles coloca um estojo na carteira. O outro vai lá e encontra o estojo. Depois façam o mesmo com uma ficha de pedido fotocopiada (record com with): rabiscar a cópia não muda o original.',
  'discussion': ['Que coisas da escola têm identidade (um aluno) e quais são só dados (uma nota de 8,5)?', 'Quando comparar pelo conteúdo pode enganar?'],
  'misconceptions': ['"var b = a faz uma cópia." Para class, copia só a referência; os dois nomes apontam para o mesmo objeto.', '"record é tipo de valor." record (record class) é de referência com igualdade por valor; record struct é que é tipo de valor.']},
 'en': {'objectives': ['Tell class from record.', 'Explain references: two variables, one object.', 'Use with to copy with a change.'], 'minutes': 20,
  'activity': 'Two students get the same "address" on paper (a desk number). One puts a pencil case on the desk. The other goes there and finds the pencil case. Then do the same with a photocopied order slip (record with with): scribbling on the copy doesn’t change the original.',
  'discussion': ['Which school things have identity (a student) and which are just data (a grade of 8.5)?', 'When can comparing by content be misleading?'],
  'misconceptions': ['"var b = a makes a copy." For a class it copies only the reference; both names point to the same object.', '"A record is a value type." A record (record class) is a reference type with value equality; record struct is the value type.']}}
write('04-classes-e-records', s4, loc4('pt'), loc4('en'), t4)

# ================================================================== 5 · nulabilidade
ACC5 = [opt('dot', 'ponto', 'dot'), opt('cond', 'interrogacao', 'conditional'), opt('coalesce', 'padrao', 'default'), opt('bang', 'exclamacao', 'bang')]
NUL5 = [opt('enable', 'enable', 'enable'), opt('disable', 'disable', 'disable')]
CALL5 = {'dot': 'Console.WriteLine(aluno.Apelido.ToUpper());', 'cond': 'Console.WriteLine(aluno.Apelido?.ToUpper());',
         'coalesce': 'Console.WriteLine(aluno.Apelido?.ToUpper() ?? "(sem apelido)");', 'bang': 'Console.WriteLine(aluno.Apelido!.ToUpper());'}
NRE = '!Unhandled exception. System.NullReferenceException: Object reference not set to an instance of an object.'
s5 = step('cs-nulabilidade', 5, TRACK, 20, ['csharp', 'null', 'nullable', 'nrt'], ['cs-classes-e-records'], SIM,
  loc('cumprimentar', 'greet'),
  {'name': 'text', 'required': False, 'default': loc('Bia', 'Bia'), 'ui': 'text'},
  [flag('access', 'acesso', 'access', 'enum', options=ACC5, default='coalesce', ui='select'),
   flag('nullable', 'nullable', 'nullable', 'enum', options=NUL5, default='enable', ui='select'),
   flag('hasNick', 'tem-apelido', 'has-nickname', 'bool', default=False, ui='switch')],
  {'options': ['error', 'warning', 'nothing'], 'answer': 'warning'}, 'nullCrash',
  {'live': True,
   'consts': {'calls': CALL5, 'nre': NRE},
   'compute': {
     'on': "nullable == 'enable'",
     'risky': "access == 'dot' || access == 'bang'",
     'warned': "on && access == 'dot'",
     'crash': '!hasNick && risky',
     'nickLit': "hasNick ? '\"Tatá\"' : 'null'",
     'line2': "hasNick ? 'TATÁ' : (access == 'coalesce' ? '(sem apelido)' : '')",
     'how': "warned ? howWarned : (on && access == 'bang' ? howBang : howOff)",
     'calmLead': 'risky && hasNick ? calmLucky : calmSafe'},
   'cases': [
     {'when': 'crash', 'flags': ['nullCrash']},
     {'when': 'warned', 'flags': ['compilerWarned']},
     {'when': "!crash && access == 'cond' && !hasNick", 'flags': ['blankLine']},
     {'when': 'true', 'vars': {'how': 'how', 'name': 'text', 'calmLead': 'calmLead'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@warnM', 'value': "=warned ? 'CS8602' : '@none'", 'tone': "=warned ? 'warn' : 'dim'"},
       {'label': '@runM', 'value': "=crash ? 'NullReferenceException' : '@ok'", 'tone': "=crash ? 'bad' : 'ok'"},
       {'label': '@nickM', 'value': "=hasNick ? '\"Tatá\"' : 'null'", 'tone': "=hasNick ? 'info' : 'warn'"}]},
     {'type': 'terminal', 'label': '@projLabel', 'lines': "=['<Nullable>' + nullable + '</Nullable>']"},
     {'type': 'terminal', 'label': 'Program.cs', 'lines': "=['var aluno = new Aluno(\"' + text + '\", ' + nickLit + ');', 'Console.WriteLine($\"Oi, {aluno.Nome}!\");', lookup(calls, access, ''), '', on ? 'record Aluno(string Nome, string? Apelido);' : 'record Aluno(string Nome, string Apelido);']"},
     {'type': 'terminal', 'label': '@runLabel', 'lines': "=concat(['$ dotnet run'], warned ? ['?…/Program.cs(3,19): warning CS8602: Dereference of a possibly null reference.'] : [], ['Oi, ' + text + '!'], crash ? [nre, '~   at Program.<Main>$(String[] args) in …/Program.cs:line 3'] : [line2])"},
     {'type': 'flow', 'label': '@flowLabel', 'steps': [
       {'label': '@fCompile', 'sub': "=warned ? '@sWarn' : (on && access == 'bang' ? '@sSilenced' : (on ? '@sClean' : '@sOff'))", 'tone': "=warned ? 'warn' : (on && access == 'bang' ? 'warn' : (on ? 'ok' : 'dim'))"},
       {'label': '@fRun', 'sub': "=crash ? '@sBoom' : '@sFine'", 'tone': "=crash ? 'bad' : 'ok'"}]},
     {'type': 'note', 'when': '=crash && warned', 'tone': 'bad', 'text': '@crashWarnedNote'},
     {'type': 'note', 'when': "=crash && on && access == 'bang'", 'tone': 'bad', 'text': '@crashBangNote'},
     {'type': 'note', 'when': '=crash && !on', 'tone': 'bad', 'text': '@crashOffNote'},
     {'type': 'note', 'when': '=!crash && warned', 'tone': 'warn', 'text': '@luckyNote'},
     {'type': 'note', 'when': "=!crash && access == 'cond' && !hasNick", 'tone': 'info', 'text': '@blankNote'},
     {'type': 'note', 'when': "=!crash && access == 'coalesce'", 'tone': 'ok', 'text': '@coalesceNote'}]})

def loc5(L):
  pt, T = mk(L)
  return {
  'title': T('Nulabilidade', 'Nullability'),
  'subtitle': T('O aluno sem apelido, o ponto que explode e o compilador que avisa antes', 'The student with no nickname, the dot that blows up and the compiler that warns you first'),
  'mission': T('O caixa cumprimenta cada aluno e grita o apelido em maiúsculas. Só que nem todo mundo tem apelido: aí o valor é null, que quer dizer "nada aqui". Escolha como o código acessa o apelido (ponto, ?., ?? ou !), ligue ou desligue a checagem de nulos do projeto e veja quem avisa e quem explode.',
               'The till greets each student and shouts their nickname (Apelido) in capitals. But not everyone has a nickname: then the value is null, which means "nothing here". Choose how the code reaches the nickname (dot, ?., ?? or !), turn the project’s null checking on or off and see who warns and who blows up.'),
  'predict': {'question': T('com <Nullable>enable</Nullable> (o padrão do dotnet new) e string? Apelido, o que acontece ao compilar aluno.Apelido.ToUpper()?', 'with <Nullable>enable</Nullable> (the dotnet new default) and string? Apelido, what happens when you compile aluno.Apelido.ToUpper()?'),
    'options': {'error': T('Não compila', 'It doesn’t compile'), 'warning': T('Compila, mas com um aviso (CS8602)', 'It compiles, but with a warning (CS8602)'), 'nothing': T('Compila sem aviso nenhum', 'It compiles with no warning at all')}},
  'feedback': {'right': T('isso: o compilador sabe que string? pode ser null e avisa com CS8602 ("possível referência nula"). Mas é só aviso: o programa compila e, se o apelido for mesmo null, explode rodando.',
                          'right: the compiler knows string? may be null and warns with CS8602 ("possibly null reference"). But it’s just a warning: the program compiles and, if the nickname really is null, it blows up at run time.'),
               'wrong': T('compila com o aviso CS8602. Os tipos anuláveis de referência são uma análise do compilador: ele avisa, mas não impede. Por padrão, aviso não barra a compilação.',
                          'it compiles with warning CS8602. Nullable reference types are a compiler analysis: it warns, but it doesn’t stop you. By default, a warning doesn’t block the build.'),
               'skipped': T('sem palpite? Rode cumprimentar --acesso ponto e olhe a linha amarela do terminal.', 'no guess? Run greet --access dot and look at the yellow terminal line.')},
  'coach': {'ui': T('palpite anotado. Troque o acesso para "ponto" e olhe o terminal. Depois tente "exclamacao".', 'guess noted. Switch the access to "dot" and look at the terminal. Then try "bang".'),
            'cmd': T('palpite anotado. Rode cumprimentar --acesso ponto e depois cumprimentar --acesso exclamacao.', 'guess noted. Run greet --access dot and then greet --access bang.')},
  'tryNext': {'ui': T('Agora use "ponto" com um aluno que tem apelido: funciona e grita TATÁ, mas o aviso continua. O aviso fala do dia em que vier alguém sem apelido.', 'Now use "dot" with a student who has a nickname: it works and shouts TATÁ, but the warning stays. The warning is about the day someone without a nickname shows up.'),
              'cmd': T('Rode cumprimentar --acesso ponto --tem-apelido sim e repare que o aviso não some.', 'Run greet --access dot --has-nickname yes and notice the warning doesn’t go away.')},
  'why': {'simples': T('null é uma caixa vazia. Pedir "o apelido em maiúsculas" de uma caixa vazia é como pedir para alguém ler um papel que não existe: o programa para com NullReferenceException, o erro mais famoso do mundo .NET.\nO C# moderno ajuda: quando você escreve string? (com interrogação), está dizendo "aqui pode não ter nada". O compilador passa a vigiar e avisa se você usar sem conferir. Três jeitos seguros de conferir: ?. ("se tiver, faça"), ?? ("se não tiver, use este outro") ou um if. E um jeito de mentir: ! ("confia, tem sim"). Mentir para o compilador cala o aviso, mas não enche a caixa.',
                       'null is an empty box. Asking for "the nickname in capitals" from an empty box is like asking someone to read a piece of paper that doesn’t exist: the program stops with a NullReferenceException, the most famous error in the .NET world.\nModern C# helps: when you write string? (with a question mark), you’re saying "there may be nothing here". The compiler starts watching and warns if you use it without checking. Three safe ways to check: ?. ("if there is one, do it"), ?? ("if not, use this instead") or an if. And one way to lie: ! ("trust me, it’s there"). Lying to the compiler silences the warning, but it doesn’t fill the box.'),
          'dev': T('Para quem vem do TypeScript: <Nullable>enable</Nullable> é parecido com strictNullChecks. string é "não nulo" e string? é "pode ser nulo"; ?. e ?? funcionam igual ao TS, e ! é o mesmo operador de "non-null assertion". Os projetos criados com dotnet new já vêm com Nullable ligado.\nDiferenças importantes: no C# são avisos, não erros (CS8602 ao desreferenciar, CS8600 ao jogar um possível null numa variável não anulável, CS8618 para propriedade não anulável sem valor, CS8625 ao passar null para um parâmetro não anulável), e não há checagem em tempo de execução. Para barrar a compilação, use <WarningsAsErrors>nullable</WarningsAsErrors>. Para validar entrada pública, use ArgumentNullException.ThrowIfNull(x).',
                   'For TypeScript folks: <Nullable>enable</Nullable> is similar to strictNullChecks. string is "not null" and string? is "may be null"; ?. and ?? work like in TS, and ! is the same "non-null assertion" operator. Projects created with dotnet new come with Nullable on.\nKey differences: in C# these are warnings, not errors (CS8602 when dereferencing, CS8600 when putting a possible null into a non-nullable variable, CS8618 for a non-nullable property with no value, CS8625 when passing null to a non-nullable parameter), and there’s no runtime check. To fail the build, use <WarningsAsErrors>nullable</WarningsAsErrors>. To validate public input, use ArgumentNullException.ThrowIfNull(x).'),
          'especialista': T('Os tipos anuláveis de referência são só anotação e análise de fluxo: string e string? são o mesmo tipo em tempo de execução, então uma biblioteca antiga, um JSON desserializado ou reflection podem entregar null num string "não nulo". Nas bordas do sistema (APIs, banco, arquivos), valide de verdade.\nA análise entende ifs, is null, ?? e retornos antecipados, e você pode ensinar o compilador com atributos como [NotNullWhen(true)] (o padrão do TryParse), [MaybeNull] e [MemberNotNull]. Em DTOs, prefira membros required (C# 11) a "= null!": assim quem cria o objeto é obrigado a preencher. Não confunda com int? (Nullable<int>), que é um tipo de valor de verdade, com HasValue e Value, checado em tempo de execução. Migrando um projeto grande, ligue por arquivo com #nullable enable e avance aos poucos.',
                            'Nullable reference types are only annotations and flow analysis: string and string? are the same type at run time, so an old library, a deserialized JSON or reflection can hand you null in a "non-null" string. At the system’s edges (APIs, database, files), validate for real.\nThe analysis understands ifs, is null, ?? and early returns, and you can teach the compiler with attributes like [NotNullWhen(true)] (the TryParse pattern), [MaybeNull] and [MemberNotNull]. In DTOs, prefer required members (C# 11) over "= null!": that way whoever creates the object must fill it in. Don’t confuse this with int? (Nullable<int>), which is a real value type, with HasValue and Value, checked at run time. When migrating a big project, turn it on per file with #nullable enable and move gradually.')},
  'break': {'mission': {'ui': T('hora de quebrar: acesse o apelido com "exclamacao", sem apelido.', 'time to break it: reach the nickname with "bang", with no nickname.'),
                        'cmd': T('hora de quebrar: rode cumprimentar --acesso exclamacao', 'time to break it: run greet --access bang')},
            'success': T('Quebrou: NullReferenceException na linha 3. {how} {name} recebeu o oi e o caixa travou no apelido que não existia.',
                         'Broken: NullReferenceException on line 3. {how} {name} got a hello and the till froze on a nickname that didn’t exist.'),
            'calm': T('{calmLead} Para quebrar, use ! num aluno sem apelido.', '{calmLead} To break it, use ! on a student with no nickname.')},
  'hints': {'ui': T(['Escolha o acesso, a checagem do projeto e se o aluno tem apelido.', 'Dois acessos não conferem se tem alguma coisa na caixa.', 'Escolha "exclamacao" com o aluno sem apelido.'],
                    ['Pick the access, the project check and whether the student has a nickname.', 'Two of the accesses don’t check whether there’s anything in the box.', 'Pick "bang" with a student with no nickname.']),
            'cmd': T(['O nome do aluno vai entre aspas; --acesso, --nullable e --tem-apelido são opcionais.', '--acesso aceita ponto, interrogacao, padrao ou exclamacao.', 'cumprimentar --acesso exclamacao'],
                     ['The student’s name goes in quotes; --access, --nullable and --has-nickname are optional.', '--access takes dot, conditional, default or bang.', 'greet --access bang'])},
  'errors': {'notInEnum.access': T('Use ponto, interrogacao, padrao ou exclamacao.', 'Use dot, conditional, default or bang.'), 'notInEnum.nullable': T('Use enable ou disable.', 'Use enable or disable.'), 'notBool.hasNick': T('Use sim ou nao.', 'Use yes or no.')},
  'controls': {'arg': T('Nome do aluno', 'Student’s name'), 'access': T('Como ler o apelido', 'How to read the nickname'), 'nullable': T('Checagem de nulos no projeto', 'Null checking in the project'), 'hasNick': T('O aluno tem apelido', 'The student has a nickname')},
  'scene': {'label': T('Cumprimentos do caixa', 'Till greetings'), 'empty': T('Rode para cumprimentar.', 'Run to greet.'),
    'warnM': T('aviso do compilador', 'compiler warning'), 'runM': T('rodando', 'at run time'), 'nickM': T('apelido', 'nickname'), 'none': T('nenhum', 'none'), 'ok': T('ok', 'ok'),
    'projLabel': T('Cantina.csproj (trecho)', 'Cantina.csproj (excerpt)'), 'runLabel': T('Terminal', 'Terminal'),
    'flowLabel': T('Quem pegou o problema', 'Who caught the problem'), 'fCompile': T('compilador', 'compiler'), 'fRun': T('execução', 'run time'),
    'sWarn': T('avisou: CS8602', 'warned: CS8602'), 'sSilenced': T('calado pelo !', 'silenced by !'), 'sClean': T('nada a avisar', 'nothing to warn about'), 'sOff': T('checagem desligada', 'checking off'),
    'sBoom': T('explodiu', 'blew up'), 'sFine': T('tudo certo', 'all good'),
    'crashWarnedNote': T('O compilador avisou (CS8602) e o aviso foi ignorado. Sem apelido, o ponto explodiu.', 'The compiler warned (CS8602) and the warning was ignored. With no nickname, the dot blew up.'),
    'crashBangNote': T('O ! disse ao compilador "confia, não é null". Ele confiou, ficou quieto, e a execução explodiu do mesmo jeito.', 'The ! told the compiler "trust me, it isn’t null". It trusted you, stayed quiet, and execution blew up anyway.'),
    'crashOffNote': T('Com Nullable desligado, o compilador nem sabe que o apelido pode faltar: zero aviso e a mesma explosão.', 'With Nullable off, the compiler doesn’t even know the nickname may be missing: zero warnings and the same blow-up.'),
    'luckyNote': T('Desta vez tinha apelido e deu certo, mas o aviso continua: o código não está preparado para o aluno sem apelido.', 'This time there was a nickname and it worked, but the warning stays: the code isn’t ready for a student without one.'),
    'blankNote': T('Com ?., sem apelido o resultado é null e o WriteLine imprime uma linha em branco. Não explode, mas também não diz nada.', 'With ?., no nickname makes the result null and WriteLine prints a blank line. No blow-up, but it says nothing either.'),
    'coalesceNote': T('?. evita a explosão e ?? troca o vazio por um texto padrão. Seguro e claro.', '?. avoids the blow-up and ?? swaps the empty value for a default text. Safe and clear.')},
  'data': {'calmSafe': T('Nada explodiu: o apelido foi lido com segurança.', 'Nothing blew up: the nickname was read safely.'),
           'calmLucky': T('Nada explodiu, mas só porque este aluno tinha apelido: o código não conferiu nada, e o aviso (se estiver ligado) continua.', 'Nothing blew up, but only because this student had a nickname: the code checked nothing, and the warning (if it is on) stays.'),
           'howWarned': T('O compilador tinha avisado (CS8602), e o aviso ficou para trás.', 'The compiler had warned (CS8602), and the warning was left behind.'),
           'howBang': T('O ! calou o compilador, mas não colocou apelido nenhum na caixa.', 'The ! silenced the compiler, but it didn’t put any nickname in the box.'),
           'howOff': T('Com a checagem de nulos desligada, ninguém avisou nada.', 'With null checking off, nobody warned you at all.')},
  'recipe': {'steps': [
     T(f'Crie o projeto (se ainda não criou): {NEW} e entre em Cantina. Abra Cantina.csproj e confira a linha <Nullable>enable</Nullable>.', f'Create the project (if you haven’t yet): {NEW} and go into Cantina. Open Cantina.csproj and find the line <Nullable>enable</Nullable>.'),
     T('Troque Program.cs por:\n' + sh('var aluno = new Aluno("Bia", null);', 'Console.WriteLine($"Oi, {aluno.Nome}!");', CALL5['dot'], '', 'record Aluno(string Nome, string? Apelido);'),
       'Replace Program.cs with:\n' + sh('var aluno = new Aluno("Bia", null);', 'Console.WriteLine($"Oi, {aluno.Nome}!");', CALL5['dot'], '', 'record Aluno(string Nome, string? Apelido);')),
     T('Rode dotnet run. Depois troque a linha 3 por ' + CALL5['coalesce'] + ' e rode de novo.', 'Run dotnet run. Then replace line 3 with ' + CALL5['coalesce'] + ' and run again.')],
   'ok': T('na primeira vez aparecem o aviso CS8602, "Oi, Bia!" e uma NullReferenceException (o texto pode vir traduzido, conforme o idioma do seu SDK); na segunda, "Oi, Bia!" e "(sem apelido)", sem aviso.', 'the first time you see warning CS8602, "Oi, Bia!" and a NullReferenceException; the second time, "Oi, Bia!" and "(sem apelido)", with no warning.')}}

t5 = {'pt': {'objectives': ['Explicar o que é null e por que NullReferenceException acontece.', 'Usar string?, ?. e ?? com segurança.', 'Entender que ! cala o aviso mas não resolve.'], 'minutes': 20,
  'activity': 'Distribua envelopes, alguns vazios. Cada aluno precisa ler em voz alta o papel do envelope. Primeiro, sem olhar dentro (ponto); depois, olhando antes e dizendo "sem apelido" quando estiver vazio (?. e ??).',
  'discussion': ['Que dados da escola podem faltar (apelido, telefone do responsável)?', 'Por que calar um aviso com ! é diferente de resolver o problema?'],
  'misconceptions': ['"Com Nullable ligado, o C# nunca mais tem null." É só análise do compilador: dados de fora ainda podem chegar como null.']},
 'en': {'objectives': ['Explain what null is and why NullReferenceException happens.', 'Use string?, ?. and ?? safely.', 'Understand that ! silences the warning but fixes nothing.'], 'minutes': 20,
  'activity': 'Hand out envelopes, some empty. Each student must read aloud the paper in the envelope. First without looking inside (dot); then looking first and saying "no nickname" when it’s empty (?. and ??).',
  'discussion': ['What school data may be missing (nickname, a guardian’s phone)?', 'Why is silencing a warning with ! different from fixing the problem?'],
  'misconceptions': ['"With Nullable on, C# never has null again." It’s only compiler analysis: data from outside can still arrive as null.']}}
write('05-nulabilidade', s5, loc5('pt'), loc5('en'), t5)

# ================================================================== 6 · exceções
STRAT6 = [opt('tryparse', 'tryparse', 'tryparse'), opt('filter', 'filtro', 'filter'), opt('swallow', 'engolir', 'swallow'), opt('none', 'sem-catch', 'no-catch')]
TOTAL6 = 'Console.WriteLine($"Total: R$ {qtd * preco:F2}");'
CODE6 = {
  'tryparse': ['if (!int.TryParse(texto, out int qtd))', '{', '    Console.WriteLine($"Quantidade inválida: \\"{texto}\\"");', '    return;', '}', TOTAL6],
  'filter': ['int qtd;', 'try', '{', '    qtd = int.Parse(texto);', '}', 'catch (Exception ex) when (ex is FormatException or OverflowException)', '{',
             '    Console.WriteLine($"Quantidade inválida: \\"{texto}\\" ({ex.GetType().Name})");', '    return;', '}', TOTAL6],
  'swallow': ['int qtd = 0;', 'try', '{', '    qtd = int.Parse(texto);', '}', 'catch (Exception)', '{', '}', TOTAL6],
  'none': ['int qtd = int.Parse(texto);', TOTAL6]}
s6 = step('cs-excecoes', 6, TRACK, 20, ['csharp', 'excecoes', 'try-catch', 'tryparse'], ['cs-nulabilidade'], SIM,
  loc('pedir', 'order'),
  {'name': 'text', 'required': False, 'default': loc('3', '3'), 'ui': 'examples',
   'examples': [loc('3', '3'), loc('abc', 'abc'), loc('99999999999', '99999999999'), loc('-2', '-2')]},
  [flag('strategy', 'estrategia', 'strategy', 'enum', options=STRAT6, default='tryparse', ui='select')],
  {'options': ['crash', 'message', 'zero'], 'answer': 'zero'}, 'swallowed',
  {'live': True,
   'consts': {'code': CODE6, 'notDigits': ['.', ',', 'e', 'x', 'b', 'o', 'i', 'n', '_'], 'maxInt': 2147483647, 'minInt': -2147483648},
   'compute': {
     'n': 'number(text)',
     'intLike': 'words(text) > 0 && !containsany(lower(text), notDigits) && n == floor(n)',
     'tooBig': 'intLike && (n > maxInt || n < minInt)',
     'valid': 'intLike && !tooBig',
     'bad': '!valid',
     'excName': "tooBig ? 'OverflowException' : 'FormatException'",
     'excMsg': "tooBig ? 'Value was either too large or too small for an Int32.' : 'The input string ' + \"'\" + text + \"'\" + ' was not in a correct format.'",
     'qtyN': 'valid ? n : 0',
     'centsN': 'qtyN * 450',
     'absC': 'abs(centsN)',
     'totalText': "(centsN < 0 ? '-' : '') + str(floor(absC / 100)) + (lang == 'pt' ? ',' : '.') + (absC % 100 < 10 ? '0' : '') + str(absC % 100)",
     'outLine': "valid ? '+Total: R$ ' + totalText : (strategy == 'swallow' ? '?Total: R$ ' + (lang == 'pt' ? '0,00' : '0.00') : (strategy == 'none' ? '!Unhandled exception. System.' + excName + ': ' + excMsg : '+Quantidade inválida: \"' + text + '\"' + (strategy == 'filter' ? ' (' + excName + ')' : '')))",
     'calmLead': "bad && strategy == 'none' ? calmCrash : calmHandled",
     'shownTotal': "valid ? totalText : (lang == 'pt' ? '0,00' : '0.00')"},
   'cases': [
     {'when': "bad && strategy == 'swallow'", 'flags': ['swallowed']},
     {'when': "bad && strategy == 'none'", 'flags': ['crashed']},
     {'when': "bad && (strategy == 'filter' || strategy == 'tryparse')", 'flags': ['handled']},
     {'when': 'valid && qtyN <= 0', 'flags': ['oddQty']},
     {'when': 'true', 'vars': {'total': 'shownTotal', 'exc': 'excName', 'input': 'text', 'calmLead': 'calmLead'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@inputM', 'value': "='\"' + text + '\"'", 'tone': "=valid ? 'ok' : 'warn'"},
       {'label': '@excM', 'value': "=bad && strategy != 'tryparse' ? excName : '@none'", 'tone': "=bad && strategy != 'tryparse' ? 'warn' : 'dim'"},
       {'label': '@cashierM', 'value': "=valid ? '@sawTotal' : (strategy == 'swallow' ? '@sawZero' : (strategy == 'none' ? '@sawCrash' : '@sawMsg'))", 'tone': "=valid ? 'ok' : (strategy == 'swallow' ? 'bad' : (strategy == 'none' ? 'bad' : 'ok'))"}]},
     {'type': 'terminal', 'label': 'Program.cs', 'lines': "=concat(['string texto = \"' + text + '\";', 'decimal preco = 4.50m;'], lookup(code, strategy, []))"},
     {'type': 'terminal', 'label': '@runLabel', 'lines': "=['$ dotnet run', outLine]"},
     {'type': 'flow', 'label': '@flowLabel', 'steps': [
       {'label': 'int.Parse', 'sub': "=strategy == 'tryparse' ? '@sTry' : (bad ? excName : '@sOk')", 'tone': "=strategy == 'tryparse' ? 'info' : (bad ? 'warn' : 'ok')"},
       {'label': 'catch', 'sub': "=strategy == 'swallow' ? '@sSwallow' : (strategy == 'filter' ? '@sFilter' : (strategy == 'none' ? '@sNone' : '@sNoNeed'))", 'tone': "=strategy == 'swallow' ? (bad ? 'bad' : 'warn') : (strategy == 'none' ? (bad ? 'bad' : 'dim') : 'ok')"},
       {'label': '@fCashier', 'sub': "=valid ? '@sawTotal' : (strategy == 'swallow' ? '@sawZero' : (strategy == 'none' ? '@sawCrash' : '@sawMsg'))", 'tone': "=valid || strategy == 'filter' || strategy == 'tryparse' ? 'ok' : 'bad'"}]},
     {'type': 'note', 'when': "=bad && strategy == 'swallow'", 'tone': 'bad', 'text': '@swallowNote'},
     {'type': 'note', 'when': "=bad && strategy == 'none'", 'tone': 'bad', 'text': '@crashNote'},
     {'type': 'note', 'when': "=bad && strategy == 'filter'", 'tone': 'ok', 'text': '@filterNote'},
     {'type': 'note', 'when': "=bad && strategy == 'tryparse'", 'tone': 'ok', 'text': '@tryNote'},
     {'type': 'note', 'when': '=valid && qtyN <= 0', 'tone': 'warn', 'text': '@oddNote'}]})

def loc6(L):
  pt, T = mk(L)
  return {
  'title': T('Exceções', 'Exceptions'),
  'subtitle': T('Quando o aluno digita "abc" na quantidade: explodir, engolir ou avisar direito?', 'When a student types "abc" as the quantity: blow up, swallow it or say so properly?'),
  'mission': T('No totem da cantina, o aluno digita quantos pastéis quer (R$ 4,50 cada). Tem gente que digita "abc", tem gente que digita um número gigante. Escolha a estratégia: TryParse, try/catch com filtro, catch que engole tudo, ou nenhum catch, e veja o que o caixa da Dona Cida enxerga.',
               'At the canteen kiosk, students type how many pastéis (fried pastries) they want (R$ 4.50 each). Some type "abc", some type a gigantic number. Pick the strategy: TryParse, try/catch with a filter, a catch that swallows everything, or no catch at all, and see what Dona Cida’s till sees. (Messages printed by the code are in Portuguese: Quantidade inválida = invalid quantity.)'),
  'predict': {'question': T('com catch (Exception) { } vazio e a entrada "abc", o que aparece para a Dona Cida?', 'with an empty catch (Exception) { } and the input "abc", what does Dona Cida see?'),
    'options': {'crash': T('O programa quebra com FormatException', 'The program crashes with a FormatException'),
                'message': T('Uma mensagem de quantidade inválida', 'An invalid-quantity message'),
                'zero': T('"Total: R$ 0,00", como se nada tivesse acontecido', '"Total: R$ 0.00", as if nothing happened')}},
  'feedback': {'right': T('isso: a exceção aconteceu, o catch vazio engoliu, qtd continuou 0 e o caixa mostrou R$ 0,00. Ninguém sabe que houve erro: nem a Dona Cida, nem o log, nem você.',
                          'right: the exception happened, the empty catch swallowed it, qtd stayed 0 and the till showed R$ 0.00. Nobody knows there was an error: not Dona Cida, not the log, not you.'),
               'wrong': T('aparece "Total: R$ 0,00". O int.Parse lançou FormatException, o catch vazio pegou e jogou fora, e o programa seguiu com qtd = 0. É o pior dos mundos: errado e silencioso.',
                          'it shows "Total: R$ 0.00". int.Parse threw a FormatException, the empty catch took it and threw it away, and the program went on with qtd = 0. Worst of both worlds: wrong and silent.'),
               'skipped': T('sem palpite? Rode pedir "abc" --estrategia engolir e olhe a linha do terminal.', 'no guess? Run order "abc" --strategy swallow and look at the terminal line.')},
  'coach': {'ui': T('palpite anotado. Escolha a entrada "abc" e a estratégia "engolir". Depois compare com "tryparse".', 'guess noted. Pick the input "abc" and the "swallow" strategy. Then compare with "tryparse".'),
            'cmd': T('palpite anotado. Rode pedir "abc" --estrategia engolir e depois pedir "abc".', 'guess noted. Run order "abc" --strategy swallow and then order "abc".')},
  'tryNext': {'ui': T('Escolha 99999999999 sem catch: não é letra, é número demais para um int, e a exceção é outra (OverflowException).', 'Pick 99999999999 with no catch: it isn’t letters, it’s too much number for an int, and the exception is a different one (OverflowException).'),
              'cmd': T('Rode pedir "99999999999" --estrategia sem-catch e leia o nome da exceção.', 'Run order "99999999999" --strategy no-catch and read the exception’s name.')},
  'why': {'simples': T('Exceção é o jeito de o programa gritar "não dá para continuar assim!". Se ninguém escuta, o programa para. try/catch é colocar alguém para escutar: "tente isto; se der errado, faça aquilo".\nO erro clássico é colocar alguém que escuta e não faz nada (o catch vazio): o problema some da vista, mas continua lá, e a conta sai errada. Melhor ainda é nem precisar gritar: quando é normal o aluno digitar errado, pergunte com calma (TryParse devolve "deu ou não deu") e explique o que ele precisa digitar.',
                       'An exception is the program shouting "I can’t go on like this!". If nobody listens, the program stops. try/catch puts someone there to listen: "try this; if it goes wrong, do that".\nThe classic mistake is putting a listener who does nothing (the empty catch): the problem disappears from view, but it’s still there, and the bill comes out wrong. Even better is not needing to shout: when it’s normal for a student to type wrong, ask calmly (TryParse returns "it worked or it didn’t") and explain what they need to type.'),
          'dev': T('Para quem vem do JS: no C# você captura por tipo (catch (FormatException ex)), do mais específico para o mais geral, e pode filtrar com when sem precisar relançar. int.Parse lança FormatException para texto que não é número e OverflowException para número fora do int; int.TryParse não lança: devolve false e deixa o valor em 0.\nRegra prática: exceção é para o que é excepcional (banco fora do ar, arquivo sumiu, bug); entrada de usuário errada é esperada, então use TryParse ou validação. Nunca escreva catch vazio; se capturar, registre (log), traduza para uma mensagem útil ou relance com throw; (sem o ex, para não perder o stack trace). E repare: "-2" passa no TryParse, mas -2 pastéis não fazem sentido; validar regra de negócio é outro passo, assunto da missão.',
                   'For JS folks: in C# you catch by type (catch (FormatException ex)), from most specific to most general, and you can filter with when without rethrowing. int.Parse throws FormatException for text that isn’t a number and OverflowException for a number outside int range; int.TryParse doesn’t throw: it returns false and leaves the value at 0.\nRule of thumb: exceptions are for the exceptional (database down, file gone, a bug); bad user input is expected, so use TryParse or validation. Never write an empty catch; if you catch, log it, turn it into a useful message, or rethrow with throw; (without the ex, so you don’t lose the stack trace). And notice: "-2" passes TryParse, but -2 pastries make no sense; validating business rules is a separate step, covered in the mission.'),
          'especialista': T('Filtros de exceção (catch … when) rodam antes de a pilha ser desenrolada: se o filtro dá false, a exceção segue como se o catch nem existisse, e o stack trace original fica intacto para o depurador e para o crash dump. Use para separar casos ("when (ex is HttpRequestException { StatusCode: HttpStatusCode.NotFound })") e até para logar sem capturar (when (Log(ex) && false)). Relançar com throw ex; reinicia o stack trace (o analisador CA2200 avisa); throw; preserva.\nLançar exceção custa caro comparado a um if (captura de stack trace, desenrolar da pilha), então não use para controle de fluxo em caminho quente; padrões Try* e tipos de resultado são a alternativa. Libere recursos com using ou finally, que rodam com ou sem exceção. Em APIs ASP.NET Core, um middleware de tratamento de exceções transforma o que escapou em ProblemDetails, em vez de cada endpoint ter seu catch genérico.',
                            'Exception filters (catch … when) run before the stack is unwound: if the filter returns false, the exception continues as if the catch weren’t there, and the original stack trace stays intact for the debugger and the crash dump. Use them to separate cases ("when (ex is HttpRequestException { StatusCode: HttpStatusCode.NotFound })") and even to log without catching (when (Log(ex) && false)). Rethrowing with throw ex; resets the stack trace (analyzer CA2200 warns); throw; preserves it.\nThrowing is expensive compared to an if (capturing the stack trace, unwinding the stack), so don’t use it for control flow on a hot path; Try* patterns and result types are the alternative. Release resources with using or finally, which run with or without an exception. In ASP.NET Core APIs, an exception-handling middleware turns whatever escaped into ProblemDetails, instead of every endpoint having its own generic catch.')},
  'break': {'mission': {'ui': T('hora de quebrar: entrada "abc" com a estratégia "engolir".', 'time to break it: input "abc" with the "swallow" strategy.'),
                        'cmd': T('hora de quebrar: rode pedir "abc" --estrategia engolir', 'time to break it: run order "abc" --strategy swallow')},
            'success': T('Quebrou: a entrada "{input}" gerou uma {exc}, o catch vazio jogou fora e o caixa mostrou Total: R$ {total}. O aluno sai sem pastel, a Dona Cida acha que foi engano dele e ninguém descobre que o totem está com defeito.',
                         'Broken: the input "{input}" raised a {exc}, the empty catch threw it away and the till showed Total: R$ {total}. The student leaves with no pastry, Dona Cida thinks it was their mistake and nobody finds out the kiosk is broken.'),
            'calm': T('A entrada "{input}" {calmLead} Para quebrar, digite "abc" e use a estratégia que engole a exceção.', 'The input "{input}" {calmLead} To break it, type "abc" and use the strategy that swallows the exception.')},
  'hints': {'ui': T(['Escolha o que o aluno digitou e a estratégia.', 'Um dos catch não faz nada com a exceção.', 'Escolha "abc" e a estratégia "engolir".'],
                    ['Pick what the student typed and the strategy.', 'One of the catches does nothing with the exception.', 'Pick "abc" and the "swallow" strategy.']),
            'cmd': T(['O que o aluno digitou vai entre aspas; --estrategia é opcional.', '--estrategia aceita tryparse, filtro, engolir ou sem-catch.', 'pedir "abc" --estrategia engolir'],
                     ['What the student typed goes in quotes; --strategy is optional.', '--strategy takes tryparse, filter, swallow or no-catch.', 'order "abc" --strategy swallow'])},
  'errors': {'notInEnum.strategy': T('Use tryparse, filtro, engolir ou sem-catch.', 'Use tryparse, filter, swallow or no-catch.')},
  'controls': {'arg': T('O que o aluno digitou', 'What the student typed'), 'strategy': T('Estratégia de erro', 'Error strategy')},
  'scene': {'label': T('Totem da cantina', 'Canteen kiosk'), 'empty': T('Rode para fazer o pedido.', 'Run to place the order.'),
    'inputM': T('entrada', 'input'), 'excM': T('exceção lançada', 'exception thrown'), 'cashierM': T('o caixa vê', 'the till sees'), 'none': T('nenhuma', 'none'),
    'sawTotal': T('o total certo', 'the right total'), 'sawZero': T('R$ 0,00 sem explicação', 'R$ 0.00 with no explanation'), 'sawCrash': T('o programa caiu', 'the program died'), 'sawMsg': T('quantidade inválida', 'invalid quantity'),
    'runLabel': T('Terminal', 'Terminal'), 'flowLabel': T('Caminho do erro', 'The error’s path'), 'fCashier': T('caixa', 'till'),
    'sTry': T('TryParse: sem exceção', 'TryParse: no exception'), 'sOk': T('número lido', 'number read'),
    'sSwallow': T('engole tudo', 'swallows everything'), 'sFilter': T('só Format e Overflow', 'only Format and Overflow'), 'sNone': T('ninguém', 'nobody'), 'sNoNeed': T('não precisa', 'not needed'),
    'swallowNote': T('A {exc} aconteceu e foi apagada. O total de R$ {total} parece um pedido válido de zero pastéis.', 'The {exc} happened and was erased. The R$ {total} total looks like a valid order for zero pastries.'),
    'crashNote': T('Ninguém capturou a {exc}: o programa inteiro caiu por causa de um campo digitado errado.', 'Nobody caught the {exc}: the whole program died because of one mistyped field.'),
    'filterNote': T('O filtro when pegou só as exceções esperadas e explicou qual foi ({exc}). Qualquer outra seguiria adiante, sem ser escondida.', 'The when filter caught only the expected exceptions and said which one it was ({exc}). Anything else would keep going, not hidden.'),
    'tryNote': T('TryParse nem lançou exceção: devolveu false e o código explicou o problema. Entrada errada é esperada, não excepcional.', 'TryParse didn’t even throw: it returned false and the code explained the problem. Bad input is expected, not exceptional.'),
    'oddNote': T('O número foi lido sem erro, mas {input} pastéis não fazem sentido. Conversão certa não é regra de negócio certa (isso fica para a missão).', 'The number was read with no error, but {input} pastries make no sense. A correct conversion isn’t a correct business rule (that’s for the mission).')},
  'data': {'calmHandled': T('foi tratada sem esconder nada.', 'was handled without hiding anything.'),
           'calmCrash': T('derrubou o programa: nada foi escondido, mas o programa caiu.', 'took the program down: nothing was hidden, but the program crashed.')},
  'recipe': {'steps': [
     T(f'Crie o projeto (se ainda não criou): {NEW} e entre em Cantina.', f'Create the project (if you haven’t yet): {NEW} and go into Cantina.'),
     T('Troque Program.cs por (args[0] é o que você passar depois de dotnet run --):\n' + sh('string texto = args.Length > 0 ? args[0] : "3";', 'decimal preco = 4.50m;', *CODE6['swallow']),
       'Replace Program.cs with (args[0] is whatever you pass after dotnet run --):\n' + sh('string texto = args.Length > 0 ? args[0] : "3";', 'decimal preco = 4.50m;', *CODE6['swallow'])),
     T('Rode dotnet run -- abc. Depois troque o bloco try/catch inteiro (de int qtd = 0; até a chave do catch) pelo bloco do TryParse:\n' + sh(*CODE6['tryparse'][:-1]) + '\ne rode dotnet run -- abc de novo.',
       'Run dotnet run -- abc. Then replace the whole try/catch block (from int qtd = 0; to the catch’s closing brace) with the TryParse block:\n' + sh(*CODE6['tryparse'][:-1]) + '\nand run dotnet run -- abc again.')],
   'ok': T('na primeira vez aparece Total: R$ 0,00 (ou 0.00, conforme o idioma do sistema) sem nenhum erro; na segunda, Quantidade inválida: "abc".', 'the first time you see Total: R$ 0.00 (or 0,00, depending on your system language) with no error at all; the second time, Quantidade inválida: "abc".')}}

t6 = {'pt': {'objectives': ['Usar try/catch capturando por tipo.', 'Preferir TryParse quando o erro é esperado.', 'Reconhecer o perigo do catch vazio.'], 'minutes': 20,
  'activity': 'Telefone sem fio do erro: um aluno "lança" um bilhete de erro; o próximo pode resolver, passar adiante ou amassar e jogar fora (catch vazio). No fim, perguntem à turma o que a Dona Cida ficou sabendo em cada caso.',
  'discussion': ['Que erros da cantina são esperados (digitação) e quais são excepcionais (impressora sem papel)?', 'Por que um erro escondido pode ser pior que um programa que para?'],
  'misconceptions': ['"Colocar try/catch em tudo deixa o programa mais seguro." Capturar sem tratar só esconde o problema e deixa os dados errados.']},
 'en': {'objectives': ['Use try/catch catching by type.', 'Prefer TryParse when the error is expected.', 'Recognize the danger of an empty catch.'], 'minutes': 20,
  'activity': 'Error telephone game: one student "throws" an error note; the next can handle it, pass it on, or crumple it and throw it away (empty catch). At the end, ask the class what Dona Cida found out in each case.',
  'discussion': ['Which canteen errors are expected (typos) and which are exceptional (printer out of paper)?', 'Why can a hidden error be worse than a program that stops?'],
  'misconceptions': ['"Wrapping everything in try/catch makes the program safer." Catching without handling only hides the problem and leaves the data wrong.']}}
write('06-excecoes', s6, loc6('pt'), loc6('en'), t6)

# ================================================================== 7 · async/await
ITEMS7 = [('misto quente', 3), ('suco', 2), ('troco', 1)]
def async_run(method, mode, fail):
  ev = []  # (tempo, ordem, linha)
  if method == 'task' and mode == 'together':
    for k, (it, d) in enumerate(ITEMS7): ev.append((0, k, f'[0 s] começou {it}'))
    for k, (it, d) in enumerate(ITEMS7):
      if not (fail and it == 'suco'): ev.append((d, 10 + k, f'[{d} s] terminou {it}'))
    end = max(d for _, d in ITEMS7); ev.sort()
    lines = [l for _, _, l in ev]
    lines += [f'[{end} s] pedido com problema: a máquina de suco quebrou'] if fail else ['Prontos: misto quente, suco, troco']
    done = sum(1 for l in lines if 'terminou' in l)
    return {'lines': lines, 'total': end, 'done': done, 'knew': True}
  if method == 'task':
    t = 0; lines = []
    for it, d in ITEMS7:
      lines.append(f'[{t} s] começou {it}'); t += d
      if fail and it == 'suco':
        lines.append(f'[{t} s] pedido com problema: a máquina de suco quebrou'); break
      lines.append(f'[{t} s] terminou {it}')
    else: lines.append('Prontos: misto quente, suco, troco')
    return {'lines': lines, 'total': t, 'done': sum(1 for l in lines if 'terminou' in l), 'knew': True}
  lines = [f'[0 s] começou {it}' for it, _ in ITEMS7] + ['[0 s] atendimento encerrado']
  for it, d in sorted(ITEMS7, key=lambda x: x[1]):
    if fail and it == 'suco':
      lines.append('!Unhandled exception. System.InvalidOperationException: a máquina de suco quebrou'); break
    lines.append(f'[{d} s] terminou {it}')
  return {'lines': lines, 'total': -1, 'done': sum(1 for l in lines if 'terminou' in l), 'knew': False}
ASYNC = {f'{m}|{md}|{int(f)}': async_run(m, md, f) for m in ('task', 'void') for md in ('together', 'sequential') for f in (0, 1)}
# Conferido com dotnet run (.NET 10), as seis combinações distintas.
assert ASYNC['task|together|0']['lines'][3:] == ['[1 s] terminou troco', '[2 s] terminou suco', '[3 s] terminou misto quente', 'Prontos: misto quente, suco, troco']
assert ASYNC['task|sequential|1']['lines'][-1] == '[5 s] pedido com problema: a máquina de suco quebrou' and ASYNC['task|sequential|1']['total'] == 5
assert ASYNC['task|together|1']['lines'][-2:] == ['[3 s] terminou misto quente', '[3 s] pedido com problema: a máquina de suco quebrou']
assert ASYNC['void|together|1']['lines'][-2:] == ['[1 s] terminou troco', '!Unhandled exception. System.InvalidOperationException: a máquina de suco quebrou']
STAMP = '{relogio.Elapsed.TotalSeconds:F0}'
PREP_TOP = ['    Console.WriteLine($"[' + STAMP + ' s] começou {item}");', '    await Task.Delay(TimeSpan.FromSeconds(segundos));']
PREP_FAIL = ['    if (item == "suco")', '    {', '        throw new InvalidOperationException("a máquina de suco quebrou");', '    }']
PREP_END = ['    Console.WriteLine($"[' + STAMP + ' s] terminou {item}");']
TOGETHER7 = ['    Task<string> chapa = Preparar("misto quente", 3);', '    Task<string> suco = Preparar("suco", 2);', '    Task<string> troco = Preparar("troco", 1);', '    string[] prontos = await Task.WhenAll(chapa, suco, troco);']
SEQ7 = ['    string chapa = await Preparar("misto quente", 3);', '    string suco = await Preparar("suco", 2);', '    string troco = await Preparar("troco", 1);', '    string[] prontos = [chapa, suco, troco];']
TASK_HEAD = ['using System.Diagnostics;', '', 'var relogio = Stopwatch.StartNew();', 'try', '{']
TASK_MID = ['    Console.WriteLine($"Prontos: {string.Join(", ", prontos)}");', '}', 'catch (Exception ex)', '{', '    Console.WriteLine($"[' + STAMP + ' s] pedido com problema: {ex.Message}");', '}',
            'Console.WriteLine($"Tempo total: {relogio.Elapsed.TotalSeconds:F1} s");', '', 'async Task<string> Preparar(string item, int segundos)', '{']
VOID_MAIN = ['using System.Diagnostics;', '', 'var relogio = Stopwatch.StartNew();', 'try', '{', '    Preparar("misto quente", 3);', '    Preparar("suco", 2);', '    Preparar("troco", 1);', '}', 'catch (Exception ex)', '{',
             '    Console.WriteLine($"Pedido com problema: {ex.Message}");', '}', 'Console.WriteLine($"[' + STAMP + ' s] atendimento encerrado");', 'await Task.Delay(TimeSpan.FromSeconds(5)); // a cantina continua aberta', '', 'async void Preparar(string item, int segundos)', '{']
def task_program(together, fail): return TASK_HEAD + (TOGETHER7 if together else SEQ7) + TASK_MID + PREP_TOP + (PREP_FAIL if fail else []) + PREP_END + ['    return item;', '}']
MODES7 = [opt('together', 'juntos', 'together'), opt('sequential', 'um-por-vez', 'one-by-one')]
METH7 = [opt('task', 'task', 'task'), opt('void', 'void', 'void')]
s7 = step('cs-async-await', 7, TRACK, 20, ['csharp', 'async', 'await', 'task'], ['cs-excecoes'], SIM,
  loc('preparar', 'prepare'),
  {'name': 'text', 'required': False, 'default': loc('pedido 42', 'order 42'), 'ui': 'text'},
  [flag('mode', 'modo', 'mode', 'enum', options=MODES7, default='together', ui='select'),
   flag('method', 'metodo', 'method', 'enum', options=METH7, default='task', ui='select'),
   flag('fail', 'falha', 'fail', 'bool', default=False, ui='switch')],
  {'options': ['six', 'three', 'one'], 'answer': 'three'}, 'asyncVoid',
  {'live': True,
   'consts': {'runs': ASYNC, 'head': TASK_HEAD, 'together': TOGETHER7, 'seq': SEQ7, 'mid': TASK_MID, 'top': PREP_TOP, 'failL': PREP_FAIL, 'endL': PREP_END, 'voidMain': VOID_MAIN},
   'compute': {
     'isVoid': "method == 'void'",
     'row': "lookup(runs, method + '|' + mode + '|' + (fail ? '1' : '0'), runs['task|together|0'])",
     'totalS': 'row.total',
     'doneN': 'row.done',
     'totalText': "totalS < 0 ? '—' : str(totalS) + (lang == 'pt' ? ',0 s' : '.0 s')",
     'outLines': "isVoid ? row.lines : concat(row.lines, ['Tempo total: ' + str(totalS) + (lang == 'pt' ? ',0 s' : '.0 s')])",
     'voidWhat': 'fail ? voidCrash : voidEarly'},
   'cases': [
     {'when': 'isVoid', 'flags': ['asyncVoid']},
     {'when': '!isVoid && fail', 'flags': ['caught']},
     {'when': '!isVoid', 'vars': {'total': 'totalText'}},
     {'when': 'true', 'vars': {'done': 'doneN', 'voidWhat': 'voidWhat'}}],
   'widgets': [
     {'type': 'metrics', 'items': [
       {'label': '@totalM', 'value': '=totalText', 'tone': "=isVoid ? 'bad' : (totalS > 3 ? 'warn' : 'ok')"},
       {'label': '@doneM', 'value': "=str(doneN) + ' / 3'", 'tone': "=doneN == 3 ? 'ok' : 'warn'"},
       {'label': '@knewM', 'value': "=isVoid ? '@no' : '@yes'", 'tone': "=isVoid ? 'bad' : 'ok'"}]},
     {'type': 'table', 'label': '@tableLabel', 'columns': ['@cItem', '@cStart', '@cEnd'],
      'rows': "=isVoid ? [['misto quente', '0 s', fail ? '@never' : '3 s'], ['suco', '0 s', fail ? '@boom' : '2 s'], ['troco', '0 s', '1 s']] : (mode == 'together' ? [['misto quente', '0 s', '3 s'], ['suco', '0 s', fail ? '@failed' : '2 s'], ['troco', '0 s', '1 s']] : [['misto quente', '0 s', '3 s'], ['suco', '3 s', fail ? '@failed' : '5 s'], ['troco', fail ? '@never' : '5 s', fail ? '@never' : '6 s']])",
      'tones': "=fail ? ['neutral', 'bad', 'neutral'] : ['neutral', 'neutral', 'neutral']"},
     {'type': 'terminal', 'label': 'Program.cs', 'lines': "=isVoid ? concat(voidMain, top, fail ? failL : [], endL, ['}']) : concat(head, mode == 'together' ? together : seq, mid, top, fail ? failL : [], endL, ['    return item;', '}'])"},
     {'type': 'terminal', 'label': '@runLabel', 'lines': "=concat(['$ dotnet run'], outLines)"},
     {'type': 'note', 'when': "=!isVoid && mode == 'together'", 'tone': 'ok', 'text': '@togetherNote'},
     {'type': 'note', 'when': "=!isVoid && mode == 'sequential'", 'tone': 'warn', 'text': '@seqNote'},
     {'type': 'note', 'when': '=!isVoid && fail', 'tone': 'info', 'text': '@caughtNote'},
     {'type': 'note', 'when': '=isVoid', 'tone': 'info', 'text': '@voidModeNote'},
     {'type': 'note', 'when': '=isVoid && !fail', 'tone': 'bad', 'text': '@voidEarlyNote'},
     {'type': 'note', 'when': '=isVoid && fail', 'tone': 'bad', 'text': '@voidCrashNote'}]})

def loc7(L):
  pt, T = mk(L)
  return {
  'title': T('async/await', 'async/await'),
  'subtitle': T('A chapa, o suco e o troco: esperar sem ficar parado olhando', 'The grill, the juice and the change: waiting without standing there staring'),
  'mission': T('Um pedido na cantina tem três partes: o misto quente na chapa (3 s), o suco (2 s) e o troco (1 s). Com async/await, o caixa pode começar tudo e esperar as três juntas, ou fazer uma de cada vez. Escolha o modo, o tipo de método (async Task ou async void) e se a máquina de suco vai quebrar.',
               'A canteen order has three parts: the toastie on the grill (misto quente, 3 s), the juice (suco, 2 s) and the change (troco, 1 s). With async/await, the till can start everything and wait for all three together, or do one at a time. Pick the mode, the method kind (async Task or async void) and whether the juice machine will break. (The program prints in Portuguese: começou = started, terminou = finished, prontos = ready.)'),
  'predict': {'question': T('começando as três tarefas e esperando com await Task.WhenAll, quanto tempo leva o pedido?', 'starting the three tasks and waiting with await Task.WhenAll, how long does the order take?'),
    'options': {'six': T('6 s: 3 + 2 + 1', '6 s: 3 + 2 + 1'), 'three': T('3 s: o tempo da mais demorada', '3 s: the slowest one’s time'), 'one': T('1 s: o tempo da mais rápida', '1 s: the fastest one’s time')}},
  'feedback': {'right': T('isso: as três começam no segundo 0 e ninguém fica parado olhando a chapa. O WhenAll termina quando a última termina, aos 3 s. Esperar uma de cada vez somaria 6 s.',
                          'right: all three start at second 0 and nobody stands there staring at the grill. WhenAll finishes when the last one does, at 3 s. Waiting one at a time would add up to 6 s.'),
               'wrong': T('são 3 s. As tarefas começam juntas (chamar Preparar já dispara o trabalho) e o await Task.WhenAll espera a mais demorada. 6 s seria fazendo um await de cada vez.',
                          'it’s 3 s. The tasks start together (calling Preparar already kicks off the work) and await Task.WhenAll waits for the slowest one. 6 s would be awaiting one at a time.'),
               'skipped': T('sem palpite? Rode preparar e depois preparar --modo um-por-vez, e compare o tempo total.', 'no guess? Run prepare and then prepare --mode one-by-one, and compare the total time.')},
  'coach': {'ui': T('palpite anotado. Olhe o tempo total e a tabela. Depois troque o modo para "um-por-vez".', 'guess noted. Look at the total time and the table. Then switch the mode to "one-by-one".'),
            'cmd': T('palpite anotado. Rode preparar e depois preparar --modo um-por-vez.', 'guess noted. Run prepare and then prepare --mode one-by-one.')},
  'tryNext': {'ui': T('Ligue a falha com async Task: o try/catch pega o erro da máquina de suco e o programa termina direitinho. Guarde isso para comparar com o async void.', 'Turn on the failure with async Task: the try/catch catches the juice machine error and the program ends properly. Keep that in mind to compare with async void.'),
              'cmd': T('Rode preparar --modo um-por-vez e veja o tempo virar 6 s.', 'Run prepare --mode one-by-one and watch the time become 6 s.')},
  'why': {'simples': T('Esperar a chapa esquentar não é trabalho: é espera. async/await é o jeito de dizer ao programa "enquanto isso esquenta, vai fazendo outra coisa". O await é o "me avisa quando terminar".\nSe você liga a chapa, espera ficar pronta, só então faz o suco e só então conta o troco, o cliente espera 6 segundos. Se você liga tudo e espera as três coisas juntas, espera só o tempo da mais demorada: 3 segundos.\nO async void é o funcionário que sai correndo para fazer o pedido e não deixa telefone: ninguém sabe quando terminou, e se der problema, ninguém fica sabendo até a cantina inteira parar.',
                       'Waiting for the grill to heat up isn’t work: it’s waiting. async/await is how you tell the program "while that heats up, go do something else". The await is the "let me know when it’s done".\nIf you turn on the grill, wait until it’s ready, only then make the juice and only then count the change, the customer waits 6 seconds. If you start everything and wait for all three together, you wait only as long as the slowest: 3 seconds.\nasync void is the worker who runs off to make the order and leaves no phone number: nobody knows when it finished, and if something goes wrong, nobody finds out until the whole canteen stops.'),
          'dev': T('É o mesmo modelo do JS: Task<T> é a Promise<T>, await funciona igual e Task.WhenAll é o Promise.all (quando aguardado, relança a primeira exceção). Atenção: ao contrário do Promise.all, que rejeita na primeira falha, o Task.WhenAll espera todas as tarefas terminarem antes de relançar. Chamar um método async já começa o trabalho; o await só decide onde você espera o resultado.\nDiferenças que pegam quem vem do Node: async void existe e é perigoso (não dá para aguardar, e exceção lá dentro não volta para quem chamou; num console ou servidor, derruba o processo), então use async Task sempre, exceto em handlers de evento de UI. Não bloqueie com .Result ou .Wait(): em apps com contexto de sincronização (WinForms, WPF, ASP.NET antigo) isso pode travar para sempre. E passe CancellationToken adiante para dar para cancelar.',
                   'It’s the same model as JS: Task<T> is Promise<T>, await works the same and Task.WhenAll is Promise.all (when awaited, it rethrows the first exception). Careful: unlike Promise.all, which rejects on the first failure, Task.WhenAll waits for all the tasks to finish before rethrowing. Calling an async method already starts the work; the await only decides where you wait for the result.\nDifferences that catch Node folks: async void exists and is dangerous (it can’t be awaited, and an exception inside doesn’t come back to the caller; in a console app or server it takes down the process), so always use async Task, except for UI event handlers. Don’t block with .Result or .Wait(): in apps with a synchronization context (WinForms, WPF, legacy ASP.NET) that can hang forever. And pass a CancellationToken along so work can be cancelled.'),
          'especialista': T('async não cria thread: o await de um Task.Delay ou de uma chamada de rede libera a thread enquanto espera, e a continuação roda depois (no pool de threads, num app console ou ASP.NET Core, que não têm SynchronizationContext). Para trabalho pesado de CPU, quem paraleliza é Task.Run ou Parallel, não o await.\nValueTask<T> evita alocar um Task quando o resultado costuma estar pronto na hora (um cache, por exemplo), mas tem regras: aguarde uma vez só, não aguarde em paralelo e não leia Result antes de completar; na dúvida, use Task. ConfigureAwait(false) diz "não preciso voltar ao contexto original": em bibliotecas, evita deadlocks e custo; no ASP.NET Core faz pouca diferença. Com WhenAll, o await relança só a primeira exceção; as outras ficam em task.Exception (AggregateException). Ferramentas: o compilador avisa quando uma Task não é aguardada (CS4014).',
                            'async doesn’t create a thread: awaiting a Task.Delay or a network call frees the thread while waiting, and the continuation runs later (on the thread pool, in a console or ASP.NET Core app, which have no SynchronizationContext). For heavy CPU work, Task.Run or Parallel do the parallelizing, not await.\nValueTask<T> avoids allocating a Task when the result is usually ready right away (a cache, for instance), but it has rules: await it only once, don’t await it concurrently and don’t read Result before it completes; when in doubt, use Task. ConfigureAwait(false) says "I don’t need to come back to the original context": in libraries it avoids deadlocks and overhead; in ASP.NET Core it makes little difference. With WhenAll, await rethrows only the first exception; the others stay in task.Exception (AggregateException). Tooling: the compiler warns when a Task is not awaited (CS4014).')},
  'break': {'mission': {'ui': T('hora de quebrar: troque o método para async void.', 'time to break it: switch the method to async void.'),
                        'cmd': T('hora de quebrar: rode preparar --metodo void', 'time to break it: run prepare --method void')},
            'success': T('Quebrou: com async void, ninguém consegue esperar o preparo. {voidWhat}',
                         'Broken: with async void, nobody can wait for the cooking. {voidWhat}'),
            'calm': T('O pedido terminou em {total} ({done} de 3 itens prontos) e quem chamou ficou sabendo de tudo, inclusive dos erros. Para quebrar, troque para async void.', 'The order finished in {total} ({done} of 3 items ready) and the caller found out about everything, errors included. To break it, switch to async void.')},
  'hints': {'ui': T(['Escolha o modo, o tipo de método e a falha.', 'Um dos tipos de método não devolve nada que dê para esperar.', 'Escolha o método void.'],
                    ['Pick the mode, the method kind and the failure.', 'One of the method kinds returns nothing you can wait for.', 'Pick the void method.']),
            'cmd': T(['--modo, --metodo e --falha são opcionais.', '--modo aceita juntos ou um-por-vez; --metodo aceita task ou void.', 'preparar --metodo void'],
                     ['--mode, --method and --fail are optional.', '--mode takes together or one-by-one; --method takes task or void.', 'prepare --method void'])},
  'errors': {'notInEnum.mode': T('Use juntos ou um-por-vez.', 'Use together or one-by-one.'), 'notInEnum.method': T('Use task ou void.', 'Use task or void.'), 'notBool.fail': T('Use sim ou nao.', 'Use yes or no.')},
  'controls': {'arg': T('Pedido', 'Order'), 'mode': T('Como esperar', 'How to wait'), 'method': T('Preparar devolve', 'Preparar returns'), 'fail': T('A máquina de suco quebra', 'The juice machine breaks')},
  'scene': {'label': T('Balcão da cantina', 'Canteen counter'), 'empty': T('Rode para preparar o pedido.', 'Run to prepare the order.'),
    'totalM': T('tempo total do pedido', 'total order time'), 'doneM': T('itens terminados', 'items finished'), 'knewM': T('quem chamou ficou sabendo?', 'did the caller find out?'), 'yes': T('sim', 'yes'), 'no': T('não', 'no'),
    'tableLabel': T('Linha do tempo', 'Timeline'), 'cItem': T('item', 'item'), 'cStart': T('começa', 'starts'), 'cEnd': T('termina', 'ends'),
    'never': T('nunca', 'never'), 'boom': T('derrubou o programa', 'took the program down'), 'failed': T('falhou', 'failed'),
    'runLabel': T('Terminal', 'Terminal'),
    'voidModeNote': T('Com async void, o controle "Como esperar" não muda nada: o código já não espera por nenhuma das três.', 'With async void the "How to wait" control changes nothing: the code doesn’t wait for any of the three anyway.'),
    'togetherNote': T('As três começaram no segundo 0; o WhenAll esperou a mais demorada.', 'All three started at second 0; WhenAll waited for the slowest one.'),
    'seqNote': T('Um await de cada vez: cada item só começa quando o anterior termina, e os tempos se somam.', 'One await at a time: each item only starts when the previous one finishes, and the times add up.'),
    'caughtNote': T('A exceção da máquina de suco voltou pelo await e caiu no catch: o programa explica o problema e termina normalmente.', 'The juice machine’s exception came back through the await and landed in the catch: the program explains the problem and ends normally.'),
    'voidEarlyNote': T('"Atendimento encerrado" saiu no segundo 0, antes de qualquer item ficar pronto, e a linha "Prontos" nunca aparece: não há Task para esperar.', '"Atendimento encerrado" (service closed) came out at second 0, before any item was ready, and the "Prontos" line never appears: there’s no Task to wait for.'),
    'voidCrashNote': T('O try/catch em volta das chamadas já tinha passado quando a máquina quebrou. A exceção do async void subiu direto e derrubou o processo inteiro.', 'The try/catch around the calls was long gone when the machine broke. The async void exception went straight up and took down the whole process.')},
  'data': {'voidCrash': T('Quando a máquina de suco quebrou, o try/catch já tinha passado: a exceção derrubou o programa inteiro e o misto quente nunca saiu.', 'When the juice machine broke, the try/catch was already behind us: the exception took down the whole program and the toastie never came out.'),
           'voidEarly': T('O atendimento foi "encerrado" no segundo 0, antes de qualquer item ficar pronto, e a lista de prontos nunca foi entregue.', 'Service was "closed" at second 0, before any item was ready, and the list of ready items was never delivered.')},
  'recipe': {'steps': [
     T(f'Crie o projeto (se ainda não criou): {NEW} e entre em Cantina.', f'Create the project (if you haven’t yet): {NEW} and go into Cantina.'),
     T('Troque Program.cs por:\n' + sh(*task_program(True, False)), 'Replace Program.cs with:\n' + sh(*task_program(True, False))),
     T('Rode dotnet run. Depois troque as quatro linhas do Task<string> e do WhenAll pelas versões com await uma de cada vez:\n' + sh(*SEQ7) + '\ne rode de novo.',
       'Run dotnet run. Then replace the four Task<string> and WhenAll lines with the one-at-a-time await versions:\n' + sh(*SEQ7) + '\nand run again.')],
   'ok': T('na primeira vez as três tarefas começam em [0 s] e o tempo total fica perto de 3 s; na segunda, cada uma começa quando a anterior termina e o total fica perto de 6 s.', 'the first time all three tasks start at [0 s] and the total time is about 3 s; the second time each one starts when the previous one ends and the total is about 6 s.')}}

t7 = {'pt': {'objectives': ['Usar async Task e await.', 'Comparar esperar em sequência com Task.WhenAll.', 'Explicar por que evitar async void.'], 'minutes': 20,
  'activity': 'Três alunos com cronômetro: um "faz" o misto (conta até 3), outro o suco (até 2), outro o troco (até 1). Primeiro um de cada vez, depois todos ao mesmo tempo. Quanto tempo o cliente esperou em cada rodada?',
  'discussion': ['Que tarefas da escola são espera (fila da secretaria) e quais são trabalho de verdade?', 'Por que o async void é perigoso mesmo quando "funciona"?'],
  'misconceptions': ['"async faz o código rodar em outra thread." Ele libera a thread enquanto espera; trabalho pesado de CPU continua precisando de Task.Run ou paralelismo.']},
 'en': {'objectives': ['Use async Task and await.', 'Compare awaiting in sequence with Task.WhenAll.', 'Explain why to avoid async void.'], 'minutes': 20,
  'activity': 'Three students with stopwatches: one "makes" the toastie (counts to 3), another the juice (to 2), another the change (to 1). First one at a time, then all at once. How long did the customer wait each round?',
  'discussion': ['Which school tasks are waiting (the office queue) and which are real work?', 'Why is async void dangerous even when it "works"?'],
  'misconceptions': ['"async makes code run on another thread." It frees the thread while waiting; heavy CPU work still needs Task.Run or parallelism.']}}
write('07-async-await', s7, loc7('pt'), loc7('en'), t7)

# ================================================================== 8 · missão: calculadora de empréstimo com testes
CALC = ['namespace Emprestimo;', '', 'public static class Calculadora', '{', '    public static decimal[] Parcelas(decimal valor, decimal taxaMensalPct, int meses)', '    {',
        '        if (valor <= 0)', '            throw new ArgumentOutOfRangeException(', '                nameof(valor),', '                "O valor precisa ser maior que zero.");',
        '        if (meses < 1)', '            throw new ArgumentOutOfRangeException(', '                nameof(meses),', '                "Precisa de pelo menos 1 parcela.");',
        '        if (taxaMensalPct < 0)', '            throw new ArgumentOutOfRangeException(', '                nameof(taxaMensalPct),', '                "A taxa não pode ser negativa.");', '',
        '        decimal taxa = taxaMensalPct / 100m;', '        decimal parcela;', '        if (taxa == 0)', '        {', '            parcela = valor / meses;', '        }', '        else', '        {',
        '            decimal fator = 1m;', '            for (int i = 0; i < meses; i++)', '            {', '                fator *= 1 + taxa;', '            }',
        '            parcela = valor * taxa * fator / (fator - 1);', '        }', '',
        '        decimal redonda = Math.Round(parcela, 2, MidpointRounding.AwayFromZero);', '        decimal[] parcelas = Enumerable.Repeat(redonda, meses).ToArray();',
        '        if (taxa == 0)', '        {', '            parcelas[^1] = valor - redonda * (meses - 1);', '        }', '        return parcelas;', '    }', '}']
TESTS = ['using Emprestimo;', '', 'namespace Emprestimo.Tests;', '', 'public class CalculadoraTests', '{',
         '    [Fact]', '    public void Basico_1000_a_2_por_cento_em_12x()', '    {', '        decimal[] parcelas = Calculadora.Parcelas(1000m, 2m, 12);', '',
         '        Assert.Equal(12, parcelas.Length);', '        Assert.All(parcelas, p => Assert.Equal(94.56m, p));', '    }', '',
         '    [Fact]', '    public void Taxa_zero_divide_sem_juros()', '    {', '        decimal[] parcelas = Calculadora.Parcelas(1000m, 0m, 4);', '',
         '        Assert.All(parcelas, p => Assert.Equal(250m, p));', '    }', '',
         '    [Fact]', '    public void Centavos_fecham_a_conta()', '    {', '        decimal[] parcelas = Calculadora.Parcelas(1000m, 0m, 3);', '',
         '        Assert.Equal(new[] { 333.33m, 333.33m, 333.34m }, parcelas);', '        Assert.Equal(1000m, parcelas.Sum());', '    }', '',
         '    [Fact]', '    public void Entrada_invalida_lanca_excecao()', '    {',
         '        Assert.Throws<ArgumentOutOfRangeException>(() => Calculadora.Parcelas(0m, 2m, 12));',
         '        Assert.Throws<ArgumentOutOfRangeException>(() => Calculadora.Parcelas(1000m, 2m, 0));',
         '        Assert.Throws<ArgumentOutOfRangeException>(() => Calculadora.Parcelas(1000m, -1m, 12));', '    }', '}']
# Valores conferidos com dotnet run (.NET 10) chamando a Calculadora acima e as variantes com defeito.
assert dotnet_double(1000.0 - round(1000.0 / 3, 2) * 2) == '333.34000000000003'
assert dotnet_double(1000.0 / 3) == '333.3333333333333'
MONEY8 = [opt('double', 'double', 'double'), opt('decimal', 'decimal', 'decimal')]
RATE8 = [opt('int', 'inteira', 'int'), opt('decimal', 'decimal', 'decimal')]
ERR8 = [opt('swallow', 'engolir', 'swallow'), opt('throw', 'lancar', 'throw')]
TEST8 = [opt('basic', 'basico', 'basic'), opt('zero', 'taxa-zero', 'zero-rate'), opt('cents', 'centavos', 'cents'), opt('invalid', 'invalido', 'invalid')]
s8 = step('cs-missao-emprestimo', 8, TRACK, 30, ['missao', 'csharp', 'decimal', 'testes', 'xunit', 'validacao'],
  ['cs-tipos-e-variaveis', 'cs-excecoes', 'cs-nulabilidade'], SIM,
  loc('calcular', 'calculate'),
  {'name': 'text', 'required': False, 'default': loc('máquina de suco nova', 'new juice machine'), 'ui': 'text'},
  [flag('money', 'dinheiro', 'money', 'enum', options=MONEY8, default='double', ui='select'),
   flag('rate', 'taxa', 'rate', 'enum', options=RATE8, default='int', ui='select'),
   flag('zeroRate', 'taxa-zero', 'zero-rate', 'bool', default=False, ui='switch'),
   flag('cents', 'centavos', 'cents', 'bool', default=False, ui='switch'),
   flag('validate', 'validar', 'validate', 'bool', default=False, ui='switch'),
   flag('errors', 'erros', 'errors', 'enum', options=ERR8, default='swallow', ui='select'),
   flag('tests', 'testes', 'tests', 'list', options=TEST8, default=['basic'], ui='checkboxes')],
  None, 'passed',
  {'live': True,
   'compute': {
     'isDec': "money == 'decimal'",
     'rateOk': "rate == 'decimal'",
     'swallowing': "errors == 'swallow'",
     'tB': "includes(tests, 'basic')", 'tZ': "includes(tests, 'zero')", 'tC': "includes(tests, 'cents')", 'tI': "includes(tests, 'invalid')",
     'pB': 'rateOk && cents',
     'pZ': 'zeroRate',
     'pC': 'zeroRate && cents && isDec',
     'pI': 'validate && !swallowing',
     'allTests': 'tB && tZ && tC && tI',
     'selN': '(tB ? 1 : 0) + (tZ ? 1 : 0) + (tC ? 1 : 0) + (tI ? 1 : 0)',
     'passN': '(tB && pB ? 1 : 0) + (tZ && pZ ? 1 : 0) + (tC && pC ? 1 : 0) + (tI && pI ? 1 : 0)',
     'k1': 'isDec', 'k2': 'rateOk', 'k3': 'zeroRate', 'k4': 'cents', 'k5': 'validate && !swallowing',
     'k6': 'allTests && pB && pZ && pC && pI',
     'done': '(k1 ? 1 : 0) + (k2 ? 1 : 0) + (k3 ? 1 : 0) + (k4 ? 1 : 0) + (k5 ? 1 : 0) + (k6 ? 1 : 0)',
     'T': "isDec ? 'decimal' : 'double'",
     'ind': "swallowing ? '        ' : '    '",
     'divZero': "isDec ? (swallowing ? '@vEmpty' : '@vDiv0') : '@vNaN'",
     'basicKey': "!rateOk ? (zeroRate ? (cents ? '@v8333' : '@v8333raw') : divZero) : (cents ? '@v9456' : '@v9456raw')",
     'lastKey': "!zeroRate ? divZero : (!cents ? (isDec ? '@v333dec' : '@v333dbl') : (isDec ? '@v33334' : '@v33334dbl'))",
     'bLine': "pB ? '@okB' : (!rateOk ? (zeroRate ? '@failB8333' : (isDec ? (swallowing ? '@failBEmpty' : '@failBDiv0') : '@failBNaN')) : '@failBRound')",
     'zLine': "pZ ? '@okZ' : (isDec ? (swallowing ? '@failZEmpty' : '@failZDiv0') : '@failZNaN')",
     'cLine': "pC ? '@okC' : (!zeroRate ? (isDec ? (swallowing ? '@failCEmpty' : '@failCDiv0') : '@failCNaN') : (!cents ? '@failCRaw' : '@failCDbl'))",
     'iLine': "pI ? '@okI' : (validate ? '@failISwallow' : '@failINone')"},
   'cases': [
     {'when': 'done == 6', 'flags': ['passed']},
     {'when': 'true', 'vars': {'done': 'done', 'passN': 'passN', 'selN': 'selN'}}],
   'widgets': [
     {'type': 'checks', 'label': '@checksLabel', 'items': [
       {'label': '@k1', 'ok': '=k1', 'why': '@w1'}, {'label': '@k2', 'ok': '=k2', 'why': '@w2'}, {'label': '@k3', 'ok': '=k3', 'why': '@w3'},
       {'label': '@k4', 'ok': '=k4', 'why': '@w4'}, {'label': '@k5', 'ok': '=k5', 'why': "=validate ? '@w5swallow' : '@w5'"}, {'label': '@k6', 'ok': '=k6', 'why': '@w6'}]},
     {'type': 'metrics', 'items': [
       {'label': '@basicM', 'value': '=basicKey', 'tone': "=pB ? 'ok' : 'bad'"},
       {'label': '@lastM', 'value': '=lastKey', 'tone': "=pC ? 'ok' : 'bad'"},
       {'label': '@testsM', 'value': "=passN + ' / ' + selN", 'tone': "=selN > 0 && passN == selN ? (allTests ? 'ok' : 'warn') : 'bad'"}]},
     {'type': 'terminal', 'label': '@codeLabel', 'lines': "=concat(['public static ' + T + '[] Parcelas(' + T + ' valor, ' + (rateOk ? T : 'int') + ' taxaMensalPct, int meses)', '{'], swallowing ? ['    try', '    {'] : [], validate ? [ind + 'if (valor <= 0 || meses < 1 || taxaMensalPct < 0)', ind + '    throw new ArgumentOutOfRangeException(…);'] : [], [ind + T + ' taxa = taxaMensalPct / ' + (rateOk ? (isDec ? '100m;' : '100.0;') : '100;'), ind + '…'], zeroRate ? [ind + 'if (taxa == 0) parcela = valor / meses;', ind + 'else parcela = valor * taxa * fator / (fator - 1);'] : [ind + 'parcela = valor * taxa * fator / (fator - 1);'], cents ? [ind + 'redonda = Math.Round(parcela, 2, MidpointRounding.AwayFromZero);', ind + 'parcelas = Enumerable.Repeat(redonda, meses).ToArray();', ind + 'if (taxa == 0) parcelas[^1] = valor - redonda * (meses - 1);', ind + 'return parcelas;'] : [ind + 'return Enumerable.Repeat(parcela, meses).ToArray();'], swallowing ? ['    }', '    catch (Exception)', '    {', '        return [];', '    }'] : [], ['}'])"},
     {'type': 'terminal', 'label': '@testLabel', 'lines': "=concat(['$ dotnet test'], tB ? [bLine] : ['@noB'], tZ ? [zLine] : ['@noZ'], tC ? [cLine] : ['@noC'], tI ? [iLine] : ['@noI'], [selN > 0 && passN == selN ? '@sumOk' : '@sumBad'])"}]},
  kind='mission')

def loc8(L):
  pt, T = mk(L)
  n = (lambda s: s) if not pt else comma
  return {
  'title': T('Missão: calculadora de empréstimo com testes', 'Mission: loan calculator with tests'),
  'subtitle': T('A cantina vai financiar uma máquina de suco, e a primeira versão do código erra em quase tudo', 'The canteen is financing a juice machine, and the first version of the code gets almost everything wrong'),
  'mission': T('A Dona Cida vai comprar uma máquina de suco de R$ 1.000 e quer saber as parcelas: 12x a 2% ao mês, ou 3x e 4x sem juros. Um estagiário escreveu Calculadora.Parcelas(valor, taxaMensalPct, meses) com tudo o que esta trilha ensinou a evitar: dinheiro em double, a taxa dividida como inteiro, nada para taxa zero, centavos soltos, nenhuma validação, um catch que engole tudo e um teste só. Conserte até os seis critérios ficarem verdes.',
               'Dona Cida is buying a R$ 1,000 juice machine and wants to know the installments: 12x at 2% a month, or 3x and 4x interest-free. An intern wrote Calculadora.Parcelas(valor, taxaMensalPct, meses) (Calculator.Installments(amount, monthlyRatePct, months)) with everything this track taught you to avoid: money in double, the rate divided as an integer, nothing for a zero rate, loose cents, no validation, a catch that swallows everything and a single test. Fix it until all six criteria turn green.'),
  'coach': {'ui': T('Mexa nos controles; os critérios mudam enquanto você ajusta. Cada um que falhar diz o porquê.', 'Move the controls; the criteria change as you adjust. Each failing one says why.'),
            'cmd': T('Edite o comando e rode. Cada critério que falhar diz o porquê. Tudo apareceu nas lições 1, 5 e 6. Para escolher vários testes, separe por vírgula: --testes basico,taxa-zero,centavos,invalido', 'Edit the command and run it. Each failing criterion says why. Everything showed up in lessons 1, 5 and 6. To pick several tests, separate them with commas: --tests basic,zero-rate,cents,invalid')},
  'why': {'simples': T('Você fez o que um bom time faz com dinheiro: guardou os valores no tipo que conta em base 10 (decimal), fez a conta da taxa sem perder a vírgula, pensou no caso estranho (sem juros, a fórmula dividiria por zero), arredondou para centavos e fez a última parcela fechar a conta, recusou entradas sem sentido com uma exceção clara e escreveu um teste para cada um desses casos.\nOs testes são a parte que fica: daqui a um ano, quando alguém "melhorar" a calculadora, eles avisam na hora se a conta voltou a errar.',
                       'You did what a good team does with money: kept the values in the type that counts in base 10 (decimal), computed the rate without losing the fraction, thought about the odd case (with no interest, the formula would divide by zero), rounded to cents and made the last installment close the bill, refused nonsense input with a clear exception and wrote a test for each of those cases.\nThe tests are the part that stays: a year from now, when someone "improves" the calculator, they’ll tell you right away if the math went wrong again.'),
          'dev': T('A fórmula é a da tabela Price: parcela = valor × i × (1 + i)^n / ((1 + i)^n − 1). Como Math.Pow só aceita double, a potência em decimal é feita com um laço de multiplicações. Com i = 0 a fórmula vira 0 / 0: em double isso dá NaN em silêncio, em decimal lança DivideByZeroException; por isso o caso sem juros tem caminho próprio (valor / meses).\nArredonde só no fim, com MidpointRounding explícito (o padrão de Math.Round é o arredondamento bancário, ToEven), e deixe a diferença na última parcela: 1000 / 3 = 333,33 + 333,33 + 333,34. A validação lança ArgumentOutOfRangeException com nameof do parâmetro, e os testes de xUnit cobrem o caminho feliz, os dois casos de taxa zero e as entradas inválidas com Assert.Throws.',
                   'The formula is the standard amortized (Price) installment: payment = amount × i × (1 + i)^n / ((1 + i)^n − 1). Since Math.Pow only takes double, the decimal power is a loop of multiplications. With i = 0 the formula becomes 0 / 0: in double that silently gives NaN, in decimal it throws DivideByZeroException; that’s why the interest-free case has its own path (amount / months).\nRound only at the end, with an explicit MidpointRounding (Math.Round’s default is banker’s rounding, ToEven), and leave the difference on the last installment: 1000 / 3 = 333.33 + 333.33 + 333.34. Validation throws ArgumentOutOfRangeException with the parameter’s nameof, and the xUnit tests cover the happy path, both zero-rate cases and invalid input with Assert.Throws.'),
          'especialista': T('Num sistema financeiro de verdade ainda faltam: a regra de arredondamento definida pelo negócio (e às vezes pela regulação), o cronograma de amortização com a última parcela calculada pelo saldo devedor, datas e dias úteis, IOF e outros encargos, e o tipo dos valores na borda (JSON e banco: use numeric/decimal no banco e serialize como número exato ou texto, nunca como double).\nTestes: além dos exemplos, testes de propriedade ("a soma das parcelas nunca passa de valor × (1 + i)^n mais alguns centavos", "para i = 0 a soma é exatamente o valor") pegam casos que ninguém pensou; e um [Theory] com [InlineData] organiza a tabela de exemplos (atributos não aceitam literais decimal, então passe double ou string e converta, ou use [MemberData]). Valide entrada pública com as guardas do .NET, como ArgumentOutOfRangeException.ThrowIfNegativeOrZero (.NET 8 ou mais novo).',
                            'A real financial system still needs: the rounding rule defined by the business (and sometimes by regulation), the amortization schedule with the last installment computed from the outstanding balance, dates and business days, taxes and other charges, and the type of values at the edges (JSON and database: use numeric/decimal in the database and serialize as an exact number or a string, never as double).\nTests: beyond examples, property tests ("the installments never add up to more than amount × (1 + i)^n plus a few cents", "for i = 0 the sum is exactly the amount") catch cases nobody thought of; and a [Theory] with [InlineData] organizes the example table (attributes don’t accept decimal literals, so pass double or string and convert, or use [MemberData]). Validate public input with .NET’s guard helpers, like ArgumentOutOfRangeException.ThrowIfNegativeOrZero (.NET 8 or newer).')},
  'success': T('Missão cumprida! {done} de 6 critérios: 12 parcelas de R$ 94,56, R$ 1.000 em 3x sem juros fechando em 333,33 + 333,33 + 333,34, entradas absurdas recusadas com ArgumentOutOfRangeException e {passN} testes verdes para provar tudo isso. A máquina de suco já pode chegar.',
               'Mission accomplished! {done} of 6 criteria: 12 installments of R$ 94.56, R$ 1,000 in 3 interest-free payments closing at 333.33 + 333.33 + 333.34, absurd input refused with ArgumentOutOfRangeException and {passN} green tests to prove all of it. The juice machine can come in now.'),
  'errors': {'notInEnum.money': T('Use double ou decimal.', 'Use double or decimal.'), 'notInEnum.rate': T('Use inteira ou decimal.', 'Use int or decimal.'),
             'notBool.zeroRate': T('Use sim ou nao.', 'Use yes or no.'), 'notBool.cents': T('Use sim ou nao.', 'Use yes or no.'), 'notBool.validate': T('Use sim ou nao.', 'Use yes or no.'),
             'notInEnum.errors': T('Use engolir ou lancar.', 'Use swallow or throw.'),
             'notInEnum.tests': T('“{value}” não é um teste daqui. Opções: {options}.', '“{value}” isn’t a test here. Options: {options}.')},
  'controls': {'arg': T('O que está sendo financiado', 'What is being financed'), 'money': T('Tipo do dinheiro', 'Money type'), 'rate': T('Divisão da taxa (taxaMensalPct / 100)', 'Rate division (taxaMensalPct / 100)'),
               'zeroRate': T('Caminho próprio para taxa zero', 'Own path for a zero rate'), 'cents': T('Arredondar para centavos e fechar a conta', 'Round to cents and close the bill'),
               'validate': T('Validar valor, taxa e meses', 'Validate amount, rate and months'), 'errors': T('O que fazer com exceções', 'What to do with exceptions'), 'tests': T('Testes escritos', 'Tests written')},
  'scene': {'label': T('Calculadora de empréstimo', 'Loan calculator'), 'empty': T('Rode para calcular as parcelas.', 'Run to compute the installments.'),
    'trackDone': T('Você concluiu a trilha Fundamentos de C# e ASP.NET Core.', 'You completed the C# and ASP.NET Core Foundations track.'),
    'checksLabel': T('Critérios ({done} de 6)', 'Criteria ({done} of 6)'),
    'k1': T('Dinheiro em decimal', 'Money in decimal'), 'w1': T('double não guarda 0,01 exato (lição 1): 1000 − 333,33 − 333,33 dá 333,34000000000003.', 'double can’t hold 0.01 exactly (lesson 1): 1000 − 333.33 − 333.33 is 333.34000000000003.'),
    'k2': T('Taxa sem divisão inteira', 'Rate without integer division'), 'w2': T('Com int taxaMensalPct, 2 / 100 dá 0 (lição 1): todo empréstimo vira sem juros. Divida com decimal.', 'With int taxaMensalPct, 2 / 100 is 0 (lesson 1): every loan becomes interest-free. Divide with decimal.'),
    'k3': T('Taxa zero tem caminho próprio', 'Zero rate has its own path'), 'w3': T('Com taxa 0, a fórmula vira 0 / 0: NaN em double, DivideByZeroException em decimal.', 'With a 0 rate the formula becomes 0 / 0: NaN in double, DivideByZeroException in decimal.'),
    'k4': T('Parcelas em centavos que fecham a conta', 'Installments in cents that close the bill'), 'w4': T('Sem arredondar, a parcela sai 94,5595966…; arredonde e deixe a diferença na última parcela.', 'Without rounding the installment is 94.5595966…; round it and leave the difference on the last installment.'),
    'k5': T('Entrada inválida vira exceção clara', 'Invalid input becomes a clear exception'), 'w5': T('Parcelas(0, 2, 12) devolve parcelas de zero em vez de recusar. Valide e lance ArgumentOutOfRangeException.', 'Parcelas(0, 2, 12) returns zero installments instead of refusing. Validate and throw ArgumentOutOfRangeException.'),
    'w5swallow': T('A validação lança, mas o catch (Exception) engole e devolve um array vazio (lição 6). Deixe a exceção sair.', 'The validation throws, but the catch (Exception) swallows it and returns an empty array (lesson 6). Let the exception out.'),
    'k6': T('Os 4 casos testados, todos verdes', 'All 4 cases tested, all green'), 'w6': T('Marque os quatro testes (basico, taxa-zero, centavos, invalido) e deixe todos passando: um teste só, mesmo verde, não protege os casos de borda.', 'Tick the four tests (basic, zero-rate, cents, invalid) and get them all passing: a single test, even green, doesn’t protect the edge cases.'),
    'basicM': T('parcela de R$ 1.000 em 12x a 2%', 'installment of R$ 1,000 in 12x at 2%'), 'lastM': T('última de R$ 1.000 em 3x sem juros', 'last of R$ 1,000 in 3x interest-free'), 'testsM': T('testes passando', 'tests passing'),
    'v9456': n('94.56'), 'v9456raw': n('94.5595966…'), 'v8333': n('83.33'), 'v8333raw': n('83.3333333…'),
    'v333dec': n('333.33333333333333333333333333'), 'v333dbl': n('333.3333333333333'), 'v33334': n('333.34'), 'v33334dbl': n('333.34000000000003'),
    'vNaN': 'NaN', 'vDiv0': 'DivideByZeroException', 'vEmpty': T('[] (erro engolido)', '[] (error swallowed)'),
    'codeLabel': T('Calculadora.cs (o essencial — código completo na receita)', 'Calculadora.cs (the essentials — full code in the recipe)'), 'testLabel': T('Testes', 'Tests'),
    'okB': T('+✓ Basico_1000_a_2_por_cento_em_12x', '+✓ Basico_1000_a_2_por_cento_em_12x'),
    'failB8333': T('!✗ Basico_1000_a_2_por_cento_em_12x: esperava 94,56, veio 83,33… (a taxa virou 0)', '!✗ Basico_1000_a_2_por_cento_em_12x: expected 94.56, got 83.33… (the rate became 0)'),
    'failBDiv0': T('!✗ Basico_1000_a_2_por_cento_em_12x: DivideByZeroException (a taxa virou 0)', '!✗ Basico_1000_a_2_por_cento_em_12x: DivideByZeroException (the rate became 0)'),
    'failBEmpty': T('!✗ Basico_1000_a_2_por_cento_em_12x: esperava 12 parcelas, veio 0 (o erro foi engolido)', '!✗ Basico_1000_a_2_por_cento_em_12x: expected 12 installments, got 0 (the error was swallowed)'),
    'failBNaN': T('!✗ Basico_1000_a_2_por_cento_em_12x: esperava 94,56, veio NaN (0 / 0 em double)', '!✗ Basico_1000_a_2_por_cento_em_12x: expected 94.56, got NaN (0 / 0 in double)'),
    'failBRound': T('!✗ Basico_1000_a_2_por_cento_em_12x: esperava 94,56, veio 94,5595966… (faltou arredondar)', '!✗ Basico_1000_a_2_por_cento_em_12x: expected 94.56, got 94.5595966… (no rounding)'),
    'okZ': T('+✓ Taxa_zero_divide_sem_juros', '+✓ Taxa_zero_divide_sem_juros'),
    'failZDiv0': T('!✗ Taxa_zero_divide_sem_juros: DivideByZeroException', '!✗ Taxa_zero_divide_sem_juros: DivideByZeroException'),
    'failZEmpty': T('!✗ Taxa_zero_divide_sem_juros: veio um array vazio (o erro foi engolido)', '!✗ Taxa_zero_divide_sem_juros: got an empty array (the error was swallowed)'),
    'failZNaN': T('!✗ Taxa_zero_divide_sem_juros: esperava 250, veio NaN', '!✗ Taxa_zero_divide_sem_juros: expected 250, got NaN'),
    'okC': T('+✓ Centavos_fecham_a_conta', '+✓ Centavos_fecham_a_conta'),
    'failCDiv0': T('!✗ Centavos_fecham_a_conta: DivideByZeroException', '!✗ Centavos_fecham_a_conta: DivideByZeroException'),
    'failCEmpty': T('!✗ Centavos_fecham_a_conta: veio um array vazio (o erro foi engolido)', '!✗ Centavos_fecham_a_conta: got an empty array (the error was swallowed)'),
    'failCNaN': T('!✗ Centavos_fecham_a_conta: veio NaN', '!✗ Centavos_fecham_a_conta: got NaN'),
    'failCRaw': T('!✗ Centavos_fecham_a_conta: esperava 333,33, veio 333,3333…', '!✗ Centavos_fecham_a_conta: expected 333.33, got 333.3333…'),
    'failCDbl': T('!✗ Centavos_fecham_a_conta: esperava 333,34, veio 333,34000000000003', '!✗ Centavos_fecham_a_conta: expected 333.34, got 333.34000000000003'),
    'okI': T('+✓ Entrada_invalida_lanca_excecao', '+✓ Entrada_invalida_lanca_excecao'),
    'failINone': T('!✗ Entrada_invalida_lanca_excecao: nenhuma exceção foi lançada para Parcelas(0, 2, 12)', '!✗ Entrada_invalida_lanca_excecao: no exception was thrown for Parcelas(0, 2, 12)'),
    'failISwallow': T('!✗ Entrada_invalida_lanca_excecao: a validação lançou, mas o catch engoliu', '!✗ Entrada_invalida_lanca_excecao: the validation threw, but the catch swallowed it'),
    'noB': T('~(sem teste do caso básico)', '~(no test for the basic case)'), 'noZ': T('~(sem teste para taxa zero)', '~(no test for a zero rate)'),
    'noC': T('~(sem teste de centavos)', '~(no test for cents)'), 'noI': T('~(sem teste de entrada inválida)', '~(no test for invalid input)'),
    'sumOk': T('+{passN} de {selN} testes passaram', '+{passN} of {selN} tests passed'), 'sumBad': T('!{passN} de {selN} testes passaram', '!{passN} of {selN} tests passed')},
  'data': {},
  'recipe': {'steps': [
     T('Numa pasta vazia, crie a biblioteca e o projeto de testes e ligue um ao outro:\n' + sh('dotnet new classlib -o Emprestimo', 'dotnet new xunit -o Emprestimo.Tests', 'dotnet add Emprestimo.Tests reference Emprestimo') + '\nApague Emprestimo/Class1.cs e Emprestimo.Tests/UnitTest1.cs.',
       'In an empty folder, create the library and the test project and link them:\n' + sh('dotnet new classlib -o Emprestimo', 'dotnet new xunit -o Emprestimo.Tests', 'dotnet add Emprestimo.Tests reference Emprestimo') + '\nDelete Emprestimo/Class1.cs and Emprestimo.Tests/UnitTest1.cs.'),
     T('Crie Emprestimo/Calculadora.cs:\n' + sh(*CALC), 'Create Emprestimo/Calculadora.cs:\n' + sh(*CALC)),
     T('Crie Emprestimo.Tests/CalculadoraTests.cs (o template do xUnit já importa o namespace Xunit para o projeto inteiro):\n' + sh(*TESTS), 'Create Emprestimo.Tests/CalculadoraTests.cs (the xUnit template already imports the Xunit namespace for the whole project):\n' + sh(*TESTS)),
     T('Rode os testes: cd Emprestimo.Tests e depois dotnet test (a primeira vez baixa os pacotes do NuGet).', 'Run the tests: cd Emprestimo.Tests and then dotnet test (the first run downloads the NuGet packages).'),
     T('Quebre de propósito: em Calculadora.cs, troque o primeiro if (taxa == 0) por if (false) e rode dotnet test de novo (o compilador avisa que o código ficou inalcançável, e tudo bem).', 'Break it on purpose: in Calculadora.cs, change the first if (taxa == 0) to if (false) and run dotnet test again (the compiler warns about unreachable code, and that’s fine).')],
   'ok': T('o dotnet test termina com 4 testes aprovados e nenhuma falha; com o if (false), os testes de taxa zero e de centavos falham com DivideByZeroException e os outros dois continuam passando.', 'dotnet test ends with 4 tests passed and no failures; with the if (false), the zero-rate and cents tests fail with DivideByZeroException and the other two still pass.')}}

t8 = {'pt': {'objectives': ['Juntar tipos, validação, exceções e testes num problema real.', 'Escrever testes para casos de borda (taxa zero, centavos, entrada inválida).', 'Justificar decimal para dinheiro.'], 'minutes': 30,
  'activity': 'Em grupos, cada um fica com um critério e precisa explicar para a turma, com um exemplo numérico, o que dá errado sem ele. Depois, juntos, escrevam no quadro os quatro testes antes de olhar a receita.',
  'discussion': ['Qual dos erros seria o mais caro de descobrir só no mês 12 do empréstimo?', 'Por que um único teste verde pode dar uma falsa sensação de segurança?'],
  'misconceptions': ['"Se o teste passou, a calculadora está certa." O teste só prova os casos que ele cobre; taxa zero e centavos precisam dos seus próprios testes.']},
 'en': {'objectives': ['Combine types, validation, exceptions and tests in a real problem.', 'Write tests for edge cases (zero rate, cents, invalid input).', 'Justify decimal for money.'], 'minutes': 30,
  'activity': 'In groups, each takes one criterion and must explain to the class, with a numeric example, what goes wrong without it. Then, together, write the four tests on the board before looking at the recipe.',
  'discussion': ['Which mistake would be the most expensive to discover only in month 12 of the loan?', 'Why can a single green test give a false sense of safety?'],
  'misconceptions': ['"If the test passed, the calculator is right." A test only proves the cases it covers; zero rate and cents need their own tests.']}}
write('08-missao-emprestimo', s8, loc8('pt'), loc8('en'), t8)
print('ok: csharp-e-aspnet/fundamentos (8 passos)')
