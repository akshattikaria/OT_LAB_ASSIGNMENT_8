"""Static, self-contained report and publication-style plots from recorded runs."""
from __future__ import annotations

import base64
import html
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np

from .data import SCENARIOS
from .experiment import summarize, write_json
from .model import Instance

LABELS = {"flexible":"Flexible windows", "flat_prices":"Flat prices", "tight_deadlines":"Tight deadlines",
          "limited_power":"Limited power", "mixed_power":"Mixed power"}
COLORS = {"baseline":"#6b7280","greedy":"#d28726","ilp":"#147d73"}


def overview_plot(summary,path):
    fig,axes = plt.subplots(3,1,figsize=(11,10),layout="constrained")
    fig.suptitle("EV charging experiment | synthetic data",fontsize=17,fontweight="bold")
    positions = np.arange(len(summary))
    for i,s in enumerate(summary):
        c = s["comparisons"]["baseline"]
        if c["mean_savings_pct"] is not None:
            axes[0].bar(i,c["mean_savings_pct"],color=COLORS["ilp"],width=.55,
                        yerr=c["sd_savings_pct"],capsize=4)
            axes[0].text(i,max(0,c["mean_savings_pct"]+c["sd_savings_pct"])+1.5,
                         f"n={c['paired_instances']}",ha="center",fontsize=10)
    axes[0].set(title="Cost reduction: proven-optimal ILP versus feasible baseline",
                ylabel="Mean reduction (%)",xticks=positions,xticklabels=[LABELS[s["scenario"]] for s in summary])
    axes[0].text(.99,.98,"Error bars: sample SD across matched instances",transform=axes[0].transAxes,
                 ha="right",va="top",fontsize=9,color="#555555")
    axes[0].margins(y=.25)
    width=.23
    for k,method in enumerate(("baseline","greedy","ilp")):
        rates = [100*s["methods"][method]["feasible"]/s["instances"] for s in summary]
        bars = axes[1].bar(positions+(k-1)*width,rates,width,label=method.upper(),color=COLORS[method])
        axes[1].bar_label(bars,labels=[f"{s['methods'][method]['feasible']}/{s['instances']}" for s in summary],fontsize=8,padding=3)
        times = [1000*s["methods"][method]["median_runtime_s"] for s in summary]
        axes[2].plot(positions,times,"o-",label=method.upper(),color=COLORS[method])
    axes[1].set(title="Full service and constraint feasibility",ylabel="Feasible instances (%)",ylim=(0,116),
                xticks=positions,xticklabels=[LABELS[s["scenario"]] for s in summary])
    axes[1].legend(loc="lower left",ncol=3,fontsize=9)
    axes[2].set(title="Computation cost on the recorded environment",ylabel="Median method time (ms, log scale)",
                xticks=positions,xticklabels=[LABELS[s["scenario"]] for s in summary],yscale="log")
    axes[2].legend(ncol=3,fontsize=9)
    for ax in axes:
        ax.grid(axis="y",alpha=.18); ax.set_axisbelow(True)
        ax.spines[["top","right"]].set_visible(False)
    fig.savefig(path,dpi=170); plt.close(fig)


