import argparse


def main():
    parser=argparse.ArgumentParser(description='Track D submodular, parallel, federated and multi-task experiments')
    sub=parser.add_subparsers(dest='command',required=True)
    b=sub.add_parser('benchmark');b.add_argument('--out',default='results-rerun');b.add_argument('--seeds',nargs='+',type=int,default=[0,1,2,3,4])
    b.add_argument('--workers',nargs='+',type=int);b.add_argument('--repeats',type=int,default=3);b.add_argument('--iterations',type=int,default=30000);b.add_argument('--mtl-steps',type=int,default=400)
    r=sub.add_parser('report');r.add_argument('directory');a=sub.add_parser('audit');a.add_argument('directory');sub.add_parser('demo');args=parser.parse_args()
    if args.command=='benchmark':
        from .experiment import run_benchmark
        from .report import build_report
        run_benchmark(args.out,args.seeds,args.workers,args.repeats,args.iterations,args.mtl_steps);build_report(args.out)
        print('Report:',args.out+'/report.html')
    elif args.command=='report':
        from .report import build_report
        build_report(args.directory)
    elif args.command=='audit':
        from .audit import audit
        print(audit(args.directory))
    else:
        from .coverage import Coverage,solve
        from .federated import data,partition,centralized,fedavg
        import numpy as np
        p=Coverage([{0,1,3,4},{0,1,2},{3,4,5}],[1]*6,2)
        for method in ('greedy','lazy_greedy','exact'):print(method,solve(p,method))
        d=data(0);clients=partition(d['ytrain'],'label_skew',0)
        print('One-step FedAvg vs centralized maximum coefficient difference:',np.max(abs(np.array(fedavg(d,clients,1,5)['theta'])-centralized(d,5)['theta'])))


if __name__=='__main__':main()
