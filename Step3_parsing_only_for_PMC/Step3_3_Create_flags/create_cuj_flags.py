
# Prepare previous .csv file and journals_cuj.csv , which has rows of clinical useful journals.

import pandas as pd

# Paths
MAIN_CSV = "/Users/choijinhyeok/Documents/ResearchJamaPvalue/20251010/Step2Complete_CSV/step2ErasedCitLastupLicenseRetracted.csv"
JOURNALS_CSV = "/Users/choijinhyeok/Documents/ResearchJamaPvalue/20251010/Step2Complete_CSV/journals_cuj.csv"
OUTPUT_CSV = "/Users/choijinhyeok/Documents/ResearchJamaPvalue/20251010/Step2Complete_CSV/step3WithCUJFlag.csv"

# Load data
df = pd.read_csv(MAIN_CSV, dtype=str)
core_journals = pd.read_csv(JOURNALS_CSV, dtype=str)

# Prepare set of valid journal names (case-insensitive)
core_set = set(core_journals["MedlineTA"].dropna().str.strip().str.lower())

# Add flag column
df["clinical_useful_journal"] = df["journal"].astype(str).str.strip().str.lower().isin(core_set)

df["clinical_useful_journal"] = (
    df["clinical_useful_journal"]
    .astype(str)            # ensure consistent type
    .str.strip()            # remove spaces
    .str.lower()            # normalize case
    .map({"true": True, "false": False})  # convert to bools
    .astype(int)            # finally to 0/1
)
# Save output
df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ Saved to {OUTPUT_CSV} — added 'clinical_useful_journal' flag.")
print(f"🩺 Total core journals matched: {df['clinical_useful_journal'].sum()} / {len(df)}")


# you will get the result 🩺 Total core journals matched: 178960 / 7236185