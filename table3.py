import json, statistics as st

runs = [json.loads(l) for l in open("results/runs.jsonl", encoding="utf-8")]
g = [r for r in runs if r["sync"] == "global"]
rw = [r for r in runs if r["sync"] == "rw"]
print(f"прогонів: global {len(g)}, rw {len(rw)}\n\nТаблиця 3 (RWLock, медіани)")
for role in ("запис", "читання", "разом"):
    med = {k: st.median(r[role][k] for r in rw) for k in ("N", "X", "p50_us", "p99_us", "wait_max_ms", "w", "cv")}
    print(role, {k: round(v, 3) for k, v in med.items()})

print("\nТаблиця 4 (медіана за 3 прогони): потік, роль, глобальний замок, RWLock")
for k in range(1, 13):
    print(k, "запис" if k % 2 else "читання",
          int(st.median(r["threads"][str(k)] for r in g)), int(st.median(r["threads"][str(k)] for r in rw)))

print("\nX_1 (медіана)")
xs = [json.loads(l) for l in open("results/x1.jsonl", encoding="utf-8")]
for s in ("global", "rw"):
    print(s, round(st.median(x["x1"] for x in xs if x["sync"] == s)), "оп/с")