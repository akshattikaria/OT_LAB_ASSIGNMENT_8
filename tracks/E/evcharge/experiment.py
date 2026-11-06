"""Reproducible benchmark runner. Every run and candidate is retained."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import sys
from time import perf_counter

import numpy as np
import scipy

from .data import SCENARIOS, generate, greedy_trap, infeasible_example, teaching_example
from .solvers import SOLVERS, integer_optimize
from .verify import audit


def write_json(path, data):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(data,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def environment():
    cpu_model = "unknown"
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text().splitlines():
            if line.startswith("model name"):
                cpu_model = line.split(":",1)[1].strip(); break
    quota = Path("/sys/fs/cgroup/cpu.max")
    return {"recorded_utc":datetime.now(timezone.utc).isoformat(),"python":sys.version,
            "numpy":np.__version__,"scipy":scipy.__version__,"platform":platform.platform(),
            "cpu_model":cpu_model,"logical_cpu_count":os.cpu_count(),
            "affinity_cpu_count":len(os.sched_getaffinity(0)) if hasattr(os,"sched_getaffinity") else None,
            "cgroup_cpu_max":quota.read_text().strip() if quota.exists() else None,
            "thread_environment":{k:os.environ.get(k) for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS")},
            "parallelism_note":"Sequential methods/runs; HiGHS internal threading not explicitly configured. No GPU used."}


def run_case(instance, repeats=3, time_limit=3):
    records = []
    for repeat in range(repeats):
        methods = list(SOLVERS)
        random.Random(f"{instance.name}/{repeat}").shuffle(methods)
        for position,method in enumerate(methods):
            start = perf_counter()
            solution = SOLVERS[method](instance,time_limit=time_limit)
            runtime = perf_counter()-start
            check_start = perf_counter()
            checked = audit(instance,solution.schedule)
            validation = perf_counter()-check_start
            if solution.status == "optimal" and not checked["feasible"]:
                raise AssertionError(f"Solver claimed optimal but independent check failed: {instance.name}: {checked}")
            objective = solution.details.get("objective")
            if checked["feasible"] and objective is not None and abs(objective-checked["cost"]) > 1e-5:
                raise AssertionError("Solver objective differs from independently recomputed cost")
            records.append({"instance":instance.name,"scenario":instance.metadata.get("scenario"),
                            "vehicles":len(instance.vehicles),"seed":instance.metadata.get("seed"),
                            "repeat":repeat,"method_order":position,"runtime_s":runtime,
                            "validation_s":validation,**solution.to_dict(),"audit":checked})
    return records


def run_benchmark(output, sizes=(10,20,30), seeds=(0,1,2,3,4), repeats=3, time_limit=3):
    if repeats < 1:
        raise ValueError("repeats must be >= 1")
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory is nonempty. Choose a new directory to preserve existing evidence.")
    output.mkdir(parents=True,exist_ok=True)
    write_json(output/"environment.json",environment())
    write_json(output/"protocol.json",{
        "sizes":list(sizes),"seeds":list(seeds),"repeats":repeats,"scenarios":list(SCENARIOS),
        "ilp_time_limit_s":time_limit,"ilp_relative_gap_target":0.0,
        "canonical_quality_repeat":0,"timing":"perf_counter around method incl. validation of inputs and model construction; independent audit excluded",
        "warmup":"One untimed tiny MILP solve before benchmarking",
        "comparisons":"Savings only on the same instance when both schedules pass the full audit. Optimum gaps require an optimal solver status.",
        "all_information":"All methods have the same complete arrival/departure/demand/tariff input; FCFS ignores price by design.",
        "generated_inputs":"All inputs synthetic; constructive feasibility witness is NOT passed to solvers.",
        "representative_plot":"First flexible instance with 20 vehicles, otherwise the first flexible instance; chosen before viewing savings."})
    integer_optimize(teaching_example(),time_limit=time_limit)
    cases = []
    for scenario in SCENARIOS:
        for n in sizes:
            for seed in seeds:
                case,witness = generate(n,seed,scenario)
                case.save(output/"instances"/f"{case.name}.json")
                write_json(output/"witnesses"/f"{case.name}.json",{"schedule":witness.tolist(),"audit":audit(case,witness)})
                cases.append(case)
    cases.extend((teaching_example(),teaching_example(flat=True),greedy_trap(),infeasible_example()))
    records = []
    for index,case in enumerate(cases,1):
        case.save(output/"instances"/f"{case.name}.json")
        records.extend(run_case(case,repeats,time_limit))
        print(f"[{index}/{len(cases)}] {case.name}",flush=True)
        # Checkpoint actual results so interrupted long runs retain measured evidence.
        write_json(output/"raw_runs.json",records)
    flat = []
    for r in records:
        row = {k:r[k] for k in ("instance","scenario","vehicles","seed","repeat","method_order","method","status","runtime_s","validation_s")}
        for k in ("feasible","cost","energy_kwh","required_kwh","unmet_kwh","missed_deadlines","peak_kw","max_capacity_excess_kw","outside_window_slots"):
            row[k] = r["audit"][k]
        row.update(mip_gap=r["details"].get("mip_gap"),dual_bound=r["details"].get("dual_bound"),
                   errors="; ".join(r["audit"]["errors"]))
        flat.append(row)
    with (output/"runs.csv").open("w",newline="",encoding="utf-8") as f:
        writer = csv.DictWriter(f,fieldnames=list(flat[0])); writer.writeheader(); writer.writerows(flat)
    hashes = {str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((output/"instances").glob("*.json"))}
    write_json(output/"input_sha256.json",hashes)
    return records


def summarize(records):
    canonical = [r for r in records if r["repeat"] == 0]
    by_instance = {}
    for r in canonical:
        by_instance.setdefault(r["instance"],{})[r["method"]] = r
    summary = []
    for scenario in SCENARIOS:
        cases = [rows for rows in by_instance.values() if rows["ilp"]["scenario"] == scenario]
        entry = {"scenario":scenario,"instances":len(cases),"methods":{},"comparisons":{}}
        for method in SOLVERS:
            runs = [r for r in records if r["scenario"] == scenario and r["method"] == method]
            medians = [statistics.median(r["runtime_s"] for r in runs if r["instance"] == c[method]["instance"]) for c in cases]
            entry["methods"][method] = {"feasible":sum(c[method]["audit"]["feasible"] for c in cases),
                                          "optimal":sum(c[method]["status"] == "optimal" for c in cases),
                                          "median_runtime_s":statistics.median(medians) if medians else None,
                                          "runtime_q1_s":float(np.percentile(medians,25)) if medians else None,
                                          "runtime_q3_s":float(np.percentile(medians,75)) if medians else None}
        for method in ("baseline","greedy"):
            paired = [c for c in cases if c[method]["audit"]["feasible"] and c["ilp"]["audit"]["feasible"] and c["ilp"]["status"] == "optimal"]
            savings = [100*(c[method]["audit"]["cost"]-c["ilp"]["audit"]["cost"])/c[method]["audit"]["cost"]
                       for c in paired if c[method]["audit"]["cost"] > 1e-9]
            entry["comparisons"][method] = {"paired_instances":len(paired),"positive_cost_pairs":len(savings),
                "mean_savings_pct":statistics.mean(savings) if savings else None,
                "sd_savings_pct":statistics.stdev(savings) if len(savings)>1 else 0.0 if savings else None,
                "min_savings_pct":min(savings) if savings else None,"max_savings_pct":max(savings) if savings else None,
                "values_pct":savings}
        summary.append(entry)
    return summary
