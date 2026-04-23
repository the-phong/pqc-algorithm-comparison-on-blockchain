"""Hybrid PQC + ECDSA transaction demo."""

from __future__ import annotations

import time
from datetime import datetime

from pqcrypto.sign import ml_dsa_44

from common import (
    DEFAULT_ABI_PATH,
    build_app_metadata,
    build_web3,
    load_abi,
    load_dotenv,
    optional_env_int,
    require_env,
    write_result,
)


def main() -> None:
    load_dotenv()

    rpc_url = require_env("RPC_URL")
    private_key = require_env("PRIVATE_KEY")
    contract_address = require_env("CONTRACT_ADDRESS")
    abi_path = require_env("CONTRACT_ABI_PATH", str(DEFAULT_ABI_PATH))
    wait_timeout = optional_env_int("TX_TIMEOUT_SECONDS", 120)

    w3 = build_web3(rpc_url)
    abi = load_abi(abi_path)

    acct = w3.eth.account.from_key(private_key)
    contract = w3.eth.contract(address=w3.to_checksum_address(contract_address), abi=abi)

    message = f"Hello from PQC demo at {datetime.utcnow().isoformat()}Z"
    payload = message.encode("utf-8")
    payload_hash = w3.to_hex(w3.keccak(payload))
    app_metadata = build_app_metadata()
    encrypted = False
    mode = "pqc_hybrid"

    keygen_start = time.perf_counter()
    public_key, secret_key = ml_dsa_44.generate_keypair()
    keygen_seconds = time.perf_counter() - keygen_start

    pqc_sign_start = time.perf_counter()
    pqc_signature = ml_dsa_44.sign(secret_key, payload)
    pqc_sign_seconds = time.perf_counter() - pqc_sign_start

    pqc_verify_start = time.perf_counter()
    verified = ml_dsa_44.verify(public_key, payload, pqc_signature)
    pqc_verify_seconds = time.perf_counter() - pqc_verify_start

    if not verified:
        raise RuntimeError("PQC verification failed")

    pqc_proof_hash = w3.to_hex(w3.keccak(payload + pqc_signature))

    nonce = w3.eth.get_transaction_count(acct.address)
    build_start = time.perf_counter()
    tx = contract.functions.storeRecord(
        payload,
        payload_hash,
        pqc_proof_hash,
        app_metadata["app_nonce"],
        app_metadata["timestamp"],
        encrypted,
        mode,
    ).build_transaction(
        {
            "from": acct.address,
            "nonce": nonce,
            "gas": 500000,
            "maxFeePerGas": w3.to_wei("30", "gwei"),
            "maxPriorityFeePerGas": w3.to_wei("1", "gwei"),
            "chainId": w3.eth.chain_id,
        }
    )
    build_seconds = time.perf_counter() - build_start

    ecdsa_sign_start = time.perf_counter()
    signed = acct.sign_transaction(tx)
    ecdsa_sign_seconds = time.perf_counter() - ecdsa_sign_start

    send_start = time.perf_counter()
    raw_tx = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction")
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=wait_timeout)
    send_seconds = time.perf_counter() - send_start
    record_id = contract.functions.lastRecordId().call()

    result = {
        "mode": "pqc_hybrid",
        "message": message,
        "account": acct.address,
        "contract_address": contract.address,
        "chain_id": w3.eth.chain_id,
        "record_id": record_id,
        "tx_hash": tx_hash.hex(),
        "gas_used": receipt.gasUsed,
        "status": receipt.status,
        "app_nonce": app_metadata["app_nonce"],
        "timestamp": app_metadata["timestamp"],
        "payload_hash": payload_hash,
        "pqc_proof_hash": pqc_proof_hash,
        "encrypted": encrypted,
        "pqc": {
            "algorithm": ml_dsa_44.ALGORITHM,
            "public_key_size_bytes": ml_dsa_44.PUBLIC_KEY_SIZE,
            "secret_key_size_bytes": ml_dsa_44.SECRET_KEY_SIZE,
            "signature_size_bytes": len(pqc_signature),
        },
        "benchmark": {
            "pqc_keygen_seconds": round(keygen_seconds, 6),
            "pqc_sign_seconds": round(pqc_sign_seconds, 6),
            "pqc_verify_seconds": round(pqc_verify_seconds, 6),
            "tx_build_seconds": round(build_seconds, 6),
            "ecdsa_sign_seconds": round(ecdsa_sign_seconds, 6),
            "send_and_confirm_seconds": round(send_seconds, 6),
            "ecdsa_signature_size_bytes": 65,
            "ecdsa_raw_tx_size_bytes": len(raw_tx),
        },
    }
    output_path = write_result("pqc_result.json", result)

    print("Hybrid PQC Mode")
    print("PQC Verification: PASS")
    print("Transaction Confirmed")
    print(f"Tx Hash: {tx_hash.hex()}")
    print(f"PQC Signature Size: {len(pqc_signature)} bytes")
    print(f"Gas Used: {receipt.gasUsed}")
    print(f"Result File: {output_path}")


if __name__ == "__main__":
    main()
