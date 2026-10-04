import pandas as pd

INPUT_CSV = "/Users/choijinhyeok/Documents/ResearchJamaPvalue/20251010/Step2Complete_CSV/step3WithCUJFlag.csv"
OUTPUT_CSV = "/Users/choijinhyeok/Documents/ResearchJamaPvalue/20251010/Step2Complete_CSV/step3WithEveryFlag.csv"

# Load
df = pd.read_csv(INPUT_CSV, dtype=str).fillna("")

# Define exact strings (case-insensitive)
TARGETS = {
    "meta_analysis": ["Meta-Analysis"],
    "clinical_trial": ["Clinical Trial"],
    "randomized_controlled_trial": ["Randomized Controlled Trial"],
    "review": ["Review"],
}

def make_flags(ptype):
    """Return dict of exact matches (1/0) after splitting by ' ; '."""
    types = [x.strip().lower() for x in ptype.split(" ; ") if x.strip()]
    flags = {
        "randomized_controlled_trial": int(any(t in [s.lower() for s in TARGETS["randomized_controlled_trial"]] for t in types)),
        "clinical_trial": int(
            any(t in [s.lower() for s in TARGETS["clinical_trial"]] for t in types) 
            and not 
            any(t in [s.lower() for s in TARGETS["randomized_controlled_trial"]] for t in types)
        ),
        "meta_analysis": int(any(t in [s.lower() for s in TARGETS["meta_analysis"]] for t in types)),
        "review": int(
            any(t in [s.lower() for s in TARGETS["review"]] for t in types) 
            and not 
            any(t in [s.lower() for s in TARGETS["meta_analysis"]] for t in types)
        ),
        "all_article": 1,
    }
    return flags

# Apply function and expand into columns
flag_df = df["PublicationType"].apply(make_flags).apply(pd.Series)

# Merge back
df = pd.concat([df, flag_df], axis=1)
df["clinical_useful_journal"] = df["clinical_useful_journal"].astype(int)

# Save
df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ Saved → {OUTPUT_CSV}")
print(df.head(10)[["PublicationType", "meta_analysis", "clinical_trial", "randomized_controlled_trial", "review", "clinical_useful_journal"]])
