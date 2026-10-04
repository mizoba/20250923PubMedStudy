"""A2 보충 표 — 2016 전후 연간 변화(기울기) 표 (보충자료 eTable 8)

a2_slopes.py 가 만든 연도별 비율(out/series.csv)에 같은 구간 선형회귀를 다시 적합해 표로 만든다.
  모형   y_t = b0 + b1*(t-2015) + b2*post + b3*(t-2015)*post,   post = 1 (t >= 2016)
  보고   1990-2015 기울기 b1,  2016-2025 기울기 b1+b3,  차 b3.  단위: 퍼센트포인트/년. 각 95% CI.
  제외   분모가 50 미만인 연도(a2_slopes.py 와 같은 규칙, series.csv 의 den 열로 다시 적용)
a2_slopes.py 와 다른 점은 둘: (1) 절단 연도가 2015다(a2_slopes.py 는 2016). (2) 뒤 구간 기울기의 CI도 나머지 둘과 같이 t 분포로 계산한다(원 스크립트는 1.96 고정).
대상: 본문 Figure 3과 같은 두 계열(전체 논문, RCT) × 3개 코퍼스 × 4개 지표 = 24행.

출력  out/A2_eTable_slopes.xlsx (시트 'eTable' = 보충자료에 들어가는 표, 시트 'numbers' = 반올림 전 숫자), out/A2_eTable_slopes.md
실행  python3.11 a2_etable.py
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
BREAK, MIN_N = 2015, 50          # 구간: 1990-2015, 2016-2025

MEASURES = [  # (series.csv 의 metric, 표에 쓸 이름): 본문 Figure 3의 패널 A-D 순서
    ('M1 % articles reporting P', 'Articles reporting at least 1 P-value'),
    ('M3 % articles with >=1 P<=.05', 'Articles with at least 1 P-value of .05 or less'),
    ('M4 % articles with >=1 P<=.005', 'Articles with at least 1 P-value of .005 or less'),
    ('M2 % exact (=) among P reports', 'Exact(‘=’) P-value reports'),
]
CORPORA = ['PubMed abstracts', 'PMC abstracts', 'PMC full-texts']
GROUPS = [('all', 'All articles'), ('RCT', 'Randomized controlled trials')]


def fit(d):
    d = d[(d.den >= MIN_N) & d.pct.notna()]
    t = (d.year - BREAK).values.astype(float)
    post = (d.year > BREAK).values.astype(float)
    m = sm.OLS(d.pct.values, sm.add_constant(np.column_stack([t, post, t * post]))).fit()
    out = {'first_year': int(d.year.min()), 'n_years': len(d)}
    for name, contrast in (('pre', [0, 1, 0, 0]), ('post', [0, 1, 0, 1]), ('diff', [0, 0, 0, 1])):
        tt = m.t_test(np.array(contrast))
        lo, hi = tt.conf_int(alpha=0.05)[0]
        out.update({name: float(tt.effect[0]), name + '_lo': float(lo), name + '_hi': float(hi)})
    return out


def cell(v, lo, hi):
    f = lambda x: ('0.00' if abs(x) < 0.005 else f'{x:.2f}').replace('-', '−')      # 음수 부호는 − (U+2212). −0.00 은 0.00 으로
    return f'{f(v)} ({f(lo)} to {f(hi)})'


def main():
    s = pd.read_csv(os.path.join(OUT, 'series.csv'))
    nums, table = [], [['Measure', 'Corpus', 'Articles', 'Years analyzed, No.', '1990-2015', '2016-2025', 'Difference']]
    for metric, label in MEASURES:
        for corpus in CORPORA:
            for sub, group in GROUPS:
                r = fit(s[(s.metric == metric) & (s.corpus == corpus) & (s['sub'] == sub)])
                nums.append(dict(measure=label, corpus=corpus, group=group, **r))
                table.append([label, corpus, group, str(r['n_years']),
                              cell(r['pre'], r['pre_lo'], r['pre_hi']), cell(r['post'], r['post_lo'], r['post_hi']),
                              cell(r['diff'], r['diff_lo'], r['diff_hi'])])
    with pd.ExcelWriter(os.path.join(OUT, 'A2_eTable_slopes.xlsx')) as xw:
        pd.DataFrame(table[1:], columns=table[0]).to_excel(xw, sheet_name='eTable', index=False)
        pd.DataFrame(nums).to_excel(xw, sheet_name='numbers', index=False)
    with open(os.path.join(OUT, 'A2_eTable_slopes.md'), 'w', encoding='utf-8') as f:
        f.write('| ' + ' | '.join(table[0]) + ' |\n|' + '---|' * len(table[0]) + '\n')
        for row in table[1:]:
            f.write('| ' + ' | '.join(row) + ' |\n')
    for row in table:
        print(' | '.join(row))


if __name__ == '__main__':
    main()
