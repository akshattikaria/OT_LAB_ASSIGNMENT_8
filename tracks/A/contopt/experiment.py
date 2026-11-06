"""Independent tuning, repeated evaluation, complete traces and environment records."""
from __future__ import annotations

from datetime import datetime,timezone
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import sys

import numpy as np
import scipy

from .checks import audit_run,finite_gradient,relative_error
from .optimizers import FIRST_ORDER,SECOND_ORDER,train
from .problems import make_dataset
from .supplement import run_supplements

RATES={
 "ridge":{
  "GD":[.005,.015,.04,.08],"SGD":[.0003,.001,.003,.01],"MiniBatchSGD":[.001,.003,.01,.03],
  "Momentum":[.0005,.002,.008,.02],"NAG":[.0005,.002,.008,.02],"AdaGrad":[.01,.05,.2,.8],
  "RMSProp":[.0005,.002,.008,.03],"Adam":[.001,.005,.02,.08]},
 "mlp":{
  "GD":[.03,.1,.3,1.0],"SGD":[.001,.005,.02,.08],"MiniBatchSGD":[.01,.03,.1,.3],
  "Momentum":[.001,.005,.02,.08],"NAG":[.001,.005,.02,.08],"AdaGrad":[.01,.05,.2,.8],
  "RMSProp":[.001,.005,.02,.08],"Adam":[.001,.005,.02,.08]}}


