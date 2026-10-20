import os

from cognite.client.data_classes.data_modeling import ViewId

INSTANCE_SPACE = os.environ["INSTANCE_SPACE"]
DATA_MODEL_SPACE = os.environ["DATA_MODEL_SPACE"]
VIEW_VERSION = os.environ.get("VIEW_VERSION", "v1")
ASSET_PREFIX = os.environ.get("ASSET_PREFIX", "WMT:")

DIAGRAM_ANNOTATION_VIEW_ID = ViewId(
    space="cdf_cdm", external_id="CogniteDiagramAnnotation", version="v1"
)
ENERGY_ASSETS_VIEW_ID = ViewId(
    space=DATA_MODEL_SPACE, external_id="EnergyAsset", version=VIEW_VERSION
)
ENERGY_FILES_VIEW_ID = ViewId(
    space=DATA_MODEL_SPACE, external_id="EnergyFile", version=VIEW_VERSION
)
