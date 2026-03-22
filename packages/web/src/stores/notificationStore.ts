// 通知状态管理
import { create } from "zustand";
import type { Notification } from "../services/api";

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;

  setNotifications: (items: Notification[], unreadCount: number) => void;
  markAsRead: (id: string) => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  unreadCount: 0,

  setNotifications: (items, unreadCount) =>
    set({ notifications: items, unreadCount }),

  markAsRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n,
      ),
      unreadCount: Math.max(0, state.unreadCount - 1),
    })),
}));
