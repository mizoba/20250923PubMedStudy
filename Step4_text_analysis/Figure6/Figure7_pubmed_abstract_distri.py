#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 05:59:38 2025

@author: choijinhyeok
"""

#!/usr/bin/env python3
import sys, os
from scipy import stats  # distinct import for trimmed mean if desired
import numpy as np
# --------module import----------
# (참고: text_to_pval_and_oper 외에는 이 스크립트에서 실제로 사용되지 않음)
from modules.text_to_pval_and_oper import text_to_pval_and_oper
# from modules.get_all_pmcids import get_all_pmcids
# from modules.get_all_pmids import get_all_pmids
# from modules.get_all_pmids import get_count_pmids
# from modules.get_abstract_by_pmcid import get_abstract_by_pmcid
# from modules.plot_histogram import plot_histogram
# from Bio import Entrez
# import requests
# import pandas as pd
# import xml.etree.ElementTree as ET
import time
from collections import Counter, defaultdict # defaultdict 사용
import csv
import subprocess
import os
import time
import matplotlib.pyplot as plt
import math

start_year=1990
end_year=2025   
proportions = []

# Loop through each year

fields=[
        'all' ]



for field in fields: 

    bin_stats = defaultdict(lambda: {'1':0,'2':0,'3':0,'4':0,'5':0,'6':0,'7':0,'8':0,'9':0,'10':0,'11to100':0,'101to1000':0,'morethan1000':0,'article_count':0,'article_haspval_count':0,'pval_count':0})
        
    # 각 빈(bin)에 대한 통계를 저장할 딕셔너리
    print(f"{field}\t1\t2\t3\t4\t5\t6\t7\t8\t9\t10\t11to100\t101to1000\tmorethan1000\tarticle_count\tarticle_haspval_count\tpval_count")  

    total_article=0
    total_article_haspval = 0
    total_pval=0
    for year in range(start_year, end_year+1,1):
        results = []
        #print(f"Processing year: {year}...")
        
        filename2 = f"pmxtract_list_{field}_{year}.txt"
        
        data_dir = f"/Volumes/ssd4TB/pubmed/xtract/{field}" 

        filepath2 = os.path.join(data_dir, filename2) 

        # 대신, 파일에서 직접 아티클을 순회하며 처리
        article_count = 0
        article_haspval_count = 0
        pval_count = 0
        
        try:
            with open(filepath2, 'r', encoding='utf-8') as f2:
                for text in f2: # 파일을 순회하며 한 줄씩 읽습니다.
                    text = text.strip()
                    if not text:
                        continue
        
                    article_count += 1
                    pval_and_oper_list = text_to_pval_and_oper(text)
                    if pval_and_oper_list:
                        article_haspval_count += 1
                        results.append(len(pval_and_oper_list)) 
                        pval_count+=len(pval_and_oper_list)
        except FileNotFoundError as e:
            # print(f"File not found, skipping field year {field} {year}: {e}")
            continue
        
        total_article+=article_count
        total_article_haspval+=article_haspval_count
        total_pval+=pval_count
        
    # --- 수동 비닝(Binning) 및 통계 계산 ---
        
        
        bin_key=f"{year}"
        bin_stats[bin_key]['article_count']=article_count
        bin_stats[bin_key]['article_haspval_count']=article_haspval_count
        bin_stats[bin_key]['pval_count']=pval_count
        if results:
            for result in results:
                if result>1000:
                    bin_stats[bin_key]['morethan1000']+=1
                elif result>100:
                    bin_stats[bin_key]['101to1000']+=1
                elif result>10:
                    bin_stats[bin_key]['11to100']+=1
                else:
                    bin_stats[bin_key][f"{result}"]+=1
        s = bin_stats[f"{bin_key}"]
        print(f"{bin_key}\t{s['1']}\t{s['2']}\t{s['3']}\t{s['4']}\t{s['5']}\t{s['6']}\t{s['7']}\t{s['8']}\t{s['9']}\t{s['10']}\t{s['11to100']}\t{s['101to1000']}\t{s['morethan1000']}\t{s['article_count']}\t{s['article_haspval_count']}\t{s['pval_count']}")
    print(f"total article {total_article} total article haspval {total_article_haspval} total pvalue {total_pval}")
