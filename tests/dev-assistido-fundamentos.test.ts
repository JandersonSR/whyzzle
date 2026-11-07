import { describe, expect, it } from 'vitest';
import { defaultCommand } from '../src/engine/command';
import { LANGS } from '../src/engine/schema';
import { lessons, runCmd } from './helpers';

/**
 * Dev assistido por IA · Fundamentos (F1 · IA no editor), simulated mode:
 * the default command runs without raising the break flag, the cheat (hint 3)
 * raises it, the guess each lesson calls right is what the sim shows, and the
 * mission starts broken and passes once everything is fixed.
 */

const track = lessons.filter((l) => l.topic === 'dev-assistido-por-ia' && l.track === 'fundamentos');
const def = (id: string, lang: 'pt' | 'en') => runCmd(id, lang, defaultCommand(track.find((l) => l.def.id === id)!.def.command, lang));

for (const lang of LANGS) {
  const pt = lang === 'pt';
  const q = (p: string, e: string) => (pt ? p : e);

  describe(`[${lang}] Dev assistido por IA · Fundamentos`, () => {
    it('has 6 steps and a final mission, in order', () => {
      expect(track.map((l) => l.def.order)).toEqual([1, 2, 3, 4, 5, 6, 7]);
      expect(track.filter((l) => l.def.kind === 'step').length).toBe(6);
      expect(track[6].def.kind).toBe('mission');
    });

    for (const l of track.filter((x) => x.def.kind === 'step')) {
      it(`${l.def.id}: default runs without breaking, cheat breaks it`, () => {
        const r = runCmd(l.def.id, lang, defaultCommand(l.def.command, lang));
        expect(r.error, 'default command must not error').toBeUndefined();
        expect(r.flags, 'default must not raise the break flag').not.toContain(l.def.break.flag);
        const cheat = l.locale[lang].hints!.cmd[2];
        const c = runCmd(l.def.id, lang, cheat);
        expect(c.error).toBeUndefined();
        expect(c.flags, cheat).toContain(l.def.break.flag);
      });
    }

    it('1 · only the agent fits the 12-file rename; autocomplete leaves files behind', () => {
      const r = def('dai-autocompletar-chat-agente', lang);
      expect(r.flags).toContain('fit');
      expect(r.vars?.left).toBe(0);
      const rename = q('Renomear preco para valor nos 12 arquivos e rodar os testes', 'Rename preco to valor across the 12 files and run the tests');
      expect(runCmd('dai-autocompletar-chat-agente', lang, `${q('usar', 'use')} "${rename}" --${q('ferramenta', 'tool')} chat`).flags).toContain('missed');
      const line = q('Completar a linha que calcula o preço com desconto', 'Finish the line that computes the discounted price');
      expect(runCmd('dai-autocompletar-chat-agente', lang, `${q('usar', 'use')} "${line}" --${q('ferramenta', 'tool')} ${q('agente', 'agent')}`).flags).toContain('overkill');
      expect(runCmd('dai-autocompletar-chat-agente', lang, `${q('usar', 'use')} "${line}" --${q('ferramenta', 'tool')} ${q('autocompletar', 'autocomplete')}`).flags).toContain('fit');
    });

    it('2 · with only the order file the AI guesses; rules + discount get it right', () => {
      expect(def('dai-contexto', lang).flags).toContain('guessed');
      const ask = q('perguntar --arquivos', 'ask --files');
      expect(runCmd('dai-contexto', lang, `${ask} ${q('desconto', 'discount')}`).flags).toContain('partial');
      expect(runCmd('dai-contexto', lang, `${ask} ${q('regras,desconto', 'rules,discount')}`).flags).toContain('right');
    });

    it('3 · the vague request passes none; the full spec passes all 5', () => {
      const r = def('dai-pedir-com-especificacao', lang);
      expect(r.vars?.passed).toBe(0);
      const full = q('pedir --entradas sim --regras sim --exemplos sim --limites sim --restricoes sim', 'request --inputs yes --rules yes --examples yes --edges yes --constraints yes');
      const f = runCmd('dai-pedir-com-especificacao', lang, full);
      expect(f.vars?.passed).toBe(5);
      expect(f.flags).toContain('allPass');
      expect(f.flags).not.toContain('addedDep');
    });

    it('4 · running the tests alone finds no problem; all checks find all 4', () => {
      expect(def('dai-revisar-o-que-a-ia-escreveu', lang).vars?.caught).toBe(0);
      const all = runCmd('dai-revisar-o-que-a-ia-escreveu', lang, q('revisar --checar rodar,ler,pacotes,dados,bordas --aprovar sim', 'review --checks run,read,deps,data,edges --approve yes'));
      expect(all.vars?.caught).toBe(4);
      expect(all.flags).toContain('merged');
      expect(all.flags).not.toContain('shipped');
    });

    it('5 · letting the AI do the exercise kills learning; tutor mode is best', () => {
      const r = def('dai-quando-nao-usar', lang);
      expect(r.flags).toContain('noLearning');
      expect(Number(r.vars?.learnPct)).toBeLessThan(30);
      const t = runCmd('dai-quando-nao-usar', lang, q('decidir --modo tutor', 'decide --mode tutor'));
      expect(t.flags).toContain('bestPick');
      expect(Number(t.vars?.learnPct)).toBeGreaterThan(50);
    });

    it('6 · the sheet names whoever delivers; all checks on is honest', () => {
      const r = def('dai-etica-e-autoria', lang) as unknown as { flags: string[]; widgets: { type: string; rows?: string[][] }[] };
      expect(r.flags).toContain('honest');
      const sheet = r.widgets.find((w) => w.type === 'table')!;
      expect(sheet.rows![0][1]).toBe('@you');
      const school = q('Trabalho da feira de ciências: app de quiz', 'Science fair project: quiz app');
      const s = runCmd('dai-etica-e-autoria', lang, `${q('entregar', 'deliver')} "${school}" --${q('licenca', 'license')} ${q('nao', 'no')}`);
      expect(s.flags).toContain('noCredit');
      expect(s.flags).not.toContain('licenseRisk');
    });

    it('7 · the mission starts broken and passes once every criterion is fixed', () => {
      const id = 'dai-missao-bug-com-teste';
      const start = def(id, lang);
      expect(start.error).toBeUndefined();
      expect(start.flags).not.toContain('fixed');
      expect(start.vars?.done).toBe(0);
      const good = pt
        ? 'consertar "3 pães de R$ 0,10 devem dar R$ 0,30; calcule em centavos" --teste-primeiro sim --contexto preco,teste --revisar sim --rodar todos'
        : 'fix "3 rolls at R$ 0.10 must total R$ 0.30; compute in cents" --test-first yes --context price,test --review yes --run suite';
      const r = runCmd(id, lang, good);
      expect(r.flags).toContain('fixed');
      expect(r.vars?.done).toBe(5);
      // Right code but no proof: the receipt is fixed, the mission isn't.
      const noProof = runCmd(id, lang, pt ? 'consertar "deve dar R$ 0,30" --contexto preco,teste' : 'fix "must total R$ 0.30" --context price,test');
      expect(noProof.flags).toContain('receiptFixed');
      expect(noProof.flags).not.toContain('fixed');
      // A bare trailing keyword ("make it 0.3") still counts as stating the expected result.
      const endKw = runCmd(id, lang, pt ? 'consertar "faça dar 0,3" --teste-primeiro sim --contexto preco,teste --revisar sim --rodar todos' : 'fix "make it 0.3" --test-first yes --context price,test --review yes --run suite');
      expect(endKw.flags).toContain('fixed');
      expect(endKw.vars?.done).toBe(5);
    });
  });
}
