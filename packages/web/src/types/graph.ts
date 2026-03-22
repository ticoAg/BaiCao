// 图谱相关类型定义

import type { VerificationStatus } from "./index";

export interface GraphNode {
  id: string;
  name: string;
  source?: string;
  status: VerificationStatus;
  verification_id?: string;
  verified_by?: string;
  verified_at?: string;
  labels?: string[];
  category?: string;
  description?: string;
  latin_name?: string;
}

export interface GraphEdge {
  id?: string;
  status: VerificationStatus;
  verification_id?: string;
  verified_by?: string;
  verified_at?: string;
  rel_type?: string;
  source?: { id: string; name: string; labels?: string[]; status?: string };
  target?: { id: string; name: string; labels?: string[]; status?: string };
}

export interface GraphData {
  center: GraphNode | null;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export type GraphQueryPropertyKey =
  | "latin_name"
  | "category"
  | "description"
  | "chemical_formula"
  | "parent_herb"
  | "min_duration"
  | "conditions"
  | "trait_category"
  | "years"
  | "quality_indicator"
  | "nature"
  | "tcm_type"
  | "type";

export type GraphNodeLabel =
  | "Herb"
  | "Component"
  | "Variant"
  | "Process"
  | "Trait"
  | "Efficacy"
  | "Flavor"
  | "Meridian"
  | "Disease"
  | "TimePoint";

export type GraphEdgeRelType =
  | "CONTAINS"
  | "EXTRACTED_FROM"
  | "HAS_VARIANT"
  | "VARIANT_OF"
  | "PROCESSED_BY"
  | "APPLIES_TO"
  | "STORED_FOR"
  | "HAS_TRAIT"
  | "OBSERVED_IN"
  | "HAS_EFFICACY"
  | "HAS_FLAVOR"
  | "ENTERS_MERIDIAN"
  | "TREATS"
  | "INTERACTS_WITH"
  | "SIMILAR_TO"
  | "PARENT_OF"
  | "CHILD_OF"
  | "ORIGINATED_FROM";

export interface GraphQueryNodeFilters {
  name_contains?: string;
  label?: GraphNodeLabel;
  status?: VerificationStatus;
  source_contains?: string;
  property_key?: GraphQueryPropertyKey;
  property_value_contains?: string;
}

export interface GraphQueryEdgeFilters {
  rel_type?: GraphEdgeRelType;
  status?: VerificationStatus;
  connected_name_contains?: string;
}

export interface GraphQueryRequest {
  node?: GraphQueryNodeFilters;
  edge?: GraphQueryEdgeFilters;
  depth?: number;
  limit?: number;
}

export interface GraphQuerySummary {
  mode: string;
  matched_nodes: number;
  matched_edges: number;
  truncated: boolean;
  active_filters: string[];
}

export interface GraphQueryResponse {
  summary: GraphQuerySummary;
  graph: GraphData;
}

export interface SearchResult {
  node: GraphNode;
  labels: string[];
}

export type SelectedItem =
  | { type: "node"; data: GraphNode }
  | { type: "edge"; data: GraphEdge & { sourceName?: string; targetName?: string } };

// 路径探索相关类型
// 后端返回: { paths: [ { path: [ nodeDict, ... ] }, ... ] }
export interface PathItem {
  path: Record<string, unknown>[];
}

export interface PathResult {
  paths: PathItem[];
}

// 节点类型 G6 颜色映射（hex 值）
export const labelColorMap: Record<string, string> = {
  Herb: "#1677ff",
  Efficacy: "#52c41a",
  Flavor: "#fa8c16",
  Meridian: "#722ed1",
  Disease: "#f5222d",
  Component: "#13c2c2",
  Variant: "#2f54eb",
  Process: "#a0d911",
  Trait: "#fa541c",
  TimePoint: "#eb2f96",
};

// 节点类型 Ant Tag 颜色
export const labelTagColors: Record<string, string> = {
  Herb: "blue",
  Efficacy: "green",
  Flavor: "orange",
  Meridian: "purple",
  Disease: "red",
  Component: "cyan",
  Variant: "geekblue",
  Process: "lime",
  Trait: "volcano",
  TimePoint: "magenta",
};

export const defaultNodeColor = "#8c8c8c";

// Neo4j 风格三元色组：填充色 + 加深边框色 + 智能文字色
export const nodeStyleMap: Record<
  string,
  { fill: string; stroke: string; textColor: string }
> = {
  Herb: { fill: "#4C8EDA", stroke: "#2870c2", textColor: "#FFFFFF" },
  Efficacy: { fill: "#8DCC93", stroke: "#5db665", textColor: "#2A2C34" },
  Flavor: { fill: "#F79767", stroke: "#f36924", textColor: "#FFFFFF" },
  Meridian: { fill: "#C990C0", stroke: "#b261a5", textColor: "#FFFFFF" },
  Disease: { fill: "#F16667", stroke: "#eb2728", textColor: "#FFFFFF" },
  Component: { fill: "#57C7E3", stroke: "#23b3d7", textColor: "#2A2C34" },
  Variant: { fill: "#4C8EDA", stroke: "#2870c2", textColor: "#FFFFFF" },
  Process: { fill: "#D9C8AE", stroke: "#c0a378", textColor: "#2A2C34" },
  Trait: { fill: "#DA7194", stroke: "#cc3c6c", textColor: "#FFFFFF" },
  TimePoint: { fill: "#FFC454", stroke: "#d7a013", textColor: "#2A2C34" },
};

export const defaultNodeStyle = {
  fill: "#A5ABB6",
  stroke: "#9AA1AC",
  textColor: "#FFFFFF",
};

// 关系类型中文映射
export const relTypeLabels: Record<string, string> = {
  CONTAINS: "含有",
  TREATS: "主治",
  HAS_FLAVOR: "味",
  ENTERS_MERIDIAN: "归经",
  HAS_EFFICACY: "功效",
  HAS_COMPONENT: "成分",
  BELONGS_TO: "属于",
  VARIANT_OF: "变种",
  PROCESSED_BY: "炮制",
  HAS_TRAIT: "特征",
  HARVESTED_AT: "采收",
};
