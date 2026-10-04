#!/bin/bash


for year in $(seq 1990 2025); do
    # Define the PubMed query
    query='"Review"[PT] NOT "Meta-analysis"[PT] AND "'$year'"[PDAT] AND hasabstract AND medline[sb]'
    
  echo "Fetching review PMIDs for $year..."
  esearch -db pubmed -query "$query" | efetch -format uid > pmid_list_review_"$year".txt

    # 4. PMID로부터 Abstract 추출 (PMID 포함)

  echo "Fetching abstracts in batches for $year..."
  > "pmxtract_list_review_$year.txt"
  
  cat "pmid_list_review_$year.txt" | xargs -n 1000 sh -c 'efetch -db pubmed -id "$@" -format xml | xtract -pattern PubmedArticle -element MedlineCitation/PMID AbstractText' -- >> "pmxtract_list_review_$year.txt"

  echo "Finished processing year $year"
  # A longer sleep is better for bigger loops to be safe
done