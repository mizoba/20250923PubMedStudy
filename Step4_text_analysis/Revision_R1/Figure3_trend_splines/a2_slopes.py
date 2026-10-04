"""A2: ASA 2016 전후 구간 회귀 (ED-1, R1-G3).

지표: M1 P값 보고 논문 비율 / M2 exact(=) 보고 비율 / M3 ≥1 P≤.05 / M4 ≥1 P≤.005  (%)
코퍼스: PubMed abstracts, PMC abstracts, PMC full-texts × (all, RCT)
모형: y_t = b0 + b1*(t-2016) + b2*post + b3*(t-2016)*post,  post = 1 if t >= 2017
  보고: 전 기울기 b1, 후 기울기 b1+b3, 차 b3, 수준변화 b2 — 각 95% CI (pp/yr)
주분석: 1990-2016 vs 2017-2025, 비가중 OLS.  민감도: 등길이창 2006-2016 vs 2017-2025 / 변곡 2019 / n 가중.
제외: 분모(해당 지표의 n) < 50 인 연도 (PMC full-texts 1990-1996, Fig 3 범례 규칙).
입력(읽기 전용): Step4_text_analysis 의 Figure1 Totalsheet(M1), Figure3 xlsx(M3·M4), Figure5 xlsx(M2). 이 폴더에서 두 단계 위.
출력: out/slopes.xlsx, out/series.csv, out/A2_<metric>.png
"""
import os
import numpy as np
import pandas as pd
import openpyxl
import statsmodels.api as sm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
S4 = os.path.normpath(os.path.join(HERE, '..', '..'))          # Step4_text_analysis (the count tables of Figure1/, Figure3/, Figure5/)

CORP = {  # corpus: (Fig1 totalsheet, Fig3 xlsx, Fig5 xlsx)
    'PubMed abstracts': ('Figure1/20251128Fig1PubmedTotal/20250920Totalsheet.xlsx', 'Figure3/PubmedAbs.xlsx', 'Figure5/Fig5_Distribution_abs_pubmed.xlsx'),
    'PMC abstracts':    ('Figure1/20251128Fig1PMCabs/20250920Totalsheet.xlsx',      'Figure3/PMCabs.xlsx',    'Figure5/Fig5_Distribution_PLOTPMCabs.xlsx'),
    'PMC full-texts':   ('Figure1/20251128Fig1PMCbody/20250920Totalsheet.xlsx',     'Figure3/PMCbody.xlsx',   'Figure5/Fig5_Distribution_PLOTPMCbody.xlsx'),
}
SUB = {'all': ('ALL', 'all_articles'), 'RCT': ('RCT', 'randomized_controlled_trial'),
       'CT': ('CT', 'clinical_trial'), 'meta': ('META', 'meta_analysis'),
       'review': ('REVIEW', 'review'), 'CUJ': ('CCJ', 'core_clinical_journal')}  # 5개 카테고리 전부
MIN_N = 50
BREAK = 2016


def sheet_rows(path, sheet):
    ws = openpyxl.load_workbook(os.path.join(S4, path), read_only=True, data_only=True)[sheet]
    return {int(r[0]): r for r in ws.iter_rows(values_only=True) if r and r[0] is not None and str(r[0]).isdigit()}


def build_series():
    rows = []
    for corpus, (f1, f3, f5) in CORP.items():
        for sub, (s13, s5) in SUB.items():
            t1, t3, t5 = sheet_rows(f1, s13), sheet_rows(f3, s13), sheet_rows(f5, s5)
            for y in range(1990, 2026):
                tot, hasp1 = t1[y][1], t1[y][2]
                hasp3, p05, p005 = t3[y][2], t3[y][3], t3[y][5]
                eq, tot5 = t5[y][2], t5[y][5]
                rows += [
                    dict(corpus=corpus, sub=sub, year=y, metric='M1 % articles reporting P', num=hasp1, den=tot),
                    dict(corpus=corpus, sub=sub, year=y, metric='M2 % exact (=) among P reports', num=eq, den=tot5),
                    dict(corpus=corpus, sub=sub, year=y, metric='M3 % articles with >=1 P<=.05', num=p05, den=hasp3),
                    dict(corpus=corpus, sub=sub, year=y, metric='M4 % articles with >=1 P<=.005', num=p005, den=hasp3),
                ]
    df = pd.DataFrame(rows)
    df['den'] = pd.to_numeric(df['den'], errors='coerce'); df['num'] = pd.to_numeric(df['num'], errors='coerce')
    df['pct'] = 100 * df['num'] / df['den']
    df.loc[df['den'] < MIN_N, 'pct'] = np.nan
    return df


