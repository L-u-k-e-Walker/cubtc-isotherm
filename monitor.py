"""Progress / ETA for running isotherm points.  Usage: python monitor.py [--watch SECONDS]"""
import re, sys, time
from pathlib import Path

root = Path(__file__).resolve().parent
init_rx = re.compile(r"^Initialization: Current cycle: (\d+) out of (\d+)", re.M)
prod_rx = re.compile(r"^Current cycle: (\d+) out of (\d+)", re.M)
load_rx = re.compile(r"Abs\. loading:?\s+([-\d.eE+]+)")

def fmt(s):
    s = int(s); return f"{s//3600}h{s%3600//60:02d}m" if s >= 3600 else f"{s//60}m{s%60:02d}s"

def report():
    rows, worst = [], 0.0
    for d in sorted(root.glob("P_*Pa"), key=lambda d: int(d.name[2:-2])):
        out = list((d / "output").glob("output_*.txt"))
        start = float((d / "started.txt").read_text()) if (d / "started.txt").exists() else None
        txt = out[0].read_text(errors="ignore") if out else ""
        if "Simulation finished!" in txt:
            m = re.search(r"Total simulation time:\s+([\d.]+)", txt)
            rows.append((d.name, 100.0, "done", fmt(float(m.group(1))) if m else "")); continue
        i, p = init_rx.findall(txt), prod_rx.findall(txt)
        ni = int(i[-1][1]) if i else 5000
        npd = int(p[-1][1]) if p else 20000
        done = (int(p[-1][0]) + ni) if p else (int(i[-1][0]) if i else 0)
        frac = done / (ni + npd)
        el = time.time() - start if start else 0
        eta = el / frac - el if frac > 0 else None
        if eta: worst = max(worst, eta)
        phase = "prod" if p else ("init" if i else "starting")
        rows.append((d.name, 100 * frac, phase, f"elapsed {fmt(el)}  ETA {fmt(eta) if eta else '?'}"))
    print(time.strftime("%H:%M:%S"))
    for name, pct, phase, info in rows:
        bar = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
        print(f"  {name:>13} [{bar}] {pct:5.1f}% {phase:8} {info}")
    print(f"  all points done in ~{fmt(worst)} (estimate updates every 1000 cycles)\n" if worst else "  all done\n")

if "--watch" in sys.argv:
    dt = int(sys.argv[sys.argv.index("--watch") + 1]) if len(sys.argv) > sys.argv.index("--watch") + 1 else 60
    while True: report(); time.sleep(dt)
else:
    report()
