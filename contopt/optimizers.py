"""Explicit first-order updates and safeguarded Newton/Gauss-Newton."""
from __future__ import annotations

from time import perf_counter
import numpy as np

FIRST_ORDER=("GD","SGD","MiniBatchSGD","Momentum","NAG","AdaGrad","RMSProp","Adam")
SECOND_ORDER=("Newton","GaussNewton")


class FirstOrder:
    def __init__(self,method,lr,dimension,beta=.9,beta2=.999,epsilon=1e-8):
        if method not in FIRST_ORDER:raise ValueError("Unknown first-order method")
        if not np.isfinite(lr) or lr<=0:raise ValueError("lr must be finite and positive")
        if not 0<=beta<1 or not 0<=beta2<1 or epsilon<=0:raise ValueError("Invalid optimizer settings")
        self.method,self.lr,self.beta,self.beta2,self.eps=method,float(lr),beta,beta2,epsilon
        self.velocity=np.zeros(dimension);self.accumulator=np.zeros(dimension);self.k=0
    def step(self,w,gradient):
        self.k+=1; lr,b=self.lr,self.beta
        at=w-b*self.velocity if self.method=="NAG" else w
        g=gradient(at)
        if self.method in ("GD","SGD","MiniBatchSGD"):return w-lr*g
        if self.method in ("Momentum","NAG"):
            self.velocity=b*self.velocity+lr*g
            return w-self.velocity
        if self.method=="AdaGrad":
            self.accumulator+=g*g
            return w-lr*g/(np.sqrt(self.accumulator)+self.eps)
        if self.method=="RMSProp":
            self.accumulator=b*self.accumulator+(1-b)*g*g
            return w-lr*g/(np.sqrt(self.accumulator)+self.eps)
        self.velocity=b*self.velocity+(1-b)*g
        self.accumulator=self.beta2*self.accumulator+(1-self.beta2)*g*g
        m=self.velocity/(1-b**self.k);v=self.accumulator/(1-self.beta2**self.k)
        return w-lr*m/(np.sqrt(v)+self.eps)


def positive_direction(matrix,g,floor=1e-8):
    """Symmetrize and shift indefinite curvature to obtain a descent direction."""
    matrix=(matrix+matrix.T)/2
    shift=max(0.0,floor-float(np.linalg.eigvalsh(matrix)[0]))
    direction=-np.linalg.solve(matrix+shift*np.eye(len(g)),g)
    if not np.all(np.isfinite(direction)) or float(g@direction)>=0:
        return -g,shift
    return direction,shift


def armijo(value,w,direction,g,current,max_trials=45):
    slope=float(g@direction)
    if slope>=0:return None,0,0
    step=1.0
    for k in range(max_trials):
        try:
            with np.errstate(over="raise",invalid="raise",divide="raise"):
                candidate=w+step*direction; candidate_value=value(candidate)
            if np.isfinite(candidate_value) and candidate_value<=current+1e-4*step*slope:
                return candidate,step,k+1
        except (FloatingPointError,OverflowError):pass
        step*=.5
    return None,step,max_trials


def train(problem,initial,method,lr=.01,epochs=40,batch_size=32,seed=0,tolerance=1e-7):
    if method not in FIRST_ORDER+SECOND_ORDER:raise ValueError("Unknown method")
    if not isinstance(epochs,int) or epochs<1 or not isinstance(batch_size,int) or batch_size<1:
        raise ValueError("Positive integer epochs and batch size required")
    w=np.asarray(initial,dtype=float).copy()
    if w.shape!=(problem.d,) or not np.all(np.isfinite(w)):raise ValueError("Invalid initial parameters")
    if method in SECOND_ORDER and not hasattr(problem,"hess"):raise ValueError("Curvature not supplied for this problem")
    state=FirstOrder(method,lr,problem.d) if method in FIRST_ORDER else None
    rng=np.random.default_rng(seed)
    counts={"gradient_calls":0,"gradient_examples":0,"hessian_calls":0,"jacobian_calls":0,
            "objective_calls":0,"diagnostic_gradient_calls":0,"diagnostic_objective_calls":0,
            "updates":0,"line_search_trials":0}
    def value(x):counts["objective_calls"]+=1;return problem.value(x)
    def gradient(x,indices=None):
        counts["gradient_calls"]+=1;counts["gradient_examples"]+=problem.n if indices is None else len(indices)
        return problem.grad(x,indices)
    def record(epoch):
        counts["diagnostic_objective_calls"]+=1;counts["diagnostic_gradient_calls"]+=1
        objective=problem.value(w);norm=float(np.linalg.norm(problem.grad(w)))
        return {"epoch":epoch,"objective":objective,"grad_norm":norm,"theta":w.tolist(),
                "gradient_passes":counts["gradient_examples"]/problem.n,
                "data_derivative_passes":counts["gradient_examples"]/problem.n+counts["hessian_calls"]+counts["jacobian_calls"],
                "hessian_calls":counts["hessian_calls"],"jacobian_calls":counts["jacobian_calls"],
                "updates":counts["updates"]}
    start=perf_counter();trace=[record(0)];status="budget_exhausted";error=None
    for epoch in range(1,epochs+1):
        if trace[-1]["grad_norm"]<=tolerance:
            status="stationary";break
        try:
            with np.errstate(over="raise",invalid="raise",divide="raise"):
                if method in SECOND_ORDER:
                    if method=="Newton":
                        g=gradient(w);B=problem.hess(w);counts["hessian_calls"]+=1
                    else:
                        residual,J=problem.residual_jac(w);counts["jacobian_calls"]+=1
                        g=J.T@residual;B=J.T@J
                    direction,shift=positive_direction(B,g)
                    candidate,step,trials=armijo(value,w,direction,g,trace[-1]["objective"])
                    counts["line_search_trials"]+=trials
                    if candidate is None:status="line_search_failed";break
                    w=candidate;counts["updates"]+=1
                else:
                    size=problem.n if method=="GD" else 1 if method=="SGD" else min(batch_size,problem.n)
                    order=np.arange(problem.n) if method=="GD" else rng.permutation(problem.n)
                    for begin in range(0,problem.n,size):
                        indices=order[begin:begin+size]
                        w=state.step(w,lambda q:gradient(q,indices))
                        counts["updates"]+=1
                        if not np.all(np.isfinite(w)) or np.linalg.norm(w)>1e8:
                            raise FloatingPointError("Parameter norm exceeded stability guard")
                point=record(epoch)
                if not np.isfinite(point["objective"]) or point["objective"]>1e12:
                    raise FloatingPointError("Objective exceeded stability guard")
                trace.append(point)
        except (FloatingPointError,OverflowError,np.linalg.LinAlgError) as e:
            status="diverged";error=str(e);w=np.array(trace[-1]["theta"]);break
    if status=="budget_exhausted" and trace[-1]["grad_norm"]<=tolerance:status="stationary"
    return {"method":method,"lr":lr,"status":status,"error":error,"theta":w.tolist(),"trace":trace,
            "runtime_s":perf_counter()-start,"counts":counts,"epochs_completed":trace[-1]["epoch"],
            "final_objective":trace[-1]["objective"],"final_grad_norm":trace[-1]["grad_norm"],
            "final_state_note":"Last finite recorded epoch if divergence occurred; attempted work counts are retained"}
