In this process, we will download raw datasets.

These are shell codes to download Pubmed Abstracts, and PMC oa_bulk files

PUBMED:

"download_from_pubmed" folder includes codes for each category ( all, Clinical Trial, Randomized controlled trial, meta-analysis, review, clinical useful journals )

As A result, we will get file structure like below
pubmed_abstract/
├─ all_article/
│   ├─ pmid_list_all_1990.txt
│   ├─ pmxtract_list_all_1990.txt
│   ├─ pmid_list_all_1991.txt
│   ├─ pmxtract_list_all_1991.txt
│   └─ ...
├─ meta_analysis/
│   ├─ pmid_list_meta_1990.txt
│   └─ ...
├─ clinical_trial/
├─ randomized_controlled_trial/
├─ review/
└─ clinical_useful_journal/

PMC:

"download_from_PMC_oa_bulk" folder includes codes for downloading PMC oa_bulk, and shows full log

As a result, we will get exact same file structure with oa_bulk

https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_bulk/

|_ oa_bulk/
|___ oa_comm/
|_____ txt/
|_____ xml/
|___ oa_noncomm/
|_____ txt/
|_____ xml/
|___ oa_other/
|_____ txt/
|_____ xml/
