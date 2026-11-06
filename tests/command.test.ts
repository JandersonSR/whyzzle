import { describe, expect, it } from 'vitest';
import { buildCommand, parseCommand, translateCommand } from '../src/engine/command';
import { lesson } from './helpers';

const temp = lesson('temperatura').def.command;
const agent = lesson('ferramentas-e-agentes').def.command;

describe('command parser', () => {
  it('reads verb, quoted text and flags in either language', () => {
    const r = parseCommand('completar "O gato subiu no" --temp 0,7 --vezes 10', temp, 'pt');
    expect(r).toEqual({ ok: true, values: { text: 'O gato subiu no', temp: 0.7, times: 10 } });
    expect(parseCommand('complete "x" --temp=1 --times=3', temp, 'pt')).toMatchObject({ ok: true, values: { temp: 1, times: 3 } });
  });

  it('accepts curly quotes pasted from phones and docs', () => {
    expect(parseCommand('completar “O gato” --temp 0', temp, 'pt')).toMatchObject({ ok: true, values: { text: 'O gato' } });
  });

  it('explains common mistakes with structured errors', () => {
    expect(parseCommand('', temp, 'pt')).toMatchObject({ ok: false, error: { code: 'empty' } });
    expect(parseCommand('rodar "x" --temp 0', temp, 'pt')).toMatchObject({ error: { code: 'unknownCommand', suggestion: 'completar' } });
    expect(parseCommand('completar "x"', temp, 'pt')).toMatchObject({ error: { code: 'missingFlag', flag: 'temp' } });
    expect(parseCommand('completar "x" -temp 0', temp, 'pt')).toMatchObject({ error: { code: 'oneDash', suggestion: '--temp' } });
    expect(parseCommand('completar "x" --tmp 0', temp, 'pt')).toMatchObject({ error: { code: 'unknownFlag', suggestion: '--temp' } });
    expect(parseCommand('completar "x" --temp quente', temp, 'pt')).toMatchObject({ error: { code: 'notNumber', flag: 'temp', value: 'quente' } });
    expect(parseCommand('completar "x" --temp -1', temp, 'pt')).toMatchObject({ error: { code: 'belowMin', flag: 'temp' } });
    expect(parseCommand('completar "x" --temp 0 --vezes 50', temp, 'pt')).toMatchObject({ error: { code: 'aboveMax', flag: 'times' } });
    expect(parseCommand('completar "x" --temp 0 --vezes 2.5', temp, 'pt')).toMatchObject({ error: { code: 'notInteger', flag: 'times' } });
  });

  it('parses lists, "none" and accents', () => {
    expect(parseCommand('agente "x" --ferramentas relógio,busca', agent, 'pt')).toMatchObject({ values: { tools: ['clock', 'search'] } });
    expect(parseCommand('agente "x" --ferramentas nenhuma', agent, 'pt')).toMatchObject({ values: { tools: [] } });
    expect(parseCommand('agente "x" --ferramentas martelo', agent, 'pt')).toMatchObject({ error: { code: 'notInEnum', value: 'martelo' } });
  });

  it('round-trips through buildCommand and translates between languages', () => {
    const values = { text: 'O gato subiu no', temp: 1.5, times: 10 };
    const line = buildCommand(temp, 'pt', values);
    expect(line).toBe('completar "O gato subiu no" --temp 1.5 --vezes 10');
    expect(parseCommand(line, temp, 'pt')).toEqual({ ok: true, values });
    expect(translateCommand(line, temp, 'pt', 'en')).toBe('complete "The cat climbed onto the" --temp 1.5 --times 10');
  });
});
