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

start_year=2015
end_year=2025   
proportions = [] # (이 스크립트에서는 사용되지 않지만 유지)

# Loop through each year
fields=[
        'randomized-controlled-trial','clinical-trial','meta-analysis','review','clinical-useful-journal','all-articles'
        ]



for field in fields: 
    abs_bin_stats = defaultdict(lambda: {'total': 0, '>': 0, '=': 0, '<': 0, 'other':0})
        
    # 각 빈(bin)에 대한 통계를 저장할 딕셔너리

    bin_width = 0.001
    num_bins = 51
    max_val = bin_width * (num_bins-1) # 0.05
    total_article_abs=0
    total_pval_abs=0
    for year in range(start_year, end_year+1,1):
        abs_results = []
        # print(f"Processing year: {year}...")
        
        filename2 = f"pmcxtract_list_{field}_{year}_abstract.txt"
        
        data_dir = f"/Volumes/ssd4TB/20251080/result/{field}" 

        filepath2 = os.path.join(data_dir, filename2) 
        
        # 대신, 파일에서 직접 아티클을 순회하며 처리
        article_count = 0
        try:
            with open(filepath2, 'r', encoding='utf-8') as f2:
                for abs_text in f2: # 파일을 순회하며 한 줄씩 읽습니다.
                    abs_text = abs_text.strip()
                    if not abs_text:
                        continue
        
                    article_count += 1
                    pval_and_oper_list = text_to_pval_and_oper(abs_text)
                    if pval_and_oper_list:
                        abs_results.extend(pval_and_oper_list) 
        except FileNotFoundError as e:
            print(f"File not found, skipping field year {field} {year}: {e}")
            continue
        total_article_abs+=article_count
        total_pval_abs+=len(abs_results)
        
    # --- 수동 비닝(Binning) 및 통계 계산 ---
        
    
        for p, oper in abs_results:     
            # --- 연산자 정규화 ---
            if oper == '<' or oper == '≤' or oper == 'less than' or oper == 'of <':
                oper = '<'
            elif oper == '>' or oper == '≥':
                oper = '>'
            elif oper == '=' or oper == 'of':
                oper = '='
            else:
                oper = 'other' 
            # --- 정규화 끝 ---
    
            bin_key = f"{year}"
            # --- 정규화 끝 ---
            if 0 <= p <= max_val:
                bin_index = math.ceil(p / bin_width)
                if bin_index == 0:
                    # p value = 0 can occur in plain texts, or due to limit of p value detection algorithm, etc
                    bin_index = 1
                elif bin_index >= (num_bins-1):
                    bin_index = num_bins - 1
            elif p > max_val:
                bin_index= num_bins
            bin_key = f"{(bin_index * bin_width):.3f}"
            abs_bin_stats[bin_key]['total'] += 1
            abs_bin_stats[bin_key][oper] += 1

    print(f"{field} absBandwidth\t<\t=\t>\tother\ttotal")
    sorted_keys = sorted(abs_bin_stats.keys())
    
    for bin_key in sorted_keys:
        stats = abs_bin_stats[bin_key]
        print(f"{bin_key}\t{stats['<']}\t{stats['=']}\t{stats['>']}\t{stats['other']}\t{stats['total']}")
    print(f"total article {total_article_abs} total pvalue {total_pval_abs}")
