"""Confidentiality demo using ML-KEM (Kyber) to derive the AES key."""

from __future__ import annotations

import hashlib
import time
from datetime import datetime

from Crypto.Cipher import AES

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
from pqcrypto.kem import ml_kem_512


def derive_aes_key(shared_secret: bytes) -> bytes:
    return hashlib.sha256(shared_secret).digest()


def encrypt_payload(key: bytes, plaintext: bytes) -> tuple[bytes, int]:
    start = time.perf_counter()
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    elapsed = time.perf_counter() - start
    return cipher.nonce + tag + ciphertext, round(elapsed, 6)


def decrypt_payload(key: bytes, payload: bytes) -> tuple[bytes, int]:
    start = time.perf_counter()
    nonce = payload[:16]
    tag = payload[16:32]
    ciphertext = payload[32:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    elapsed = time.perf_counter() - start
    return plaintext, round(elapsed, 6)


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

    message = f"Hello from ML-KEM confidentiality demo at {datetime.utcnow().isoformat()}Z"
    plaintext = message.encode("utf-8")

    keygen_start = time.perf_counter()
    public_key, secret_key = ml_kem_512.generate_keypair()
    keygen_seconds = time.perf_counter() - keygen_start

    encaps_start = time.perf_counter()
    kem_ciphertext, shared_secret_enc = ml_kem_512.encrypt(public_key)
    encaps_seconds = time.perf_counter() - encaps_start

    decaps_start = time.perf_counter()
    shared_secret_dec = ml_kem_512.decrypt(secret_key, kem_ciphertext)
    decaps_seconds = time.perf_counter() - decaps_start

    if shared_secret_enc != shared_secret_dec:
        raise RuntimeError("ML-KEM shared secret mismatch")

    aes_key = derive_aes_key(shared_secret_enc)
    payload, encryption_seconds = encrypt_payload(aes_key, plaintext)
    decrypted, decrypt_seconds = decrypt_payload(aes_key, payload)
    if decrypted != plaintext:
        raise RuntimeError("ML-KEM confidentiality decrypt check failed")

    payload_hash = w3.to_hex(w3.keccak(payload))
    app_metadata = build_app_metadata()
    encrypted = True
    mode = "kyber_kem_confidential"
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
    build_seconds = time.perf_counter() - build_start

    sign_start = time.perf_counter()
    signed = acct.sign_transaction(tx)
    ecdsa_sign_seconds = time.perf_counter() - sign_start

    send_start = time.perf_counter()
    raw_tx = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction")
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=wait_timeout)
    send_seconds = time.perf_counter() - send_start
    record_id = contract.functions.lastRecordId().call()

    result = {
        "mode": mode,
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
        "kem_proof_hash": kem_proof_hash,
        "encrypted": encrypted,
        "confidentiality": {
            "algorithm": "aes-256-gcm",
            "plaintext_size_bytes": len(plaintext),
            "encrypted_payload_size_bytes": len(payload),
            "encryption_seconds": encryption_seconds,
            "decrypt_seconds": decrypt_seconds,
            "decrypt_matches_plaintext": True,
        },
        "kem": {
            "algorithm": ml_kem_512.ALGORITHM,
            "public_key_size_bytes": ml_kem_512.PUBLIC_KEY_SIZE,
            "secret_key_size_bytes": ml_kem_512.SECRET_KEY_SIZE,
            "ciphertext_size_bytes": len(kem_ciphertext),
            "shared_secret_size_bytes": len(shared_secret_enc),
        },
        "benchmark": {
            "kem_keygen_seconds": round(keygen_seconds, 6),
            "kem_encaps_seconds": round(encaps_seconds, 6),
            "kem_decaps_seconds": round(decaps_seconds, 6),
            "tx_build_seconds": round(build_seconds, 6),
            "ecdsa_sign_seconds": round(ecdsa_sign_seconds, 6),
            "send_and_confirm_seconds": round(send_seconds, 6),
            "ecdsa_signature_size_bytes": 65,
            "ecdsa_raw_tx_size_bytes": len(raw_tx),
        },
    }
    output_path = write_result("kyber_confidentiality_result.json", result)

    print("ML-KEM Confidentiality Mode")
    print("Shared Secret Match: YES")
    print("Payload Encrypted: YES")
    print("Transaction Confirmed")
    print(f"Tx Hash: {tx_hash.hex()}")
    print(f"ML-KEM Ciphertext Size: {len(kem_ciphertext)} bytes")
    print(f"Gas Used: {receipt.gasUsed}")
    print(f"Result File: {output_path}")


if __name__ == "__main__":
    main()
