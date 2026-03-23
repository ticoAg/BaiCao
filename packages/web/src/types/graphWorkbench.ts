import type {
  GraphWorkbenchLabelMetaItem,
  GraphWorkbenchMetaSummary,
  GraphWorkbenchPropertyKeyMetaItem,
  GraphWorkbenchRelationshipTypeMetaItem,
  GraphWorkbenchSchemaResponse,
} from "@bai-cao/shared";
import type { SelectedItem } from "./graph";

export type GraphWorkbenchInspectorMode = "overview" | "details";

export interface GraphWorkbenchSelectionState {
  selectedItem: SelectedItem | null;
  hoveredItem: SelectedItem | null;
}

export interface GraphWorkbenchHighlightState {
  highlightedLabel: string | null;
  highlightedRelationshipType: string | null;
}

export interface GraphWorkbenchPanelState {
  isMetadataSidebarCollapsed: boolean;
  isInspectorCollapsed: boolean;
  inspectorMode: GraphWorkbenchInspectorMode;
}

export interface GraphWorkbenchMetaState {
  summary: GraphWorkbenchMetaSummary | null;
  labels: GraphWorkbenchLabelMetaItem[];
  relationshipTypes: GraphWorkbenchRelationshipTypeMetaItem[];
  propertyKeys: GraphWorkbenchPropertyKeyMetaItem[];
  schema: GraphWorkbenchSchemaResponse | null;
}
