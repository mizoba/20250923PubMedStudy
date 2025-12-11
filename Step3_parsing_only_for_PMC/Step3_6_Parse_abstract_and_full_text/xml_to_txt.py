#!/usr/bin/env python3
import os
import tarfile
import re
from lxml import etree
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
from pathlib import Path

# ---------- helpers ----------
def clean_text(s: str) -> str:
    if s is None:
        return ""
    # replace CR/LF with tab, collapse repeated whitespace/tabs, strip
    s = re.sub(r'[\r\n]+', '\t', s)
    s = re.sub(r'\t+', '\t', s)
    s = re.sub(r'[ \t]+', ' ', s)
    return s.strip()

def extract_text_from_el(el):
    # get concatenated text of element and children
    return ''.join(el.itertext()).strip()

def parse_xml_bytes_get_abstract_body(xml_bytes):
    try:
        root = etree.fromstring(xml_bytes)
    except Exception:
        return None, None  # parse failed
    # abstract: try common paths
    abstract_text = None
    # search for <abstract>
    abstract_nodes = root.xpath('//abstract | //Abstract | //ABSTRACT')
    # Case-insensitive abstract search
    #abstract_nodes = (root.xpath('//abstract') or root.xpath('//Abstract') or root.xpath('//ABSTRACT'))x
    if abstract_nodes:
        texts = []
        for a in abstract_nodes:
            t = extract_text_from_el(a)
            if t:
                texts.append(t)
        if texts:
            abstract_text = '\n'.join(texts)
    # body: try <body>
    body_text = None
    body_nodes = root.xpath('//body | //Body | //BODY')
    if body_nodes:
        texts = []
        for b in body_nodes:
            t = extract_text_from_el(b)
            if t:
                texts.append(t)
        if texts:
            body_text = '\n'.join(texts)
    return abstract_text, body_text

# ---------- core: process single tar ----------# ---------- core: process single tar ----------
def process_tar(tar_path, field_name, year_str, outdir):
    tar_path = Path(tar_path)
    
    # 'outdir'를 {field_name} 하위 폴더로 재정의합니다.
    outdir = Path(outdir) / field_name 
    
    outdir.mkdir(parents=True, exist_ok=True)

    # output filenames
    base = outdir / f"pmcid_list_{field_name}_{year_str}_abstract.txt"
    base2 = outdir / f"pmcxtract_list_{field_name}_{year_str}_abstract.txt"
    base3 = outdir / f"pmcid_list_{field_name}_{year_str}_body.txt"
    base4 = outdir / f"pmcxtract_list_{field_name}_{year_str}_body.txt"

    processing_flag = tar_path.with_suffix(tar_path.suffix + ".processing")
    done_flag = tar_path.with_suffix(tar_path.suffix + ".done")

    if done_flag.exists():
        print(f"[SKIP] done: {tar_path}")
        return

    # create processing file (simple semaphore)
    processing_flag.write_text("processing")

    try:
        with tarfile.open(tar_path, 'r:*') as tf, \
             open(base, 'a', encoding='utf-8') as f_pmcid_abs, \
             open(base2, 'a', encoding='utf-8') as f_extract_abs, \
             open(base3, 'a', encoding='utf-8') as f_pmcid_body, \
             open(base4, 'a', encoding='utf-8') as f_extract_body:

            for member in tf:
                if not member.isfile():
                    continue
                # skip non-xml names
                if not member.name.lower().endswith('.xml'):
                    continue

                try:
                    mfile = tf.extractfile(member)
                    if mfile is None:
                        continue
                    data = mfile.read()
                except Exception as e:
                    # log and continue
                    print(f"[WARN] failed read {member.name}: {e}")
                    continue

                # PMCID from filename (strip directories)
                pmcid = os.path.splitext(os.path.basename(member.name))[0]

                abstract, body = parse_xml_bytes_get_abstract_body(data)
                if abstract:
                    t = clean_text(abstract)
                    if t:
                        f_pmcid_abs.write(pmcid + "\n")
                        f_extract_abs.write(f"{pmcid} {t}\n")
                if body:
                    t = clean_text(body)
                    if t:
                        f_pmcid_body.write(pmcid + "\n")
                        f_extract_body.write(f"{pmcid} {t}\n")

        # finished
        done_flag.write_text("done")
        print(f"[DONE] {tar_path}")
    except Exception as e:
        print(f"[ERROR] {tar_path}: {e}")
        raise
    finally:
        if processing_flag.exists():
            processing_flag.unlink(missing_ok=True)

# ---------- driver: traverse folders & run ----------
def find_jobs(root_dir):
    jobs = []
    root_dir = Path(root_dir)
    # expect structure: root/field/{year}.tar
    for field_dir in root_dir.iterdir():
        if not field_dir.is_dir():
            continue
        for tarfile_entry in field_dir.iterdir():
            if tarfile_entry.is_file() and tarfile_entry.suffix in ('.tar', '.tgz', '.tar.gz', '.tar.bz2'):
                # derive year from filename (strip ext)
                year = tarfile_entry.stem  # e.g., "2001"
                jobs.append((str(tarfile_entry), field_dir.name, year))
    return jobs

def main(args):
    jobs = find_jobs(args.input_root)
    print(f"Found {len(jobs)} jobs")
    if args.dry_run:
        for j in jobs[:10]:
            print("DRY:", j)
        return

    # adjust workers as needed
    with ProcessPoolExecutor(max_workers=args.workers) as exe:
        futures = {}
        for tar_path, field, year in jobs:
            fut = exe.submit(process_tar, tar_path, field, year, args.output_dir)
            futures[fut] = tar_path
        for fut in as_completed(futures):
            tarpath = futures[fut]
            try:
                fut.result()
            except Exception as e:
                print(f"[JOB ERROR] {tarpath}: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process PMC tar -> produce pmcid/pmcxtract lists")
    parser.add_argument("input_root", help="root folder containing field subfolders")
    parser.add_argument("output_dir", help="output directory")
    parser.add_argument("--workers", type=int, default=2, help="max parallel tar files")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(args)
