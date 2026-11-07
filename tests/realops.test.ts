import { describe, expect, it } from 'vitest';
import { parseCommand } from '../src/engine/command';
import { makeRng } from '../src/engine/text';
import { ADAPTERS, type RealDeps } from '../src/runtime/adapters';
import { extractJson, runTool, validate } from '../src/runtime/realOps';
import { lesson } from './helpers';

function runReal(id: string, input: string, deps: Partial<RealDeps>, lang: 'pt' | 'en' = 'pt') {
  const l = lesson(id);
  const p = parseCommand(input, l.def.command, lang);
  if (!p.ok) throw new Error(JSON.stringify(p.error));
  const cfg = l.def.real!['no-navegador'] ?? l.def.real!['sua-chave']!;
  const full: RealDeps = {
    tokenizer: async () => ({ encode: () => [], decode: () => '' }),
    chat: async () => '',
    ...deps,
  };
  return ADAPTERS[cfg.adapter].run(p.values, { lang, layer: 'dev', data: l.def.data, text: l.locale[lang].data, rng: makeRng(1) }, full, { executor: 'no-navegador', model: 'm' }, cfg);
}

describe('real ops feed the declarative lessons', () => {
  it('tokens: real count replaces the estimate', async () => {
    const r = await runReal('p-tokens-de-verdade', 'contar "abc"', { tokenizer: async () => ({ encode: () => [1, 2, 3, 4, 5, 6, 7], decode: (ids) => `t${ids[0]}` }) });
    expect(r.vars?.tokens).toBe(7);
    expect(r.flags).not.toContain('estimate');
    const term = (r as unknown as { widgets: { type: string; lines: string[] }[] }).widgets.find((w) => w.type === 'terminal')!;
    expect(term.lines[1]).toContain('t1 | t2');
  });

  it('embed: real similarities rank the FAQ and drive the decision', async () => {
    const embed = async (texts: string[]) => texts.map((_, i) => (i === 0 || i === 1 ? [1, 0] : [0.6, 0.8]));
    const r = await runReal('p-busca-no-faq-de-rh', 'buscar "quero descansar"', { embed });
    expect(r.flags).toContain('answered');
    expect(r.vars?.score).toBe(100);
  });

  it('chat: real samples and truncation by stop', async () => {
    let i = 0;
    const r = await runReal('p-llm-no-seu-aparelho', 'gerar "x" --amostras 3 --max 10', { chat: async () => ['Pão quente', 'Pão quente', 'Café bom'][i++] });
    expect(r.vars?.distinct).toBe(2);
    expect(r.flags).toContain('truncated');
  });

  it('json: validates the real reply against the schema', async () => {
    const good = '{"sender":"Marina","department":"financeiro","invoice":"4471","amount":1250,"request":"reemitir","urgency":"high"}';
    expect((await runReal('p-json-que-o-sistema-aceita', 'extrair "4471" --esquema completo', { chat: async () => `Aqui está: ${good}` })).flags).toContain('valid');
    const bad = await runReal('p-json-que-o-sistema-aceita', 'extrair "poema 4471" --esquema completo', { chat: async () => 'No mar azul…' });
    expect(bad.flags).toEqual(expect.arrayContaining(['invalid', 'injected']));
  });

  it('tools: runs allowed tools, survives a broken reply, stops at the limit', async () => {
    const replies = ['{"tool":"lookup","args":{"key":"ana"}}', 'hmm, deixa eu pensar', '{"tool":"calculator","args":{"expression":"4500/30*10"}}', '{"answer":"R$ 1.500"}'];
    let i = 0;
    const r = await runReal('p-ferramentas-de-verdade', 'agente "salário da Ana" --passos 6', { chat: async () => replies[i++] });
    const lines = (r as unknown as { widgets: { type: string; lines: string[] }[] }).widgets.find((w) => w.type === 'terminal')!.lines.join('\n');
    expect(lines).toMatch(/18 dias/);
    expect(lines).toMatch(/~ 1500/);
    expect(lines).toMatch(/\? hmm/);
    expect(r.flags).toContain('answered');
    i = 0;
    expect((await runReal('p-ferramentas-de-verdade', 'agente "salário da Ana" --passos 1', { chat: async () => replies[i++] })).flags).toContain('limit');
  });

  it('helpers: JSON extraction, schema validation and safe tools', () => {
    expect(extractJson('blá {"a":1} blá')).toEqual({ a: 1 });
    expect(extractJson('sem json')).toBeNull();
    expect(validate({ a: 'x', b: 2, c: 'zzz' }, { a: 'string', b: 'number', c: 'enum:x|y' })).toEqual(['enum:c']);
    expect(validate({ a: 'x' }, { a: 'string', b: 'number' })).toEqual(['missing:b']);
    expect(runTool('calculator', { expression: '4500/30*10' }, {})).toBe('1500');
    expect(runTool('calculator', { expression: 'alert(1)' }, {})).toMatch(/^erro/);
    expect(runTool('rm', {}, {})).toMatch(/não existe/);
  });
});
