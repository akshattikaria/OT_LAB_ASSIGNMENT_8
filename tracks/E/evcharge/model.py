"""Input model. All demand is explicitly slot-aligned; no hidden rounding."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path


def _integer(value, label, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")


def _finite(value, label, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    if not math.isfinite(value) or (value <= 0 if positive else value < 0):
        raise ValueError(f"{label} must be finite and {'positive' if positive else 'nonnegative'}")


@dataclass(frozen=True)
class Vehicle:
    id: str
    arrival: int
    departure: int  # Exclusive boundary: slot departure is NOT available.
    required_slots: int
    power_kw: float = 7.0


@dataclass(frozen=True)
class Instance:
    name: str
    slot_minutes: int
    prices: tuple[float, ...]
    capacity_kw: tuple[float, ...]
    vehicles: tuple[Vehicle, ...]
    metadata: dict = field(default_factory=dict)

    @property
    def horizon(self):
        return len(self.prices)

    @property
    def slot_hours(self):
        return self.slot_minutes / 60.0

    def validate(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Instance needs a nonempty name")
        _integer(self.slot_minutes, "slot_minutes", 1)
        if not self.prices or len(self.capacity_kw) != self.horizon:
            raise ValueError("Prices and capacity must have the same nonzero length")
        for p in self.prices:
            _finite(p, "price")
        for p in self.capacity_kw:
            _finite(p, "capacity")
        ids = set()
        for v in self.vehicles:
            if not isinstance(v.id, str) or not v.id or v.id in ids:
                raise ValueError("Vehicle ids must be unique, nonempty strings")
            ids.add(v.id)
            _integer(v.arrival, "arrival")
            _integer(v.departure, "departure", 1)
            _integer(v.required_slots, "required_slots")
            _finite(v.power_kw, "power_kw", positive=True)
            if not 0 <= v.arrival < v.departure <= self.horizon:
                raise ValueError("Availability must satisfy 0 <= arrival < departure <= horizon")
        # Demand greater than a window is a valid but infeasible optimization input.
        # It is intentionally not rejected as malformed data.
        return self

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        required = {"name", "slot_minutes", "prices", "capacity_kw", "vehicles"}
        if not required <= set(d):
            raise ValueError(f"Missing fields: {sorted(required - set(d))}")
        return cls(
            name=d["name"], slot_minutes=d["slot_minutes"],
            prices=tuple(d["prices"]), capacity_kw=tuple(d["capacity_kw"]),
            vehicles=tuple(Vehicle(**v) for v in d["vehicles"]),
            metadata=d.get("metadata", {}),
        ).validate()

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
