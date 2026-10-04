#!/usr/bin/env python3
"""원본 연구 엑셀의 차트 스타일을 '바이트 그대로' 물려받기 위한 ZIP 수준 복제 도구.

원리: xlsx 를 압축 해제하지 않고 part 단위로 다루면서
  - chart XML(선·색·마커·범례·축), theme1.xml, drawing XML, 시트 포맷은 그대로 두고
  - 바꾸는 것은 ① 시트 이름 ② 셀 값 ③ 차트 제목의 텍스트 런 ④ 미사용 시트 삭제 뿐.
따라서 Excel 이 차트를 렌더링할 때 참조하는 요소가 원본과 동일하다.
"""
import re, shutil, zipfile
from collections import OrderedDict


class XlsxTemplate:
    def __init__(self, path):
        self.parts = OrderedDict()
        with zipfile.ZipFile(path) as z:
            for info in z.infolist():
                self.parts[info.filename] = z.read(info.filename)

    # ---------- 구조 파악 ----------
    def sheet_list(self):
        """[(display_name, rId, sheet_part)] (workbook.xml 순서)."""
        wb = self.parts["xl/workbook.xml"].decode("utf-8")
        rels = self.parts["xl/_rels/workbook.xml.rels"].decode("utf-8")
        rid2tgt = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="(worksheets/[^"]+)"', rels))
        out = []
        for name, rid in re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wb):
            out.append((name, rid, "xl/" + rid2tgt[rid]))
        return out

    def _rel_targets(self, part, pattern):
        d, fn = part.rsplit("/", 1)
        rel = f"{d}/_rels/{fn}.rels"
        if rel not in self.parts:
            return []
        base = d
        out = []
        for tgt in re.findall(r'Target="([^"]+)"', self.parts[rel].decode("utf-8")):
            norm = tgt.replace("../", "xl/") if tgt.startswith("../") else f"{base}/{tgt}"
            if re.search(pattern, norm):
                out.append(norm)
        return out

    def chart_of_sheet(self, sheet_part):
        """sheet -> drawing -> chart part 경로."""
        for drawing in self._rel_targets(sheet_part, r"drawings/drawing\d+\.xml$"):
            for chart in self._rel_targets(drawing, r"charts/chart\d+\.xml$"):
                return chart, drawing
        return None, None

    # ---------- 편집 ----------
    def rename_sheet(self, old, new):
        wb = self.parts["xl/workbook.xml"].decode("utf-8")
        assert f'name="{old}"' in wb, old
        self.parts["xl/workbook.xml"] = wb.replace(f'name="{old}"', f'name="{new}"').encode()
        for p in list(self.parts):
            if re.match(r"xl/charts/chart\d+\.xml$", p):
                s = self.parts[p]
                s = s.replace(f"'{old}'!".encode(), f"'{new}'!".encode())
                s = s.replace(f"{old}!".encode(), f"{new}!".encode())
                self.parts[p] = s

    def set_cells(self, sheet_part, updates):
        """updates: {'B2': 123, 'A1': ('str','text'), ...} — 값만 교체, 서식 유지."""
        xml = self.parts[sheet_part].decode("utf-8")
        for ref, val in updates.items():
            pat = re.compile(rf'<c r="{ref}"([^>]*?)/?>(?:(?!<c ).)*?</c>|<c r="{ref}"([^>]*?)/>', re.S)
            m = re.search(rf'<c r="{ref}"([^>]*?)(/>|>.*?</c>)', xml, re.S)
            if isinstance(val, tuple) and val[0] == "str":
                inner = f'<is><t xml:space="preserve">{_esc(val[1])}</t></is>'
                attrs = _strip_t(m.group(1)) + ' t="inlineStr"' if m else ' t="inlineStr"'
            else:
                inner = f"<v>{val}</v>"
                attrs = _strip_t(m.group(1)) if m else ""
            new_c = f'<c r="{ref}"{attrs}>{inner}</c>'
            if m:
                xml = xml[:m.start()] + new_c + xml[m.end():]
            else:
                rownum = re.match(r"[A-Z]+(\d+)", ref).group(1)
                rm = re.search(rf'(<row r="{rownum}"[^>]*>)', xml)
                assert rm, f"row {rownum} not found for {ref}"
                xml = xml[:rm.end()] + new_c + xml[rm.end():]
        self.parts[sheet_part] = xml.encode()

    def set_chart_title_first_run(self, chart_part, text):
        xml = self.parts[chart_part].decode("utf-8")
        tm = re.search(r"<c:title>.*?</c:title>", xml, re.S)
        assert tm, chart_part
        block = tm.group(0)
        block2 = re.sub(r"<a:t>[^<]*</a:t>", f"<a:t>{_esc(text)}</a:t>", block, count=1)
        self.parts[chart_part] = (xml[:tm.start()] + block2 + xml[tm.end():]).encode()

    def delete_sheets(self, names):
        info = {n: (rid, part) for n, rid, part in self.sheet_list()}
        wb = self.parts["xl/workbook.xml"].decode("utf-8")
        rels = self.parts["xl/_rels/workbook.xml.rels"].decode("utf-8")
        ct = self.parts["[Content_Types].xml"].decode("utf-8")
        dead_parts = []
        for n in names:
            rid, sheet = info[n]
            chart, drawing = self.chart_of_sheet(sheet)
            chain = [sheet, f"{sheet.rsplit('/',1)[0]}/_rels/{sheet.rsplit('/',1)[1]}.rels"]
            if drawing:
                chain += [drawing, f"xl/drawings/_rels/{drawing.rsplit('/',1)[1]}.rels"]
            if chart:
                cn = chart.rsplit("/", 1)[1]
                num = re.search(r"(\d+)", cn).group(1)
                chain += [chart, f"xl/charts/_rels/{cn}.rels",
                          f"xl/charts/style{num}.xml", f"xl/charts/colors{num}.xml"]
            dead_parts += chain
            wb = re.sub(rf'<sheet name="{re.escape(n)}"[^>]*/>', "", wb)
            rels = re.sub(rf'<Relationship Id="{rid}"[^>]*/>', "", rels)
        # calcChain 은 시트 삭제 후 안전하지 않으므로 함께 제거 (Excel 이 재계산)
        dead_parts.append("xl/calcChain.xml")
        for p in dead_parts:
            self.parts.pop(p, None)
            ct = re.sub(rf'<Override PartName="/{re.escape(p)}"[^>]*/>', "", ct)
        wb = re.sub(r' activeTab="\d+"', "", wb)
        self.parts["xl/workbook.xml"] = wb.encode()
        self.parts["xl/_rels/workbook.xml.rels"] = rels.encode()
        self.parts["[Content_Types].xml"] = ct.encode()

    def save(self, path):
        tmp = path + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in self.parts.items():
                z.writestr(name, data)
        shutil.move(tmp, path)


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _strip_t(attrs):
    return re.sub(r'\s+t="[^"]*"', "", attrs or "")


