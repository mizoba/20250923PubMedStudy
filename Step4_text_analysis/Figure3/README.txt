		Step 4 — Figure 3: Comparative Trends in P-value Reporting


Figure 3 presents a comparative analysis of P-value reporting across three major biomedical text sources—PMC full-texts, PMC abstracts, and PubMed abstracts—between 1990 and 2025. This analysis quantifies how often research items contain at least one P-value below conventional significance thresholds. The figure is produced using the scripts listed below:

PMC Abstracts: Figure3pmcAbs.py 

Figure3pmcAbs

PMC Full-texts: Figure3PMCbody.py 

Figure3PMCbody

PubMed Abstracts: Figure3pubmedAbs.py 

Figure3pubmedAbs

All scripts use the unified P-value extraction function (text_to_pval_and_oper) to ensure consistent detection across sources.

			Objectives

Figure 3 examines temporal trends in:

Any P-value reported (≥1 extracted P-value)

Any P-value ≤ 0.05 (traditional statistical significance)

Any P-value ≤ 0.005 (proposed stricter threshold; Amrhein et al., 2017)

These three metrics allow comparison of reporting practices across:

Full-text availability (PMC full-texts)

Abstract-level summaries (PMC abstracts / PubMed abstracts)

Different indexing systems (PubMed vs PMC)

			Data Sources

PMC full-texts: Derived from XML body sections after normalization (Step 3-6)

PMC abstracts: Extracted from <abstract> elements

PubMed abstracts: Downloaded and processed via the PubMed xtract pipeline in Step 1

Each file contains one article per line in the format:

PMCID(or PMID)  {text}


All newline characters in text have been converted to tabs to guarantee one record per line.

			Analytical Method

For each year from 1990–2025, and for each source (PMC full-text, PMC abstract, PubMed abstract), the scripts:

Count the total number of items (total_items).

Extract all P-values using:

pval_and_oper = text_to_pval_and_oper(body_text)


Identify whether an item contains:

≥1 P-value of any kind

≥1 P-value ≤ 0.05

≥1 P-value ≤ 0.005

Output yearly aggregates.

Threshold logic (example from all three scripts):

Any P-value: if len(pval_and_oper) > 0

P ≤ 0.05: first P-value entry satisfying pval <= 0.05

P ≤ 0.005: first P-value entry satisfying pval <= 0.005

This ensures each article is counted at most once per threshold.

				
				How to Reproduce the Figures

Run one of the scripts:

python Figure3pmcAbs.py
python Figure3PMCbody.py
python Figure3pubmedAbs.py


Copy the printed output (yearly values) into the corresponding Excel sheet located in:

Excel_folder/


Use Excel to generate the line charts following the reference formatting shown in Plot3_*.png.