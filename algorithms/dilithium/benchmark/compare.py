"""Compare benchmark outputs from traditional and PQC demo runs."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt


RESULTS_DIR = Path(__file__).resolve().parent / "results"
TRADITIONAL_RESULT = RESULTS_DIR / "traditional_result.json"
PQC_RESULT = RESULTS_DIR / "pqc_result.json"
OUTPUT_PLOT = RESULTS_DIR / "comparison.png"


def load_result(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing result file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def print_summary(traditional: dict, pqc: dict) -> None:
    print("Comparison Summary")
    print(f"Traditional tx hash: {traditional['tx_hash']}")
    print(f"PQC tx hash: {pqc['tx_hash']}")
    print(f"Traditional gas used: {traditional['gas_used']}")
    print(f"PQC gas used: {pqc['gas_used']}")
    print(
        "Traditional signing time: "
        f"{traditional['benchmark']['ecdsa_sign_seconds']} s"
    )
    print(f"PQC sign time: {pqc['benchmark']['pqc_sign_seconds']} s")
    print(f"PQC verify time: {pqc['benchmark']['pqc_verify_seconds']} s")
    print(f"PQC signature size: {pqc['pqc']['signature_size_bytes']} bytes")


def save_plot(traditional: dict, pqc: dict) -> Path:
    labels = [
        "Signing time",
        "Send+confirm",
        "Gas used",
        "Auth bytes",
    ]
    traditional_values = [
        traditional["benchmark"]["ecdsa_sign_seconds"],
        traditional["benchmark"]["send_and_confirm_seconds"],
        traditional["gas_used"],
        traditional["benchmark"]["signature_size_bytes"],
    ]
    pqc_values = [
        pqc["benchmark"]["pqc_sign_seconds"] + pqc["benchmark"]["pqc_verify_seconds"],
        pqc["benchmark"]["send_and_confirm_seconds"],
        pqc["gas_used"],
        pqc["pqc"]["signature_size_bytes"],
    ]

    x_positions = range(len(labels))
    width = 0.35

    plt.figure(figsize=(10, 6))
    plt.bar([x - width / 2 for x in x_positions], traditional_values, width=width, label="Traditional")
    plt.bar([x + width / 2 for x in x_positions], pqc_values, width=width, label="PQC Hybrid")
    plt.xticks(list(x_positions), labels)
    plt.ylabel("Value")
    plt.title("Traditional vs PQC Hybrid")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT)
    plt.close()
    return OUTPUT_PLOT


def main() -> None:
    traditional = load_result(TRADITIONAL_RESULT)
    pqc = load_result(PQC_RESULT)
    print_summary(traditional, pqc)
    plot_path = save_plot(traditional, pqc)
    print(f"Plot saved to: {plot_path}")


if __name__ == "__main__":
    main()
