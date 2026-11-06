import argparse


def main():
    p=argparse.ArgumentParser(description='Track H real SQLite index-selection experiment');sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('benchmark');b.add_argument('--out',default='results-rerun');b.add_argument('--rows',type=int,default=200000);b.add_argument('--repeats',type=int,default=5);b.add_argument('--profile-repeats',type=int,default=3);b.add_argument('--stream-size',type=int,default=100);b.add_argument('--write-rows',type=int,default=2000);b.add_argument('--write-repeats',type=int,default=3)
    a=sub.add_parser('audit');a.add_argument('directory');r=sub.add_parser('report');r.add_argument('directory');args=p.parse_args()
    if args.command=='benchmark':
        from .experiment import run
        run(args.out,args.rows,args.repeats,args.profile_repeats,args.stream_size,args.write_rows,args.write_repeats)
        from .report import build_report
        build_report(args.out)
    elif args.command=='audit':
        from .audit import audit
        print(audit(args.directory))
    else:
        from .report import build_report
        build_report(args.directory)


if __name__=='__main__':main()
