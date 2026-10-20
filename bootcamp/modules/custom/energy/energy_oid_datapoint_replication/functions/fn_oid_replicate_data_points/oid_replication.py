from __future__ import annotations

import os
import random
from datetime import timedelta

from cognite.client import ClientConfig, CogniteClient
from cognite.client.credentials import OAuthClientCredentials
from cognite.client.data_classes.data_modeling import NodeId

OID_CDF_CLUSTER = "api"
OID_TENANT_ID = "48d5043c-cf70-4c49-881c-c638f5796997"
OID_CLIENT_ID = "1b90ede3-271e-401b-81a0-a4d52bea3273"
OID_PROJECT = "publicdata"

WEEK_OFFSET_MS = int(timedelta(weeks=1).total_seconds() * 1000)


def instance_space() -> str:
    return os.environ.get("INSTANCE_SPACE", "energy_time_series")


def oid_root_asset_external_id() -> str:
    return os.environ.get("OID_ROOT_ASSET_EXTERNAL_ID", "WMT:Aker BP")


def get_public_client(secret: str) -> CogniteClient:
    scopes = [f"https://{OID_CDF_CLUSTER}.cognitedata.com/.default"]
    token_url = f"https://login.microsoftonline.com/{OID_TENANT_ID}/oauth2/v2.0/token"
    base_url = f"https://{OID_CDF_CLUSTER}.cognitedata.com"

    creds = OAuthClientCredentials(
        token_url=token_url,
        client_id=OID_CLIENT_ID,
        scopes=scopes,
        client_secret=secret,
    )
    cnf = ClientConfig(
        client_name=OID_PROJECT,
        project=OID_PROJECT,
        credentials=creds,
        base_url=base_url,
    )
    return CogniteClient(cnf)


def update_time_series(
    client: CogniteClient,
    public_client: CogniteClient,
    start: str,
    external_ids: list[str],
) -> int:
    if not external_ids:
        return 0

    dps_list = public_client.time_series.data.retrieve(
        external_id=external_ids,
        start=start,
        end="168h-ago",
    )

    datapoint_count = sum(len(dps) for dps in dps_list)
    label = dps_list[0].external_id if len(dps_list) == 1 else "multiple external IDs"
    print(
        f"Inserting {datapoint_count} datapoints from OID since {start} for {label}"
    )

    space = instance_space()
    client.time_series.data.insert_multiple(
        datapoints=[
            {
                "instance_id": NodeId(space, external_id=dps.external_id),
                "datapoints": [
                    {
                        "timestamp": dp.timestamp + WEEK_OFFSET_MS,
                        "value": dp.value,
                    }
                    for dp in dps
                ],
            }
            for dps in dps_list
            if len(dps) > 0
        ]
    )
    return datapoint_count


def replicate_oid_datapoints(client: CogniteClient, oid_secret: str) -> dict[str, int | str]:
    public_client = get_public_client(oid_secret)
    ts_ext_ids = public_client.time_series.list(
        asset_subtree_external_ids=[oid_root_asset_external_id()],
        limit=None,
    ).as_external_ids()

    if not ts_ext_ids:
        print(
            f"No time series found under OID asset {oid_root_asset_external_id()!r}"
        )
        return {
            "status": "succeeded",
            "timeSeriesCount": 0,
            "recentDatapoints": 0,
            "backfillDatapoints": 0,
        }

    recent = update_time_series(client, public_client, "169h-ago", ts_ext_ids)
    backfill = update_time_series(
        client,
        public_client,
        "4w-ago",
        [random.choice(ts_ext_ids)],
    )

    return {
        "status": "succeeded",
        "timeSeriesCount": len(ts_ext_ids),
        "recentDatapoints": recent,
        "backfillDatapoints": backfill,
    }
