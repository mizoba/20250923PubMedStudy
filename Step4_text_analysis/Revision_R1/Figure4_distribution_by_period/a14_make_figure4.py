"""A14 2단계 — Figure 4와 보충 그림(RCT) 워크북 만들기 (데이터 표 + Excel 차트)

PMC full-texts의 P-value 분포를 2016년 ASA 성명 전후로 나눠 본다.
본문 Figure 4는 전체 논문 2패널만 남기고, RCT 2패널은 보충자료 그림으로 옮긴다.
  Figure 4 (본문)        A  All PMC full-texts, 1990-2015      B  All PMC full-texts, 2016-2025
  보충 그림 (RCT)        A  Randomized controlled trials, 1990-2015   B  Randomized controlled trials, 2016-2025
  4패널이던 이전 판(스크립트, 워크북, 그림)은 out/_superseded_4panel_Figure4/ 에 있다. 숫자와 차트 양식은 그대로다.

입력  out/bins_by_year.csv, out/articles_by_year.csv   (a14_scan_distribution.py 산출)
출력  out/Figure4_distribution_PMC_fulltexts.xlsx              시트 2개, 시트마다 데이터 표(A1:F53)와 차트 1개
      out/eFigure_distribution_PMC_fulltexts_RCT.xlsx          시트 2개(RCT)

차트 양식
  제출본 Figure 2를 만든 Step4_text_analysis/Figure2/Fig2_Distribution_body_pmc.xlsx 의 차트 XML을 그대로 옮겨 쓴다
  (색, 글꼴, 막대 간격, 축 제목이 제출본과 같아진다). RCT 패널은 그 파일의 RCT 차트, 전체 패널은 All 차트가 바탕이다.
  바꾸는 것은 데이터, 차트 제목, y축 단위(×10^n)와 눈금 간격뿐이다.

데이터 표 열
  A  x축 라벨(.001, .01, ..., .05, 마지막 '>'는 P > .05 구간)
  B  '<' 로 보고된 P-value 수   C  '=' 로 보고된 수   D  '>' 로 보고된 수   E  other   F  합계
  53행  'total article N total pvalue M' (원본 시트와 같은 형식)
"""
import csv
import math
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
from xlsx_template_clone import XlsxTemplate  # noqa: E402  (기존 차트 이식 도구)

TEMPLATE = os.path.normpath(os.path.join(HERE, '..', '..', 'Figure2', 'Fig2_Distribution_body_pmc.xlsx'))
OUT = os.path.join(HERE, 'out')

PERIODS = {'1990-2015': (1990, 2015), '2016-2025': (2016, 2025)}
SETS = {  # 파일 이름 -> 패널 목록 (패널, 분야, 기간, 새 시트 이름, 템플릿에서 빌려 쓸 시트, 바탕 차트가 있는 시트, 제목 앞부분)
    'Figure4_distribution_PMC_fulltexts.xlsx': [
        ('A', 'all', '1990-2015', 'A_All_1990_2015', 'all_articles', 'all_articles', 'All PMC full-texts, 1990-2015'),
        ('B', 'all', '2016-2025', 'B_All_2016_2025', 'review', 'all_articles', 'All PMC full-texts, 2016-2025'),
    ],
    'eFigure_distribution_PMC_fulltexts_RCT.xlsx': [
        ('A', 'rct', '1990-2015', 'A_RCT_1990_2015', 'randomized_controlled_trial', 'randomized_controlled_trial',
         'Randomized controlled trials, 1990-2015'),
        ('B', 'rct', '2016-2025', 'B_RCT_2016_2025', 'meta_analysis', 'randomized_controlled_trial',
         'Randomized controlled trials, 2016-2025'),
    ],
}
# x축 라벨. 마지막 구간(P > .05)의 라벨은 제출본에서 '<'였으나 '>'로 바꿨다.
AXIS_LABELS = {2: '.001', 11: '.01', 21: '.02', 31: '.03', 41: '.04', 51: '.05', 52: '>'}
SUPERSCRIPT = str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')


