"""Scientific figures and a self-contained report from the saved experiments."""
from __future__ import annotations

import base64
import html
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .experiment import summarize,write_json
from .optimizers import FIRST_ORDER,SECOND_ORDER

METHODS=FIRST_ORDER+SECOND_ORDER
COLORS={m:plt.get_cmap("tab10")(i) for i,m in enumerate(METHODS)}


def style(ax):
    ax.grid(alpha=.18);ax.set_axisbelow(True);ax.spines[["top","right"]].set_visible(False)


def comparison_plot(output,runs,summary,protocol):
    fig,axes=plt.subplots(2,2,figsize=(13,9),layout="constrained")
    handles=[];labels=[]
    for ax,kind,epochs in ((axes[0,0],"ridge",protocol["ridge_epochs"]),(axes[0,1],"mlp",protocol["mlp_epochs"])):
        for method in METHODS:
            rr=[r for r in runs if r["problem"]==kind and r["method"]==method and r["repeat"]==0]
            if not rr:continue
            grid=np.linspace(0,epochs,epochs+1);ys=[]
            for r in rr:
                x=[p["data_derivative_passes"] for p in r["trace"]]
                y=[p["objective"]-(r["reference_objective"] or 0) for p in r["trace"]]
                ys.append(np.interp(grid,x,y))
            values=np.array(ys);mean=np.median(values,axis=0);low,high=np.percentile(values,[25,75],axis=0)
            line,=ax.plot(grid,np.maximum(mean,1e-16),label=method,color=COLORS[method],linewidth=1.7)
            ax.fill_between(grid,np.maximum(low,1e-16),np.maximum(high,1e-16),color=COLORS[method],alpha=.08)
            if kind=="ridge":handles.append(line);labels.append(method)
        ax.set(xlabel="Data derivative passes (diagnostics excluded)",ylabel="Training objective gap" if kind=="ridge" else "Training objective",
               title="Strongly convex ridge regression" if kind=="ridge" else "Non-convex neural-network training")
        if kind=="ridge":ax.set_yscale("log")
        style(ax)
    ridge=[s for s in summary if s["problem"]=="ridge"]
    x=np.arange(len(ridge));times=[s["median_runtime_s"]*1000 for s in ridge]
    axes[1,0].bar(x,times,color=[COLORS[s["method"]] for s in ridge])
    axes[1,0].set(xticks=x,xticklabels=[s["method"] for s in ridge],yscale="log",ylabel="Median runtime (ms, log scale)",title="Ridge: time includes updates and diagnostics")
    axes[1,0].tick_params(axis="x",rotation=45);style(axes[1,0])
    nn=[s for s in summary if s["problem"]=="mlp"];x=np.arange(len(nn))
    axes[1,1].bar(x,[100*s["test_accuracy_mean"] for s in nn],yerr=[100*s["test_accuracy_sd"] for s in nn],capsize=3,color=[COLORS[s["method"]] for s in nn])
    axes[1,1].set(xticks=x,xticklabels=[s["method"] for s in nn],ylabel="Test accuracy (%)",ylim=(0,105),title="Neural network: mean +/- SD across data seeds")
    axes[1,1].tick_params(axis="x",rotation=45);style(axes[1,1])
    fig.legend(handles,labels,loc="outside lower center",ncol=5,fontsize=9)
    fig.suptitle("Track A | synthetic data | independently selected learning rates",fontsize=16)
    fig.savefig(output/"optimizer_comparison.png",dpi=160);plt.close(fig)