def write_json(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def environment():
    model="unknown";cpuinfo=Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text().splitlines():
            if line.startswith("model name"):model=line.split(":",1)[1].strip();break
    quota=Path("/sys/fs/cgroup/cpu.max")
    return {"utc":datetime.now(timezone.utc).isoformat(),"python":sys.version,"numpy":np.__version__,
            "scipy":scipy.__version__,"platform":platform.platform(),"cpu":model,"logical_cpus":os.cpu_count(),
            "affinity_cpus":len(os.sched_getaffinity(0)) if hasattr(os,"sched_getaffinity") else None,
            "cpu_quota":quota.read_text().strip() if quota.exists() else None,
            "thread_env":{key:os.environ.get(key) for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS")},
            "note":"Sequential CPU experiments, no GPU, numerical-library threading not explicitly controlled."}


def save_dataset(output,kind,seed,n):
    problem,w,Xtest,ytest=make_dataset(kind,seed,n)
    folder=output/"datasets";folder.mkdir(exist_ok=True)
    np.savez_compressed(folder/f"{kind}_seed{seed}.npz",X=problem.X,y=problem.y,initial=w,Xtest=Xtest,ytest=ytest)
    write_json(folder/f"{kind}_seed{seed}.json",{"kind":kind,"seed":seed,"n":n,"dimension":problem.d,
        "l2":problem.l2,"source":"synthetic","role":"tuning" if seed==999 else "evaluation",
        "problem":"ridge regression" if kind=="ridge" else "XOR classification, 2-8-1 tanh/logit network"})
    return problem,w,Xtest,ytest


def tuning(output,kind,epochs,n):
    problem,w,_,_=save_dataset(output,kind,999,n)
    runs=[];selected={}
    for method in FIRST_ORDER:
        candidates=[]
        for lr in RATES[kind][method]:
            result=train(problem,w,method,lr,epochs=epochs,seed=20999)
            result["audit"]=audit_run(problem,result)
            if not result["audit"]["valid"]:raise AssertionError(result["audit"])
            runs.append(result)
            score=result["final_objective"] if result["status"] not in ("diverged","line_search_failed") else np.inf
            candidates.append((score,lr))
        score,choice=min(candidates)
        if not np.isfinite(score):raise RuntimeError(f"All tuning candidates failed for {kind}/{method}")
        selected[method]=choice
    write_json(output/f"tuning_{kind}.json",{"kind":kind,"seed":999,"criterion":"lowest final training objective on independent tuning instance; no evaluation/test input used",
        "candidates_per_first_order_method":4,"epochs_per_candidate":epochs,"selected":selected,"runs":runs})
    return selected


def run_benchmark(directory,seeds=(0,1,2,3,4),repeats=3,ridge_epochs=35,mlp_epochs=80,n=256):
    if not seeds or 999 in seeds:raise ValueError("Nonempty evaluation seeds must exclude tuning seed 999")
    if len(set(seeds))!=len(seeds):raise ValueError("Seeds must be unique")
    if not isinstance(repeats,int) or repeats<1:raise ValueError("Positive integer repeats required")
    if not isinstance(n,int) or n<8:raise ValueError("n must be an integer >= 8")
    output=Path(directory)
    if output.exists() and any(output.iterdir()):raise ValueError("Choose a new empty output directory")
    output.mkdir(parents=True,exist_ok=True)
    write_json(output/"environment.json",environment())
    protocol={"seeds":list(seeds),"repeats":repeats,"tuning_seed":999,"n_train":n,"n_test":256,
        "ridge_epochs":ridge_epochs,"mlp_epochs":mlp_epochs,"batch_size":32,"full_gradient_tolerance":1e-7,
        "rates":RATES,"quality_repeat":0,"early_stop":"Full training gradient checked at epoch boundaries; stationary does not imply global optimum for non-convex problems",
        "work":"Same maximum epochs for all methods within a problem. One epoch is n sampled-gradient examples for first-order methods. Hessian/Jacobian calls are extra and reported separately; not equal-FLOP budgets.",
        "timing":"perf_counter includes updates, line search, counters and full epoch diagnostics; excludes data generation, tuning, independent audits, test metrics, plotting and imports",
        "repetition":"Data, initial state, batch permutation seed and learning rate fixed across timing repeats; quality uses repeat 0, never best repeat",
        "method_order":"Deterministically shuffled within each problem/seed/repeat",
        "warmup":"One untimed small first-order update on each problem family",
        "test_data":"Test metrics reported only after training; never used for candidate selection",
        "reference":"Ridge: independently augmented least-squares solution. MLP: no known global optimum; objective and accuracy only."}
    write_json(output/"protocol.json",protocol)
    results=[]
    for kind,epochs in (("ridge",ridge_epochs),("mlp",mlp_epochs)):
        warm,w,_,_=make_dataset(kind,123,n);train(warm,w,"Adam",.01,epochs=1)
        print(f"Tuning {kind}: 8 methods x 4 rates on seed 999",flush=True)
        selected=tuning(output,kind,epochs,n)
        print(f"Chosen {kind} rates: {selected}",flush=True)
        methods=list(FIRST_ORDER)+(list(SECOND_ORDER) if kind=="ridge" else [])
        for seed in seeds:
            problem,initial,Xtest,ytest=save_dataset(output,kind,seed,n)
            reference=problem.value(problem.reference()) if kind=="ridge" else None
            for repeat in range(repeats):
                order=methods.copy();random.Random(f"{kind}/{seed}/{repeat}").shuffle(order)
                for position,method in enumerate(order):
                    result=train(problem,initial,method,selected.get(method,1.0),epochs=epochs,seed=seed+20000)
                    result.update(problem=kind,seed=seed,repeat=repeat,method_order=position,
                        initial_objective=problem.value(initial),reference_objective=reference)
                    result["audit"]=audit_run(problem,result)
                    if not result["audit"]["valid"]:raise AssertionError(result["audit"])
                    theta=np.asarray(result["theta"])
                    result["test_accuracy"]=problem.accuracy(theta,Xtest,ytest) if kind=="mlp" else None
                    result["test_mse"]=float(np.mean((Xtest@theta-ytest)**2)) if kind=="ridge" else None
                    result["reference_gap"]=result["final_objective"]-reference if reference is not None else None
                    results.append(result)
            print(f"Completed {kind}, seed {seed}",flush=True)
            write_json(output/"raw_runs.json",results)
    print("Running landscape, curvature, nonlinear-fit, noise and regularization controls",flush=True)
    supplements=run_supplements();write_json(output/"supplementary.json",supplements)
    flat=[]
    for r in results:
        row={k:r[k] for k in ("problem","seed","repeat","method_order","method","lr","status","runtime_s","initial_objective","final_objective","final_grad_norm","reference_gap","test_accuracy","test_mse","epochs_completed")}
        row.update(r["counts"]);row["audit_valid"]=r["audit"]["valid"];flat.append(row)
    with (output/"runs.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    write_json(output/"dataset_sha256.json",{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((output/"datasets").iterdir())})
    write_json(output/"summary.json",summarize(results))
    return results


def summarize(runs):
    rows=[]
    for kind in ("ridge","mlp"):
        for method in FIRST_ORDER+(SECOND_ORDER if kind=="ridge" else ()):
            all_runs=[r for r in runs if r["problem"]==kind and r["method"]==method]
            canonical=[r for r in all_runs if r["repeat"]==0]
            usable=[r for r in canonical if r["status"] not in ("diverged","line_search_failed") and r["audit"]["valid"]]
            if not canonical:continue
            runtime=[statistics.median(q["runtime_s"] for q in all_runs if q["seed"]==r["seed"]) for r in canonical]
            row={"problem":kind,"method":method,"instances":len(canonical),"usable":len(usable),
                 "diverged":sum(r["status"]=="diverged" for r in canonical),"lr":canonical[0]["lr"],
                 "median_runtime_s":statistics.median(runtime),"runtime_q1_s":float(np.percentile(runtime,25)),"runtime_q3_s":float(np.percentile(runtime,75))}
            for key in ("final_objective","final_grad_norm","reference_gap","test_accuracy","test_mse"):
                values=[r[key] for r in usable if r[key] is not None]
                row[key+"_mean"]=statistics.mean(values) if values else None
                row[key+"_sd"]=statistics.stdev(values) if len(values)>1 else 0.0 if values else None
            row["mean_updates"]=statistics.mean(r["counts"]["updates"] for r in canonical)
            row["mean_derivative_passes"]=statistics.mean(r["trace"][-1]["data_derivative_passes"] for r in canonical)
            row["mean_hessian_calls"]=statistics.mean(r["counts"]["hessian_calls"] for r in canonical)
            row["mean_jacobian_calls"]=statistics.mean(r["counts"]["jacobian_calls"] for r in canonical)
            rows.append(row)
    return rows
