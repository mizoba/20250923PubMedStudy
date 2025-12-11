							 Step 3-3 — Creating Article Category Flags

Located at:
Step3_parsing_only_for_PMC/Step3_3_Create_flags/

In this step, we generate binary flag columns (0/1) for each major article category used in the study.
These flags allow PMC articles to be grouped and analyzed by publication type in Step 4.

Categories created:

all_article

randomized controlled trial (RCT)

clinical trial

meta-analysis

review

clinical useful journals (CUJ)


     						 1. Clinical Useful Journals Flag (CUJ)

Script: create_cuj_flags.py 

Additional input file: journals_cuj.csv

Purpose

To identify PMC articles published in clinically useful journals, based on a curated list provided in journals_cuj.csv.

How it works

Load the main metadata CSV from Step 3-2

Load the CUJ list (MedlineTA names)

Normalize journal names (case-insensitive)

Check whether each article’s journal name appears in the CUJ list

Create a binary flag:

1 = article appears in a clinical useful journal

0 = otherwise

Output

step3_3WithCUJFlag.csv


This file contains the full metadata plus the new column:

clinical_useful_journal   (0/1)




							 2. Flags for RCT, Clinical Trial, Meta-analysis, Review, All Articles

Script: create_every_flags.py 

Input: step3_3WithCUJFlag.csv

Purpose

To translate PubMed PublicationType (retrieved in Step 3-1) into structured 0/1 category flags.

Logic (summary)

PublicationType values are split by " ; "

Matching is case-insensitive

Exact string matches are used to avoid false positives

Hierarchical exclusions are applied:

Clinical Trial excludes RCT

Review excludes Meta-analysis

all_article is always 1 for every row

Flags created
Flag column					Meaning
randomized_controlled_trial			PublicationType includes "Randomized Controlled Trial"
clinical_trial						PublicationType includes "Clinical Trial" (but not RCT)
meta_analysis					PublicationType includes "Meta-Analysis"
review						PublicationType includes "Review" (but not meta-analysis)
all_article						Always 1
clinical_useful_journal				From Step 3-3-1


Output
step3_3WithEveryFlag.csv


This dataset is now fully annotated with all classification flags, and is ready for Step 4 (P-value detection and statistical analysis).

   								 Final Output of Step 3-3

After this step, each PMC article has:

Standardized journal name

Publication year

PublicationType from PubMed

All category flags

Clinical useful journal flag