import { describe, expect, it } from 'vitest';
import { initialState, reduce, feedbackKey } from '../src/engine/stepMachine';

const ran = (flags: string[]) => ({ type: 'ran' as const, input: 'x', result: { flags }, breakFlag: 'weird' });

describe('step machine', () => {
  it('walks predict → run → see → why → break', () => {
    let s = initialState('x');
    s = reduce(s, { type: 'predict', option: 'same' });
    expect(s.phase).toBe(1);
    s = reduce(s, ran([]));
    expect(s.phase).toBe(2);
    expect(feedbackKey(s, 'same')).toBe('right');
    s = reduce(s, { type: 'goto', phase: 3 });
    s = reduce(s, { type: 'goto', phase: 4 });
    s = reduce(s, ran(['varied']));
    expect(s.broke).toBe(false);
    s = reduce(s, ran(['weird']));
    expect(s.broke).toBe(true);
  });

  it('allows running before guessing, and never jumps ahead', () => {
    let s = reduce(initialState('x'), ran([]));
    expect(s.phase).toBe(2);
    expect(feedbackKey(s, 'same')).toBe('skipped');
    s = reduce(initialState('x'), { type: 'goto', phase: 4 });
    expect(s.phase).toBe(0);
  });

  it('caps hints at 3', () => {
    let s = initialState('x');
    for (let i = 0; i < 5; i++) s = reduce(s, { type: 'hint' });
    expect(s.hints).toBe(3);
  });
});
