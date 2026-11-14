import json, shutil, subprocess, time
from pathlib import Path

template = Path.home() / "projects/raspa3-src/examples/basic/11_mc_adsorption_of_co2_in_cu_btc"
root = Path.home() / "projects/cubtc_isotherm"
T = 298.0                                                  # K
pressures = [1e3, 5e3, 1e4, 2.5e4, 5e4, 1e5, 2e5, 5e5,     # Pa (0.01 to 5 bar)
             1e6, 2e6, 3e6]                                # 10, 20, 30 bar (toward saturation)

procs = []
for p in pressures:
    d = root / f"P_{int(p)}Pa"
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(template, d, ignore=shutil.ignore_patterns("output"))

    sim = json.loads((d / "simulation.json").read_text())
    sim["NumberOfCycles"] = 20000
    sim["NumberOfInitializationCycles"] = 5000
    sim["PrintEvery"] = 1000
    sim["Systems"][0]["ExternalTemperature"] = T
    sim["Systems"][0]["ExternalPressure"] = p
    # Real-gas correction: with no FugacityCoefficient key, RASPA3 computes it from the
    # Peng-Robinson EOS using Tc/Pc/omega in CO2.json (phi ~ 1 at low P, ~0.85 at 30 bar).
    for c in sim["Components"]:
        c.pop("FugacityCoefficient", None)
    (d / "simulation.json").write_text(json.dumps(sim, indent=2))

    (d / "started.txt").write_text(f"{time.time()}\n")     # used by monitor.py for ETA
    log = open(d / "log.txt", "w")
    procs.append(subprocess.Popen(["raspa3"], cwd=d, stdout=log, stderr=subprocess.STDOUT))
    print("started", d.name, flush=True)

for pr in procs:
    pr.wait()
print("all done", flush=True)
