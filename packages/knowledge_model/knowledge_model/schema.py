from typing import Annotated

from pydantic import Field

from .node_models import (
    ComponentNodeModel,
    DiseaseNodeModel,
    EfficacyNodeModel,
    FlavorNodeModel,
    HerbNodeModel,
    MeridianNodeModel,
    TimePointNodeModel,
    VariantNodeModel,
)


GraphNodeModel = Annotated[
    HerbNodeModel
    | ComponentNodeModel
    | VariantNodeModel
    | EfficacyNodeModel
    | FlavorNodeModel
    | MeridianNodeModel
    | DiseaseNodeModel
    | TimePointNodeModel,
    Field(discriminator="type"),
]
