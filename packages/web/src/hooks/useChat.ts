// Chat hook - SSE stream 消费
import { useCallback, useRef } from "react";
import { message } from "antd";
import { chatApi } from "../services/api";
import { useChatStore } from "../stores/chatStore";
import type { Message } from "../types/chat";

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

      try {
        const response = await chatApi.ask(question.trim(), sessionId || undefined);

        const assistantMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: response.answer,
          reasoningChain: response.reasoning_chain,
          sources: response.sources,
          graphData: response.graph_data,
        };

        addMessage(assistantMsg);

        if (response.session_id) {
          setSessionId(response.session_id);
        }
      } catch (err: any) {
        message.error(err.response?.data?.detail || "提问失败");
        addMessage({
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "抱歉，我遇到了一些问题，请稍后再试。",
        });
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

  return {
    messages,
    isStreaming,
    input,
    setInput,
    sendMessage,
    clearChat,
  };
}