# ---------- 확장: 시리즈 절단 · 외부링크 제거 · 셀 비우기 ----------
def _extend():
    import re as _re

    def keep_first_series(self, chart_part, n):
        """차트의 <c:ser> 블록을 앞에서 n개만 남기고 제거 (남는 시리즈 스타일 불변)."""
        xml = self.parts[chart_part].decode("utf-8")
        spans = [m.span() for m in _re.finditer(r"<c:ser>.*?</c:ser>", xml, _re.S)]
        for s, e in reversed(spans[n:]):
            xml = xml[:s] + xml[e:]
        self.parts[chart_part] = xml.encode()

    def strip_external_links(self):
        """외부 통합문서 링크 제거 (열 때 '링크 업데이트' 대화상자 방지).
        참조하던 수식 셀은 미리 정적 값으로 교체해 두어야 한다."""
        wb = self.parts["xl/workbook.xml"].decode("utf-8")
        wb = _re.sub(r"<externalReferences>.*?</externalReferences>", "", wb, flags=_re.S)
        self.parts["xl/workbook.xml"] = wb.encode()
        rels = self.parts["xl/_rels/workbook.xml.rels"].decode("utf-8")
        rels = _re.sub(r'<Relationship [^>]*externalLink[^>]*/>', "", rels)
        self.parts["xl/_rels/workbook.xml.rels"] = rels.encode()
        ct = self.parts["[Content_Types].xml"].decode("utf-8")
        for p in [p for p in list(self.parts) if p.startswith("xl/externalLinks/")]:
            del self.parts[p]
            ct = _re.sub(rf'<Override PartName="/{_re.escape(p)}"[^>]*/>', "", ct)
        self.parts["[Content_Types].xml"] = ct.encode()

    def clear_cells(self, sheet_part, refs):
        """지정 셀들을 빈 셀로 (수식·값 제거, 서식 attr 유지)."""
        xml = self.parts[sheet_part].decode("utf-8")
        for ref in refs:
            m = _re.search(rf'<c r="{ref}"([^>]*?)(/>|>.*?</c>)', xml, _re.S)
            if m:
                attrs = _strip_t(m.group(1))
                xml = xml[:m.start()] + f'<c r="{ref}"{attrs}/>' + xml[m.end():]
        self.parts[sheet_part] = xml.encode()

    XlsxTemplate.keep_first_series = keep_first_series
    XlsxTemplate.strip_external_links = strip_external_links
    XlsxTemplate.clear_cells = clear_cells


