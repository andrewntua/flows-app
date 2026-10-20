from cognite.client import CogniteClient

import diagram_annotations


def handle(
    client: CogniteClient,
    data: dict | None = None,
    secrets: dict | None = None,
    function_call_info: dict | None = None,
):
    return diagram_annotations.delete_diagram_annotations(client)
