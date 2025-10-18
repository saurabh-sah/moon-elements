

#!/usr/bin/env python3
"""
prepare_xsm_for_xspec.py (Version 8: Final Absolute Path Fix)
"""
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from astropy.io import fits
from astropy.time import Time

def prepare_xsm_spectrum(prime_csv_path, xsm_fits_path, obs_index, output_pha_path, xsm_bkg_path, xsm_rsp_path):
    df_prime = pd.read_csv(prime_csv_path)
    df_prime.columns = [c.strip().lower() for c in df_prime.columns]
    target_obs = df_prime.iloc[obs_index]
    start_time, end_time = Time(target_obs['start_time']), Time(target_obs['end_time'])
    
    with fits.open(xsm_fits_path) as hdul:
        xsm_data = hdul['DATA'].data
        xsm_times = Time(xsm_data['UTCString'])
        time_mask = (xsm_times >= start_time) & (xsm_times <= end_time)
        xsm_subset = xsm_data[time_mask]

    if len(xsm_subset) == 0:
        print(f"Error: No XSM data found for index {obs_index} in the given time window.")
        return False

    coadded_2048 = np.sum(xsm_subset['DataArray'], axis=0, dtype=np.int32)
    rebinned_512 = coadded_2048.reshape(512, 4).sum(axis=1)
    total_exposure = float(len(xsm_subset))
    
    channel_col = fits.Column(name='CHANNEL', format='I', array=np.arange(512))
    counts_col = fits.Column(name='COUNTS', format='J', array=rebinned_512, unit='count')
    
    hdu_spectrum = fits.BinTableHDU.from_columns([channel_col, counts_col])
    
    hdr = hdu_spectrum.header
    hdr['EXTNAME'] = ('SPECTRUM', 'Name of this extension')
    hdr['TELESCOP'] = ('CH-2_ORBITER', 'Telescope (mission) name')
    hdr['INSTRUME'] = ('CH2_XSM', 'Instrument name')
    hdr['EXPOSURE'] = (total_exposure, 'Exposure time in seconds')
    
    # === THIS IS THE CORRECTED SECTION ===
    # We now write the FULL PATH to the header by removing .name
    hdr['BACKFILE'] = (str(xsm_bkg_path), 'Associated background file')
    hdr['RESPFILE'] = (str(xsm_rsp_path), 'Associated response file')
    # =====================================

    hdr['ANCRFILE'] = ('none', 'Associated ancillary file')
    # ... (the rest of the header keywords are correct and unchanged) ...
    hdr['FILTER'] = ('NONE', 'Filter in use')
    hdr['AREASCAL'] = (1.0, 'Area scaling factor')
    hdr['BACKSCAL'] = (1.0, 'Background scaling factor')
    hdr['CORRFILE'] = ('none', 'Associated correction file')
    hdr['CORRSCAL'] = (1.0, 'Correction file scaling factor')
    hdr['HDUCLASS'] = ('OGIP', 'Format conforms to OGIP standard')
    hdr['HDUCLAS1'] = ('SPECTRUM', 'This is a PHA spectrum')
    hdr['HDUCLAS2'] = ('TOTAL', 'Spectrum is a total of source + background')
    hdr['HDUVERS'] = ('1.2.1', 'Version of the format')
    hdr['POISSERR'] = (True, 'Poissonian errors are to be assumed')
    hdr['CHANTYPE'] = ('PHA', 'Channels are Pulse Height Analyser channels')
    hdr['DETCHANS'] = (512, 'Total number of detector channels')
    hdr['QUALITY'] = (0, 'No data quality information specified')
    hdr['STAT_ERR'] = (0, 'No statistical error specified')
    hdr['SYS_ERR'] = (0, 'No systematic error specified')
    hdr['GROUPING'] = (0, 'No grouping of the data has been defined')

    primary_hdu = fits.PrimaryHDU()
    hdul_out = fits.HDUList([primary_hdu, hdu_spectrum])
    hdul_out.writeto(output_pha_path, overwrite=True)
    
    print(f"✅ Successfully created definitive PHA file: {output_pha_path}")
    return True

if __name__ == '__main__':
    # This block now correctly allows the script to be run from the command line
    
    parser = argparse.ArgumentParser(description="Prepare a co-added XSM spectrum for XSPEC analysis.")
    parser.add_argument('--prime-csv', type=Path, required=True)
    parser.add_argument('--xsm-fits', type=Path, required=True)
    parser.add_argument('--xsm-bkg', type=Path, required=True)
    parser.add_argument('--xsm-rsp', type=Path, required=True)
    parser.add_argument('--index', type=int, default=0, help="Index of the observation to process.")
    parser.add_argument('--output', type=Path, required=True, help="Path to save the output .pha file.")
    
    args = parser.parse_args()
    
    if not args.prime_csv.exists():
         print(f"Error: The prime CSV file was not found at '{args.prime_csv}'")
    else:
        prepare_xsm_spectrum(
            args.prime_csv, 
            args.xsm_fits, 
            args.index, 
            args.output,
            args.xsm_bkg,
            args.xsm_rsp
        )