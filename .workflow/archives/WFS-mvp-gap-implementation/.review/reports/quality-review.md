# Code Quality Review Report: WFS-mvp-gap-implementation

## 审查范围
- 13 个修改文件 + 15 个新建文件
- 审查维度：代码质量（复杂度、重复、类型安全、错误处理、命名、可读性）

## 统计

| Severity | Count |
|----------|-------|
| Critical | 1 |
| High | 12 |
| Medium | 10 |
| Low | 8 |
| **Total** | **31** |

---

## Top 3 优先修复

### 1. [CRITICAL] `ChatGraphData` 使用 `any` 类型
- **文件**: `packages/web/src/types/chat.ts:46-49`
- **问题**: `center: any; nodes: any[]; edges: any[]` 完全绕过 TypeScript 类型检查
- **修复**: 替换为 `center: GraphNode | null; nodes: GraphNode[]; edges: GraphEdge[]`

### 2. [HIGH] 状态常量三处重复
- **文件**: `EvidenceDetail.tsx`, `EvidenceList.tsx`, `LineageChain.tsx`
- **问题**: `statusColors` 和 `statusLabels` 在 3 个文件中完全重复
- **修复**: 提取到 `packages/web/src/types/provenance.ts` 共享

### 3. [HIGH] sendMessage 重试逻辑重复
- **文件**: `packages/web/src/hooks/useChat.ts:52-96`
- **问题**: "创建 session → 调用 API → 构建消息" 在两处几乎相同
- **修复**: 提取为 `executeChatRequest` 辅助函数

---

## 全部 Findings

### Critical (1)

| File | Line | Category | Title |
|------|------|----------|-------|
| types/chat.ts | 46-49 | type-safety | `ChatGraphData` 使用 `any` 类型，完全绕过 TS 类型系统 |

### High (12)

| File | Line | Category | Title |
|------|------|----------|-------|
| GraphPage.tsx | 72-140 | complexity | `g6Data` useMemo ~70 行 |
| GraphPage.tsx | 142-193 | complexity | `graphOptions` useMemo ~50 行 |
| GraphPage.tsx | 195-233 | complexity | `handleReady` callback ~40 行 |
| GraphPage.tsx | 252-487 | complexity | render 函数 ~235 行 |
| api.ts | 206-281 | complexity | SSE `stream` 函数 ~75 行 |
| useChat.ts | 26-117 | duplication | sendMessage 重试逻辑重复 |
| HerbDetailPage.tsx | 88-140 | duplication | Card 模式重复 6 次 |
| EvidenceDetail.tsx | 30-42 | duplication | statusColors/statusLabels 重复 (1/3) |
| EvidenceList.tsx | 26-38 | duplication | statusColors/statusLabels 重复 (2/3) |
| LineageChain.tsx | 30-51 | duplication | statusColors/statusLabels/statusIcon 重复 (3/3) |
| GraphPage.tsx | 34-40 | code-smell | 魔法字符串在内联样式中 |
| GraphPage.tsx | 146-149 | type-safety | `behaviors` 用 `any[]` |

### Medium (10)

| File | Line | Category | Title |
|------|------|----------|-------|
| api.ts | 68 | type-safety | `getPending` 返回 `any[]` |
| api.ts | 292 | type-safety | `getSession` 返回 `any` |
| useChat.ts | 55 | type-safety | `response as any` 断言 |
| HerbDetailPage.tsx | 258-288 | code-smell | evidence 用 `Record<string, unknown>` 强转 |
| PathExplorer.tsx | 38-40 | type-safety | `extractSteps` 不安全类型转换 |
| PathExplorer.tsx | 71-95 | duplication | fromSearch/toSearch 几乎相同 |
| LineageChain.tsx | 20-38 | code-smell | helper 函数用不安全属性访问 |
| MessageList.tsx | 32-46 | code-smell | helper 函数放置位置不佳 |
| GraphPage.tsx | 34-40 | code-smell | 魔法颜色值 |
| EvidenceDetail.tsx | 44 | code-smell | URL 验证可改进 |

### Low (8)

| File | Line | Category | Title |
|------|------|----------|-------|
| ReviewRequestModal.tsx | 50-52 | error-handling | 通用 catch 块 |
| EvidenceList.tsx | 17 | duplication | EvidenceItem 接口与 EvidenceDetailData 相似 |
| Header.tsx | 14-19 | code-smell | 路径匹配魔法字符串 |
| useProvenance.ts | 36-60 | complexity | 3 个并行查询 |
| ChatPage.tsx | 108-113 | duplication | 欢迎问题硬编码 |
| EntityHighlighter.tsx | 8-16 | duplication | labelColors 与 MessageList 重复 |
| MessageList.tsx | 16-23 | duplication | labelColors 重复定义 |
| notification.py | 29-39 | code-smell | from_model 可简化 |

---

## 无问题的文件

以下文件代码质量良好，无需修改：
- `packages/api/app/main.py`
- `packages/web/src/App.tsx`
- `packages/api/app/models/notification.py`
- `packages/web/src/stores/chatStore.ts`
- `packages/web/src/stores/notificationStore.ts`
- `packages/web/src/hooks/useHerbDetail.ts`
- `packages/web/src/hooks/useNotifications.ts`
- `packages/web/src/pages/HerbDetailPage.test.tsx`

---

## 建议执行顺序

1. **立即修复** (Critical): ChatGraphData `any` → 强类型 (5 分钟)
2. **本轮修复** (High): 状态常量提取 + useChat 重试逻辑去重 (20 分钟)
3. **后续迭代** (High): GraphPage 拆分子组件 (30 分钟)
4. **后续迭代** (Medium/Low): 类型安全改善 + 小型重复清理
