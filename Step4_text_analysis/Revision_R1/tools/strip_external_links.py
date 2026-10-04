"""xlsx에서 다른 워크북을 가리키는 연결을 없앤다: 외부 참조 수식은 저장된 값으로 바꾸고, externalLinks 부품을 지운다.
이렇게 해 두면 Excel이 파일을 열 때 '연결 업데이트' 창을 띄우지 않는다(제출 파일을 받는 쪽에서도).
사용  python3.11 strip_external_links.py <파일.xlsx> [...]
"""
import re
import shutil
import sys
import zipfile


def strip(path):
    z = zipfile.ZipFile(path)
    parts = {i.filename: z.read(i.filename) for i in z.infolist()}
    z.close()
    n_f = 0
    for name in list(parts):
        if re.search(r'xl/worksheets/sheet\d+\.xml$', name):
            x = parts[name].decode('utf-8')
            x2, k = re.subn(r'<f(?: [^>]*)?>[^<]*\[\d+\][^<]*</f>', '', x)       # 값(<v>)은 남는다
            n_f += k
            parts[name] = x2.encode('utf-8')
    dead = [n for n in parts if n.startswith('xl/externalLinks/')]
    for n in dead:
        del parts[n]
    wb = parts['xl/workbook.xml'].decode('utf-8')
    rids = re.findall(r'<externalReference r:id="(rId\d+)"/>', wb)
    wb = re.sub(r'<externalReferences>.*?</externalReferences>', '', wb, flags=re.S)
    parts['xl/workbook.xml'] = wb.encode('utf-8')
    rels = parts['xl/_rels/workbook.xml.rels'].decode('utf-8')
    for rid in rids:
        rels = re.sub(rf'<Relationship Id="{rid}"[^>]*/>', '', rels)
    rels = re.sub(r'<Relationship [^>]*Target="calcChain.xml"[^>]*/>', '', rels)
    parts['xl/_rels/workbook.xml.rels'] = rels.encode('utf-8')
    parts.pop('xl/calcChain.xml', None)
    ct = parts['[Content_Types].xml'].decode('utf-8')
    ct = re.sub(r'<Override PartName="/xl/externalLinks/[^"]+"[^>]*/>', '', ct)
    ct = re.sub(r'<Override PartName="/xl/calcChain.xml"[^>]*/>', '', ct)
    parts['[Content_Types].xml'] = ct.encode('utf-8')
    with zipfile.ZipFile(path + '.tmp', 'w', zipfile.ZIP_DEFLATED) as o:
        for n, d in parts.items():
            o.writestr(n, d)
    shutil.move(path + '.tmp', path)
    print(path.split('/')[-1], '| 외부 참조 수식 → 값', n_f, '| 지운 부품', len(dead))


if __name__ == '__main__':
    for p in sys.argv[1:]:
        strip(p)
