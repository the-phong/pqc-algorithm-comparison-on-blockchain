# PQC Suite

This folder groups all four algorithm demos into one structured suite.

## Environment

Preferred workflow:
- create one shared file at `pqc-suite/.env`
- all algorithm folders will read it automatically
- if an algorithm folder also has its own `.env`, that local file overrides the shared values

## Shared

Common files used by every algorithm:
- `shared/contracts/Demo.sol`
- `shared/contracts/DemoABI.json`
- `shared/python/common.py`
- `shared/requirements.txt`

## Algorithms

- `algorithms/dilithium`
  fixed algorithm: `ml_dsa_44`
  use this for the original signature-based demo

- `algorithms/falcon`
  fixed algorithm: `falcon_512`
  use this for a signature-based comparison against Dilithium

- `algorithms/sphincs-plus`
  fixed algorithm: `sphincs_sha2_128f_simple`
  use this for another signature-based comparison against Dilithium

- `algorithms/kyber-kem`
  fixed algorithm: `ml_kem_512`
  use this for confidentiality and key encapsulation

## Rule of thumb

- `dilithium`, `falcon`, `sphincs-plus` are signature-oriented packs.
- `kyber-kem` is a KEM-oriented pack.
