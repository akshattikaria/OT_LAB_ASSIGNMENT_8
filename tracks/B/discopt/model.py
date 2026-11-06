from dataclasses import dataclass,asdict,field
import json
from pathlib import Path
import numpy as np


@dataclass(frozen=True)
class Knapsack:
    name:str
    values:tuple[int,...]
    weights:tuple[int,...]
    capacity:int
    metadata:dict=field(default_factory=dict)

    @property
    def n(self):return len(self.values)

    def validate(self):
        if not isinstance(self.name,str) or not self.name:raise ValueError("Nonempty name required")
        if len(self.values)!=len(self.weights):raise ValueError("Values/weights must have equal length")
        if isinstance(self.capacity,bool) or not isinstance(self.capacity,int) or self.capacity<0:raise ValueError("Integer nonnegative capacity required")
        for sequence,minimum in ((self.values,0),(self.weights,1)):
            if any(isinstance(x,bool) or not isinstance(x,int) or x<minimum for x in sequence):
                raise ValueError("Integer nonnegative values and positive weights required")
        if sum(self.values)>10**12 or sum(self.weights)>10**12 or self.capacity>10**12:
            raise ValueError("This experiment limits numeric totals to 1e12")
        if not isinstance(self.metadata,dict):raise ValueError("Metadata must be a dictionary")
        return self

    def save(self,path):
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(asdict(self),indent=2)+"\n",encoding="utf-8")

    @classmethod
    def load(cls,path):
        d=json.loads(Path(path).read_text());d["values"]=tuple(d["values"]);d["weights"]=tuple(d["weights"])
        return cls(**d).validate()


def audit(problem,selection,tolerance=1e-6):
    """Recompute value, weight and feasibility without solver tables or bounds."""
    problem.validate()
    if selection is None:return {"feasible":False,"errors":["No candidate returned"],"value":None,"weight":None}
    try:x=np.asarray(selection,dtype=float)
    except (TypeError,ValueError):return {"feasible":False,"errors":["Nonnumeric selection"],"value":None,"weight":None}
    if x.shape!=(problem.n,) or not np.all(np.isfinite(x)):
        return {"feasible":False,"errors":["Invalid shape or nonfinite selection"],"value":None,"weight":None}
    if np.any(x < -tolerance) or np.any(x > 1+tolerance) or np.any(np.abs(x-np.rint(x))>tolerance):
        return {"feasible":False,"errors":["Selection is not binary"],"value":None,"weight":None}
    bits=[int(round(float(b))) for b in x]
    value=sum(v*b for v,b in zip(problem.values,bits));weight=sum(w*b for w,b in zip(problem.weights,bits))
    errors=[] if weight<=problem.capacity else ["Budget exceeded"]
    return {"feasible":not errors,"errors":errors,"value":value,"weight":weight,
            "unused_capacity":problem.capacity-weight,"selected_items":[i for i,b in enumerate(bits) if b]}
