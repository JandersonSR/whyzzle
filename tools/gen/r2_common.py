"""Shared helpers for IA aplicada · Produção · Etapa R2 (Segurança, privacidade e governança).
Writes only content/ia-aplicada/producao/08-… to 14-…  Reuses the R1 helpers."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r1_common import *  # noqa: F401,F403  (write, step, flag, LQ, ex, opt, real_chat, teacher, yn, LLAMA)
from r1_common import CHUNKS

MODEL_FAST = 'claude-haiku-5-5'      # platform.claude.com/docs/en/about-claude/models/overview
MODEL_SMART = 'claude-sonnet-5-5'

WEEKLY = 2000   # conversations per week in production (from R1 · 07)
SHARE_PII = {'cpf': 7, 'email': 6, 'phone': 5}   # % of conversations that carry each kind of personal data
SHARE_HEALTH = 3                                  # % that carry health data (sensitive, LGPD art. 5 II / art. 11)


def hb(L, i):
    """Handbook chunk text, 0-based."""
    return CHUNKS[L][i][1]
