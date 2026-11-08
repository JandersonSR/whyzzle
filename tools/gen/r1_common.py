"""Shared helpers for IA aplicada · Produção · Etapa R1 (Avaliação e qualidade).
Writes only content/ia-aplicada/producao/NN-slug/{step,pt,en,teacher}.json."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write as _write, flag, step as _step
from p2_corpus import CHUNKS

TOPIC, TRACK = 'ia-aplicada', 'producao'
LLAMA = 'Llama-3.2-1B-Instruct-q4f16_1-MLC'
E5 = 'Xenova/multilingual-e5-small'


def write(folder, s, pt, en, teacher):
    _write(TOPIC, TRACK, folder, s, pt, en, teacher)


def step(id, order, minutes, tags, requires, executors, verb, arg, flags, predict, brk, sim, real=None):
    return _step(id, order, TRACK, minutes, tags, requires, executors, verb, arg, flags, predict, brk, sim, real)


def LQ(pt, en):
    return {'pt': pt, 'en': en}


def ex(*qs):
    return [{'pt': q['pt'], 'en': q['en']} for q in qs]


def opt(id, pt, en=None):
    return {'id': id, 'pt': pt, 'en': en or pt}


def real_chat(op, args):
    """Same op for the in-browser Llama and for the person's own key."""
    return {'no-navegador': {'adapter': 'declarative', 'model': LLAMA, 'op': op, 'args': args},
            'sua-chave': {'adapter': 'declarative', 'op': op, 'args': args}}


def teacher(pt, en):
    return {'pt': pt, 'en': en}


def yn(T):
    return T('Use sim ou nao.', 'Use yes or no.')


def chunk(L, i):
    return CHUNKS[L][i][1]
