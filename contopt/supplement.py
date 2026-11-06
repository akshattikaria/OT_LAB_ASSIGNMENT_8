"""Landscapes, noise, curvature and nonlinear least-squares controls."""
from __future__ import annotations

from time import perf_counter
import numpy as np
from scipy.optimize import least_squares,minimize

from .checks import finite_gradient,finite_hessian,relative_error
from .optimizers import FirstOrder,armijo,positive_direction,train
from .problems import ExpFit,Logistic,Ridge,make_dataset


def landscapes():
    x=10.0;convex=[]
    for k in range(81):
        f=float(np.hypot(1,x)-1)
        convex.append({"k":k,"x":x,"gap":f,"bound":None if not k else 100/(2*k)})
        x-=x/np.hypot(1,x)
    w=np.array([5.0,5.0]);strong=[];f0=137.5
    for k in range(81):
        gap=float(.5*(w[0]**2+10*w[1]**2))
        strong.append({"k":k,"theta":w.tolist(),"gap":gap,"bound":f0*.9**k})
        w-=.1*np.array([w[0],10*w[1]])
    assert all(r["gap"]<=r["bound"]+1e-10 for r in convex[1:])
    assert all(r["gap"]<=r["bound"]+1e-10 for r in strong)
    stationary=[]
    for root in np.roots([4,0,-4,.1]):
        r=float(root.real)
        stationary.append({"x":r,"objective":float((r*r-1)**2+.1*r),"hessian":12*r*r-4})
    global_value=min(p["objective"] for p in stationary if p["hessian"]>0)
    double_well=[]
    for initial in (-2.0,2.0):
        x=initial;points=[]
        for k in range(201):
            points.append({"k":k,"x":x,"objective":float((x*x-1)**2+.1*x)})
            x-=.03*(4*x**3-4*x+.1)
        double_well.append({"initial":initial,"trace":points,"global_gap":points[-1]["objective"]-global_value})
    saddle=[]
    for y0 in (0.0,.05):
        w=np.array([2.0,y0]);points=[]
        for k in range(201):
            g=np.array([w[0],4*w[1]*(w[1]**2-1)])
            points.append({"k":k,"theta":w.tolist(),"objective":float(.5*w[0]**2+(w[1]**2-1)**2),"grad_norm":float(np.linalg.norm(g))})
            w-=.1*g
        saddle.append({"initial_y":y0,"trace":points})
    sensitivity=[]
    for lr in (.1,.5,1.0,1.1):
        x=0.0;points=[]
        for k in range(13):
            points.append({"k":k,"x":x,"objective":(x-3)**2})
            x-=lr*2*(x-3)
        sensitivity.append({"lr":lr,"trace":points})
    return {"convex_smooth":convex,"strongly_convex":strong,"stationary_points":stationary,
            "double_well":double_well,"saddle":saddle,"learning_rate":sensitivity,
            "saddle_hessian_eigenvalues":[-4.0,1.0],"bounds_verified":True}


def conjugate_gradient(hvp,b,tol=1e-10,max_steps=None):
    x=np.zeros_like(b);r=b.copy();p=r.copy();rr=float(r@r);calls=0
    for _ in range(max_steps or len(b)*2):
        if np.sqrt(rr)<=tol:break
        Hp=hvp(p);calls+=1;curvature=float(p@Hp)
        if curvature<=0:raise ValueError("CG requires positive definite curvature")
        alpha=rr/curvature;x+=alpha*p;r-=alpha*Hp
        new_rr=float(r@r)
        p=r+(new_rr/rr)*p;rr=new_rr
    return x,calls,float(np.linalg.norm(hvp(x)-b))


