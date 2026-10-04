#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 16 04:45:32 2025

@author: choijinhyeok

다운로드받은 초록들의 무결성 검증하기
Checking Integrity

"""

import sys, os
from modules.get_all_pmids import get_all_pmids
from modules.get_all_pmids import get_count_pmids
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
import re

start_year=1990
end_year=2025
years = []
proportions = []

def stripfolder(folder_path):
    # folder_path = "/Users/choijinhyeok/coreclinicaljournal"
    
    # Loop over all files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):  # only process .txt files
            filepath = os.path.join(folder_path, filename)
                    
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip().split('\n')  # automatically removes \n
            # Remove empty lines
            lines = [line for line in content if line.strip()]
            # Write back to the same file
            with open(filepath, 'w', encoding='utf-8') as f:
                for line in lines:
                    f.write(line + '\n')


def get_query(field,year):
    if field=="ct":
        return f'"Clinical Trial"[PT] NOT "Randomized Controlled trial"[PT] AND "{year}"[PDAT] AND hasabstract AND medline[sb]'
    if field=="rct":
        return f'"Randomized Controlled Trial"[PT] AND "{year}"[PDAT] AND hasabstract AND medline[sb]'
    if field=="meta":
        return f'"Meta-analysis"[PT] AND "{year}"[PDAT] AND hasabstract AND medline[sb]'
    if field=="review":
        return f'"Review"[PT] NOT "Meta-analysis"[PT] AND "{year}"[PDAT] AND hasabstract AND medline[sb]'
    if field=="all":
        return f'"{year}"[PDAT] AND hasabstract AND medline[sb]'
    if field=="cuj":
        return f'("AACN Adv Crit Care"[Journal] OR "Acad Emerg Med"[Journal] OR "Acad Med"[Journal] OR "Addict Behav"[Journal] OR "Age Ageing"[Journal] OR "AJR Am J Roentgenol"[Journal] OR "Allergy"[Journal] OR "Am Fam Physician"[Journal] OR "Am Heart J"[Journal] OR "Am J Epidemiol"[Journal] OR "Am J Gastroenterol"[Journal] OR "Am J Hematol"[Journal] OR "Am J Kidney Dis"[Journal] OR "Am J Med Genet A"[Journal] OR "Am J Med"[Journal] OR "Am J Nurs"[Journal] OR "Am J Obstet Gynecol"[Journal] OR "Am J Prev Med"[Journal] OR "Am J Psychiatry"[Journal] OR "Am J Respir Crit Care Med"[Journal] OR "Am J Sports Med"[Journal] OR "Am J Surg Pathol"[Journal] OR "Am J Med Sci"[Journal] OR "Anesth Analg"[Journal] OR "Ann Allergy Asthma Immunol"[Journal] OR "Ann Emerg Med"[Journal] OR "Ann Intern Med"[Journal] OR "Ann Neurol"[Journal] OR "Ann Oncol"[Journal] OR "Ann Pharmacother"[Journal] OR "Ann Surg"[Journal] OR "Ann Surg Oncol"[Journal] OR "Ann Rheum Dis"[Journal] OR "Ann Thorac Surg"[Journal] OR "Arch Dis Child"[Journal] OR "Arch Dis Child Fetal Neonatal Ed"[Journal] OR "Arch Phys Med Rehabil"[Journal] OR "Arthritis Rheumatol"[Journal] OR "Arthritis Care Res (Hoboken)"[Journal] OR "Arthroscopy"[Journal] OR "Autoimmun Rev"[Journal] OR "Best Pract Res Clin Rheumatol"[Journal] OR "Biol Psychiatry"[Journal] OR "BJOG"[Journal] OR "BJU Int"[Journal] OR "Blood"[Journal] OR "BMJ"[Journal] OR "Bone Marrow Transplant"[Journal] OR "Brain"[Journal] OR "Breastfeed Med"[Journal] OR "Br J Anaesth"[Journal] OR "Br J Cancer"[Journal] OR "Br J Dermatol"[Journal] OR "Br J Haematol"[Journal] OR "Br J Ophthalmol"[Journal] OR "Br Med Bull"[Journal] OR "CA Cancer J Clin"[Journal] OR "Cancer"[Journal] OR "Cancer Treat Rev"[Journal] OR "Catheter Cardiovasc Interv"[Journal] OR "Chest"[Journal] OR "Circulation"[Journal] OR "Clin Biochem"[Journal] OR "Clin Biomech (Bristol)"[Journal] OR "Clin Gastroenterol Hepatol"[Journal] OR "Clin Infect Dis"[Journal] OR "Clin Obstet Gynecol"[Journal] OR "Clin Pharmacol Ther"[Journal] OR "Clin Ther"[Journal] OR "Clin Podiatr Med Surg"[Journal] OR "CMAJ"[Journal] OR "Comput Inform Nurs"[Journal] OR "Crit Care Med"[Journal] OR "Curr Opin Cardiol"[Journal] OR "Curr Opin Gastroenterol"[Journal] OR "Curr Opin Nephrol Hypertens"[Journal] OR "Curr Opin Pediatr"[Journal] OR "Curr Opin Rheumatol"[Journal] OR "Diabetes Care"[Journal] OR "Diabetes Res Clin Pract"[Journal] OR "Diagn Microbiol Infect Dis"[Journal] OR "Dig Dis Sci"[Journal] OR "Dis Colon Rectum"[Journal] OR "Drug Alcohol Depend"[Journal] OR "Early Hum Dev"[Journal] OR "Epilepsia"[Journal] OR "Epilepsy Behav"[Journal] OR "Europace"[Journal] OR "Eur Heart J"[Journal] OR "Eur J Cancer"[Journal] OR "Eur J Cardiothorac Surg"[Journal] OR "Eur J Heart Fail"[Journal] OR "Eur J Intern Med"[Journal] OR "Eur J Nucl Med Mol Imaging"[Journal] OR "Eur J Radiol"[Journal] OR "Eur Urol"[Journal] OR "Fertil Steril"[Journal] OR "Gastroenterology"[Journal] OR "Gastrointest Endosc"[Journal] OR "Gut"[Journal] OR "Gynecol Oncol"[Journal] OR "Head Neck"[Journal] OR "Headache"[Journal] OR "Health Aff (Millwood)"[Journal] OR "Heart"[Journal] OR "Heart Rhythm"[Journal] OR "Hepatology"[Journal] OR "Hum Pathol"[Journal] OR "Hum Reprod"[Journal] OR "Hypertension"[Journal] OR "Infect Control Hosp Epidemiol"[Journal] OR "Int J Antimicrob Agents"[Journal] OR "Int J Cancer"[Journal] OR "Int J Cardiol"[Journal] OR "Int J Clin Pract"[Journal] OR "Int J Obes"[Journal] OR "Int J Radiat Oncol Biol Phys"[Journal] OR "Int Urogynecol J"[Journal] OR "JAMA"[Journal] OR "JAMA Dermatol"[Journal] OR "JAMA Intern Med"[Journal] OR "JAMA Neurol"[Journal] OR "JAMA Ophthalmol"[Journal] OR "JAMA Otolaryngol Head Neck Surg"[Journal] OR "JAMA Pediatr"[Journal] OR "JAMA Psychiatry"[Journal] OR "JAMA Surg"[Journal] OR "J Healthc Qual"[Journal] OR "J Acquir Immune Defic Syndr"[Journal] OR "J Adv Nurs"[Journal] OR "J Allergy Clin Immunol"[Journal] OR "J Altern Complement Med"[Journal] OR "J Bone Joint Surg Am"[Journal] OR "J Card Fail"[Journal] OR "J Clin Endocrinol Metab"[Journal] OR "J Clin Gastroenterol"[Journal] OR "J Clin Neurosci"[Journal] OR "J Clin Oncol"[Journal] OR "J Clin Pathol"[Journal] OR "J Clin Psychol"[Journal] OR "J Clin Psychopharmacol"[Journal] OR "J Emerg Med"[Journal] OR "J Foot Ankle Surg"[Journal] OR "J Gen Intern Med"[Journal] OR "J Hand Surg Am"[Journal] OR "J Hepatol"[Journal] OR "J Hosp Infect"[Journal] OR "J Hosp Med"[Journal] OR "J Infect"[Journal] OR "J Infect Dis"[Journal] OR "J Intern Med"[Journal] OR "J Invest Dermatol"[Journal] OR "J Med Genet"[Journal] OR "J Midwifery Womens Health"[Journal] OR "J Neurol Neurosurg Psychiatry"[Journal] OR "J Nurs Adm"[Journal] OR "J Obstet Gynecol Neonatal Nurs"[Journal] OR "J Occup Environ Med"[Journal] OR "J Oral Maxillofac Surg"[Journal] OR "J Orthop Sports Phys Ther"[Journal] OR "J Orthop Trauma"[Journal] OR "J Pain Symptom Manage"[Journal] OR "J Palliat Med"[Journal] OR "J Pediatr Gastroenterol Nutr"[Journal] OR "J Pediatr Hematol Oncol"[Journal] OR "J Pediatr Orthop"[Journal] OR "J Pediatr Surg"[Journal] OR "J Perinatol"[Journal] OR "J Psychopharmacol"[Journal] OR "J Subst Abuse Treat"[Journal] OR "J Surg Oncol"[Journal] OR "J Am Coll Cardiol"[Journal] OR "J Am Geriatr Soc"[Journal] OR "J Am Med Dir Assoc"[Journal] OR "J Am Med Inform Assoc"[Journal] OR "J Natl Cancer Inst"[Journal] OR "J Thorac Cardiovasc Surg"[Journal] OR "J Thromb Haemost"[Journal] OR "J Trauma Acute Care Surg"[Journal] OR "J Urol"[Journal] OR "J Vasc Surg"[Journal] OR "JPEN J Parenter Enteral Nutr"[Journal] OR "Kidney Int"[Journal] OR "Lancet"[Journal] OR "Laryngoscope"[Journal] OR "Leukemia"[Journal] OR "Liver Transpl"[Journal] OR "Med Care"[Journal] OR "Med Clin North Am"[Journal] OR "Med Lett Drugs Ther"[Journal] OR "Medicine (Baltimore)"[Journal] OR "Mod Pathol"[Journal] OR "Mol Genet Metab"[Journal] OR "Mov Disord"[Journal] OR "Muscle Nerve"[Journal] OR "Nephrol Dial Transplant"[Journal] OR "Neurology"[Journal] OR "Neurosurgery"[Journal] OR "N Engl J Med"[Journal] OR "Nursing"[Journal] OR "Obesity (Silver Spring)"[Journal] OR "Obstet Gynecol Surv"[Journal] OR "Obstet Gynecol"[Journal] OR "Oral Surg Oral Med Oral Pathol Oral Radiol"[Journal] OR "Otolaryngol Head Neck Surg"[Journal] OR "Pain"[Journal] OR "Pain Med"[Journal] OR "Patient Educ Couns"[Journal] OR "Pediatr Dermatol"[Journal] OR "Pediatr Infect Dis J"[Journal] OR "Pediatrics"[Journal] OR "Pharmacoepidemiol Drug Saf"[Journal] OR "Plast Reconstr Surg"[Journal] OR "Postgrad Med J"[Journal] OR "Prev Med"[Journal] OR "Prim Care"[Journal] OR "Psychiatr Serv"[Journal] OR "QJM"[Journal] OR "Radiographics"[Journal] OR "Radiology"[Journal] OR "Radiother Oncol"[Journal] OR "Respir Med"[Journal] OR "Semin Dial"[Journal] OR "Semin Nucl Med"[Journal] OR "Semin Perinatol"[Journal] OR "Semin Respir Crit Care Med"[Journal] OR "Semin Ultrasound CT MR"[Journal] OR "Sex Transm Dis"[Journal] OR "Sex Transm Infect"[Journal] OR "Soc Sci Med"[Journal] OR "South Med J"[Journal] OR "Spine (Phila Pa 1976)"[Journal] OR "Stat Methods Med Res"[Journal] OR "Stat Med"[Journal] OR "Stroke"[Journal] OR "Thorax"[Journal] OR "Thromb Res"[Journal] OR "Thyroid"[Journal] OR "Ultrasound Obstet Gynecol"[Journal] OR "Vaccine"[Journal] OR "World Neurosurg"[Journal]) AND "{year}"[PDAT] AND hasabstract AND medline[sb]'
    if field=="Systematic_Review":
        return f'"Systematic Review"[PT] AND "{year}"[PDAT] AND hasabstract AND medline[sb]'
    if field=="Observational_Study":
        return f'"Observational Study"[PT] AND "{year}"[PDAT] AND hasabstract AND medline[sb]'
    return "error"

def remove_duplicate_lines(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Keep order but remove duplicates
    seen = set()
    unique_lines = []
    for line in lines:
        if line not in seen:
            unique_lines.append(line)
            seen.add(line)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(unique_lines)

#returns num of rows in text
def length(content):
    listof = [line for line in content.strip().split('\n') if line.strip()]
    return len(listof)

#key = xtract or id

def get_filepath_from_key(key,foldername,field,year):
        filename = f"pm{key}_list_{field}_{year}.txt"

        data_dir = f"/Users/choijinhyeok/spydercoding/20250801/xtract/{foldername}" # folder where files are stored

        filepath = os.path.join(data_dir, filename) 
        return filepath
    
def get_list_from_filepath(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    
        # Abstracts in the efetch output are separated by double newlines
        listof = [line for line in content.strip().split('\n') if line.strip()]
        return listof
# Integrity check
# print(len(get_file_to_list('id','rct','1997')))

#does number of id same with efetch? #does number of id same with efetch?#does number of id same with efetch?
#does number of id same with efetch? #does number of id same with efetch?#does number of id same with efetch?
#does number of id same with efetch? #does number of id same with efetch?#does number of id same with efetch?


for field in ['cuj']:
    for year in range(start_year,end_year+1,1):
            query=get_query(field, year)
            count_pmids = get_count_pmids(query)
            
            # data_dir = f"/Users/choijinhyeok/spydercoding/20250801/xtract/{field}" # folder where files are stored
            data_dir = f"/Users/choijinhyeok/cuj"
            idfilename= f"pmid_list_{field}_{year}.txt"
            idfilepath= os.path.join(data_dir,idfilename)
            
            with open(idfilepath,'r',encoding='utf-8') as f:
                content = f.read()
            ids=content.strip().split('\n')
            if len(ids) == 1 and ids[0] == '':
                ids = []
            total_id_count = len(ids)
            time.sleep(0.34)
            
            if count_pmids == total_id_count:
                print(f"{year} well done!")
            else:
                print(f"{year} internet_pmids={count_pmids}, saved_count={total_id_count}")

#does number of abstract text same with number of id? #does number of abstract text same with number of id?#does number of abstract text same with number of id?
#does number of abstract text same with number of id? #does number of abstract text same with number of id?#does number of abstract text same with number of id?
#does number of abstract text same with number of id? #does number of abstract text same with number of id?#does number of abstract text same with number of id?

for field in ['cuj']:
    for year in range(start_year,end_year+1,1):
            total_id_count=len(get_list_from_filepath(f"/Users/choijinhyeok/cuj/pmid_list_{field}_{year}.txt"))
            total_xtract_count=len(get_list_from_filepath(f"/Users/choijinhyeok/cuj/pmxtract_list_{field}_{year}.txt"))
            if total_xtract_count == total_id_count:
                print(f"{year} {field} well done!")
            else:
                print(f"{year} ids={total_id_count}, total_xtract_count={total_xtract_count}")

#If there are some IDs missing, define missing ids

for field in ['cuj']:
     for year in range(start_year,end_year+1,1):
        id_file = f"/Users/choijinhyeok/cuj/pmid_list_{field}_{year}.txt"         # right-side file (just IDs)
        abstract_file = f"/Users/choijinhyeok/cuj/pmxtract_list_{field}_{year}.txt"  # left-side file (ID + abstract)
        
        # Step 1: load ID list
        with open(id_file, "r") as f:
            ids= f.read().strip().split('\n')
        with open(abstract_file, "r") as f:
            abstracts= f.read().strip().split('\n')
        
        missing_ids = len(ids)-len(abstracts)
        print(f"{year} Missing {missing_ids} abstracts")
        
        abstract_ids=[line.strip().split()[0] for line in abstracts]
        missing_ids = sorted(set(ids) - set(abstract_ids))

        if missing_ids:
            output_dir = "/Users/choijinhyeok"
            out_path = os.path.join(output_dir, f"missingid_{year}.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(missing_ids))
            print(f"Saved {len(missing_ids)} IDs → {out_path}")



#operate in shell
#For missing years; do
#Revise filename, dir before you start

for year in 1993 1995 2007 2016; do
  echo "--- Processing year: $year ---"
    # 4. PMID로부터 Abstract 추출 (PMID 포함)

  echo "Fetching abstracts in batches for $year..."
  
  cat "missingid_$year.txt" | xargs -n 1000 sh -c 'efetch -db pubmed -id "$@" -format xml | xtract -pattern PubmedArticle -element MedlineCitation/PMID AbstractText' -- >> "pmxtract_list_cuj_$year.txt"

  echo "Finished processing year $year"
  # A longer sleep is better for bigger loops to be safe
done


