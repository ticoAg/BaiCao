import axios from "axios";
import type {
  GraphWorkbenchLabelMetaItem,
  GraphWorkbenchMetaSummary,
  GraphWorkbenchPropertyKeyMetaItem,
  GraphWorkbenchRelationshipTypeMetaItem,
  GraphWorkbenchSchemaResponse,
} from "@bai-cao/shared";

const API_BASE = "/api/v1";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

type MetaListParams = {
  q?: string;
  limit?: number;
  offset?: number;
};

export const graphWorkbenchApi = {
  getMetaSummary: async (): Promise<GraphWorkbenchMetaSummary> => {
    const { data } = await api.get("/graph/meta/summary");
    return {
      nodeCount: data.node_count,
      relationshipCount: data.relationship_count,
      labelCount: data.label_count,
      relationshipTypeCount: data.relationship_type_count,
      propertyKeyCount: data.property_key_count,
      indexCount: data.index_count,
      constraintCount: data.constraint_count,
      truncated: data.truncated,
      generatedAt: data.generated_at,
    };
  },

  getMetaLabels: async (
    params?: MetaListParams,
  ): Promise<{ items: GraphWorkbenchLabelMetaItem[]; total: number }> => {
    const { data } = await api.get("/graph/meta/labels", { params });
    return {
      items: data.items.map((item: any) => ({
        name: item.name,
        count: item.count,
        propertyKeys: item.property_keys,
      })),
      total: data.total,
    };
  },

  getMetaRelationshipTypes: async (
    params?: MetaListParams,
  ): Promise<{ items: GraphWorkbenchRelationshipTypeMetaItem[]; total: number }> => {
    const { data } = await api.get("/graph/meta/relationship-types", { params });
    return {
      items: data.items.map((item: any) => ({
        name: item.name,
        count: item.count,
        propertyKeys: item.property_keys,
      })),
      total: data.total,
    };
  },

  getMetaPropertyKeys: async (
    params?: MetaListParams,
  ): Promise<{ items: GraphWorkbenchPropertyKeyMetaItem[]; total: number }> => {
    const { data } = await api.get("/graph/meta/property-keys", { params });
    return {
      items: data.items.map((item: any) => ({
        name: item.name,
        usedByLabels: item.used_by_labels,
        usedByRelationshipTypes: item.used_by_relationship_types,
      })),
      total: data.total,
    };
  },

  getMetaSchema: async (): Promise<GraphWorkbenchSchemaResponse> => {
    const { data } = await api.get("/graph/meta/schema");
    return {
      indexes: data.indexes.map((item: any) => ({
        name: item.name,
        type: item.type,
        entityType: item.entity_type,
        labelsOrTypes: item.labels_or_types,
        properties: item.properties,
        state: item.state,
      })),
      constraints: data.constraints.map((item: any) => ({
        name: item.name,
        type: item.type,
        entityType: item.entity_type,
        labelsOrTypes: item.labels_or_types,
        properties: item.properties,
      })),
    };
  },
};
