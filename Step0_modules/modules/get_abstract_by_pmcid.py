# -*- coding: utf-8 -*-
"""
Created on Fri Aug  1 08:14:06 2025

@author: jake4
"""
import traceback

import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
from collections import Counter
import csv

#🔹 Step 3: 초록(abstract) 가져오기 (efetch) by pcmids
def get_abstract_by_pmcid(pmcids):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    batch_size = 200
    abstract_text_all = ""
    
    for i in range(0, 1000, batch_size):
        batch_ids = pmcids[i:i+batch_size]
        params = {
            "db": "pmc",
            "id": ",".join(batch_ids),
            "retmode": "xml",
            "email":"jake47111@gmail.com"
        }
        time.sleep(0.34)  # Rate-limit 보호
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            try:
                root = ET.fromstring(response.text)
            except ET.ParseError as e:
                print(f"❌ XML 파싱 오류 (PMC IDs: {i}): {e}")
                continue
            
            abstract_text=""
            abstract_nodes = root.findall(".//abstract")
            # Pubmed이면 Abstract
            if not abstract_nodes:
                print(f"⚠️ No abstract found in batch {batch_ids}")
            else:
                for abstract in abstract_nodes:
                    parts = [elem.text for elem in abstract.iter() if elem.text]
                    abstract_text += " ".join(parts) + " "
            abstract_text_all += abstract_text.strip() + "\n"
            print(f"well done {i}")
        except Exception as e:
            print(f"❌ Abstract fetch 실패 (PMC{i}): {e}")
            
            print("❌ 네트워크 오류 발생:")
            print(f"   ⤷ {type(e).__name__}: {e}")
            traceback.print_exc()
            # 요청 헤더
            print("📤 [Request Headers]")
            for k, v in response.request.headers.items():
                print(f"{k}: {v}")
            
            # 응답 헤더
            print("\n📥 [Response Headers]")
            for k, v in response.headers.items():
                print(f"{k}: {v}")
    
            # 응답 본문(XML)
            print("\n📦 [Response XML Preview]")
            print(response.text[:1000])  # 미리보기
                
            # XML 파싱
            try:
                root = ET.fromstring(response.content)
                print("\n🧩 [Parsed XML Structure]")
                for child in root[:10]:  # 최상위 하위 요소 일부만 미리 보기
                    print(f"Tag: {child.tag}, Attributes: {child.attrib}")
            except ET.ParseError as pe:
                print(f"❌ XML 파싱 실패: {pe}")

    

    return abstract_text_all.strip()
        