from __future__ import annotations

import sys
from pathlib import Path

from cognite.client import CogniteClient

sys.path.append(str(Path(__file__).parent))

import oid_replication


def handle(
    client: CogniteClient,
    data: dict | None = None,
    secrets: dict | None = None,
    function_call_info: dict | None = None,
) -> dict:
    oid_secret = (secrets or {}).get("oid-secret")
    if not oid_secret:
        print("Missing function secret oid-secret")
        return {"status": "failed", "reason": "missing_oid_secret"}

    return oid_replication.replicate_oid_datapoints(client, oid_secret)
