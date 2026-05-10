"""End-to-end verifier for SPHINCS+ records stored on-chain."""

from __future__ import annotations

import argparse
import time

from pqcrypto.sign import sphincs_sha2_128f_simple

from common import (
    DEFAULT_ABI_PATH,
    build_web3,
    load_abi,
    load_dotenv,
    require_env,
    write_result,
)
from offchain_storage import load_public_key, load_signature, storage_backend_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a SPHINCS+ record end-to-end.")
    parser.add_argument("--record-id", type=int, required=True, help="On-chain record id to verify")
    parser.add_argument(
        "--public-key-cid",
        required=True,
        help="CID of the stored SPHINCS+ public key used to verify the record",
    )
    return parser.parse_args()


def fetch_record(contract, record_id: int) -> dict[str, object]:
    (
        fetched_record_id,
        owner,
        payload,
        payload_hash,
        pqc_proof_hash,
        app_nonce,
        timestamp,
        encrypted,
        mode,
        ipfs_cid,
        algorithm,
    ) = contract.functions.getRecord(record_id).call()

    return {
        "record_id": fetched_record_id,
        "owner": owner,
        "payload": payload,
        "payload_hash": payload_hash.hex() if isinstance(payload_hash, bytes) else payload_hash,
        "pqc_proof_hash": pqc_proof_hash.hex() if isinstance(pqc_proof_hash, bytes) else pqc_proof_hash,
        "app_nonce": app_nonce,
        "timestamp": timestamp,
        "encrypted": encrypted,
        "mode": mode,
        "ipfs_cid": ipfs_cid,
        "algorithm": algorithm,
    }


def add_hex_prefix(value: str) -> str:
    return value if value.startswith("0x") else f"0x{value}"


def main() -> None:
    args = parse_args()
    load_dotenv()

    rpc_url = require_env("RPC_URL")
    contract_address = require_env("CONTRACT_ADDRESS")
    abi_path = require_env("CONTRACT_ABI_PATH", str(DEFAULT_ABI_PATH))

    w3 = build_web3(rpc_url)
    abi = load_abi(abi_path)
    contract = w3.eth.contract(address=w3.to_checksum_address(contract_address), abi=abi)

    record = fetch_record(contract, args.record_id)
    if record["record_id"] == 0:
        raise RuntimeError(f"Record {args.record_id} does not exist")

    signature, signature_path, signature_download_seconds = load_signature(str(record["ipfs_cid"]))
    public_key, public_key_path, public_key_download_seconds = load_public_key(args.public_key_cid)

    hash_start = time.perf_counter()
    recomputed_payload_hash = w3.to_hex(w3.keccak(record["payload"]))
    recomputed_proof_hash = w3.to_hex(w3.keccak(record["payload"] + signature))
    payload_hash_matches = recomputed_payload_hash == add_hex_prefix(str(record["payload_hash"]))
    proof_hash_matches = recomputed_proof_hash == add_hex_prefix(str(record["pqc_proof_hash"]))
    hash_comparison_seconds = round(time.perf_counter() - hash_start, 6)

    verify_start = time.perf_counter()
    signature_valid = bool(sphincs_sha2_128f_simple.verify(public_key, record["payload"], signature))
    pqc_verify_seconds = round(time.perf_counter() - verify_start, 6)

    e2e_verification_latency = round(
        signature_download_seconds
        + public_key_download_seconds
        + hash_comparison_seconds
        + pqc_verify_seconds,
        6,
    )

    result = {
        "record_id": record["record_id"],
        "owner": record["owner"],
        "mode": record["mode"],
        "algorithm": record["algorithm"],
        "ipfs_cid": record["ipfs_cid"],
        "public_key_cid": args.public_key_cid,
        "payload_hash_matches": payload_hash_matches,
        "proof_hash_matches": proof_hash_matches,
        "signature_valid": signature_valid,
        "verification_passed": payload_hash_matches and proof_hash_matches and signature_valid,
        "offchain_storage": {
            "storage_backend": storage_backend_name(),
            "signature_path": str(signature_path),
            "public_key_path": str(public_key_path),
        },
        "benchmark": {
            "signature_download_seconds": signature_download_seconds,
            "public_key_download_seconds": public_key_download_seconds,
            "hash_comparison_seconds": hash_comparison_seconds,
            "pqc_verify_seconds": pqc_verify_seconds,
            "e2e_verification_latency": e2e_verification_latency,
        },
    }
    output_path = write_result("verify_e2e_result.json", result)

    print("SPHINCS+ End-to-End Verification")
    print(f"Record ID: {record['record_id']}")
    print(f"Payload Hash Match: {payload_hash_matches}")
    print(f"Proof Hash Match: {proof_hash_matches}")
    print(f"Signature Valid: {signature_valid}")
    print(f"Verification Passed: {result['verification_passed']}")
    print(f"Result File: {output_path}")


if __name__ == "__main__":
    main()
