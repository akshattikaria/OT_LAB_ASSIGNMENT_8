"""Own lexer and precedence parser; arithmetic has total modulo-2**64 semantics."""
from dataclasses import dataclass
import re

MASK=(1<<64)-1
RESERVED={'fn','let','return'}
TOKEN=re.compile(r'(?P<SPACE>\s+)|(?P<COMMENT>//[^\n]*)|(?P<NUM>0[xX][0-9a-fA-F]+|[0-9]+)|(?P<ID>[A-Za-z_][A-Za-z0-9_]*)|(?P<OP><<|>>|[+*^&|\-(),;={}])')


@dataclass(frozen=True)
class Token:
    kind:str
    value:str
    offset:int


@dataclass(frozen=True)
class Expr:
    kind:str
    value:object
    args:tuple=()


@dataclass(frozen=True)
class Program:
    name:str
    params:tuple
    bindings:tuple
    result:Expr


def lex(source):
    if not isinstance(source,str) or len(source)>200000:raise ValueError('Source must be text of at most 200,000 characters')
    tokens=[];offset=0
    while offset<len(source):
        match=TOKEN.match(source,offset)
        if not match:raise ValueError(f'Unknown character at offset {offset}: {source[offset]!r}')
        if match.lastgroup not in ('SPACE','COMMENT'):tokens.append(Token(match.lastgroup,match.group(),offset))
        offset=match.end()
    return tokens+[Token('EOF','<eof>',len(source))]


class Parser:
    def __init__(self,source):self.tokens=lex(source);self.index=0;self.defined=set()
    @property
    def current(self):return self.tokens[self.index]
    def pop(self,value=None):
        token=self.current
        if value is not None and token.value!=value:raise ValueError(f'Expected {value!r}, got {token.value!r} at offset {token.offset}')
        if token.kind=='EOF':raise ValueError('Unexpected end of input')
        self.index+=1;return token
    def identifier(self):
        token=self.current
        if token.kind!='ID' or token.value in RESERVED:raise ValueError(f'Expected identifier at offset {token.offset}')
        return self.pop().value
    def expression(self,level=0):
        levels=(('|',),('^',),('&',),('<<','>>'),('+','-'),('*',))
        if level==len(levels):return self.primary()
        result=self.expression(level+1)
        while self.current.value in levels[level]:
            operator=self.pop().value;result=Expr('binary',operator,(result,self.expression(level+1)))
        return result
    def primary(self):
        token=self.current
        if token.value in ('+','-'):
            op=self.pop().value;return Expr('unary',op,(self.primary(),))
        if token.value=='(':
            self.pop('(');result=self.expression();self.pop(')');return result
        if token.kind=='NUM':
            text=self.pop().value;value=int(text,16 if text.lower().startswith('0x') else 10)
            if value>MASK:raise ValueError('Integer literal exceeds uint64 range')
            return Expr('literal',value)
        if token.kind=='ID':
            name=self.identifier()
            if name not in self.defined:raise ValueError(f'Undefined variable {name!r}')
            return Expr('name',name)
        raise ValueError(f'Expected expression at offset {token.offset}')
    def parse(self):
        self.pop('fn');name=self.identifier();self.pop('(');params=[]
        if self.current.value!=')':
            while True:
                parameter=self.identifier()
                if parameter in self.defined:raise ValueError('Duplicate parameter')
                params.append(parameter);self.defined.add(parameter)
                if self.current.value!=',':break
                self.pop(',')
        if len(params)>8:raise ValueError('At most eight arguments supported')
        self.pop(')');self.pop('{');bindings=[]
        while self.current.value=='let':
            self.pop('let');variable=self.identifier()
            if variable in self.defined:raise ValueError('Bindings are immutable; duplicate name')
            self.pop('=');expression=self.expression();self.pop(';');bindings.append((variable,expression));self.defined.add(variable)
        self.pop('return');result=self.expression();self.pop(';');self.pop('}')
        if self.current.kind!='EOF':raise ValueError('Trailing tokens after function')
        return Program(name,tuple(params),tuple(bindings),result)


def parse(source):return Parser(source).parse()


def evaluate(program,arguments):
    """Independent recursive AST reference; never uses Python eval or C code."""
    if len(arguments)!=len(program.params) or any(not isinstance(v,int) or not 0<=v<=MASK for v in arguments):raise ValueError('Arguments must match uint64 parameters')
    environment=dict(zip(program.params,arguments))
    def expression(node):
        if node.kind=='literal':return node.value
        if node.kind=='name':return environment[node.value]
        if node.kind=='unary':
            value=expression(node.args[0]);return value if node.value=='+' else (-value)&MASK
        left=expression(node.args[0]);right=expression(node.args[1]);op=node.value
        if op=='+':value=left+right
        elif op=='-':value=left-right
        elif op=='*':value=left*right
        elif op=='^':value=left^right
        elif op=='&':value=left&right
        elif op=='|':value=left|right
        elif op=='<<':value=left<<(right&63)
        elif op=='>>':value=left>>(right&63)
        else:raise ValueError('Unknown AST operator')
        return value&MASK
    for name,node in program.bindings:environment[name]=expression(node)
    return expression(program.result)
