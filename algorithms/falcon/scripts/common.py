"""Shim that exposes shared helpers to the Falcon scripts."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SUITE_ROOT = PROJECT_ROOT.parents[1]
SHARED_COMMON = SUITE_ROOT / "shared" / "python" / "common.py"

os.environ.setdefault("PQC_PROJECT_ROOT", str(PROJECT_ROOT))
os.environ.setdefault("PQC_SUITE_ROOT", str(SUITE_ROOT))

spec = importlib.util.spec_from_file_location("_suite_shared_common", SHARED_COMMON)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

for name in dir(module):
    if not name.startswith("_"):
        globals()[name] = getattr(module, name)
