"""Independent schedule audit: no solver matrices, objective or status are trusted."""
from __future__ import annotations

import math
import numpy as np

from .model import Instance


def audit(instance: Instance, schedule, tolerance=1e-6):
    instance.validate()
    result = {"feasible": False, "errors": [], "cost": None, "energy_kwh": None,
              "required_kwh": sum(v.required_slots*v.power_kw*instance.slot_hours
                                  for v in instance.vehicles),
              "unmet_kwh": None, "missed_deadlines": None,
              "peak_kw": None, "max_capacity_excess_kw": None,
              "outside_window_slots": None}
    if schedule is None:
        result["errors"] = ["No schedule returned"]
        return result
    try:
        x = np.asarray(schedule, dtype=float)
    except (TypeError, ValueError):
        result["errors"] = ["Schedule is not a numeric matrix"]
        return result
    if x.shape != (len(instance.vehicles), instance.horizon):
        result["errors"] = [f"Wrong shape: {x.shape}"]
        return result
    if not np.all(np.isfinite(x)):
        result["errors"] = ["Non-finite schedule values"]
        return result
    if np.any(x < -tolerance) or np.any(x > 1+tolerance) or np.any(np.abs(x-np.rint(x)) > tolerance):
        result["errors"] = ["Schedule is not binary within tolerance"]
        return result
    # Snap only values already independently checked to be within numerical tolerance.
    x = np.rint(x).astype(int)
    loads = [0.0]*instance.horizon
    cost = 0.0
    delivered = 0.0
    unmet = 0.0
    missed = 0
    outside = 0
    errors = []
    per_vehicle = []
    for i, v in enumerate(instance.vehicles):
        total_slots = 0
        in_window_slots = 0
        for t in range(instance.horizon):
            if x[i, t]:
                total_slots += 1
                loads[t] += v.power_kw
                energy = v.power_kw*instance.slot_hours
                delivered += energy
                cost += energy*instance.prices[t]
                if v.arrival <= t < v.departure:
                    in_window_slots += 1
                else:
                    outside += 1
        deficit = max(0, v.required_slots-in_window_slots)*v.power_kw*instance.slot_hours
        unmet += deficit
        missed += int(deficit > tolerance)
        if total_slots != v.required_slots:
            errors.append(f"{v.id}: delivered {total_slots} slots, required {v.required_slots}")
        per_vehicle.append({"vehicle_id": v.id, "required_slots": v.required_slots,
                            "delivered_in_window_slots": in_window_slots, "unmet_kwh": deficit})
    excess = max([0.0] + [loads[t]-instance.capacity_kw[t] for t in range(instance.horizon)])
    if outside:
        errors.append(f"{outside} charging slots outside availability")
    if excess > tolerance:
        errors.append(f"Station capacity exceeded by {excess:.6g} kW")
    if missed and not any("required" in e for e in errors):
        errors.append("Energy was not delivered within all departure deadlines")
    result.update(feasible=not errors, errors=errors, cost=float(cost), energy_kwh=delivered,
                  unmet_kwh=unmet, missed_deadlines=missed, peak_kw=max(loads, default=0.0),
                  max_capacity_excess_kw=excess, outside_window_slots=outside,
                  load_kw=loads, per_vehicle=per_vehicle)
    assert all(math.isfinite(result[k]) for k in ("cost", "energy_kwh", "unmet_kwh", "peak_kw"))
    return result
