#!/bin/bash

wget -m -nH --cut-dirs=2 -np -R "index.html*" ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_bulk/
