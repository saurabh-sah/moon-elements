



#!/usr/bin/env python3
import argparse, os
from xspec import *

parser = argparse.ArgumentParser(description="XSM PyXspec fitting pipeline")
parser.add_argument("--pha", required=True)
parser.add_argument("--rsp", required=True)
parser.add_argument("--outdir", required=True)
parser.add_argument("--emin", type=float, default=0.5)
parser.add_argument("--emax", type=float, default=10.0)
args = parser.parse_args()

pha = os.path.abspath(args.pha)
rsp = os.path.abspath(args.rsp)
outdir = os.path.abspath(args.outdir)
os.makedirs(outdir, exist_ok=True)

print(f"🟢 Loading XSM spectrum: {pha}")

# Load spectrum
s = Spectrum(pha)

# Attach response & background
bkg = "/home/saurabh/moon_project/calib/XSM/caldb/bkgspec/ch2_xsm_20200128_bkg.pha"
s.background = bkg
print(f"✅ Background attached: {bkg}")
s.response = rsp
print(f"✅ Response attached: {rsp}")

# ----------- FIX BAD CHANNELS -------------
AllData.ignore("**-0.5 10.0-**")   # limit range
AllData.ignore("bad")              # ignore channels marked bad
s.groupCounts(50)                  # min 50 counts/bin
print("✅ Grouped to min 50 counts per bin")

# ----------- XSPEC ENV --------------------
Fit.statMethod = "chi"
Fit.method = "leven 1000 0.01"
Xset.abund = "wilm"
Xset.xsect = "vern"
Fit.query = "yes"

# ----------- DEFINE MODEL -----------------
print("✅ Defining TBabs*(apec+gaussian+gaussian)")
m = Model("tbabs*(apec+gaussian+gaussian)")

# TBabs nH
m(1).values = "0.05 0.01 0.01 0.001 1.0"
# APEC (solar scatter)
m(2).values = "1.0 0.1 0.1 0.1 10.0"
m(3).frozen = True
m(5).values = "1.0"
# Gaussian 1 (Mg line ~1.25 keV)
m(6).values = "1.25 0.01 0.01 0.01 1.5"
m(7).values = "0.05"
m(8).values = "1.0"
# Gaussian 2 (Si line ~1.8 keV)
m(9).values = "1.85 0.01 0.01 0.01 2.0"
m(10).values = "0.05"
m(11).values = "1.0"

# ----------- FIT --------------------------
print("🔧 Performing spectral fit...")
Fit.nIterations = 2000
Fit.perform()

reduced_chi = Fit.statistic / Fit.dof if Fit.dof > 0 else 999
print(f"📊 Reduced Chi² = {reduced_chi:.2f}")

if reduced_chi < 2:
    try:
        Fit.error("1-11")
    except Exception as e:
        print(f"⚠️ XSPEC error calc failed: {e}")
else:
    print("⚠️ Skipping error calc due to high Chi².")

# ----------- SAVE RESULTS -----------------
out_txt = os.path.join(outdir, "xsm_fit_results.txt")
with open(out_txt, "w") as f:
    f.write(f"Chi² = {Fit.statistic:.3e}\n")
    f.write(f"DOF = {Fit.dof}\n")
    f.write(f"Reduced Chi² = {reduced_chi:.3f}\n\n")
    f.write("Model Parameters:\n")
    for p in m.parameterValues:
        f.write(f"{p}\n")

print(f"✅ Results written to {out_txt}")
print("🏁 Done.")
