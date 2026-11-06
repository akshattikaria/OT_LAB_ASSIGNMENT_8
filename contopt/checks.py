"""Derivative and recorded-result checks independent of optimizer update code."""
import numpy as np


def finite_gradient(value,w,step=1e-5):
    w=np.asarray(w,dtype=float);result=np.zeros_like(w)
    for j in range(len(w)):
        delta=np.zeros_like(w);delta[j]=step
        result[j]=(value(w+delta)-value(w-delta))/(2*step)
    return result


def finite_hessian(gradient,w,step=1e-5):
    result=np.zeros((len(w),len(w)))
    for j in range(len(w)):
        delta=np.zeros_like(w);delta[j]=step
        result[:,j]=(gradient(w+delta)-gradient(w-delta))/(2*step)
    return result


def relative_error(a,b):
    return float(np.linalg.norm(np.asarray(a)-b)/max(1.0,np.linalg.norm(a),np.linalg.norm(b)))


def audit_run(problem,result):
    w=np.asarray(result["theta"]);issues=[]
    if w.shape!=(problem.d,) or not np.all(np.isfinite(w)):return {"valid":False,"issues":["Invalid final parameters"]}
    value=problem.value(w);gradient=problem.grad(w)
    if not np.isclose(value,result["final_objective"],atol=1e-10,rtol=1e-10):issues.append("Objective mismatch")
    if not np.isclose(np.linalg.norm(gradient),result["final_grad_norm"],atol=1e-9,rtol=1e-9):issues.append("Gradient norm mismatch")
    if result["status"]=="stationary" and np.linalg.norm(gradient)>1.001e-7:issues.append("False stationarity claim")
    return {"valid":not issues,"issues":issues,"recomputed_objective":float(value),
            "recomputed_grad_norm":float(np.linalg.norm(gradient)),
            "finite_difference_gradient_relative_error":relative_error(gradient,finite_gradient(problem.value,w))}
