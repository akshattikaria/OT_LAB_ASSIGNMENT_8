import argparse


def main():
    parser=argparse.ArgumentParser(description='Track I SDK quantum algorithms and QML comparison');sub=parser.add_subparsers(dest='command',required=True)
    b=sub.add_parser('benchmark');b.add_argument('--out',default='results-rerun');b.add_argument('--seeds',nargs='+',type=int,default=[0,1,2]);b.add_argument('--shots',type=int,default=4096);b.add_argument('--train-size',type=int,default=60);b.add_argument('--test-size',type=int,default=60);b.add_argument('--steps',type=int,default=60);b.add_argument('--maxfev',type=int,default=300);b.add_argument('--quick',action='store_true')
    a=sub.add_parser('audit');a.add_argument('directory');a.add_argument('--replay-noise',action='store_true');r=sub.add_parser('report');r.add_argument('directory');args=parser.parse_args()
    if args.command=='benchmark':
        from .experiment import run
        run(args.out,args.seeds,args.shots,args.train_size,args.test_size,args.steps,args.maxfev,args.quick)
        from .report import build_report
        build_report(args.out)
    elif args.command=='audit':
        from .audit import audit
        print(audit(args.directory,args.replay_noise))
    else:
        from .report import build_report
        build_report(args.directory)


if __name__=='__main__':main()
