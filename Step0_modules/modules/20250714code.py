# Core Clinical Journal csv를 바탕으로, 논문 ID를 수집하고, ID로 ABSTRACT를 수집하고, ABSTRACT에서 P value를 추출하여 그래프로 그림

import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
from collections import Counter
import csv

#🔹 Step 1: 저널 목록 불러오기
# CSV에서 MedlineTA 열만 불러옴
df = pd.read_csv("journals.csv")
journal_list = df["MedlineTA"].dropna().unique().tolist()
print(f"✅ 총 {len(journal_list)}개의 저널이 로드됨")

#🔹 Step 2: PMC에서 Open Access 논문 검색 (esearch)
def get_pmcids_for_journal(journal_name, retmax=100000):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    query = f'"{journal_name}"[Journal] AND open access[filter]'
    params = {
        "db": "pmc",
        "term": query,
        "retmode": "xml",
        "retmax": retmax
    }

    try:
        time.sleep(0.34)  # Rate-limit 보호
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        pmcids = [id_elem.text for id_elem in root.findall(".//Id")]
        return pmcids
    except Exception as e:
        print(f"❌ {journal_name} 실패: {e}")
        return []

#🔹 Step 3: 초록(abstract) 가져오기 (efetch) by pcmids
def get_abstract_by_pmcid(pmcids):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    batch_size = 200
    abstract_text_all = ""

    for i in range(0, len(pmcids), batch_size):
        batch_ids = pmcids[i:i+batch_size]
        params = {
            "db": "pubmed",
            "id": ",".join(batch_ids),
            "retmode": "xml",
            "email":"jake47111@gmail.com"
        }
        time.sleep(0.34)  # Rate-limit 보호
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            root = ET.fromstring(response.text)
    
            abstract_text = ""
            for abstract in root.findall(".//Abstract"):
              parts = [elem.text for elem in abstract.iter() if elem.text]
              abstract_text += " ".join(parts) + " "
            else:
                print("No abstract found")
            abstract_text_all += abstract_text + "\n"
    
            '''
            for abstract in root.findall(".//Abstract"):
                abstract_text = abstract.findtext(".//AbstractText")
                if abstract_text:
                    abstract_text_all += abstract_text + "\n"
    '''
        except Exception as e:
            print(f"❌ Abstract fetch 실패 (PMC{batch_ids}): {e}")

    return abstract_text_all.strip()
        
#🔹 Step 4: 전체 저널 + 논문 → 초록 모으기
all_abstracts2 = []

for journal in journal_list[0:10]:
    print(f"🔍 {journal} → PMC 검색 중...")
    pmc_ids = get_pmcids_for_journal(journal, retmax=100000)  # 실험 시 적은 수로 제한
    print(f"   ↪️ {len(pmc_ids)}건 발견")

    abs_text = get_abstract_by_pmcid(pmc_ids)
    if abs_text:
        all_abstracts2.append(abs_text)
    total_abstract="\n\n".join(all_abstracts2)
with open("total_abstract.txt", "w", encoding="utf-8") as f:
    f.write(total_abstract)  # 각 abstract 블록 사이 2줄 띄움

print(f"📄 총 {len(all_abstracts2)}개의 초록이 저장됨")   

pval_oper_list = text_to_pval_and_oper(total_abstract)
plot_histogram([pval for pval,oper in pval_oper_list])
