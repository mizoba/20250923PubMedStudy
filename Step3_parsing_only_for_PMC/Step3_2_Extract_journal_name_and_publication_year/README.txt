					 Step 3-2 — Extracting Journal Name & Publication Year from PMC Metadata

Located at:
Step3_parsing_only_for_PMC/Step3_2_Extract_journal_name_and_publication_year/

In this step, we normalize the “Article Citation” field from the PMC metadata by splitting it into two separate columns:

journal

year

This is required because PMC’s OA bulk metadata does not explicitly provide journal names or publication years as structured columns.


					 Input Pattern

The column Article Citation typically follows this structure:

{content1 = Journal name}.{content2 = Published Year};{content3 = additional info}


Characteristics:

content1 (journal name) is always ≥ 3 characters

content2 (year) may be valid (e.g., 1998, 2012) or missing

content3 may or may not exist

Some rows contain misformatted or incomplete citation strings

Because PMC's citation formatting is inconsistent, we perform a two-stage extraction.


					 Step 3-2-1 — Pattern-Based Extraction

Script: Step3_2_1_extract_by_pattern.py 

This script:

Applies a robust regular expression to parse:

journal name

publication year

Creates two new columns:

journal

year

Identifies rows that do not match the expected pattern

Saves these problematic rows to:

invalid_rows.csv


These rows require manual correction because their citation strings deviate from standard formatting.

					 Step 3-2-2 — Handling Invalid Patterns

Script: Step3_2_2_deal_with_invalid_pattern.py 

This step processes the rows that failed automated pattern extraction.

Workflow:

1. Open invalid_rows.csv

2. Manually extract the correct:

journal name

year

3. Save the cleaned rows as:

invalid_rows_fixed.csv

4. The script merges these corrected rows back into the main dataset using:

A unique identifier (e.g., AccessionID)

5. Saves the final normalized file as:

step3normalized_with_journal_year.csv



					 Output

Final output of Step 3-2:

step3normalized_with_journal_year.csv


This file contains complete, cleaned metadata for all PMC articles, including:

Journal name

Publication year

Original PMC metadata

Previously added PublicationType (from Step 3-1)