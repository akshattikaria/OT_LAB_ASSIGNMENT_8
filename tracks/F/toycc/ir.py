"""Immutable three-address SSA and a separately dispatched register interpreter."""
from dataclasses import dataclass
from .frontend import MASK

OPNAMES={'+':'add','-':'sub','*':'mul','^':'xor','&':'and','|':'or','<<':'shl','>>':'shr'}
COMMUTATIVE={'add','mul','xor','and','or'}
COST={'arg':1,'const':1,'copy':1,'add':1,'sub':1,'mul':4,'xor':1,'and':1,'or':1,'shl':1,'shr':1}


@dataclass(frozen=True)
class Inst:
    dest:int
    op:str
    args:tuple=()
    value:int|None=None


@dataclass(frozen=True)
class IR:
    params:tuple
    code:tuple
    result:int

    def json(self):return {'params':list(self.params),'code':[{'dest':i.dest,'op':i.op,'args':list(i.args),'value':i.value} for i in self.code],'result':self.result}


def from_json(data):
    result=IR(tuple(data['params']),tuple(Inst(i['dest'],i['op'],tuple(i['args']),i['value']) for i in data['code']),data['result']);validate(result);return result


def validate(ir):
    seen=set()
    for instruction in ir.code:
        if not isinstance(instruction.dest,int) or instruction.dest<0 or instruction.dest in seen:raise ValueError('Duplicate/invalid SSA definition')
        if instruction.op not in COST or any(a not in seen for a in instruction.args):raise ValueError('Unknown operation or use before definition')
        arity=0 if instruction.op in ('arg','const') else 1 if instruction.op=='copy' else 2
        if len(instruction.args)!=arity:raise ValueError('Wrong operation arity')
        if instruction.op=='arg' and (not isinstance(instruction.value,int) or not 0<=instruction.value<len(ir.params)):raise ValueError('Invalid input index')
        if instruction.op=='const' and (not isinstance(instruction.value,int) or not 0<=instruction.value<=MASK):raise ValueError('Constant outside uint64')
        seen.add(instruction.dest)
    if ir.result not in seen:raise ValueError('Missing result definition')
    return ir


def canonical(ir):
    validate(ir);mapping={};code=[]
    for old in ir.code:
        dest=len(code);code.append(Inst(dest,old.op,tuple(mapping[a] for a in old.args),old.value));mapping[old.dest]=dest
    return IR(ir.params,tuple(code),mapping[ir.result])


def lower(program):
    code=[];environment={}
    def emit(op,args=(),value=None):
        dest=len(code);code.append(Inst(dest,op,tuple(args),value));return dest
    for index,name in enumerate(program.params):environment[name]=emit('arg',value=index)
    def expression(node):
        if node.kind=='literal':return emit('const',value=node.value)
        if node.kind=='name':return environment[node.value]
        if node.kind=='unary':
            value=expression(node.args[0]);return value if node.value=='+' else emit('sub',(emit('const',value=0),value))
        left=expression(node.args[0]);right=expression(node.args[1]);return emit(OPNAMES[node.value],(left,right))
    for name,node in program.bindings:environment[name]=expression(node)
    result=expression(program.result);return validate(IR(program.params,tuple(code),result))


def operation(op,a,b):
    if op=='add':value=a+b
    elif op=='sub':value=a-b
    elif op=='mul':value=a*b
    elif op=='xor':value=a^b
    elif op=='and':value=a&b
    elif op=='or':value=a|b
    elif op=='shl':value=a<<(b&63)
    elif op=='shr':value=a>>(b&63)
    else:raise ValueError('Unknown binary opcode')
    return value&MASK


def execute(ir,arguments):
    if len(arguments)!=len(ir.params) or any(not isinstance(v,int) or not 0<=v<=MASK for v in arguments):raise ValueError('Invalid uint64 inputs')
    values={}
    for instruction in ir.code:
        if instruction.op=='arg':value=arguments[instruction.value]
        elif instruction.op=='const':value=instruction.value
        elif instruction.op=='copy':value=values[instruction.args[0]]
        else:value=operation(instruction.op,*(values[a] for a in instruction.args))
        values[instruction.dest]=value
    return values[ir.result]


def score(ir):return sum(COST[i.op] for i in ir.code)
