import { registerModel } from '../engine/registry';
import { agent } from './agent';
import { embeddings } from './embeddings';
import { evals } from './evals';
import { mission } from './mission';
import { nextToken } from './nextToken';
import { promptGrader } from './promptGrader';
import { rag } from './rag';
import { sampler } from './sampler';
import { tokenizer } from './tokenizer';

/** Registers every simulated model. Import once at startup (and in tests). */
export function registerAllModels(): void {
  [nextToken, tokenizer, sampler, promptGrader, embeddings, rag, agent, evals, mission].forEach((m) => registerModel(m));
}
