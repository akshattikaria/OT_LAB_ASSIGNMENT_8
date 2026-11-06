"""Run with python -m evcharge. No downloads, accounts or API keys required."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Track E EV charging experiments")
    sub = parser.add_subparsers(dest="command",required=True)
    p = sub.add_parser("demo",help="Run and verify the four-vehicle worked example")
    p.add_argument("--out",default="demo_results")
    p = sub.add_parser("benchmark",help="Run the synthetic experiment suite")
    p.add_argument("--out",default="results-rerun")
    p.add_argument("--sizes",nargs="+",type=int,default=[10,20,30])
    p.add_argument("--seeds",nargs="+",type=int,default=[0,1,2,3,4])
    p.add_argument("--repeats",type=int,default=3)
    p.add_argument("--time-limit",type=float,default=3.0)
    p = sub.add_parser("report",help="Regenerate charts and report from stored runs")
    p.add_argument("directory")
    p = sub.add_parser("solve",help="Solve a supplied instance JSON file")
    p.add_argument("instance")
    p.add_argument("--method",choices=["baseline","greedy","ilp"],default="ilp")
    p.add_argument("--time-limit",type=float,default=3.0)
    p.add_argument("--out",default="solution.json")
    args = parser.parse_args()
    from .experiment import run_benchmark, run_case, write_json
    from .data import teaching_example
    from .model import Instance
    from .solvers import SOLVERS
    from .verify import audit
    if args.command == "demo":
        path = Path(args.out)
        if path.exists() and any(path.iterdir()):
            parser.error("Choose an empty output directory")
        case = teaching_example(); case.save(path/"instance.json")
        records = run_case(case,repeats=1)
        write_json(path/"runs.json",records)
        for r in sorted(records,key=lambda x:x["method"]):
            print(f"{r['method']:10} cost={r['audit']['cost']:.2f} feasible={r['audit']['feasible']} status={r['status']}")
    elif args.command == "benchmark":
        from .reporting import build_report
        run_benchmark(args.out,args.sizes,args.seeds,args.repeats,args.time_limit)
        build_report(args.out)
        print(f"Report: {Path(args.out)/'report.html'}")
    elif args.command == "report":
        from .reporting import build_report
        build_report(args.directory)
    elif args.command == "solve":
        case = Instance.load(args.instance)
        solution = SOLVERS[args.method](case,time_limit=args.time_limit)
        result = {**solution.to_dict(),"audit":audit(case,solution.schedule)}
        write_json(args.out,result)
        print(json.dumps({"status":result["status"],"audit":result["audit"]},indent=2))


if __name__ == "__main__":
    main()
