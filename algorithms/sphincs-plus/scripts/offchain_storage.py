"""Shim that exposes shared off-chain storage helpers to SPHINCS+ scripts."""

from __future__ import annotations

import importlib.util

from common import SUITE_ROOT


SHARED_HELPER = SUITE_ROOT / "shared" / "python" / "offchain_storage.py"

spec = importlib.util.spec_from_file_location("_suite_shared_offchain_storage", SHARED_HELPER)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

for name in dir(module):
    if not name.startswith("_"):
        globals()[name] = getattr(module, name)
