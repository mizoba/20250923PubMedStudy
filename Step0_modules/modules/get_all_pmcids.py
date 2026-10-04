
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
from collections import Counter
import csv



# def get_pmcids_for(retmax=100000):
#     base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    
#     # Clinical Trial publication type + Open Access filter
#     query = '"Clinical Trial"[PT] AND open access[filter]'
    
#     params = {
#         "db": "pmc",             # PubMed Central (full text articles)
#         "term": query,           # Search query
#         "retmode": "xml",        # Return format
#         "retmax": retmax,         # Max number of results
#         "email":"jake47111@gmail.com"
#     }

#     try:
#         time.sleep(0.34)  # Rate-limit 보호
#         response = requests.get(base_url, params=params)
#         print(response.url)
#         response.raise_for_status()
#         root = ET.fromstring(response.text)
#         pmcids = [id_elem.text for id_elem in root.findall(".//Id")]
#         return pmcids
#     except Exception as e:
#         print(f"❌ 실패: {e}")
#         return []
    

import requests
import xml.etree.ElementTree as ET
import time

def get_all_pmcids(query):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    
    retmax=100000
    all_ids = []
    params = {
        "db": "pmc",
        "term": query,
        "retmode": "xml",
        "retmax": retmax,
        "usehistory":"y",
        "email":"jake47111@gmail.com"
    }   

    response = requests.get(base_url, params=params)
    
    if response.status_code != 200:
        raise Exception("초기 요청 실패")
    root = ET.fromstring(response.content)
    
    total_count=int(root.findtext("Count"))
    webenv = root.findtext("WebEnv")
    query_key = root.findtext("QueryKey")
    print(f"Total count = {total_count}")
    for start in range(0, total_count, retmax):
        params = {
            "db": "pmc",
            "retmode": "xml",
            "retmax": 100000,
            "WebEnv": webenv,
            "query_key": query_key,
            "retstart": start,
            "email":"jake47111@gmail.com"
        }
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            print(f"Request failed at start={start}")
            break
        root = ET.fromstring(response.content)
        ids = [id_elem.text for id_elem in root.findall(".//Id")]
        all_ids.extend(ids)
        
        print(f"Retrieved {len(ids)} IDs (start={start})")

        # 필수: 요청 간 대기 (NCBI 제한 회피)
        time.sleep(0.34)  # 초당 3회 이하 권장
    # print(f"all ids {all_ids}")
    return all_ids
