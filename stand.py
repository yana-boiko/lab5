
import argparse, json, math, os, random, sys, threading, time

CAPACITY = 64
WARMUP, D = 1.0, 10.0
now = time.perf_counter_ns


class GlobalLock:
    def __init__(self):
        self.m = threading.Lock()

    def acquire_read(self):
        self.m.acquire()

    def release_read(self):
        self.m.release()

    acquire_write = acquire_read
    release_write = release_read


class PQueue:
    def __init__(self, lock):
        self.lock = lock
        self.h = []

    def push(self, p, x):
        t_call = now()
        self.lock.acquire_write()
        t_acq = now()
        h = self.h
        ok = len(h) < CAPACITY
        if ok:
            h.append((p, x))
            i = len(h) - 1
            while i > 0 and h[(i - 1) // 2][0] < h[i][0]:
                h[(i - 1) // 2], h[i] = h[i], h[(i - 1) // 2]
                i = (i - 1) // 2
        self.lock.release_write()
        return ok, t_call, t_acq, now()

    def pop(self):
        t_call = now()
        self.lock.acquire_write()
        t_acq = now()
        h = self.h
        item = None
        if h:
            item = h[0]
            last = h.pop()
            if h:
                h[0] = last
                i, n = 0, len(h)
                while True:
                    m, l, r = i, 2 * i + 1, 2 * i + 2
                    if l < n and h[l][0] > h[m][0]:
                        m = l
                    if r < n and h[r][0] > h[m][0]:
                        m = r
                    if m == i:
                        break
                    h[i], h[m] = h[m], h[i]
                    i = m
        self.lock.release_write()
        return item, t_call, t_acq, now()

    def peek_max(self):
        t_call = now()
        self.lock.acquire_read()
        t_acq = now()
        item = self.h[0] if self.h else None
        self.lock.release_read()
        return item, t_call, t_acq, now()

    def size(self):
        t_call = now()
        self.lock.acquire_read()
        t_acq = now()
        n = len(self.h)
        self.lock.release_read()
        return n, t_call, t_acq, now()


def thread_body(k, q, t_begin, t_warm, t_end, res):
    writer = k % 2 == 1
    rnd = random.Random(k)
    ops, pushed, popped = [], [], []

    time.sleep(max(0, (t_begin - now()) / 1e9))
    t, i = now(), 0

    while t < t_end:
        i += 1
        for step in (0, 1):
            if writer and step == 0:
                p, x = rnd.randrange(1000), k * 10**9 + i
                r, tc, ta, t = q.push(p, x)
                assert r, "черга переповнена"
                pushed.append(x)

            elif writer:
                r, tc, ta, t = q.pop()
                popped.append(r[1])

            elif step == 0:
                r, tc, ta, t = q.peek_max()

            else:
                r, tc, ta, t = q.size()

            if tc >= t_warm and t <= t_end:
                ops.append((t - tc, ta - tc))

    res[k - 1] = {
        "ops": ops,
        "pushed": pushed,
        "popped": popped
    }


def check(q, res):
    h = q.h
    pushed = [x for r in res for x in r["pushed"]]
    popped = [x for r in res for x in r["popped"]]

    t = PQueue(GlobalLock())
    for j in range(50):
        t.push(random.randrange(1000), j)

    order = []
    while t.h:
        top = t.peek_max()[0][0]
        assert top == max(p for p, _ in t.h)
        order.append(t.pop()[0][0])

    return {
        "розмір від 0 до 64": 0 <= len(h) <= CAPACITY,
        "властивість купи": all(
            h[(i - 1) // 2][0] >= h[i][0]
            for i in range(1, len(h))
        ),
        "жоден елемент не вийнято двічі":
            len(popped) == len(set(popped)),
        "покладені = вийняті + залишок":
            sorted(pushed) == sorted(
                popped + [x for _, x in h]
            ),
        "peek_max і pop у порядку спадання":
            order == sorted(order, reverse=True),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sync", choices=["global"], default="global")
    ap.add_argument("--mode", choices=["run", "x1", "tcs"], default="run")
    ap.add_argument("--threads", type=int, default=12)
    ap.add_argument("--d", type=float, default=D)
    ap.add_argument("--rep", type=int, default=1)

    a = ap.parse_args()

    n, nw, nr = a.threads, (a.threads + 1) // 2, a.threads // 2
    q = PQueue(GlobalLock())

    print(
        f"Python {sys.version.split()[0]}, "
        f"логічних ядер {os.cpu_count()}, "
        f"n={n}, n_w={nw}, n_r={nr}, sync={a.sync}"
    )

    t_begin = now() + int(0.5e9)
    t_warm = t_begin + int(WARMUP * 1e9)
    t_end = t_warm + int(a.d * 1e9)

    if a.mode == "x1":
        rnd, cnt, i, t = random.Random(0), 0, 0, now()

        while t < t_end:
            i += 1
            q.push(rnd.randrange(1000), i)
            q.pop()
            q.peek_max()
            t = q.size()[3]

            if t > t_warm:
                cnt += 4

        x1 = cnt / a.d
        print(f"X_1 = {x1:.0f} оп/с")

        with open("results/x1.jsonl", "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {"sync": a.sync, "rep": a.rep, "x1": x1},
                    ensure_ascii=False
                ) + "\n"
            )
        return

    if a.mode == "tcs":
        rnd, i, t, cyc, sw, sr = random.Random(0), 0, now(), 0, 0, 0

        while t < t_end:
            i += 1
            o1 = q.push(rnd.randrange(1000), i)
            o2 = q.pop()
            o3 = q.peek_max()
            o4 = q.size()
            t = o4[3]

            if o1[1] >= t_warm:
                cyc += 1
                sw += (o1[3] - o1[2]) + (o2[3] - o2[2])
                sr += (o3[3] - o3[2]) + (o4[3] - o4[2])

        tw, tr = sw / (2 * cyc) / 1e3, sr / (2 * cyc) / 1e3
        tbar = (nw * tw + nr * tr) / n

        print(
            f"t_cs,w = {tw:.3f} мкс, "
            f"t_cs,r = {tr:.3f} мкс, "
            f"середнє t_cs = {tbar:.3f} мкс, "
            f"межа 1/t_cs = {1e6 / tbar:.0f} оп/с"
        )

        with open("results/tcs.jsonl", "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "rep": a.rep,
                        "tw": tw,
                        "tr": tr,
                        "tbar": tbar,
                        "limit": 1e6 / tbar
                    },
                    ensure_ascii=False
                ) + "\n"
            )
        return

    res = [None] * n

    ts = [
        threading.Thread(
            target=thread_body,
            args=(k, q, t_begin, t_warm, t_end, res)
        )
        for k in range(1, n + 1)
    ]

    for t in ts:
        t.start()

    for t in ts:
        t.join()

    out = {"sync": a.sync, "rep": a.rep, "n": n, "threads": {}}

    for role, ids, cnt in (
        ("запис", range(1, n + 1, 2), nw),
        ("читання", range(2, n + 1, 2), nr),
        ("разом", range(1, n + 1), n)
    ):
        ops = [o for k in ids for o in res[k - 1]["ops"]]
        per = [len(res[k - 1]["ops"]) for k in ids]
        mu = sum(per) / len(per)
        tau = sorted(o[0] for o in ops)
        N = len(ops)

        out[role] = {
            "N": N,
            "X": N / a.d,
            "p50_us": tau[math.ceil(0.5 * N) - 1] / 1e3,
            "p99_us": tau[math.ceil(0.99 * N) - 1] / 1e3,
            "w": sum(o[1] for o in ops) / 1e9 / (cnt * a.d),
            "wait_max_ms": max(o[1] for o in ops) / 1e6,
            "cv": math.sqrt(
                sum((c - mu) ** 2 for c in per) / len(per)
            ) / mu
        }

        if role != "разом":
            for k, c in zip(ids, per):
                out["threads"][k] = c

    print("\nОперацій по потоках:", out["threads"])

    for role in ("запис", "читання", "разом"):
        s = out[role]
        print(
            f"{role}: N={s['N']}  "
            f"X={s['X']:.0f} оп/с  "
            f"p50={s['p50_us']:.1f} мкс  "
            f"p99={s['p99_us']:.1f} мкс  "
            f"w={s['w']:.3f}  "
            f"cv={s['cv']:.3f}"
            + (
                f"  найбільший t_wait={s['wait_max_ms']:.2f} мс"
                if role == "запис" else ""
            )
        )

    out["invariants"] = check(q, res)

    print("Інваріанти:")

    for name, ok in out["invariants"].items():
        print(f"  {'OK ' if ok else 'ПОМИЛКА'} {name}")

    with open("results/runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
