import argparse


def main():
    p=argparse.ArgumentParser(description='Track C quantum optimization simulation experiments')
    sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('benchmark');q.add_argument('--out',default='results-rerun');q.add_argument('--seeds',nargs='+',type=int,default=[0,1,2,3,4])
    q.add_argument('--steps',type=int,default=80);q.add_argument('--qaoa-maxfev',type=int,default=600);q.add_argument('--barren-samples',type=int,default=64)
    q=sub.add_parser('report');q.add_argument('directory')
    sub.add_parser('demo');args=p.parse_args()
    if args.command=='benchmark':
        from .experiment import run_benchmark
        from .report import build_report
        run_benchmark(args.out,args.seeds,args.steps,args.qaoa_maxfev,args.barren_samples);build_report(args.out);print('Report:',args.out+'/report.html')
    elif args.command=='report':
        from .report import build_report
        build_report(args.directory)
    else:
        from .optimizers import train_vqe
        from .models import hamiltonian
        import numpy as np
        r=train_vqe('QNG',0,40)
        print('Exact classical ground energy:',np.linalg.eigvalsh(hamiltonian())[0])
        print('Simulated VQE energy:',r['final_exact_energy'])
        print('Simulation work:',r['work'])


if __name__=='__main__':main()
