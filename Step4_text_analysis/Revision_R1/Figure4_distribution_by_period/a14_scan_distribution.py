"""A14 1단계 — Figure 4용 P-value 분포 스캔 (PMC full-texts, 연도별)

무엇을 하나
  PMC full-text 원문(연도별 텍스트 파일, 한 줄 = 논문 1편)에서 P-value를 뽑아
  0.001 폭 구간(bin)별·연산자(<, =, >)별 개수를 '연도마다' 센다.
  연도별로 저장해 두면 1990-2015, 2016-2025 같은 기간 합산을 다시 스캔 없이 할 수 있다.

원본과의 관계
  제출본 Figure 2를 만든 Step4_text_analysis/Figure2/Fig2_pmc_body_to_pval.py 의 구간 규칙을 그대로 옮겼다.
  달라진 점은 (1) 연도 범위 1990-2025, (2) 연도별로 따로 저장, (3) 병렬 실행 세 가지뿐이다.
  P-value 검출은 원고와 같은 모듈 text_to_pval_and_oper 를 수정 없이 쓴다.

구간 규칙 (원본 그대로)
  bin 1..49 : (k-1)/1000 < p <= k/1000   (p = 0 은 bin 1)
  bin 50    : 0.049 < p <= 0.050
  bin 51    : p > 0.050
  연산자: '<', '≤', 'less than', 'of <' -> '<' / '>', '≥' -> '>' / '=', 'of' -> '=' / 그 밖 -> 'other'

출력  out/bins_by_year.csv   field, year, bin, lt, eq, gt, other
      out/articles_by_year.csv field, year, n_articles, n_pvalues, n_negative_skipped

사용  python3.11 a14_scan_distribution.py [--procs 8] [--fields rct all] [--years 1990-2025]
"""
import argparse
import csv
import math
import os
import sys
import time
from collections import defaultdict
from multiprocessing import Pool

MODULE_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'Step0_modules'))
sys.path.insert(0, MODULE_DIR)
from modules.text_to_pval_and_oper import text_to_pval_and_oper  # noqa: E402

DATA = '/Volumes/ssd4TB/20251080/result'
FIELDS = {  # 짧은 이름 -> 원자료 폴더 이름
    'rct': 'randomized-controlled-trial',
    'all': 'all-articles',
}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')

BIN_WIDTH = 0.001
NUM_BINS = 51                      # 1..50 = 0.001 폭 구간, 51 = p > 0.05
MAX_VAL = BIN_WIDTH * (NUM_BINS - 1)  # 0.05


def normalize_operator(oper):
    if oper in ('<', '≤', 'less than', 'of <'):
        return 'lt'
    if oper in ('>', '≥'):
        return 'gt'
    if oper in ('=', 'of'):
        return 'eq'
    return 'other'


def bin_of(p):
    """원본 스크립트와 같은 구간 번호(1..51). 음수는 None."""
    if p < 0:
        return None
    if p <= MAX_VAL:
        k = math.ceil(p / BIN_WIDTH)
        if k == 0:
            return 1
        if k >= NUM_BINS - 1:
            return NUM_BINS - 1
        return k
    return NUM_BINS


def scan_one(job):
    field, year = job
    folder = FIELDS[field]
    path = os.path.join(DATA, folder, f'pmcxtract_list_{folder}_{year}_body.txt')
    counts = defaultdict(lambda: {'lt': 0, 'eq': 0, 'gt': 0, 'other': 0})
    n_articles = n_pvalues = n_negative = 0
    if not os.path.exists(path):
        return field, year, None, 0, 0, 0
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
    return field, year, dict(counts), n_articles, n_pvalues, n_negative


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--procs', type=int, default=8)
    ap.add_argument('--fields', nargs='+', default=['rct', 'all'])
    ap.add_argument('--years', default='1990-2025')
    a = ap.parse_args()
    y0, y1 = (int(x) for x in a.years.split('-'))
    os.makedirs(OUT, exist_ok=True)

    jobs = [(f, y) for f in a.fields for y in range(y0, y1 + 1)]

    def size(job):  # 큰 파일부터 돌려 끝부분 대기 시간을 줄인다
        folder = FIELDS[job[0]]
        p = os.path.join(DATA, folder, f'pmcxtract_list_{folder}_{job[1]}_body.txt')
        return -os.path.getsize(p) if os.path.exists(p) else 0
    jobs.sort(key=size)

    bins_path = os.path.join(OUT, 'bins_by_year.csv')
    arts_path = os.path.join(OUT, 'articles_by_year.csv')
    t0 = time.time()
    rows_bins, rows_arts = [], []
    with Pool(a.procs) as pool:
        for field, year, counts, n_art, n_p, n_neg in pool.imap_unordered(scan_one, jobs):
            if counts is None:
                print(f'[{time.time() - t0:6.0f}s] {field} {year}: 파일 없음', flush=True)
                continue
            for b in range(1, NUM_BINS + 1):
                c = counts.get(b, {'lt': 0, 'eq': 0, 'gt': 0, 'other': 0})
                rows_bins.append([field, year, b, c['lt'], c['eq'], c['gt'], c['other']])
            rows_arts.append([field, year, n_art, n_p, n_neg])
            print(f'[{time.time() - t0:6.0f}s] {field} {year}: articles={n_art:,} pvalues={n_p:,}', flush=True)
            # 중간 저장(중단돼도 끝난 연도는 남는다)
            with open(bins_path, 'w', newline='') as fh:
                w = csv.writer(fh)
                w.writerow(['field', 'year', 'bin', 'lt', 'eq', 'gt', 'other'])
                w.writerows(sorted(rows_bins))
            with open(arts_path, 'w', newline='') as fh:
                w = csv.writer(fh)
                w.writerow(['field', 'year', 'n_articles', 'n_pvalues', 'n_negative_skipped'])
                w.writerows(sorted(rows_arts))
    print(f'done in {(time.time() - t0) / 60:.1f} min -> {bins_path}', flush=True)


if __name__ == '__main__':
    main()
