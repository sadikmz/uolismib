#!/bin/bash
# PAVprot Integration Test Runner
# Runs pavprot with test data and logs output

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="${PROJECT_DIR}/test/output_${TIMESTAMP}"
LOG_FILE="${OUTPUT_DIR}/test_run.log"

echo "=============================================="
echo "PAVprot Integration Test"
echo "=============================================="
echo "Timestamp: ${TIMESTAMP}"
echo "Output dir: ${OUTPUT_DIR}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Run pavprot
echo "Running pavprot..." | tee "${LOG_FILE}"
cd "${PROJECT_DIR}"

python pavprot.py \
  --gff-comp test/data/gffcompare.tracking \
  --gff test/data/gff_feature_table.gff3 \
  --interproscan-out test/data/test_interproscan.tsv \
  --output-dir "${OUTPUT_DIR}" \
  --output-prefix integration_test \
  2>&1 | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "=============================================="  | tee -a "${LOG_FILE}"
echo "Output files:" | tee -a "${LOG_FILE}"
echo "=============================================="  | tee -a "${LOG_FILE}"
ls -la "${OUTPUT_DIR}"/*.tsv "${OUTPUT_DIR}"/*.txt 2>/dev/null | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "Test completed. Log saved to: ${LOG_FILE}"
