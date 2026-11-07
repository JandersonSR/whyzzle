import json, os
BASE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','content','ia-aplicada','pratica')
def write(folder, step, pt, en, teacher):
    d=f'{BASE}/{folder}'; os.makedirs(d, exist_ok=True)
    for name,obj in (('step',step),('pt',pt),('en',en),('teacher',teacher)):
        with open(f'{d}/{name}.json','w') as f:
            json.dump(obj,f,ensure_ascii=False,indent=2); f.write('\n')
def flag(name, pt, en, type, **kw):
    f={'name':name,'alias':{'pt':pt,'en':en},'type':type}; f.update(kw); return f
def step(id, order, minutes, tags, requires, executors, verb, arg, flags, predict, brk, sim, real=None):
    s={'id':id,'order':order,'track':'pratica','minutes':minutes,'tags':tags,'requires':requires,'executors':executors,
       'model':'declarative','scene':'widgets','command':{'verb':verb,'arg':arg,'flags':flags},
       'predict':predict,'break':{'flag':brk},'data':{'sim':sim}}
    if real: s['real']=real
    return s
