import json, statistics as st

runs = [json.loads(l) for l in open("results/runs.jsonl", encoding="utf-8")]
sets = {"G": [r for r in runs if r["sync"] == "global"], "RW": [r for r in runs if r["sync"] == "rw"]}
threads = {"запис": 6, "читання": 6}

def col(s, role):
    d = {k: st.median(r[role][k] for r in sets[s]) for k in ("X", "p50_us", "p99_us", "wait_max_ms", "w", "cv")}
    d["x"] = d["X"] / threads[role]
    d["h"] = d["p99_us"] / d["p50_us"]
    d["phi"] = st.median(r[role]["X"] / r["разом"]["X"] for r in sets[s])
    return d

cols = {(s, role): col(s, role) for s in ("G", "RW") for role in ("запис", "читання")}
rows = [("X, оп/с", "X"), ("x на потік, оп/с", "x"), ("p50, мкс", "p50_us"), ("p99, мкс", "p99_us"),
        ("h = p99/p50", "h"), ("найбільший t_wait, мс", "wait_max_ms"), ("w", "w"), ("cv", "cv"), ("phi", "phi")]
print(f"прогонів: G {len(sets['G'])}, RW {len(sets['RW'])}")
print(f"{'показник':<24}{'G запис':>12}{'G читання':>12}{'RW запис':>12}{'RW читання':>12}{'RW/G запис':>12}{'RW/G чит.':>12}")
for name, k in rows:
    v = [cols[(s, role)][k] for s in ("G", "RW") for role in ("запис", "читання")]
    ratio = [v[2] / v[0] if v[0] else v[2] - v[0], v[3] / v[1] if v[1] else v[3] - v[1]]
    print(f"{name:<24}" + "".join(f"{x:>12.4f}" for x in v + ratio))