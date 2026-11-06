"""Upper-triangular QUBO and Ising with spin s=1-2*x; offsets retained."""
from dataclasses import dataclass
import math
import numpy as np


@dataclass
class QUBO:
    Q:np.ndarray
    offset:float
    names:list[str]
    metadata:dict

    @property
    def n(self):return len(self.names)

    def validate(self):
        if self.Q.shape!=(self.n,self.n) or not np.all(np.isfinite(self.Q)) or not np.isfinite(self.offset):
            raise ValueError("Finite matching Q matrix and offset required")
        if np.any(np.tril(self.Q,-1)!=0):raise ValueError("Q must be upper triangular; off-diagonals counted once")
        magnitude=abs(float(self.offset))+float(np.abs(self.Q).sum())
        if magnitude>2**45:
            raise ValueError("Expanded QUBO coefficients exceed this float encoder's validated range; reduce/rescale the problem explicitly")
        return self

    def energy(self,x):
        self.validate()
        x=np.asarray(x,dtype=float)
        if x.shape!=(self.n,) or not np.all((x==0)|(x==1)):raise ValueError("Binary vector required")
        return float(self.offset+x@self.Q@x)

    def ising(self):
        """x=(1-s)/2, with s=+1 for bit 0 and s=-1 for bit 1."""
        self.validate();diagonal=np.diag(self.Q);off=np.triu(self.Q,1)
        h=-.5*diagonal-.25*(off.sum(axis=0)+off.sum(axis=1))
        J=.25*off
        offset=float(self.offset+.5*diagonal.sum()+.25*off.sum())
        return {"h":h.tolist(),"J_upper":J.tolist(),"offset":offset,"spin_mapping":"s_i = 1 - 2*x_i"}

    def to_dict(self):
        return {"schema":"track-b-qubo-v1","variables":self.names,"Q_upper":self.Q.tolist(),"offset":self.offset,
                "energy":"offset + sum_i Q_ii*x_i + sum_(i<j) Q_ij*x_i*x_j",
                "statevector_index":"sum_i x_i * 2**i; variable 0 is least significant",
                "display_bits":"variable_order_bits lists x_0 first; statevector_label lists most significant bit first",
                "ising":self.ising(),"metadata":self.metadata}


def knapsack_qubo(p,penalty=None):
    p.validate()
    penalty=float(sum(p.values)+1) if penalty is None else float(penalty)
    if not math.isfinite(penalty) or penalty<0:raise ValueError("Nonnegative finite penalty required")
    k=p.capacity.bit_length()
    slack=[1<<i for i in range(k)]
    a=np.array(list(p.weights)+slack,dtype=float)
    reward=np.array(list(p.values)+[0]*k,dtype=float)
    Q=np.diag(penalty*(a*a-2*p.capacity*a)-reward)
    Q+=np.triu(2*penalty*np.outer(a,a),1)
    names=[f"item_{i}" for i in range(p.n)]+[f"slack_{i}" for i in range(k)]
    return QUBO(Q,penalty*p.capacity*p.capacity,names,{"problem":"knapsack","name":p.name,
        "values":list(p.values),"weights":list(p.weights),"capacity":p.capacity,"item_count":p.n,
        "slack_weights":slack,"penalty":penalty,"sufficient_penalty_condition":"P > sum(values)",
        "direct_energy":"-value(items) + P*(weight(items)+slack-capacity)**2"}).validate()


def maxcut_qubo(n,edges):
    if not isinstance(n,int) or n<1:raise ValueError("Positive integer node count required")
    Q=np.zeros((n,n));normalized=[];seen=set()
    for u,v,weight in edges:
        if not 0<=u<n or not 0<=v<n or u==v or not np.isfinite(weight) or weight<=0:raise ValueError("Invalid edge")
        u,v=min(u,v),max(u,v)
        if (u,v) in seen:raise ValueError("Duplicate edge")
        seen.add((u,v));Q[u,u]-=weight;Q[v,v]-=weight;Q[u,v]+=2*weight;normalized.append([u,v,weight])
    return QUBO(Q,0.0,[f"node_{i}" for i in range(n)],{"problem":"maxcut","edges":normalized,
        "direct_energy":"-sum_edges weight*(x_u+x_v-2*x_u*x_v)","note":"Max-Cut itself is unconstrained; knapsack provides the explicit penalty demonstration."}).validate()


def enumerate_qubo(model,max_states=1_100_000):
    model.validate()
    if (1<<model.n)>max_states:raise ValueError("Classical exhaustive state limit exceeded")
    ising=model.ising();h=np.array(ising["h"]);J=np.array(ising["J_upper"])
    states=[];max_error=0.0
    for index in range(1<<model.n):
        x=np.array([(index>>i)&1 for i in range(model.n)]);spins=1-2*x
        energy=model.energy(x);spin_energy=float(ising["offset"]+h@spins+spins@J@spins)
        meta=model.metadata
        if meta["problem"]=="knapsack":
            n=meta["item_count"];value=sum(v*int(b) for v,b in zip(meta["values"],x[:n]))
            weight=sum(w*int(b) for w,b in zip(meta["weights"],x[:n]));slack=sum(w*int(b) for w,b in zip(meta["slack_weights"],x[n:]))
            residual=weight+slack-meta["capacity"];direct=-value+meta["penalty"]*residual**2
            extra={"value":value,"weight":weight,"slack":slack,"constraint_residual":residual,
                   "original_feasible":weight<=meta["capacity"],"encoded_feasible":residual==0}
        else:
            cut=sum(weight for u,v,weight in meta["edges"] if x[u]!=x[v]);direct=-cut
            extra={"cut":cut,"original_feasible":True,"encoded_feasible":True}
        error=max(abs(energy-spin_energy),abs(energy-direct));max_error=max(max_error,error)
        if error>1e-8:raise AssertionError("Direct, QUBO and Ising energies disagree")
        states.append({"index":index,"bits":x.tolist(),"variable_order_bits":"".join(map(str,x.tolist())),
                       "statevector_label":format(index,f"0{model.n}b"),"energy":energy,"ising_energy":spin_energy,**extra})
    minimum=min(s["energy"] for s in states)
    ground=[s for s in states if abs(s["energy"]-minimum)<=1e-8]
    return {"minimum_energy":minimum,"states":states,"ground_states":ground,"max_energy_identity_error":max_error,
            "all_ground_states_encoded_feasible":all(s["encoded_feasible"] for s in ground)}
