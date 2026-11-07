import { describe, expect, it } from 'vitest';
import { defaultCommand, parseCommand } from '../src/engine/command';
import { LANGS } from '../src/engine/schema';
import { interpolate, makeRng } from '../src/engine/text';
import { ADAPTERS, type RealDeps } from '../src/runtime/adapters';
import { lesson, lessons, runCmd } from './helpers';

/**
 * Prática P3 (prompts e agentes): for pt and en the default command runs without error and never
 * raises the break flag, hint 3 raises it, and the guess marked right in "predict" is what the simulator shows.
 * Real ops are exercised with fake deps.
 */

const P3 = [
  'p-prompt-de-sistema-e-papeis',
  'p-exemplos-few-shot-e-formato',
  'p-extrair-emails-e-notas-fiscais',
  'p-triagem-de-tickets',
  'p-agente-com-ferramentas-e-limites',
  'p-memoria-de-conversa-e-resumo',
  'p-mcp-conectar-sistemas',
];

function runReal(id: string, input: string, deps: Partial<RealDeps>, lang: 'pt' | 'en' = 'pt', executor: 'no-navegador' | 'sua-chave' = 'no-navegador') {
  const l = lesson(id);
  const p = parseCommand(input, l.def.command, lang);
  if (!p.ok) throw new Error(JSON.stringify(p.error));
  const cfg = l.def.real![executor]!;
  const full: RealDeps = { tokenizer: async () => ({ encode: () => [], decode: () => '' }), chat: async () => '', ...deps };
  return ADAPTERS[cfg.adapter].run(p.values, { lang, layer: 'dev', data: l.def.data, text: l.locale[lang].data, rng: makeRng(1) }, full, { executor, model: 'm' }, cfg);
}


