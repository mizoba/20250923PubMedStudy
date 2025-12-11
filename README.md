# 20250923PubMedStudy
Full code for the article. See README for usage and authorship policy

## Usage & Authorship Policy

This repository contains the full code used for the bibliographic analysis described in the article.

If you wish to use, modify, or extend this code for your own research, feel free.  
For any publications or academic work that use this code, **please include me as a co-author**.

Contact: hirosi47111@gmail.com  

## Citation
If you use this code, please cite the associated article (when available) with this repository.

doi: Not published Yet


###				 PubMed & PMC Bibliometric Mining Pipeline

A complete end-to-end workflow for downloading biomedical literature, categorizing articles, extracting P-values, and visualizing statistical reporting trends.

This repository contains the full codebase used to conduct our bibliographic research study on PubMed and PMC.
The goal of this project is to download all biomedical articles (1990–present), divide them by study category, extract statistical information (specifically P-values), and generate summary tables and plots of P-value reporting trends.

The pipeline is implemented in five modular steps (0 → 4), allowing researchers to reproduce the entire workflow or reuse individual components.

				 Workflow Overview
Step 0 — Core Python Modules

Reusable functions for text cleaning, P-value extraction, and PubMed ID handling.

Step 1 — Raw Dataset Download

Shell scripts for downloading PubMed abstracts (by category and year) and PMC OA bulk datasets.

Step 2 — Integrity Checks

Verification scripts ensuring that downloaded PubMed and PMC datasets are complete and consistent.

Step 3 — PMC CSV Data Extraction

Parsing of PMC-provided .csv metadata files to fetch article attributes and indexing information.

Step 4 — P-value Detection & Results Generation

Pattern-matching extraction of P-values, structured output tables, and summary visualizations (Excel + PNG).

					 Repository Structure
.
├── step0_modules/
│   ├── text_to_pval_and_oper.py        # Extracts P-values and operators from text
│   ├── get_all_pmids.py                # Retrieves PubMed IDs
│   └── Other optional helper modules

├── step1_download/
│   ├── download_from_pubmed/           # Scripts to download PubMed abstracts by category/year
│   └──  download_from_PMC_oa_bulk/      # Scripts to download PMC OA bulk (txt/xml)
│   

├── step2_integrity_check/
│   ├──  Integrity_Pubmed      # Ensures all PubMed yearly files exist
│   └──  Integrity_Pubmed_central          # Ensures full OA bulk folder structure is present
│   

├── step3_parsing_only_for_PMC/
│   ├── parse_PMC_metadata.py           # Reads .csv metadata provided by PMC
│   ├── Field extraction scripts         # Journal, license, date, etc.
│   
├── Step4_text_analysis/
│   ├── detect_pvalues.py               # Runs extraction on all downloaded text files
│   ├── generated_results.xlsx          # Tables summarizing extracted data
│   ├── plots/                          # .png plots created from Excel
│   └── Statistical summaries

└── README.md

**Due to lack of repository space, we were not able to upload .csv files included in Step3.**

				 Step 0 — Core Modules

These Python modules provide the analytical foundation.

text_to_pval_and_oper.py

Cleans numeric expressions

Standardizes notation (×, exp, parentheses, etc.)

Matches P-value patterns and operators

Returns structured tuples for downstream analysis

get_all_pmids.py

Queries PubMed via Entrez

Retrieves PMIDs for each study category

Used for generating raw download lists

				 Step 1 — Downloading Raw Datasets
PubMed Abstracts

Located in:
step1_download_raw/download_from_pubmed/

Script categories:

All articles

Clinical trials

Randomized controlled trials

Meta-analysis

Review

Clinically useful journals

Each script creates files like:

pubmed_abstract/
├─ all_article/
│   ├─ pmid_list_all_1990.txt
│   ├─ pmxtract_list_all_1990.txt
│   └── ...

PMC OA Bulk

Located in:
step1_download_raw/download_from_PMC_oa_bulk/

This reproduces the official NCBI FTP structure:

oa_bulk/
├── oa_comm/
│   ├── txt/
│   └── xml/
├── oa_noncomm/
│   ├── txt/
│   └── xml/
└── oa_other/
    ├── txt/
    └── xml/


Warning: This dataset is extremely large (hundreds of GB).

					 Step 2 — Integrity Checks

Scripts ensure correctness of downloaded datasets.

Examples:

Are all years downloaded?

Are all categories complete?

Are PMC txt/xml files consistent with NCBI index?

Are any files missing or corrupted?

These checks prevent downstream errors before P-value extraction.

					Step 3 — Fetching PMC Metadata (.csv)

PMC distributes article metadata tables.
This step parses them to extract:

Article titles

Journal names

Licensing

Publication year

Corresponding PMC/OA folder mapping

Output is a cleaned metadata table aligned with downloaded files.

					 Step 4 — Detecting P-values & Generating Results
Key components:

Pattern-matching extraction based on Step 0 modules

Batch processing of all PubMed/PMC text files

Output generation in .xlsx tables

Plot generation (proportion of articles with P-values, P-value distribution, etc.)

This step produces the final data products used in the study.

Outputs include:

step4_pvalue_detection_and_results/
├── pvalue_summary.xlsx
├── pvalue_distribution.png
├── yearly_proportion_plot.png
└── category_comparison_plot.png

					 Usage & Authorship Policy

You are welcome to use, modify, or extend this code for your research.
If this code contributes to a publication, please contact me and include me as a co-author.

Contact:
					 hirosi47111@gmail.com

This ensures fair academic credit and reproducibility.

						 Citation

If you use this repository, please cite:

Choi Jinhyeok. PubMed & PMC Bibliometric Mining Pipeline. GitHub Repository. 2025.


When the associated paper is published, please update citations accordingly.


			 Future Enhancements

Automated extraction of effect sizes (OR, HR, RR)

More robust text normalization models

Machine-learning–based classification of statistical reporting

Automated linking between PubMed abstracts and PMC full text

Improved visualization scripts

		 Need help?

You can reach me anytime at:
	jake47111@gmail.com

