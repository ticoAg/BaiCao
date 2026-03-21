// 聊天相关类型定义

import type { GraphData } from "./graph";

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

export interface ChatResponse {
  answer: string;
  reasoning_chain: ReasoningStep[];
  sources: Source[];
  graph_data: GraphData;
  session_id: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  reasoningChain?: ReasoningStep[];
  sources?: Source[];
  graphData?: ChatGraphData;
}

// chat 上下文中简化的 graph 数据（center 可能缺少完整字段）
export interface ChatGraphData {
  center: any;
  nodes: any[];
  edges: any[];
}

export interface SSECallbacks {
  onSession?: (sessionId: string) => void;
  onReasoning?: (chain: ReasoningStep[]) => void;
  onSources?: (sources: Source[]) => void;
  onToken?: (token: string) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
}
