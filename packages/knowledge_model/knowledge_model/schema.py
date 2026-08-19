from typing import Annotated

from pydantic import Field

from .node_models import (
    AcupointNodeModel,
    ComponentNodeModel,
    DiseaseNodeModel,
    EvidenceNodeModel,
    EfficacyNodeModel,
    FlavorNodeModel,
    FormulaNodeModel,
    HerbNodeModel,
    MedicalCaseNodeModel,
    MeridianNodeModel,
    PreparedHerbNodeModel,
    SymptomNodeModel,
    TimePointNodeModel,
    TreatmentMethodNodeModel,
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
    | SymptomNodeModel
    | FormulaNodeModel
    | MedicalCaseNodeModel
    | AcupointNodeModel
    | TreatmentMethodNodeModel
    | TimePointNodeModel
    | EvidenceNodeModel,
    Field(discriminator="type"),
]
