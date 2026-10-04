#!/usr/bin/env python3
import sys, os

# --------module import----------
# (참고: text_to_pval_and_oper 외에는 이 스크립트에서 실제로 사용되지 않음)
from modules.text_to_pval_and_oper import text_to_pval_and_oper
from scipy import stats  # distinct import for trimmed mean if desired
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
        'all'
        ]


for field in fields: 

    bin_stats = defaultdict(lambda: {'density_all':0,'mean':0,'trimmed_mean':0,'prop_gt_5':0,'average':0,'median': 0, 'p_25': 0, 'p_75': 0, 'article_count': 0,'article_haspval_count':0,'pval_count':0})
    print(f"{field}\tmean\ttrimmed_mean\tprop_gt_5\tdensity_all\tp_25\tmedian\tp_75\tarticle_count\tarticle_haspval_count\tpval_count")
    
    # 각 빈(bin)에 대한 통계를 저장할 딕셔너리

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
        
        total_pval+=pval_count
        total_article+=article_count
        total_article_haspval+=article_haspval_count
        
    # --- 수동 비닝(Binning) 및 통계 계산 ---
        import numpy as np
        
        p_num_median=0
        p_num_25=0
        p_num_75=0
        p_mean = 0
        p_trimmed_mean=0
        p_prop_high = 0 # Proportion with > 5 p-values
        p_density_all = 0 # Mean over ALL articles (including 0s)
        
        if results:
            # 1. The Mean (Smooth trend)
            p_mean = np.mean(results)
            
            # 2. Trimmed Mean (Robust trend - removes top/bottom 5% outliers)
            # This prevents one crazy paper with 200 p-values from skewing the graph
            p_trimmed_mean = stats.trim_mean(results, 0.05) 
    
            # 3. Proportion of "P-value dense" papers (> 5 p-values)
            # converts boolean list to float mean (True=1, False=0)
            p_prop_high = np.mean(np.array(results) > 5) 
    
            # Standard Percentiles
            p_num_25, p_num_median, p_num_75 = np.percentile(results, [25, 50, 75])
        
        # 4. Density (Total P-values / Total Articles scanned)
        if article_haspval_count > 0:
            p_density_all = pval_count / article_count
    
        bin_key = f"{year}"
        bin_stats[bin_key]['mean'] = p_mean
        bin_stats[bin_key]['trimmed_mean'] = p_trimmed_mean
        bin_stats[bin_key]['prop_gt_5'] = p_prop_high
        bin_stats[bin_key]['density_all'] = p_density_all
        bin_stats[bin_key]['median'] = p_num_median
        bin_stats[bin_key]['p_75'] = p_num_75
        bin_stats[bin_key]['p_25'] = p_num_25
        bin_stats[bin_key]['article_count'] = article_count
        bin_stats[bin_key]['article_haspval_count'] = article_haspval_count
        bin_stats[bin_key]['pval_count']=pval_count
        s = bin_stats[f"{bin_key}"]
        print(f"{bin_key}\t{s['mean']:.4f}\t{s['trimmed_mean']:.4f}\t{s['prop_gt_5']:.4f}\t{s['density_all']:.4f}\t{s['p_25']}\t{s['median']}\t{s['p_75']}\t{s['article_count']}\t{s['article_haspval_count']}\t{s['pval_count']}")
    print(f"total article {total_article} total article haspvalue {total_article_haspval} total pvalue {total_pval}")
