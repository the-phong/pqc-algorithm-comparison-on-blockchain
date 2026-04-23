#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$ROOT_DIR/algorithms/kyber-kem"

cd "$PROJECT_DIR"

python3 scripts/traditional_demo.py
python3 scripts/kem_confidentiality_demo.py
python3 scripts/availability_kem_benchmark.py --mode traditional --count 5
python3 scripts/availability_kem_benchmark.py --mode kyber_kem_confidential --count 5
python3 benchmark/compare_kem.py
python3 benchmark/compare_availability_kem.py