_extend()


def _extend2():
    import re as _re

    def purge_external_formulas(self):
        """모든 워크시트에서 외부 통합문서([n]) 참조 수식을 제거하고 캐시된 값만 남김.
        strip_external_links() 전에 호출해야 Excel 복구 경고가 안 뜬다."""
        for p in list(self.parts):
            if _re.match(r"xl/worksheets/sheet\d+\.xml$", p):
                xml = self.parts[p].decode("utf-8")
                new = _re.sub(r"<f[^>]*>[^<]*\[\d+\][^<]*</f>", "", xml)
                if new != xml:
                    self.parts[p] = new.encode()

    XlsxTemplate.purge_external_formulas = purge_external_formulas


_extend2()


# ---------- 확장3: Y축 자동조정 (2026-09-03, 랩미팅 후속) ----------
def _nice_ceil(x):
    """1/2/2.5/5×10^k 올림 (nice number)."""
    import math
    if x <= 0:
        return 1
    k = math.floor(math.log10(x))
    for m in (1, 2, 2.5, 5, 10):
        c = m * 10 ** k
        if c >= x:
            return c
    return 10 ** (k + 1)


def fix_valax_xml(xml, data_max, data_min=None, mode="line", cap=None,
                  min_val=None, anchor_frac=0.3):
    """차트 XML 문자열의 <c:valAx> Y축을 데이터 스케일에 맞게 재계산해 반환.

    mode="line": 선그래프. 축 바닥 결정 우선순위 —
      ① min_val 명시 시 그 값 (호출부가 강제)
      ② data_min 제공 시 판정규칙: data_min < anchor_frac×data_max → 0 앵커,
         아니면 절단축(unit 을 range 기준 nice 로 정하고 min/max 를 unit 배수로)
      ③ 둘 다 없으면 min=0
    mode="dist": 분포(카운트) 막대/누적 — min 은 항상 0 고정(크기 왜곡 방지),
      표시 단위·축 제목 지수(×10⁵/×10³/원값) 조정 포함.
    cap: 축 최대 상한 (% 차트 100). 반환: 수정된 XML 문자열 (valAx 없으면 원본).
    """
    import math
    import re as _re
    m = _re.search(r"<c:valAx>.*?</c:valAx>", xml, _re.S)
    if not m:
        return xml
    v = m.group(0)

    if mode == "dist":
        ax_min = 0.0
    elif min_val is not None:
        ax_min = float(min_val)
    elif data_min is not None and data_min >= anchor_frac * data_max:
        ax_min = None  # 절단축: unit 확정 후 계산
    else:
        ax_min = 0.0

    if ax_min is None:  # 절단축
        unit = _nice_ceil((data_max - data_min) / 5)
        ax_min = math.floor(data_min / unit) * unit
        ax_max = math.ceil(data_max / unit) * unit
    else:
        unit = _nice_ceil((data_max - ax_min) / 5)
        ax_max = ax_min + math.ceil((data_max - ax_min) / unit) * unit
    # 헤드룸: 데이터 최대가 축 상단에 딱 붙으면(95% 초과) 한 눈금 여유 추가
    if (data_max - ax_min) / (ax_max - ax_min) > 0.95:
        ax_max += unit
    if cap is not None and ax_max > cap:
        ax_max = cap
        unit = _nice_ceil((ax_max - ax_min) / 5)

    v = _re.sub(r"<c:scaling>.*?</c:scaling>",
                f'<c:scaling><c:orientation val="minMax"/>'
                f'<c:max val="{ax_max:g}"/><c:min val="{ax_min:g}"/></c:scaling>',
                v, flags=_re.S)
    if "<c:majorUnit" in v:
        v = _re.sub(r'<c:majorUnit val="[^"]*"/>', f'<c:majorUnit val="{unit:g}"/>', v)
    else:
        v = v.replace("</c:valAx>", f'<c:majorUnit val="{unit:g}"/></c:valAx>')

    if mode == "dist":
        if data_max >= 1e5:
            built_in, expo = "hundredThousands", "5"
        elif data_max >= 1e4:
            built_in, expo = "thousands", "3"
        else:
            built_in, expo = None, None
        if built_in:
            v = _re.sub(r"<c:dispUnits>.*?</c:dispUnits>",
                        f'<c:dispUnits><c:builtInUnit val="{built_in}"/></c:dispUnits>',
                        v, flags=_re.S)
            v = _re.sub(r"<a:t>(\d+)</a:t>", f"<a:t>{expo}</a:t>", v)
        else:
            v = _re.sub(r"<c:dispUnits>.*?</c:dispUnits>", "", v, flags=_re.S)
            v = v.replace("<a:t> Values, ×10</a:t>", "<a:t> Values</a:t>")
            v = _re.sub(r"<a:r>(?:(?!</a:r>).)*?<a:t>\d+</a:t>(?:(?!</a:r>).)*?</a:r>",
                        "", v, flags=_re.S)
    return xml[:m.start()] + v + xml[m.end():]


