Step 3-6 — Parsing Abstract and Full Text from PMC XML

Directory:
Step3_parsing_only_for_PMC/Step3_6_Parse_abstract_and_full_text/

This step converts each PMC bucket (a .tar file created in Step 3-5) into four text files containing extracted abstracts and full texts.

Processing is performed using:

xml_to_txt.py (Python) — parses XML and extracts <abstract> and <body> text

ShellCommand.sh — wrapper to run the Python parser with multiprocessing





		Output Files (Per Year × Category)

For each (category, year) pair, four text files are created:

pmcid_list_{category}_{year}_abstract.txt
pmcxtract_list_{category}_{year}_abstract.txt
pmcid_list_{category}_{year}_body.txt
pmcxtract_list_{category}_{year}_body.txt


For example:

pmc/
├─ all_article/
│   ├─ pmcid_list_all_1990_abstract.txt
│   ├─ pmcxtract_list_all_1990_abstract.txt
│   ├─ pmcid_list_all_1990_body.txt
│   ├─ pmcxtract_list_all_1990_body.txt
│   ├─ ...


Each category folder (all_article, meta_analysis, clinical_trial, randomized_controlled_trial, review, clinical_useful_journal) contains the corresponding yearly text outputs.





Algorithm Overview
		1. Reading XML from TAR

XML files are read directly inside the tar archive without extraction.
This is handled by xml_to_txt.py.

		2. Extracting Abstract

An abstract is detected via XPath:

//abstract | //Abstract | //ABSTRACT


If found:

The PMCID (filename stem) is added to pmcid_list_{category}_{year}_abstract.txt

Abstract text is normalized:

\n → \t

repeated whitespace collapsed

One line per article is written to:

pmcxtract_list_{category}_{year}_abstract.txt


in the format:

{PMCID} {abstract_text}


If no <abstract> is present, nothing is written.

		3. Extracting Full Text (Body)

A body is detected using:

//body | //Body | //BODY


If <body> is missing, the script may also fall back to <sec> depending on XML structure.

If found:

PMCID appended to:
pmcid_list_{category}_{year}_body.txt

Text normalized identically to abstract

One line output to:
pmcxtract_list_{category}_{year}_body.txt

Note:
Abstract text is not included inside the body extraction because <abstract> and <body> appear at the same hierarchical level.





		Execution
Shell wrapper (multiprocessing)

ShellCommand.sh runs the parser in parallel:


ShellCommand
"""
ulimit -n 10240
python3 xml_to_txt.py --workers 11 <input_pmc_folder> <output_folder>

		Python XML parser
"""
Core parsing logic:

"xml_to_txt.py"

It:

Finds all (category, year) tar jobs

Parses each XML with lxml

Extracts abstract/body text

Writes normalized outputs

Creates .processing and .done flags for robustness

Uses ProcessPoolExecutor for parallel speed



		Summary of Step 3-6 Output

For every PMC article included in the tar buckets, you obtain:

List of PMCIDs with abstracts

Extracted abstract text

List of PMCIDs with body text

Extracted full-text content


