"""Integrity test cases for the record-based demo contract."""

from __future__ import annotations

import time
from datetime import datetime

from pqcrypto.sign import sphincs_sha2_128f_simple
from web3.exceptions import ContractLogicError

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


def safe_verify(public_key: bytes, payload: bytes, signature: bytes) -> bool:
    try:
        return bool(sphincs_sha2_128f_simple.verify(public_key, payload, signature))
    except Exception:
        return False


def mutate_bytes(value: bytes) -> bytes:
    if not value:
        return b"\x00"
    mutated = bytearray(value)
    mutated[0] ^= 0x01
    return bytes(mutated)


def send_setup_transaction(contract, acct, w3, payload: bytes, app_nonce: int, timestamp: int, wait_timeout: int) -> tuple[str, int, int]:
    payload_hash = w3.to_hex(w3.keccak(payload))
    tx = contract.functions.storeRecord(
        payload,
        payload_hash,
        "0x" + ("00" * 32),
        app_nonce,
        timestamp,
        False,
        "integrity_replay_setup",
    ).build_transaction(
        {
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "gas": 500000,
            "maxFeePerGas": w3.to_wei("30", "gwei"),
            "maxPriorityFeePerGas": w3.to_wei("1", "gwei"),
            "chainId": w3.eth.chain_id,
        }
    )

    signed = acct.sign_transaction(tx)
    raw_tx = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction")
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=wait_timeout)
    record_id = contract.functions.lastRecordId().call()
    return tx_hash.hex(), receipt.status, record_id


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

    payload = f"Integrity test payload at {datetime.utcnow().isoformat()}Z".encode("utf-8")
    public_key, secret_key = sphincs_sha2_128f_simple.generate_keypair()
    signature = sphincs_sha2_128f_simple.sign(secret_key, payload)

    tampered_payload = mutate_bytes(payload)
    tampered_signature = mutate_bytes(signature)

    case_payload_tampered = {
        "case": "tampered_payload_before_verify",
        "expected": "verify_fail_no_tx",
        "verify_passed": safe_verify(public_key, tampered_payload, signature),
    }

    case_signature_tampered = {
        "case": "tampered_signature_before_verify",
        "expected": "verify_fail_no_tx",
        "verify_passed": safe_verify(public_key, payload, tampered_signature),
    }

    app_metadata = build_app_metadata()
    replay_payload = f"Replay setup payload at {datetime.utcnow().isoformat()}Z".encode("utf-8")
    setup_tx_hash, setup_status, setup_record_id = send_setup_transaction(
        contract,
        acct,
        w3,
        replay_payload,
        app_metadata["app_nonce"],
        app_metadata["timestamp"],
        wait_timeout,
    )

    replay_payload_hash = w3.to_hex(w3.keccak(replay_payload))
    replay_blocked = False
    replay_error = ""

    try:
        contract.functions.storeRecord(
            replay_payload,
            replay_payload_hash,
            "0x" + ("00" * 32),
            app_metadata["app_nonce"],
            int(time.time()),
            False,
            "integrity_replay_attempt",
        ).call({"from": acct.address})
    except ContractLogicError as exc:
        replay_blocked = True
        replay_error = str(exc)
    except Exception as exc:
        replay_blocked = True
        replay_error = str(exc)

    result = {
        "contract_address": contract.address,
        "account": acct.address,
        "chain_id": w3.eth.chain_id,
        "pqc_algorithm": sphincs_sha2_128f_simple.ALGORITHM,
        "cases": [
            case_payload_tampered,
            case_signature_tampered,
            {
                "case": "replay_same_app_nonce",
                "expected": "contract_revert_stale_nonce",
                "setup_tx_hash": setup_tx_hash,
                "setup_status": setup_status,
                "setup_record_id": setup_record_id,
                "app_nonce": app_metadata["app_nonce"],
                "replay_blocked": replay_blocked,
                "replay_error": replay_error,
            },
        ],
    }
    output_path = write_result("integrity_cases.json", result)

    print("Integrity Cases")
    print(f"Tampered payload verify passed: {case_payload_tampered['verify_passed']}")
    print(f"Tampered signature verify passed: {case_signature_tampered['verify_passed']}")
    print(f"Replay blocked: {replay_blocked}")
    if replay_error:
        print(f"Replay error: {replay_error}")
    print(f"Result File: {output_path}")


if __name__ == "__main__":
    main()
