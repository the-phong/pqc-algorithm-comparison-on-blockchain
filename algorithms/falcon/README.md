# Falcon Demo Pack

This folder is an isolated copy of the blockchain demo configured for Falcon.

Fixed algorithm:
- `falcon_512`

Shared files are outside this folder:
- `../../shared/contracts/Demo.sol`
- `../../shared/contracts/DemoABI.json`
- `../../shared/python/common.py`

Main scripts:
- `scripts/traditional_demo.py`
- `scripts/pqc_demo.py`
- `scripts/integrity_cases.py`
- `scripts/confidentiality_demo.py`
- `scripts/availability_benchmark.py`

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
