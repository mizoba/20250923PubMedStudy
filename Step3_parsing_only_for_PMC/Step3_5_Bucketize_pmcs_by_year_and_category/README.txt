Thought for 11s
Step 3-5 — Bucketizing PMC XMLs by Year and Category

Directory:
Step3_parsing_only_for_PMC/Step3_5_Bucketize_pmcs_by_year_and_category/

In this step, we group PMC XML files into tar archives by year and article category, creating one .tar file for each (year, category) pair. This structure is used later for efficient P-value detection and analysis.

			Files

	bucketize_pmcs.py
Python script that:

Reads the metadata CSV (step3_4Refined.csv or an equivalent flag list)

Maps each PMCID to its publication year and category flags

Writes XML files into bucketed tar archives (one tar per year–category pair)

	Bucketize_pmcs.sh
Shell script that runs bucketize_pmcs.py for each PMC source directory
(e.g., oa_comm/xml, oa_noncomm/xml, oa_other/xml).
Before running, you must update all input/output paths in the script to match your environment.

	step3_4Refined.csv

Input metadata file containing, at minimum:

PMCID

publication year

category flags (e.g., all_article, meta_analysis, clinical_trial, randomized_controlled_trial, review, clinical_useful_journal)

	Log.txt
Example log output showing the expected behavior and summary of the run.

Output Structure

After running Bucketize_pmcs.sh, the output directory will contain tar archives organized as:

pmc/
├─ all_article/
│   ├─ 1990.tar
│   ├─ 1991.tar
│   └─ ...
├─ meta_analysis/
│   ├─ 1990.tar
│   └─ ...
├─ clinical_trial/
├─ randomized_controlled_trial/
├─ review/
└─ clinical_useful_journal/


Each .tar file contains the PMC XML files for that category and publication year.
pmc/
├─ all_article/
│   ├─ 1990.tar
│   ├─ 1991.tar
│   └─ ...
├─ meta_analysis/
│   ├─ 1990.tar
│   └─ ...
├─ clinical_trial/
├─ randomized_controlled_trial/
├─ review/
└─ clinical_useful_journal/