def landscape_plot(output,data):
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout="constrained")
    for ax,key,title in ((axes[0,0],"convex_smooth","Convex smooth, not globally strongly convex"),(axes[0,1],"strongly_convex","Strongly convex quadratic")):
        rr=data[key];k=[r["k"] for r in rr]
        ax.semilogy(k,np.maximum([r["gap"] for r in rr],1e-20),label="Measured gap")
        ax.semilogy([r["k"] for r in rr if r["bound"] is not None],[r["bound"] for r in rr if r["bound"] is not None],"--",label="Applicable upper bound")
        ax.set(title=title,xlabel="GD iterations",ylabel="Objective gap");ax.legend(fontsize=9);style(ax)
    for r in data["double_well"]:
        axes[1,0].plot([p["k"] for p in r["trace"]],[p["objective"] for p in r["trace"]],label=f"Start x={r['initial']:g}")
    global_min=min(p["objective"] for p in data["stationary_points"] if p["hessian"]>0)
    axes[1,0].axhline(global_min,linestyle="--",color="#6b7280",label="Global minimum value")
    axes[1,0].set(title="Tilted double well: different local minima",xlabel="GD iterations",ylabel="Objective");axes[1,0].set_ylim(-.13,.5)
    axes[1,0].legend(fontsize=9);style(axes[1,0])
    for r in data["saddle"]:
        axes[1,1].plot([p["k"] for p in r["trace"]],[p["objective"] for p in r["trace"]],label=f"Initial y={r['initial_y']:g}")
    axes[1,1].set(title="A saddle can trap an unperturbed trajectory",xlabel="GD iterations",ylabel="Objective")
    axes[1,1].legend(fontsize=9);style(axes[1,1])
    fig.suptitle("Landscape controls and convergence bounds",fontsize=16)
    fig.savefig(output/"landscape_controls.png",dpi=160);plt.close(fig)


def noise_plot(output,supplements):
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout="constrained")
    ax=axes[0,0]
    for r in supplements["landscapes"]["learning_rate"]:
        ax.semilogy([p["k"] for p in r["trace"]],np.maximum([p["objective"] for p in r["trace"]],1e-20),"o-",label=f"eta={r['lr']:g}",markersize=3)
    ax.set(title="Learning-rate control: f(w)=(w-3)^2",xlabel="GD iterations",ylabel="Objective gap (zero floored for display)");ax.legend(fontsize=9);style(ax)
    records=supplements["noise"]["runs"]
    for ax,sigma in zip((axes[0,1],axes[1,0],axes[1,1]),(0.0,.1,.5)):
        for method in ("GD_constant","GD_decay","Momentum","Adam"):
            rr=[r for r in records if r["sigma"]==sigma and r["method"]==method]
            arr=np.array([[p["true_objective"] for p in r["trace"]] for r in rr]);k=[p["k"] for p in rr[0]["trace"]]
            mean=np.median(arr,axis=0);low,high=np.percentile(arr,[25,75],axis=0)
            line,=ax.semilogy(k,np.maximum(mean,1e-20),label=method)
            ax.fill_between(k,np.maximum(low,1e-20),np.maximum(high,1e-20),alpha=.08,color=line.get_color())
        ax.set(title=f"Additive oracle noise: sigma={sigma:g}",xlabel="Gradient queries",ylabel="True objective gap");ax.legend(fontsize=8);style(ax)
    fig.suptitle("Step-size sensitivity and noise floors | 10 noise seeds",fontsize=16)
    fig.savefig(output/"tuning_and_noise.png",dpi=160);plt.close(fig)


def curvature_plot(output,data):
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout="constrained")
    for r in data["curvature"]["runs"]:
        axes[0].plot([p["k"] for p in r["trace"]],[p["objective"] for p in r["trace"]],"o-",label=r["method"],markersize=3)
    axes[0].set(title="Logistic curvature approximations",xlabel="Optimization updates",ylabel="Regularized objective");axes[0].legend(fontsize=8);style(axes[0])
    for r in data["nonlinear_fit"]["runs"]:
        axes[1].semilogy([p["epoch"] for p in r["trace"]],[p["objective"] for p in r["trace"]],"o-",label=r["method"],markersize=3)
    axes[1].axhline(data["nonlinear_fit"]["reference"]["objective"],linestyle="--",color="#6b7280",label="SciPy least-squares reference")
    axes[1].set(title="Nonlinear exponential fit",xlabel="Optimization updates",ylabel="Half mean squared residual");axes[1].legend(fontsize=8);style(axes[1])
    fig.savefig(output/"curvature_and_fit.png",dpi=160);plt.close(fig)


