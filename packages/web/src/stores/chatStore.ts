// Chat 状态管理
import { create } from "zustand";
import type { Message, ReasoningStep, Source, ChatGraphData } from "../types/chat";

interface ChatState {
  messages: Message[];
  sessionId: string | null;
  conversationContext: string | null;
  isNewTopic: boolean;
  isStreaming: boolean;
  input: string;

  setInput: (input: string) => void;
  setSessionId: (id: string) => void;
  setConversationContext: (ctx: string | null) => void;
  setStreaming: (streaming: boolean) => void;
  addMessage: (message: Message) => void;
  appendToLastMessage: (token: string) => void;
  updateLastMessageContent: (updater: (msg: Message) => Partial<Message>) => void;
  clearMessages: () => void;
  startNewTopic: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  sessionId: null,
  conversationContext: null,
  isNewTopic: false,
  isStreaming: false,
  input: "",

  setInput: (input) => set({ input }),
  setSessionId: (id) => set({ sessionId: id }),
  setConversationContext: (ctx) => set({ conversationContext: ctx }),
  setStreaming: (streaming) => set({ isStreaming: streaming }),

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  appendToLastMessage: (token) =>
    set((state) => {
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === "assistant") {
        msgs[msgs.length - 1] = { ...last, content: last.content + token };
      }
      return { messages: msgs };
    }),

  updateLastMessageContent: (updater) =>
    set((state) => {
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === "assistant") {
        msgs[msgs.length - 1] = { ...last, ...updater(last) };
      }
      return { messages: msgs };
    }),

  clearMessages: () =>
    set({ messages: [], sessionId: null, conversationContext: null, isNewTopic: false }),

  startNewTopic: () =>
    set({ sessionId: null, conversationContext: null, isNewTopic: true }),
}));
