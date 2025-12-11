#!/bin/bash

# =============================================================================
# Script Name: verify_integrity.sh
# Description: Verifies the integrity of downloaded .tar.gz files using standard
#              gzip and tar integrity checks.
# Output: logs verification errors to validation_error.log
# =============================================================================

LOG_FILE="validation_error.log"
DATA_DIR="./pmc_data" # 

echo "Starting Integrity Check: $(date)"

# Find all .tar.gz files and loop through them
find "$DATA_DIR" -name "*.tar.gz" | while read -r file; do
    
    # 1. Check GZIP integrity (CRC check)
    if ! gunzip -t "$file" 2>/dev/null; then
        echo "[ERROR] GZIP Check Failed: $file" | tee -a "$LOG_FILE"
        continue
    fi

    # 2. Check TAR structure integrity (List content check)
    if ! tar -tzf "$file" > /dev/null 2>&1; then
        echo "[ERROR] TAR Structure Check Failed: $file" | tee -a "$LOG_FILE"
        continue
    fi
    
    # Optional: Print progress
    # echo "Verified: $file"
done

echo "Integrity Check Completed: $(date)"