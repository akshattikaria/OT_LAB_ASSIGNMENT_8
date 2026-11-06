import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from toycc import frontend as f,ir as r,passes as p,search as s,native,programs


class CompilerTests(unittest.TestCase):
    def compile(self,expression):return r.lower(f.parse('fn test(x,y,z) { return '+expression+'; }'))

    def test_lex_comments_offsets(self):
        tokens=f.lex(' // hi\nfn a(){return 1;}');self.assertEqual(tokens[0].value,'fn');self.assertEqual(tokens[0].offset,7)

    def test_lexer_rejects_unknown(self):
        with self.assertRaises(ValueError):f.lex('fn a(){ return x / 2; }')

    def test_precedence_and_parentheses(self):
        for expr,value in (('2 + 3 * 4',14),('(2+3)*4',20),('1+2 << 3+1',48),('1|2&4',1),('12-3-2',7)):
            self.assertEqual(f.evaluate(f.parse('fn p(){return '+expr+';}'),[]),value)

    def test_unsigned_wrap_and_unary(self):
        for expr,value in (('0-1',f.MASK),('-1',f.MASK),('18446744073709551615+1',0),('18446744073709551615*2',f.MASK-1)):
            self.assertEqual(r.execute(self.compile(expr),[0,0,0]),value)

    def test_masked_shift_amounts(self):
        for amount in (0,1,63,64,65,f.MASK):
            ir=self.compile('x << y');self.assertEqual(r.execute(ir,[f.MASK,amount,0]),(f.MASK<<(amount&63))&f.MASK)

    def test_bindings_immutable_and_defined(self):
        sources=('fn p(x,x){return x;}','fn p(x){let x=2;return x;}','fn p(x){let a=b;return a;}','fn p(){return x;}')
        for source in sources:
            with self.assertRaises(ValueError):f.parse(source)

    def test_literal_range_and_trailing_tokens(self):
        for source in ('fn p(){return 18446744073709551616;}','fn p(){return 0;} extra','fn p(){return 0x;}'):
            with self.assertRaises(ValueError):f.parse(source)

    def test_input_arity_and_range(self):
        program=f.parse('fn p(x){return x;}');ir=r.lower(program)
        for args in ([],[-1],[1<<64]):
            with self.assertRaises(ValueError):f.evaluate(program,args)
            with self.assertRaises(ValueError):r.execute(ir,args)

    def test_lowering_reference(self):
        for family in programs.FAMILIES:
            program=f.parse(programs.generate(family,0));ir=r.lower(program)
            for args in programs.vectors(0,3):self.assertEqual(r.execute(ir,args),f.evaluate(program,args))

    def test_ssa_validation_and_roundtrip(self):
        ir=self.compile('(x+y)*8');self.assertEqual(r.from_json(json.loads(json.dumps(ir.json()))),ir)
        with self.assertRaises(ValueError):r.validate(r.IR(('x',),(r.Inst(0,'add',(1,2)),),0))
        with self.assertRaises(ValueError):r.validate(r.IR((),(r.Inst(0,'const',(),0),r.Inst(0,'const',(),1)),0))

    def test_constant_chain_propagation(self):
        ir=r.lower(f.parse('fn p(x){let a=2*4;let b=a+8;return x*b;}'));folded=p.fold(ir)
        self.assertTrue(any(i.op=='const' and i.value==16 for i in folded.code))
        for x in (0,1,f.MASK):self.assertEqual(r.execute(folded,[x]),(x*16)&f.MASK)

    def test_fold_valid_identities(self):
        for expr in ('x+0','0+x','x*1','1*x','x*0','x-x','x^x','x&0','x|18446744073709551615','x<<64'):
            a=self.compile(expr);b=p.fold(a)
            for x in (0,1,1<<63,f.MASK):self.assertEqual(r.execute(a,[x,0,0]),r.execute(b,[x,0,0]))

    def test_cse_commutative_only(self):
        ir=self.compile('(x+y)+(y+x)');optimized=p.cse(ir);self.assertLess(len(optimized.code),len(ir.code))
        different=self.compile('(x-y)+(y-x)');self.assertEqual(len(p.cse(different).code),len(different.code))

    def test_cse_chained_aliases(self):
        ir=r.lower(f.parse('fn p(x,y){let a=x+y;let b=y+x;let c=a*8;let d=b*8;return c+d;}'))
        optimized=p.cse(ir)
        self.assertEqual(sum(i.op=='mul' for i in optimized.code),1)
        self.assertEqual(r.execute(optimized,[3,4]),112)

    def test_dead_code_transitive(self):
        ir=r.lower(f.parse('fn p(x,y){let a=x*3;let b=a+y;return 7;}'));optimized=p.dce(ir)
        self.assertEqual(len(optimized.code),1);self.assertEqual(r.execute(optimized,[f.MASK,0]),7)

    def test_strength_every_power_of_two(self):
        for exponent in range(64):
            ir=self.compile('x*'+str(1<<exponent));optimized=p.strength(ir)
            self.assertTrue(any(i.op=='shl' for i in optimized.code))
            for value in (0,1,1<<63,f.MASK):self.assertEqual(r.execute(ir,[value,0,0]),r.execute(optimized,[value,0,0]))

    def test_strength_zero_and_nonpower_not_changed(self):
        for constant in (0,3,5,f.MASK):
            ir=self.compile('x*'+str(constant));self.assertEqual(p.strength(ir),r.canonical(ir))

    def test_all_passes_are_pure(self):
        ir=self.compile('(x+y)*8');before=ir.json()
        for transform in p.PASSES.values():transform(ir);self.assertEqual(ir.json(),before)

    def test_canonical_preserves_nonmonotone_ids(self):
        ir=r.IR(('x',),(r.Inst(5,'arg',(),0),r.Inst(100,'const',(),8),r.Inst(2,'mul',(5,100))),2)
        result=r.canonical(ir);self.assertEqual(r.execute(result,[7]),56);self.assertEqual([i.dest for i in result.code],[0,1,2])

    def test_order_can_change_cost(self):
        ir=self.compile('(x*8)+(x*8)');values={r.score(p.apply_order(ir,order)) for order in itertools.permutations(p.PASS_NAMES)}
        self.assertGreater(len(values),1)

    def test_dp_matches_exhaustive_all_families(self):
        for family in programs.FAMILIES:
            for seed in range(3):
                ir=r.lower(f.parse(programs.generate(family,seed)));result,info=s.dynamic_programming(ir)
                self.assertEqual(r.score(result),s.exhaustive(ir)['minimum_score']);self.assertEqual(len(set(info['order'])),4)

    def test_dp_retains_ir_in_state(self):
        result,info=s.dynamic_programming(self.compile('(x*8)+(x*8)'))
        self.assertGreater(info['states'],16);self.assertGreater(info['cache_hits'],0)

    def test_dp_never_worse_than_greedy_or_fixed(self):
        for family in programs.FAMILIES:
            ir=r.lower(f.parse(programs.generate(family,0)));dp,_=s.dynamic_programming(ir);greedy,_=s.greedy(ir)
            self.assertLessEqual(r.score(dp),r.score(greedy));self.assertLessEqual(r.score(dp),r.score(p.apply_order(ir,s.FIXED)))

    def test_greedy_applies_each_candidate_once(self):
        calls=[];original=s.PASSES
        def wrap(name,fn):
            def call(ir):calls.append(name);return fn(ir)
            return call
        with patch.object(s,'PASSES',{name:wrap(name,fn) for name,fn in original.items()}):result,info=s.greedy(self.compile('(x+y)*8'))
        self.assertEqual(len(calls),10);self.assertEqual(info['transition_evaluations'],len(calls))

    def test_random_all_orders_against_ast(self):
        # 50 programs * 24 orders * 5 vectors = 6,000 differential cases.
        for seed in range(50):
            program=f.parse(programs.random_program(seed));baseline=r.lower(program);pool=programs.vectors(seed,2);vectors=[pool[i] for i in (0,6,7,-2,-1)]
            expected=[f.evaluate(program,args) for args in vectors]
            for order in itertools.permutations(p.PASS_NAMES):
                optimized=p.apply_order(baseline,order)
                self.assertEqual([r.execute(optimized,args) for args in vectors],expected)

    def test_native_matches_ast_and_all_pass_orders(self):
        source=programs.random_program(17,10);program=f.parse(source);baseline=r.lower(program)
        variants=[baseline]+[p.apply_order(baseline,order) for order in itertools.permutations(p.PASS_NAMES)]
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);c=path/'test.c';c.write_text(native.translation_unit(variants))
            for level in ('O0','O2'):
                library,_=native.compile_library(c,path/(level+'.so'),level)
                for args in programs.vectors(17,4):
                    reference=f.evaluate(program,args)
                    for index in range(len(variants)):self.assertEqual(native.evaluate(library,index,args),reference)

    def test_native_wrapper_rejects_bad_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);c=path/'test.c';c.write_text(native.translation_unit([self.compile('x+1')]))
            library,_=native.compile_library(c,path/'test.so')
            for index,args in ((1,[0,0,0]),(0,[]),(0,[-1,0,0])):
                with self.assertRaises(ValueError):native.evaluate(library,index,args)

    def test_native_checksum_and_machine_inspection(self):
        baseline=self.compile('(x+y)*8');optimized,_=s.dynamic_programming(baseline)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);c=path/'test.c';c.write_text(native.translation_unit([baseline,optimized]));library,_=native.compile_library(c,path/'test.so')
            self.assertEqual(library.benchmark_variant(0,123,1000),library.benchmark_variant(1,123,1000))
            records,assembly=native.inspect_library(path/'test.so',2);self.assertEqual(len(records),2);self.assertTrue(all(row['machine_code_bytes']>0 for row in records));self.assertIn('toy_v0',assembly)

    def test_no_argument_constant_function(self):
        program=f.parse('fn p(){let a=7*9;return a;}');ir=p.apply_order(r.lower(program),s.FIXED)
        self.assertEqual(r.execute(ir,[]),63)


if __name__=='__main__':unittest.main()
