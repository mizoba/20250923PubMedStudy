"""A14 보충 — eFigure 3-5: P-value 분포, 2016-2025, 코퍼스 3개 × 카테고리 6개

보충자료 eFigure 3 (PMC full-texts), eFigure 4 (PMC abstracts), eFigure 5 (PubMed abstracts).
제출본에서는 2015-2025였다. 2016-2025로 통일한다(1990-2015를 다룬 2016년 JAMA 논문과 겹치지 않게).
2015-2025 판의 코드·데이터·그림은 20260101eFigure3/ 에 보관했다.

하는 일
  1) out/bins_by_year_all.csv (a14_scan_all_corpora.py 산출, 연도별 구간 개수)에서 2016-2025를 더한다. 제외하는 연도·값은 없다.
  2) 제출본 그림을 만든 Excel 워크북(Step4_text_analysis/Figure2/Fig2_Distribution_*.xlsx)을 복사해 양식(색·글꼴·축)은 그대로 두고
     데이터 표와 차트 값, 차트 제목만 2016-2025 값으로 바꾼다. 원본 워크북은 읽기만 한다.
  3) Excel에서 차트 6개를 내보내 3열 × 2행으로 붙인다(제출본과 같은 순서).
출력  out/eFigure{3,4,5}_<코퍼스>_2016_2025.xlsx, out/eFigure{3,4,5}_charts/, out/eFigure{3,4,5}.png,
      out/efigures_3to5_summary.csv (패널별 논문 수, P-value 수, 주요 구간 비율: 본문·범례에 쓰는 숫자)
실행  python3.11 a14_make_efigures_3to5.py            (Microsoft Excel 필요)
      python3.11 a14_make_efigures_3to5.py --no-excel  (워크북과 요약표만 만들고 그림 내보내기는 하지 않는다)
"""
import csv
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'tools'))
from xlsx_template_clone import XlsxTemplate, _applescript, _excel_chart_to_pdf  # noqa: E402
import a14_make_figure4 as f4                                                    # noqa: E402  (제목·범례·값 캐시 함수 재사용)

S4 = HERE.parent.parent / 'Figure2'
OUT = HERE / 'out'
Y0, Y1 = 2016, 2025
FIGURES = [  # (그림 번호, 스캔의 corpus 이름, 템플릿 워크북, 파일 이름 조각, 'All' 패널 이름)
    (3, 'pmc_body', 'Fig2_Distribution_body_pmc.xlsx', 'PMC_fulltexts', 'All PMC Full-texts'),
    (4, 'pmc_abs', 'Fig2_Distribution_abs_pmc.xlsx', 'PMC_abstracts', 'All PMC Abstracts'),
    (5, 'pubmed_abs', 'Fig2_Distribution_abs_pubmed.xlsx', 'PubMed_abstracts', 'All PubMed Abstracts'),
]
PANELS = [  # (스캔의 field, 템플릿 시트, 제목에 쓸 이름): 제출본 그림과 같은 순서
    ('rct', 'randomized_controlled_trial', 'Randomized controlled trial'),
    ('ct', 'clinical_trial', 'Clinical trial'),
    ('meta', 'meta_analysis', 'Meta analysis'),
    ('review', 'review', 'Review'),
    ('cuj', 'core_clinical_journal', 'Clinically Useful Journals'),
    ('all', 'all_articles', None),
]
LEGEND_SHEET = 'meta_analysis'
AXIS_LABELS = {2: '.001', 11: '.01', 21: '.02', 31: '.03', 41: '.04', 51: '.05', 52: '>'}   # 마지막 구간(P > .05) 라벨: '<'에서 '>'로
PANEL_WIDTH = 2000


def load_counts():
    """{(corpus, field): {'bins': [[lt, eq, gt, other] x 51], 'articles': n, 'pvalues': m}} for 2016-2025."""
    out = defaultdict(lambda: {'bins': [[0, 0, 0, 0] for _ in range(51)], 'articles': 0, 'pvalues': 0})
    with open(OUT / 'bins_by_year_all.csv') as fh:
        for r in csv.DictReader(fh):
            if Y0 <= int(r['year']) <= Y1:
                b = out[(r['corpus'], r['field'])]['bins'][int(r['bin']) - 1]
                for i, k in enumerate(('lt', 'eq', 'gt', 'other')):
                    b[i] += int(r[k])
    with open(OUT / 'articles_by_year_all.csv') as fh:
        for r in csv.DictReader(fh):
            if Y0 <= int(r['year']) <= Y1:
                out[(r['corpus'], r['field'])]['articles'] += int(r['n_articles'])
                out[(r['corpus'], r['field'])]['pvalues'] += int(r['n_pvalues'])
    return out


