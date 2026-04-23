"""Traditional (ECDSA-only) transaction demo."""

from __future__ import annotations

import time
from datetime import datetime

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

    message = f"Hello from traditional demo at {datetime.utcnow().isoformat()}Z"
    payload = message.encode("utf-8")
    payload_hash = w3.to_hex(w3.keccak(payload))
    app_metadata = build_app_metadata()
    pqc_proof_hash = "0x" + ("00" * 32)
    encrypted = False
    mode = "traditional"

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

    sign_start = time.perf_counter()
    signed = acct.sign_transaction(tx)
    sign_seconds = time.perf_counter() - sign_start

    send_start = time.perf_counter()
    raw_tx = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction")
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=wait_timeout)
    send_seconds = time.perf_counter() - send_start
    record_id = contract.functions.lastRecordId().call()

    result = {
        "mode": "traditional",
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
        "benchmark": {
            "tx_build_seconds": round(build_seconds, 6),
            "ecdsa_sign_seconds": round(sign_seconds, 6),
            "send_and_confirm_seconds": round(send_seconds, 6),
            "signature_size_bytes": 65,
            "raw_tx_size_bytes": len(raw_tx),
        },
    }
    output_path = write_result("traditional_result.json", result)

    print("Traditional Mode")
    print("Transaction Confirmed")
    print(f"Tx Hash: {tx_hash.hex()}")
    print(f"Gas Used: {receipt.gasUsed}")
    print(f"Result File: {output_path}")


if __name__ == "__main__":
    main()
