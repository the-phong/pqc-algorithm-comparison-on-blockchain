"""Availability benchmark for traditional mode and ML-KEM confidentiality mode."""

from __future__ import annotations

import argparse
import hashlib
import statistics
import time
from datetime import datetime

from Crypto.Cipher import AES
from pqcrypto.kem import ml_kem_512
from web3.exceptions import ContractLogicError, TimeExhausted

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["traditional", "kyber_kem_confidential"],
        required=True,
    )
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--retry-delay", type=float, default=2.0)
    return parser.parse_args()


def derive_aes_key(shared_secret: bytes) -> bytes:
    return hashlib.sha256(shared_secret).digest()


def encrypt_payload(key: bytes, plaintext: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return cipher.nonce + tag + ciphertext


def build_mode_payload(mode: str, kem) -> tuple[str, bytes, bool, bytes, dict[str, float]]:
    message = f"Availability {mode} at {datetime.utcnow().isoformat()}Z"
    plaintext = message.encode("utf-8")
    if mode == "traditional":
        return message, plaintext, False, b"", {
            "kem_keygen_seconds": 0.0,
            "kem_encaps_seconds": 0.0,
            "kem_decaps_seconds": 0.0,
        }

    keygen_start = time.perf_counter()
    public_key, secret_key = kem.generate_keypair()
    kem_keygen_seconds = time.perf_counter() - keygen_start

    encaps_start = time.perf_counter()
    kem_ciphertext, shared_secret_enc = kem.encrypt(public_key)
    kem_encaps_seconds = time.perf_counter() - encaps_start

    decaps_start = time.perf_counter()
    shared_secret_dec = kem.decrypt(secret_key, kem_ciphertext)
    kem_decaps_seconds = time.perf_counter() - decaps_start

    if shared_secret_enc != shared_secret_dec:
        raise RuntimeError("ML-KEM shared secret mismatch during availability benchmark")

    payload = encrypt_payload(derive_aes_key(shared_secret_enc), plaintext)
    return message, payload, True, kem_ciphertext, {
        "kem_keygen_seconds": kem_keygen_seconds,
        "kem_encaps_seconds": kem_encaps_seconds,
        "kem_decaps_seconds": kem_decaps_seconds,
    }


def classify_error(exc: Exception) -> str:
    message = str(exc).lower()
    if isinstance(exc, TimeExhausted) or "timeout" in message:
        return "timeout"
    if isinstance(exc, ContractLogicError) or "execution reverted" in message or "revert" in message:
        return "contract_revert"
    if "nonce too low" in message or "replacement transaction underpriced" in message:
        return "nonce_conflict"
    if "insufficient funds" in message:
        return "insufficient_funds"
    if "failed to connect" in message or "connection" in message or "rpc" in message:
        return "rpc_error"
    if "shared secret mismatch" in message:
        return "kem_shared_secret_failed"
    return "unknown_error"


def percentile(sorted_values: list[float], ratio: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = ratio * (len(sorted_values) - 1)
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = index - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction


def send_one(contract, acct, w3, mode: str, wait_timeout: int, kem) -> dict:
    message, payload, encrypted, kem_ciphertext, kem_bench = build_mode_payload(mode, kem)
    payload_hash = w3.to_hex(w3.keccak(payload))
    app_metadata = build_app_metadata()
    kem_proof_hash = "0x" + ("00" * 32)
    if mode == "kyber_kem_confidential":
        kem_proof_hash = w3.to_hex(w3.keccak(payload + kem_ciphertext))

    nonce = w3.eth.get_transaction_count(acct.address)
    build_start = time.perf_counter()
    tx = contract.functions.storeRecord(
        payload,
        payload_hash,
        kem_proof_hash,
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
    tx_build_seconds = time.perf_counter() - build_start

    sign_start = time.perf_counter()
    signed = acct.sign_transaction(tx)
    ecdsa_sign_seconds = time.perf_counter() - sign_start

    send_start = time.perf_counter()
    raw_tx = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction")
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=wait_timeout)
    send_and_confirm_seconds = time.perf_counter() - send_start

    return {
        "message": message,
        "tx_hash": tx_hash.hex(),
        "status": receipt.status,
        "gas_used": receipt.gasUsed,
        "record_id": contract.functions.lastRecordId().call(),
        "app_nonce": app_metadata["app_nonce"],
        "timestamp": app_metadata["timestamp"],
        "encrypted": encrypted,
        "benchmark": {
            "kem_keygen_seconds": round(kem_bench["kem_keygen_seconds"], 6),
            "kem_encaps_seconds": round(kem_bench["kem_encaps_seconds"], 6),
            "kem_decaps_seconds": round(kem_bench["kem_decaps_seconds"], 6),
            "tx_build_seconds": round(tx_build_seconds, 6),
            "ecdsa_sign_seconds": round(ecdsa_sign_seconds, 6),
            "send_and_confirm_seconds": round(send_and_confirm_seconds, 6),
        },
    }


def send_with_retries(contract, acct, w3, mode: str, wait_timeout: int, max_retries: int, retry_delay: float, kem):
    attempts = max_retries + 1
    last_failure = None
    for attempt in range(1, attempts + 1):
        try:
            run = send_one(contract, acct, w3, mode, wait_timeout, kem)
            run["attempt"] = attempt
            run["retries_used"] = attempt - 1
            return run, None
        except Exception as exc:
            last_failure = {
                "attempt": attempt,
                "retries_used": attempt - 1,
                "error_type": classify_error(exc),
                "error": str(exc),
            }
            if attempt < attempts:
                time.sleep(retry_delay)
    return None, last_failure


def main() -> None:
    args = parse_args()
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

    runs = []
    failures = []
    latencies = []
    retry_counts = []
    start_time = time.perf_counter()

    for index in range(args.count):
        run, failure = send_with_retries(
            contract,
            acct,
            w3,
            args.mode,
            wait_timeout,
            args.max_retries,
            args.retry_delay,
            ml_kem_512,
        )
        if run is not None:
            runs.append(run)
            latencies.append(run["benchmark"]["send_and_confirm_seconds"])
            retry_counts.append(run["retries_used"])
            print(
                f"[{index + 1}/{args.count}] status={run['status']} "
                f"record_id={run['record_id']} latency={run['benchmark']['send_and_confirm_seconds']}s "
                f"retries={run['retries_used']}"
            )
        else:
            failure["run_index"] = index + 1
            failures.append(failure)
            print(
                f"[{index + 1}/{args.count}] failed: "
                f"{failure['error_type']} after {failure['attempt']} attempts"
            )

    success_count = sum(1 for run in runs if run["status"] == 1)
    total_runs = args.count
    success_rate = (success_count / total_runs) * 100 if total_runs else 0.0
    benchmark_elapsed = time.perf_counter() - start_time
    sorted_latencies = sorted(latencies)
    total_retries = sum(retry_counts) + sum(failure["retries_used"] for failure in failures)
    throughput_tps = success_count / benchmark_elapsed if benchmark_elapsed > 0 else None
    error_breakdown = {}
    for failure in failures:
        error_type = failure["error_type"]
        error_breakdown[error_type] = error_breakdown.get(error_type, 0) + 1

    result = {
        "mode": args.mode,
        "count": total_runs,
        "max_retries": args.max_retries,
        "retry_delay_seconds": args.retry_delay,
        "contract_address": contract.address,
        "account": acct.address,
        "chain_id": w3.eth.chain_id,
        "kem_algorithm": ml_kem_512.ALGORITHM,
        "summary": {
            "success_count": success_count,
            "failure_count": total_runs - success_count,
            "success_rate_percent": round(success_rate, 2),
            "average_latency_seconds": round(statistics.mean(latencies), 6) if latencies else None,
            "max_latency_seconds": round(max(latencies), 6) if latencies else None,
            "min_latency_seconds": round(min(latencies), 6) if latencies else None,
            "p50_latency_seconds": round(percentile(sorted_latencies, 0.50), 6) if latencies else None,
            "p95_latency_seconds": round(percentile(sorted_latencies, 0.95), 6) if latencies else None,
            "p99_latency_seconds": round(percentile(sorted_latencies, 0.99), 6) if latencies else None,
            "throughput_tx_per_second": round(throughput_tps, 6) if throughput_tps is not None else None,
            "benchmark_elapsed_seconds": round(benchmark_elapsed, 6),
            "retry_count": total_retries,
            "error_breakdown": error_breakdown,
        },
        "runs": runs,
        "failures": failures,
    }

    output_name = f"availability_{args.mode}.json"
    output_path = write_result(output_name, result)
    print("Availability Benchmark")
    print(f"Mode: {args.mode}")
    print(f"Success rate: {result['summary']['success_rate_percent']}%")
    print(f"Average latency: {result['summary']['average_latency_seconds']}s")
    print(f"P95 latency: {result['summary']['p95_latency_seconds']}s")
    print(f"Throughput: {result['summary']['throughput_tx_per_second']} tx/s")
    print(f"Retry count: {result['summary']['retry_count']}")
    print(f"Result File: {output_path}")


if __name__ == "__main__":
    main()
