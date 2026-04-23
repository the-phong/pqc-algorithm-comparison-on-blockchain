"""Compare traditional baseline against ML-KEM confidentiality results."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt


RESULTS_DIR = Path(__file__).resolve().parent / "results"
TRADITIONAL_RESULT = RESULTS_DIR / "traditional_result.json"
KEM_RESULT = RESULTS_DIR / "kyber_confidentiality_result.json"
OUTPUT_PLOT = RESULTS_DIR / "comparison_kem.png"


def load_result(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing result file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def print_summary(traditional: dict, kem_result: dict) -> None:
    print("Comparison Summary")
    print(f"Traditional tx hash: {traditional['tx_hash']}")
    print(f"ML-KEM tx hash: {kem_result['tx_hash']}")
    print(f"Traditional gas used: {traditional['gas_used']}")
    print(f"ML-KEM gas used: {kem_result['gas_used']}")
    print(f"Traditional signing time: {traditional['benchmark']['ecdsa_sign_seconds']} s")
    print(f"ML-KEM encaps time: {kem_result['benchmark']['kem_encaps_seconds']} s")
    print(f"ML-KEM decaps time: {kem_result['benchmark']['kem_decaps_seconds']} s")
    print(f"ML-KEM ciphertext size: {kem_result['kem']['ciphertext_size_bytes']} bytes")


def save_plot(traditional: dict, kem_result: dict) -> Path:
    labels = [
        "Auth/KEM time",
        "Send+confirm",
        "Gas used",
        "Crypto bytes",
    ]
    traditional_values = [
        traditional["benchmark"]["ecdsa_sign_seconds"],
        traditional["benchmark"]["send_and_confirm_seconds"],
        traditional["gas_used"],
        traditional["benchmark"]["signature_size_bytes"],
    ]
    kem_values = [
        kem_result["benchmark"]["kem_encaps_seconds"] + kem_result["benchmark"]["kem_decaps_seconds"],
        kem_result["benchmark"]["send_and_confirm_seconds"],
        kem_result["gas_used"],
        kem_result["kem"]["ciphertext_size_bytes"],
    ]

    x_positions = range(len(labels))
    width = 0.35

    plt.figure(figsize=(10, 6))
    plt.bar([x - width / 2 for x in x_positions], traditional_values, width=width, label="Traditional")
    plt.bar([x + width / 2 for x in x_positions], kem_values, width=width, label="ML-KEM Confidential")
    plt.xticks(list(x_positions), labels)
    plt.ylabel("Value")
    plt.title("Traditional vs ML-KEM Confidentiality")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT)
    plt.close()
    return OUTPUT_PLOT


def main() -> None:
    traditional = load_result(TRADITIONAL_RESULT)
    kem_result = load_result(KEM_RESULT)
    print_summary(traditional, kem_result)
    plot_path = save_plot(traditional, kem_result)
    print(f"Plot saved to: {plot_path}")


if __name__ == "__main__":
    main()
