import { describe, expect, it } from 'vitest';
import { defaultCommand, defaultValues, type Values } from '../src/engine/command';
import { LANGS } from '../src/engine/schema';
import { lesson, lessons, runCmd, runValues } from './helpers';

/**
 * Contêineres e Kubernetes · Fundamentos (F1 · Do programa ao contêiner), simulated mode:
 * the default command runs without raising the break flag, the hint-3 cheat raises it,
 * the guess each lesson calls right is what the sim shows, every tryNext command runs,
 * and the mission starts broken, partial fixes fail and the full fix passes.
 */

const track = lessons.filter((l) => l.topic === 'conteineres-e-kubernetes' && l.track === 'fundamentos');
const steps = track.filter((l) => l.def.kind === 'step');
const dflt = (id: string, lang: (typeof LANGS)[number]) => runCmd(id, lang, defaultCommand(lesson(id).def.command, lang));

/** Every combination of the lesson's options (ints at min, default and max). */
function combos(id: string, lang: (typeof LANGS)[number]): Values[] {
  const def = lesson(id).def.command;
  let out: Values[] = [defaultValues(def, lang)];
  for (const f of def.flags) {
    const vals: Values[string][] =
      f.type === 'enum' ? f.options!.map((o) => o.id) : f.type === 'bool' ? [true, false] : f.type === 'int' ? [f.min!, f.default as number, f.max!] : [];
    if (!vals.length) continue;
    out = out.flatMap((v) => vals.map((x) => ({ ...v, [f.name]: x })));
  }
  return out;
}

/** "@key" strings left in resolved widgets (they must exist in the lesson's scene texts). */
function sceneKeys(v: unknown, out = new Set<string>()): Set<string> {
  if (typeof v === 'string' && /^@[\w.]+$/.test(v)) out.add(v.slice(1));
  else if (Array.isArray(v)) v.forEach((x) => sceneKeys(x, out));
  else if (v && typeof v === 'object') Object.values(v).forEach((x) => sceneKeys(x, out));
  return out;
}

