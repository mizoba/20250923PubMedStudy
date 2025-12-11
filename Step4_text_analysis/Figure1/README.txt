					Step 4 — P-Value Detection and Trend Visualization

Directory:
Step4_text_analysis/

Step 4 performs the final stage of the pipeline.
Using the processed abstract/body text files generated in earlier steps, this stage:

Detects all P-values using the pattern-matching engine in
text_to_pval_and_oper()

Computes yearly proportions of articles containing P-values

Generates publication-type–specific trend plots (Figure 1)

This step uses the standardized output structures from both PubMed and PMC, allowing identical analysis workflows.

					1. P-Value Detection Logic

For every record (each line = 1 article), the scripts perform:

Token cleaning

P-value regex extraction

Operator normalization

Identification of:

Any P-value

P ≤ 0.05

P ≤ 0.01

P ≤ 0.005

P ≤ 0.001

Only the presence of at least one P-value is used for Figure 1.

The extraction engine is the same across all three scripts and uses:

text_to_pval_and_oper(body_text)


which returns a list of detected P-values and their operators.

					2. Input File Structure
PMC Abstracts

Source:
pmcxtract_list_{category}_{year}_abstract.txt

PMC Full Texts

Source:
pmcxtract_list_{category}_{year}_body.txt

PubMed Abstracts

Source:
pmxtract_list_{category}_{year}.txt

Each file contains one article per line, in the format:

PMCID(or PMID)  {text}


All newline characters inside text were normalized to tabs in Step 3.

					3. Figure 1 Scripts
Figure 1A – PMC Abstracts

File: Figure1pmcAbs.py


Figure1pmcAbs

Reads yearly abstract files from PMC and calculates:

Total abstracts per year

Number containing ≥1 P-value

Proportion with P-values

Across the following categories:

randomized-controlled-trial

clinical-trial

meta-analysis

review

clinical-useful-journal

all-articles

Output:
Proportion of PMC Abstracts With P-Values (%)

Figure 1B – PMC Full Texts

File: Figure1PMCbody.py


Figure1PMCbody

Same logic as Figure 1A, but using full-text body files instead of abstracts.

Output:
Proportion of PMC Full-texts With P-Values (%)

Figure 1C – PubMed Abstracts

File: Figure1pubmedAbs.py


Figure1pubmedAbs

Extracts yearly trends for PubMed abstracts.

Categories:

rct

ct

meta

review

cuj

all

Output:
Proportion of PubMed Abstracts With P-Values (%)




					4. Output Figures

The scripts produce three line charts corresponding to:

PMC Abstracts (1990–2025)

PMC Full Texts (1990–2025)

PubMed Abstracts (1990–2025)

Each figure displays the year-by-year trend in the prevalence of P-value reporting for all six categories.

					5. Interpretation

Together, these three plots allow direct comparison of:

Abstract vs full-text reporting

PMC (full text) vs PubMed (abstract-only indexing)

Trends across article types (RCT, CT, MA, Review, CUJ, All)