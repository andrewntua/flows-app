"""Diagram annotation delete/detect logic (ported from valhall/documents.py)."""

from __future__ import annotations

import random
import uuid
from typing import Any

import config
from cognite.client import CogniteClient
from cognite.client.data_classes.data_modeling import (
    DirectRelationReference,
    EdgeApply,
    NodeApply,
    NodeId,
    NodeOrEdgeData,
)

MAX_FILE_ASSET_LINKS = 100


def _log(message: str) -> None:
    """Emit one log line (CDF Functions splits multi-arg print() across lines)."""
    print(message, flush=True)


def _list_pdf_file_nodes(client: CogniteClient, limit_pdfs: int | None) -> list:
    file_nodes = client.data_modeling.instances.list(
        sources=config.ENERGY_FILES_VIEW_ID,
        space=config.INSTANCE_SPACE,
        limit=None,
    )
    pdf_file_nodes = [node for node in file_nodes if node.external_id.endswith(".pdf")]
    random.shuffle(pdf_file_nodes)
    if limit_pdfs is not None:
        pdf_file_nodes = pdf_file_nodes[:limit_pdfs]
    return pdf_file_nodes


def delete_diagram_annotations(client: CogniteClient) -> dict[str, Any]:
    edges = client.data_modeling.instances.list(
        instance_type="edge",
        sources=config.DIAGRAM_ANNOTATION_VIEW_ID,
        space=config.INSTANCE_SPACE,
        limit=None,
    )
    deleted_count = len(edges)
    _log(f"Deleting {deleted_count} diagram annotation edges")
    if deleted_count:
        client.data_modeling.instances.delete(edges=edges.as_ids())
    return {"status": "success", "deleted_count": deleted_count}


def detect_diagram_tag_annotations(
    client: CogniteClient, limit_pdfs: int | None = None
) -> dict[str, Any]:
    asset_nodes = client.data_modeling.instances.list(
        sources=config.ENERGY_ASSETS_VIEW_ID,
        space=config.INSTANCE_SPACE,
        limit=None,
    )
    pdf_file_nodes = _list_pdf_file_nodes(client, limit_pdfs)

    _log(
        f"Trying to detect {len(asset_nodes)} asset tags in {len(pdf_file_nodes)} documents"
    )
    entities = [
        {"asset_external_id": asset.external_id.replace(config.ASSET_PREFIX, "")}
        for asset in asset_nodes
    ]

    pdfs_processed = 0
    edges_created = 0
    errors: list[str] = []

    if asset_nodes and pdf_file_nodes:
        for file in pdf_file_nodes:
            pdfs_processed += 1
            items = None
            timeout = 75
            remaining_retries = 15
            while True:
                try:
                    detect_results = client.diagrams.detect(
                        entities=entities,
                        search_field="asset_external_id",
                        file_instance_ids=[file.as_id()],
                    )
                    detect_results.wait_for_completion(timeout=timeout, interval=2)
                    items = detect_results.result.get("items")
                    if items:
                        break
                    remaining_retries -= 1
                    if remaining_retries:
                        timeout += 30
                        _log(f"Retrying {file.external_id} timeout={timeout}")
                        continue
                    break
                except Exception as e:
                    msg = f"{file.external_id}: {e}"
                    _log(f"Error during detection: {msg}")
                    errors.append(msg)
                    _log("Retrying...")
                    continue

            if items:
                edges_created += _create_diagram_annotations(
                    client, detect_results.result["items"]
                )
            else:
                _log(f"No items detected in {file.external_id}")

    return {
        "status": "success",
        "pdfs_processed": pdfs_processed,
        "edges_created": edges_created,
        "errors": errors,
    }


def detect_diagram_file_annotations(
    client: CogniteClient, limit_pdfs: int | None = None
) -> dict[str, Any]:
    pdf_file_nodes = _list_pdf_file_nodes(client, limit_pdfs)

    _log(f"Trying to detect file references in {len(pdf_file_nodes)} documents")
    entities = [
        {"file_ext_id": file_node.external_id.replace(".pdf", "")}
        for file_node in pdf_file_nodes
    ]

    pdfs_processed = 0
    edges_created = 0
    errors: list[str] = []

    for file in pdf_file_nodes:
        pdfs_processed += 1
        while True:
            try:
                detect_results = client.diagrams.detect(
                    entities=entities,
                    search_field="file_ext_id",
                    file_instance_ids=[file.as_id()],
                )
                detect_results.wait_for_completion(timeout=180, interval=5)
                break
            except Exception as e:
                msg = f"{file.external_id}: {e}"
                _log(f"Error during detection: {msg}")
                errors.append(msg)
                _log("Retrying...")
                continue

        items = detect_results.result.get("items")
        if items:
            edges_created += _create_file_annotations(
                client, detect_results.result["items"]
            )

    return {
        "status": "success",
        "pdfs_processed": pdfs_processed,
        "edges_created": edges_created,
        "errors": errors,
    }


def _asset_ref(external_id: str) -> DirectRelationReference:
    return DirectRelationReference(config.INSTANCE_SPACE, external_id)


def _existing_asset_refs(existing_assets) -> dict[str, DirectRelationReference]:
    linked: dict[str, DirectRelationReference] = {}
    for asset in existing_assets or []:
        if isinstance(asset, DirectRelationReference):
            linked[asset.external_id] = asset
        elif isinstance(asset, dict):
            ext_id = asset.get("externalId") or asset.get("external_id")
            if ext_id:
                linked[ext_id] = _asset_ref(ext_id)
    return linked


