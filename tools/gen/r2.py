"""IA aplicada · Produção · Etapa R2 — Segurança, privacidade e governança (lições 8 a 14).
Run: python3 tools/gen/r2.py   (writes only content/ia-aplicada/producao/08-… to 14-…)
Story: Aurora's HR assistant, already measured in R1, now has to survive attackers, leaks and auditors."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib

for name in ('r2_l1', 'r2_l2', 'r2_l3', 'r2_l4', 'r2_l5', 'r2_l6', 'r2_l7'):
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), name + '.py')):
        importlib.import_module(name).build()
