            Step 3-4 — Refining the PMC Metadata Table

Directory:
Step3_parsing_only_for_PMC/Step3_4_Refine/

After assigning journal/year information and category flags in previous steps, this step refines the dataset by removing unnecessary columns and preparing a clean table for Step 4 (P-value detection).

The purpose is to reduce file size, remove unused metadata, and retain only the columns required for analysis.

               Script: Refine.py 

	Purpose

To clean the consolidated metadata by:

Dropping unused columns

Renaming AccessionID → pmcid

Producing a compact dataset ready for P-value processing

	Columns removed

The following columns are dropped:

journal

PMID

PublicationType

These are no longer needed after category flags and metadata extraction.

	Column renamed

AccessionID → pmcid

This provides a standardized identifier used throughout Step 4.

			Output

The resulting cleaned file is:

step4Refined.csv


This file contains:

pmcid

publication year

category flags (RCT, clinical trial, meta-analysis, review, CUJ, all_article)

additional metadata required for Step 4