"""A14 4단계 — Figure 4와 보충 그림(RCT) 통합 이미지: Excel 차트 2개씩을 Excel에서 그대로 내보내 가로로 나란히 붙인다
(2026-10-02 오후: 4패널 Figure 4를 전체 2패널 + RCT 2패널(보충)로 나눴다. 이전 판은 out/_superseded_4panel_Figure4/)

절차
  1) Figure 4 워크북을 Excel로 열어 시트마다 차트를 벡터 PDF로 복사해 저장한다(우클릭 '그림으로 저장'과 같은 결과).
  2) PDF를 고해상 PNG로 바꾼다.
  3) 2장을 가로로 붙이고 왼쪽 위에 A, B 라벨을 단다.
Excel이 워크북을 연 뒤 저장 없이 닫는다. 이미 열려 있던 다른 문서는 건드리지 않는다.

입력  out/Figure4_distribution_PMC_fulltexts.xlsx, out/eFigure_distribution_PMC_fulltexts_RCT.xlsx  (a14_make_figure4.py 산출)
출력  out/excel_charts/panel_A.pdf, panel_B.pdf (+png)            Figure 4 패널(벡터 PDF 포함)
      out/Figure4.png                                             Figure 4 통합 이미지
      out/excel_charts_RCT/panel_A.pdf, panel_B.pdf (+png)        보충 그림(RCT) 패널
      out/eFigure_distribution_PMC_fulltexts_RCT.png              보충 그림(RCT) 통합 이미지

실행  python3.11 a14_export_figure4_from_excel.py     (Microsoft Excel 필요, macOS)
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
from xlsx_template_clone import _applescript, _excel_chart_to_pdf  # noqa: E402  (기존 Excel 내보내기 도구)

JOBS = [  # (워크북, 패널 폴더, 통합 이미지, [(패널, 시트)])
    (HERE / 'out' / 'Figure4_distribution_PMC_fulltexts.xlsx', HERE / 'out' / 'excel_charts', HERE / 'out' / 'Figure4.png',
     [('A', 'A_All_1990_2015'), ('B', 'B_All_2016_2025')]),
    (HERE / 'out' / 'eFigure_distribution_PMC_fulltexts_RCT.xlsx', HERE / 'out' / 'excel_charts_RCT',
     HERE / 'out' / 'eFigure_distribution_PMC_fulltexts_RCT.png', [('A', 'A_RCT_1990_2015'), ('B', 'B_RCT_2016_2025')]),
]
PANEL_WIDTH = 2600        # 패널 한 장의 가로 픽셀


def export(XLSX, PANEL_DIR, OUT_PNG, PANELS):
    if PANEL_DIR.exists():
        shutil.rmtree(PANEL_DIR)
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    name = XLSX.name
    already_open = _applescript(f'tell application "Microsoft Excel" to exists workbook "{name}"').stdout.strip() == 'true'
    _applescript(f'tell application "Microsoft Excel" to if not (exists workbook "{name}") then open POSIX file "{XLSX}"')
    try:
        for letter, sheet in PANELS:
            pdf = PANEL_DIR / f'panel_{letter}.pdf'
            _excel_chart_to_pdf(str(XLSX), sheet, 1, str(pdf), open_wb=False, close_wb=False)
            subprocess.run(['qlmanage', '-t', '-s', str(PANEL_WIDTH), '-o', str(PANEL_DIR), str(pdf)],
                           check=True, capture_output=True, timeout=120)
            shutil.move(str(PANEL_DIR / (pdf.name + '.png')), str(PANEL_DIR / f'panel_{letter}.png'))
            print('exported', letter, sheet)
    finally:
        if not already_open:
            _applescript(f'tell application "Microsoft Excel" to close workbook "{name}" saving no')

    # 가로로 나란히 붙이기
    imgs = [Image.open(PANEL_DIR / f'panel_{l}.png').convert('RGB') for l, _ in PANELS]
    w = max(im.width for im in imgs)
    h = max(im.height for im in imgs)
    pad = 40
    sheet = Image.new('RGB', (len(imgs) * w + (len(imgs) + 1) * pad, h + 2 * pad), 'white')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 96)
    for k, (im, (letter, _)) in enumerate(zip(imgs, PANELS)):
        x = pad + k * (w + pad)
        y = pad
        sheet.paste(im, (x, y))
        draw.text((x + 12, y + 4), letter, fill='black', font=font)
    sheet.save(OUT_PNG, dpi=(600, 600))
    print('saved', OUT_PNG, sheet.size)


def main():
    for job in JOBS:
        export(*job)


if __name__ == '__main__':
    main()
