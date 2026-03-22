// 聊天相关类型定义

import type { GraphData, GraphNode, GraphEdge } from "./graph";

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
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  reasoningChain?: ReasoningStep[];
  sources?: Source[];
  graphData?: ChatGraphData;
  entities?: Entity[];
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
