					 Step 3-1 — Fetching Publication Categories (PublicationType)

Located at:
Step3_parsing_only_for_PMC/Step3_1_Fetch_Categories/

In this step, we classify PMC articles into publication categories (e.g., clinical trial, RCT, review, meta-analysis) by retrieving each article’s PublicationType from PubMed.

PMC does not provide publication-category labels inside OA bulk metadata.
Therefore, we must link each PMC article to its PubMed record using the corresponding PMID, then query PubMed for its publication types.


						 Process Overview

The script Fetch_categories.py retrieves publication categories using:

ESearch / EFetch calls to PubMed

PMIDs extracted from the concatenated PMC metadata CSV

XML parsing of <PublicationType> tags

This creates a categorical mapping between PMC full-text articles and PubMed article types, enabling downstream bibliographic classification.


					 How it Works (Script Logic Summary)

The script performs several passes to ensure completeness:

 1. Batch Fetch (200 PMIDs per request)

Sends large EFetch queries to NCBI

Parses returned XML

Extracts and stores all <PublicationType> values

Detects PMIDs that were not returned by NCBI

Queues missing IDs for retry

 2. Retry Fetch (20 PMIDs per request)

Smaller batch size to reduce NCBI failure rates

Attempts to fill missing PublicationType entries

Still identifies non-returned PMIDs for final retry

 3. Single-PMID Fetch (optional final pass)

Fetches each remaining PMID individually

Ensures maximum coverage and classification completeness

 4. Save Results

Writes all PublicationTypes back into the metadata CSV

Outputs a list of unresolved PMIDs for reinspection

For reference, the complete script is in:
Fetch_categories.py 

Fetch_categories


					 Performance Note

Fetch_categories.py may require several days to complete because:

The PMC dataset contains hundreds of thousands to millions of articles

NCBI rate limits EFetch requests

The script intentionally uses polite delays to avoid API throttling


					 Recommendation

We recommend revising the script to support:

Multithreading or

Multiprocessing or

Distributed/parallel execution across multiple machines

This can reduce runtime from days → hours depending on hardware.


						 Output

Output file:

Result.csv — Contains the original PMC metadata plus the newly added "PublicationType" column.

Optional output:

*_unresolved_pmids.txt — PMIDs that failed after all retry attempts.