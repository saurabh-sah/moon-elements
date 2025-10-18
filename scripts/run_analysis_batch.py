print("Finally it is Working..")
            

#!/usr/bin/env python3
"""
run_analysis_batch.py (Version 22: Final AttributeError Fix)

This is the final, definitive version of the main batch script,
containing all path definitions and the correct pyxspec logic.
"""
import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.optimize import minimize
import traceback
import xspec
import shutil

from prepare_xsm_for_xspec import prepare_xsm_spectrum
from py_calibrate_xsm import create_xsm_interpolator
from py_forward_model_and_subtract import *
from py_fit_xrf_lines import fit_xrf_lines

# --- Corrected and Centralized File Paths ---
PRIME_CSV_FILE = Path("/home/saurabh/moon_project/metadata/filtered_subsets/match_CLASS_XSM_20250801_prime.csv")
XSM_FITS_FILE = Path("/home/saurabh/moon_project/data/XSM/xsm_2025_08/ch2_xsm_20250801_v1/xsm/data/2025/08/01/raw/ch2_xsm_20250801_v1_level1.fits")
CLASS_ARF_FILE = Path("/home/saurabh/moon_project/calib/CLASS/cla/calibration/class_arf_v1.arf")
CLASS_BKG_FILE = Path("/home/saurabh/moon_project/calib/CLASS/cla/calibration/background_allevents.fits")
XSM_BKG_FILE = Path("/home/saurabh/moon_project/calib/XSM/caldb/bkgspec/ch2_xsm_20200128_bkg.pha")
XSM_RSP_FILE = Path("/home/saurabh/moon_project/calib/XSM/caldb/CH2xsmrspwitharea_open20191214v01.rsp")
RESULTS_DIR = Path("/home/saurabh/moon_project/results/batch_run/")


def run_xspec_analysis_with_pyxspec(pha_file, bkg_file, rsp_file):
    xspec.AllData.clear(); xspec.AllModels.clear()
    xspec.Fit.query = "no"; xspec.Xset.chatter = 0; xspec.Xset.logChatter = 0
    s = xspec.Spectrum(str(pha_file)); s.background = str(bkg_file); s.response = str(rsp_file)
    xspec.Fit.statMethod = "cstat"; xspec.AllData.ignore("**-0.7 10.0-**")
    m = xspec.Model("apec"); m.apec.kT = 0.9; m.apec.norm = 1.0
    m.apec.kT.frozen = False; m.apec.norm.frozen = False
    xspec.Fit.perform()
    xspec.Plot.device = "/null"; xspec.Plot.xAxis = "keV"; xspec.Plot("model")
    energies = np.array(xspec.Plot.x(1)); fluxes = np.array(xspec.Plot.model(1))
    if len(energies) == 0 or len(fluxes) == 0:
        raise ValueError("pyxspec fit was unsuccessful and generated no data.")
    return energies, fluxes

