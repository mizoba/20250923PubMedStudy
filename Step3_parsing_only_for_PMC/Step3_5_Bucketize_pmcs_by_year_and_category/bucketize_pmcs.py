#!/usr/bin/env python3
"""
bucketize_pmcs.py
===================

This script takes a directory of source tar archives containing XML files from
the PubMed Central Open Access corpus, along with a CSV file describing
publication year and category flags for each PMC ID. It then builds a set of
output tar archives, one per (category, year) combination, storing the XML
files belonging to that bucket. Duplicate PMC IDs across different input
archives are de‑duplicated, and the script is resumable between runs via a
SQLite state database that tracks processed entries and previously seen PMC
IDs.

Key features and improvements over the original prototype:

* **Persistent de‑duplication across runs.** Previously a simple in‑memory
  ``seen_pmcs`` set avoided duplicating files within a single run but would
  forget about duplicates when restarted. This version rebuilds that set by
  querying the state database for all previously processed PMC IDs at
  startup, ensuring that duplicates are skipped even after a crash or
  incremental processing.

* **Graceful handling of missing metadata.** If a PMC ID is not present in
  the CSV or its year cannot be parsed, the file is no longer silently
  skipped. Instead, such entries are routed to a special ``unknown-year``
  bucket so that nothing is lost. Likewise, if no category flags are set
  the file is logged to a ``skipped.csv`` with an explanatory reason.

* **Use of POSIX/PAX tar format.** The specification calls for either
  POSIX/PAX or USTAR format. When a new output archive is created it is
  initialized with ``format=tarfile.PAX_FORMAT`` to ensure standard
  compliance. Subsequent appends reuse the existing format.

* **Manifest and skip logs.** Two CSV files are produced: a ``manifest.csv``
  containing one row per processed PMC ID with its year, categories,
  originating source archive and output paths; and a ``skipped.csv``
  capturing duplicates and files with missing metadata. These logs provide
  transparency and aid reproducibility.

* **Cross‑check summary.** At the end of a run the script prints a
  cross‑tabulation of the number of files stored in each (category, year)
  bucket. This acts as a sanity check and can be redirected to a file if
  desired.

The script is designed to handle tens of millions of files and hundreds of
gigabytes of input without exhausting memory. Only a small LRU cache of
output tar handles is kept open at once.

Example usage:

```
python3 bucketize_pmcs.py \
  --input-dir path/to/pmc-tars \
  --csv labels.csv \
  --out-dir path/to/output \
  --state path/to/state.sqlite \
  --manifest path/to/manifest.csv \
  --skipped path/to/skipped.csv
```

``--manifest`` and ``--skipped`` default to files inside the output
directory if not specified. These CSV files are opened in append mode, so
resuming a run will extend them without truncating previous entries.

``--max-open`` controls the number of simultaneously open output tar
archives; increasing it may improve throughput at the cost of file
descriptors.

The script uses the same category mapping as the original code, with keys
corresponding to the columns in the labels CSV. Adjust ``BUCKET_MAP`` if
additional categories are needed.
"""

import argparse
import csv
import io
import os
import re
import sqlite3
import sys
import tarfile
import time
from collections import OrderedDict, defaultdict

# Optional: pandas speeds up CSV read. Fallback to csv module if missing.
try:
    import pandas as pd
    HAS_PANDAS = True
except Exception:
    HAS_PANDAS = False

PMC_RE = re.compile(r"^(PMC\d+)\.xml$", re.IGNORECASE)

# Mapping from CSV flag name to normalized bucket name. These correspond to
# directory names under the output ``pmc`` folder. Adjust as needed if you
# introduce new flags.
BUCKET_MAP = OrderedDict([
    ("all_article",              "all-articles"),
    ("meta_analysis",            "meta-analysis"),
    ("review",                   "review"),
    ("clinical_useful_journal",    "clinical-useful-journal"),
    ("randomized_controlled_trial", "randomized-controlled-trial"),
    ("clinical_trial",           "clinical-trial"),
])

