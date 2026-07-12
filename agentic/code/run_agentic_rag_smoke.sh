#!/bin/bash
# v0.3 smoke test: run pipeline on a small sample (no reranker)

set -e

cd "$(dirname "$0")"

INPUT_JSONL="${INPUT_JSONL:-/mnt/data_1/yds/多模态/agentic/outputs/qa_gold_4000/qa_gold_4000.jsonl}"
OUTPUT_JSONL="${OUTPUT_JSONL:-/mnt/data_1/yds/多模态/agentic/outputs/runtime/smoke_test.jsonl}"
LIMIT="${LIMIT:-5}"

echo "=== v0.3 Smoke Test (no reranker) ==="
echo "Input: $INPUT_JSONL"
echo "Output: $OUTPUT_JSONL"
echo "Limit: $LIMIT"
echo ""

python3 agentic_rag_pipeline.py \
  --input-jsonl "$INPUT_JSONL" \
  --output-jsonl "$OUTPUT_JSONL" \
  --limit "$LIMIT" \
  --text-k 20 \
  --image-k 20 \
  --max-rounds 2 \
  --continue-on-error

echo ""
echo "=== Done ==="
echo "Check output: $OUTPUT_JSONL"
