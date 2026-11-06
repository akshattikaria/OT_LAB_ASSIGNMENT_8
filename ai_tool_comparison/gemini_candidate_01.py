from typing import Any


def solve_knapsack(
    weights: list[int] | tuple[int, ...],
    values: list[int] | tuple[int, ...],
    capacity: int,
) -> dict[str, Any]:
    if not isinstance(weights, (list, tuple)) or not isinstance(values, (list, tuple)):
        raise ValueError("weights and values must be lists or tuples.")
    if len(weights) != len(values):
        raise ValueError("weights and values must have the same length.")
    if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 0:
        raise ValueError("capacity must be a nonnegative integer.")

    for w in weights:
        if not isinstance(w, int) or isinstance(w, bool) or w <= 0:
            raise ValueError("All weights must be positive integers.")

    for v in values:
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            raise ValueError("All values must be nonnegative integers.")

    if not weights or capacity == 0:
        return {"value": 0, "weight": 0, "indices": []}

    dp_val = [-1] * (capacity + 1)
    dp_idx: list[tuple[int, ...]] = [()] * (capacity + 1)
    dp_val[0] = 0

    max_w = 0
    for i, (w, v) in enumerate(zip(weights, values)):
        if w > capacity:
            continue
        max_w = min(capacity, max_w + w)
        for curr_w in range(max_w, w - 1, -1):
            prev_w = curr_w - w
            prev_v = dp_val[prev_w]
            if prev_v != -1:
                cand_v = prev_v + v
                curr_v = dp_val[curr_w]
                if cand_v > curr_v:
                    dp_val[curr_w] = cand_v
                    dp_idx[curr_w] = dp_idx[prev_w] + (i,)
                elif cand_v == curr_v:
                    cand_idx = dp_idx[prev_w] + (i,)
                    if cand_idx < dp_idx[curr_w]:
                        dp_idx[curr_w] = cand_idx

    best_val = 0
    best_weight = 0
    best_indices: tuple[int, ...] = ()

    for w in range(1, max_w + 1):
        if dp_val[w] > best_val:
            best_val = dp_val[w]
            best_weight = w
            best_indices = dp_idx[w]

    return {
        "value": best_val,
        "weight": best_weight,
        "indices": list(best_indices),
    }
