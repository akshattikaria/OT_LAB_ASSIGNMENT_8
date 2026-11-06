"""Four semantics-preserving passes for pure immutable uint64 operations."""
from .frontend import MASK
from .ir import Inst,IR,canonical,operation,COMMUTATIVE


def _resolve(alias,index):
    while index in alias:index=alias[index]
    return index


def fold(ir):
    known={};alias={};code=[]
    for old in ir.code:
        args=tuple(_resolve(alias,a) for a in old.args);op=old.op;replacement=None
        if op=='copy':alias[old.dest]=args[0];continue
        if op=='const':known[old.dest]=old.value
        elif op not in ('arg','const'):
            a,b=args;ka=known.get(a);kb=known.get(b)
            if ka is not None and kb is not None:replacement=Inst(old.dest,'const',(),operation(op,ka,kb))
            elif op in ('add','xor','or') and (ka==0 or kb==0):alias[old.dest]=b if ka==0 else a;continue
            elif op=='sub' and kb==0:alias[old.dest]=a;continue
            elif op=='mul' and (ka==1 or kb==1):alias[old.dest]=b if ka==1 else a;continue
            elif op in ('mul','and') and (ka==0 or kb==0):replacement=Inst(old.dest,'const',(),0)
            elif op=='and' and (ka==MASK or kb==MASK):alias[old.dest]=b if ka==MASK else a;continue
            elif op=='or' and (ka==MASK or kb==MASK):replacement=Inst(old.dest,'const',(),MASK)
            elif op in ('sub','xor') and a==b:replacement=Inst(old.dest,'const',(),0)
            elif op in ('and','or') and a==b:alias[old.dest]=a;continue
            elif op in ('shl','shr') and kb is not None and kb&63==0:alias[old.dest]=a;continue
        instruction=replacement or Inst(old.dest,op,args,old.value)
        if instruction.op=='const':known[instruction.dest]=instruction.value
        code.append(instruction)
    return canonical(IR(ir.params,tuple(code),_resolve(alias,ir.result)))


def cse(ir):
    alias={};available={};code=[]
    for old in ir.code:
        args=tuple(_resolve(alias,a) for a in old.args)
        if old.op=='copy':alias[old.dest]=args[0];continue
        if old.op in COMMUTATIVE:args=tuple(sorted(args))
        key=(old.op,args,old.value)
        if key in available:alias[old.dest]=available[key]
        else:available[key]=old.dest;code.append(Inst(old.dest,old.op,args,old.value))
    return canonical(IR(ir.params,tuple(code),_resolve(alias,ir.result)))


def dce(ir):
    live={ir.result};kept=[]
    for instruction in reversed(ir.code):
        if instruction.dest in live:kept.append(instruction);live.update(instruction.args)
    return canonical(IR(ir.params,tuple(reversed(kept)),ir.result))


def strength(ir):
    constants={i.dest:i.value for i in ir.code if i.op=='const'};next_id=max(i.dest for i in ir.code)+1;code=[]
    for old in ir.code:
        transformed=False
        if old.op=='mul':
            for literal,other in ((old.args[0],old.args[1]),(old.args[1],old.args[0])):
                value=constants.get(literal)
                if value is not None and value>0 and value&(value-1)==0:
                    amount=value.bit_length()-1;code.append(Inst(next_id,'const',(),amount))
                    code.append(Inst(old.dest,'shl',(other,next_id)));next_id+=1;transformed=True;break
        if not transformed:code.append(old)
    return canonical(IR(ir.params,tuple(code),ir.result))


PASSES={'fold':fold,'cse':cse,'dce':dce,'strength':strength}
PASS_NAMES=tuple(PASSES)


def apply_order(ir,order):
    for name in order:ir=PASSES[name](ir)
    return canonical(ir)
