"""Shared helpers for lesson generators. Each generator writes data files only:
content/<topic>/<track>/NN-slug/{step,pt,en,teacher}.json. Run with python3."""
import json, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'content')

def write(topic, track, folder, step, pt, en, teacher):
    d = os.path.join(ROOT, topic, track, folder); os.makedirs(d, exist_ok=True)
    for name, obj in (('step', step), ('pt', pt), ('en', en), ('teacher', teacher)):
        with open(os.path.join(d, f'{name}.json'), 'w') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2); f.write('\n')

def flag(name, pt, en, type, **kw):
    f = {'name': name, 'alias': {'pt': pt, 'en': en}, 'type': type}; f.update(kw); return f

def step(id, order, track, minutes, tags, requires, executors, verb, arg, flags, predict, brk, sim, real=None, kind='step'):
    s = {'id': id, 'order': order, 'track': track, 'kind': kind, 'minutes': minutes, 'tags': tags, 'requires': requires,
         'executors': executors, 'model': 'declarative', 'scene': 'widgets',
         'command': {'verb': verb, 'arg': arg, 'flags': flags}, 'break': {'flag': brk}, 'data': {'sim': sim}}
    if predict: s['predict'] = predict
    if real: s['real'] = real
    return s
