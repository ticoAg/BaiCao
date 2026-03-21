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
  center: GraphNode;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface SearchResult {
  node: GraphNode;
  labels: string[];
}

export type SelectedItem =
  | { type: "node"; data: GraphNode }
  | { type: "edge"; data: GraphEdge & { sourceName?: string; targetName?: string } };

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
