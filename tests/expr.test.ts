import { describe, expect, it } from 'vitest';
import { check, evaluate, ExprError } from '../src/engine/expr';
import { makeRng } from '../src/engine/text';

const env = { n: 5, a: 0.99, modo: 'sincrono', list: [3, 1, 2], obj: { x: 7 } };
const ev = (s: string) => evaluate(s, env, makeRng(1));

describe('expression language', () => {
  it('follows arithmetic precedence and right-associative power', () => {
    expect(ev('1 + 2 * 3')).toBe(7);
    expect(ev('(1 + 2) * 3')).toBe(9);
    expect(ev('2 ** 3 ** 2')).toBe(512);
    expect(ev('-2 ** 2')).toBe(4);
    expect(ev('10 % 4')).toBe(2);
  });

  it('compares, combines and branches', () => {
    expect(ev("modo == 'sincrono' && n > 3")).toBe(true);
    expect(ev("modo != 'sincrono' || n >= 5")).toBe(true);
    expect(ev('!(n < 3) ? "sim" : "não"')).toBe('sim');
  });

  it('reads members, indexes, lists and functions', () => {
    expect(ev('obj.x + list[0] + list.length')).toBe(13);
    expect(ev('round(pow(a, n) * 100, 1)')).toBe(95.1);
    expect(ev('sum(list) + max(1, 9, 4) + len("abc")')).toBe(18);
    expect(ev('includes(list, 2) && !includes(list, 9)')).toBe(true);
    expect(ev('range(3, 1)')).toEqual([1, 2, 3]);
    expect(ev('concat([1], 2, [3, 4])')).toEqual([1, 2, 3, 4]);
    expect(ev("'pedido-' + n")).toBe('pedido-5');
  });

  it('is deterministic with a seeded rng', () => {
    expect(evaluate('rand()', {}, makeRng(3))).toBe(evaluate('rand()', {}, makeRng(3)));
  });

  it('refuses unknown names, unknown functions and prototype tricks', () => {
    expect(() => ev('nope + 1')).toThrow(ExprError);
    expect(() => ev('alert(1)')).toThrow(ExprError);
    expect(() => ev('constructor')).toThrow(ExprError);
    expect(ev('obj.constructor')).toBeUndefined();
    expect(ev('obj.__proto__')).toBeUndefined();
    expect(() => check('1 +')).toThrow(ExprError);
    expect(() => check("'aberta")).toThrow(ExprError);
  });
});
