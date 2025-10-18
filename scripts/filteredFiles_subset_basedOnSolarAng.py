import pandas as pd
from pathlib import Path

filtered = Path("/home/saurabh/moon_project/metadata/filtered/match_CLASS_XSM_20250801_filtered.csv")
df = pd.read_csv(filtered)
df.columns = [c.strip().lower() for c in df.columns]

out_dir = Path("/home/saurabh/moon_project/metadata/filtered_subsets/")
out_dir.mkdir(parents=True, exist_ok=True)

mask_prime      = df["solarang_deg"].astype(float) <= 60.0
mask_secondary  = (df["solarang_deg"] > 60.0) & (df["solarang_deg"] <= 75.0)
mask_marginal   = (df["solarang_deg"] > 75.0) & (df["solarang_deg"] <= 90.0)
mask_scatter    = (df["solarang_deg"] > 90.0) & (df["solarang_deg"] <= 120.0)

df[mask_prime].to_csv(out_dir / "match_CLASS_XSM_20250801_prime.csv", index=False)
df[mask_secondary].to_csv(out_dir / "match_CLASS_XSM_20250801_secondary.csv", index=False)
df[mask_marginal].to_csv(out_dir / "match_CLASS_XSM_20250801_marginal.csv", index=False)
df[mask_scatter].to_csv(out_dir / "match_CLASS_XSM_20250801_scatter.csv", index=False)