def thin(n):
    """12345 -> '12 345' (제출본 그림 제목과 같은 자릿수 표기)."""
    return f'{n:,}'.replace(',', ' ')


def load_period_counts():
    """{(field, period): {'bins': [[lt, eq, gt, other] x 51], 'articles': n, 'pvalues': m}}"""
    out = {(f, p): {'bins': [[0, 0, 0, 0] for _ in range(51)], 'articles': 0, 'pvalues': 0}
           for f in ('rct', 'all') for p in PERIODS}
    with open(os.path.join(OUT, 'bins_by_year.csv')) as fh:
        for r in csv.DictReader(fh):
            for p, (y0, y1) in PERIODS.items():
                if y0 <= int(r['year']) <= y1:
                    b = out[(r['field'], p)]['bins'][int(r['bin']) - 1]
                    for i, k in enumerate(('lt', 'eq', 'gt', 'other')):
                        b[i] += int(r[k])
    with open(os.path.join(OUT, 'articles_by_year.csv')) as fh:
        for r in csv.DictReader(fh):
            for p, (y0, y1) in PERIODS.items():
                if y0 <= int(r['year']) <= y1:
                    out[(r['field'], p)]['articles'] += int(r['n_articles'])
                    out[(r['field'], p)]['pvalues'] += int(r['n_pvalues'])
    return out


def axis_unit(max_bar):
    """막대 최댓값에 맞춘 y축 표시 단위(10^e)와 눈금 간격."""
    e = int(math.floor(math.log10(max_bar)))
    m = max_bar / 10 ** e
    step = 0.5 if m <= 2 else (1 if m <= 5 else 2)
    return e, step * 10 ** e


def retarget_chart(xml, old_sheet, new_sheet):
    return xml.replace(f"'{old_sheet}'!", f'{new_sheet}!').replace(f'{old_sheet}!', f'{new_sheet}!')


def set_series_cache(xml, columns):
    """차트 안에 저장된 값 캐시(numCache)를 새 데이터로 바꾼다. columns = [lt 값들, eq 값들, gt 값들]."""
    sers = list(re.finditer(r'<c:ser>.*?</c:ser>', xml, re.S))
    assert len(sers) == 3, len(sers)
    for ser, vals in reversed(list(zip(sers, columns))):
        block = ser.group(0)
        v = re.search(r'(<c:val>.*?<c:numCache>)(.*?)(</c:numCache>)', block, re.S)
        fmt = re.search(r'<c:formatCode>[^<]*</c:formatCode>', v.group(2))
        cache = (fmt.group(0) if fmt else '') + f'<c:ptCount val="{len(vals)}"/>' + ''.join(
            f'<c:pt idx="{i}"><c:v>{x}</c:v></c:pt>' for i, x in enumerate(vals))
        block = block[:v.start(2)] + cache + block[v.end(2):]
        xml = xml[:ser.start()] + block + xml[ser.end():]
    return xml


def set_title(xml, text):
    """제목 첫 run을 바꾼다. 뒤의 run 두 개(기울임 'P ' 와 'values)')는 템플릿 그대로 둔다."""
    t = re.search(r'<c:title>.*?</c:title>', xml, re.S)
    runs = re.findall(r'<a:t>([^<]*)</a:t>', t.group(0))
    if len(runs) > 1 and runs[1].startswith(' '):      # 다음 run이 공백으로 시작하면(RCT 템플릿) 공백이 겹치지 않게 한다
        text = text.rstrip()
    block = re.sub(r'<a:t>[^<]*</a:t>', f'<a:t>{text}</a:t>', t.group(0), count=1)
    block = block.replace('sz="1500"', f'sz="{TITLE_SIZE}"')     # 제목이 한 줄에 들어가도록 글자 크기를 줄인다
    return xml[:t.start()] + block + xml[t.end():]


