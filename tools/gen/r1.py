"""IA aplicada · Produção · Etapa R1 — Avaliação e qualidade (lições 1 a 7).
Run: python3 tools/gen/r1.py   (writes only content/ia-aplicada/producao/01-… to 07-…)
Story: Aurora's HR assistant (from the Prática mission) goes to production. Every lesson works in 'simulado';
02 wires real embeddings (relevance), 03/06/07 wire the json op (judge, hard-case action, feedback triage)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r1_l1, r1_l2, r1_l3, r1_l4, r1_l5, r1_l6, r1_l7

for m in (r1_l1, r1_l2, r1_l3, r1_l4, r1_l5, r1_l6, r1_l7):
    m.build()
