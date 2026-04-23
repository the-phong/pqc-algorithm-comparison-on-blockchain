"""Aggregate availability results for traditional mode and ML-KEM mode."""

from __future__ import annotations

import json
from pathlib import Path


RESULTS_DIR = Path(__file__).resolve().parent / "results"
INPUT_FILES = {
    "traditional": RESULTS_DIR / "availability_traditional.json",
    "kyber_kem_confidential": RESULTS_DIR / "availability_kyber_kem_confidential.json",
}
OUTPUT_MD = RESULTS_DIR / "availability_summary_kem.md"


def load_result(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing result file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def fmt_number(value: object, decimals: int = 6) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{decimals}f}"
    return str(value)


def build_rows(results: dict[str, dict]) -> list[list[str]]:
    rows = []
    for mode, payload in results.items():
        summary = payload["summary"]
        runs = payload.get("runs", [])
        avg_gas = None
        if runs:
            avg_gas = sum(run["gas_used"] for run in runs) / len(runs)
        rows.append(
            [
                mode,
                str(summary["success_count"]),
                str(summary["failure_count"]),
                f"{summary['success_rate_percent']}%",
                fmt_number(summary["average_latency_seconds"]),
                fmt_number(summary["p95_latency_seconds"]),
                fmt_number(summary["p99_latency_seconds"]),
                fmt_number(summary["throughput_tx_per_second"]),
                str(summary["retry_count"]),
                fmt_number(avg_gas, 2),
            ]
        )
    return rows


def render_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_line, separator_line, *body_lines])


def main() -> None:
    results = {mode: load_result(path) for mode, path in INPUT_FILES.items()}
    headers = [
        "Mode",
        "Success",
        "Failure",
        "Success Rate",
        "Avg Latency (s)",
        "P95 (s)",
        "P99 (s)",
        "Throughput (tx/s)",
        "Retries",
        "Avg Gas",
    ]
    rows = build_rows(results)
    markdown = "\n".join(
        [
            "# Availability Summary - ML-KEM",
            "",
            render_markdown_table(headers, rows),
            "",
        ]
    )
    OUTPUT_MD.write_text(markdown, encoding="utf-8")
    print("Availability Comparison - ML-KEM")
    for row in rows:
        print(" | ".join(row))
    print(f"Markdown report saved to: {OUTPUT_MD}")


if __name__ == "__main__":
    main()
