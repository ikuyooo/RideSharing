"""Survey S1 design statistics (pure Python, no numerical dependency).

Used by scripts/survey/design_diagnostics.py and the TEST pilot test to judge the
Part-1A discrete-choice experiment as the conditional (multinomial) logit of
Revision 9 Section 65.3 will see it:

  U_j = ASC_j + b_price * price_k + b_time * time + b_detour * detour (pool)
        + b_gap * (unmatched - expected)_k (pool) + likelihood / walk dummies (pool)
        + b_rain_bike * rain * [j = bike] + b_urgent_time * urgent * time

Base alternative: CAR_URBAN_PRIVATE. Prices in thousand VND, times in minutes. The
pool card shows no own travel time: it rides the private route, so its time is the
private time and its extra time is the detour attribute.
"""

import math
import random
from typing import Any

COLUMNS = ["asc_bike", "asc_pool", "price_k", "time_min", "detour_min", "unmatched_gap_k",
           "like_medium", "like_low", "walk_200", "rain_x_bike", "urgent_x_time"]
ALTERNATIVES = ("BIKE_URBAN", "CAR_URBAN_POOL", "CAR_URBAN_PRIVATE")
# Illustrative priors for D_p-error and the TEST pilot only (an ASSUMPTION, not an estimate):
# value of time ~ 50 000 VND / h (0.83 k / min), detour disliked a little more than riding time.
PRIORS = [0.5, -0.2, -0.03, -0.025, -0.03, -0.01, -0.3, -0.8, -0.2, -0.8, -0.02]


def encode(task: dict[str, Any]) -> list[list[float]]:
    """One Part-1A task -> one row per alternative (ALTERNATIVES order)."""
    c = {x["alternative"]: x for x in task["cards"]}
    rain = float("Mưa" in task["context"]["weather"])
    urgent = float("đúng giờ" in task["context"]["urgency"])
    bike, pool, priv = c["BIKE_URBAN"], c["CAR_URBAN_POOL"], c["CAR_URBAN_PRIVATE"]
    t_priv = float(priv["travel_min"])
    return [
        [1, 0, bike["price_vnd"] / 1000, bike["travel_min"], 0, 0, 0, 0, 0, rain, urgent * bike["travel_min"]],
        [0, 1, pool["price_vnd"] / 1000, t_priv, pool["max_detour_min"],
         (pool["max_price_if_unmatched_vnd"] - pool["price_vnd"]) / 1000,
         float(pool["match_likelihood"] == "MEDIUM"), float(pool["match_likelihood"] == "LOW"),
         float(pool["walk_m"] == 200), 0, urgent * t_priv],
        [0, 0, priv["price_vnd"] / 1000, t_priv, 0, 0, 0, 0, 0, 0, urgent * t_priv],
    ]


# --- small linear algebra -------------------------------------------------------------------


def inverse(m: list[list[float]]) -> list[list[float]] | None:
    n = len(m)
    a = [row[:] + [float(i == j) for j in range(n)] for i, row in enumerate(m)]
    for col in range(n):
        piv = max(range(col, n), key=lambda i: abs(a[i][col]))
        if abs(a[piv][col]) < 1e-12:
            return None
        a[col], a[piv] = a[piv], a[col]
        p = a[col][col]
        a[col] = [x / p for x in a[col]]
        for i in range(n):
            if i != col and a[i][col]:
                f = a[i][col]
                a[i] = [x - f * y for x, y in zip(a[i], a[col], strict=True)]
    return [row[n:] for row in a]


def log_det(m: list[list[float]]) -> float | None:
    n = len(m)
    a = [row[:] for row in m]
    total = 0.0
    for col in range(n):
        piv = max(range(col, n), key=lambda i: abs(a[i][col]))
        if abs(a[piv][col]) < 1e-12:
            return None
        a[col], a[piv] = a[piv], a[col]
        total += math.log(abs(a[col][col]))
        for i in range(col + 1, n):
            f = a[i][col] / a[col][col]
            a[i] = [x - f * y for x, y in zip(a[i], a[col], strict=True)]
    return total


def eigenvalues(m: list[list[float]], sweeps: int = 100) -> list[float]:
    """Jacobi eigenvalues of a symmetric matrix."""
    a = [row[:] for row in m]
    n = len(a)
    for _ in range(sweeps):
        off = sum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j)
        if off < 1e-20:
            break
        for p in range(n):
            for q in range(p + 1, n):
                if abs(a[p][q]) < 1e-15:
                    continue
                theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
                t = (1 if theta >= 0 else -1) / (abs(theta) + math.sqrt(theta * theta + 1))
                c = 1 / math.sqrt(t * t + 1)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p], a[k][q] = c * akp - s * akq, s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k], a[q][k] = c * apk - s * aqk, s * apk + c * aqk
    return sorted(a[i][i] for i in range(n))


