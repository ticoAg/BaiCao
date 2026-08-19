// 聊天相关类型定义

import type { GraphData, GraphNode, GraphEdge } from "./graph";
import type { WorkbenchFrame } from "./workbench";

export interface ReasoningStep {
  step: number;
  description: string;
  entities?: string[];
  relations?: string[];
  confidence?: number;
}

export interface Source {
  id: string;
  name: string;
  citation: string;
}

export interface Entity {
  name: string;
  type: string;
  id?: string;
}

export interface ChatResponse {
  answer: string;
  reasoning_chain: ReasoningStep[];
  sources: Source[];
  graph_data: GraphData;
  session_id: string;
  entities?: Entity[];
  workbench_frames?: WorkbenchFrame[];
}

export interface GraphAgentEvidence {
  entity_id?: string;
  evidence_id?: string;
  snippet: string;
  source_id?: string;
  source_name?: string;
  /** 旧字段，仅作展示回退，不得当作 lineage 实体 */
  node_id?: string;
}

export interface ChatReviewPrefill {
  entityType?: string;
  entityId?: string;
  content?: string;
  sourceId?: string;
}

/** lineage 只能用 entity_id，禁止把 source_id 当实体 */
export function getEvidenceEntityId(evidence: GraphAgentEvidence): string | undefined {
  const entityId = evidence.entity_id?.trim();
  return entityId ? entityId : undefined;
}

export function getEvidenceSourceLabel(evidence: GraphAgentEvidence): string {
  const sourceName = evidence.source_name?.trim();
  return sourceName ? sourceName : "来源未标注";
}

export interface GraphAgentSubgraphMeta {
  center_node_id: string | null;
  actual_depth: number;
  fallback_used: boolean;
  node_count: number;
  edge_count: number;
}

export interface GraphAgentReasoningTraceItem {
  kind?: string;
  summary: string;
}

export interface GraphAgentToolCall {
  call_id?: string;
  tool_name: string;
  arguments?: Record<string, unknown>;
  summary: string;
  result_summary?: string | null;
  status?: string;
}

export interface GraphAgentResponse {
  answer: string;
  evidence: GraphAgentEvidence[];
  related_nodes: Array<Partial<GraphNode> & { id?: string; name?: string }>;
  related_edges: Array<
    Partial<GraphEdge> & {
      type?: string;
      source?: string | { id?: string; name?: string; labels?: string[]; status?: string };
      target?: string | { id?: string; name?: string; labels?: string[]; status?: string };
    }
  >;
  subgraph_meta: GraphAgentSubgraphMeta;
  reasoning_trace: GraphAgentReasoningTraceItem[];
  tool_calls: GraphAgentToolCall[];
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  reasoningChain?: ReasoningStep[];
  sources?: Source[];
  graphData?: ChatGraphData;
  entities?: Entity[];
  workbenchFrames?: WorkbenchFrame[];
  evidence?: GraphAgentEvidence[];
  subgraphMeta?: GraphAgentSubgraphMeta;
  reasoningTrace?: GraphAgentReasoningTraceItem[];
  toolCalls?: GraphAgentToolCall[];
  providerReasoning?: ChatAgentProviderReasoningChunk[];
}

// chat 上下文中的 graph 数据（后端返回字段可能不完整，用 Partial）
export interface ChatGraphData {
  center:
    | (Partial<GraphNode> & {
        name: string;
        labels?: string[];
        status?: string;
      })
    | null;
  nodes: Partial<GraphNode>[];
  edges: Partial<GraphEdge>[];
}

export interface ChatAgentProviderReasoningChunk {
  id?: string;
  text: string;
}

export interface ChatAgentToolStartEvent {
  call_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
}

export interface ChatAgentToolResultEvent {
  call_id: string;
  tool_name: string;
  result_summary: string;
  payload_preview?: Record<string, unknown> | null;
}

export interface ChatAgentSubgraphPatchEvent {
  nodes?: Array<Partial<GraphNode> & { id?: string; name?: string }>;
  edges?: Partial<GraphEdge>[];
  center_node_id?: string | null;
}

export interface ChatAgentFinalPayload extends GraphAgentResponse {
  provider_reasoning: ChatAgentProviderReasoningChunk[];
  session_id: string;
}

export interface ChatAgentSSECallbacks {
  onSession?: (sessionId: string, turnId?: string) => void;
  onProviderReasoning?: (chunk: ChatAgentProviderReasoningChunk) => void;
  onToolStart?: (event: ChatAgentToolStartEvent) => void;
  onToolResult?: (event: ChatAgentToolResultEvent) => void;
  onSubgraphPatch?: (patch: ChatAgentSubgraphPatchEvent) => void;
  onAnswerChunk?: (text: string) => void;
  onFinal?: (payload: ChatAgentFinalPayload) => void;
  onError?: (message: string) => void;
}

export type SSECallbacks = ChatAgentSSECallbacks;
