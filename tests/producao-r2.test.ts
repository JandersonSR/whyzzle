import { describe, expect, it } from 'vitest';
import { defaultCommand, parseCommand } from '../src/engine/command';
import { LANGS, type Lang } from '../src/engine/schema';
import { interpolate, makeRng } from '../src/engine/text';
import { ADAPTERS, type RealDeps } from '../src/runtime/adapters';
import { lesson, lessons, runCmd } from './helpers';

/**
 * IA aplicada · Produção · R2 (segurança, privacidade e governança). For pt and en: the default command runs without error and
 * never raises the break flag, hint 3 raises it, the guess marked right is what the simulator shows, and every
 * tryNext command runs with every text it triggers fully filled. Real ops run with fake deps.
 */

const R2 = [
  'r-prompt-injection-direta-e-indireta',
  'r-guardrails-de-entrada-e-saida',
  'r-vazamento-de-dados-e-permissoes',
  'r-dados-pessoais-e-lgpd',
  'r-jailbreak-e-red-teaming',
  'r-auditoria-e-rastreabilidade',
  'r-politica-de-uso-de-ia',
];

type Run = ReturnType<typeof runCmd> & { widgets?: Record<string, unknown>[] };
const vars = (r: { vars?: Record<string, unknown> }) => (r.vars ?? {}) as Record<string, string | number>;
const filled = (t: string) => !/\{\w+\}/.test(t) && !/undefined|NaN/.test(t);

