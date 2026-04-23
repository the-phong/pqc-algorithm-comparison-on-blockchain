# Kyber / ML-KEM Demo Pack

This folder is a separate demo pack for ML-KEM (Kyber). It is intentionally
organized around confidentiality and key encapsulation, not signature-based
integrity, because Kyber is a KEM rather than a digital signature algorithm.

Fixed algorithm:
- `ml_kem_512`

Shared files are outside this folder:
- `../../shared/contracts/Demo.sol`
- `../../shared/contracts/DemoABI.json`
- `../../shared/python/common.py`

Main scripts:
- `scripts/traditional_demo.py`
- `scripts/kem_confidentiality_demo.py`
- `scripts/availability_kem_benchmark.py`
- `benchmark/compare_kem.py`
- `benchmark/compare_availability_kem.py`

Quick start:
```bash
cp .env.example .env
python3 scripts/traditional_demo.py
python3 scripts/kem_confidentiality_demo.py
python3 scripts/availability_kem_benchmark.py --mode traditional --count 5
python3 scripts/availability_kem_benchmark.py --mode kyber_kem_confidential --count 5
python3 benchmark/compare_kem.py
python3 benchmark/compare_availability_kem.py
```
