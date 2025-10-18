# ======================================
# extract_xsm_metadata.py
# ======================================

from astropy.io import fits
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm

# Path to one day's XSM FITS file
xsm_file = Path("/home/saurabh/moon_project/data/XSM/xsm_2025_08/ch2_xsm_20250801_v1/xsm/data/2025/08/01/raw/ch2_xsm_20250801_v1_level1.fits")

# Output folder
output_dir = Path("/home/saurabh/moon_project/metadata/metadata_XSM/Aug_25")
output_dir.mkdir(parents=True, exist_ok=True)

# Open the FITS file
with fits.open(xsm_file, memmap=True) as hdul:
    hdr = hdul[1].header
    data = hdul[1].data

    # Extract table columns
    utc = data["UTCString"]
    met = data["Time"]
    frame = data["FrameNumber"]
    flag = data["DecodingStatusFlag"]
    spectra = data["DataArray"]   # shape: (n_rows, 1024)

    # Compute simple metrics to summarize each second
    mean_counts = np.mean(spectra, axis=1)
    total_counts = np.sum(spectra, axis=1)

    # Create DataFrame
    df = pd.DataFrame({
        "UTC": utc,
        "MET": met,
        "FrameNumber": frame,
        "MeanCounts": mean_counts,
        "TotalCounts": total_counts,
        "DecodingFlag": flag,
        "SourceFile": xsm_file.name
    })

# Save to CSV
out_path = output_dir / f"metadata_XSM_{xsm_file.stem}.csv"
df.to_csv(out_path, index=False)

print(f"✅ Saved {len(df)} rows to {out_path}")
