import argparse
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description='Track B discrete optimization experiments')
    sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('benchmark');q.add_argument('--out',default='results-rerun')
    q.add_argument('--sizes',nargs='+',type=int,default=[10,20,40,80]);q.add_argument('--seeds',nargs='+',type=int,default=[0,1,2,3,4])
    q.add_argument('--repeats',type=int,default=3);q.add_argument('--time-limit',type=float,default=2)
    q=sub.add_parser('report');q.add_argument('directory')
    sub.add_parser('demo')
    args=p.parse_args()
    if args.command=='benchmark':
        from .experiment import run_benchmark
        from .report import build_report
        run_benchmark(args.out,args.sizes,args.seeds,args.repeats,args.time_limit)
        build_report(args.out);print('Report:',str(Path(args.out)/'report.html'))
    elif args.command=='report':
        from .report import build_report
        build_report(args.directory)
    else:
        from .data import teaching
        from .model import audit
        from .solvers import SOLVERS
        from .qubo import knapsack_qubo,enumerate_qubo
        p=teaching()
        for name,f in SOLVERS.items():
            r=f(p);a=audit(p,r.selection)
            print(f"{name:14} value={a['value']} weight={a['weight']} feasible={a['feasible']} status={r.status}")
        q=enumerate_qubo(knapsack_qubo(p));print('QUBO minimum energy:',q['minimum_energy'],'All ground states valid:',q['all_ground_states_encoded_feasible'])


if __name__=='__main__':main()
