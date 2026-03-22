// Chat hook - SSE stream 消费
import { useCallback, useRef } from "react";
import { message } from "antd";
import { chatApi } from "../services/api";
import { useChatStore } from "../stores/chatStore";
import type { Message, ChatResponse } from "../types/chat";

/** 从 ChatResponse 构建 assistant Message */
function buildAssistantMessage(response: ChatResponse): Message {
  return {
    id: (Date.now() + 1).toString(),
    role: "assistant",
    content: response.answer,
    reasoningChain: response.reasoning_chain,
    sources: response.sources,
    graphData: response.graph_data,
    entities: response.entities,
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
    appendToLastMessage,
    updateLastMessageContent,
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

      // 首次提问时自动创建 session
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        try {
          const session = await chatApi.createSession();
          currentSessionId = session.id;
          setSessionId(currentSessionId);
        } catch {
          // 创建 session 失败则不携带 sessionId 继续
        }
      }

      /** 重建 session 后重试一次 */
      const retryWithNewSession = async (): Promise<ChatResponse> => {
        const session = await chatApi.createSession();
        currentSessionId = session.id;
        setSessionId(currentSessionId);
        return chatApi.ask(question.trim(), currentSessionId);
      };

      try {
        const response = await chatApi.ask(question.trim(), currentSessionId || undefined);
        addMessage(buildAssistantMessage(response));
        if (response.session_id) setSessionId(response.session_id);
      } catch (err: unknown) {
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (status === 404) {
          // session 过期 → 重建并重试一次
          try {
            const retryResponse = await retryWithNewSession();
            addMessage(buildAssistantMessage(retryResponse));
            if (retryResponse.session_id) setSessionId(retryResponse.session_id);
          } catch (retryErr) {
            showErrorMessage(retryErr, addMessage);
          }
        } else {
          showErrorMessage(err, addMessage);
        }
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
      updateLastMessageContent,
      appendToLastMessage,
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
