#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure 3. proportion of MEDLINE abstracts with more than 1 P value that is <0=.05
"""

import sys, os

from modules.get_all_pmcids import get_all_pmcids
from modules.get_all_pmids import get_all_pmids
from modules.get_all_pmids import get_count_pmids
from modules.get_abstract_by_pmcid import get_abstract_by_pmcid
from modules.text_to_pval_and_oper import text_to_pval_and_oper
from modules.plot_histogram import plot_histogram
from Bio import Entrez
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
from collections import Counter
import csv



import subprocess
import os
import time
import matplotlib.pyplot as plt

# --- Step 1: Placeholder for YOUR function ---
# Replace this mock function with your actual function by importing it.
# from modules.text_to_pval_and_oper import text_to_pval_and_oper
#
# This placeholder simulates finding a p-value for demonstration purposes.

# # Create a directory to store the data files
# if not os.path.exists('data'):
#     os.makedirs('data')
start_year=1990
end_year=2025
# Lists to store the results for plotting
years = []
proportions = []
fields=[
        'randomized-controlled-trial','clinical-trial','meta-analysis','review','clinical-useful-journal','all-articles'
        ]


# Loop through each year from 1990 to 2015 (the range in the figure)
for field in fields:
    print(f'field: {field}')
    for year in range(start_year, end_year+1,1):
        
        filename = f"pmcxtract_list_{field}_{year}_abstract.txt"
        
        data_dir = f"/Volumes/ssd4TB/20251080/result/{field}" # folder where files are stored

        filepath = os.path.join(data_dir, filename) 
        
        years.append(year)
        total_abstracts = 0
        p_value_count = 0
        p_value_005_count=0
        p_value_001_count=0
        p_value_0005_count=0
        p_value_0001_count=0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for body_text in f: # 파일을 순회하며 한 줄씩 읽습니다.
                    body_text = body_text.strip()
                    if not body_text:
                        continue
                    
                    total_abstracts += 1
                    
                    pval_and_oper = text_to_pval_and_oper(body_text)
                    if len(pval_and_oper)>0:
                        p_value_count += 1
                        for pval, oper in pval_and_oper:
                            if pval <= 0.05:
                                p_value_005_count += 1
                                break
                        for pval, oper in pval_and_oper:
                            if pval <= 0.01:
                                p_value_001_count += 1
                                break
                        for pval, oper in pval_and_oper:
                            if pval <= 0.005:
                                p_value_0005_count += 1
                                break
                        for pval, oper in pval_and_oper:
                            if pval <= 0.001:
                                p_value_0001_count += 1
                                break
        
            print(f'{year}\t{total_abstracts}\t{p_value_count}\t{p_value_005_count}\t{p_value_001_count}\t{p_value_0005_count}\t{p_value_0001_count}')
            
        # 2차 출력
        except FileNotFoundError as e:
            print(f"{year}\t0\t0\t0\t0\t0\t0")
            continue
        # 3차 출력
        # print(p_value_005_count)
        
