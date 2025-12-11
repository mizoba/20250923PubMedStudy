# Targets only rows with PMID present and PublicationType empty.

# Requests 100 PMIDs at a time, parses, and fills PublicationType.

# If NCBI returns fewer articles than requested, detects the gap and retries missing PMIDs in mini-batches of 20, then singles.


import os
import time
import math
import pandas as pd
import numpy as np
from xml.etree import ElementTree as ET
from Bio import Entrez
from typing import List

# ===== SETTINGS =====
Entrez.email = ""       # <- keep your contact email
# Entrez.api_key = "YOUR_NCBI_API_KEY"         # <- optional but recommended
Entrez.max_tries = 1
Entrez.sleep_between_tries = 1

INPUT_CSV  = "/Users/choijinhyeok/Documents/ResearchJamaPvalue/20251010/Step2Complete_CSV/concatenated.csv"  # current file
OUTPUT_CSV = "/Users/choijinhyeok/Documents/ResearchJamaPvalue/20251010/Step2Complete_CSV/concatenated.csv"
BATCH_200  = 200
RETRY_20   = 20
SLEEP_BETWEEN_CALLS = 0.35  # be polite to NCBI

# ===== HELPERS =====
def fetch_xml(pmids: List[str], retry=1):
    """Fetch PubMed XML for a list of PMIDs with simple retry/backoff."""
    last = None
    for attempt in range(1, retry+1):
        try:
            with Entrez.efetch(db="pubmed",
                               id=",".join(pmids)) as h:
                root = ET.parse(h).getroot()
            return root
        except Exception as e:
            last = e
            time.sleep(0.35)  # backoff
    raise last

def parse_pubtype(article) -> str:
    pts = [pt.text for pt in article.findall(".//PublicationType") if pt.text]
    return " ; ".join(pts) if pts else ""

def chunk(lst: List[str], n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

# ===== LOAD & TARGET ROWS =====
df = pd.read_csv(INPUT_CSV)

# normalize PMID; treat '', '0', 'nan', 'None' as NaN
df["PMID"] = df["PMID"].astype(str).str.strip()
df["PMID"] = df["PMID"].replace({"": np.nan, "0": np.nan, "nan": np.nan, "None": np.nan})

if "PublicationType" not in df.columns:
    df["PublicationType"] = ""

mask_missing_pt = df["PublicationType"].isna() | (df["PublicationType"].astype(str).str.strip() == "")
mask_valid_pmid = df["PMID"].notna()

target_idx = df.index[mask_missing_pt & mask_valid_pmid].tolist()
print(f"🔎 Rows needing PT with valid PMID: {len(target_idx):,}")

if not target_idx:
    print("Nothing to do. Exiting.")
    # still write a copy for idempotence if you want:
    df.to_csv(OUTPUT_CSV, index=False)
    raise SystemExit

# build (pmid -> index) mapping just for targets
pmid_to_idx = {df.at[i, "PMID"]: i for i in target_idx}
pmids_all   = list(pmid_to_idx.keys())

updated, still_missing_all = 0, []

# ===== PASS 1: batches of 200 =====
for sub in chunk(pmids_all, BATCH_200):
    try:
        root = fetch_xml(sub)
    except Exception as e:
        print(f"❌ Batch of {len(sub)} failed: {e}")
        still_missing_all.extend(sub)
        continue
    
    print("fetched 200")
    
    returned = set()
    for art in root.findall(".//PubmedArticle"):
        pmid = art.findtext(".//PMID")
        if not pmid:
            continue
        returned.add(pmid)
        idx = pmid_to_idx.get(pmid)
        if idx is not None:
            df.at[idx, "PublicationType"] = parse_pubtype(art)
            updated += 1

    # anything requested but not returned goes to retry list
    missing_here = sorted(set(sub) - returned)
    still_missing_all.extend(missing_here)


print(f"✅ First pass updated: {updated:,}, to retry: {len(still_missing_all):,}")

# ===== PASS 2 (retry): mini-batches of 20, then singles as last resort =====
retry_list = [p for p in still_missing_all if pd.isna(df.loc[pmid_to_idx[p], "PublicationType"]) or
              str(df.loc[pmid_to_idx[p], "PublicationType"]).strip() == ""]

second_updated, final_missing = 0, []

for sub in chunk(retry_list, RETRY_20):
    try:
        root = fetch_xml(sub)
    except Exception as e:
        print(f"⚠️ Retry batch of {len(sub)} failed: {e}")
        final_missing.extend(sub)
        continue

    returned = set()
    for art in root.findall(".//PubmedArticle"):
        pmid = art.findtext(".//PMID")
        if not pmid:
            continue
        returned.add(pmid)
        idx = pmid_to_idx.get(pmid)
        if idx is not None:
            df.at[idx, "PublicationType"] = parse_pubtype(art)
            second_updated += 1

    # any still missing after retry batches → try singles next
    not_back = sorted(set(sub) - returned)
    final_missing.extend(not_back)

    time.sleep(SLEEP_BETWEEN_CALLS)

print(f"🔁 Second pass updated: {second_updated:,}, remaining: {len(final_missing):,}")

# ===== OPTIONAL PASS 3: singles (comment out to skip) =====
third_updated, really_missing = 0, []
for pmid in final_missing:
    # skip if already filled by previous steps
    v = str(df.at[pmid_to_idx[pmid], "PublicationType"]).strip()
    if v:
        continue
    try:
        root = fetch_xml([pmid])
        arts = root.findall(".//PubmedArticle")
        if arts:
            df.at[pmid_to_idx[pmid], "PublicationType"] = parse_pubtype(arts[0])
            third_updated += 1
        else:
            really_missing.append(pmid)
    except Exception:
        really_missing.append(pmid)
    time.sleep(SLEEP_BETWEEN_CALLS)

print(f"🧷 Singles updated: {third_updated:,}, unresolved: {len(really_missing):,}")

# ===== SAVE =====
df.to_csv(OUTPUT_CSV, index=False)
print(f"💾 Saved → {OUTPUT_CSV}")

# Optional: write list of unresolved PMIDs for inspection/re-run
unresolved_path = os.path.splitext(OUTPUT_CSV)[0] + "_unresolved_pmids.txt"
with open(unresolved_path, "w", encoding="utf-8") as f:
    for pmid in really_missing:
        f.write(pmid + "\n")
print(f"📝 Unresolved PMIDs list → {unresolved_path}")


                                          