def set_value_axis(xml, exponent, major_unit):
    """y축: 표시 단위 10^exponent, 눈금 간격, 축 제목의 지수."""
    a0, a1 = xml.index('<c:valAx>'), xml.index('</c:valAx>')
    ax = xml[a0:a1]
    ax = re.sub(r'<c:majorUnit val="[^"]+"/>', f'<c:majorUnit val="{major_unit:g}"/>', ax)
    ax = re.sub(r'<c:dispUnits>.*?</c:dispUnits>', f'<c:dispUnits><c:custUnit val="{10 ** exponent}"/></c:dispUnits>',
                ax, flags=re.S)
    title = re.search(r'<c:title>.*?</c:title>', ax, re.S)
    runs = list(re.finditer(r'<a:t>([^<]*)</a:t>', title.group(0)))
    last = runs[-1]
    # RCT 템플릿은 지수를 위첨자 문자(⁵)로, All 템플릿은 숫자(6)에 위첨자 서식으로 적는다.
    new_exp = str(exponent).translate(SUPERSCRIPT) if last.group(1) in '⁰¹²³⁴⁵⁶⁷⁸⁹' else str(exponent)
    tb = title.group(0)
    tb = tb[:last.start(1)] + new_exp + tb[last.end(1):]
    ax = ax[:title.start()] + tb + ax[title.end():]
    return xml[:a0] + ax + xml[a1:]


# Excel 기본 범례(P<, P=, P>). 제출본 Figure 2처럼 오른쪽 패널(B)에만 넣는다.
# 글꼴·배경은 Figure 5 계열의 범례 사양과 같고, 위치만 막대를 가리지 않는 곳으로 잡았다.
LEGEND_XML = ('<c:legend><c:legendPos val="t"/><c:layout><c:manualLayout><c:xMode val="edge"/><c:yMode val="edge"/>'
              '<c:x val="0.70"/><c:y val="0.13"/><c:w val="0.10"/><c:h val="0.22"/>'
              '</c:manualLayout></c:layout><c:overlay val="1"/><c:spPr><a:solidFill><a:schemeClr val="bg1"/></a:solidFill>'
              '<a:ln><a:solidFill><a:schemeClr val="tx1"/></a:solidFill></a:ln></c:spPr>'
              '<c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="1400" b="0"><a:solidFill><a:schemeClr val="tx1"/>'
              '</a:solidFill></a:defRPr></a:pPr><a:endParaRPr lang="en-US"/></a:p></c:txPr></c:legend>')
LEGEND_PANEL = 'B'
TITLE_SIZE = 1300        # 차트 제목 글자 크기(1/100 pt). 제출본은 1500이나 새 제목이 길어 13pt로 줄였다


def set_series_names(xml):
    """계열 이름 캐시를 'P<', 'P=', 'P>' 로 맞춘다(전체 템플릿은 '<', '=', '>' 로 되어 있다)."""
    for old, new in (('&lt;', 'P&lt;'), ('=', 'P='), ('&gt;', 'P&gt;')):
        xml = re.sub(r'(<c:tx><c:strRef>(?:(?!</c:tx>).)*?<c:pt idx="0"><c:v>)' + re.escape(old) + r'(</c:v>)',
                     r'\1' + new + r'\2', xml, count=1, flags=re.S)
    return xml


def add_legend(xml):
    xml = re.sub(r'<c:legend>.*?</c:legend>', '', xml, flags=re.S)
    return xml.replace('</c:plotArea>', '</c:plotArea>' + LEGEND_XML, 1)


