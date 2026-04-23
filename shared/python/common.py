"""Shared helpers for the blockchain demo scripts."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from web3 import Web3


PROJECT_ROOT = Path(os.environ.get("PQC_PROJECT_ROOT", Path.cwd())).resolve()
SUITE_ROOT = Path(os.environ.get("PQC_SUITE_ROOT", PROJECT_ROOT.parents[1])).resolve()
DEFAULT_ABI_PATH = SUITE_ROOT / "shared" / "contracts" / "DemoABI.json"


def load_dotenv() -> None:
    """Load suite-level .env first, then project-level .env as an override."""
    env_paths = [
        SUITE_ROOT / ".env",
        PROJECT_ROOT / ".env",
    ]

    for env_path in env_paths:
        if not env_path.exists():
            continue

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ[key] = value


def require_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if not value:
        print(f"Missing required env var: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def optional_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        print(f"Invalid integer env var: {name}={value}", file=sys.stderr)
        sys.exit(1)


def load_abi(abi_path: str) -> list[dict[str, Any]]:
    resolved_path = Path(abi_path)
    if not resolved_path.is_absolute():
        project_relative = (PROJECT_ROOT / resolved_path).resolve()
        suite_relative = (SUITE_ROOT / resolved_path).resolve()
        if project_relative.exists():
            resolved_path = project_relative
        else:
            resolved_path = suite_relative
    with open(resolved_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def build_web3(rpc_url: str) -> Web3:
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("Failed to connect to RPC", file=sys.stderr)
        sys.exit(1)
    return w3


def ensure_results_dir() -> Path:
    result_dir = PROJECT_ROOT / "benchmark" / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    return result_dir


def write_result(filename: str, payload: dict[str, Any]) -> Path:
    output_path = ensure_results_dir() / filename
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def build_app_metadata() -> dict[str, int]:
    timestamp = int(time.time())
    app_nonce = int(time.time_ns())
    return {
        "app_nonce": app_nonce,
        "timestamp": timestamp,
    }
