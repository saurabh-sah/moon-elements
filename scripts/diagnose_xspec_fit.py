print("running..")
#!/usr/bin/env python3
"""
diagnose_xspec_fit.py

A simple, interactive script to diagnose the XSPEC fit for a single observation.
It will open a plot window to show the data and the fit result.
"""
from pathlib import Path
import xspec

# --- CONFIGURE THE FILES FOR THE OBSERVATION YOU WANT TO TEST ---
# We will test the very first observation (index 0)
OBS_ID = "ch2_cla_l1_20250801T022933069_20250801T022949069"
PHA_FILE = Path(f"/home/saurabh/moon_project/results/batch_run/{OBS_ID}_xsm.pha")

# --- Paths to your calibration files ---
XSM_BKG_FILE = Path("/home/saurabh/moon_project/calib/XSM/caldb/bkgspec/ch2_xsm_20200128_bkg.pha")
XSM_RSP_FILE = Path("/home/saurabh/moon_project/calib/XSM/caldb/CH2xsmrspwitharea_open20191214v01.rsp")

# --- SCRIPT START ---
print("--- Starting XSPEC Diagnostic Script ---")

try:
    # 1. Clear previous state and set up
    xspec.AllData.clear()
    xspec.AllModels.clear()
    xspec.Fit.query = "no"
    xspec.Xset.chatter = 10  # Maximum text output
    
    # 2. Load all data and responses
    print(f"Loading data: {PHA_FILE.name}")
    s = xspec.Spectrum(str(PHA_FILE))
    s.background = str(XSM_BKG_FILE)
    s.response = str(XSM_RSP_FILE)
    
    # 3. Set statistic and ignore channels
    xspec.Fit.statMethod = "cstat"
    xspec.AllData.ignore("**-0.7 10.0-**")
    
    # 4. Set up the plot window
    # This is the key change: we will now plot to a window ("/xw")
    xspec.Plot.device = "/xw"
    xspec.Plot.xAxis = "keV"
    
    # Show the data before we do anything
    print("--- Displaying loaded data. Check the plot window. ---")
    xspec.Plot("data")
    input("Press Enter to define the model and continue...")

    # 5. Define the model and parameters
    m = xspec.Model("apec")
    m.apec.kT = 0.9
    m.apec.norm = 1.0
    m.apec.kT.frozen = False
    m.apec.norm.frozen = False
    
    # Show the data with the initial guess for the model
    print("--- Displaying data with initial model guess. ---")
    xspec.Plot("data, model")
    input("Press Enter to perform the fit...")

    # 6. Perform the fit
    print("--- Performing fit... ---")
    xspec.Fit.perform()
    
    # 7. Show the final fit result
    print("--- Displaying final fit result. ---")
    xspec.Plot("fit")
    
    # 8. Show the final parameters
    print("\n--- Final Best-Fit Parameters ---")
    xspec.AllModels.show()

    input("\nAnalysis complete. Press Enter to exit.")

except Exception as e:
    import traceback
    print("\n--- AN ERROR OCCURRED ---")
    traceback.print_exc()