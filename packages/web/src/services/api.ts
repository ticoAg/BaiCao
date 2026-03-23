// API Service - 与后端通信
import axios from "axios";
import type { ReasoningStep, Source, ChatResponse, SSECallbacks } from "../types/chat";
import type {
  GraphData,
  GraphNode,
  GraphEdge,
  HerbGraphResponse,
  SearchResult,
  GraphQueryRequest,
  GraphQueryResponse,
  PathResult,
} from "../types/graph";

// 从 types/ 重新导出，保持向后兼容
export type {
  GraphNode,
  GraphEdge,
  GraphData,
  HerbGraphResponse,
  SearchResult,
  GraphQueryRequest,
  GraphQueryResponse,
  PathResult,
} from "../types/graph";
export type { ReasoningStep, Source, ChatResponse, SSECallbacks } from "../types/chat";
export type { VerificationStatus } from "../types/index";

const API_BASE = "/api/v1";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

// ============ Graph API ============

export const graphApi = {
  // 获取药材图谱
  getHerbGraph: async (name: string, depth = 1): Promise<HerbGraphResponse> => {
    const { data } = await api.get(`/graph/herb/${encodeURIComponent(name)}`, {
      params: { depth },
    });
    return data;
  },

  // 高级图谱查询
  queryGraph: async (payload: GraphQueryRequest): Promise<GraphQueryResponse> => {
    const { data } = await api.post("/graph/query", payload);
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

  // 按节点展开一跳邻居子图
  expandNodeGraph: async (id: string, depth = 1, limit = 20): Promise<GraphData> => {
    const { data } = await api.get(`/graph/node/${id}/expand`, {
      params: { depth, limit },
    });
    return data;
  },

  // 获取待验证项
  getPending: async (type: "nodes" | "relationships", limit = 50): Promise<{ items: GraphNode[]; total: number }> => {
    const { data } = await api.get("/graph/pending", {
      params: { type, limit },
    });
    return data;
  },

  // 查找两节点之间的路径
  getPath: async (fromName: string, toName: string, maxDepth = 4): Promise<PathResult> => {
    const { data } = await api.get("/graph/path", {
      params: { from_name: fromName, to_name: toName, max_depth: maxDepth },
    });
    return data;
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
  alias?: string[];
  efficacy?: string[];
  flavor?: string[];
  meridian?: string[];
  dosage?: string;
  contraindications?: string;
  created_at?: string;
  updated_at?: string;
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

export const chatApi = {
  // 同步提问
  ask: async (question: string, sessionId?: string): Promise<ChatResponse> => {
    const { data } = await api.post("/chat/question", {
      question,
      session_id: sessionId,
    });
    return data;
  },

  // SSE 流式提问 - 返回 ReadableStream
  stream: (
    question: string,
    sessionId?: string,
    callbacks?: SSECallbacks,
  ): AbortController => {
    const controller = new AbortController();

    fetch(`${API_BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, session_id: sessionId }),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok || !response.body) {
          callbacks?.onError?.(`HTTP ${response.status}`);
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let currentEvent = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) {
              currentEvent = line.slice(7);
            } else if (line.startsWith("data: ") && currentEvent) {
              try {
                const data = JSON.parse(line.slice(6));
                switch (currentEvent) {
                  case "session":
                    callbacks?.onSession?.(data.session_id);
                    break;
                  case "reasoning":
                    callbacks?.onReasoning?.(data.reasoning_chain);
                    break;
                  case "sources":
                    callbacks?.onSources?.(data.sources);
                    break;
                  case "token":
                    callbacks?.onToken?.(data.token);
                    break;
                  case "done":
                    callbacks?.onDone?.();
                    break;
                  case "error":
                    callbacks?.onError?.(data.message);
                    break;
                }
              } catch {
                // skip malformed JSON
              }
              currentEvent = "";
            }
          }
        }

        callbacks?.onDone?.();
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          callbacks?.onError?.(err.message);
        }
      });

    return controller;
  },

  // 创建会话
  createSession: async (userId?: string): Promise<{ id: string }> => {
    const { data } = await api.post("/chat/session", null, {
      params: { user_id: userId },
    });
    return data;
  },

  // 获取会话
  getSession: async (sessionId: string): Promise<{ id: string; messages: unknown[]; created_at?: string }> => {
    const { data } = await api.get(`/chat/session/${sessionId}`);
    return data;
  },
};

// ============ Provenance API ============

export interface ProvenanceEvidence {
  id: string;
  content: string;
  source_name: string;
  page_reference?: string;
  status: string;
}

export interface LineageChain {
  entity: Record<string, unknown>;
  evidence: Record<string, unknown>;
  source: Record<string, unknown>;
}

export const provenanceApi = {
  createEvidence: async (params: {
    content: string;
    source_name: string;
    page_reference?: string;
  }): Promise<ProvenanceEvidence> => {
    const { data } = await api.post("/provenance/evidence", params);
    return data;
  },

  getEvidence: async (id: string): Promise<ProvenanceEvidence> => {
    const { data } = await api.get(`/provenance/evidence/${id}`);
    return data;
  },

  linkSource: async (
    evidenceId: string,
    sourceId: string,
  ): Promise<{ relationship: Record<string, unknown>; message: string }> => {
    const { data } = await api.post(
      `/provenance/evidence/${evidenceId}/link-source`,
      { source_id: sourceId },
    );
    return data;
  },

  getEntityLineage: async (entityId: string): Promise<LineageChain> => {
    const { data } = await api.get(`/provenance/entity/${entityId}/lineage`);
    return data;
  },

  getSourceDerivations: async (
    sourceId: string,
  ): Promise<{ derivations: LineageChain[]; count: number }> => {
    const { data } = await api.get(
      `/provenance/source/${sourceId}/derivations`,
    );
    return data;
  },

  getEntityEvidence: async (
    entityId: string,
  ): Promise<{ evidence: Record<string, unknown>[]; count: number }> => {
    const { data } = await api.get(
      `/provenance/entity/${entityId}/evidence`,
    );
    return data;
  },

  checkCompleteness: async (
    entityId: string,
  ): Promise<{
    entity: Record<string, unknown>;
    has_evidence: boolean;
    has_source: boolean;
    chain_complete: boolean;
  }> => {
    const { data } = await api.get(
      `/provenance/entity/${entityId}/completeness`,
    );
    return data;
  },
};

// ============ Notification API ============

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  content?: {
    message?: string;
    link?: string;
    verdict?: string;
  };
  read: boolean;
  created_at: string;
}

export const notificationApi = {
  list: async (params?: {
    user_id?: string;
    unread_only?: boolean;
    limit?: number;
  }): Promise<{ items: Notification[]; total: number; unread_count: number }> => {
    const { data } = await api.get("/notifications/", { params });
    return data;
  },

  markRead: async (id: string): Promise<{ id: string; read: boolean }> => {
    const { data } = await api.post(`/notifications/${id}/read`);
    return data;
  },
};

export default api;
