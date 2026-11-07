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
  describe(`[${lang}] Prática`, () => {
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

    it('P2 guesses match what the simulator shows', () => {
      const pt = lang === 'pt';
      const q = (p: string, e: string) => (pt ? p : e);
      // 8: 4 header lines + 1 duplicate = 5 junk lines removed
      expect(runCmd('p-ingestao-e-limpeza', lang, q('limpar', 'clean')).vars?.removed).toBe(5);
      // 9: doubling chunk size roughly halves the count
      const n40 = Number(runCmd('p-fatiar-documentos', lang, q('fatiar --tamanho 40', 'chunk --size 40')).vars?.n);
      const n80 = Number(runCmd('p-fatiar-documentos', lang, q('fatiar --tamanho 80', 'chunk --size 80')).vars?.n);
      expect(n80).toBeLessThan(n40);
      expect(n80).toBeGreaterThanOrEqual(Math.floor(n40 / 2) - 1);
      // 10: 12 × 384 × 4 bytes ≈ 18 KB
      expect(runCmd('p-indice-vetorial', lang, q('indexar', 'index')).vars?.mem).toBe('18 KB');
      // 11: keyword-only misses the synonym question; hybrid finds it
      expect(runCmd('p-busca-hibrida', lang, q('buscar --modo palavra', 'search --mode keyword')).flags).not.toContain('found');
      expect(runCmd('p-busca-hibrida', lang, q('buscar', 'search')).flags).toContain('found');
      // 12: without the reranker, top 2 misses one of the two chunks
      expect(runCmd('p-reranking', lang, q('reordenar --rerank nao', 'rerank --rerank no')).flags).not.toContain('found');
      expect(runCmd('p-reranking', lang, q('reordenar', 'rerank')).flags).toContain('found');
      // 13: off-topic with refusal on → refused; on-topic → cited
      expect(runCmd('p-citar-e-recusar', lang, q('responder "Qual o horário da academia da empresa?"', 'answer "What are the company gym’s opening hours?"')).flags).toContain('refused');
      expect(runCmd('p-citar-e-recusar', lang, q('responder', 'answer')).flags).toContain('cited');
      // 14: one query brings only one topic; two queries bring both
      expect(runCmd('p-perguntas-compostas', lang, q('perguntar --consultas 1', 'ask --queries 1')).flags).toContain('partial');
      expect(runCmd('p-perguntas-compostas', lang, q('perguntar', 'ask')).flags).toContain('complete');
      // 15: hybrid has the best mean recall at k = 2
      expect(runCmd('p-avaliar-recuperacao', lang, q('avaliar --k 2', 'evaluate --k 2')).flags).toContain('hybridBest');
    });

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