def schedule_plot(output,records,path):
    names = sorted({r["instance"] for r in records if r["scenario"] == "flexible" and r["vehicles"] == 20})
    if not names:
        names = sorted({r["instance"] for r in records if r["scenario"] == "flexible"})
    name = names[0]
    case = Instance.load(output/"instances"/f"{name}.json")
    runs = {r["method"]:r for r in records if r["instance"] == name and r["repeat"] == 0}
    fig,axes = plt.subplots(4,1,figsize=(12,11),layout="constrained",gridspec_kw={"height_ratios":[2.2,2.2,1,1]})
    cmap = ListedColormap(["#ffffff","#e5e7eb","#147d73"])
    norm = BoundaryNorm([-.5,.5,1.5,2.5],3)
    hours = 8+np.arange(case.horizon+1)*case.slot_hours
    for ax,method in zip(axes[:2],("baseline","ilp")):
        r = runs[method]
        if r["schedule"] is None:
            ax.text(.5,.5,"No schedule returned",ha="center",transform=ax.transAxes)
            continue
        x = np.rint(np.array(r["schedule"]))
        mat = np.zeros_like(x)
        for i,v in enumerate(case.vehicles):
            mat[i,v.arrival:v.departure] = 1
        mat[x == 1] = 2
        ax.pcolormesh(hours,np.arange(len(case.vehicles)+1),mat,cmap=cmap,norm=norm,shading="flat")
        ax.set(yticks=np.arange(len(case.vehicles))+.5,yticklabels=[v.id for v in case.vehicles],ylabel="Vehicle",
               title=f"{method.upper()} | cost Rs {r['audit']['cost']:.2f} | feasible: {r['audit']['feasible']}")
        ax.tick_params(axis="y",labelsize=8)
        ax.invert_yaxis()
    for method in ("baseline","ilp"):
        load = runs[method]["audit"].get("load_kw")
        if load is not None:
            axes[2].stairs(load,hours,color=COLORS[method],label=method.upper(),linewidth=1.8)
    axes[2].stairs(case.capacity_kw,hours,color="#b64242",linestyle="--",label="Station limit")
    axes[2].set(ylabel="Power (kW)",title="Station load")
    axes[2].legend(ncol=3,fontsize=9)
    axes[3].stairs(case.prices,hours,color="#9b6c24",fill=True,alpha=.5)
    axes[3].set(ylabel="Price (Rs/kWh)",xlabel="Time of day",title="Fictional electricity tariff")
    for ax in axes:
        ax.set_xlim(hours[0],hours[-1]); ax.set_xticks(np.arange(8,21,2))
        ax.set_xticklabels([f"{h:02d}:00" for h in range(8,21,2)])
        ax.spines[["top","right"]].set_visible(False)
    fig.suptitle(f"Schedule example: {name}\nGreen: charging | grey: connected and idle | white: not connected",fontsize=13)
    fig.savefig(path,dpi=170); plt.close(fig)
    return name


