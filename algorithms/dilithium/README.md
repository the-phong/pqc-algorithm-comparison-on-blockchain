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
python3 scripts/verify_e2e.py --record-id <record_id> --public-key-cid <public_key_cid>
python3 scripts/integrity_cases.py
python3 scripts/confidentiality_demo.py
python3 scripts/availability_benchmark.py --mode traditional --count 5
python3 scripts/availability_benchmark.py --mode pqc_hybrid --count 5
python3 scripts/availability_benchmark.py --mode pqc_confidential --count 5
python3 benchmark/compare.py
python3 benchmark/compare_availability.py
```

Notes:
- `pqc_demo.py` now stores the Dilithium signature and public key in local off-chain storage by default at `../../shared/offchain_store/`.
- If `IPFS_API_URL` is set, the same flow uses a real IPFS node instead.
- The on-chain record stores `ipfsCid` and `algorithm`, so you must redeploy the updated `Demo.sol` and refresh `shared/contracts/DemoABI.json` before running the new flow.