def curvature_experiment(seed=41):
    rng=np.random.default_rng(seed)
    X=rng.normal(size=(192,6));truth=rng.normal(size=6)
    probability=1/(1+np.exp(-(X@truth)))
    y=(rng.random(192)<probability).astype(float)
    problem=Logistic(X,y);w=rng.normal(scale=.3,size=6);v=rng.normal(size=6)
    H=problem.hess(w);F=problem.fisher(w);empirical=problem.empirical_fisher(w)
    checks={"hessian_fd_error":relative_error(H,finite_hessian(problem.grad,w)),
            "hvp_dense_error":relative_error(problem.hvp(w,v),H@v),
            "hvp_fd_error":relative_error(problem.hvp(w,v),(problem.grad(w+1e-5*v)-problem.grad(w-1e-5*v))/(2e-5)),
            "expected_fisher_hessian_error":relative_error(F,H-problem.l2*np.eye(problem.d)),
            "empirical_expected_fisher_difference":float(np.linalg.norm(empirical-F)),
            "diagonal_relative_matrix_error":relative_error(np.diag(np.diag(H)),H)}
    eigenvalues,U=np.linalg.eigh(H);rank=2;floor=float(np.mean(eigenvalues[:-rank]))
    B=floor*np.eye(problem.d)+(U[:,-rank:]*(eigenvalues[-rank:]-floor))@U[:,-rank:].T
    checks["low_rank_relative_matrix_error"]=relative_error(B,H)
    runs=[]
    for method in ("GD","FullFisher","DiagonalFisher","LowRankFisher","HVP_CG"):
        theta=np.zeros(problem.d);trace=[];calls=0;start=perf_counter();status="budget_exhausted"
        for k in range(31):
            g=problem.grad(theta);value=problem.value(theta)
            trace.append({"k":k,"objective":value,"grad_norm":float(np.linalg.norm(g))})
            if np.linalg.norm(g)<=1e-8:status="stationary";break
            if k==30:break
            if method=="GD":direction=-g
            elif method=="HVP_CG":
                direction,used,residual=conjugate_gradient(lambda q:problem.hvp(theta,q),-g)
                calls+=used+1  # Includes independently checked CG residual product.
            else:
                matrix=problem.hess(theta)
                if method=="DiagonalFisher":matrix=np.diag(np.diag(matrix))
                if method=="LowRankFisher":
                    eig,Q=np.linalg.eigh(matrix);base=float(np.mean(eig[:-rank]))
                    matrix=base*np.eye(problem.d)+(Q[:,-rank:]*(eig[-rank:]-base))@Q[:,-rank:].T
                direction,_=positive_direction(matrix,g)
            candidate,_,_=armijo(problem.value,theta,direction,g,value)
            if candidate is None:status="line_search_failed";break
            theta=candidate
        runs.append({"method":method,"theta":theta.tolist(),"trace":trace,"status":status,
                     "runtime_s":perf_counter()-start,"hvp_calls":calls})
    return {"seed":seed,"checks":checks,"runs":runs,"rank":rank,"dimension":problem.d,
            "construction_note":"Diagonal/low-rank demonstrations use explicit small Hessians; low-rank eigendecomposition is not presented as a scalable implementation. HVP_CG uses matrix-free products.",
            "fisher_note":"Conditional model Fisher equals unregularized logistic Hessian; empirical observed-label Fisher generally differs. L2 curvature is added separately."}


def nonlinear_fit(seed=37):
    rng=np.random.default_rng(seed);x=np.linspace(0,1,80);y=2*np.exp(.7*x)+rng.normal(scale=.02,size=80)
    problem=ExpFit(x,y);initial=np.array([1.0,-.2]);reference=least_squares(lambda w:problem.residual_jac(w)[0],initial,
        jac=lambda w:problem.residual_jac(w)[1],ftol=1e-13,xtol=1e-13,gtol=1e-13,max_nfev=1000)
    runs=[train(problem,initial,m,epochs=50) for m in ("Newton","GaussNewton")]
    _,J=problem.residual_jac(initial)
    return {"seed":seed,"x":x.tolist(),"y":y.tolist(),"initial":initial.tolist(),
            "gradient_fd_error":relative_error(problem.grad(initial),finite_gradient(problem.value,initial)),
            "hessian_fd_error":relative_error(problem.hess(initial),finite_hessian(problem.grad,initial)),
            "initial_hessian_gn_difference":float(np.linalg.norm(problem.hess(initial)-J.T@J)),
            "reference":{"theta":reference.x.tolist(),"objective":problem.value(reference.x),"success":bool(reference.success),"message":reference.message},
            "runs":runs}