def _link_file_to_assets(
    client: CogniteClient, file_ext_id: str, asset_ext_ids: set[str]
) -> bool:
    if not asset_ext_ids:
        return False

    file_result = client.data_modeling.instances.retrieve(
        nodes=NodeId(config.INSTANCE_SPACE, file_ext_id),
        sources=config.ENERGY_FILES_VIEW_ID,
    )
    if not file_result.nodes:
        _log(f"File node not found, skipping asset link: {file_ext_id}")
        return False

    file_props = file_result.nodes[0].properties.data.get(config.ENERGY_FILES_VIEW_ID, {})
    linked = _existing_asset_refs(file_props.get("assets"))
    new_assets = [ext_id for ext_id in asset_ext_ids if ext_id not in linked]
    if not new_assets:
        return False

    for ext_id in new_assets:
        linked[ext_id] = _asset_ref(ext_id)

    properties = {"assets": list(linked.values())[:MAX_FILE_ASSET_LINKS]}
    source = NodeOrEdgeData(source=config.ENERGY_FILES_VIEW_ID, properties=properties)
    client.data_modeling.instances.apply(
        NodeApply(
            space=config.INSTANCE_SPACE,
            external_id=file_ext_id,
            sources=[source],
        )
    )
    _log(
        f"Linked file {file_ext_id} to {len(new_assets)} asset(s): "
        + ", ".join(sorted(new_assets))
    )
    return True


def _create_diagram_annotations(client: CogniteClient, detections) -> int:
    edge_nodes = []
    created = 0

    for detection in detections:
        file_ext_id = detection["fileInstanceId"]["externalId"]
        detected_asset_ext_ids: set[str] = set()
        for annotation in detection.get("annotations", []):
            asset_ext_id = (
                config.ASSET_PREFIX + annotation["entities"][0]["asset_external_id"]
            )
            detected_asset_ext_ids.add(asset_ext_id)

            vertices = annotation["region"]["vertices"]
            x_min = min(vertex["x"] for vertex in vertices)
            x_max = max(vertex["x"] for vertex in vertices)
            y_min = min(vertex["y"] for vertex in vertices)
            y_max = max(vertex["y"] for vertex in vertices)

            properties = {
                "name": asset_ext_id,
                "confidence": annotation["confidence"],
                "status": "Approved",
                "startNodePageNumber": annotation["region"]["page"],
                "endNodePageNumber": annotation["region"]["page"],
                "startNodeXMin": x_min,
                "startNodeXMax": x_max,
                "startNodeYMin": y_min,
                "startNodeYMax": y_max,
                "startNodeText": annotation["text"],
            }

            source = NodeOrEdgeData(
                source=config.DIAGRAM_ANNOTATION_VIEW_ID, properties=properties
            )
            edge_type = DirectRelationReference(
                config.INSTANCE_SPACE, "diagrams.AssetLink"
            )
            start_node = DirectRelationReference(config.INSTANCE_SPACE, file_ext_id)
            end_node = DirectRelationReference(config.INSTANCE_SPACE, asset_ext_id)

            edge_ext_id = file_ext_id + "-" + asset_ext_id + "-" + str(uuid.uuid4())
            edge_nodes.append(
                EdgeApply(
                    space=config.INSTANCE_SPACE,
                    external_id=edge_ext_id,
                    sources=[source],
                    type=edge_type,
                    start_node=start_node,
                    end_node=end_node,
                )
            )

        if edge_nodes:
            _log(f"Creating {len(edge_nodes)} tag edges for file {file_ext_id}")
            client.data_modeling.instances.apply(edge_nodes)
            created += len(edge_nodes)
            edge_nodes = []

        if detected_asset_ext_ids:
            _link_file_to_assets(client, file_ext_id, detected_asset_ext_ids)

    return created


def _create_file_annotations(client: CogniteClient, detections) -> int:
    edge_nodes = []
    created = 0

    for detection in detections:
        file_ext_id = detection["fileInstanceId"]["externalId"]
        for annotation in detection.get("annotations", []):
            target_file_ext_id = annotation["entities"][0]["file_ext_id"] + ".pdf"

            if file_ext_id != target_file_ext_id:
                vertices = annotation["region"]["vertices"]
                x_min = min(vertex["x"] for vertex in vertices)
                x_max = max(vertex["x"] for vertex in vertices)
                y_min = min(vertex["y"] for vertex in vertices)
                y_max = max(vertex["y"] for vertex in vertices)

                properties = {
                    "name": file_ext_id,
                    "confidence": annotation["confidence"],
                    "status": "Approved",
                    "startNodePageNumber": annotation["region"]["page"],
                    "endNodePageNumber": annotation["region"]["page"],
                    "startNodeXMin": x_min,
                    "startNodeXMax": x_max,
                    "startNodeYMin": y_min,
                    "startNodeYMax": y_max,
                    "startNodeText": annotation["text"],
                }

                source = NodeOrEdgeData(
                    source=config.DIAGRAM_ANNOTATION_VIEW_ID, properties=properties
                )
                edge_type = DirectRelationReference(
                    config.INSTANCE_SPACE, "diagrams.FileLink"
                )
                start_node = DirectRelationReference(config.INSTANCE_SPACE, file_ext_id)
                end_node = DirectRelationReference(
                    config.INSTANCE_SPACE, target_file_ext_id
                )

                edge_ext_id = (
                    file_ext_id + "-" + target_file_ext_id + "-" + str(uuid.uuid4())
                )
                edge_nodes.append(
                    EdgeApply(
                        space=config.INSTANCE_SPACE,
                        external_id=edge_ext_id,
                        sources=[source],
                        type=edge_type,
                        start_node=start_node,
                        end_node=end_node,
                    )
                )

        if edge_nodes:
            _log(
                f"Creating {len(edge_nodes)} file reference edges for file {file_ext_id}"
            )
            client.data_modeling.instances.apply(edge_nodes)
            created += len(edge_nodes)
            edge_nodes = []

    return created
