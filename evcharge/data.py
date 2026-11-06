"""Seeded synthetic sessions; guaranteed-feasible cases carry a separate witness."""
from __future__ import annotations

from dataclasses import replace
import math
import random
import numpy as np

from .model import Instance, Vehicle
from .verify import audit

SCENARIOS = ("flexible", "flat_prices", "tight_deadlines", "limited_power", "mixed_power")


def teaching_example(flat=False):
    return Instance("teaching_flat" if flat else "teaching_variable",60,
                    (8,)*6 if flat else (12,12,10,4,4,8),(14,)*6,
                    (Vehicle("A",0,3,1),Vehicle("B",0,6,2),Vehicle("C",1,6,1),Vehicle("D",2,6,1)),
                    {"source":"synthetic","scenario":"teaching","clock_start":"09:00"}).validate()


def greedy_trap():
    # A's earlier deadline does not imply it should take B's scarce cheap slot.
    return Instance("greedy_trap",60,(2,2,1,2),(7,)*4,
                    (Vehicle("A",0,3,1),Vehicle("B",2,4,2)),
                    {"source":"synthetic","scenario":"greedy_trap","clock_start":"08:00"}).validate()


def infeasible_example():
    return Instance("infeasible_capacity",15,(8,)*4,(7,)*4,
                    (Vehicle("A",0,4,3),Vehicle("B",0,4,3)),
                    {"source":"synthetic","scenario":"infeasible_control","clock_start":"08:00"}).validate()


def generate(n=20, seed=0, scenario="flexible"):
    if isinstance(n,bool) or not isinstance(n,int) or not 1 <= n <= 500:
        raise ValueError("n must be an integer from 1 to 500")
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    rng = random.Random(seed)
    h = 48  # 08:00-20:00 at 15-minute resolution.
    # Fictional tariff: 08-11 high, 11-16 low, 16-20 high.
    prices = tuple(12.0 if t < 12 else 4.0 if t < 32 else 10.0 for t in range(h))
    if scenario == "flat_prices":
        prices = (8.0,)*h
    mixed = scenario == "mixed_power"
    ratio = 0.22 if scenario == "limited_power" else 0.45
    cap = (11.0 if mixed else 7.0)*max(2,math.ceil(n*ratio))
    if mixed:
        cap = max(22.0,cap)
    for attempt in range(1,101):
        vehicles = []
        for i in range(n):
            slots = rng.randint(4,12)
            if scenario == "tight_deadlines":
                arrival = rng.randint(0,28)
                departure = min(h,arrival+slots+rng.randint(0,3))
            else:
                arrival = rng.randint(0,12)
                departure = rng.randint(32,48)
            power = float(rng.choice([7,11,22])) if mixed else 7.0
            vehicles.append(Vehicle(f"EV{i+1:03d}",arrival,departure,slots,power))
        instance = Instance(f"{scenario}_n{n}_s{seed}",15,prices,(cap,)*h,tuple(vehicles),
                            {"source":"synthetic","scenario":scenario,"seed":seed,
                             "clock_start":"08:00","generation_attempt":attempt,
                             "plugs":n,"feasibility":"independently checked construction witness"}).validate()
        witness = np.zeros((n,h),dtype=int)
        load = [0.0]*h
        order = sorted(range(n),key=lambda i:(vehicles[i].departure-vehicles[i].arrival-vehicles[i].required_slots,
                                             vehicles[i].departure,vehicles[i].id))
        complete = True
        for i in order:
            v = vehicles[i]
            candidates = [t for t in range(v.arrival,v.departure) if load[t]+v.power_kw <= cap+1e-9]
            # Balance a witness, not an objective-optimal schedule. It is never passed to a solver.
            tie_break = {t:rng.random() for t in candidates}
            candidates.sort(key=lambda t:(load[t],tie_break[t]))
            if len(candidates) < v.required_slots:
                complete = False
                break
            for t in candidates[:v.required_slots]:
                witness[i,t] = 1
                load[t] += v.power_kw
        if complete and audit(instance,witness)["feasible"]:
            return instance,witness
    raise RuntimeError(f"Could not construct feasible {scenario}, n={n}, seed={seed}; no silent demand reduction")
