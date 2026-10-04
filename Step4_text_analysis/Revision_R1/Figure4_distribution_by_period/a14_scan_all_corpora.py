"""A14 보충 — eFigure 3-5용 P-value 분포 스캔: 3개 코퍼스 × 6개 카테고리, 연도별

a14_scan_distribution.py(PMC full-texts의 RCT·전체만)와 같은 방법을 3개 코퍼스, 6개 카테고리로 넓힌 것이다.
구간 규칙·연산자 분류·검출 모듈은 제출본 Figure 2를 만든 Step4_text_analysis/Figure2/Fig2_*_to_pval.py 와 같다.
연도별로 저장하므로 2016-2025, 1990-2015 같은 기간 합산을 다시 스캔 없이 할 수 있다. 제외하는 연도·논문은 없다.

원자료 (읽기만 한다)
  PubMed abstracts  /Volumes/ssd4TB/pubmed/xtract/<분야>/pmxtract_list_<분야>_<연도>.txt
  PMC abstracts     /Volumes/ssd4TB/20251080/result/<분야>/pmcxtract_list_<분야>_<연도>_abstract.txt
  PMC full-texts    /Volumes/ssd4TB/20251080/result/<분야>/pmcxtract_list_<분야>_<연도>_body.txt
  한 줄 = 논문 1편.

출력  out/bins_by_year_all.csv      corpus, field, year, bin, lt, eq, gt, other
      out/articles_by_year_all.csv  corpus, field, year, n_articles, n_pvalues, n_negative_skipped
사용  python3.11 a14_scan_all_corpora.py [--procs 8] [--years 1990-2025]
"""
import argparse
import csv
import os
import time
from collections import defaultdict
from multiprocessing import Pool

from a14_scan_distribution import NUM_BINS, bin_of, normalize_operator, text_to_pval_and_oper   # 같은 규칙을 그대로 쓴다

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
FIELDS = ['rct', 'ct', 'meta', 'review', 'cuj', 'all']          # 제출본 Figure 2와 같은 6개 카테고리
PMC_DIR = {'rct': 'randomized-controlled-trial', 'ct': 'clinical-trial', 'meta': 'meta-analysis', 'review': 'review',
           'cuj': 'clinical-useful-journal', 'all': 'all-articles'}


def path_of(corpus, field, year):
    if corpus == 'pubmed_abs':
        return f'/Volumes/ssd4TB/pubmed/xtract/{field}/pmxtract_list_{field}_{year}.txt'
    part = 'abstract' if corpus == 'pmc_abs' else 'body'
    d = PMC_DIR[field]
    return f'/Volumes/ssd4TB/20251080/result/{d}/pmcxtract_list_{d}_{year}_{part}.txt'


def scan_one(job):
    corpus, field, year = job
    path = path_of(corpus, field, year)
    if not os.path.exists(path):
        return corpus, field, year, None, 0, 0, 0
    counts = defaultdict(lambda: {'lt': 0, 'eq': 0, 'gt': 0, 'other': 0})
    n_articles = n_pvalues = n_negative = 0
    with open(path, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            n_articles += 1
            found = text_to_pval_and_oper(line)
            if not found:
                continue
            n_pvalues += len(found)
            for p, oper in found:
                b = bin_of(p)
                if b is None:
                    n_negative += 1
                    continue
                counts[b][normalize_operator(oper)] += 1
    return corpus, field, year, dict(counts), n_articles, n_pvalues, n_negative


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--procs', type=int, default=8)
    ap.add_argument('--years', default='1990-2025')
    a = ap.parse_args()
    y0, y1 = (int(x) for x in a.years.split('-'))
    os.makedirs(OUT, exist_ok=True)
    jobs = [(c, f, y) for c in ('pubmed_abs', 'pmc_abs', 'pmc_body') for f in FIELDS for y in range(y0, y1 + 1)]
    jobs.sort(key=lambda j: -os.path.getsize(path_of(*j)) if os.path.exists(path_of(*j)) else 0)   # 큰 파일부터
    bins_path = os.path.join(OUT, 'bins_by_year_all.csv')
    arts_path = os.path.join(OUT, 'articles_by_year_all.csv')
    t0, rows_bins, rows_arts, done = time.time(), [], [], 0

    def save():
        with open(bins_path, 'w', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(['corpus', 'field', 'year', 'bin', 'lt', 'eq', 'gt', 'other'])
            w.writerows(sorted(rows_bins))
        with open(arts_path, 'w', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(['corpus', 'field', 'year', 'n_articles', 'n_pvalues', 'n_negative_skipped'])
            w.writerows(sorted(rows_arts))

    with Pool(a.procs) as pool:
        for corpus, field, year, counts, n_art, n_p, n_neg in pool.imap_unordered(scan_one, jobs):
            done += 1
            if counts is None:
                print(f'[{time.time() - t0:6.0f}s] {corpus} {field} {year}: 파일 없음', flush=True)
                continue
            for b in range(1, NUM_BINS + 1):
                c = counts.get(b, {'lt': 0, 'eq': 0, 'gt': 0, 'other': 0})
                rows_bins.append([corpus, field, year, b, c['lt'], c['eq'], c['gt'], c['other']])
            rows_arts.append([corpus, field, year, n_art, n_p, n_neg])
            print(f'[{time.time() - t0:6.0f}s] {done}/{len(jobs)} {corpus} {field} {year}: articles={n_art:,} pvalues={n_p:,}', flush=True)
            if done % 20 == 0:
                save()
    save()
    print(f'done in {(time.time() - t0) / 60:.1f} min -> {bins_path}', flush=True)


if __name__ == '__main__':
    main()
