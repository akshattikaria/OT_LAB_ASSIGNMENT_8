import argparse
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description='Track F unsigned toy compiler and pass-order study')
    sub=parser.add_subparsers(dest='command',required=True)
    b=sub.add_parser('benchmark');b.add_argument('--out',default='results-rerun');b.add_argument('--seeds',nargs='+',type=int,default=[0,1,2,3,4]);b.add_argument('--repeats',type=int,default=5);b.add_argument('--iterations',type=int,default=100000);b.add_argument('--compile-repeats',type=int,default=3)
    c=sub.add_parser('compile');c.add_argument('source');c.add_argument('--method',default='dp_order',choices=('baseline','fold_only','cse_only','dce_only','strength_only','fixed','greedy_order','dp_order'));c.add_argument('--out',required=True)
    r=sub.add_parser('report');r.add_argument('directory');a=sub.add_parser('audit');a.add_argument('directory');sub.add_parser('demo');args=parser.parse_args()
    if args.command=='benchmark':
        from .experiment import run_benchmark
        from .report import build_report
        run_benchmark(args.out,args.seeds,args.repeats,args.iterations,args.compile_repeats);build_report(args.out);print('Report:',args.out+'/report.html')
    elif args.command=='compile':
        from .experiment import compile_variant
        from .native import translation_unit
        ir,info=compile_variant(Path(args.source).read_text(),args.method);path=Path(args.out)
        if path.exists():raise ValueError('Choose a new generated-C output file')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(translation_unit([ir]));print(info)
    elif args.command=='report':
        from .report import build_report
        build_report(args.directory)
    elif args.command=='audit':
        from .audit import audit
        print(audit(args.directory))
    else:
        from .frontend import parse,evaluate
        from .ir import lower,score
        from .search import dynamic_programming
        source='fn demo(x,y,z) { let dead=x*y; let k=2*4; let a=x+y; let b=y+x; return a*k+b*8+0; }'
        program=parse(source);baseline=lower(program);optimized,info=dynamic_programming(baseline)
        print('Baseline IR instructions / weighted score:',len(baseline.code),score(baseline));print('DP IR instructions / weighted score:',len(optimized.code),score(optimized));print('Chosen order:',info['order']);print('AST result at (1,2,3):',evaluate(program,[1,2,3]))


if __name__=='__main__':main()
