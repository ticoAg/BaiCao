# IMPL-8 Summary: 审查结果通知

## 状态: completed

## 完成的工作

### 新增文件
**后端:**
- `packages/api/app/models/notification.py` — Notification SQLAlchemy model (id/user_id/type/title/content/read/created_at)
- `packages/api/app/api/notification.py` — 2 个端点: GET /notifications/ (列表+未读数) / POST /notifications/{id}/read

**前端:**
- `packages/web/src/stores/notificationStore.ts` — Zustand store (notifications/unreadCount/setNotifications/markAsRead)
- `packages/web/src/hooks/useNotifications.ts` — TanStack Query hook，30秒轮询 (refetchInterval: 30_000)
- `packages/web/src/components/NotificationBell.tsx` — 铃铛图标 + Badge 未读数 + Popover 通知面板，点击通知跳转

### 修改文件
- `packages/api/app/main.py` — 注册 notification_router
- `packages/web/src/services/api.ts` — 新增 notificationApi (list/markRead)
- `packages/web/src/components/Header.tsx` — 集成 NotificationBell

## 功能验证
```bash
ruff check packages/api/app/api/notification.py packages/api/app/models/notification.py  # All checks passed
vp build  # exit 0
grep 'notificationApi' packages/web/src/services/api.ts  # 命中
grep 'NotificationBell' packages/web/src/components/Header.tsx  # 命中
grep 'refetchInterval' packages/web/src/hooks/useNotifications.ts  # 命中
```

## US 覆盖
- US-012: 审查结果通知 ✅（轮询方案，通知面板显示结论/链接/跳转）
