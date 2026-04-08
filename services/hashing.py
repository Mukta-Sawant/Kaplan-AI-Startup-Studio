"""
Deterministic input hashing for agent run deduplication and versioning.
"""

import hashlib
import json
from typing import Any


def hash_input(payload: Any) -> str:
    """
    Produce a stable SHA-256 hash of any JSON-serialisable value.

    The payload is serialised with sorted keys so that key-ordering
    differences between Python dicts do not produce different hashes.

    Returns:
        A 64-character hex string.
    """
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
