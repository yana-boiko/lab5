import json, statistics as st

runs = [json.loads(l) for l in open("results/runs.jsonl", encoding="utf-8")]
runs = [r for r in runs if r["sync"] == "global"]
tcs = [json.loads(l) for l in open("results/tcs.jsonl", encoding="utf-8")]
print(f"прогонів: {len(runs)}, вимірів t_cs: {len(tcs)}")
for role in ("запис", "читання", "разом"):
    med = {k: st.median(r[role][k] for r in runs) for k in ("N", "X", "p50_us", "p99_us", "wait_max_ms", "w", "cv")}
    print(role, {k: round(v, 3) for k, v in med.items()})
tw, tr, tb = (st.median(t[k] for t in tcs) for k in ("tw", "tr", "tbar"))
print(f"t_cs,w = {tw:.3f} мкс, t_cs,r = {tr:.3f} мкс, t_cs середнє = {tb:.3f} мкс, межа 1/t_cs = {1e6 / tb:.0f} оп/с")