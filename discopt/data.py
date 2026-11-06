"""Seeded synthetic knapsacks and explicitly designed diagnostic controls."""
import random
from .model import Knapsack

FAMILIES=("uncorrelated","weakly_correlated","strongly_correlated","subset_sum")


def generate(n=20,seed=0,family="uncorrelated"):
    if not isinstance(n,int) or isinstance(n,bool) or not 1<=n<=1000:raise ValueError("n must be 1..1000")
    if family not in FAMILIES:raise ValueError("Unknown instance family")
    rng=random.Random(f"{family}/{n}/{seed}")
    weights=tuple(rng.randint(1,50) for _ in range(n))
    if family=="uncorrelated":values=tuple(rng.randint(1,100) for _ in range(n))
    elif family=="weakly_correlated":values=tuple(max(1,w+rng.randint(-10,10)) for w in weights)
    elif family=="strongly_correlated":values=tuple(w+20 for w in weights)
    else:values=weights
    capacity=max(1,int(sum(weights)*.4))
    return Knapsack(f"{family}_n{n}_s{seed}",values,weights,capacity,
        {"source":"synthetic","family":family,"seed":seed,"capacity_fraction":.4}).validate()


def teaching():
    return Knapsack("teaching",(5,4,3,2),(3,2,2,1),3,{"source":"synthetic","family":"control"}).validate()


def controls():
    return [teaching(),Knapsack("greedy_trap",(60,100,120),(10,20,30),50,{"family":"control"}),
            Knapsack("no_item_fits",(9,10),(4,5),3,{"family":"control"}),
            Knapsack("zero_capacity",(4,5),(1,2),0,{"family":"control"}),
            Knapsack("empty",(),(),5,{"family":"control"})]