def build(out_name, PANELS, data):
    OUT_XLSX = os.path.join(OUT, out_name)
    tpl = XlsxTemplate(TEMPLATE)
    slots = {name: part for name, _rid, part in tpl.sheet_list()}
    base_chart_xml = {s: tpl.parts[tpl.chart_of_sheet(slots[s])[0]].decode('utf-8')
                      for s in ('randomized_controlled_trial', 'all_articles')}

    for panel, field, period, new_name, host_sheet, base_sheet, title in PANELS:
        d = data[(field, period)]
        part = slots[host_sheet]
        chart = tpl.chart_of_sheet(part)[0]
        bars = [b[0] + b[1] + b[2] for b in d['bins']]           # 차트에 그리는 것은 <, =, > 세 계열
        exponent, major = axis_unit(max(bars))

        # 1) 차트 XML: 바탕 차트를 가져와 새 시트를 가리키게 하고 값·제목·축을 바꾼다
        xml = retarget_chart(base_chart_xml[base_sheet], base_sheet, new_name)
        xml = set_series_cache(xml, [[b[i] for b in d['bins']] for i in range(3)])
        xml = set_title(xml, f"{title} ({thin(d['articles'])} articles, {thin(d['pvalues'])} ")
        xml = set_value_axis(xml, exponent, major)
        xml = set_series_names(xml)
        if panel == LEGEND_PANEL:
            xml = add_legend(xml)
        tpl.parts[chart] = xml.encode('utf-8')

        # 2) 데이터 표
        cells = {'A1': ('str', f'{title} (PMC full-texts), bin upper bound'),
                 'B1': ('str', 'P<'), 'C1': ('str', 'P='), 'D1': ('str', 'P>'),
                 'E1': ('str', 'other'), 'F1': ('str', 'total')}
        for k, b in enumerate(d['bins']):
            row = k + 2
            cells[f'B{row}'], cells[f'C{row}'], cells[f'D{row}'], cells[f'E{row}'] = b
            cells[f'F{row}'] = sum(b)
        for row, lab in AXIS_LABELS.items():
            cells[f'A{row}'] = ('str', lab)
        cells['A53'] = ('str', f"total article {d['articles']} total pvalue {d['pvalues']}")
        tpl.clear_cells(part, [f'{c}{r}' for c in 'ABCDEFGHIJ' for r in range(1, 56)])
        tpl.set_cells(part, cells)

        # 3) 시트 이름
        wb = tpl.parts['xl/workbook.xml'].decode('utf-8')
        tpl.parts['xl/workbook.xml'] = wb.replace(f'name="{host_sheet}"', f'name="{new_name}"').encode('utf-8')
        print(f"{panel}  {title}: articles={d['articles']:,}  P-values={d['pvalues']:,}  "
              f"max bar={max(bars):,}  axis x10^{exponent}, step {major:g}")

    keep = {p[3] for p in PANELS}
    tpl.delete_sheets([n for n, _r, _p in tpl.sheet_list() if n not in keep])
    # 시트 순서를 A, B 로
    wb = tpl.parts['xl/workbook.xml'].decode('utf-8')
    sheets = re.search(r'<sheets>(.*?)</sheets>', wb, re.S)
    items = re.findall(r'<sheet [^>]*/>', sheets.group(1))
    items.sort(key=lambda s: re.search(r'name="([^"]+)"', s).group(1))
    tpl.parts['xl/workbook.xml'] = (wb[:sheets.start(1)] + ''.join(items) + wb[sheets.end(1):]).encode('utf-8')
    # 삭제한 부품을 가리키는 관계 정리(Excel '복구' 대화상자 방지), 외부 링크 제거
    rels = tpl.parts['xl/_rels/workbook.xml.rels'].decode('utf-8')
    for m in re.finditer(r'<Relationship [^>]*Target="([^"]+)"[^>]*/>', rels):
        tgt = m.group(1)
        if not tgt.startswith('http') and ('xl/' + tgt) not in tpl.parts and 'externalLink' not in tgt:
            rels = rels.replace(m.group(0), '')
    tpl.parts['xl/_rels/workbook.xml.rels'] = rels.encode('utf-8')
    tpl.purge_external_formulas()
    tpl.strip_external_links()
    tpl.save(OUT_XLSX)
    print('saved', OUT_XLSX)


def main():
    data = load_period_counts()
    for out_name, panels in SETS.items():
        build(out_name, panels, data)


if __name__ == '__main__':
    main()
