#!/usr/bin/env python3
"""
py_forward_model_and_subtract.py (Helper Functions - Final Version)

This script only contains the necessary helper functions. It does not
import from other scripts.
"""
from pathlib import Path
import numpy as np
from astropy.io import fits

def load_class_spectrum(fits_path, gain):
    with fits.open(fits_path) as hdul:
        hdr = hdul['SPECTRUM'].header
        data = hdul['SPECTRUM'].data
        obs_counts = data['COUNTS'].astype(np.float64)
        channels = data['CHANNEL']
        exposure = hdr['EXPOSURE']
        energy_kev = (gain * channels) / 1000.0
    return obs_counts, energy_kev, exposure

def load_arf_interpolator(arf_path):
    with fits.open(arf_path) as hdul:
        data = hdul['SPECRESP'].data
        e_low = data['E_LOW']
        e_high = data['E_HIGH']
        specresp = data['SPECRESP']
        e_mid = (e_low + e_high) / 2.0
    return lambda E: np.interp(E, e_mid, specresp, left=0.0, right=0.0)

def load_background(bkg_path):
    with fits.open(bkg_path) as hdul:
        data = hdul['SPECTRUM'].data
        if 'COUNTS' in data.columns.names:
            return data['COUNTS'].astype(np.float64)
        elif 'RATE' in data.columns.names:
            return data['RATE'].astype(np.float64)
    raise KeyError("Could not find 'COUNTS' or 'RATE' in background file.")

def objective_function(alpha, observed_counts, continuum_mask, model_counts_per_alpha):
    predicted_counts = alpha * model_counts_per_alpha
    diff = (observed_counts[continuum_mask] - predicted_counts[continuum_mask])**2
    return np.sum(diff)

if __name__ == '__main__':
    print("This script provides helper functions and is called by run_analysis_batch.py")