def render_markdown(lines,output):
    parts=[];paragraph=[];table=[]
    def flush_p():
        if paragraph:parts.append("<p>"+html.escape(" ".join(paragraph))+"</p>");paragraph.clear()
    def flush_t():
        if not table:return
        heads=[x.strip() for x in table[0].strip("|").split("|")]
        body="<div class='table-wrap'><table><thead><tr>"+"".join("<th>"+html.escape(x)+"</th>" for x in heads)+"</tr></thead><tbody>"
        for row in table[2:]:body+="<tr>"+"".join("<td>"+html.escape(x.strip())+"</td>" for x in row.strip("|").split("|"))+"</tr>"
        parts.append(body+"</tbody></table></div>");table.clear()
    for line in lines:
        if line.startswith("|"):flush_p();table.append(line);continue
        flush_t()
        if not line:flush_p();continue
        if line.startswith("#"):
            flush_p();level=len(line)-len(line.lstrip("#"));parts.append(f"<h{level}>"+html.escape(line[level:].strip())+f"</h{level}>")
        elif line.startswith("!["):
            flush_p();alt=line[2:].split("]",1)[0];name=line.split("](",1)[1][:-1]
            encoded=base64.b64encode((output/name).read_bytes()).decode();parts.append(f"<img alt='{html.escape(alt)}' src='data:image/png;base64,{encoded}'>")
        else:paragraph.append(line)
    flush_p();flush_t()
    return "<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Track A continuous optimization</title><style>body{font:16px/1.6 system-ui,sans-serif;color:#162b35;max-width:1080px;margin:40px auto;padding:0 24px}h1{font-size:32px;line-height:1.2}h2{font-size:23px;border-bottom:1px solid #d7e2e5;padding:18px 0 6px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:8px;border-bottom:1px solid #d7e2e5;text-align:left}th{background:#eff5f5}.table-wrap{overflow:auto}img{max-width:100%;height:auto}@media print{body{font-size:11px;margin:0}h2{break-after:avoid}tr,img{break-inside:avoid}}</style><main>"+"\n".join(parts)+"</main></html>"