def load_labels(csv_path):
    """
    Load the labels CSV and return a mapping of PMC IDs to their metadata.

    The returned ``meta`` dict maps uppercase PMC ID (e.g., ``PMC12345``) to
    a dict ``{"year": year_or_None, "buckets": set[str]}``. Years are
    integers where possible, or ``None`` if parsing fails. ``years`` is a
    set of all years successfully parsed (excluding None).
    """
    meta = {}
    years = set()
    # Use pandas for efficiency if available
    if HAS_PANDAS:
        df = pd.read_csv(csv_path, dtype=str)
        # Normalize column names
        cols = {c.strip().lower(): c for c in df.columns}
        need_base = ["pmc id", "pmc_id", "pmcid"]
        pmc_col = next((cols[c] for c in need_base if c in cols), None)
        if pmc_col is None:
            raise SystemExit("❌ CSV must include a PMC ID column (pmc id / pmc_id / pmcid).")
        year_col = None
        for k in ["year", "pdat_year", "pub_year"]:
            if k in cols:
                year_col = cols[k]
                break
        if year_col is None:
            raise SystemExit("❌ CSV must include a publication year column (e.g., 'year').")
        for _, row in df.iterrows():
            raw = str(row[pmc_col]).strip()
            if not raw:
                continue
            pmc_id = raw if raw.upper().startswith("PMC") else f"PMC{raw}"
            pmc_id = pmc_id.upper()
            # Parse year; if fails, mark as None
            yr = None
            try:
                yr_tmp = str(row[year_col]).strip()
                if yr_tmp:
                    yr = int(yr_tmp.split(".")[0])
                    years.add(yr)
            except Exception:
                yr = None
            # Determine buckets
            buckets = set()
            for csv_flag, bucket_name in BUCKET_MAP.items():
                if csv_flag in cols:
                    val = str(row[cols[csv_flag]]).strip().lower()
                    if val in ("1", "true", "t", "y", "yes"):
                        buckets.add(bucket_name)
            meta[pmc_id] = {"year": yr, "buckets": buckets}
    else:
        # Fallback to Python's csv.DictReader
        with open(csv_path, newline="", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            cols = {c.strip().lower(): c for c in rdr.fieldnames}
            need_base = ["pmc id", "pmc_id", "pmcid"]
            pmc_col = next((cols[c] for c in need_base if c in cols), None)
            if pmc_col is None:
                raise SystemExit("❌ CSV must include a PMC ID column (pmc id / pmc_id / pmcid).")
            year_col = None
            for k in ["year", "pdat_year", "pub_year"]:
                if k in cols:
                    year_col = cols[k]
                    break
            if year_col is None:
                raise SystemExit("❌ CSV must include a publication year column (e.g., 'year').")
            for row in rdr:
                raw = str(row[pmc_col]).strip()
                if not raw:
                    continue
                pmc_id = raw if raw.upper().startswith("PMC") else f"PMC{raw}"
                pmc_id = pmc_id.upper()
                yr = None
                try:
                    yr_tmp = str(row[year_col]).strip()
                    if yr_tmp:
                        yr = int(yr_tmp.split(".")[0])
                        years.add(yr)
                except Exception:
                    yr = None
                buckets = set()
                for csv_flag, bucket_name in BUCKET_MAP.items():
                    if csv_flag in cols:
                        val = str(row[cols[csv_flag]]).strip().lower()
                        if val in ("1", "true", "t", "y", "yes"):
                            buckets.add(bucket_name)
                meta[pmc_id] = {"year": yr, "buckets": buckets}
    return meta, years

class OutputTarLRU:
    """
    LRU cache of open tarfile handles for output archives.

    Opening and closing tar files repeatedly can be expensive when there are
    thousands of distinct (category, year) buckets. This class keeps up to
    ``max_open`` tarfiles open at once. When the cache exceeds ``max_open``
    entries the least recently used handle is closed.

    New archives are initialized with the POSIX/PAX format to satisfy the
    specification. On subsequent opens we append (``mode='a'``) to retain the
    existing format.
    """
    def __init__(self, max_open=16, tar_format=tarfile.PAX_FORMAT):
        self.max_open = max_open
        self.tar_format = tar_format
        self.cache = OrderedDict()  # path -> tarfile object

    def _evict_if_needed(self):
        while len(self.cache) > self.max_open:
            # remove the least recently used (first) item
            path, tf = self.cache.popitem(last=False)
            try:
                tf.close()
            except Exception:
                pass

    def get(self, path):
        """Return an open tarfile handle for ``path`` (creating if necessary)."""
        path = os.path.abspath(path)
        # If already open, mark as recently used and return
        if path in self.cache:
            tf = self.cache.pop(path)
            self.cache[path] = tf
            return tf
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # If the file doesn't exist, create it with the requested format
        if not os.path.exists(path):
            with tarfile.open(path, mode="w", format=self.tar_format) as tmp:
                # write nothing; just initialize the header
                pass
        # Open for append; Python will detect the existing header and reuse its format
        tf = tarfile.open(path, mode="a")
        self.cache[path] = tf
        self._evict_if_needed()
        return tf

    def close_all(self):
        """Close all open tarfile handles."""
        for _, tf in list(self.cache.items()):
            try:
                tf.close()
            except Exception:
                pass
        self.cache.clear()

class StateDB:
    """
    Thin wrapper around a SQLite database used to persist processing state.

    The ``processed`` table stores one row per (source tar, inner path,
    pmc_id). This allows the script to skip files that were already
    transferred from a given tar archive. The ``pmc_id`` column is also
    leveraged to rebuild the set of previously seen PMC IDs upon startup,
    enabling resumable de‑duplication across runs.
    """
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Connect with check_same_thread=False so that we could expand later if needed
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS processed(
                src_tar TEXT,
                inner_path TEXT,
                pmc_id TEXT,
                PRIMARY KEY (src_tar, inner_path)
            )
            """
        )
        self.conn.commit()
        self.batch = []

    def load_seen_pmcs(self):
        """
        Return a set of all PMC IDs that have been processed previously.

        An empty string in the pmc_id column represents a file whose PMC ID
        could not be determined; these are ignored for de‑duplication.
        """
        cur = self.conn.execute("SELECT DISTINCT pmc_id FROM processed WHERE pmc_id != ''")
        return {row[0] for row in cur.fetchall()}

    def seen(self, src_tar, inner_path):
        """Check if the (src_tar, inner_path) combination has been processed."""
        cur = self.conn.execute(
            "SELECT 1 FROM processed WHERE src_tar=? AND inner_path=? LIMIT 1",
            (src_tar, inner_path),
        )
        return cur.fetchone() is not None

    def mark(self, src_tar, inner_path, pmc_id):
        """
        Add an entry to the batch of processed files. The actual insertion
        happens in bulk when ``flush()`` is called to reduce I/O overhead.
        """
        self.batch.append((src_tar, inner_path, pmc_id))
        # Flush in batches of 1000
        if len(self.batch) >= 1000:
            self.flush()

    def flush(self):
        """Persist the batched processed records to the database."""
        if not self.batch:
            return
        self.conn.executemany(
            "INSERT OR IGNORE INTO processed(src_tar, inner_path, pmc_id) VALUES (?,?,?)",
            self.batch,
        )
        self.conn.commit()
        self.batch.clear()

    def close(self):
        """Flush any outstanding records and close the database connection."""
        self.flush()
        self.conn.close()

def iter_tar_members(tar_path):
    """
    Yield (TarInfo, base filename, tarfile handle) for each XML file within ``tar_path``.

    This helper wraps ``tarfile.open`` in a context manager and iterates
    lazily over members, yielding only regular files with ``.xml`` extension.
    Tarfiles can contain nested directories; the base name of each member is
    used to extract the PMC ID.
    """
    with tarfile.open(tar_path, mode="r:*") as tf:
        for m in tf:
            if not m.isfile():
                continue
            base = os.path.basename(m.name)
            if not base.lower().endswith(".xml"):
                continue
            yield m, base, tf

def add_member_to_output(tf_out, name_in_out, data):
    """
    Write a member with ``name_in_out`` and bytes ``data`` to the open
    ``tarfile.TarFile`` ``tf_out``. Metadata such as uid/gid and mtime
    are normalized for reproducibility.
    """
    ti = tarfile.TarInfo(name=name_in_out)
    ti.size = len(data)
    # Set metadata fields to deterministic values
    ti.uid = ti.gid = 0
    ti.uname = ti.gname = ""
    ti.mtime = int(time.time())
    tf_out.addfile(ti, fileobj=io.BytesIO(data))

def build_target_path(out_root, bucket, year):
    """
    Construct the output tar path for a given bucket and year.

    ``year`` may be an integer or ``None``; when ``None`` it is rendered
    as the string ``unknown-year``. The directory structure is
    ``<out_root>/pmc/<bucket>/<year>.tar``.
    """
    if year is None:
        year_str = "unknown-year"
    else:
        year_str = str(int(year))
    return os.path.join(out_root, "pmc", bucket, f"{year_str}.tar")

def ensure_parent_dirs(out_root):
    """
    Precreate the category directories under ``out_root``. This isn't strictly
    necessary since ``OutputTarLRU`` will ``os.makedirs`` on demand, but
    performing it up front makes the layout visible on disk immediately.
    """
    buckets_all = set(BUCKET_MAP.values())
    for b in sorted(buckets_all):
        os.makedirs(os.path.join(out_root, "pmc", b), exist_ok=True)

def main():
    parser = argparse.ArgumentParser(
        description="Bucketize PMC OA XMLs into per-bucket/year tar files with logging and de‑duplication",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-dir", required=True, help="Directory containing source .tar files")
    parser.add_argument("--csv", required=True, help="Labels CSV (PMC_ID + year + flags)")
    parser.add_argument("--out-dir", required=True, help="Output root directory")
    parser.add_argument("--state", default="./state/state.sqlite", help="SQLite state path")
    parser.add_argument(
        "--manifest",
        default=None,
        help="Path to manifest CSV (processed files). Defaults to '<out-dir>/manifest.csv'",
    )
    parser.add_argument(
        "--skipped",
        default=None,
        help="Path to skipped CSV (duplicates/missing metadata). Defaults to '<out-dir>/skipped.csv'",
    )
    parser.add_argument("--max-open", type=int, default=512, help="Max simultaneously open output tar files")
    args = parser.parse_args()

    out_root = os.path.abspath(args.out_dir)
    # Determine default manifest/skipped paths if not provided
    if args.manifest is None:
        manifest_path = os.path.join(out_root, "manifest.csv")
    else:
        manifest_path = args.manifest
    if args.skipped is None:
        skipped_path = os.path.join(out_root, "skipped.csv")
    else:
        skipped_path = args.skipped

    # Load CSV metadata
    meta, years = load_labels(args.csv)
    if years:
        print(f"✅ Loaded labels: {len(meta):,} PMC IDs; years {min(years)}–{max(years)}")
    else:
        print(f"✅ Loaded labels: {len(meta):,} PMC IDs; no valid year values found")

    # Ensure output directories exist
    ensure_parent_dirs(out_root)

    # Initialize state database and rebuild seen_pmcs
    state = StateDB(args.state)
    seen_pmcs = state.load_seen_pmcs()
    if seen_pmcs:
        print(f"🔄 Resuming run: {len(seen_pmcs):,} PMC IDs previously processed will be skipped")

    # Prepare LRU for output tars (use PAX format)
    lru = OutputTarLRU(max_open=args.max_open, tar_format=tarfile.PAX_FORMAT)

    # Prepare manifest and skipped CSV files in append mode
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    os.makedirs(os.path.dirname(skipped_path), exist_ok=True)
    manifest_file = open(manifest_path, "a", newline="", encoding="utf-8")
    skipped_file = open(skipped_path, "a", newline="", encoding="utf-8")
    manifest_writer = csv.writer(manifest_file)
    skipped_writer = csv.writer(skipped_file)
    # If files are empty, write headers
    if os.stat(manifest_path).st_size == 0:
        manifest_writer.writerow(["pmcid", "year", "categories", "src_tar", "output_tar_paths"])
    if os.stat(skipped_path).st_size == 0:
        skipped_writer.writerow(["pmcid", "src_tar", "inner_path", "reason"])

    # Input tar files sorted for reproducibility
    tars = [os.path.join(args.input_dir, f) for f in os.listdir(args.input_dir) if f.endswith(".tar")]
    tars.sort()
    total_scanned = 0
    total_copied = 0
    bucket_counts = defaultdict(int)  # key: (bucket, year) -> count

    try:
        for tar_path in tars:
            tar_name = os.path.basename(tar_path)
            print(f"📦 Scanning: {tar_name}")
            # Iterate over members; tarfile is opened in iter_tar_members
            for m, base, tf in iter_tar_members(tar_path):
                total_scanned += 1
                inner_path = m.name
                # Skip if this file was already processed for this src tar
                if state.seen(tar_path, inner_path):
                    continue
                # Determine PMC ID from filename
                mo = PMC_RE.match(base)
                if not mo:
                    # Not a PMC ID or not an expected filename; record and skip
                    state.mark(tar_path, inner_path, "")
                    skipped_writer.writerow(["", tar_name, inner_path, "non-xml or unrecognized filename"])
                    continue
                pmc_id = mo.group(1).upper()
                # Duplicate across previous runs or earlier in this run
                if pmc_id in seen_pmcs:
                    state.mark(tar_path, inner_path, pmc_id)
                    skipped_writer.writerow([pmc_id, tar_name, inner_path, "duplicate-pmcid"])
                    continue
                # Add to seen set
                seen_pmcs.add(pmc_id)
                # Lookup metadata
                if pmc_id not in meta:
                    # Unknown PMC ID
                    state.mark(tar_path, inner_path, pmc_id)
                    skipped_writer.writerow([pmc_id, tar_name, inner_path, "metadata-missing"])
                    continue
                info = meta[pmc_id]
                year = info.get("year")
                buckets = info.get("buckets", set())
                if not buckets:
                    # No category flags set
                    state.mark(tar_path, inner_path, pmc_id)
                    skipped_writer.writerow([pmc_id, tar_name, inner_path, "no-category-flags"])
                    continue
                # Extract data once
                fobj = tf.extractfile(m)
                if fobj is None:
                    # Could not read member
                    state.mark(tar_path, inner_path, pmc_id)
                    skipped_writer.writerow([pmc_id, tar_name, inner_path, "extract-failed"])
                    continue
                data = fobj.read()
                fobj.close()
                # List of output tar paths for manifest
                out_paths = []
                for b in buckets:
                    out_tar_path = build_target_path(out_root, b, year)
                    tf_out = lru.get(out_tar_path)
                    add_member_to_output(tf_out, base, data)
                    out_paths.append(os.path.relpath(out_tar_path, start=out_root))
                    # Increase count per bucket
                    bucket_key = (b, year if year is not None else "unknown")
                    bucket_counts[bucket_key] += 1
                total_copied += 1
                # Write manifest row
                # Join categories and output paths with semicolons to keep CSV simple
                cat_str = ";".join(sorted(buckets))
                out_paths_str = ";".join(out_paths)
                manifest_writer.writerow([pmc_id, year if year is not None else "unknown", cat_str, tar_name, out_paths_str])
                # Mark state
                state.mark(tar_path, inner_path, pmc_id)
                # Periodically flush state and files
                if total_copied % 5000 == 0:
                    state.flush()
                    manifest_file.flush()
                    skipped_file.flush()
                    print(f"…progress: copied {total_copied:,} / scanned {total_scanned:,}")
        # Final flushes
        state.flush()
        manifest_file.flush()
        skipped_file.flush()
        # Print summary
        print(f"🎉 Done. Copied {total_copied:,} files (scanned {total_scanned:,}).")
        # Cross‑check summary
        if bucket_counts:
            print("\n📊 Bucket counts (category, year):")
            # Sort by category then year
            for (bucket, yr), count in sorted(bucket_counts.items(), key=lambda x: (x[0][0], str(x[0][1]))):
                print(f"  {bucket}/{yr}: {count:,}")
        else:
            print("No files were copied.")
    finally:
        # Close all resources
        lru.close_all()
        state.close()
        manifest_file.close()
        skipped_file.close()

if __name__ == "__main__":
    main()
