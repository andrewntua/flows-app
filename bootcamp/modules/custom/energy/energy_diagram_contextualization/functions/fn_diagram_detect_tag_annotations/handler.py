from cognite.client import CogniteClient

import diagram_annotations


def _limit_pdfs(data: dict | None) -> int | None:
    if not data:
        return None
    limit = data.get("limit_pdfs")
    return int(limit) if limit is not None else None


def handle(
    client: CogniteClient,
    data: dict | None = None,
    secrets: dict | None = None,
    function_call_info: dict | None = None,
):
    return diagram_annotations.detect_diagram_tag_annotations(
        client, limit_pdfs=_limit_pdfs(data)
    )
