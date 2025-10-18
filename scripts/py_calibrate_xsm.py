

#!/usr/bin/env python3
"""
py_calibrate_xsm.py (Version 3: Direct Data Input)

This version no longer reads files. It takes NumPy arrays directly
and creates the interpolation function.
"""
import numpy as np
from scipy.interpolate import interp1d

def create_xsm_interpolator(energy_kev, flux):
    """
    Takes energy and flux arrays and returns a flux interpolation function.
    """
    if len(energy_kev) == 0 or len(flux) == 0:
        print("Error: Received empty arrays for interpolation.")
        return None
        
    # Create an interpolation function.
    solar_flux_func = interp1d(
        energy_kev, 
        flux, 
        kind='linear', 
        bounds_error=False, 
        fill_value=0.0
    )
    
    return solar_flux_func

if __name__ == '__main__':
    print("This script provides a helper function and is called by run_analysis_batch.py")
