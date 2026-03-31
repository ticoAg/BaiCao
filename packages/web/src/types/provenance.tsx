// 溯源相关共享常量与类型
import { CheckCircleOutlined, ClockCircleOutlined, ExclamationCircleOutlined } from "@ant-design/icons";
import type { ReactNode } from "react";
import { getGraphNodeLabelDisplayName } from "./graph";

/** 证据/溯源状态颜色映射 */
export const statusColors: Record<string, string> = {
  verified: "green",
  pending: "gold",
  rejected: "red",
  draft: "default",
};

/** 证据/溯源状态中文标签映射 */
export const statusLabels: Record<string, string> = {
  verified: "已验证",
  pending: "待验证",
  rejected: "已拒绝",
  draft: "草稿",
};

/** 证据/溯源状态图标映射 */
export function statusIcon(status: string): ReactNode | null {
  switch (status) {
    case "verified":
      return <CheckCircleOutlined style={{ color: "#52c41a" }} />;
    case "pending":
      return <ClockCircleOutlined style={{ color: "#faad14" }} />;
    case "rejected":
      return <ExclamationCircleOutlined style={{ color: "#ff4d4f" }} />;
    default:
      return null;
  }
}

/** 从 Record 节点提取名称 */
export function getNodeName(node: Record<string, unknown>): string {
  if (typeof node.name === "string") return node.name;
  if (typeof node.title === "string") return node.title;
  if (typeof node.id === "string") return node.id;
  return "未知";
}

/** 从 Record 节点提取类型 */
export function getNodeType(node: Record<string, unknown>): string {
  if (typeof node.type === "string") return getGraphNodeLabelDisplayName(node.type);
  if (Array.isArray(node.labels) && node.labels.length > 0) {
    return getGraphNodeLabelDisplayName(String(node.labels[0]));
  }
  return "";
}

/** 从 Record 节点提取状态 */
export function getNodeStatus(node: Record<string, unknown>): string {
  if (typeof node.status === "string") return node.status;
  return "";
}

/** 证据项公共接口 */
export interface EvidenceItemBase {
  id: string;
  content: string;
  source_name: string;
  page_reference?: string;
  status: string;
  [key: string]: unknown;
}