def _extend3():
    def fix_valax(self, chart_part, data_max, data_min=None, mode="line",
                  cap=None, min_val=None):
        """self.parts[chart_part] 의 차트 XML 에 fix_valax_xml 적용 (부수효과)."""
        xml = self.parts[chart_part].decode("utf-8")
        self.parts[chart_part] = fix_valax_xml(
            xml, data_max, data_min=data_min, mode=mode, cap=cap,
            min_val=min_val).encode()

    XlsxTemplate.fix_valax = fix_valax


_extend3()


# ---------- 확장4: Excel 차트 → 고해상 PNG (2026-09-03) ----------
# Excel 의 'save as picture' 스크립팅은 이 빌드(16.112)에서 결함(-50)이라,
# copy picture(벡터) → 클립보드 PDF → qlmanage 목표폭 렌더로 우회한다.
# 우클릭 "이미지로 저장하기"와 동급 산출물. 단일 세션 전제(Excel automation).
def _applescript(script, timeout=180):
    import subprocess
    return subprocess.run(["osascript", "-e", script], check=True,
                          timeout=timeout, capture_output=True, text=True)


def _excel_chart_to_pdf(xlsx_path, sheet_name, chart_index, pdf_path,
                        open_wb=True, close_wb=True):
    """차트 하나를 벡터 PDF 로 저장. open_wb/close_wb 로 워크북 수명 제어
    (여러 차트 연속 내보내기 시 열고 닫기를 호출부가 한 번만 하도록)."""
    from pathlib import Path
    name = Path(xlsx_path).name
    # 열 때 '연결 업데이트' 창이 뜨지 않게 한다.
    # ask to update links 와 경고 창을 잠시 끄고 연다. 끝나면 원래 설정으로 되돌린다.
    # 'open POSIX file' 로 연다: 'open workbook workbook file name' 은 처음 여는 폴더에서 '액세스 권한 부여' 창을 띄운다(2026-10-04).
    opener = (f'''if not (exists workbook "{name}") then
        set oldAsk to ask to update links
        set ask to update links to false
        set display alerts to false
        try
            open POSIX file "{xlsx_path}"
        end try
        set display alerts to true
        set ask to update links to oldAsk
    end if''' if open_wb else "")
    closer = f'close workbook "{name}" saving no' if close_wb else ""
    _applescript(f'''with timeout of 180 seconds
tell application "Microsoft Excel"
    {opener}
    copy picture (chart object {chart_index} of worksheet "{sheet_name}" of workbook "{name}") appearance printer format picture
    {closer}
end tell
end timeout
set d to the clipboard as «class PDF »
set f to open for access POSIX file "{pdf_path}" with write permission
set eof f to 0
write d to f
close access f''')