def build_workbook(no, corpus, template, stem, all_label, data, summary):
    f4.TITLE_SIZE = 1500                      # 제출본과 같은 제목 크기
    tpl = XlsxTemplate(str(S4 / template))
    slots = {name: part for name, _rid, part in tpl.sheet_list()}
    for field, sheet, label in PANELS:
        d = data[(corpus, field)]
        label = label or all_label
        part = slots[sheet]
        chart = tpl.chart_of_sheet(part)[0]
        xml = tpl.parts[chart].decode('utf-8')
        xml = f4.set_series_cache(xml, [[b[i] for b in d['bins']] for i in range(3)])
        xml = f4.set_title(xml, f"{label} ({f4.thin(d['articles'])} articles, {f4.thin(d['pvalues'])} ")
        xml = f4.set_series_names(xml)
        if sheet == LEGEND_SHEET:
            xml = f4.add_legend(xml)
        tpl.parts[chart] = xml.encode('utf-8')
        cells = {'A1': ('str', f'{label}, {Y0}-{Y1}, bin upper bound'), 'B1': ('str', 'P<'), 'C1': ('str', 'P='),
                 'D1': ('str', 'P>'), 'E1': ('str', 'other'), 'F1': ('str', 'total')}
        for k, b in enumerate(d['bins']):
            row = k + 2
            cells[f'B{row}'], cells[f'C{row}'], cells[f'D{row}'], cells[f'E{row}'] = b
            cells[f'F{row}'] = sum(b)
        for row, lab in AXIS_LABELS.items():
            cells[f'A{row}'] = ('str', lab)
        cells['A53'] = ('str', f"total article {d['articles']} total pvalue {d['pvalues']}")
        tpl.clear_cells(part, [f'{c}{r}' for c in 'ABCDEFGHIJ' for r in range(1, 56)])
        tpl.set_cells(part, cells)
        tot = sum(sum(b) for b in d['bins'])
        b1, b50, b51 = sum(d['bins'][0]), sum(d['bins'][49]), sum(d['bins'][50])
        summary.append(dict(eFigure=no, corpus=corpus, field=field, panel=label, articles=d['articles'],
                            pvalues=d['pvalues'], binned_total=tot, n_le_001=b1, n_049_050=b50, n_gt_05=b51,
                            pct_le_001=round(100 * b1 / tot, 2), pct_049_050=round(100 * b50 / tot, 2),
                            pct_gt_05=round(100 * b51 / tot, 2), ratio_05_to_001=round(b50 / b1, 3),
                            ratio_gt05_to_001=round(b51 / b1, 3)))
        print(f"eFigure {no}  {label}: {d['articles']:,} articles, {d['pvalues']:,} P-values")
    keep = {p[1] for p in PANELS}
    tpl.delete_sheets([n for n in slots if n not in keep])
    rels = tpl.parts['xl/_rels/workbook.xml.rels'].decode('utf-8')
    for m in re.finditer(r'<Relationship [^>]*Target="([^"]+)"[^>]*/>', rels):
        tgt = m.group(1)
        if not tgt.startswith('http') and ('xl/' + tgt) not in tpl.parts and 'externalLink' not in tgt:
            rels = rels.replace(m.group(0), '')
    tpl.parts['xl/_rels/workbook.xml.rels'] = rels.encode('utf-8')
    tpl.purge_external_formulas()
    tpl.strip_external_links()
    xlsx = OUT / f'eFigure{no}_{stem}_{Y0}_{Y1}.xlsx'
    tpl.save(str(xlsx))
    return xlsx


def export_and_compose(no, xlsx):
    chart_dir = OUT / f'eFigure{no}_charts'
    chart_dir.mkdir(parents=True, exist_ok=True)
    name = xlsx.name
    already = _applescript(f'tell application "Microsoft Excel" to exists workbook "{name}"').stdout.strip() == 'true'
    _applescript(f'tell application "Microsoft Excel" to if not (exists workbook "{name}") then open POSIX file "{xlsx}"')
    try:
        for k, (_field, sheet, _label) in enumerate(PANELS, 1):
            pdf = chart_dir / f'panel_{k}_{sheet}.pdf'
            _excel_chart_to_pdf(str(xlsx), sheet, 1, str(pdf), open_wb=False, close_wb=False)
            subprocess.run(['qlmanage', '-t', '-s', str(PANEL_WIDTH), '-o', str(chart_dir), str(pdf)],
                           check=True, capture_output=True, timeout=120)
            shutil.move(str(chart_dir / (pdf.name + '.png')), str(pdf.with_suffix('.png')))
    finally:
        if not already:
            _applescript(f'tell application "Microsoft Excel" to close workbook "{name}" saving no')
    imgs = [Image.open(chart_dir / f'panel_{k}_{s}.png').convert('RGB') for k, (_f, s, _l) in enumerate(PANELS, 1)]
    w, h = max(i.width for i in imgs), max(i.height for i in imgs)
    sheet = Image.new('RGB', (3 * w, 2 * h), 'white')
    for k, im in enumerate(imgs):
        sheet.paste(im, ((k % 3) * w, (k // 3) * h))
    png = OUT / f'eFigure{no}.png'
    sheet.save(png, dpi=(600, 600))
    print('saved', png, sheet.size)


def main():
    data, summary, books = load_counts(), [], []
    for no, corpus, template, stem, all_label in FIGURES:
        books.append((no, build_workbook(no, corpus, template, stem, all_label, data, summary)))
    with open(OUT / 'efigures_3to5_summary.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    if '--no-excel' not in sys.argv:
        for no, xlsx in books:
            export_and_compose(no, xlsx)


if __name__ == '__main__':
    main()