def build_report(directory):
    output=Path(directory);runs=json.loads((output/"raw_runs.json").read_text());protocol=json.loads((output/"protocol.json").read_text())
    data=json.loads((output/"supplementary.json").read_text());env=json.loads((output/"environment.json").read_text())
    summary=summarize(runs);write_json(output/"summary.json",summary)
    comparison_plot(output,runs,summary,protocol);landscape_plot(output,data["landscapes"])
    noise_plot(output,data);curvature_plot(output,data)
    L=["# Track A: Continuous Optimization", "",
       "Measured software experiments on synthetic data. Implementations, derivatives, tuning and diagnostics are reproducible; no global-optimality claim is made for the neural network.", "",
       "## Problems and mathematical formulation", "",
       "Ridge regression: minimize F(w) = ||Xw-y||^2/(2n) + lambda*||w||^2/2 over unconstrained real weights. The 8-parameter problem is strongly convex with lambda=0.01. An augmented linear least-squares solution independently supplies the optimum.", "",
       "Neural classification: minimize mean binary cross-entropy + 0.001*||theta||^2/2. A 2-8-1 tanh/logit network has 33 trainable parameters including biases, all regularized. Inputs and XOR labels are synthetic. Backpropagation computes the gradient; the optimizer separately chooses the update.", "",
       "## Protocol and fair comparison", "",
       f"Training size {protocol['n_train']}, test size 256, evaluation seeds {protocol['seeds']}, timing repetitions {protocol['repeats']}. Ridge budget: {protocol['ridge_epochs']} epochs; neural budget: {protocol['mlp_epochs']} epochs. Full-gradient stationarity tolerance: 1e-7, checked once per epoch. There are {len(runs)} main training runs.", "",
       "Each first-order method receives four candidate learning rates on separate tuning seed 999 with the same per-problem epoch budget. Candidate selection minimizes that independent tuning problem's training objective. Evaluation and test data never choose the learning rate. All 64 tuning candidates and selected settings are retained. Newton/Gauss-Newton use prescribed curvature safeguarding and Armijo backtracking, not an extra tuning search.", "",
       "GD uses the full training set per update, SGD one shuffled sample, and mini-batch SGD/Momentum/NAG/AdaGrad/RMSProp/Adam up to 32 shuffled samples. One first-order epoch evaluates n sample gradients, but methods perform different numbers of updates. Newton also computes a full Hessian; Gauss-Newton computes full residuals/Jacobians. These are not equal-FLOP budgets. Update counts, derivative work and runtime must be considered together.", "",
       "The same data and initial weights are used across methods for each seed; stochastic permutations are reproducible. Method order is shuffled deterministically for timing. Imports, data generation, tuning and independent audits are outside the main timer; epoch diagnostics are inside. CPU/numerical-library threading is not controlled. Runtime summaries are medians over per-seed median timing repeats. Quality uses repeat 0, never the best repeat.", "",
       "## Main results", "",
       "| Problem | Method | Chosen rate | Usable seeds | Mean objective +/- SD | Mean gap to ridge optimum | Mean test accuracy | Median ms |",
       "|---|---|---:|---:|---:|---:|---:|---:|"]
    def fmt(x):return "n/a" if x is None else f"{x:.6g}"
    for s in summary:
        accuracy="n/a" if s["test_accuracy_mean"] is None else f"{100*s['test_accuracy_mean']:.2f}% +/- {100*s['test_accuracy_sd']:.2f} pp"
        L.append(f"| {s['problem']} | {s['method']} | {s['lr']:g} | {s['usable']}/{s['instances']} | {fmt(s['final_objective_mean'])} +/- {fmt(s['final_objective_sd'])} | {fmt(s['reference_gap_mean'])} | {accuracy} | {1000*s['median_runtime_s']:.3f} |")
    L += ["", "![Optimizer comparison](optimizer_comparison.png)", "",
          "Convergence curves show medians and shaded interquartile ranges across data seeds; neural accuracy bars use means and sample SD. For display only, stopped trajectories are held at their final value and near-zero ridge gaps are floored at 1e-16. The horizontal work coordinate counts sample-gradient passes plus full Hessian/Jacobian evaluations, excluding diagnostics; it is an accounting proxy, not a FLOP-equivalence claim. Raw main benchmark values are unchanged.", "",
          "Ridge Newton and Gauss-Newton coincide because the residual model is linear and its J-transpose-J is the exact Hessian, including regularization. A small iteration count can still involve more work per iteration. SGD's many inexpensive updates and a full-batch GD update have different overhead. Adaptive methods can retain a residual error at a fixed rate. The neural results concern this small dataset and budget, and establish no universal optimizer ranking.", "",
          "## Work and resource accounting", "",
          "| Problem | Method | Mean updates | Mean derivative passes | Hessian calls | Jacobian calls |",
          "|---|---|---:|---:|---:|---:|"]
    for s in summary:L.append(f"| {s['problem']} | {s['method']} | {s['mean_updates']:.1f} | {s['mean_derivative_passes']:.1f} | {s['mean_hessian_calls']:.1f} | {s['mean_jacobian_calls']:.1f} |")
    L += ["", "An explicit dense d-by-d Hessian uses d^2 numbers; a diagonal approximation d; a rank-k representation O(d*k) plus a diagonal floor. The small low-rank demonstration constructs a full Hessian and eigendecomposes it, so it does not demonstrate a memory-saving implementation. The matrix-free HVP/CG path avoids materializing a Hessian during its updates. Measured peak resident memory is not reported; only structural storage counts are claimed.", "",
          "## Backpropagation and derivative verification", "",
          "The hand-coded chain rule differentiates the output logit, the tanh activation, and the input/hidden/output parameters. The derivative is tested for every one of the 33 parameters against central finite differences, both on full data and a mini-batch. Each main run independently recomputes final objective and gradient norm and compares its final gradient with numerical differentiation. Relative-error normalization uses max(1, norm(analytic), norm(numeric)).", "",
          f"Largest final-gradient check error across main runs: {max(r['audit']['finite_difference_gradient_relative_error'] for r in runs):.3e}. Test cases also verify the explicit first and second optimizer updates, Newton/Gauss-Newton against closed-form solutions, batch averaging, unstable steps and false result claims.", "",
          "## Landscapes and convergence", "",
          "The convex control f(x)=sqrt(1+x^2)-1 is globally 1-smooth and not globally strongly convex. With step 1, measured gaps are checked against ||x0-x*||^2/(2k). The strongly convex quadratic has mu=1, L=10; with step 1/L its gaps satisfy the conservative geometric bound f0*(1-mu/L)^k. These experiments check valid upper bounds, not exact asymptotic-rate estimates.", "",
          "A tilted double well, f(x)=(x^2-1)^2+0.1x, has two unequal local minima. Cubic derivative roots and Hessian signs identify them; GD from opposite starts reaches different minima. The bounded-below saddle example f(x,y)=0.5*x^2+(y^2-1)^2 has Hessian eigenvalues -4 and +1 at the origin. A trajectory with y=0 approaches the saddle; a perturbed y escapes. A zero gradient alone does not establish a minimum.", "",
          "The neural loss is non-convex. Full-gradient stationarity would not prove a global minimum. Smoothness/step-size assumptions supporting the convex controls are not automatically imposed on the neural model or transferred to Adam/noisy updates.", "",
          "![Landscape controls](landscape_controls.png)", "",
          "## Step-size sensitivity and noisy objectives", "",
          "For (w-3)^2, error is multiplied by 1-2*eta. The recorded rates 0.1, 0.5, 1 and 1.1 show contraction, a one-step solution, oscillation and divergence. A separate noisy oracle adds zero-mean Gaussian gradient and value noise to a known quadratic. Each method sees the same seeded noise stream; true costs are available only because this control is synthetic. Ten seeds and sigma 0/0.1/0.5 show variability and residual noise floors. Noise curves display medians and interquartile ranges; the table reports means and sample SD. Learning rates are prescribed controls rather than a second tuned optimizer contest.", "",
          "![Tuning and noise](tuning_and_noise.png)", "",
          "| Noise sigma | Method | Final true gap mean | SD across noise seeds |",
          "|---|---|---:|---:|"]
    for sigma in (0.0,.1,.5):
        for method in ("GD_constant","GD_decay","Momentum","Adam"):
            values=[r["final_gap"] for r in data["noise"]["runs"] if r["sigma"]==sigma and r["method"]==method]
            L.append(f"| {sigma:g} | {method} | {statistics.mean(values):.6g} | {statistics.stdev(values):.6g} |")
    L += ["", "## Curvature, Fisher information and nonlinear fitting", "",
          "Binary logistic regression's conditional model Fisher is X-transpose diag(p*(1-p)) X/n, equal to its unregularized cross-entropy Hessian. The empirical Fisher formed from observed-label per-example gradients generally differs. L2 curvature is added separately. Full, diagonal and rank-2 curvature approximations drive actual safeguarded updates; a matrix-free Hessian-vector product is used by conjugate gradient and checked against both dense multiplication and a directional finite difference.", "",
          "| Check | Normalized error / difference |", "|---|---:|"]
    for key,value in data["curvature"]["checks"].items():L.append(f"| {key} | {value:.3e} |")
    L += ["", "For the nonlinear model a*exp(b*x), the exact Hessian contains residual-weighted second derivatives that Gauss-Newton omits. Both safeguarded implementations are compared with an independently called SciPy least_squares reference using the same residual definition and starting point. This reference is a local least-squares solution, not a proof of global optimality.", "",
          "| Fit method | Objective | Difference from reference | Status |", "|---|---:|---:|---|"]
    ref=data["nonlinear_fit"]["reference"]["objective"]
    for r in data["nonlinear_fit"]["runs"]:L.append(f"| {r['method']} | {r['final_objective']:.8g} | {r['final_objective']-ref:.3e} | {r['status']} |")
    L += ["", "![Curvature and fitting](curvature_and_fit.png)", "",
          f"A separate library L-BFGS-B experiment, with no finite bounds, reaches a ridge objective gap of {data['lbfgs']['reference_gap']:.3e}. It has its own line-search/evaluation budget and is not mixed into the main equal-epoch comparison. This is a library demonstration of the limited-memory quasi-Newton method mentioned in the strategy slides.", "",
          "## Loss functions, regularization and corrected slide example", "",
          "MSE, cross-entropy and hinge losses have independently evaluated examples in supplementary.json. L0 counts nonzero parameters; L1 soft-thresholding can set a coefficient to zero; the L2 penalty trades fit against weight norm. Ridge uses half-MSE consistently, including its gradient and Gauss-Newton residual scaling.", "",
          "| L2 strength | Weight norm | Train MSE | Test MSE |", "|---|---:|---:|---:|"]
    for r in data["foundations"]["regularization"]:L.append(f"| {r['lambda']:g} | {r['weight_norm']:.6g} | {r['train_mse']:.6g} | {r['test_mse']:.6g} |")
    L += ["", "PPT1 slide 10 correction: at w=0 on samples (1,2),(2,2), the stated half-MSE loss gives gradient [(-2)*1+(-2)*2]/2 = -3, so eta=0.1 gives w1=0.3. The slide's -5 and 0.5 do not match its stated data. The least-squares optimum remains 6/5=1.2. This independently verified source arithmetic issue is not represented as a fabricated AI-code failure.", "",
          "## Limitations and assignment status", "",
          "Results use small synthetic problems, one independent tuning instance per family, finite hyperparameter grids and a fixed compute environment. They do not establish a general ranking or large-model scalability. There is no real-data benchmark or global neural optimum. Memory complexity is described rather than measured with a peak-memory profiler. Timing includes Python/diagnostic overhead and library threading is uncontrolled. Longer training or different settings can change the outcomes.", "",
          "This package implements the core Track A requirements and the additional L-BFGS demonstration. Research spotlights such as GRNG and AdaFisher are explicitly listed as pending literature/reproduction items in the coverage checklist; they are not claimed as implemented. The assignment-wide second AI-tool comparison, genuine failure log, full chat exports, remaining tracks and public GitHub publication remain outstanding.", "",
          "## Environment and sources", "", f"Recorded UTC: {env['utc']}; Python: {env['python'].splitlines()[0]}; NumPy {env['numpy']}; SciPy {env['scipy']}.",
          f"CPU: {env['cpu']}; logical/affinity CPUs: {env['logical_cpus']}/{env['affinity_cpus']}; cpu.max: {env['cpu_quota']}. {env['note']}", "",
          "Sources: supplied Assignment 8 Track A/Section 5; Chapter 6 PPT1 and PPT4. Adam: Kingma and Ba, https://arxiv.org/abs/1412.6980. Backpropagation: Goodfellow, Bengio and Courville, https://www.deeplearningbook.org/contents/mlp.html. Library references: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html and https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html. Public references accessed 2026-10-31. Installed versions are recorded above.", ""]
    (output/"REPORT.md").write_text("\n".join(L),encoding="utf-8")
    (output/"report.html").write_text(render_markdown(L,output),encoding="utf-8")
    return summary