def rank(rows: list[list[float]], eps: float = 1e-9) -> int:
    a = [r[:] for r in rows]
    r = 0
    for c in range(len(a[0])):
        piv = max(range(r, len(a)), key=lambda i: abs(a[i][c]), default=None)
        if piv is None or abs(a[piv][c]) < eps:
            continue
        a[r], a[piv] = a[piv], a[r]
        for i in range(len(a)):
            if i != r and abs(a[i][c]) > eps:
                f = a[i][c] / a[r][c]
                a[i] = [x - f * y for x, y in zip(a[i], a[r], strict=True)]
        r += 1
        if r == len(a):
            break
    return r


def corr(a: list[float], b: list[float]) -> float | None:
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    va, vb = sum((x - ma) ** 2 for x in a), sum((y - mb) ** 2 for y in b)
    if va == 0 or vb == 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=True)) / math.sqrt(va * vb)


# --- MNL quantities -----------------------------------------------------------------------------


def probabilities(xs: list[list[float]], beta: list[float]) -> list[float]:
    v = [sum(b * x for b, x in zip(beta, row, strict=True)) for row in xs]
    m = max(v)
    e = [math.exp(x - m) for x in v]
    s = sum(e)
    return [x / s for x in e]


def information(sets: list[list[list[float]]], beta: list[float]) -> list[list[float]]:
    k = len(beta)
    info = [[0.0] * k for _ in range(k)]
    for xs in sets:
        p = probabilities(xs, beta)
        mean = [sum(pj * row[i] for pj, row in zip(p, xs, strict=True)) for i in range(k)]
        for pj, row in zip(p, xs, strict=True):
            d = [row[i] - mean[i] for i in range(k)]
            for i in range(k):
                for j in range(k):
                    info[i][j] += pj * d[i] * d[j]
    return info


def d_error(sets: list[list[list[float]]], beta: list[float]) -> float | None:
    """det(I^-1)^(1/K) per choice set (smaller is better); None when singular."""
    info = information(sets, beta)
    n = len(sets)
    ld = log_det([[v / n for v in row] for row in info])
    return None if ld is None else math.exp(-ld / len(beta))


def condition_number(info: list[list[float]]) -> float | None:
    """lambda_max / lambda_min of the information matrix scaled to unit diagonal."""
    d = [math.sqrt(info[i][i]) if info[i][i] > 0 else 0 for i in range(len(info))]
    if not all(d):
        return None
    scaled = [[info[i][j] / (d[i] * d[j]) for j in range(len(info))] for i in range(len(info))]
    ev = eigenvalues(scaled)
    return None if ev[0] <= 1e-12 else ev[-1] / ev[0]


def vif(sets: list[list[list[float]]], first_attr: int = 2) -> dict[str, float | None]:
    """VIF of the attribute columns of the within-task differences (vs the base alternative)."""
    diffs = [[a - b for a, b in zip(row, xs[-1], strict=True)] for xs in sets for row in xs[:-1]]
    cols = list(zip(*diffs, strict=True))
    attrs = list(range(first_attr, len(COLUMNS)))
    r = [[corr(cols[i], cols[j]) or 0.0 for j in attrs] for i in attrs]
    inv = inverse(r)
    return {COLUMNS[k]: (None if inv is None else round(inv[n][n], 2)) for n, k in enumerate(attrs)}


def fit_mnl(sets: list[list[list[float]]], chosen: list[int], iters: int = 50) -> dict[str, Any]:
    """Conditional logit by Newton-Raphson; returns estimates, standard errors, log-likelihood."""
    k = len(sets[0][0])
    beta = [0.0] * k
    for _ in range(iters):
        grad = [0.0] * k
        for xs, c in zip(sets, chosen, strict=True):
            p = probabilities(xs, beta)
            for i in range(k):
                grad[i] += xs[c][i] - sum(pj * row[i] for pj, row in zip(p, xs, strict=True))
        info = information(sets, beta)
        inv = inverse(info)
        if inv is None:
            return {"converged": False, "reason": "singular information matrix"}
        step = [sum(inv[i][j] * grad[j] for j in range(k)) for i in range(k)]
        beta = [b + s for b, s in zip(beta, step, strict=True)]
        if max(abs(s) for s in step) < 1e-8:
            break
    inv = inverse(information(sets, beta))
    ll = sum(math.log(probabilities(xs, beta)[c]) for xs, c in zip(sets, chosen, strict=True))
    return {"converged": True, "beta": beta, "se": [math.sqrt(inv[i][i]) for i in range(k)], "log_likelihood": ll}


def simulate(sets: list[list[list[float]]], beta: list[float], seed: int) -> list[int]:
    rng = random.Random(seed)
    out = []
    for xs in sets:
        p = probabilities(xs, beta)
        u, acc = rng.random(), 0.0
        for j, pj in enumerate(p):
            acc += pj
            if u <= acc:
                out.append(j)
                break
        else:
            out.append(len(p) - 1)
    return out