def run_continuum_subtraction(class_fits_file, solarang_deg, gain, F_sun):
    obs_counts, energy_kev, exposure = load_class_spectrum(class_fits_file, gain)
    arf_func = load_arf_interpolator(CLASS_ARF_FILE)
    bkg_counts = load_background(CLASS_BKG_FILE)
    if len(bkg_counts) != len(obs_counts):
        new_bkg = np.zeros_like(obs_counts); n_min = min(len(bkg_counts), len(obs_counts)); new_bkg[:n_min] = bkg_counts[:n_min]; bkg_counts = new_bkg
    continuum_mask = ((energy_kev > 1.0) & (energy_kev < 1.2)) | ((energy_kev > 1.6) & (energy_kev < 1.7)) | ((energy_kev > 1.85) & (energy_kev < 2.2))
    solarang_rad = np.deg2rad(solarang_deg)
    physical_model = np.cos(solarang_rad) * F_sun(energy_kev)
    channel_width_kev = np.mean(np.diff(energy_kev))
    model_counts_per_alpha = physical_model * arf_func(energy_kev) * exposure * channel_width_kev
    net_obs_counts = obs_counts - bkg_counts
    with np.errstate(divide='ignore', invalid='ignore'):
        ratios = net_obs_counts[continuum_mask] / model_counts_per_alpha[continuum_mask]
        initial_alpha_guess = np.nanmedian(ratios)
        if not np.isfinite(initial_alpha_guess) or initial_alpha_guess <= 0: initial_alpha_guess = 0.1
    result = minimize(objective_function, x0=[initial_alpha_guess], args=(net_obs_counts, continuum_mask, model_counts_per_alpha), method='Nelder-Mead')
    best_alpha = result.x[0]
    best_fit_scatter = best_alpha * model_counts_per_alpha
    residual_xrf_counts = net_obs_counts - best_fit_scatter
    return energy_kev, residual_xrf_counts

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run the full analysis pipeline in batch mode.")
    parser.add_argument('--limit', type=int, default=None, help="Limit the run to the first N observations for testing.")
    args = parser.parse_args()
    RESULTS_DIR.mkdir(exist_ok=True, parents=True)
    print(f"--- Starting Full Batch Analysis ---")
    df_prime = pd.read_csv(PRIME_CSV_FILE)
    df_prime.columns = [c.strip().lower() for c in df_prime.columns]
    if args.limit:
        df_prime = df_prime.head(args.limit)
    all_results = []
    for index, row in df_prime.iterrows():
        print(f"\n--- Processing Observation {index+1}/{len(df_prime)} ---")
        obs_id = Path(row['class_filepath']).stem
        xsm_pha_file = RESULTS_DIR / f"{obs_id}_xsm.pha"
        unfolded_xsm_file = RESULTS_DIR / f"{obs_id}_unfolded.txt"
        residual_file = RESULTS_DIR / f"{obs_id}_residual.txt"
        try:
            prepare_xsm_spectrum(PRIME_CSV_FILE, XSM_FITS_FILE, index, xsm_pha_file, XSM_BKG_FILE, XSM_RSP_FILE)
            print("Step 2: Running XSPEC analysis via pyxspec...")
            energies, fluxes = run_xspec_analysis_with_pyxspec(xsm_pha_file, XSM_BKG_FILE, XSM_RSP_FILE)
            np.savetxt(unfolded_xsm_file, np.c_[energies, fluxes])
            print(f"--> Success: XSPEC step completed.")
            F_sun = create_xsm_interpolator(energies, fluxes)
            if F_sun is None:
                print(f"--> ERROR: Could not create solar interpolator. Skipping."); continue
            energy, residual = run_continuum_subtraction(Path(row['class_filepath']), row['solarang_deg'], row['gain_ev_ch'], F_sun)
            np.savetxt(residual_file, np.c_[energy, residual], header="Energy_keV Residual_Counts")
            print("Step 4: Fitting XRF lines...")
            line_results = fit_xrf_lines(residual_file)
            if line_results:
                line_results.update({'latitude': row['bore_lat'], 'longitude': row['bore_lon'], 'obs_id': obs_id}); all_results.append(line_results)
                print("--> Success. Results collected.")
            else:
                print("--> Warning: Line fitting failed.")
        except Exception:
            print(f"--> AN ERROR OCCURRED ON OBSERVATION {index}. SKIPPING.")
            traceback.print_exc()
            fail_dir = RESULTS_DIR / "failed_files"; fail_dir.mkdir(exist_ok=True)
            try: shutil.copy(xsm_pha_file, fail_dir / xsm_pha_file.name)
            except Exception as copy_e: print(f"--> Could not copy failing file: {copy_e}")
            continue
    print("\n--- Batch processing complete ---")
    if all_results:
        final_df = pd.DataFrame(all_results); output_csv = RESULTS_DIR / "final_abundance_ratios.csv"
        final_df.to_csv(output_csv, index=False)
        print(f"\n✅ All results saved to: {output_csv}"); print("--- Final Results Sample ---"); print(final_df.head())
    else:
        print("\nNo observations were processed successfully.")