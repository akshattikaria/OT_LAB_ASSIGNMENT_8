import argparse
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description="Track A continuous optimization experiments")
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("benchmark");p.add_argument("--out",default="results-rerun")
    p.add_argument("--seeds",nargs="+",type=int,default=[0,1,2,3,4]);p.add_argument("--repeats",type=int,default=3)
    p.add_argument("--ridge-epochs",type=int,default=35);p.add_argument("--mlp-epochs",type=int,default=80)
    p.add_argument("--n",type=int,default=256)
    p=sub.add_parser("report");p.add_argument("directory")
    sub.add_parser("demo")
    args=parser.parse_args()
    if args.command=="benchmark":
        from .experiment import run_benchmark
        from .report import build_report
        run_benchmark(args.out,args.seeds,args.repeats,args.ridge_epochs,args.mlp_epochs,args.n)
        build_report(args.out);print("Report:",str(Path(args.out)/"report.html"))
    elif args.command=="report":
        from .report import build_report
        build_report(args.directory)
    elif args.command=="demo":
        from .problems import make_dataset
        from .optimizers import train
        from .checks import audit_run
        p,w,_,_=make_dataset("ridge",0)
        reference=p.value(p.reference())
        for method,lr in (("GD",.08),("Adam",.02),("Newton",1.0),("GaussNewton",1.0)):
            r=train(p,w,method,lr,epochs=35)
            print(f"{method:12} loss={r['final_objective']:.9f} gap={r['final_objective']-reference:.3g} audit={audit_run(p,r)['valid']}")


if __name__=="__main__":main()
