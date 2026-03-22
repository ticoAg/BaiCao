# Task: IMPL-5 追问与上下文延续 (多轮对话)

## Implementation Summary

### Files Modified

- `packages/web/src/stores/chatStore.ts`: 新增 `conversationContext`、`isNewTopic` 状态和 `startNewTopic`、`setConversationContext` action；修改 `clearMessages` 同步重置新增字段
- `packages/web/src/hooks/useChat.ts`: 新增首次提问自动创建 session 逻辑；新增 session 过期(404)自动重建重试；从 store 解构并暴露 `startNewTopic`；返回值新增 `sessionId` 和 `startNewTopic`
- `packages/web/src/pages/ChatPage.tsx`: 引入 `Tag`、`Button`、`Tooltip`、`PlusOutlined`；从 `useChat` 解构 `sessionId` 和 `startNewTopic`；在标题栏右侧条件渲染"对话进行中"Tag 和"新话题"Button

### Content Added

- **`conversationContext: string | null`** (`chatStore.ts:8`): 存储对话上下文摘要，初始值 null，可供后续扩展使用
- **`isNewTopic: boolean`** (`chatStore.ts:9`): 标记是否为新话题，初始值 false
- **`startNewTopic()`** (`chatStore.ts:63`): 重置 `sessionId` 和 `conversationContext`，保留消息历史，设置 `isNewTopic: true`
- **`setConversationContext(ctx)`** (`chatStore.ts:34`): 更新上下文摘要的 action
- **自动 session 创建** (`useChat.ts:40-49`): `sendMessage` 执行前若 `sessionId` 为 null，先调用 `chatApi.createSession()` 获取并存储 sessionId
- **session 过期重试** (`useChat.ts:79-105`): catch 块检测 `err.response?.status === 404`，自动重建 session 并重试一次请求
- **`handleStartNewTopic()`** (`useChat.ts:138-144`): 封装 abort 中断 + `startNewTopic()` 调用
- **会话指示器 UI** (`ChatPage.tsx:58-73`): `sessionId` 存在时展示绿色"对话进行中"Tag 和"新话题"Button，流式响应中 Button disabled

## Outputs for Dependent Tasks

### Available Components

```typescript
// useChat hook 新增返回值
const { sessionId, startNewTopic } = useChat();

// chatStore 新增 state 和 actions
const { conversationContext, isNewTopic, startNewTopic, setConversationContext } = useChatStore();
```

### Integration Points

- **`startNewTopic`**: 调用后重置 `sessionId` 和 `conversationContext`，保留消息历史；下次 `sendMessage` 将自动创建新 session
- **`sessionId`**: 由 `useChat` 返回，可用于在任意组件中判断当前是否有活跃会话
- **`conversationContext`**: 预留字段，可在后续迭代中由后端返回并存储上下文摘要

### Usage Examples

```typescript
// 在组件中读取 session 状态并触发新话题
const { sessionId, startNewTopic, isStreaming } = useChat();

// 条件渲染会话状态
{sessionId && <Tag color="green">对话进行中</Tag>}
{sessionId && <Button onClick={startNewTopic} disabled={isStreaming}>新话题</Button>}
```

## Verification Results

| Check | Result |
|---|---|
| `vp build` exit code | 0 (pass) |
| `grep 'startNewTopic' chatStore.ts` | 2 hits (line 21, 63) |
| `grep 'createSession' useChat.ts` | 3 hits (line 43, 56, 81) |
| `grep '新话题' ChatPage.tsx` | 2 hits (line 61, 68) |
| `grep 'conversationContext' chatStore.ts` | 4 hits (lines 8, 27, 34, 61) |

## Status: Complete
