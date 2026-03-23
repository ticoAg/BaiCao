export interface GraphWorkbenchMetaSummary {
  nodeCount: number;
  relationshipCount: number;
  labelCount: number;
  relationshipTypeCount: number;
  propertyKeyCount: number;
  indexCount: number;
  constraintCount: number;
  truncated: boolean;
  generatedAt: string;
}

export interface GraphWorkbenchLabelMetaItem {
  name: string;
  count: number;
  propertyKeys: string[];
}

export interface GraphWorkbenchRelationshipTypeMetaItem {
  name: string;
  count: number;
  propertyKeys: string[];
}

export interface GraphWorkbenchPropertyKeyMetaItem {
  name: string;
  usedByLabels: string[];
  usedByRelationshipTypes: string[];
}

export interface GraphWorkbenchSchemaIndexItem {
  name?: string;
  type?: string;
  entityType?: string;
  labelsOrTypes: string[];
  properties: string[];
  state?: string;
}

export interface GraphWorkbenchSchemaConstraintItem {
  name?: string;
  type?: string;
  entityType?: string;
  labelsOrTypes: string[];
  properties: string[];
}

export interface GraphWorkbenchSchemaResponse {
  indexes: GraphWorkbenchSchemaIndexItem[];
  constraints: GraphWorkbenchSchemaConstraintItem[];
}

export interface GraphSceneInfo {
  truncated: boolean;
  nodeLimitHit: boolean;
  relationshipLimitHit: boolean;
  infoMessage?: string;
}
