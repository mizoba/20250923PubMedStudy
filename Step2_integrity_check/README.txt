# 	Step 2 — Integrity Verification of Downloaded Datasets

This step ensures that all downloaded PubMed and PMC datasets are complete, consistent, and free of corruption before downstream analysis.

## PubMed Integrity Verification

Located in:
step2_integrity_check/Integrity_Pubmed/

The file Verification_python.py performs a three-stage validation:

1. Search Count Validation

Checks whether the number of downloaded UIDs matches the total count returned by the PubMed search query.
This verifies that all expected records for a given year and category were fully retrieved.

2. Content Matching

Verifies that the number of parsed abstract text files matches the number of UIDs.
This ensures every PMID has a corresponding abstract in the output directory.

3. Error Handling & Recovery

Detects missing or failed downloads and automatically re-attempts retrieval.
This step guarantees dataset completeness even in cases of network errors or partial downloads.

Note:
Each validation step is implemented separately inside the script.
You should open the .py file and run each block independently as instructed in the comments.

The file log.txt contains the verification summary.

### PMC Integrity Verification

Located in:
step2_integrity_check/Integrity_Pubmed_central/

The script Integrity_code.sh performs structural and compression validation of all downloaded PMC OA bulk archives.

Dual-Validation Process

To guarantee the integrity of all .tar.gz archives, we used two standard GNU tools:

1. Compression Integrity Check — gunzip -t

Validates the gzip headers

Performs cyclic redundancy code (CRC) checks

Detects any corrupted compressed blocks before extraction

2. Archive Structure Verification — tar -tzf

Lists archive contents

Confirms the internal file structure

Ensures no broken or incomplete tar members

This process confirmed that all downloaded PMC archives were uncorrupted and structurally valid prior to extraction.

The file validation_error_log.txt stores all warnings, missing archives, and structural inconsistencies detected during verification.