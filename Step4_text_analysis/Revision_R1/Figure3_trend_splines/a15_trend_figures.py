"""A15 — Figure 3과 보충 그림 5개: 1990-2025 추세와 2016년 이후 변화 (4개 지표)

전체 논문과 무작위 대조 시험(RCT)은 따로 그린다(그림 하나에 집단 하나).
  본문에는 PubMed 초록·전체 논문 그림만 남기고, 나머지 5개(전체: PMC 초록, PMC 전문 / RCT: PubMed 초록, PMC 초록, PMC 전문)는 보충자료에 둔다.
  겹쳐 그린 이전 판과 그때의 스크립트는 out/_superseded_all_and_RCT_in_one_plot/ 에 있다.

패널 구성
  A  P-value를 1개 이상 보고한 논문 비율                      (분석 기록의 M1)
  B  P-value 보고 논문 중 P <= .05 가 1개 이상인 비율          (M3)
  C  P-value 보고 논문 중 P <= .005 가 1개 이상인 비율         (M4)
  D  보고된 P-value 중 등호(=)로 적힌 것의 비율. 제목 'Exact(‘=’) P-value reports'   (M2)
  A-C는 앞선 Figure 1, 2와 같은 순서이고 등호 비율이 마지막이다.

그림 6개 (코퍼스 3 × 집단 2. 그림 하나에 집단 하나)
  Figure3_PubMed_abstracts_all.png/.pdf        본문 Figure 3
  eFigure_trends_PMC_abstracts_all.png          보충
  eFigure_trends_PMC_fulltexts_all.png          보충
  eFigure_trends_PubMed_abstracts_RCT.png       보충
  eFigure_trends_PMC_abstracts_RCT.png          보충
  eFigure_trends_PMC_fulltexts_RCT.png          보충

그리는 것
  점 = 연도별 관측값(그 그림의 집단 하나)
  선 = 자연 3차 스플라인 적합(매듭 1996, 2006, 2016, 2021. 자료 범위 밖 매듭은 제외), 띠 = 95% 신뢰구간
  세로 점선 = 2016 ASA 성명, 2017-2018 "Redefine statistical significance", 2019 "Retire statistical significance"
             (그림 안에는 연도만 적고, 무엇인지는 원고의 figure legend에 적는다)

입력  out/series.csv  (같은 폴더의 a2_slopes.py 가 Step4 xlsx에서 만든 연도별 분자·분모·비율. 분모 50 미만 연도는 비율이 비어 있다)
적합 방법은 a3_splines.py 와 같다(같은 매듭, 같은 모형). LOWESS 선은 뺐다.
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from patsy import dmatrix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
SERIES = os.path.join(OUT, 'series.csv')          # written by a2_slopes.py
KNOTS = [1996, 2006, 2016, 2021]
EVENTS = [(2016, '2016'), (2017.5, '2017-2018'), (2019, '2019')]   # 라벨은 연도만, 내용은 그림 설명(legend)에 적는다

# y축 제목(2026-10-02 수정): 예전에는 y축에 분모를 적었다('Articles reporting P-values, %' 등). 그러면 패널 B·C의 y축이
# 'P-value를 보고한 논문의 비율'(패널 A의 지표)로 읽힌다. y축은 재는 값만 적고('Proportion, %'), 무엇의 비율인지는 패널 제목이,
# 분모가 무엇인지는 그림 설명(legend)이 말한다.
YLABEL = 'Proportion, %'
PANELS = [  # (패널, series.csv 의 metric 이름, 패널 제목. {unit} 자리에 코퍼스에 맞는 단위가 들어간다)
    ('A', 'M1 % articles reporting P', '{unit} reporting at least 1 P-value'),
    ('B', 'M3 % articles with >=1 P<=.05', '{unit} with at least 1 P-value of .05 or less'),
    ('C', 'M4 % articles with >=1 P<=.005', '{unit} with at least 1 P-value of .005 or less'),
    ('D', 'M2 % exact (=) among P reports', 'Exact(‘=’) P-value reports'),
]
FIGURES = [  # (코퍼스, 집단, 파일 이름, 패널 제목에 쓸 단위: 그림 설명의 낱말과 같게 한다)
    ('PubMed abstracts', 'all', 'Figure3_PubMed_abstracts_all', 'Abstracts'),
    ('PMC abstracts', 'all', 'eFigure_trends_PMC_abstracts_all', 'Abstracts'),
    ('PMC full-texts', 'all', 'eFigure_trends_PMC_fulltexts_all', 'Full-texts'),
    ('PubMed abstracts', 'RCT', 'eFigure_trends_PubMed_abstracts_RCT', 'Abstracts'),
    ('PMC abstracts', 'RCT', 'eFigure_trends_PMC_abstracts_RCT', 'Abstracts'),
    ('PMC full-texts', 'RCT', 'eFigure_trends_PMC_fulltexts_RCT', 'Full-texts'),
]
STYLE = {  # 집단별 모양: 색, 점 모양(겹쳐 그리던 판과 같은 색·점 모양을 쓴다. 선은 둘 다 실선)
    'all': dict(color='#2B4B5C', marker='o', ls='-'),
    'RCT': dict(color='#C0612B', marker='^', ls='-'),
}


def spline_fit(d):
    """자연 3차 스플라인 적합값과 95% 신뢰구간(0.25년 간격)."""
    kn = [k for k in KNOTS if d.year.min() < k < d.year.max()]
    X = dmatrix('cr(year, knots=kn)', {'year': d.year, 'kn': kn}, return_type='dataframe')
    model = sm.OLS(d.pct.values, X).fit()
    grid = np.arange(d.year.min(), 2025.01, 0.25)
    Xg = dmatrix('cr(year, knots=kn)', {'year': grid, 'kn': kn}, return_type='dataframe')
    pred = model.get_prediction(Xg).summary_frame(alpha=0.05)
    return grid, pred['mean'].values, pred['mean_ci_lower'].values, pred['mean_ci_upper'].values


def draw(df, corpus, sub, stem, unit, fits):
    plt.rcParams.update({'font.family': 'Arial', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                         'pdf.fonttype': 42})          # keep text as text in the PDF (editable), not as glyph outlines
    fig, axes = plt.subplots(2, 2, figsize=(9.5, 7.2))
    for ax, (panel, metric, title) in zip(axes.flat, PANELS):
        for sub in (sub,):                               # 그림 하나에 집단 하나
            d = df[(df.corpus == corpus) & (df['sub'] == sub) & (df.metric == metric) & df.pct.notna()]
            if len(d) < 8:
                continue
            st = STYLE[sub]
            grid, mean, lo, hi = spline_fit(d)
            ax.fill_between(grid, lo, hi, color=st['color'], alpha=0.15, lw=0)
            ax.plot(grid, mean, st['ls'], color=st['color'], lw=1.6)
            ax.plot(d.year, d.pct, linestyle='none', marker=st['marker'], ms=3.6, color=st['color'],
                    mfc='white', mew=0.9)
            for yr, fv, a, b in zip(grid, mean, lo, hi):
                if abs(yr - round(yr)) < 1e-9:
                    fits.append(dict(corpus=corpus, panel=panel, metric=metric, series=sub, year=int(round(yr)),
                                     spline=round(float(fv), 3), ci_low=round(float(a), 3), ci_high=round(float(b), 3)))
        y0, y1 = ax.get_ylim()
        ax.set_ylim(y0, y1 + (y1 - y0) * 0.20)          # 연도 라벨 자리
        for x, lab in EVENTS:
            ax.axvline(x, color='0.45', lw=0.8, ls=':')
            ax.text(x - 0.2, ax.get_ylim()[1], lab, fontsize=6.5, rotation=90, va='top', ha='right', color='0.3')
        ax.set_title(title.format(unit=unit), fontsize=10, loc='left', pad=14)
        ax.text(-0.13, 1.09, panel, transform=ax.transAxes, fontsize=13, fontweight='bold', va='bottom')
        ax.set_xlabel('Year of publication')
        ax.set_ylabel(YLABEL)
        ax.set_xlim(1989, 2026)
        ax.set_xticks(range(1990, 2026, 5))
    fig.tight_layout(h_pad=2.2, w_pad=2.0)            # 집단이 하나라 범례는 두지 않는다(무엇의 그림인지는 그림 설명에 적는다)
    fig.savefig(os.path.join(OUT, stem + '.png'), dpi=300)
    fig.savefig(os.path.join(OUT, stem + '.pdf'))
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    df = pd.read_csv(SERIES)
    fits = []
    for corpus, sub, stem, unit in FIGURES:
        draw(df, corpus, sub, stem, unit, fits)
        print('saved', stem)
    pd.DataFrame(fits).to_csv(os.path.join(OUT, 'spline_fits_by_panel.csv'), index=False)
    # 그림에 쓰인 관측값도 함께 저장(검토용)
    keep = df[df.metric.isin([p[1] for p in PANELS])].copy()
    keep['panel'] = keep.metric.map({p[1]: p[0] for p in PANELS})
    keep.sort_values(['corpus', 'panel', 'sub', 'year']).to_csv(os.path.join(OUT, 'observed_by_panel.csv'), index=False)


if __name__ == '__main__':
    main()