def noise_experiment(seeds=range(10),steps=800):
    records=[];target=np.array([1.0,-2.0])
    for sigma in (0.0,.1,.5):
        for seed in seeds:
            rng=np.random.default_rng(seed+12000)
            noises=rng.normal(size=(steps,2))*sigma;value_noise=rng.normal(size=steps+1)*sigma
            for method in ("GD_constant","GD_decay","Momentum","Adam"):
                w=np.array([5.0,5.0]);state=FirstOrder("GD" if method.startswith("GD") else method,.1 if method.startswith("GD") else .03 if method=="Momentum" else .05,2)
                trace=[]
                for k in range(steps+1):
                    if k%10==0 or k==steps:
                        true=.5*float((w-target)@(w-target))
                        trace.append({"k":k,"true_objective":true,"observed_objective":true+value_noise[k],"theta":w.tolist()})
                    if k==steps:break
                    if method=="GD_decay":state.lr=.2/np.sqrt(k+1)
                    w=state.step(w,lambda q:q-target+noises[k])
                records.append({"sigma":sigma,"seed":seed,"method":method,"trace":trace,"final_gap":trace[-1]["true_objective"]})
    return {"model":"f(w)=0.5||w-[1,-2]||^2; independent zero-mean additive gradient and value noise",
            "steps":steps,"common_random_numbers":True,"runs":records}


def foundations():
    p,w,Xtest,ytest=make_dataset("ridge",42)
    regularization=[]
    for strength in (0.0,.01,.1,1.0):
        problem=Ridge(p.X,p.y,strength);theta=problem.reference()
        regularization.append({"lambda":strength,"weight_norm":float(np.linalg.norm(theta)),
                               "train_mse":float(np.mean((p.X@theta-p.y)**2)),"test_mse":float(np.mean((Xtest@theta-ytest)**2))})
    simple=Ridge([[1.0],[2.0]],[2.0,2.0],0)
    return {"mse_example":float(np.mean((np.array([1.,3.])-np.array([2.,2.]))**2)),
            "cross_entropy_correct_probability_0_8":float(-np.log(.8)),
            "cross_entropy_correct_probability_0_1":float(-np.log(.1)),
            "hinge_margin_0_2":.8,"L0_at_0_5":1,"L1_at_0_5":.5,"L2_squared_at_0_5":.25,
            "soft_threshold_lambda_0_5":{"z_1_5":1.0,"z_0_3":0.0},"regularization":regularization,
            "slide_10_check":{"data":[[1,2],[2,2]],"loss":"0.5 * mean((w*x-y)^2)","gradient_at_zero":float(simple.grad(np.zeros(1))[0]),
                            "GD_step_lr_0_1":float((np.zeros(1)-.1*simple.grad(np.zeros(1)))[0]),"reference_weight":float(simple.reference()[0]),
                            "note":"The supplied PPT1 slide 10 states gradient -5 and step 0.5. Its stated data and loss give -3 and step 0.3; optimum remains 1.2."}}


def lbfgs_demo(seed=43):
    p,w,_,_=make_dataset("ridge",seed)
    result=minimize(p.value,w,jac=p.grad,method="L-BFGS-B",options={"maxiter":200,"ftol":1e-14,"gtol":1e-10,"maxcor":5})
    return {"method":"L-BFGS-B (unconstrained bounds)","seed":seed,"success":bool(result.success),"message":str(result.message),
            "objective":float(result.fun),"reference_objective":p.value(p.reference()),"reference_gap":float(result.fun-p.value(p.reference())),
            "iterations":int(result.nit),"function_evaluations":int(result.nfev),"gradient_evaluations":int(result.njev),
            "note":"Separate library experiment with its own line-search budget; not mixed into the main equal-epoch timing comparison."}


def run_supplements():
    return {"landscapes":landscapes(),"curvature":curvature_experiment(),"nonlinear_fit":nonlinear_fit(),
            "noise":noise_experiment(),"foundations":foundations(),"lbfgs":lbfgs_demo()}
