import argparse


def main():
    p=argparse.ArgumentParser(description='Track G actual xv6/QEMU validation and benchmarks');sub=p.add_subparsers(dest='command',required=True)
    v=sub.add_parser('validate');v.add_argument('--out',default='validation-rerun');v.add_argument('--toolchain');v.add_argument('--cpus',type=int,default=3)
    b=sub.add_parser('benchmark');b.add_argument('--out',default='results-rerun');b.add_argument('--toolchain');b.add_argument('--repeats',type=int,default=3);b.add_argument('--cpus',type=int,default=3);b.add_argument('--scale',type=float,default=1)
    r=sub.add_parser('report');r.add_argument('directory');a=sub.add_parser('audit');a.add_argument('directory');args=p.parse_args()
    if args.command=='validate':
        from .experiment import validate_all
        validate_all(args.out,args.toolchain,args.cpus)
    elif args.command=='benchmark':
        from .experiment import run_benchmark
        from .report import build_report
        run_benchmark(args.out,args.toolchain,args.repeats,args.cpus,args.scale);build_report(args.out)
    elif args.command=='report':
        from .report import build_report
        build_report(args.directory)
    else:
        from .audit import audit
        print(audit(args.directory))


if __name__=='__main__':main()
