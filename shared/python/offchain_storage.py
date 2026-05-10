"""Local off-chain storage helpers used to emulate IPFS-style proof storage."""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("PQC_PROJECT_ROOT", Path.cwd())).resolve()
SUITE_ROOT = Path(os.environ.get("PQC_SUITE_ROOT", PROJECT_ROOT.parents[1])).resolve()
DEFAULT_STORAGE_DIR = SUITE_ROOT / "shared" / "offchain_store"
IPFS_API_URL = os.getenv("IPFS_API_URL", "").strip()


def ensure_storage_dir(storage_dir: str | Path | None = None) -> Path:
    resolved_dir = Path(storage_dir) if storage_dir else DEFAULT_STORAGE_DIR
    if not resolved_dir.is_absolute():
        resolved_dir = (PROJECT_ROOT / resolved_dir).resolve()
    resolved_dir.mkdir(parents=True, exist_ok=True)
    return resolved_dir


def build_cid(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def storage_backend_name() -> str:
    return "ipfs" if IPFS_API_URL else "local_cid_store"


def build_ipfs_uri(cid: str) -> str:
    return f"ipfs://{cid}"


def _build_path_repr(path_or_uri: str | Path) -> str:
    return str(path_or_uri)


def _ipfs_client():
    try:
        import ipfshttpclient  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "IPFS backend requested but ipfshttpclient is not installed. "
            "Run: pip install ipfshttpclient"
        ) from exc

    try:
        return ipfshttpclient.connect(IPFS_API_URL)
    except Exception as exc:
        raise RuntimeError(f"Failed to connect to IPFS API at {IPFS_API_URL}: {exc}") from exc


def save_blob(data: bytes, suffix: str, storage_dir: str | Path | None = None) -> tuple[str, Path, float]:
    if IPFS_API_URL:
        start = time.perf_counter()
        with _ipfs_client() as client:
            cid = client.add_bytes(data)
        elapsed = time.perf_counter() - start
        return cid, Path(build_ipfs_uri(cid)), round(elapsed, 6)

    start = time.perf_counter()
    cid = build_cid(data)
    output_path = ensure_storage_dir(storage_dir) / f"{cid}.{suffix}"
    output_path.write_bytes(data)
    elapsed = time.perf_counter() - start
    return cid, output_path, round(elapsed, 6)


def load_blob(cid: str, suffix: str, storage_dir: str | Path | None = None) -> tuple[bytes, Path, float]:
    if cid.startswith("ipfs://"):
        cid = cid.removeprefix("ipfs://")

    if IPFS_API_URL:
        start = time.perf_counter()
        with _ipfs_client() as client:
            data = client.cat(cid)
        elapsed = time.perf_counter() - start
        return data, Path(build_ipfs_uri(cid)), round(elapsed, 6)

    start = time.perf_counter()
    input_path = ensure_storage_dir(storage_dir) / f"{cid}.{suffix}"
    data = input_path.read_bytes()
    elapsed = time.perf_counter() - start
    return data, input_path, round(elapsed, 6)


def save_signature(signature: bytes, storage_dir: str | Path | None = None) -> tuple[str, Path, float]:
    return save_blob(signature, "sig", storage_dir)


def load_signature(cid: str, storage_dir: str | Path | None = None) -> tuple[bytes, Path, float]:
    return load_blob(cid, "sig", storage_dir)


def save_public_key(public_key: bytes, storage_dir: str | Path | None = None) -> tuple[str, Path, float]:
    return save_blob(public_key, "pub", storage_dir)


def load_public_key(cid: str, storage_dir: str | Path | None = None) -> tuple[bytes, Path, float]:
    return load_blob(cid, "pub", storage_dir)
