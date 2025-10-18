import pandas as pd
from pathlib import Path

path = Path("/home/saurabh/moon_project/metadata/metadata_CLASS/AUG_25/")
files = path.rglob("*.csv")

for f in files:
    df = pd.read_csv(f)
    print(f"\n{f}")
    print("Rows:", len(df))
    print("NaN per column:\n", df.isna().sum())

