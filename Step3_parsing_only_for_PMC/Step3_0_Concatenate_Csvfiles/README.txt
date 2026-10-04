			 Step 3 — Parsing PMC Metadata (Concatenating filelist.csv)

In this step, we consolidate all filelist.csv metadata files provided within the PMC OA bulk dataset.
Because PMC does not provide a global index, the only source of metadata for each article is the individual filelist.csv files located inside each /xml folder of the OA bulk directories.

To manage all PMC articles as a single dataset, we must concatenate these distributed CSV files into one unified metadata table.

					 Why is this step necessary?

PMC provides no global master index for OA articles.

Each batch directory (e.g., oa_comm/xml/, oa_noncomm/xml/, oa_other/xml/) contains its own filelist.csv.

These files collectively describe every PMC OA article, including:

PMCID

associated filenames

licensing

article-level metadata

Therefore, we must merge them into a single .csv to manage PMC articles efficiently.

				 Files and Folder Structure

Your local structure (example):

Step3_parsing_only_for_PMC/
└── Step3_0_Concatenate_Csvfiles/
    ├── Csv_concatenate.py