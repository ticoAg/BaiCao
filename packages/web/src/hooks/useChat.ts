// Chat hook - graph runtime agent 消费
import { useCallback, useRef } from "react";
import { message } from "antd";
import { graphAgentApi } from "../services/api";
import { useChatStore } from "../stores/chatStore";
import type {
  ChatGraphData,
  Entity,
  GraphAgentResponse,
  Message,
} from "../types/chat";
import type { GraphEdge, GraphNode } from "../types/graph";

type RawGraphAgentEdge = GraphAgentResponse["related_edges"][number];

const validStatuses = new Set(["pending", "verified", "rejected"]);

function normalizeStatus(status: unknown): GraphNode["status"] {
  return typeof status === "string" && validStatuses.has(status)
    ? (status as GraphNode["status"])
    : "pending";
}

function normalizeLabels(labels: unknown): string[] {
  return Array.isArray(labels) ? labels.map(String) : [];
}

function normalizeNode(node: Partial<GraphNode> & { id?: string; name?: string }): GraphNode | null {
  const id = node.id ?? node.name;
  const name = node.name ?? node.id;
  if (!id || !name) return null;

  return {
    ...node,
    id: String(id),
    name: String(name),
    status: normalizeStatus(node.status),
    labels: normalizeLabels(node.labels),
  };
}

function getEndpointRef(value: RawGraphAgentEdge["source"] | RawGraphAgentEdge["target"]) {
  if (typeof value === "string") {
    return { id: value, name: value, labels: [] };
  }
  if (value && typeof value === "object") {
    const id = value.id ?? value.name;
    const name = value.name ?? value.id;
    return {
      id: id ? String(id) : "",
      name: name ? String(name) : "",
      labels: normalizeLabels(value.labels),
      status: normalizeStatus(value.status),
    };
  }
  return { id: "", name: "", labels: [] };
}

function normalizeGraphData(response: GraphAgentResponse): ChatGraphData {
  const nodeMap = new Map<string, GraphNode>();

  response.related_nodes
    .map(normalizeNode)
    .filter((node): node is GraphNode => Boolean(node))
    .forEach((node) => nodeMap.set(node.id, node));

  const edges: GraphEdge[] = response.related_edges.map((edge, index) => {
    const sourceRef = getEndpointRef(edge.source);
    const targetRef = getEndpointRef(edge.target);

    [sourceRef, targetRef].forEach((ref) => {
      if (ref.id && !nodeMap.has(ref.id)) {
        nodeMap.set(ref.id, {
          id: ref.id,
          name: ref.name || ref.id,
          labels: ref.labels,
          status: ref.status ?? "pending",
        });
      }
    });

    return {
      ...edge,
      id: edge.id ? String(edge.id) : `graph-agent-edge-${index}`,
      status: normalizeStatus(edge.status),
      rel_type: edge.rel_type || edge.type || "相关",
      source: sourceRef.id
        ? {
            id: sourceRef.id,
            name: nodeMap.get(sourceRef.id)?.name ?? sourceRef.name,
            labels: nodeMap.get(sourceRef.id)?.labels,
            status: nodeMap.get(sourceRef.id)?.status,
          }
        : undefined,
      target: targetRef.id
        ? {
            id: targetRef.id,
            name: nodeMap.get(targetRef.id)?.name ?? targetRef.name,
            labels: nodeMap.get(targetRef.id)?.labels,
            status: nodeMap.get(targetRef.id)?.status,
          }
        : undefined,
    };
  });

  const nodes = Array.from(nodeMap.values());
  const center =
    nodes.find((node) => node.id === response.subgraph_meta.center_node_id) ??
    nodes[0] ??
    null;

  return {
    center,
    nodes,
    edges,
  };
}

function extractEntities(graphData: ChatGraphData): Entity[] {
  return graphData.nodes.slice(0, 8).map((node) => ({
    id: node.id,
    name: node.name ?? node.id ?? "",
    type: node.labels?.[0] ?? "GraphNode",
  }));
}

function createLocalSessionId() {
  return globalThis.crypto?.randomUUID?.() ?? `graph-agent-${Date.now()}`;
}

/** 从 GraphAgentResponse 构建 assistant Message */
function buildAssistantMessage(response: GraphAgentResponse): Message {
  const graphData = normalizeGraphData(response);

  return {
    id: (Date.now() + 1).toString(),
    role: "assistant",
    content: response.answer,
    graphData,
    entities: extractEntities(graphData),
    evidence: response.evidence,
    subgraphMeta: response.subgraph_meta,
    reasoningTrace: response.reasoning_trace,
    toolCalls: response.tool_calls,
  };
}

/** 展示错误并添加错误消息 */
function showErrorMessage(err: unknown, addMessage: (msg: Message) => void) {
  const detail =
    (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "提问失败";
  message.error(detail);
  addMessage({
    id: (Date.now() + 1).toString(),
    role: "assistant",
    content: "抱歉，我遇到了一些问题，请稍后再试。",
  });
}

export function useChat() {
  const {
    messages,
    sessionId,
    isStreaming,
    input,
    setInput,
    setSessionId,
    setStreaming,
    addMessage,
    clearMessages,
    startNewTopic,
  } = useChatStore();

  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (question: string) => {
      if (!question.trim() || isStreaming) return;

      const userMsg: Message = {
        id: Date.now().toString(),
        role: "user",
        content: question.trim(),
      };
      addMessage(userMsg);
      setInput("");
      setStreaming(true);

      if (!sessionId) {
        setSessionId(createLocalSessionId());
      }

      try {
        const response = await graphAgentApi.ask(question.trim());
        addMessage(buildAssistantMessage(response));
      } catch (err: unknown) {
        showErrorMessage(err, addMessage);
      } finally {
        setStreaming(false);
      }
    },
    [
      isStreaming,
      sessionId,
      addMessage,
      setInput,
      setStreaming,
      setSessionId,
    ],
  );

  const clearChat = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    clearMessages();
  }, [clearMessages]);

  const handleStartNewTopic = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    startNewTopic();
  }, [startNewTopic]);

  return {
    messages,
    sessionId,
    isStreaming,
    input,
    setInput,
    sendMessage,
    clearChat,
    startNewTopic: handleStartNewTopic,
  };
}
