# PubMed Text & P-Value Mining Tools

This repository contains a collection of Python modules designed to interact with PubMed and extract statistical information (specifically P-values) from text. The core logic is organized within the `modules/` directory to allow for easy importing into other scripts.

## Project Structure

```text
.
├── modules/
│   ├── text_to_pval_and_oper.py    # Extracts list of P-values and operators from strings
│   ├── get_all_pmids.py            # Retrieves PubMed IDs using Entrez APIs
│   └── Additional modules not used in the main code, but available for adjustments or debugging
└── README.md
```