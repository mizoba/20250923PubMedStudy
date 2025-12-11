#!/bin/bash
ulimit -n 512
python3 /Volumes/ssd4TB/20251080/bucketize_pmcs.py \
--input-dir "/Volumes/ssd4TB/20251080/oa_bulk/oa_comm/xml" \
--csv "/Volumes/ssd4TB/20251080/flaglist.csv" \
--out-dir "/Volumes/ssd4TB/20251080/output" \
--state "/Volumes/ssd4TB/20251080/state/state.sqlite" \
--max-open 400
python3 /Volumes/ssd4TB/20251080/bucketize_pmcs.py \
--input-dir "/Volumes/ssd4TB/20251080/oa_bulk/oa_noncomm/xml" \
--csv "/Volumes/ssd4TB/20251080/flaglist.csv" \
--out-dir "/Volumes/ssd4TB/20251080/output" \
--state "/Volumes/ssd4TB/20251080/state/state.sqlite" \
--max-open 400
python3 /Volumes/ssd4TB/20251080/bucketize_pmcs.py \
--input-dir "/Volumes/ssd4TB/20251080/oa_bulk/oa_other/xml" \
--csv "/Volumes/ssd4TB/20251080/flaglist.csv" \
--out-dir "/Volumes/ssd4TB/20251080/output" \
--state "/Volumes/ssd4TB/20251080/state/state.sqlite" \
--max-open 400