"""Synthetic teaching kernels and independent random programs for equivalence checks."""
import random
from .frontend import MASK


FAMILIES=('constant_chain','redundant','dead_heavy','mixed')


def generate(family,seed):
    rng=random.Random(6000+seed);length=12+seed%3*4;lines=[f'fn {family}_{seed}(x,y,z) {{']
    if family=='constant_chain':
        lines+=['let k0 = 2 * 4;','let k1 = k0 + 0;','let value0 = x + y;']
        for i in range(1,length+1):lines.append(f'let value{i} = value{i-1} + (z * k1) + ({i} * 3);')
        result=f'value{length}'
    elif family=='redundant':
        lines+=['let value0 = z;']
        for i in range(1,length+1):
            lines+=[f'let a{i} = x + y;',f'let b{i} = y + x;',f'let value{i} = value{i-1} + a{i} * 8 + b{i} * 8;']
        result=f'value{length}'
    elif family=='dead_heavy':
        lines+=['let value0 = x ^ y;']
        for i in range(1,length+1):
            lines+=[f'let dead{i} = (x + {i}) * (y + z) + ({i} * 8);',f'let value{i} = value{i-1} + z;']
        result=f'value{length}'
    elif family=='mixed':
        lines+=['let k = 2 * 4;','let value0 = z;']
        for i in range(1,length+1):
            constant=rng.choice((1,2,4,8,16));lines+=[f'let a{i} = x + y;',f'let b{i} = y + x;',f'let dead{i} = (a{i} * {i+3}) ^ z;',
                f'let value{i} = value{i-1} + a{i} * k + b{i} * {constant} + 0;']
        result=f'value{length}'
    else:raise ValueError('Unknown source family')
    lines+=[f'return {result};','}'];return '\n'.join(lines)+'\n'


def vectors(seed,count=24,arity=3):
    rng=random.Random(7000+seed);edges=[0,1,2,63,64,65,1<<63,MASK,MASK-1]
    rows=[[(value+q)&MASK for q in range(arity)] for value in edges]
    rows+=[[rng.getrandbits(64) for _ in range(arity)] for _ in range(count)]
    return rows


def random_program(seed,statements=8):
    rng=random.Random(seed+8000);names=['x','y','z'];lines=['fn random(x,y,z) {']
    def leaf():return rng.choice(names) if rng.random()<.65 else str(rng.choice([0,1,2,4,8,63,64,65,1<<63,MASK]))
    for i in range(statements):
        left=leaf();right=leaf();op=rng.choice(['+','-','*','^','&','|','<<','>>']);name=f't{i}'
        lines.append(f'let {name} = ({left} {op} {right}) + 0;');names.append(name)
    lines+=['return '+rng.choice(names[-3:])+';','}'];return '\n'.join(lines)+'\n'