def segfit(d, y0, y1, brk, weighted=False):
    d = d[(d.year >= y0) & (d.year <= y1) & d.pct.notna()].copy()
    if len(d) < 8:
        return None
    t = d.year - brk; post = (d.year > brk).astype(float)
    X = sm.add_constant(np.column_stack([t, post, t * post]))
    w = d.den if weighted else None
    yv = d.pct.values
    m = (sm.WLS(yv, X, weights=d.den.values) if weighted else sm.OLS(yv, X)).fit()
    b = np.asarray(m.params); ci = np.asarray(m.conf_int()); V = np.asarray(m.cov_params())
    post_slope = b[1] + b[3]
    se = np.sqrt(V[1, 1] + V[3, 3] + 2 * V[1, 3]); tcrit = 1.96
    return dict(n_years=len(d), pre_slope=b[1], pre_lo=ci[1][0], pre_hi=ci[1][1],
                post_slope=post_slope, post_lo=post_slope - tcrit * se, post_hi=post_slope + tcrit * se,
                diff=b[3], diff_lo=ci[3][0], diff_hi=ci[3][1], level=b[2], level_lo=ci[2][0], level_hi=ci[2][1],
                fitted=(d.year.values, np.asarray(m.fittedvalues)))


def main():
    df = build_series(); df.to_csv(os.path.join(OUT, 'series.csv'), index=False)
    specs = [('primary 1990-2016 vs 2017-2025', 1990, 2025, 2016, False),
             ('sens A equal windows 2006-2016 vs 2017-2025', 2006, 2025, 2016, False),
             ('sens B break 2019 (1990-2019 vs 2020-2025)', 1990, 2025, 2019, False),
             ('sens C weighted by n, 1990-2016 vs 2017-2025', 1990, 2025, 2016, True)]
    res, fits = [], {}
    for (corpus, sub, metric), d in df.groupby(['corpus', 'sub', 'metric']):
        for name, y0, y1, brk, w in specs:
            r = segfit(d, y0, y1, brk, w)
            if r is None:
                continue
            if name.startswith('primary'):
                fits[(corpus, sub, metric)] = r['fitted']
            res.append(dict(corpus=corpus, subset=sub, metric=metric, spec=name, **{k: v for k, v in r.items() if k != 'fitted'}))
    out = pd.DataFrame(res)
    cols = ['corpus', 'subset', 'metric', 'spec', 'n_years', 'pre_slope', 'pre_lo', 'pre_hi', 'post_slope', 'post_lo', 'post_hi', 'diff', 'diff_lo', 'diff_hi', 'level', 'level_lo', 'level_hi']
    out = out[cols].round(3)
    with pd.ExcelWriter(os.path.join(OUT, 'slopes.xlsx')) as xw:
        out.to_excel(xw, sheet_name='all_specs', index=False)
        out[out.spec.str.startswith('primary')].to_excel(xw, sheet_name='primary', index=False)
        df.pivot_table(index='year', columns=['metric', 'corpus', 'sub'], values='pct').round(2).to_excel(xw, sheet_name='series')
    # 그림: 지표별 1장, 코퍼스 3패널, all(실선)+RCT(점선), 주분석 적합선
    for metric in sorted(df.metric.unique()):
        fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), sharey=False)
        for ax, corpus in zip(axes, CORP):
            for sub, ls in (('all', '-'), ('RCT', ':')):
                d = df[(df.corpus == corpus) & (df["sub"] == sub) & (df.metric == metric)]
                ax.plot(d.year, d.pct, ls, marker='o', ms=3, lw=1, label=f'{sub} observed')
                f = fits.get((corpus, sub, metric))
                if f is not None:
                    yrs, fv = f; pre = yrs <= BREAK
                    ax.plot(yrs[pre], fv[pre], ls, color='k', lw=1.5); ax.plot(yrs[~pre], fv[~pre], ls, color='r', lw=1.5)
            ax.axvline(BREAK + 0.5, color='gray', lw=0.8, ls='--'); ax.set_title(corpus, fontsize=10); ax.set_xlabel('Year')
        axes[0].set_ylabel(metric); axes[0].legend(fontsize=7)
        fig.suptitle(f'{metric}: segmented fit 1990-2016 (black) vs 2017-2025 (red); solid=all, dotted=RCT', fontsize=10)
        fig.tight_layout(); fig.savefig(os.path.join(OUT, f'A2_{metric[:2]}.png'), dpi=150); plt.close(fig)
    p = out[out.spec.str.startswith('primary')]
    print(p.to_string(index=False))


if __name__ == '__main__':
    main()