def export_chart_png(xlsx_path, sheet_name, out_png, chart_index=1, width=2600,
                     open_wb=True, close_wb=True):
    """xlsx 차트 하나를 고해상 PNG 로 저장 ('그림으로 저장하기' 우회판)."""
    import shutil
    import subprocess
    from pathlib import Path
    out_png = Path(out_png)
    tmp_pdf = out_png.with_suffix(".tmp.pdf")
    _excel_chart_to_pdf(str(Path(xlsx_path).resolve()), sheet_name, chart_index,
                        str(tmp_pdf), open_wb=open_wb, close_wb=close_wb)
    subprocess.run(["qlmanage", "-t", "-s", str(width), "-o", str(tmp_pdf.parent),
                    str(tmp_pdf)], check=True, capture_output=True, timeout=120)
    shutil.move(str(tmp_pdf.parent / (tmp_pdf.name + ".png")), str(out_png))
    tmp_pdf.unlink()


# ---------- 확장5: 범례 가림 판정 + 픽셀급 자동 이동 (2026-09-03) ----------
# figure4·figure5 에서 수동으로 하던 범례 위치 조정의 일반화판.
# 전 시리즈의 연도별 값 전체를 꺾은선 "선분"으로 잇고, 범례/플롯 사각형과 같은
# 좌표계(차트 비율)에 놓는다 — 축 min/max 는 값→위치 환산 축척으로만 쓴다.
# 범례가 선분과 겹치면 플롯 내부를 step 간격(기본 0.005 ≈ 2600px 차트에서 13px)으로
# 전수 탐색해 겹치는 선분 수가 최소인 위치로 manualLayout(x, y)만 옮긴다.
# 플롯 밖으로는 보내지 않는다(미관). 무침범이면 원위치 유지.
def fix_legend_xml(xml, n_cats, series_values, step=0.005, pad=0.03, edge=0.01, prefer_corners=True, corner_bonus=0.10):
    """반환: (수정된 xml, 이동 여부, 이동 전 침범 선분 수, 이동 후 침범 선분 수).

    pad: 범례 상자 둘레에 두는 여유(차트 폭·높이 비율)의 상한. 이 띠 안에 선분이 들어와도 침범으로
        센다. 교차 0 인 자리가 없으면 0.01 씩 줄여 재탐색(실제 사용값: fix_legend_xml.last_pad).
    edge: 플롯 영역 테두리(축선)에서 범례를 띄우는 여유.
    prefer_corners: True 면 교차가 같을 때 우상단→좌상단→우하단→좌하단 순으로 가점(corner_bonus)을
        주어 코너에 붙인다(원래 위치에 교차가 없어도 재배치). False 면 교차 있을 때만,
        원래 위치에서 가장 가까운 최소 교차 지점으로 옮긴다.
    corner_bonus: 코너 순위 한 단계당 거리 가점(차트 비율). 크게 주면 순서가 엄격해진다.
    n_cats: 카테고리(연도) 개수. series_values: 시리즈별 전 구간 값(결측은 None).
    꼭짓점이 아니라 점을 잇는 선분과 범례 사각형의 교차를 세므로, 양 끝점이 상자
    밖이어도 가로지르는 선을 잡는다(결측 구간은 선이 끊긴 것으로 처리).
    전제: fix_valax 로 valAx min/max 가 명시돼 있어야 좌표 환산이 정확하다.
    한계: XML 기하 판정이라 선 두께·마커 크기는 근사(pad 로 여유 흡수).
    """
    import re as _re

    lm = _re.search(r"<c:legend>.*?</c:legend>", xml, _re.S)
    if not lm:
        return xml, False, 0, 0
    leg = lm.group(0)

    def _val(tag, s):
        m = _re.search(rf'<c:{tag} val="([^"]+)"/>', s)
        return float(m.group(1)) if m else None

    lx, ly, lw, lh = (_val(t, leg) for t in ("x", "y", "w", "h"))
    if None in (lx, ly, lw, lh):
        return xml, False, 0, 0            # 자동배치·플롯 밖 범례 → 판정 불필요

    pm = _re.search(r"<c:plotArea><c:layout><c:manualLayout>(.*?)</c:manualLayout>",
                    xml, _re.S)
    if pm:
        px, py, pw, ph = (_val(t, pm.group(1)) for t in ("x", "y", "w", "h"))
    else:
        # 템플릿에 plotArea manualLayout 이 없을 때의 대체 사각형.
        # y 는 렌더된 템플릿 차트(격자선 픽셀)에서 실측: 상단 0.085, 높이 0.743.
        # x 는 데이터 선이 격자를 끊어 실측이 어려워 넉넉히 잡음(판정이 보수적이 됨).
        # 절대 좌표에 오차가 있어도 후보 위치 간 "상대 비교"는 같은 매핑을 쓰므로
        # 순위는 유지된다 — 최종 확인은 렌더 육안검증.
        px, py, pw, ph = 0.05, 0.085, 0.93, 0.743
    v = _re.search(r"<c:valAx>.*?</c:valAx>", xml, _re.S)
    if not v:
        return xml, False, 0, 0
    ymax = _val("max", v.group(0))
    ymin = _val("min", v.group(0))
    if ymax is None:
        return xml, False, 0, 0            # 축이 자동이면 환산 불가 → 통과
    if ymin is None:
        ymin = 0.0

    def _flush(run, out):
        """연속 구간을 선분으로 변환(bbox 동봉). 고립 점은 길이 0 선분으로 보존."""
        if len(run) == 1:
            fx, fy = run[0]
            out.append((fx, fy, fx, fy, fx, fx, fy, fy))
        else:
            for k in range(len(run) - 1):
                ax, ay = run[k]
                cx, cy = run[k + 1]
                out.append((ax, ay, cx, cy,
                            min(ax, cx), max(ax, cx), min(ay, cy), max(ay, cy)))

    segs = []
    for ys in series_values:
        run = []
        for i, val in enumerate(ys):
            if val is None:                        # 결측 → 선이 끊김
                if run:
                    _flush(run, segs)
                    run = []
                continue
            fx = px + (i + 0.5) / n_cats * pw
            fy = py + (1 - (float(val) - ymin) / (ymax - ymin)) * ph
            run.append((fx, fy))
        if run:
            _flush(run, segs)
    if not segs:
        return xml, False, 0, 0

    def _hits(seg, xa, ya, xb, yb):
        """선분–사각형 교차 (Liang–Barsky 슬랩 클리핑), bbox 로 선기각."""
        x0s, y0s, x1s, y1s, mnx, mxx, mny, mxy = seg
        if mxx < xa or mnx > xb or mxy < ya or mny > yb:
            return False
        dx, dy = x1s - x0s, y1s - y0s
        if dx == 0.0 and dy == 0.0:                # 고립 점 → bbox 로 내부 확정
            return True
        t0, t1 = 0.0, 1.0
        for pp, qq in ((-dx, x0s - xa), (dx, xb - x0s),
                       (-dy, y0s - ya), (dy, yb - y0s)):
            if pp == 0.0:
                if qq < 0.0:
                    return False                   # 슬랩과 평행하며 바깥
            else:
                r = qq / pp
                if pp < 0.0:
                    if r > t1:
                        return False
                    if r > t0:
                        t0 = r
                else:
                    if r < t0:
                        return False
                    if r < t1:
                        t1 = r
        return True

    def score(x0, y0):
        xa, ya, xb, yb = x0 - pad, y0 - pad, x0 + lw + pad, y0 + lh + pad
        return sum(1 for sg in segs if _hits(sg, xa, ya, xb, yb))

    before = score(lx, ly)
    if before == 0 and not prefer_corners:
        return xml, False, 0, 0

    # 후보 채점: 1순위 교차 선분 수(적을수록), 2순위 코너 가점을 뺀 거리.
    # 코너 가점: 우상단 > 좌상단 > 우하단 > 좌하단. 후보 사각형의 중심이
    # 속한 사분면의 코너를 그 후보의 코너로 보고, 코너까지의 거리(차트 비율, x+y)에서
    # 순위별로 corner_bonus 씩 차감한다. 즉 낮은 순위 코너는 corner_bonus 만큼 더 가까이
    # 붙어야 이긴다(플롯 한가운데 뜬 우상단 후보보다 좌상단 구석에 딱 붙은 후보가 이길 수 있다).
    # prefer_corners=False 이면 종전대로 (교차 수, 원래 위치와의 거리) 로만 고른다.
    cx0, cy0 = px + pw / 2, py + ph / 2
    x_lo, x_hi = px + edge, px + pw - lw - edge
    y_lo, y_hi = py + edge, py + ph - lh - edge
    if x_hi < x_lo or y_hi < y_lo:                 # 범례가 플롯보다 큼 → 판정 불가
        return xml, False, before, before

    def key(x0, y0, pad_now):
        xa, ya, xb, yb = x0 - pad_now, y0 - pad_now, x0 + lw + pad_now, y0 + lh + pad_now
        sc = sum(1 for sg in segs if _hits(sg, xa, ya, xb, yb))
        if not prefer_corners:
            return (sc, abs(x0 - lx) + abs(y0 - ly))
        mx, my = x0 + lw / 2, y0 + lh / 2
        right, top = mx >= cx0, my <= cy0
        rank = {(True, True): 0, (False, True): 1, (True, False): 2, (False, False): 3}[(right, top)]
        dx = (x_hi - x0) if right else (x0 - x_lo)
        dy = (y0 - y_lo) if top else (y_hi - y0)
        return (sc, dx + dy + rank * corner_bonus)

    def search(pad_now):
        best_key, bx, by = None, lx, ly
        y0 = y_lo
        while y0 <= y_hi + 1e-9:
            x0 = x_lo
            while x0 <= x_hi + 1e-9:
                k = key(x0, y0, pad_now)
                if best_key is None or k < best_key:
                    best_key, bx, by = k, x0, y0
                x0 += step
            y0 += step
        return best_key, bx, by

    # 여유(pad)는 요청값부터 시작해 교차 0 인 자리가 없으면 0.01 씩 줄여 다시 찾는다(최소 0).
    # 즉 "교차 없이 둘 수 있는 최대 여유"를 쓴다. 실제 사용한 여유는 fix_legend_xml.last_pad 에 남긴다.
    pad_now = pad
    while True:
        best_key, bx, by = search(pad_now)
        if best_key[0] == 0 or pad_now <= 0.0:
            break
        pad_now = max(0.0, round(pad_now - 0.01, 6))
    fix_legend_xml.last_pad = pad_now
    best_sc = best_key[0]
    if best_sc > before and not prefer_corners:  # 종전 모드: 더 나빠지면 그대로 둠
        return xml, False, before, before
    moved = abs(bx - lx) > 1e-9 or abs(by - ly) > 1e-9
    if not moved:
        return xml, False, before, best_sc

    leg2 = _re.sub(r'<c:x val="[^"]+"/>', f'<c:x val="{bx:.6f}"/>', leg, count=1)
    leg2 = _re.sub(r'<c:y val="[^"]+"/>', f'<c:y val="{by:.6f}"/>', leg2, count=1)
    return xml[:lm.start()] + leg2 + xml[lm.end():], True, before, best_sc
