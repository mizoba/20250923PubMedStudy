#!/usr/bin/env python3
import sys, os

# --- 모듈 임포트 ---
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
from math import log
start_year=1990
end_year=2025   
proportions = [] # (이 스크립트에서는 사용되지 않지만 유지)

# Loop through each year
fields=[
        'rct','ct','meta','review','cuj','all'
        ]


for field in fields: 
    print(field)
    total_article_abs=0
    total_pval_abs=0
    error=0
    for year in range(start_year, end_year+1,1):
        abs_min_p_results = []
        abs_max_p_results = []
        # print(f"Processing year: {year}...")
        
        filename2 = f"pmxtract_list_{field}_{year}.txt"
        
        data_dir = f"/Volumes/ssd4TB/pubmed/xtract/{field}" 

        filepath2 = os.path.join(data_dir, filename2) 

        # 대신, 파일에서 직접 아티클을 순회하며 처리
        article_count = 0
        abs_includes_p = 0
        try:
            with open(filepath2, 'r', encoding='utf-8') as f2:
                for abs_text in f2: # 파일을 순회하며 한 줄씩 읽습니다.
                    abs_text = abs_text.strip()
                    if not abs_text:
                        continue
                    
                    article_count += 1
                    
                    pval_and_oper_list = text_to_pval_and_oper(abs_text)
                    
                    if pval_and_oper_list:
                        abs_includes_p += 1
                        min_p=10
                        max_p=0
                        min_updated_flag=0
                        max_updated_flag=0
                        for pval, oper in pval_and_oper_list:
                            if pval != 0.0:
                                if pval<min_p:
                                    min_p = pval
                                    min_updated_flag=1
                                if pval>max_p:
                                    max_p = pval
                                    max_updated_flag=1
                        if min_updated_flag==1:
                            abs_min_p_results.append(min_p) 
                        if max_updated_flag==1:
                            abs_max_p_results.append(max_p) 
                    
        except FileNotFoundError as e:
            print(f"{year}\t0\t0\t0\t0\t0\t0")
            continue
        total_article_abs+=article_count
        total_pval_abs+=abs_includes_p
        
    # --- -logp값 평균 계산 ---
        
        min_count = 0
        min_log_add = 0
        min_log_avg=0
        for pval in abs_min_p_results:     
            if pval == 0:
                print(error)
                continue
            min_count +=1
            min_log_add += -math.log(pval,10)
        if min_count > 0:
            min_log_avg = min_log_add/min_count

        
        max_count = 0
        max_log_add = 0
        max_log_avg=0
        for pval in abs_max_p_results:     
            if pval == 0:
                print(error)
                continue
            max_count +=1
            max_log_add += -math.log(pval,10)
        if max_count > 0:
            max_log_avg = max_log_add/max_count

        
        print(f"{year}\t{min_log_avg}\t{max_log_avg}\t{article_count}\t{abs_includes_p}\t{min_count}\t{max_count}")
        