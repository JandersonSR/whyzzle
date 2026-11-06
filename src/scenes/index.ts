import { AgentScene } from './Agent';
import { EmbeddingsScene } from './Embeddings';
import { EvalsScene } from './Evals';
import { MissionScene } from './Mission';
import { NextTokenScene } from './NextToken';
import { PromptScene } from './Prompt';
import { RagScene } from './Rag';
import { SamplerScene } from './Sampler';
import { TokensScene } from './Tokens';
import { WidgetsScene } from './Widgets';
import type { Scene } from './types';

/** Scenes by the name a lesson uses in step.json → "scene". */
export const scenes: Record<string, Scene> = {
  'next-token': NextTokenScene,
  tokenizer: TokensScene,
  sampler: SamplerScene,
  prompt: PromptScene,
  embeddings: EmbeddingsScene,
  rag: RagScene,
  agent: AgentScene,
  evals: EvalsScene,
  mission: MissionScene,
  widgets: WidgetsScene,
};
