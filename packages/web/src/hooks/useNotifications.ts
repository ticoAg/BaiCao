// 通知轮询 hook
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notificationApi } from "../services/api";
import { useNotificationStore } from "../stores/notificationStore";
import { useEffect } from "react";

const POLL_INTERVAL = 30_000; // 30 秒轮询

export function useNotifications(userId = "anonymous") {
  const { setNotifications, markAsRead } = useNotificationStore();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["notifications", userId],
    queryFn: () => notificationApi.list({ user_id: userId, limit: 20 }),
    refetchInterval: POLL_INTERVAL,
    staleTime: 10_000,
  });

  useEffect(() => {
    if (data) {
      setNotifications(data.items, data.unread_count);
    }
  }, [data, setNotifications]);

  const { mutate: markReadMutate } = useMutation({
    mutationFn: (id: string) => notificationApi.markRead(id),
    onSuccess: (_, id) => {
      markAsRead(id);
      void queryClient.invalidateQueries({ queryKey: ["notifications", userId] });
    },
  });

  const notifications = useNotificationStore((s) => s.notifications);
  const unreadCount = useNotificationStore((s) => s.unreadCount);

  return {
    notifications,
    unreadCount,
    loading: isLoading,
    markAsRead: (id: string) => markReadMutate(id),
  };
}
