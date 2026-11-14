import json, re, csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")              # save to file; WSL has no plot window
import matplotlib.pyplot as plt

root = Path.home() / "projects/cubtc_isotherm"
pat = {
    "abs": re.compile(r"Abs\. loading average\s+(\S+)\s+\+/-\s+(\S+)\s+\[mol/kg-framework\]"),
    "exc": re.compile(r"Excess loading average\s+(\S+)\s+\+/-\s+(\S+)\s+\[mol/kg-framework\]"),
}

rows = []
for d in sorted(root.glob("P_*Pa")):
    sim = json.loads((d / "simulation.json").read_text())
    p_bar = sim["Systems"][0]["ExternalPressure"] / 1e5
    T = sim["Systems"][0]["ExternalTemperature"]
    txt = next((d / "output").glob("output_*.txt")).read_text()
    phi = re.search(r"Fugacity coefficient:\s+(\S+)", txt)
    row = {"P_bar": p_bar, "T_K": T, "fug_coeff": float(phi.group(1)) if phi else None}
    for k, rx in pat.items():
        val, err = rx.findall(txt)[-1]          # last = final summary
        row[f"{k}_mmol_g"], row[f"{k}_err"] = float(val), float(err)
    rows.append(row)

rows.sort(key=lambda r: r["P_bar"])
with open(root / "isotherm.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)

for r in rows:
    print(f"{r['P_bar']:7.3f} bar  phi={r['fug_coeff']:.3f}  excess {r['exc_mmol_g']:6.3f} ± {r['exc_err']:.3f} mmol/g")

P = [r["P_bar"] for r in rows]
plt.errorbar(P, [r["exc_mmol_g"] for r in rows], yerr=[r["exc_err"] for r in rows],
             fmt="o-", capsize=3, label="GCMC excess")
plt.errorbar(P, [r["abs_mmol_g"] for r in rows], yerr=[r["abs_err"] for r in rows],
             fmt="s--", capsize=3, alpha=0.6, label="GCMC absolute")
plt.errorbar([30.0], [8.25], fmt="*", ms=12, color="k", label="Experiment, 30 bar (8.25 mmol/g)")
plt.xlabel("CO$_2$ pressure (bar)")
plt.ylabel("CO$_2$ uptake (mmol/g)")
plt.title(f"CO$_2$ in HKUST-1 (Cu-BTC), {rows[0]['T_K']:.0f} K")
plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
plt.savefig(root / "isotherm.png", dpi=200)
print("saved isotherm.csv and isotherm.png")