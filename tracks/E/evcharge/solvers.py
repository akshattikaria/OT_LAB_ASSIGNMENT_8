"""FCFS baseline, price-aware greedy, and a binary linear formulation via HiGHS."""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, product
import math
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

from .model import Instance


@dataclass
class Solution:
    method: str
    status: str
    schedule: np.ndarray | None
    details: dict = field(default_factory=dict)

    def to_dict(self):
        return {"method": self.method, "status": self.status,
                "schedule": self.schedule.tolist() if self.schedule is not None else None,
                "details": self.details}


def baseline(instance: Instance, **_):
    """Arrival-order priority, charge immediately if enough power is available."""
    instance.validate()
    x = np.zeros((len(instance.vehicles), instance.horizon), dtype=int)
    remaining = [v.required_slots for v in instance.vehicles]
    order = sorted(range(len(instance.vehicles)), key=lambda i:(instance.vehicles[i].arrival, instance.vehicles[i].id))
    for t in range(instance.horizon):
        available = instance.capacity_kw[t]
        for i in order:
            v = instance.vehicles[i]
            if v.arrival <= t < v.departure and remaining[i] and v.power_kw <= available+1e-9:
                x[i, t] = 1
                remaining[i] -= 1
                available -= v.power_kw
    return Solution("baseline", "candidate", x)


def greedy(instance: Instance, **_):
    """Earlier deadlines first; reserve cheapest available periods for each EV.

    This heuristic can leave later vehicles without enough feasible slots.
    Such outputs remain in the results and do not qualify for cost-savings claims.
    """
    instance.validate()
    x = np.zeros((len(instance.vehicles), instance.horizon), dtype=int)
    remaining_power = list(instance.capacity_kw)
    order = sorted(range(len(instance.vehicles)), key=lambda i:(
        instance.vehicles[i].departure,
        instance.vehicles[i].departure-instance.vehicles[i].arrival-instance.vehicles[i].required_slots,
        instance.vehicles[i].arrival, instance.vehicles[i].id))
    for i in order:
        v = instance.vehicles[i]
        candidates = [t for t in range(v.arrival, v.departure) if remaining_power[t]+1e-9 >= v.power_kw]
        candidates.sort(key=lambda t:(instance.prices[t], t))
        for t in candidates[:v.required_slots]:
            x[i, t] = 1
            remaining_power[t] -= v.power_kw
    return Solution("greedy", "candidate", x)


def integer_optimize(instance: Instance, time_limit=3.0, **_):
    """One binary variable per available vehicle-slot pair; exact energy equality."""
    instance.validate()
    if not math.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("time_limit must be positive and finite")
    n, h = len(instance.vehicles), instance.horizon
    if not n or not any(v.required_slots for v in instance.vehicles):
        return Solution("ilp", "optimal", np.zeros((n, h), dtype=int),
                        {"objective": 0.0, "dual_bound": 0.0, "mip_gap": 0.0, "solver_status": 0})
    edges = [(i,t) for i,v in enumerate(instance.vehicles) for t in range(v.arrival,v.departure)]
    c = np.array([instance.prices[t]*instance.vehicles[i].power_kw*instance.slot_hours for i,t in edges])
    rows, columns, values = [], [], []
    for j, (i,t) in enumerate(edges):
        rows.extend((i,n+t)); columns.extend((j,j)); values.extend((1.0,instance.vehicles[i].power_kw))
    matrix = coo_matrix((values,(rows,columns)),shape=(n+h,len(edges))).tocsc()
    demand = np.array([v.required_slots for v in instance.vehicles], dtype=float)
    lower = np.concatenate((demand,np.full(h,-np.inf)))
    upper = np.concatenate((demand,np.array(instance.capacity_kw,dtype=float)))
    result = milp(c=c,integrality=np.ones(len(edges)),bounds=Bounds(0,1),
                  constraints=LinearConstraint(matrix,lower,upper),
                  options={"time_limit":float(time_limit),"mip_rel_gap":0.0,"presolve":True})
    statuses = {0:"optimal",1:"time_limit",2:"infeasible",3:"unbounded",4:"solver_error"}
    status = statuses.get(result.status,"solver_error")
    schedule = None
    if result.x is not None:
        # Keep raw floating values until the independent checker checks integrality.
        schedule = np.zeros((n,h),dtype=float)
        for j,(i,t) in enumerate(edges):
            schedule[i,t] = result.x[j]
        if result.status == 1:
            status = "time_limit_with_candidate"
    def scalar(name):
        value = getattr(result,name,None)
        return float(value) if value is not None and np.isfinite(value) else None
    return Solution("ilp",status,schedule,{
        "solver_status":int(result.status),"message":str(result.message),
        "objective":scalar("fun"),"dual_bound":scalar("mip_dual_bound"),
        "mip_gap":scalar("mip_gap"),"mip_nodes":scalar("mip_node_count"),
        "binary_variables":len(edges),"constraints":n+h,"time_limit_seconds":time_limit})


def exhaustive(instance: Instance, max_candidates=200_000):
    """Independent small-instance oracle; enumerate vehicle slot sets directly."""
    instance.validate()
    count = math.prod(math.comb(v.departure-v.arrival,v.required_slots)
                      if v.required_slots <= v.departure-v.arrival else 0 for v in instance.vehicles)
    if count > max_candidates:
        raise ValueError(f"Exhaustive search capped at {max_candidates}; would inspect {count}")
    choices = [list(combinations(range(v.arrival,v.departure),v.required_slots)) for v in instance.vehicles]
    best, best_cost = None, math.inf
    for assignment in product(*choices):
        loads = [0.0]*instance.horizon
        value = 0.0
        for v,times in zip(instance.vehicles,assignment):
            for t in times:
                loads[t] += v.power_kw
                value += instance.prices[t]*v.power_kw*instance.slot_hours
        if any(load > cap+1e-9 for load,cap in zip(loads,instance.capacity_kw)):
            continue
        if value < best_cost-1e-9:
            best_cost = value
            best = np.zeros((len(instance.vehicles),instance.horizon),dtype=int)
            for i,times in enumerate(assignment):
                best[i,list(times)] = 1
    return Solution("exhaustive","optimal" if best is not None else "infeasible",best,
                    {"objective":best_cost if best is not None else None,"candidate_count":count})


SOLVERS = {"baseline":baseline,"greedy":greedy,"ilp":integer_optimize}
