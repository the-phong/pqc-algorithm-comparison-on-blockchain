#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$ROOT_DIR/algorithms/dilithium"

cd "$PROJECT_DIR"

python3 scripts/traditional_demo.py
python3 scripts/pqc_demo.py
python3 scripts/integrity_cases.py
python3 scripts/confidentiality_demo.py
python3 scripts/availability_benchmark.py --mode traditional --count 5
python3 scripts/availability_benchmark.py --mode pqc_hybrid --count 5
python3 scripts/availability_benchmark.py --mode pqc_confidential --count 5
python3 benchmark/compare.py
python3 benchmark/compare_availability.py
