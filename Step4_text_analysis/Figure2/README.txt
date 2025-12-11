					Step 4 — Figure 2: Distribution of Extracted P-values

Directory:
Step4_text_analysis/Figure2/

This folder contains the scripts used to compute P-value distributions and produce the histograms shown in Figure 2 of the study.

Each category (RCT, clinical trial, meta-analysis, review, CUJ, all articles) has a corresponding histogram.

					Files
Fig2_pmc_abs_to_pval.py     # PMC abstracts
Fig2_pmc_body_to_pval.py    # PMC full texts
Fig2_pubmed_abs_to_pval.py  # PubMed abstracts
Excel_folder/               # tables for plotting
Plot_*.png                  # example output figures

					Purpose

These scripts compute:

Counts of extracted P-values for each bin (0.001, 0.002, …, 0.05+)

Operator type frequencies (<, =, >, other)

Total number of articles and total number of P-values per category

Output values appear directly in the terminal when running the scripts.

The histograms in this step correspond to:

PMC Abstracts

PMC Full-texts

PubMed Abstracts
across predefined article categories.

					How to Use

Run the script

python Fig2_pmc_abs_to_pval.py


or

python Fig2_pmc_body_to_pval.py


or

python Fig2_pubmed_abs_to_pval.py


Copy the printed bin statistics
Paste them into the appropriate Excel file inside Excel_folder/.

Generate the histogram
Insert a column chart in Excel.
Match formatting with the example Plot_*.png files.