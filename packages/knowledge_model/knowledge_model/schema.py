from typing import Annotated

from pydantic import Field

from .node_models import (
    ComponentNodeModel,
    DiseaseNodeModel,
    EvidenceNodeModel,
    EfficacyNodeModel,
    FlavorNodeModel,
    HerbNodeModel,
    MeridianNodeModel,
    PreparedHerbNodeModel,
    TimePointNodeModel,
    VariantNodeModel,
)


GraphNodeModel = Annotated[
    HerbNodeModel
    | PreparedHerbNodeModel
    | ComponentNodeModel
    | VariantNodeModel
    | EfficacyNodeModel
    | FlavorNodeModel
    | MeridianNodeModel
    | DiseaseNodeModel
    | TimePointNodeModel
    | EvidenceNodeModel,
    Field(discriminator="type"),
]