/** The command inside a tryNext.cmd sentence ("Rode conectar --x y e veja…"): the longest prefix from the verb that parses, minus trailing prose. */
function tryNextCommand(id: string, lang: 'pt' | 'en'): string {
  const l = lesson(id);
  const t = l.locale[lang].tryNext!.cmd;
  const rest = t.slice(t.indexOf(l.def.command.verb[lang]));
  const cuts = [...rest.matchAll(/ /g)].map((m) => m.index!).concat([rest.length]).reverse();
  for (const i of cuts) {
    let c = rest.slice(0, i).replace(/[.,]$/, '');
    if ((c.match(/"/g) ?? []).length % 2) continue;
    if (!parseCommand(c, l.def.command, lang).ok) continue;
    const q = c.lastIndexOf('"');
    if (q >= 0 && !c.slice(q).includes('--')) c = c.slice(0, q + 1);
    return c;
  }
  throw new Error(`no command in tryNext of ${id}`);
}

/** The break.success text for a run, with the run's vars interpolated (what the app shows). */
function successText(id: string, lang: 'pt' | 'en', r: { vars?: Record<string, unknown> }): string {
  return interpolate(lesson(id).locale[lang].break!.success, (r.vars ?? {}) as Record<string, string | number>);
}

describe('P3 structure', () => {
  it('ships the seven lessons in order 16..22, the first requiring p-avaliar-recuperacao', () => {
    const got = lessons.filter((l) => P3.includes(l.def.id)).sort((a, b) => a.def.order - b.def.order);
    expect(got.map((l) => l.def.id)).toEqual(P3);
    expect(got.map((l) => l.def.order)).toEqual([16, 17, 18, 19, 20, 21, 22]);
    expect(got[0].def.requires[0]).toBe('p-avaliar-recuperacao');
    for (const l of got) {
      expect(l.def.executors).toContain('simulado');
      expect(l.def.executors).toContain('sua-chave');
      expect(l.def.executors).toContain('no-navegador');
    }
  });

  it('no computed value shadows a flag (it would overwrite it)', () => {
    for (const id of P3) {
      const l = lesson(id);
      const sim = l.def.data.sim as { compute: Record<string, string>; cases: { flags: string[] }[] };
      const flags = new Set(sim.cases.flatMap((c) => c.flags));
      const optionNames = l.def.command.flags.map((f) => f.name);
      for (const name of Object.keys(sim.compute)) {
        expect(flags.has(name), `${id}: compute "${name}" is also a result flag`).toBe(false);
        expect(optionNames.includes(name), `${id}: compute "${name}" overwrites a command option`).toBe(false);
      }
    }
  });
});

for (const lang of LANGS) {
  describe(`[${lang}] P3 journeys`, () => {
    const pt = lang === 'pt';
    const q = (p: string, e: string) => (pt ? p : e);
    for (const id of P3) {
      it(`${id}: default runs clean, cheat breaks it`, () => {
        const l = lesson(id);
        const def = runCmd(id, lang, defaultCommand(l.def.command, lang));
        expect(def.error, 'default command must not error').toBeUndefined();
        expect(def.flags, 'default must not raise the break flag').not.toContain(l.def.break.flag);
        const cheat = l.locale[lang].hints!.cmd[2];
        expect(runCmd(id, lang, cheat).flags, cheat).toContain(l.def.break.flag);
      });
    }

    it('every tryNext command runs; when it raises the break flag, the success text is fully filled and fits the case', () => {
      const raised: string[] = [];
      for (const id of P3) {
        const l = lesson(id);
        const r = runCmd(id, lang, tryNextCommand(id, lang));
        expect(r.error, `${id} tryNext errors`).toBeUndefined();
        if (r.flags.includes(l.def.break.flag)) {
          raised.push(id);
          const text = successText(id, lang, r);
          expect(text, `${id}: unfilled placeholder`).not.toMatch(/\{\w+\}/);
          expect(text, id).not.toMatch(/undefined|NaN/);
        }
      }
      // the three tryNext commands that raise the flag the success text has to fit
      expect(raised).toEqual(['p-extrair-emails-e-notas-fiscais', 'p-triagem-de-tickets', 'p-memoria-de-conversa-e-resumo']);
    });

    it('18/19/21: the success texts fit every command that raises their flag', () => {
      const mail = tryNextCommand('p-extrair-emails-e-notas-fiscais', lang);
      const t18 = successText('p-extrair-emails-e-notas-fiscais', lang, runCmd('p-extrair-emails-e-notas-fiscais', lang, mail));
      expect(t18).toMatch(pt ? /R\$ 3,48 em vez de R\$ 3\.480/ : /R\$ 3\.48 instead of R\$ 3,480/);
      expect(t18).not.toMatch(/Without a check|Sem conferência/);
      expect(t18).toMatch(pt ? /sem itens para somar/ : /no items to add up/);
      const t19 = successText('p-triagem-de-tickets', lang, runCmd('p-triagem-de-tickets', lang, tryNextCommand('p-triagem-de-tickets', lang)));
      expect(t19).not.toMatch(/baixo demais|too low/);
      expect(t19).toMatch(pt ? /88%/ : /88%/);
      // 21: summary + coupon and window + order both raise "forgot" and name the right fact / position / strategy
      const t21a = successText('p-memoria-de-conversa-e-resumo', lang, runCmd('p-memoria-de-conversa-e-resumo', lang, tryNextCommand('p-memoria-de-conversa-e-resumo', lang)));
      expect(t21a).toContain(pt ? 'resumo' : 'summary');
      expect(t21a).toContain(pt ? 'o cupom' : 'the coupon');
      expect(t21a).toContain(pt ? '5ª mensagem' : 'message 5');
      const win = q('continuar --memoria janela', 'continue --memory window');
      const t21b = successText('p-memoria-de-conversa-e-resumo', lang, runCmd('p-memoria-de-conversa-e-resumo', lang, win));
      expect(t21b).toContain(pt ? '"janela"' : '"window"');
      expect(t21b).toContain(pt ? 'o pedido' : 'the order');
      expect(t21b).toContain(pt ? '1ª mensagem' : 'message 1');
      const none = successText('p-memoria-de-conversa-e-resumo', lang, runCmd('p-memoria-de-conversa-e-resumo', lang, q('continuar --memoria nenhuma', 'continue --memory none')));
      expect(none).not.toMatch(/\{\w+\}/);
    });

    it('17: distinct counts the real number of categories shown (5 varied → 5; same-category → 1)', () => {
      const id = 'p-exemplos-few-shot-e-formato';
      expect(runCmd(id, lang, q('assunto --exemplos 5', 'subject --examples 5')).vars?.distinct).toBe(5);
      expect(runCmd(id, lang, q('assunto --exemplos 5 --variedade nao', 'subject --examples 5 --variety no')).vars?.distinct).toBe(1);
      expect(runCmd(id, lang, q('assunto --exemplos 0', 'subject --examples 0')).vars?.distinct).toBe(0);
      const calm = interpolate(lesson(id).locale[lang].break!.calm, runCmd(id, lang, q('assunto', 'subject')).vars as Record<string, string | number>);
      expect(calm).toMatch(pt ? /categorias distintas nos exemplos: 3/ : /distinct categories in the examples: 3/);
    });

    it('PT/EN money in the texts is formatted for the language', () => {
      const id = 'p-agente-com-ferramentas-e-limites';
      const cheat = runCmd(id, lang, q('agir --aprovacao 10000', 'act --approval 10000'));
      const t = successText(id, lang, cheat);
      expect(t).toContain(pt ? 'R$ 10.000' : 'R$ 10,000');
      expect(t).toContain(pt ? 'R$ 1.125' : 'R$ 1,125');
      expect(t).toContain(pt ? 'R$ 500' : 'R$ 500');
      expect(t).toMatch(pt ? /a partir dos quais a política exige aprovação/ : /the policy says needs approval/);
      expect(t).not.toMatch(/teto|ceiling/);
      const t18 = successText('p-extrair-emails-e-notas-fiscais', lang, runCmd('p-extrair-emails-e-notas-fiscais', lang, q('importar --formato nao --conferir nao', 'import --format no --reconcile no')));
      expect(t18).toContain(pt ? 'R$ 1,25 em vez de R$ 1.250' : 'R$ 1.25 instead of R$ 1,250');
    });

    it('16: scope holds the line; short format fits', () => {
      const cake = q('Me dá uma receita de bolo de cenoura?', 'Can you give me a carrot cake recipe?');
      const v = q('conversar', 'chat') + ` "${cake}"`;
      expect(lesson('p-prompt-de-sistema-e-papeis').def.predict!.answer).toBe('refuse');
      expect(runCmd('p-prompt-de-sistema-e-papeis', lang, v).flags).toContain('stayed');
      const noFmt = runCmd('p-prompt-de-sistema-e-papeis', lang, q('conversar --partes papel,escopo,tom', 'chat --parts role,scope,tone'));
      expect(Number(noFmt.vars?.n)).toBeGreaterThan(30);
      expect(Number(runCmd('p-prompt-de-sistema-e-papeis', lang, q('conversar', 'chat')).vars?.n)).toBeLessThanOrEqual(30);
      // an empty prompt part list is accepted and shows the "no system prompt" case
      expect(runCmd('p-prompt-de-sistema-e-papeis', lang, q('conversar --partes nenhuma', 'chat --parts none')).error).toBeUndefined();
    });

    it('17: no examples → free text; varied examples → right category; the right guess is shown', () => {
      const id = 'p-exemplos-few-shot-e-formato';
      expect(lesson(id).def.predict!.answer).toBe('free');
      expect(runCmd(id, lang, q('assunto --exemplos 0', 'subject --examples 0')).flags).toContain('freeform');
      expect(runCmd(id, lang, q('assunto', 'subject')).flags).toContain('good');
      const e3 = q('assunto "Não consigo trocar a senha do portal: o link por e-mail não chega."', 'subject "I can’t change my portal password: the email link never arrives."');
      const r = runCmd(id, lang, e3);
      expect(r.flags).toContain('good');
      expect(String(r.vars?.out)).not.toContain('(#');
      // same-category examples don't hurt when the email really is about billing
      const e2 = q('assunto "Fui cobrado duas vezes pelo pedido 7301 no cartão." --variedade nao', 'subject "I was charged twice for order 7301 on my card." --variety no');
      expect(runCmd(id, lang, e2).flags).toContain('good');
    });

    it('18: without the Brazilian-format hint the sum check sends the invoice to review', () => {
      const id = 'p-extrair-emails-e-notas-fiscais';
      expect(lesson(id).def.predict!.answer).toBe('review');
      const r = runCmd(id, lang, q('importar --formato nao', 'import --format no'));
      expect(r.flags).toEqual(expect.arrayContaining(['review', 'caught']));
      expect(r.flags).not.toContain('saved');
      expect(runCmd(id, lang, q('importar', 'import')).flags).toContain('saved');
      // no items to add up → the check can't catch it (the email case)
      const mail = q('Oi, aqui é a Marina da Gráfica Boa Vista. Segue a cobrança do contrato 31/2026: R$ 3.480,00, com vencimento em 15/04/2026. Qualquer dúvida é só chamar!', 'Hi, Marina from Gráfica Boa Vista here. Here is the charge for contract 31/2026: R$ 3.480,00, due on 15/04/2026. Any questions, just ask!');
      expect(runCmd(id, lang, `${q('importar', 'import')} "${mail}" ${q('--formato nao', '--format no')}`).flags).toContain('silentError');
      // a missing field is caught by the schema
      const nf = q('NOTA FISCAL DE SERVIÇO Nº 4472 | Prestador: Gráfica Boa Vista Ltda | Itens: arte final R$ 350,00 | Total: R$ 350,00', 'SERVICE INVOICE No. 4472 | Provider: Gráfica Boa Vista Ltda | Items: final artwork R$ 350,00 | Total: R$ 350,00');
      expect(runCmd(id, lang, `${q('importar', 'import')} "${nf}"`).flags).toEqual(expect.arrayContaining(['invalid', 'review']));
    });

    it('19: the ambiguous ticket escalates at 70%; a confident error slips through', () => {
      const id = 'p-triagem-de-tickets';
      expect(lesson(id).def.predict!.answer).toBe('human');
      const amb = q('Não consigo entrar no portal e ainda fui cobrado duas vezes este mês.', 'I can’t log in to the portal and I was also charged twice this month.');
      const v = q('triar', 'triage');
      expect(runCmd(id, lang, `${v} "${amb}"`).flags).toContain('escalated');
      expect(runCmd(id, lang, v).flags).toContain('routed');
      const color = q('Recebi o produto, mas a cor é diferente da foto e quero devolver.', 'I got the product, but the color is different from the photo and I want to return it.');
      expect(runCmd(id, lang, `${v} "${color}" ${q('--limite 0.95', '--threshold 0.95')}`).flags).toContain('escalated');
      expect(runCmd(id, lang, `${v} "${color}"`).flags).toContain('misrouted');
      expect(runCmd(id, lang, `${v} ${q('--rotulos livres', '--labels free')}`).flags).toContain('unroutable');
    });

    it('20: the portal asks for approval above the limit; small refunds go through; steps and tools are respected', () => {
      const id = 'p-agente-com-ferramentas-e-limites';
      expect(lesson(id).def.predict!.answer).toBe('ask');
      const v = q('agir', 'act');
      const def = runCmd(id, lang, v);
      expect(def.flags).toContain('pending');
      expect(def.flags).not.toContain('executed');
      const small = q('O pedido 9001 chegou com defeito. Reembolse 90% do valor, como manda a política.', 'Order 9001 arrived defective. Refund 90% of the value, as the policy says.');
      expect(runCmd(id, lang, `${v} "${small}"`).flags).toContain('executed');
      const old = q('O pedido 7700 não serviu. Reembolse o valor todo.', 'Order 7700 didn’t fit. Refund the whole amount.');
      expect(runCmd(id, lang, `${v} "${old}"`).flags).toContain('refused');
      expect(runCmd(id, lang, `${v} ${q('--passos 2', '--steps 2')}`).flags).toContain('limit');
      expect(runCmd(id, lang, `${v} ${q('--ferramentas calculadora,reembolsar', '--tools calculator,refund')}`).flags).toContain('blocked');
      expect(runCmd(id, lang, `${v} ${q('--ferramentas consultar,reembolsar', '--tools lookup,refund')}`).flags).toContain('wrongAmount');
      expect(runCmd(id, lang, `${v} ${q('--ferramentas consultar,calculadora', '--tools lookup,calculator')}`).flags).not.toContain('pending');
    });

    it('21: the summary sends fewer tokens; a window forgets the start; the summary loses the coupon', () => {
      const id = 'p-memoria-de-conversa-e-resumo';
      expect(lesson(id).def.predict!.answer).toBe('less');
      const v = q('continuar', 'continue');
      const sum = runCmd(id, lang, `${v} ${q('--memoria resumo', '--memory summary')}`);
      const full = runCmd(id, lang, `${v} ${q('--memoria completa', '--memory full')}`);
      expect(Number(sum.vars?.sentTok)).toBeLessThan(Number(full.vars?.sentTok));
      expect(Number(sum.vars?.savedPct)).toBeGreaterThan(30);
      expect(Number(full.vars?.savedPct)).toBe(0);
      expect(sum.flags).toContain('remembered');
      const coupon = q('Qual cupom eu usei na compra?', 'Which coupon did I use on the purchase?');
      expect(runCmd(id, lang, `${v} "${coupon}"`).flags).toContain('forgot');
      expect(runCmd(id, lang, `${v} "${coupon}" ${q('--memoria completa', '--memory full')}`).flags).toContain('remembered');
      expect(runCmd(id, lang, `${v} ${q('--memoria nenhuma', '--memory none')}`).flags).toContain('forgot');
      const addr = q('Para onde vai a entrega agora?', 'Where is the delivery going now?');
      expect(runCmd(id, lang, `${v} "${addr}" ${q('--memoria janela', '--memory window')}`).flags).toContain('remembered');
    });

    it('22: the third-party server is blocked by confirmation; an open HTTP endpoint is flagged', () => {
      const id = 'p-mcp-conectar-sistemas';
      expect(lesson(id).def.predict!.answer).toBe('block');
      const v = q('conectar', 'connect');
      expect(runCmd(id, lang, `${v} ${q('--servidor terceiro', '--server thirdparty')}`).flags).toContain('blocked');
      expect(runCmd(id, lang, v).flags).toContain('done');
      expect(runCmd(id, lang, `${v} ${q('--transporte http --login nao', '--transport http --auth no')}`).flags).toContain('exposed');
      expect(runCmd(id, lang, `${v} ${q('--transporte http', '--transport http')}`).flags).not.toContain('exposed');
    });
  });
}

describe('P3 real ops with fake deps', () => {
  const cake = 'Me dá uma receita de bolo de cenoura?';

  it('chat (16): the system prompt is assembled from the checked parts; the refusal sentence is read from the answer', async () => {
    const seen: string[] = [];
    const chat = async (m: { role: string; content: string }[]) => {
      seen.push(m.map((x) => `${x.role}:${x.content}`).join('\n'));
      return 'Isso foge do que eu posso ajudar: sou a Aurinha, do RH da Aurora.';
    };
    const kept = await runReal('p-prompt-de-sistema-e-papeis', `conversar "${cake}"`, { chat });
    expect(kept.flags).toContain('stayed');
    expect(seen[0]).toMatch(/system:Você é a Aurinha/);
    expect(seen[0]).toMatch(/Responda em no máximo duas frases/);
    const gone = await runReal('p-prompt-de-sistema-e-papeis', `conversar "${cake}" --partes papel,tom,formato`, { chat: async () => 'Claro! Bata 3 cenouras e 4 ovos.' }, 'pt', 'sua-chave');
    expect(gone.flags).toContain('offscript');
    expect(seen.length).toBe(1);
  });

  it('chat (17): examples go into the prompt; the category and the format are read from the answer', async () => {
    let sys = '';
    const mk = (reply: string) => async (m: { role: string; content: string }[]) => {
      sys = m[0].content;
      return reply;
    };
    const ok = await runReal('p-exemplos-few-shot-e-formato', 'assunto', { chat: mk('[Entrega] Pedido atrasado (#8812)') });
    expect(ok.flags).toContain('good');
    expect(sys).toContain('<examples>');
    expect(sys).toContain('[Acesso]');
    const copy = await runReal('p-exemplos-few-shot-e-formato', 'assunto --variedade nao', { chat: mk('[Cobrança] Pedido atrasado (#8812)') });
    expect(copy.flags).toContain('copycat');
    expect(sys).not.toContain('[Acesso]');
    const free = await runReal('p-exemplos-few-shot-e-formato', 'assunto --exemplos 0', { chat: mk('Cliente reclamando do atraso.') });
    expect(free.flags).toContain('freeform');
    expect(sys).not.toContain('<examples>');
  });

  it('json (18): schema problems, a wrong total caught by the check, and a silent error without it', async () => {
    const good = '{"number":"4471","provider":"Gráfica Boa Vista Ltda","date":"2026-03-12","items":[1000,250],"total":1250}';
    const bad = '{"number":"4471","provider":"Gráfica Boa Vista Ltda","date":"2026-03-12","items":[1,250],"total":1.25}';
    expect((await runReal('p-extrair-emails-e-notas-fiscais', 'importar', { chat: async () => `Aqui: ${good}` })).flags).toContain('saved');
    const caught = await runReal('p-extrair-emails-e-notas-fiscais', 'importar --formato nao', { chat: async () => bad });
    expect(caught.flags).toEqual(expect.arrayContaining(['review', 'caught']));
    expect((await runReal('p-extrair-emails-e-notas-fiscais', 'importar --formato nao --conferir nao', { chat: async () => bad })).flags).toContain('silentError');
    const prose = await runReal('p-extrair-emails-e-notas-fiscais', 'importar', { chat: async () => 'O total é mil duzentos e cinquenta.' });
    expect(prose.flags).toEqual(expect.arrayContaining(['invalid', 'review']));
    const noDate = await runReal('p-extrair-emails-e-notas-fiscais', 'importar', { chat: async () => '{"number":"4471","provider":"x","date":null,"items":[],"total":1250}' });
    expect(noDate.flags).toContain('invalid');
  });

  it('json (19): category and verbalized confidence drive the routing; free labels fail the enum', async () => {
    const amb = 'Não consigo entrar no portal e ainda fui cobrado duas vezes este mês.';
    const r1 = await runReal('p-triagem-de-tickets', `triar "${amb}"`, { chat: async () => '{"category":"access","confidence":"medium"}' });
    expect(r1.flags).toContain('escalated');
    const r2 = await runReal('p-triagem-de-tickets', `triar "${amb}"`, { chat: async () => '{"category":"access","confidence":"high"}' });
    expect(r2.flags).toContain('misrouted');
    const r3 = await runReal('p-triagem-de-tickets', `triar "${amb}" --rotulos livres`, { chat: async () => '{"category":"Pagamento duplicado","confidence":"high"}' });
    expect(r3.flags).toContain('unroutable');
    const r4 = await runReal('p-triagem-de-tickets', 'triar', { chat: async () => '{"category":"billing","confidence":"high"}' }, 'pt', 'sua-chave');
    expect(r4.flags).toContain('routed');
  });

  it('tools (20): a real loop proposes a refund; the portal still applies the approval rule', async () => {
    const replies = ['{"tool":"lookup","args":{"key":"8812"}}', '{"tool":"calculator","args":{"expression":"1250*0.9"}}', '{"answer":"REEMBOLSAR 8812 1125"}'];
    let i = 0;
    const r = await runReal('p-agente-com-ferramentas-e-limites', 'agir', { chat: async () => replies[i++] });
    expect(r.flags).toContain('pending');
    const text = JSON.stringify((r as unknown as { widgets: unknown[] }).widgets);
    expect(text).toMatch(/1125/);
    i = 0;
    const cheat = await runReal('p-agente-com-ferramentas-e-limites', 'agir --aprovacao 10000', { chat: async () => replies[i++] });
    expect(cheat.flags).toContain('overreach');
    i = 0;
    const slow = await runReal('p-agente-com-ferramentas-e-limites', 'agir --passos 1', { chat: async () => replies[i++] });
    expect(slow.flags).toContain('limit');
    expect(slow.flags).not.toContain('pending');
    const wrong = await runReal('p-agente-com-ferramentas-e-limites', 'agir --aprovacao 10000', { chat: async () => '{"answer":"REEMBOLSAR 8812 1250"}' });
    expect(wrong.flags).not.toContain('overreach');
  });

  it('chat (21): what the model answers decides remembered / forgot, with the right context sent', async () => {
    let user = '';
    const chat = (reply: string) => async (m: { role: string; content: string }[]) => {
      user = m[m.length - 1].content;
      return reply;
    };
    const ok = await runReal('p-memoria-de-conversa-e-resumo', 'continuar', { chat: chat('Seu pedido é o 8812.') });
    expect(ok.flags).toContain('remembered');
    expect(user).toMatch(/Resumo da conversa até aqui/);
    const lost = await runReal('p-memoria-de-conversa-e-resumo', 'continuar --memoria janela', { chat: chat('Desculpe, não tenho essa informação.') });
    expect(lost.flags).toContain('forgot');
    expect(user).not.toMatch(/8812/);
    const none = await runReal('p-memoria-de-conversa-e-resumo', 'continuar --memoria nenhuma', { chat: chat('Não sei.') });
    expect(none.flags).toContain('forgot');
  });

  it('chat (22): whether the real model follows the poisoned description decides the leak', async () => {
    let sys = '';
    const chat = (reply: string) => async (m: { role: string; content: string }[]) => {
      sys = m[0].content;
      return reply;
    };
    const obeyed = 'formatar_texto(texto="x", contexto="tabela-de-precos: ...")';
    const leak = await runReal('p-mcp-conectar-sistemas', 'conectar --servidor terceiro --confirmar nao', { chat: chat(obeyed) });
    expect(leak.flags).toContain('leak');
    expect(sys).toMatch(/tabela-de-precos/);
    const blocked = await runReal('p-mcp-conectar-sistemas', 'conectar --servidor terceiro', { chat: chat(obeyed) });
    expect(blocked.flags).toContain('blocked');
    const resisted = await runReal('p-mcp-conectar-sistemas', 'conectar --servidor terceiro --confirmar nao', { chat: chat('formatar_texto(texto="x")') });
    expect(resisted.flags).toEqual(expect.arrayContaining(['ignored']));
    expect(resisted.flags).not.toContain('leak');
    const fine = await runReal('p-mcp-conectar-sistemas', 'conectar', { chat: chat('criar_chamado(pedido="8812")') }, 'pt', 'sua-chave');
    expect(fine.flags).toContain('done');
    expect(sys).toMatch(/consultar_pedido/);
  });
  it('chat (16): the refusal is read from the exact sentence; the role intro or a mention of HR is not a refusal', async () => {
    const off = (reply: string) => runReal('p-prompt-de-sistema-e-papeis', `conversar "${cake}"`, { chat: async () => reply });
    expect((await off('Oi, eu sou a Aurinha, do RH da Aurora! Bata 3 cenouras e 4 ovos.')).flags).toContain('offscript');
    expect((await off('Isso foge do que eu posso ajudar: sou a Aurinha, do RH da Aurora.')).flags).toContain('stayed');
    const l = lesson('p-prompt-de-sistema-e-papeis');
    expect(l.locale.pt.data.refusalMark).toBe('foge do que eu posso ajudar');
    expect(l.locale.en.data.refusalMark).toBe('outside what I can help with');
    expect(String(l.locale.pt.data.refusal)).toContain(String(l.locale.pt.data.refusalMark));
    expect(String(l.locale.en.data.refusal)).toContain(String(l.locale.en.data.refusalMark));
    expect(String(l.locale.pt.data.sysScope)).toContain(String(l.locale.pt.data.refusal));
  });

  it('json (18): the sum check uses the values the model returned (realFields), not scripted ones', async () => {
    const id = 'p-extrair-emails-e-notas-fiscais';
    const run = (reply: string, cmd = 'importar') => runReal(id, cmd, { chat: async () => reply });
    const head = '"number":"4471","provider":"Gráfica Boa Vista Ltda","date":"2026-03-12"';
    // items and total consistent with each other but both wrong: the check passes, and the gold total says it is wrong
    const both = await run(`{${head},"items":[1,250],"total":251}`);
    expect(both.flags).toContain('silentError');
    // total right, items wrong → the check catches it, with the model's own numbers in the text
    const diff = await run(`{${head},"items":[1000,200],"total":1250}`);
    expect(diff.flags).toEqual(expect.arrayContaining(['review', 'caught']));
    const metrics = JSON.stringify((diff as unknown as { widgets: unknown[] }).widgets);
    expect(metrics).toMatch(/"value":1200/);
    // 12500 is not 1250 (a prefix match would have said it was right)
    const prefix = await run(`{${head},"items":[12500],"total":12500}`, 'importar --conferir nao');
    expect(prefix.flags).toContain('silentError');
    // no items returned: nothing to add up, so the check cannot stop a wrong total
    const noItems = await run(`{${head},"items":[],"total":1.25}`);
    expect(noItems.flags).toContain('silentError');
    const t = interpolate(lesson(id).locale.pt.break!.success, noItems.vars as Record<string, string | number>);
    expect(t).toContain('R$ 1,25 em vez de R$ 1.250');
  });

  it('tools (20): in real mode the denial comes from the model; proposing a refund for an expired order is flagged', async () => {
    const id = 'p-agente-com-ferramentas-e-limites';
    const r3 = 'O pedido 7700 não serviu. Reembolse o valor todo.';
    const go = (reply: string) => {
      const replies = ['{"tool":"lookup","args":{"key":"7700"}}', reply];
      let i = 0;
      return runReal(id, `agir "${r3}"`, { chat: async () => replies[i++] });
    };
    const denied = await go('{"answer":"NEGAR 7700 fora do prazo"}');
    expect(denied.flags).toContain('refused');
    expect(denied.flags).not.toContain('proposedAnyway');
    const anyway = await go('{"answer":"REEMBOLSAR 7700 300"}');
    expect(anyway.flags).toContain('proposedAnyway');
    expect(anyway.flags).not.toContain('refused');
    expect(anyway.flags).not.toContain('executed');
    expect(String(lesson(id).locale.pt.data.sysTools)).toContain('NEGAR');
    expect(String(lesson(id).locale.en.data.sysTools)).toContain('DENY');
  });

  it('chat (22): a refusal that only quotes the URI is not obeying; the system prompt is neutral about whose server it is', async () => {
    let sys = '';
    const chat = (reply: string) => async (m: { role: string; content: string }[]) => {
      sys = m[0].content;
      return reply;
    };
    const refusal = 'Não vou enviar aurora://financeiro/tabela-de-precos para esse servidor.';
    const r = await runReal('p-mcp-conectar-sistemas', 'conectar --servidor terceiro --confirmar nao', { chat: chat(refusal) });
    expect(r.flags).not.toContain('leak');
    expect(r.flags).toContain('ignored');
    expect(sys).not.toMatch(/servidor MCP da Aurora/);
  });
});