describe('conteineres-e-kubernetes / fundamentos', () => {
  it('ships 6 steps and the final mission, in order, all declarative', () => {
    expect(track.map((l) => l.def.order)).toEqual([1, 2, 3, 4, 5, 6, 7]);
    expect(steps.length).toBe(6);
    expect(track[6].def.kind).toBe('mission');
    for (const l of track) {
      expect(l.def.id.startsWith('k8s-'), l.def.id).toBe(true);
      expect(l.def.model).toBe('declarative');
      expect(l.def.scene).toBe('widgets');
      expect(l.def.executors).toEqual(['simulado']);
    }
  });

  it('no computed value shadows a result flag or a command option', () => {
    for (const l of track) {
      const sim = l.def.data.sim as { compute: Record<string, string>; cases: { flags?: string[] }[] };
      const flags = new Set(sim.cases.flatMap((c) => c.flags ?? []));
      const options = l.def.command.flags.map((f) => f.name);
      for (const name of Object.keys(sim.compute)) {
        expect(flags.has(name), `${l.def.id}: compute "${name}" is also a result flag`).toBe(false);
        expect(options.includes(name), `${l.def.id}: compute "${name}" overwrites a command option`).toBe(false);
      }
    }
  });

  for (const lang of LANGS) {
    it(`[${lang}] every option combination runs and only uses scene texts that exist`, () => {
      for (const l of track) {
        const scene = l.locale[lang].scene;
        for (const v of combos(l.def.id, lang)) {
          const r = runValues(l.def.id, lang, v) as unknown as { error?: unknown; widgets: unknown[] };
          expect(r.error, `${l.def.id} ${JSON.stringify(v)}`).toBeUndefined();
          expect(JSON.stringify(r.widgets)).not.toMatch(/"=(?!>)/);
          for (const k of sceneKeys(r.widgets)) expect(typeof scene[k], `${l.def.id}: scene.${k}`).toBe('string');
        }
      }
    });
  }
});

for (const lang of LANGS) {
  const pt = lang === 'pt';
  const q = (p: string, e: string) => (pt ? p : e);

  describe(`[${lang}] Contêineres e Kubernetes · Fundamentos`, () => {
    for (const l of steps) {
      it(`${l.def.id}: default runs calm, cheat breaks it`, () => {
        const d = runCmd(l.def.id, lang, defaultCommand(l.def.command, lang));
        expect(d.error, 'default command must not error').toBeUndefined();
        expect(d.flags, 'default must not raise the break flag').not.toContain(l.def.break.flag);
        const cheat = l.locale[lang].hints!.cmd[2];
        const c = runCmd(l.def.id, lang, cheat);
        expect(c.error).toBeUndefined();
        expect(c.flags, cheat).toContain(l.def.break.flag);
      });
    }

    it('1 · containers share one kernel; plain processes clash; VMs run out of room', () => {
      const id = 'k8s-processo-conteiner-vm';
      const d = dflt(id, lang);
      expect(d.vars?.kernels).toBe(1);
      expect(d.vars?.brokenApps).toBe(0);
      const vm = runCmd(id, lang, q('hospedar --isolamento vm', 'host --isolation vm'));
      expect(vm.vars?.kernels).toBe(3);
      const p = runCmd(id, lang, q('hospedar --isolamento processo', 'host --isolation process'));
      expect(p.vars?.brokenApps).toBe(1);
      // tryNext: 20 VMs on 16 GB → only 11 fit
      const full = runCmd(id, lang, q('hospedar --isolamento vm --apps 20', 'host --isolation vm --apps 20'));
      expect(full.error).toBeUndefined();
      expect(full.flags).toContain('noRoom');
      expect(full.vars?.maxApps).toBe(11);
    });

    it('2 · a code-only change pulls 2 MB; a base change pulls everything; rm in a new layer keeps the bytes', () => {
      const id = 'k8s-imagem-e-camadas';
      const d = dflt(id, lang);
      expect(d.vars?.pullMB).toBe(2);
      expect(d.vars?.imageMB).toBe(182);
      const base = runCmd(id, lang, q('puxar --mudou base', 'pull --changed base'));
      expect(base.error).toBeUndefined();
      expect(base.flags).toContain('fullPull');
      expect(base.vars?.pullMB).toBe(182);
      expect(runCmd(id, lang, q('puxar --limpeza run-separado', 'pull --cleanup separate-run')).vars?.imageMB).toBe(362);
    });

    it('3 · deps first: a code change rebuilds in ~2 s; copy-all reruns npm ci', () => {
      const id = 'k8s-dockerfile';
      const d = dflt(id, lang);
      expect(d.vars?.reran).toBe(1);
      expect(Number(d.vars?.secs)).toBeLessThan(5);
      expect(Number(runCmd(id, lang, q('construir --ordem copia-tudo', 'build --order copy-all')).vars?.secs)).toBeGreaterThan(80);
      // tryNext: changing deps legitimately reruns npm ci (not the break); no .dockerignore swells the context
      const deps = runCmd(id, lang, q('construir --mudou dependencias', 'build --changed deps'));
      expect(deps.error).toBeUndefined();
      expect(deps.flags).not.toContain('cacheBusted');
      expect(Number(deps.vars?.secs)).toBeGreaterThan(80);
      const fat = runCmd(id, lang, q('construir --dockerignore nao', 'build --dockerignore no'));
      expect(fat.error).toBeUndefined();
      expect(fat.flags).toContain('fatContext');
      expect(fat.vars?.ctxMB).toBe(380);
    });

    it('4 · the 1.4 tag keeps both servers on 1.4; latest and an overwritten tag drift; a digest never does', () => {
      const id = 'k8s-registro';
      const d = dflt(id, lang);
      expect(d.vars?.b).toBe('1.4');
      expect(d.flags).not.toContain('drift');
      expect(runCmd(id, lang, q('implantar --referencia latest', 'deploy --ref latest')).vars?.b).toBe('1.5');
      const over = runCmd(id, lang, q('implantar --sobrescreveu sim', 'deploy --overwritten yes'));
      expect(over.error).toBeUndefined();
      expect(over.flags).toContain('drift');
      const pinned = runCmd(id, lang, q('implantar --referencia digest --sobrescreveu sim', 'deploy --ref digest --overwritten yes'));
      expect(pinned.error).toBeUndefined();
      expect(pinned.flags).not.toContain('drift');
      expect(pinned.flags).toContain('pinned');
    });

    it('5 · the orchestrator reschedules the lost replica; one server or the manual way needs a human', () => {
      const id = 'k8s-por-que-orquestrar';
      const d = dflt(id, lang);
      expect(d.flags).toContain('selfHealed');
      expect(d.vars?.autoN).toBe(1);
      expect(d.vars?.humansN).toBe(0);
      const one = runCmd(id, lang, q('operar --servidores 1', 'operate --servers 1'));
      expect(one.error).toBeUndefined();
      expect(one.flags).toContain('humanNeeded');
      const rel = runCmd(id, lang, q('operar --evento versao', 'operate --event release'));
      expect(rel.error).toBeUndefined();
      expect(rel.vars?.downMin).toBe(0);
    });

    it('6 · the scheduler places pods; stopping it leaves them Pending while old pods keep running', () => {
      const id = 'k8s-o-que-e-cluster';
      const d = dflt(id, lang);
      expect(d.flags).toContain('scheduled');
      expect(d.vars?.runningN).toBe(4);
      const s = runCmd(id, lang, q('escalar --parado scheduler', 'scale --stopped scheduler'));
      expect(s.vars?.pendingN).toBe(2);
      expect(s.vars?.runningN).toBe(2);
      // tryNext: kubelet down on one worker is worked around; controller-manager down creates nothing
      const k = runCmd(id, lang, q('escalar --parado kubelet', 'scale --stopped kubelet'));
      expect(k.error).toBeUndefined();
      expect(k.flags).toContain('nodeNotReady');
      expect(k.flags).not.toContain('stuck');
      const c = runCmd(id, lang, q('escalar --parado controller-manager', 'scale --stopped controller-manager'));
      expect(c.error).toBeUndefined();
      expect(c.flags).toContain('stuck');
      expect(c.vars?.pendingN).toBe(0);
    });

    it('mission: starts broken, partial fixes fail, the full fix passes (slim and distroless)', () => {
      const id = 'k8s-missao-empacotar-api';
      const flag = lesson(id).def.break.flag;
      const d = dflt(id, lang);
      expect(d.flags).not.toContain(flag);
      expect(d.vars?.okCount).toBe(0);
      const cmd = (base: string, ignore: boolean) =>
        q(
          `empacotar --base ${base} --ordem deps-primeiro --usuario nao-root --segredo execucao --dockerignore ${ignore ? 'sim' : 'nao'} --tag 1.0.0`,
          `package --base ${base} --order deps-first --user non-root --secret runtime --dockerignore ${ignore ? 'yes' : 'no'} --tag 1.0.0`,
        );
      // everything right but no .dockerignore: .env and node_modules ride along
      const noIgnore = runCmd(id, lang, cmd('node:24-slim', false));
      expect(noIgnore.flags).not.toContain(flag);
      expect(noIgnore.flags).toContain('secretLeak');
      expect(noIgnore.flags).toContain('fatImage');
      // pinned but full base: too big
      expect(runCmd(id, lang, cmd('node:24', true)).flags).not.toContain(flag);
      for (const base of ['node:24-slim', 'distroless']) {
        const fixed = runCmd(id, lang, cmd(base, true));
        expect(fixed.error).toBeUndefined();
        expect(fixed.flags, base).toContain(flag);
        expect(fixed.vars?.secretsN).toBe(0);
        expect(Number(fixed.vars?.imgMB)).toBeLessThanOrEqual(300);
      }
    });
  });
}
