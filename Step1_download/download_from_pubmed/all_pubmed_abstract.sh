#!/bin/bash


# all pubmed

for year in $(seq 1990 2025); do
  echo "--- Processing year: $year ---"

  query='"'$year'"[PDAT] AND hasabstract AND medline[sb]'

  echo "Fetching all PMIDs for $year..."
  esearch -db pubmed -query "$query" | efetch -format uid > pmid_list_all_"$year".txt

    # 4. PMID로부터 Abstract 추출 (PMID 포함)

  echo "Fetching abstracts in batches for $year..."
  > "pmxtract_list_all_$year.txt"
  
  cat "pmid_list_all_$year.txt" | xargs -n 1000 sh -c 'efetch -db pubmed -id "$@" -format xml | xtract -pattern PubmedArticle -element MedlineCitation/PMID AbstractText' -- >> "pmxtract_list_all_$year.txt"

  echo "Finished processing year $year"
  # A longer sleep is better for bigger loops to be safe
done
