import { describe, expect, it } from 'vitest';
import { defaultCommand } from '../src/engine/command';
import { LANGS } from '../src/engine/schema';
import { lessons, runCmd } from './helpers';

/**
 * Prática P1 journeys in simulated mode (the default on any phone): the default
 * command runs, the guess the lesson calls right is what the sim shows, and the
 * "break it" cheat (hint 3) raises the break flag.
 */

const pratica = lessons.filter((l) => l.track === 'pratica');

for (const lang of LANGS) {
  describe(`[${lang}] Prática P1`, () => {
    for (const l of pratica) {
      it(`${l.def.id}: default runs, cheat breaks it`, () => {
        const def = runCmd(l.def.id, lang, defaultCommand(l.def.command, lang));
        expect(def.error, 'default command must not error').toBeUndefined();
        const cheat = l.locale[lang].hints!.cmd[2];
        expect(runCmd(l.def.id, lang, cheat).flags, cheat).toContain(l.def.break.flag);
      });
    }

    const c = lang === 'pt'
      ? { pt: 'contar "Preciso reemitir a nota fiscal 4471 com urgência, por favor."', en: 'contar "I need to reissue invoice 4471 urgently, please."', faq: 'buscar "Como faço para pedir minhas férias?"', game: 'buscar "Qual foi o placar do jogo ontem?"', gen0: 'gerar "Crie um slogan curto para uma padaria de bairro" --temp 0 --amostras 3', json: 'extrair "Oi, aqui é a Marina do financeiro. A nota 4471, de R$ 1.250,00, venceu ontem e o cliente está cobrando. Dá para reemitir hoje?"' }
      : { pt: 'count "Preciso reemitir a nota fiscal 4471 com urgência, por favor."', en: 'count "I need to reissue invoice 4471 urgently, please."', faq: 'search "How do I ask for my vacation?"', game: 'search "What was the score of last night’s game?"', gen0: 'generate "Write a short slogan for a neighborhood bakery" --temp 0 --samples 3', json: 'extract "Hi, Marina from finance here. Invoice 4471 for $1,250.00 was due yesterday and the client is chasing it. Can you reissue it today?"' };

    it('guesses match what the simulator shows', () => {
      // 1: Portuguese costs more tokens than English
      expect(Number(runCmd('p-tokens-de-verdade', lang, c.pt).vars?.tokens)).toBeGreaterThan(Number(runCmd('p-tokens-de-verdade', lang, c.en).vars?.tokens));
      // 3: an on-topic FAQ question is answered; an off-topic one is forwarded
      expect(runCmd('p-busca-no-faq-de-rh', lang, c.faq).flags).toContain('answered');
      expect(runCmd('p-busca-no-faq-de-rh', lang, c.game).flags).toContain('forwarded');
      // 4: temperature 0 gives one distinct answer
      expect(runCmd('p-llm-no-seu-aparelho', lang, c.gen0).vars?.distinct).toBe(1);
      // 5: no schema → prose, not valid data
      expect(runCmd('p-json-que-o-sistema-aceita', lang, c.json).flags).toContain('invalid');
      expect(runCmd('p-json-que-o-sistema-aceita', lang, `${c.json} ${lang === 'pt' ? '--esquema completo' : '--schema strict'}`).flags).toContain('valid');
      // 7: 50k × (800 × 1 + 200 × 4) / 1M = 80
      expect(runCmd('p-local-aberto-ou-fronteira', lang, defaultCommand(lessons.find((x) => x.def.id === 'p-local-aberto-ou-fronteira')!.def.command, lang)).vars?.monthly).toBe(80);
    });
  });
}
