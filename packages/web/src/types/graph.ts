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

export interface GraphSceneInfo {
  truncated: boolean;
  node_limit_hit: boolean;
  relationship_limit_hit: boolean;
  info_message: string | null;
}

export interface HerbGraphResponse extends GraphData {
  scene: GraphSceneInfo;
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
  | "药材"
  | "成分"
  | "品种"
  | "工艺"
  | "性状"
  | "功效"
  | "性味"
  | "归经"
  | "病证"
  | "时间点";

export type GraphEdgeRelType =
  | "具有饮片"
  | "包含成分"
  | "提取自"
  | "具有品种"
  | "属于药材"
  | "经过工艺"
  | "适用于"
  | "储存时间"
  | "具有性状"
  | "观察于"
  | "具有功效"
  | "具有性味"
  | "归于经脉"
  | "治疗病证"
  | "相互作用"
  | "相似于"
  | "父类"
  | "子类"
  | "来源于"
  | "派生自"
  | "由证据支持";

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
  scene: GraphSceneInfo;
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

export const graphNodeLabelDisplayMap: Record<string, string> = {
  Herb: "药材",
  药材: "药材",
  PreparedHerb: "饮片",
  饮片: "饮片",
  Component: "成分",
  成分: "成分",
  Variant: "品种",
  品种: "品种",
  Process: "工艺",
  工艺: "工艺",
  Trait: "性状",
  性状: "性状",
  Efficacy: "功效",
  功效: "功效",
  Flavor: "性味",
  性味: "性味",
  Meridian: "归经",
  归经: "归经",
  Disease: "病证",
  病证: "病证",
  Formula: "方剂",
  方剂: "方剂",
  MedicalCase: "医案",
  医案: "医案",
  Acupoint: "穴位",
  穴位: "穴位",
  TreatmentMethod: "治法",
  治法: "治法",
  TimePoint: "时间点",
  时间点: "时间点",
  Source: "来源",
  来源: "来源",
  Evidence: "证据",
  证据: "证据",
  Unknown: "未知类型",
};

export function getGraphNodeLabelDisplayName(label?: string): string {
  return graphNodeLabelDisplayMap[label ?? ""] || label || graphNodeLabelDisplayMap.Unknown;
}

export function isHerbGraphLabel(label?: string): boolean {
  return getGraphNodeLabelDisplayName(label) === "药材";
}

export const graphPropertyLabels: Record<GraphQueryPropertyKey, string> = {
  latin_name: "拉丁名",
  category: "分类",
  description: "描述",
  chemical_formula: "化学式",
  parent_herb: "母本药材",
  min_duration: "最短时长",
  conditions: "条件",
  trait_category: "性状分类",
  years: "年份",
  quality_indicator: "质量指标",
  nature: "药性",
  tcm_type: "中医类型",
  type: "类型",
};

// 节点类型 G6 颜色映射（hex 值）
export const labelColorMap: Record<string, string> = {
  药材: "#1677ff",
  饮片: "#69b1ff",
  功效: "#52c41a",
  性味: "#fa8c16",
  归经: "#722ed1",
  病证: "#f5222d",
  成分: "#13c2c2",
  品种: "#2f54eb",
  工艺: "#a0d911",
  性状: "#fa541c",
  方剂: "#2f54eb",
  医案: "#13c2c2",
  穴位: "#eb2f96",
  治法: "#fa541c",
  时间点: "#eb2f96",
  来源: "#595959",
  证据: "#8c8c8c",
};

// 节点类型 Ant Tag 颜色
export const labelTagColors: Record<string, string> = {
  药材: "blue",
  功效: "green",
  性味: "orange",
  归经: "purple",
  病证: "red",
  成分: "cyan",
  品种: "geekblue",
  工艺: "lime",
  性状: "volcano",
  时间点: "magenta",
  来源: "default",
};

export const defaultNodeColor = "#8c8c8c";

export function getGraphNodeColor(label?: string): string {
  return labelColorMap[getGraphNodeLabelDisplayName(label)] || defaultNodeColor;
}

export function getGraphNodeTagColor(label?: string): string {
  return labelTagColors[getGraphNodeLabelDisplayName(label)] || "default";
}

// Neo4j 风格三元色组：填充色 + 加深边框色 + 智能文字色
export const nodeStyleMap: Record<
  string,
  { fill: string; stroke: string; textColor: string }
> = {
  药材: { fill: "#4C8EDA", stroke: "#2870c2", textColor: "#FFFFFF" },
  功效: { fill: "#8DCC93", stroke: "#5db665", textColor: "#2A2C34" },
  性味: { fill: "#F79767", stroke: "#f36924", textColor: "#FFFFFF" },
  归经: { fill: "#C990C0", stroke: "#b261a5", textColor: "#FFFFFF" },
  病证: { fill: "#F16667", stroke: "#eb2728", textColor: "#FFFFFF" },
  成分: { fill: "#57C7E3", stroke: "#23b3d7", textColor: "#2A2C34" },
  品种: { fill: "#4C8EDA", stroke: "#2870c2", textColor: "#FFFFFF" },
  工艺: { fill: "#D9C8AE", stroke: "#c0a378", textColor: "#2A2C34" },
  性状: { fill: "#DA7194", stroke: "#cc3c6c", textColor: "#FFFFFF" },
  时间点: { fill: "#FFC454", stroke: "#d7a013", textColor: "#2A2C34" },
  来源: { fill: "#A5ABB6", stroke: "#8d95a0", textColor: "#FFFFFF" },
};

export const defaultNodeStyle = {
  fill: "#A5ABB6",
  stroke: "#9AA1AC",
  textColor: "#FFFFFF",
};

export function getGraphNodeStyle(label?: string) {
  return nodeStyleMap[getGraphNodeLabelDisplayName(label)] || defaultNodeStyle;
}

// 关系类型中文映射
export const relTypeLabels: Record<string, string> = {
  具有饮片: "具有饮片",
  包含成分: "包含成分",
  提取自: "提取自",
  具有品种: "具有品种",
  属于药材: "属于药材",
  经过工艺: "经过工艺",
  适用于: "适用于",
  储存时间: "储存时间",
  具有性状: "具有性状",
  观察于: "观察于",
  具有功效: "具有功效",
  具有性味: "具有性味",
  归于经脉: "归于经脉",
  治疗病证: "治疗病证",
  相互作用: "相互作用",
  相似于: "相似于",
  父类: "父类",
  子类: "子类",
  来源于: "来源于",
  派生自: "派生自",
  由证据支持: "由证据支持",
};
