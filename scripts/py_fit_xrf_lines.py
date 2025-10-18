# py_fit_xrf_lines.py (Version 3: Function-based)
import sys, argparse, numpy as np, matplotlib.pyplot as plt
from pathlib import Path
from scipy.optimize import curve_fit

LINE_ENERGIES = {"Mg": 1.254, "Al": 1.486, "Si": 1.740}

def gaussian(x, amplitude, mean, sigma):
    return amplitude * np.exp(-((x - mean)**2) / (2 * sigma**2))

def multi_peak_model(x, amp_mg, mean_mg, sig_mg, amp_al, mean_al, sig_al, amp_si, mean_si, sig_si):
    return gaussian(x, amp_mg, mean_mg, sig_mg) + \
           gaussian(x, amp_al, mean_al, sig_al) + \
           gaussian(x, amp_si, mean_si, sig_si)

def fit_xrf_lines(residual_file_path):
    """Loads a residual spectrum, fits the lines, and returns the results."""
    try:
        data = np.loadtxt(residual_file_path)
        energy_kev, residual_counts = data[:, 0], data[:, 1]
    except (FileNotFoundError, IndexError):
        return None # Return None if file is bad

    amp_guess_mg = np.max(residual_counts[(energy_kev > 1.2) & (energy_kev < 1.3)])
    amp_guess_al = np.max(residual_counts[(energy_kev > 1.4) & (energy_kev < 1.55)])
    amp_guess_si = np.max(residual_counts[(energy_kev > 1.7) & (energy_kev < 1.8)])

    p0 = [max(0, amp_guess_mg), LINE_ENERGIES["Mg"], 0.05,
          max(0, amp_guess_al), LINE_ENERGIES["Al"], 0.05,
          max(0, amp_guess_si), LINE_ENERGIES["Si"], 0.05]
    bounds = ([0, 1.2, 0.02, 0, 1.4, 0.02, 0, 1.7, 0.02],
              [np.inf, 1.3, 0.1, np.inf, 1.6, 0.1, np.inf, 1.8, 0.1])

    try:
        popt, pcov = curve_fit(multi_peak_model, energy_kev, residual_counts, p0=p0, bounds=bounds, maxfev=5000)
    except (ValueError, RuntimeError):
        return None # Return None if fit fails

    params = {"Mg": popt[0:3], "Al": popt[3:6], "Si": popt[6:9]}
    errors = {"Mg": pcov[0:3, 0:3], "Al": pcov[3:6, 3:6], "Si": pcov[6:9, 6:9]}
    
    results = {}
    for elem, (amp, mean, sig) in params.items():
        flux = amp * sig * np.sqrt(2 * np.pi)
        results[f"{elem}_flux"] = flux

    if results['Si_flux'] > 0:
        results['mg_si_ratio'] = results['Mg_flux'] / results['Si_flux']
        results['al_si_ratio'] = results['Al_flux'] / results['Si_flux']
    else:
        results['mg_si_ratio'] = np.nan
        results['al_si_ratio'] = np.nan
        
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Fit Gaussian peaks to a residual XRF spectrum.")
    parser.add_argument('residual_file', type=Path, help="Path to the residual spectrum text file.")
    args = parser.parse_args()
    
    final_results = fit_xrf_lines(args.residual_file)
    if final_results:
        print("\n--- Fit Results ---")
        print(final_results)