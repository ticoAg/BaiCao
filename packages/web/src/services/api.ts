// API Service - 与后端通信
import axios from "axios";

const API_BASE = "/api/v1";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

// ============ Graph API ============

export interface GraphNode {
  id: string;
  name: string;
  source?: string;
  status: "pending" | "verified" | "rejected";
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
  status: "pending" | "verified" | "rejected";
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

export const graphApi = {
  // 获取药材图谱
  getHerbGraph: async (name: string, depth = 1): Promise<GraphData> => {
    const { data } = await api.get(`/graph/herb/${encodeURIComponent(name)}`, {
      params: { depth },
    });
    return data;
  },

  // 搜索节点
  search: async (q: string, label?: string, limit = 20): Promise<SearchResult[]> => {
    const { data } = await api.get("/graph/search", {
      params: { q, label, limit },
    });
    return data.items;
  },

  // 获取节点
  getNode: async (id: string): Promise<GraphNode> => {
    const { data } = await api.get(`/graph/node/${id}`);
    return data;
  },

  // 获取待验证项
  getPending: async (type: "nodes" | "relationships", limit = 50): Promise<any[]> => {
    const { data } = await api.get("/graph/pending", {
      params: { type, limit },
    });
    return data.items;
  },
};

// ============ Verification API ============

export interface Verification {
  id: string;
  entity_type: string;
  entity_id: string;
  field_name?: string;
  claimed_value: string;
  source_id?: string;
  status: "pending" | "verified" | "rejected";
  applicant_id: string;
  verifier_id?: string;
  verdict?: string;
  verified_at?: string;
  created_at: string;
}

export interface VerificationEvidence {
  source_id: string;
  quote: string;
  page_reference?: string;
  relevance_score?: number;
}

export const verificationApi = {
  // 创建验证申请
  create: async (params: {
    entity_type: string;
    entity_id: string;
    claimed_value: string;
    applicant_id?: string;
    source_id?: string;
    field_name?: string;
    evidence?: VerificationEvidence[];
  }): Promise<Verification> => {
    const { data } = await api.post("/verifications/", params);
    return data;
  },

  // 获取验证详情
  get: async (id: string): Promise<Verification> => {
    const { data } = await api.get(`/verifications/${id}`);
    return data;
  },

  // 列出验证申请
  list: async (params?: {
    status?: string;
    entity_type?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ items: Verification[]; total: number }> => {
    const { data } = await api.get("/verifications/", { params });
    return data;
  },

  // 专家审核
  verify: async (
    id: string,
    verifier_id: string | undefined,
    status: "verified" | "rejected",
    verdict: string,
  ): Promise<Verification> => {
    const { data } = await api.post(`/verifications/${id}/verify`, null, {
      params: { verifier_id, status, verdict },
    });
    return data;
  },
};

// ============ Herb API ============

export interface Herb {
  id: string;
  name: string;
  latin_name?: string;
  category: string;
  description?: string;
}

export const herbApi = {
  list: async (params?: {
    category?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ items: Herb[]; total: number }> => {
    const { data } = await api.get("/herbs/", { params });
    return data;
  },

  get: async (id: string): Promise<Herb> => {
    const { data } = await api.get(`/herbs/${id}`);
    return data;
  },

  search: async (name: string): Promise<Herb> => {
    const { data } = await api.get(`/herbs/search/${encodeURIComponent(name)}`);
    return data;
  },
};

// ============ Chat API ============

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

export const chatApi = {
  // 提问
  ask: async (question: string, sessionId?: string): Promise<ChatResponse> => {
    const { data } = await api.post("/chat/question", {
      question,
      session_id: sessionId,
    });
    return data;
  },

  // 创建会话
  createSession: async (userId?: string): Promise<{ id: string }> => {
    const { data } = await api.post("/chat/session", null, {
      params: { user_id: userId },
    });
    return data;
  },

  // 获取会话
  getSession: async (sessionId: string): Promise<any> => {
    const { data } = await api.get(`/chat/session/${sessionId}`);
    return data;
  },
};

export default api;