def build_report(directory):
    output = Path(directory)
    records = json.loads((output/"raw_runs.json").read_text())
    protocol = json.loads((output/"protocol.json").read_text())
    env = json.loads((output/"environment.json").read_text())
    summary = summarize(records)
    write_json(output/"summary.json",summary)
    overview_plot(summary,output/"benchmark_overview.png")
    representative = schedule_plot(output,records,output/"schedule_example.png")
    main_instances = sum(s["instances"] for s in summary)
    canonical = [r for r in records if r["repeat"] == 0]
    main_ilp = [r for r in canonical if r["scenario"] in SCENARIOS and r["method"] == "ilp"]
    timed = [r for r in main_ilp if r["status"] == "time_limit_with_candidate"]
    solved = sum(r["status"] == "optimal" for r in main_ilp)
    lines = ["# Track E: EV Charging Schedule Optimization", "",
             "All sessions and tariffs in this report are synthetic. These are measured software experiment results, not field deployment savings.","",
             "## Problem and formulation", "",
             "Minimize electricity cost while giving every EV its required energy within its connection window and respecting per-EV fixed power and the station limit. Each vehicle has an assigned plug. Charging may pause and resume at slot boundaries.","",
             "Binary x[i,t] indicates whether EV i charges in slot t. Minimize sum(price[t] * power[i] * slot_hours * x[i,t]); require sum_t x[i,t] = required_slots[i], sum_i power[i] * x[i,t] <= capacity[t], and x[i,t] = 0 outside [arrival[i], departure[i]). See docs/FORMULATION.md for assumptions and strategy selection.","",
             "## Experimental protocol", "",
             f"{main_instances} main instances, plus 4 diagnostic controls; {protocol['repeats']} timing repetitions per method and instance; {len(records)} method runs in total. Fleet sizes: {protocol['sizes']}; seeds: {protocol['seeds']}. Main instances use 48 fifteen-minute slots (08:00-20:00).", "",
             "The baseline charges immediately with arrival-order priority. Greedy processes earlier departures first and reserves each EV's cheapest available slots. ILP considers all vehicles jointly. All methods receive the same full input. Inputs are not withheld to create a look-ahead advantage.", "",
             f"ILP uses SciPy/HiGHS with relative MIP gap target 0 and {protocol['ilp_time_limit_s']} s per solve. Timings include method execution and ILP model construction, exclude imports, plotting and independent checking, and follow one untimed solver warm-up. Method order is deterministically shuffled. Runtime summaries are medians across per-instance median repetition times.", "",
             "Quality/feasibility summaries use repetition 0, fixed in advance. All repetitions are retained in raw_runs.json and runs.csv. Savings compare matching feasible instances only and require an optimal ILP status. A failed heuristic's lower cost is not a saving. SD below describes variation across synthetic instances, not a confidence interval.", "",
             "## Results", "",
             "| Scenario | FCFS feasible | Greedy feasible | ILP feasible | ILP optimal | Paired FCFS cases | Mean cost reduction +/- SD |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for s in summary:
        c = s["comparisons"]["baseline"]
        saving = "n/a" if c["mean_savings_pct"] is None else f"{c['mean_savings_pct']:.2f}% +/- {c['sd_savings_pct']:.2f} pp"
        lines.append(f"| {LABELS[s['scenario']]} | {s['methods']['baseline']['feasible']}/{s['instances']} | {s['methods']['greedy']['feasible']}/{s['instances']} | {s['methods']['ilp']['feasible']}/{s['instances']} | {s['methods']['ilp']['optimal']}/{s['instances']} | {c['paired_instances']} | {saving} |")
    lines += ["", "| Scenario | Baseline median ms | Greedy median ms | ILP median ms | ILP reduction vs feasible greedy |",
              "|---|---:|---:|---:|---:|"]
    for s in summary:
        g = s["comparisons"]["greedy"]
        gap = "n/a" if g["mean_savings_pct"] is None else f"{g['mean_savings_pct']:.2f}% (n={g['paired_instances']})"
        times = [1000*s["methods"][m]["median_runtime_s"] for m in ("baseline","greedy","ilp")]
        lines.append(f"| {LABELS[s['scenario']]} | {times[0]:.3f} | {times[1]:.3f} | {times[2]:.3f} | {gap} |")
    lines += ["", f"ILP certified {solved}/{main_instances} main instances as optimal. {len(timed)} reached the time limit with a candidate; these candidates passed the independent schedule audit. They are included in feasibility and runtime counts, but excluded from the proven-optimum savings comparisons above. This conditional comparison must not be presented as savings over all instances.", "",
              "![Benchmark overview](benchmark_overview.png)", "", "## Interpretation", "",
              "Flexible connection windows allow demand to move into cheaper periods. Flat tariffs remove this cost-shifting opportunity: any fully served schedule costs the same when per-vehicle energy is fixed. Tight deadlines reduce freedom. Restricted station power creates competition for the cheap slots. Mixed charger powers introduce discrete packing choices.", "",
              "Greedy can be fast and competitive, but has no feasibility or optimality guarantee for this formulation. ILP returns an optimum only when it proves the requested gap within the time limit. A time-limited candidate must still pass the independent audit; an infeasible status is different from running out of time.", "",
              "## Diagnostic controls", "",
              "| Control | Method | Status | Feasible | Delivered kWh | Unmet kWh | Actual cost Rs |",
              "|---|---|---|---|---:|---:|---:|"]
    for r in canonical:
        if r["scenario"] in SCENARIOS:
            continue
        a = r["audit"]
        def fmt(v): return "n/a" if v is None else f"{v:.2f}"
        lines.append(f"| {r['instance']} | {r['method']} | {r['status']} | {a['feasible']} | {fmt(a['energy_kwh'])} | {fmt(a['unmet_kwh'])} | {fmt(a['cost'])} |")
    lines += ["", "The teaching examples and greedy trap use one-hour slots for hand calculation; the overload control uses fifteen-minute slots. The deliberately infeasible capacity control needs six charging slots but has room for four. The greedy-trap control is feasible: reserving the cheapest slot for an earlier-departing flexible vehicle blocks a later vehicle's scarce window. These are designed algorithm controls, not fabricated AI mistakes.", "",
              "## Correctness and reproducibility", "",
              "An independent checker recomputes cost and energy from the returned schedule and input, checks binary values, availability, exact demand and slotwise station power. It does not use the solver constraint matrix or trust solver status. Exhaustive enumeration checks the integer model on 80 seeded small random cases and analytic examples. The 29-test suite also exercises malformed inputs, fractional schedules, deadline boundaries and infeasible cases.", "",
              "Every generated main instance has an audited feasibility witness, saved separately and never supplied to any solver. Generation can retry up to 100 times and records the successful attempt. This intentionally selects feasible workloads; it is not an unbiased sample of real charging demand. Inputs have SHA-256 hashes. Seeds reproduce datasets; solver ties and timing may vary by system/version.", "",
              "## Representative schedule", "", f"Preselected case: {representative}.", "",
              "![Schedule example](schedule_example.png)", "",
              "## Limitations and next steps", "",
              "This is an offline, synthetic, fixed-rate, preemptive charging model with an assigned plug per vehicle. Energy is specified as an integer number of charging slots; no physical energy request is silently rounded. Tariffs are fictional. The model excludes forecast error, battery tapering/degradation, charging losses, user price response, vehicle movement and plug queues. Peak power is measured and capped, not minimized. No claim of real station savings or deployment readiness is made.", "",
              "With identical powers and integral per-slot capacity in charger units, this model has a bipartite assignment/min-cost-flow structure; binary variables alone do not make that restricted case hard. Heterogeneous rates remove that simple unit-capacity interpretation. Solver scaling observations should be limited to these tested instances.", "",
              "A next study could add public charging-session data, explicitly mapped demand and tariff assumptions, or rolling-horizon decisions with uncertain departures. Extra constraints and finer slots increase computational work. Full Assignment 8 still needs Tracks A-D and F-J, the full Chapter 6 checklist, a second AI-tool comparison, genuine failure records, public repository publication and the demonstration.", "",
              "## Environment", "", f"- Recorded UTC: {env['recorded_utc']}", f"- Python: {env['python'].splitlines()[0]}",
              f"- NumPy {env['numpy']}, SciPy {env['scipy']}", f"- CPU: {env['cpu_model']}",
              f"- Logical/affinity CPU counts: {env['logical_cpu_count']}/{env['affinity_cpu_count']}; cgroup cpu.max: {env['cgroup_cpu_max']}",
              f"- {env['parallelism_note']}", "",
              "## Sources", "",
              "- Supplied Assignment 8 brief: main-process case study, comparison and reproducibility requirements.",
              "- Supplied Chapter 6 PPT1: greedy/ILP; PPT4: strategy selection.",
              "- SciPy milp reference: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html (accessed 2026-10-31). Installed version is recorded above.",
              "- ACN-Data (candidate future real-data source; not used in these results): https://ev.caltech.edu/dataset", ""]
    markdown = "\n".join(lines)
    (output/"REPORT.md").write_text(markdown,encoding="utf-8")
    # Small Markdown-to-HTML renderer for the controlled report grammar, with no dependency or CDN.
    parts=[]; table=[]; paragraph=[]
    def flush_paragraph():
        if paragraph:
            parts.append("<p>"+html.escape(" ".join(paragraph))+"</p>"); paragraph.clear()
    def flush_table():
        if not table:return
        head = [s.strip() for s in table[0].strip("|").split("|")]
        content = "<div class='table-wrap'><table><thead><tr>"+"".join("<th>"+html.escape(c)+"</th>" for c in head)+"</tr></thead><tbody>"
        for line in table[2:]:
            content += "<tr>"+"".join("<td>"+html.escape(c.strip())+"</td>" for c in line.strip("|").split("|"))+"</tr>"
        parts.append(content+"</tbody></table></div>");table.clear()
    for line in lines:
        if line.startswith("|"):
            flush_paragraph();table.append(line);continue
        flush_table()
        if not line:
            flush_paragraph();continue
        if line.startswith("#"):
            flush_paragraph();level=len(line)-len(line.lstrip("#"))
            parts.append(f"<h{level}>"+html.escape(line[level:].strip())+f"</h{level}>")
        elif line.startswith("!["):
            flush_paragraph();name=line.split("](",1)[1][:-1];alt=line[2:].split("]",1)[0]
            encoded=base64.b64encode((output/name).read_bytes()).decode()
            parts.append(f"<img alt='{html.escape(alt)}' src='data:image/png;base64,{encoded}'>")
        elif line.startswith("- "):
            flush_paragraph();parts.append("<p class='detail'>"+html.escape(line[2:])+"</p>")
        else:paragraph.append(line)
    flush_paragraph();flush_table()
    doc = "<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Track E experiment report</title><style>body{font:16px/1.6 system-ui,sans-serif;color:#172b35;max-width:1080px;margin:40px auto;padding:0 24px}h1{font-size:32px;line-height:1.2}h2{font-size:22px;border-bottom:1px solid #d9e2e6;padding-top:18px;padding-bottom:6px}p{max-width:95ch}table{border-collapse:collapse;font-size:13px;width:100%}th,td{padding:9px;border-bottom:1px solid #d9e2e6;text-align:left}th{background:#eff6f5}img{max-width:100%;height:auto}.table-wrap{overflow:auto}.detail{margin:3px 0}@media print{body{margin:0;font-size:11px}h2{break-after:avoid}img,tr{break-inside:avoid}}</style><main>"+"\n".join(parts)+"</main></html>"
    (output/"report.html").write_text(doc,encoding="utf-8")
    return summary
