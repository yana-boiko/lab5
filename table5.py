import json, statistics as st

def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]

runs, x1, tcs = load("results/runs.jsonl"), load("results/x1.jsonl"), load("results/tcs.jsonl")
g = [r for r in runs if r["sync"] == "global"]
rw = [r for r in runs if r["sync"] == "rw"]
n, nw, nr = 12, 6, 6

def X(rs, role):
    return st.median(r[role]["X"] for r in rs)

XG, XRW = X(g, "разом"), X(rw, "разом")
XwG, XwRW = X(g, "запис"), X(rw, "запис")
XrG, XrRW = X(g, "читання"), X(rw, "читання")
X1G = st.median(x["x1"] for x in x1 if x["sync"] == "global")
X1RW = st.median(x["x1"] for x in x1 if x["sync"] == "rw")
tw, tr = st.median(t["tw"] for t in tcs), st.median(t["tr"] for t in tcs)
tbar = (nw * tw + nr * tr) / n * 1e-6          # секунди

print(f"n={n}  X_1(G)={X1G:.0f}  X_1(RW)={X1RW:.0f}  X(G)={XG:.0f}  X(RW)={XRW:.0f}")
print(f"S(n), глобальний замок = {XG / X1G:.4f}")
print(f"E(n), глобальний замок = {XG / X1G / n:.4f}")
print(f"S(n), RWLock           = {XRW / X1RW:.4f}")
print(f"E(n), RWLock           = {XRW / X1RW / n:.4f}")
print(f"S_w = {XwRW / XwG:.4f}   (X_w(RW)={XwRW:.0f}, X_w(G)={XwG:.0f})")
print(f"S_r = {XrRW / XrG:.4f}   (X_r(RW)={XrRW:.0f}, X_r(G)={XrG:.0f})")
print(f"S_Σ = {XRW / XG:.4f}")
print(f"t_cs,w={tw:.3f} мкс  t_cs,r={tr:.3f} мкс  t̄_cs={tbar * 1e6:.4f} мкс")
print(f"межа 1/t̄_cs = {1 / tbar:.0f} оп/с")
print(f"ρ = X(G)·t̄_cs = {XG * tbar:.4f}")
print(f"межа / X(G) = {1 / tbar / XG:.1f}")