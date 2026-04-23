# Dilithium Demo Pack

This folder is the original Dilithium / ML-DSA demo inside the unified suite.

Fixed algorithm:
- `ml_dsa_44`

Shared files are outside this folder:
- `../../shared/contracts/Demo.sol`
- `../../shared/contracts/DemoABI.json`
- `../../shared/python/common.py`

Quick start:
```bash
cp .env.example .env
python3 scripts/traditional_demo.py
python3 scripts/pqc_demo.py
python3 scripts/integrity_cases.py
python3 scripts/confidentiality_demo.py
python3 scripts/availability_benchmark.py --mode traditional --count 5
python3 scripts/availability_benchmark.py --mode pqc_hybrid --count 5
python3 scripts/availability_benchmark.py --mode pqc_confidential --count 5
python3 benchmark/compare.py
python3 benchmark/compare_availability.py
```