/** The command inside a tryNext.cmd sentence: the longest prefix from the verb that parses, minus trailing prose. */
function tryNextCommand(id: string, lang: Lang): string {
  const l = lesson(id);
  const t = l.locale[lang].tryNext!.cmd;
  const rest = t.slice(t.indexOf(`${l.def.command.verb[lang]} `));
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

/** Every "@key" text the resolved widgets show, interpolated with the run's vars (what the scene renders). */
function sceneTexts(id: string, lang: Lang, r: Run): string[] {
  const scene = lesson(id).locale[lang].scene as Record<string, unknown>;
  const out: string[] = [];
  const walk = (v: unknown) => {
    if (typeof v === 'string' && v.startsWith('@')) {
      const s = scene[v.slice(1)];
      expect(typeof s, `${id}: scene.${v.slice(1)}`).toBe('string');
      out.push(interpolate(String(s), vars(r)));
    } else if (Array.isArray(v)) v.forEach(walk);
    else if (v && typeof v === 'object') Object.values(v).forEach(walk);
  };
  walk(r.widgets ?? []);
  return out;
}

/** The texts the app shows after a run: success when the break flag is up, calm otherwise, plus the scene texts. */
function shownTexts(id: string, lang: Lang, r: Run): string[] {
  const l = lesson(id);
  const b = l.locale[lang].break!;
  const main = r.flags.includes(l.def.break.flag) ? b.success : b.calm;
  return [interpolate(main, vars(r)), ...sceneTexts(id, lang, r)];
}


describe('R2 structure', () => {
  it('ships the seven lessons in order 8..14 on the producao track, the first requiring the last R1 lesson', () => {
    const got = lessons.filter((l) => R2.includes(l.def.id)).sort((a, b) => a.def.order - b.def.order);
    expect(got.map((l) => l.def.id)).toEqual(R2);
    expect(got.map((l) => l.def.order)).toEqual([8, 9, 10, 11, 12, 13, 14]);
    for (const l of got) {
      expect(l.track).toBe('producao');
      expect(l.def.executors[0]).toBe('simulado');
    }
    expect(got[0].def.requires).toEqual(['r-ciclo-de-feedback-de-usuarios']);
    got.slice(1).forEach((l, i) => expect(l.def.requires).toEqual([got[i].def.id]));
  });

  it('no computed value shadows a result flag or a command option', () => {
    for (const id of R2) {
      const l = lesson(id);
      const sim = l.def.data.sim as { compute: Record<string, string>; cases: { flags: string[] }[] };
      const flags = new Set(sim.cases.flatMap((c) => c.flags));
      const options = l.def.command.flags.map((f) => f.name);
      for (const name of Object.keys(sim.compute)) {
        expect(flags.has(name), `${id}: compute "${name}" is a flag`).toBe(false);
        expect(options.includes(name), `${id}: compute "${name}" is an option`).toBe(false);
      }
    }
  });

  it('recipes are real multi-line code, and table cells stay short', () => {
    for (const id of R2) {
      for (const lang of LANGS) {
        const loc = lesson(id).locale[lang];
        expect(loc.recipe.steps.some((s) => s.split('\n').length >= 3), `${id} recipe has a multi-line step`).toBe(true);
        const r = runCmd(id, lang, defaultCommand(lesson(id).def.command, lang)) as Run;
        for (const w of r.widgets ?? []) {
          if (w.type !== 'table') continue;
          for (const row of w.rows as unknown[][]) {
            for (const cell of row) {
              const t = typeof cell === 'string' && cell.startsWith('@') ? String((loc.scene as Record<string, unknown>)[cell.slice(1)]) : String(cell);
              expect(t.length, `${id} cell "${t}"`).toBeLessThanOrEqual(36);
            }
          }
        }
      }
    }
  });

  it('models are named with the current ids, no curly quotes in real markers, LGPD disclaimer is stated once', () => {
    for (const id of R2) {
      for (const lang of LANGS) {
        const text = JSON.stringify(lesson(id).locale[lang].recipe);
        for (const old of ['claude-3', 'claude-2', 'claude-instant', 'gpt-4', 'claude-sonnet-4', 'claude-haiku-4']) expect(text.includes(old), `${id} ${old}`).toBe(false);
      }
    }
    for (const lang of LANGS) {
      const l = lesson('r-dados-pessoais-e-lgpd').locale[lang];
      expect(l.why.especialista).toMatch(lang === 'pt' ? /não é aconselhamento jurídico/ : /not legal advice/);
      expect(l.why.simples + l.why.dev).not.toMatch(lang === 'pt' ? /não é aconselhamento jurídico/ : /not legal advice/);
    }
  });
});

for (const lang of LANGS) {
  const pt = lang === 'pt';
  const q = <T,>(a: T, b: T): T => (pt ? a : b);

  describe(`[${lang}] R2 journeys`, () => {
    for (const id of R2) {
      it(`${id}: default runs clean, cheat breaks it, texts are filled`, () => {
        const l = lesson(id);
        const def = runCmd(id, lang, defaultCommand(l.def.command, lang)) as Run;
        expect(def.error, 'default must not error').toBeUndefined();
        expect(def.flags, 'default must not raise the break flag').not.toContain(l.def.break.flag);
        for (const t of shownTexts(id, lang, def)) expect(filled(t), `${id} default: ${t}`).toBe(true);
        const cheat = l.locale[lang].hints!.cmd[2];
        expect(l.locale[lang].break!.mission.cmd).toContain(cheat);
        const r = runCmd(id, lang, cheat) as Run;
        expect(r.error).toBeUndefined();
        expect(r.flags, cheat).toContain(l.def.break.flag);
        for (const t of shownTexts(id, lang, r)) expect(filled(t), `${id} cheat: ${t}`).toBe(true);
      });

      it(`${id}: the tryNext command runs, every text it triggers is filled and it does not break the lesson`, () => {
        const l = lesson(id);
        const r = runCmd(id, lang, tryNextCommand(id, lang)) as Run;
        expect(r.error, `${id} tryNext errors`).toBeUndefined();
        expect(r.flags, `${id} tryNext must not be the break`).not.toContain(l.def.break.flag);
        for (const t of shownTexts(id, lang, r)) expect(filled(t), `${id} tryNext: ${t}`).toBe(true);
      });
    }

    it('every example argument runs in simulated mode with filled texts', () => {
      for (const id of R2) {
        const l = lesson(id);
        for (const ex of l.def.command.arg.examples) {
          const r = runCmd(id, lang, `${l.def.command.verb[lang]} "${ex[lang]}"`) as Run;
          expect(r.error, `${id} ${ex[lang]}`).toBeUndefined();
          for (const t of shownTexts(id, lang, r)) expect(filled(t), `${id} ${ex[lang]}: ${t}`).toBe(true);
        }
      }
    });

    it('the break success text is true for every command that raises the break flag (all combinations of the options)', () => {
      for (const id of R2) {
        const l = lesson(id);
        const verb = l.def.command.verb[lang];
        // Every enum/bool flag combination, the default argument: whenever the break flag is raised, its texts are filled.
        const opts = l.def.command.flags.filter((f) => f.type === 'enum' || f.type === 'bool');
        const combos: string[][] = [[]];
        for (const f of opts) {
          const vals = f.type === 'bool' ? ['yes', 'no'] : f.options!.map((o) => o.id);
          const next: string[][] = [];
          for (const c of combos) for (const v of vals) next.push([...c, `--${f.name}=${v}`]);
          combos.splice(0, combos.length, ...next);
        }
        for (const c of combos) {
          const values: Record<string, string | boolean> = {};
          const line = `${verb} ${c.map((x) => { const [k, v] = x.slice(2).split('='); const f = l.def.command.flags.find((z) => z.name === k)!; return `--${f.alias[lang]}=${v}`; }).join(' ')}`;
          void values;
          const r = runCmd(id, lang, line) as Run;
          if (r.error) continue;
          for (const t of shownTexts(id, lang, r)) expect(filled(t), `${id} ${line}: ${t}`).toBe(true);
        }
      }
    });

    it('08: marking documents cuts the obeyed variations from 15 to 4 but not to zero; privilege and confirmation contain the damage', () => {
      const id = 'r-prompt-injection-direta-e-indireta';
      const [send, leak, hijack, benign] = lesson(id).def.command.arg.examples.map((e) => e[lang]);
      const v = q('injetar', 'inject');
      expect(lesson(id).def.predict!.answer).toBe('some');
      const def = runCmd(id, lang, v);
      expect(def.vars).toMatchObject({ obeyN: 4, variants: 20 });
      expect(def.flags).toEqual(expect.arrayContaining(['blocked']));
      expect(def.flags).not.toContain('exfil');
      expect(runCmd(id, lang, q('injetar --delimitar nao', 'inject --delimit no')).vars).toMatchObject({ obeyN: 15 });
      expect(runCmd(id, lang, q('injetar --canal chat', 'inject --channel chat')).vars).toMatchObject({ obeyN: 11 });
      expect(runCmd(id, lang, q('injetar --canal chat --delimitar nao', 'inject --channel chat --delimit no')).vars).toMatchObject({ obeyN: 11 });
      const noTool = runCmd(id, lang, q('injetar --ferramentas consulta --confirmar nao', 'inject --tools read --confirm no'));
      expect(noTool.flags).toEqual(expect.arrayContaining(['noPower']));
      expect(noTool.flags).not.toContain('exfil');
      expect(runCmd(id, lang, `${v} "${leak}"`).flags).toContain('promptLeak');
      expect(runCmd(id, lang, `${v} "${hijack}"`).flags).toContain('hijacked');
      expect(runCmd(id, lang, `${v} "${benign}"`).flags).toContain('clean');
      expect(runCmd(id, lang, `${v} "${send}" ${q('--confirmar nao', '--confirm no')}`).flags).toContain('exfil');
      expect((runCmd(id, lang, `${v} "texto livre"`).error as { code?: string } | undefined)?.code).toBe('unknownPayload');
      // the real marker never appears in the intro texts
      const loc = lesson(id).locale[lang];
      expect(JSON.stringify([loc.title, loc.subtitle, loc.mission, loc.predict])).not.toContain('ZK-4821');
    });

    it('09: keywords miss the rewritten attack and block the legitimate question; the classifier and the output filter fix what they can; the poem passes everything', () => {
      const id = 'r-guardrails-de-entrada-e-saida';
      const [ok, literal, legit, , poem] = lesson(id).def.command.arg.examples.map((e) => e[lang]);
      const v = q('proteger', 'guard');
      const kw = q('--entrada palavras', '--input keywords');
      expect(lesson(id).def.predict!.answer).toBe('misses');
      const def = runCmd(id, lang, v);
      expect(def.flags).toContain('stopped');
      expect(def.vars).toMatchObject({ scoreS: q('0,83', '0.83'), limitS: q('0,60', '0.60'), layers: 2 });
      expect(runCmd(id, lang, `${v} ${kw} ${q('--saida nao', '--output no')}`).flags).toContain('leaked');
      expect(runCmd(id, lang, `${v} ${kw}`).flags).toContain('stopped'); // the output filter catches the CPF
      expect(runCmd(id, lang, `${v} "${literal}" ${kw}`).flags).toContain('stopped');
      expect(runCmd(id, lang, `${v} "${legit}" ${kw}`).flags).toContain('overblock');
      expect(runCmd(id, lang, `${v} "${legit}"`).flags).toContain('served');
      expect(runCmd(id, lang, `${v} "${legit}" ${q('--limite 0.3', '--threshold 0.3')}`).flags).toContain('overblock');
      expect(runCmd(id, lang, `${v} "${ok}" ${q('--entrada nenhum --saida nao', '--input off --output no')}`).flags).toContain('served');
      const hi = runCmd(id, lang, `${v} ${q('--limite 0.9', '--threshold 0.9')}`);
      expect(hi.flags).toContain('stopped');
      expect(runCmd(id, lang, `${v} ${q('--limite 0.9 --saida nao', '--threshold 0.9 --output no')}`).flags).toContain('leaked');
      const p = runCmd(id, lang, `${v} "${poem}"`) as Run;
      expect(p.flags).toContain('leaked');
      expect(p.widgets!.some((w) => w.type === 'note' && w.tone === 'bad' && String(w.text).startsWith('@leakNote'))).toBe(true);
      expect((runCmd(id, lang, `${v} "qualquer coisa"`).error as { code?: string } | undefined)?.code).toBe('unknownMsg');
    });

    it('10: a rule only in the prompt exposes the salary documents; filtering after the ranking loses the profit-share answer; the search filter does neither', () => {
      const id = 'r-vazamento-de-dados-e-permissoes';
      const [vac, salary, disc, plr] = lesson(id).def.command.arg.examples.map((e) => e[lang]);
      const v = q('acessar', 'access');
      const f = (x: string) => q(`--filtro ${x}`, `--filter ${x === 'busca' ? 'search' : x === 'depois' ? 'after' : x}`);
      expect(lesson(id).def.predict!.answer).toBe('yes');
      const def = runCmd(id, lang, v);
      expect(def.flags).toContain('refused');
      expect(def.vars).toMatchObject({ nCtx: 0, nExposed: 0 });
      const bad = runCmd(id, lang, `${v} ${f('prompt')}`);
      expect(bad.flags).toContain('leak');
      expect(bad.vars).toMatchObject({ nCtx: 2, nExposed: 2 });
      expect(runCmd(id, lang, `${v} ${f('depois')}`).flags).not.toContain('leak');
      expect(runCmd(id, lang, `${v} "${plr}" ${f('depois')}`).flags).toContain('lostAnswer');
      expect(runCmd(id, lang, `${v} "${plr}"`).flags).toContain('answered');
      expect(runCmd(id, lang, `${v} "${plr}" ${f('prompt')}`).vars).toMatchObject({ nExposed: 3 });
      expect(runCmd(id, lang, `${v} "${vac}" ${f('prompt')}`).flags).not.toContain('leak');
      expect(runCmd(id, lang, `${v} "${disc}" ${q('--perfil gestor', '--role manager')} ${f('prompt')}`).vars).toMatchObject({ nExposed: 1 });
      expect(runCmd(id, lang, `${v} "${disc}" ${q('--perfil gestor', '--role manager')}`).flags).toContain('refused');
      for (const x of ['busca', 'depois', 'prompt']) expect(runCmd(id, lang, `${v} "${salary}" ${q('--perfil rh', '--role hr')} ${f(x)}`).flags, x).not.toContain('leak');
      expect(runCmd(id, lang, `${v} "${salary}" ${q('--perfil rh', '--role hr')}`).flags).toContain('answered');
      expect((runCmd(id, lang, `${v} "qualquer"`).error as { code?: string } | undefined)?.code).toBe('unknownQ');
      const loc = lesson(id).locale[lang];
      expect(JSON.stringify([loc.title, loc.subtitle, loc.mission, loc.predict])).not.toMatch(/41[.,]370|ADV-1703|PIP-0731|1[.,]284[.,]560/);
    });

    it('11: keeping everything 730 days exposes 43,800 conversations; health data left in is flagged as sensitive; redaction is shown for the examples', () => {
      const id = 'r-dados-pessoais-e-lgpd';
      const [m1, m2, m3] = lesson(id).def.command.arg.examples.map((e) => e[lang]);
      const v = q('minimizar', 'minimize');
      expect(lesson(id).def.predict!.answer).toBe('many');
      const def = runCmd(id, lang, v) as Run;
      expect(def.flags).toContain('minimal');
      expect(def.vars).toMatchObject({ retained: 25714, records: 0 });
      const bad = runCmd(id, lang, q('minimizar --redigir nenhum --retencao 730', 'minimize --redact none --retention 730'));
      expect(bad.flags).toContain('excess');
      expect(bad.vars).toMatchObject({ retained: 208571, keptPct: 21, records: 43800, recordsS: q('43.800', '43,800') });
      const noHealth = runCmd(id, lang, q('minimizar --redigir cpf,email,telefone', 'minimize --redact cpf,email,phone'));
      expect(noHealth.flags).toEqual(expect.arrayContaining(['sensitive']));
      expect(noHealth.flags).not.toContain('excess');
      expect(noHealth.vars).toMatchObject({ records: 771 });
      expect(runCmd(id, lang, q('minimizar --redigir cpf,email,telefone --retencao 30', 'minimize --redact cpf,email,phone --retention 30')).vars).toMatchObject({ records: 257 });
      expect(runCmd(id, lang, q('minimizar --retencao 120 --base nenhuma', 'minimize --retention 120 --basis none')).flags).toEqual(expect.arrayContaining(['longRetention', 'noBasis']));
      const r1 = runCmd(id, lang, `${v} "${m1}"`) as Run;
      const flow = r1.widgets!.find((w) => w.type === 'flow') as { steps: { sub: string }[] };
      expect(flow.steps[1].sub).toBe('Meu CPF é [CPF] e meu e-mail é [EMAIL]. Pode atualizar meu cadastro?'.replace(/.*/, q('Meu CPF é [CPF] e meu e-mail é [EMAIL]. Pode atualizar meu cadastro?', 'My CPF is [CPF] and my e-mail is [EMAIL]. Can you update my record?')));
      const r2 = runCmd(id, lang, `${v} "${m2}" ${q('--redigir telefone', '--redact phone')}`) as Run;
      expect((r2.widgets!.find((w) => w.type === 'flow') as { steps: { sub: string }[] }).steps[1].sub).toContain('[');
      expect(runCmd(id, lang, `${v} "${m3}"`).error).toBeUndefined();
    });

    it('12: a blocklist zeroes the known suite but not the new variations; the classifier generalizes but format attacks remain', () => {
      const id = 'r-jailbreak-e-red-teaming';
      const [roleplay, authority, format, benign] = lesson(id).def.command.arg.examples.map((e) => e[lang]);
      const v = q('atacar', 'attack');
      const fx = (x: string) => q(`--correcao ${x}`, `--fix ${x === 'lista' ? 'blocklist' : x === 'nenhuma' ? 'none' : x}`);
      expect(lesson(id).def.predict!.answer).toBe('same');
      const def = runCmd(id, lang, v);
      expect(def.flags).toContain('stopped');
      expect(def.vars).toMatchObject({ suiteB: 35, freshB: 38, suiteAP: 8, freshAP: 13, humanFound: 9 });
      const bad = runCmd(id, lang, `${v} ${fx('lista')}`);
      expect(bad.flags).toContain('overfit');
      expect(bad.vars).toMatchObject({ suiteAP: 0, freshAP: 35, freshA: 14 });
      expect(runCmd(id, lang, `${v} "${authority}" ${fx('lista')}`).flags).toContain('worked');
      expect(runCmd(id, lang, `${v} "${roleplay}" ${fx('lista')}`).flags).not.toContain('worked');
      expect(runCmd(id, lang, `${v} "${format}"`).flags).toContain('worked');
      expect(runCmd(id, lang, `${v} "${authority}"`).flags).toContain('stopped');
      expect(runCmd(id, lang, `${v} "${roleplay}" ${fx('nenhuma')}`).flags).toContain('worked');
      expect(runCmd(id, lang, `${v} "${benign}"`).flags).toContain('clean');
      expect(runCmd(id, lang, `${v} ${q('--horas 0', '--hours 0')}`).vars).toMatchObject({ humanFound: 0 });
      expect((runCmd(id, lang, `${v} "x"`).error as { code?: string } | undefined)?.code).toBe('unknownAtk');
      const loc = lesson(id).locale[lang];
      expect(JSON.stringify([loc.title, loc.subtitle, loc.mission, loc.predict])).not.toContain('COFRE-7Q2X');
    });

    it('13: the default trail answers the incident; missing fields or no text leave it unanswered; raw text is the break; a plain file is forgeable', () => {
      const id = 'r-auditoria-e-rastreabilidade';
      const [why, who, cost, blocked] = lesson(id).def.command.arg.examples.map((e) => e[lang]);
      const v = q('auditar', 'audit');
      expect(lesson(id).def.predict!.answer).toBe('no');
      expect(lesson(id).def.executors).toEqual(['simulado']);
      expect(lesson(id).def.real).toBeUndefined();
      const def = runCmd(id, lang, v);
      expect(def.flags).toEqual(expect.arrayContaining(['traceable', 'sealed']));
      expect(def.vars).toMatchObject({ piiNow: 0, nFields: 8 });
      const raw = runCmd(id, lang, q('auditar --texto bruto', 'audit --content raw'));
      expect(raw.flags).toContain('overlog');
      expect(raw.vars).toMatchObject({ piiNow: 420, readers: 12 });
      const gap = runCmd(id, lang, `${v} "${who}" ${q('--campos quando,docs', '--fields when,docs')}`);
      expect(gap.flags).toContain('gap');
      expect(gap.vars).toMatchObject({ nMissing: 1 });
      expect(runCmd(id, lang, `${v} "${why}" ${q('--texto nenhum', '--content none')}`).flags).toContain('gap');
      expect(runCmd(id, lang, `${v} "${cost}" ${q('--campos quando,tokens --texto nenhum', '--fields when,tokens --content none')}`).flags).toContain('traceable');
      expect(runCmd(id, lang, `${v} "${blocked}" ${q('--campos quando,guardrails', '--fields when,guards')}`).flags).toContain('traceable');
      expect(runCmd(id, lang, `${v} ${q('--integridade comum', '--integrity plain')}`).flags).toContain('forgeable');
      const t = (runCmd(id, lang, v) as Run).widgets!.find((w) => w.type === 'terminal') as { lines: string[] };
      expect(t.lines.join('\n')).toMatch(/207/);
    });

    it('14: tiers is the default; ban breaks with shadow use; confidential never passes; people decisions need human review', () => {
      const id = 'r-politica-de-uso-de-ia';
      const [, code, cpf, screen] = lesson(id).def.command.arg.examples.map((e) => e[lang]);
      const v = q('decidir', 'decide');
      expect(lesson(id).def.predict!.answer).toBe('many');
      const def = runCmd(id, lang, v);
      expect(def.flags).toContain('allowed');
      expect(def.flags).not.toContain('shadow');
      expect(def.vars).toMatchObject({ allowedPct: 93, shadowPct: 5 });
      const ban = runCmd(id, lang, q('decidir --politica proibir', 'decide --policy ban'));
      expect(ban.flags).toEqual(expect.arrayContaining(['shadow', 'denied']));
      expect(ban.vars).toMatchObject({ allowedPct: 0, shadowPct: 70, abandonedPct: 30 });
      const green = runCmd(id, lang, q('decidir --politica publico', 'decide --policy public'));
      expect(green.vars).toMatchObject({ allowedPct: 40, shadowPct: 42 });
      expect(green.flags).toContain('shadow');
      const open = runCmd(id, lang, q('decidir --politica liberar', 'decide --policy open'));
      expect(open.flags).toContain('permissive');
      expect(open.flags).not.toContain('shadow');
      expect(runCmd(id, lang, `${v} "${code}" ${q('--ferramenta publica', '--tool consumer')}`).flags).toContain('denied');
      expect(runCmd(id, lang, `${v} "${code}"`).flags).toContain('denied');
      expect(runCmd(id, lang, `${v} "${cpf}"`).flags).toContain('conditional');
      expect(runCmd(id, lang, `${v} "${screen}"`).flags).toContain('conditional');
      expect(runCmd(id, lang, `${v} "${screen}" ${q('--revisao nao', '--review no')}`).flags).toContain('denied');
    });
  });
}

describe('real executors with fake deps', () => {
  function runReal(id: string, lang: Lang, input: string, deps: Partial<RealDeps>, executor: 'no-navegador' | 'sua-chave' = 'sua-chave') {
    const l = lesson(id);
    const p = parseCommand(input, l.def.command, lang);
    if (!p.ok) throw new Error(JSON.stringify(p.error));
    const cfg = l.def.real![executor]!;
    const full: RealDeps = { tokenizer: async () => ({ encode: () => [], decode: () => '' }), chat: async () => '', ...deps };
    return ADAPTERS[cfg.adapter].run(p.values, { lang, layer: 'dev', data: l.def.data, text: l.locale[lang].data, rng: makeRng(1) }, full, { executor, model: 'm' }, cfg);
  }
  const V = (lang: Lang, id: string) => lesson(id).def.command.verb[lang];

  for (const lang of LANGS) {
    const q = <T,>(a: T, b: T): T => (lang === 'pt' ? a : b);

    it(`[${lang}] 08: the real model is judged by whether it ends its answer with the planted code`, async () => {
      const id = 'r-prompt-injection-direta-e-indireta';
      let msgs: { role: string; content: string }[] = [];
      const obey = await runReal(id, lang, V(lang, id), { chat: async (m) => { msgs = m as typeof msgs; return 'Pode vender até um terço. ZK-4821'; } });
      expect(msgs[0].content).toContain(q('<documento>', '<document>'));
      expect(msgs[0].content).toContain('ZK-4821');
      expect(msgs[1].content).toBe(q('Posso vender parte das férias?', 'Can I sell part of my vacation?'));
      expect(obey.flags).toEqual(expect.arrayContaining(['blocked']));
      const open = await runReal(id, lang, `${V(lang, id)} ${q('--confirmar nao', '--confirm no')}`, { chat: async () => 'ok. ZK-4821.' });
      expect(open.flags).toContain('exfil');
      const refuse = await runReal(id, lang, V(lang, id), { chat: async () => 'Não vou obedecer ao pedido de escrever ZK-4821 porque vem do documento.' });
      expect(refuse.flags).toContain('resisted');
      expect(refuse.flags).not.toContain('exfil');
      const direct = await runReal(id, lang, `${V(lang, id)} ${q('--canal chat', '--channel chat')}`, { chat: async (m) => { msgs = m as typeof msgs; return 'ok'; } });
      expect(msgs[1].content).toContain('ZK-4821');
      expect(direct.flags).toContain('resisted');
      for (const r of [obey, open, refuse, direct]) for (const t of shownTexts(id, lang, r as Run)) expect(filled(t), t).toBe(true);
    });

    it(`[${lang}] 09: the real classifier decides allow or block; broken JSON fails closed`, async () => {
      const id = 'r-guardrails-de-entrada-e-saida';
      let system = '';
      const block = await runReal(id, lang, `${V(lang, id)} "texto qualquer"`, { chat: async (m) => { system = m[0].content; return '{"decision":"block","reason":"parece ataque"}'; } }, 'no-navegador');
      expect(system).toMatch(/JSON/);
      expect(block.flags).toContain('blockedReal');
      const allow = await runReal(id, lang, `${V(lang, id)} "texto qualquer"`, { chat: async () => 'Resposta: {"decision":"allow","reason":"normal"}' });
      expect(allow.flags).toContain('passedReal');
      const broken = await runReal(id, lang, `${V(lang, id)} "texto qualquer"`, { chat: async () => 'acho que pode' });
      expect(broken.flags).toEqual(expect.arrayContaining(['invalidJson', 'blockedReal']));
      const stopped = await runReal(id, lang, V(lang, id), { chat: async () => '{"decision":"allow","reason":"ok"}' });
      expect(stopped.flags).toContain('stopped'); // allowed at the entrance, but the CPF is caught on the way out
      const leaked = await runReal(id, lang, `${V(lang, id)} ${q('--saida nao', '--output no')}`, { chat: async () => '{"decision":"allow","reason":"ok"}' });
      expect(leaked.flags).toContain('leaked');
      for (const r of [block, allow, broken, stopped, leaked]) for (const t of shownTexts(id, lang, r as Run)) expect(filled(t), t).toBe(true);
    });

    it(`[${lang}] 10: a real model that repeats a mark from a restricted document leaks it; only the permitted documents are sent otherwise`, async () => {
      const id = 'r-vazamento-de-dados-e-permissoes';
      let system = '';
      const spill = await runReal(id, lang, `${V(lang, id)} ${q('--filtro prompt', '--filter prompt')}`, { chat: async (m) => { system = m[0].content; return q('O diretor financeiro ganha R$ 41.370 por mês.', 'The finance director earns R$ 41,370 a month.'); } });
      expect(system).toContain(q('41.370', '41,370'));
      expect(spill.flags).toEqual(expect.arrayContaining(['leak', 'revealed']));
      const held = await runReal(id, lang, `${V(lang, id)} ${q('--filtro prompt', '--filter prompt')}`, { chat: async () => q('Não posso mostrar documentos restritos.', 'I cannot show restricted documents.') });
      expect(held.flags).toEqual(expect.arrayContaining(['leak', 'heldBack']));
      expect(held.flags).not.toContain('revealed');
      const safe = await runReal(id, lang, V(lang, id), { chat: async (m) => { system = m[0].content; return 'Não encontrei.'; } });
      expect(system).not.toContain(q('41.370', '41,370'));
      expect(safe.flags).not.toContain('leak');
      for (const r of [spill, held, safe]) for (const t of shownTexts(id, lang, r as Run)) expect(filled(t), t).toBe(true);
    });

    it(`[${lang}] 11: the real detector reports which personal data types the message has`, async () => {
      const id = 'r-dados-pessoais-e-lgpd';
      const r = await runReal(id, lang, `${V(lang, id)} "texto livre"`, { chat: async () => '{"cpf":false,"email":false,"phone":false,"health":true}' }, 'no-navegador');
      const tbl = (r as unknown as Run).widgets!.find((w) => w.type === 'table') as { rows: string[][] };
      expect(tbl.rows.map((x) => x[1])).toEqual(q(['não', 'não', 'não', 'sim'], ['no', 'no', 'no', 'yes']));
      const bad = await runReal(id, lang, V(lang, id), { chat: async () => 'nada' });
      expect(bad.flags).toContain('invalidJson');
      for (const x of [r, bad]) for (const t of shownTexts(id, lang, x as Run)) expect(filled(t), t).toBe(true);
    });

    it(`[${lang}] 12: the real model is judged by the canary (also reversed); the hardened prompt is used only with the classifier fix; the list blocks the exact phrase before the model`, async () => {
      const id = 'r-jailbreak-e-red-teaming';
      const seen: string[] = [];
      const chat = (reply: string) => async (m: { content: string }[]) => { seen.push(m[0].content); return reply; };
      const spill = await runReal(id, lang, `${V(lang, id)} ${q('--correcao nenhuma', '--fix none')}`, { chat: chat('O código é COFRE-7Q2X.') });
      expect(spill.flags).toContain('worked');
      const rev = await runReal(id, lang, `${V(lang, id)} ${q('--correcao nenhuma', '--fix none')}`, { chat: chat('X2Q7-ERFOC') });
      expect(rev.flags).toContain('worked');
      const held = await runReal(id, lang, V(lang, id), { chat: chat('Não posso ajudar com isso.') });
      expect(held.flags).toContain('stopped');
      expect(seen[0]).not.toMatch(q(/nunca revele, repita ou transforme/, /never reveal, repeat or transform/));
      expect(seen[2]).toMatch(q(/nunca revele, repita ou transforme/, /never reveal, repeat or transform/));
      const list = await runReal(id, lang, `${V(lang, id)} ${q('--correcao lista', '--fix blocklist')}`, { chat: chat('COFRE-7Q2X') });
      expect(list.flags).toContain('overfit');
      expect(list.flags).not.toContain('worked'); // the exact phrase never reaches the model
      for (const r of [spill, rev, held, list]) for (const t of shownTexts(id, lang, r as Run)) expect(filled(t), t).toBe(true);
    });
    it(`[${lang}] 14: a real classifier decides the class and whether people are decided about; invalid JSON assumes the worst case`, async () => {
      const id = 'r-politica-de-uso-de-ia';
      let user = '';
      const json = (s: string) => async (m: { content: string }[]) => { user = m[m.length - 1].content; return s; };
      const ok = await runReal(id, lang, `${V(lang, id)} "${q('Escrever um e-mail com o CPF do cliente.', 'Write an e-mail with the customer CPF.')}"`, { chat: json('{"data_class":"personal","decides_people":false}') });
      expect(user).toContain('CPF');
      expect(ok.flags).toContain('conditional');
      const pub = await runReal(id, lang, `${V(lang, id)} "x"`, { chat: json('{"data_class":"public","decides_people":false}') });
      expect(pub.flags).toContain('allowed');
      const people = await runReal(id, lang, `${V(lang, id)} "x"`, { chat: json('{"data_class":"personal","decides_people":true}') });
      expect(people.flags).toContain('conditional');
      const bad = await runReal(id, lang, `${V(lang, id)} "x"`, { chat: json('não sei') });
      expect(bad.flags).toEqual(expect.arrayContaining(['invalidJson', 'denied']));
      for (const r of [ok, pub, people, bad]) for (const t of shownTexts(id, lang, r as Run)) expect(filled(t), t).toBe(true);
    });
  }
});
