# ================================
# extract_class_metadata.py
# ================================

from astropy.io import fits
from pathlib import Path
import pandas as pd
from tqdm import tqdm

BASE_DATA_ROOT = Path("/home/saurabh/moon_project/data/CLASS/ch2_cla_l1_2025_08/cla/data/calibrated/2025/08/")

# making a list of path of date folders
date_folders = [d for d in BASE_DATA_ROOT.rglob("*") if d.is_dir() and d != BASE_DATA_ROOT]

for data_root in tqdm(date_folders, desc="Processing Date Folders"):
    try:
        # 2️⃣ Prepare list of all FITS files sorted alpha
        # rglob repeatively goes through the directory 
        # rglob(),Path() available in pathlib
        # while *.fits is a filter that takes only files ending with .fits
        fits_files = sorted(data_root.rglob("*.fits"))

        if not fits_files:
            print("Error: No FITS files found. Check your 'data_root' path.")
        else:
            print(f"Found {len(fits_files)} files. Starting metadata extraction.")
        # 3️⃣ Prepare a list to collect all metadata
        rows = []

        # 4️⃣ Loop through each FITS file
        for fpath in tqdm(fits_files): 
            # tqdm just gives me a visual progress bar and time remaining as the loop iterates
            try:
                # open header only, no data load (fast)
                # hdu -> header data units
                # a fits file has multiple files called hdu
                # each hdu has header and its data
                # hdul -> header data units list
                with fits.open(fpath, memmap=True) as hdul:
                    # memmap = memory mapping
                    # used for large file handling, this way not the entire file is loaded onto the memory while opening and using of file
                    # only requested data of that file is pulled onto the RAM (memory management)
                    hdr = hdul[1].header  # CLASS spectrum is in extension 1

                    # 5️⃣ Extract key info
                    row = {
                        "filename": fpath.name,
                        "filepath": str(fpath),
                        "start_time": hdr.get("STARTIME"),
                        "end_time": hdr.get("ENDTIME"),
                        "mid_time": hdr.get("MID_UTC"),
                        "exposure_s": hdr.get("EXPOSURE"),
                        "temp_c": hdr.get("TEMP"),
                        "gain_ev_ch": hdr.get("GAIN"),
                        "sat_alt" : hdr.get("SAT_ALT"),
                        "sat_lat": hdr.get("SAT_LAT"),
                        "sat_lon": hdr.get("SAT_LON"),
                        "bore_lat": hdr.get("BORE_LAT"),
                        "bore_lon": hdr.get("BORE_LON"),
                        "solarang_deg": hdr.get("SOLARANG"),
                        "phaseang_deg": hdr.get("PHASEANG"),
                        "program": hdr.get("PROGRAM"),
                        "version": hdr.get("SW_VERSN"),
                        "dataset": hdr.get("DATASET"),
                        "scd_fltr": hdr.get("SCD_FLTR"),
                        "scd_used": hdr.get("SCD_USED"),
                        "v0_lat": hdr.get("V0_LAT"),
                        "v0_lon": hdr.get("V0_LON"),
                        "v1_lat": hdr.get("V1_LAT"),
                        "v1_lon": hdr.get("V1_LON"),
                        "v2_lat": hdr.get("V2_LAT"),
                        "v2_lon": hdr.get("V2_LON"),
                        "v3_lat": hdr.get("V3_LAT"),
                        "v3_lon": hdr.get("V3_LON"),
                        "notes": str("")
                    }

                    rows.append(row)

            except Exception as e:
                print(f"⚠️ Error reading {fpath.name}: {e}")
                rows.append({"filename": fpath.name, "filepath": str(fpath.absolute()), "notes": str(e)})


        # 6️⃣ Create DataFrame
        df = pd.DataFrame(rows)

        # 7️⃣ Save to CSV
        # convert dataframe to csv to write in csv
        output_path = Path(f"/home/saurabh/moon_project/metadata/metadata_CLASS/AUG_25/metadata_CLASS_{data_root.name}.csv")
        # access name of each path folder data_root.name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

        print(f"✅ Saved metadata for {len(df)} files to {output_path}")
    except Exception as e:
        tqdm.write(f"\nFATAL ERROR processing folder {data_root.name}: {e}")


"""output_path = Path(...): Defines the exact location and name of the output file.

output_path.parent.mkdir(...): This line ensures the destination directory (/project_root/outputs/metadata/) exists.

    parents=True: Creates any necessary parent directories.

    exist_ok=True: Prevents an error if the directory already exists.

df.to_csv(output_path, index=False): This is the final action. It writes the organized DataFrame (df) from your computer's memory to a permanent CSV (Comma Separated Values) file on your disk.

    index=False: Prevents Pandas from writing the internal DataFrame row numbers as an unnecessary column in the CSV file."""
