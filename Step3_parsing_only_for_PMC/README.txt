					Step 3 — Converting PMC OA Bulk Data into PubMed-Compatible Structure

Directory:
Step3_parsing_only_for_PMC/

The goal of Step 3 is to transform the PMC OA bulk dataset into the same structural format used for PubMed abstracts.
This allows the downstream P-value extraction pipeline (Step 4) to work identically for both PubMed and PMC sources.

				Before Processing (Original PMC OA Bulk Layout)

The raw PMC dataset is distributed in multiple subfolders:

PMC/
└── oa_bulk/
    ├── oa_comm/
    │   ├── txt/
    │   └── xml/
    ├── oa_noncomm/
    │   ├── txt/
    │   └── xml/
    └── oa_other/
        ├── txt/
        └── xml/

PMC provides:

XML full texts

filelist.csv files containing metadata (but no index or category labels)
**Due to lack of repository space, we were not able to upload .csv files included in Step3.**


Thus, Step 3 performs the tasks needed to build a full processing-ready dataset:
metadata extraction → categorization → journal/year parsing → flag creation → bucketization → abstract/body extraction.


				After Processing (PubMed-Compatible Format)

After completing Steps 3-0 through 3-6, the PMC dataset is reorganized into the following structure:

pmc/
├─ all_article/
│   ├─ pmcid_list_all_1990_abstract.txt
│   ├─ pmcxtract_list_all_1990_abstract.txt
│   ├─ pmcid_list_all_1991_abstract.txt
│   ├─ pmcxtract_list_all_1991_abstract.txt
│   ├─ ...
│   ├─ pmcid_list_all_2025_abstract.txt
│   ├─ pmcxtract_list_all_2025_abstract.txt
│   ├─ pmcid_list_all_1990_body.txt
│   ├─ pmcxtract_list_all_1990_body.txt
│   ├─ pmcid_list_all_1991_body.txt
│   ├─ pmcxtract_list_all_1991_body.txt
│   ├─ ...
│   ├─ pmcid_list_all_2025_body.txt
│   └─ pmcxtract_list_all_2025_body.txt
│
├─ meta_analysis/
│   ├─ pmcid_list_meta_1990_abstract.txt
│   ├─ pmcxtract_list_meta_1990_abstract.txt
│   ├─ pmcid_list_meta_1990_body.txt
│   └─ pmcxtract_list_meta_1990_body.txt
│
├─ clinical_trial/
│   └─ (same file structure for years 1990–2025)
│
├─ randomized_controlled_trial/
│   └─ (same structure)
│
├─ review/
│   └─ (same structure)
│
└─ clinical_useful_journal/
    └─ (same structure)


				Meaning of the Output Files

Each category folder contains four types of files per year:

File	Meaning
pmcid_list_{cat}_{year}_abstract.txt	List of PMCIDs that have an abstract
pmcxtract_list_{cat}_{year}_abstract.txt	Extracted abstract text (one line per PMCID)
pmcid_list_{cat}_{year}_body.txt	List of PMCIDs that have full-text body content
pmcxtract_list_{cat}_{year}_body.txt	Extracted full-text content (one line per PMCID)

		Characteristics:

Each line contains exactly one record

Newlines in XML are replaced with tabs so each article occupies one line

Abstracts and bodies are extracted independently

Categories correspond to PubMed PublicationTypes and CUJ labels obtained earlier in Step 3

				Purpose of This Transformation

By the end of Step 3, the PMC dataset:

is categorized (RCT, CT, MA, Review, CUJ, All)

is grouped by publication year

has abstracts and bodies extracted into flat text files

is structured identically to the PubMed abstract folder created in Step 1
