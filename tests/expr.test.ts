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

  it('has text helpers for lessons', () => {
    expect(ev("words('o gato  subiu')")).toBe(3);
    expect(ev("nonascii('ação 🙂')")).toBe(3);
    expect(ev("overlap('Como peço férias?', 'pedir FERIAS como')")).toBeCloseTo(2 / 4);
    expect(ev("endsany('Pão quente.', ['.', '!'])")).toBe(true);
  });

  it('has list helpers for tables and samples', () => {
    expect(ev('argmax([0.2, 0.9, 0.5])')).toBe(1);
    expect(ev('order([0.2, 0.9, 0.5])')).toEqual([1, 2, 0]);
    expect(ev("zip(['a', 'b'], [1, 2])")).toEqual([['a', 1], ['b', 2]]);
    expect(ev('roundall(affine([0, 0.5], 0.7, 0.3), 2)')).toEqual([0.7, 0.85]);
    expect(ev("mark(3, 1, 'ok', 'neutral')")).toEqual(['neutral', 'ok', 'neutral']);
    expect(ev("truncwords(['um dois três quatro'], 2)")).toEqual(['um dois…']);
    expect(ev("len(unique(sample(['a','b','c'], 5, 1)))")).toBe(1);
  });

  it('has RAG helpers', () => {
    expect(ev("chunks('a b c d e f g', 3, 1)")).toEqual(['a b c', 'c d e', 'e f g']);
    expect(ev("chunks('a b c d', 10, 0)")).toEqual(['a b c d']);
    expect(ev("trimall(dropmatching(['Página 1 de 3', ' Férias ', 'CONFIDENCIAL', ''], ['página', 'confidencial']))")).toEqual(['Férias']);
    expect(evaluate('unhyphen(t)', { t: 'ante-\ncedência' })).toBe('antecedência');
    const s = evaluate("bm25('reembolso VR', docs)", { docs: ['VR é vale-refeição', 'reembolso de despesas', 'férias'] }) as number[];
    expect(s[2]).toBe(0);
    expect(Math.max(...s)).toBe(1);
    expect(ev('blend([1, 0], [0, 1], 0.25)')).toEqual([0.25, 0.75]);
    expect(evaluate("lookup(m, 'x', 0)", { m: { x: 2 } })).toBe(2);
    expect(ev("refs('Sim [1], e [3].')")).toEqual([1, 3]);
    expect(ev('recall([2, 5, 7], [5, 9])')).toBe(0.5);
  });

  it('has matrix helpers for retrieval evals', () => {
    expect((ev('minmax([0.7, 0.8, 0.9])') as number[]).map((x: number) => Math.round(x * 10) / 10)).toEqual([0, 0.5, 1]);
    expect(ev('topk([0.1, 0.9, 0.5], 2)')).toEqual([1, 2]);
    expect(ev('recallall([[0.9, 0.1, 0.5], [0.1, 0.2, 0.9]], [[0], [0, 1]], 1)')).toEqual([1, 0]);
    expect(ev("split('férias e VR', ' e ')")).toEqual(['férias', 'VR']);
    expect(ev("anyincludes(['abc', 'xyz'], 'yz')")).toBe(true);
    expect(ev('topk([0, 0, 0.4], 3)')).toEqual([2]);
    expect(ev('memberall([3, 5, 7], [5])')).toEqual([0, 1, 0]);
    expect(ev('mul([1, 2], [3, 4])')).toEqual([3, 8]);
    expect(ev('cumsum([1, 2, 3])')).toEqual([1, 3, 6]);
    expect(ev('maxall([[1, 5], [7, 2]])')).toEqual([5, 7]);
    expect(ev('geall([0.7, 0.8], 0.75)')).toEqual([false, true]);
    expect(ev('ltall([0.7, 0.8], 0.75)')).toEqual([true, false]);
    expect(ev('pickrows([[1], [2], [3]], [2, 0])')).toEqual([[3], [1]]);
    expect(evaluate("lookupall(m, ['a', 'z'], 0)", { m: { a: 2 } })).toEqual([2, 0]);
    expect(ev("containsany('Fica 0,30 então', ['0,30', 'x'])")).toBe(true);
    expect(ev("tagmatching(['Página 1', 'texto'], ['página'], '! ', '')")).toEqual(['! Página 1', 'texto']);
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
