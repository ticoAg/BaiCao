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
  node_id?: string;
  snippet: string;
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

export interface SSECallbacks {
  onSession?: (sessionId: string) => void;
  onReasoning?: (chain: ReasoningStep[]) => void;
  onSources?: (sources: Source[]) => void;
  onToken?: (token: string) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
}
