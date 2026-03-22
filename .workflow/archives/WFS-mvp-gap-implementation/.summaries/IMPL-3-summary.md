# Task: IMPL-3 答案实体高亮 + 溯源按钮 (MessageList 集成)

## Implementation Summary

### Files Modified

- `packages/web/src/types/chat.ts`: 新增 `Entity` 接口，在 `Message` 和 `ChatResponse` 中新增 `entities?` 字段
- `packages/web/src/hooks/useChat.ts`: assistantMsg 构建新增 `entities: response.entities` 映射
- `packages/web/src/components/chat/MessageList.tsx`: 重构为有状态组件，集成 EntityHighlighter、ProvenanceDrawer、EvidenceList、LineageChain
- `packages/web/src/components/chat/EntityHighlighter.tsx`: 新建文件

### Content Added

- **Entity** (`packages/web/src/types/chat.ts:19-23`): 实体类型接口 `{ name: string; type: string; id?: string }`
- **EntityHighlighter** (`packages/web/src/components/chat/EntityHighlighter.tsx`): 将纯文本 + entities 列表转为高亮可点击 Tag 的组件
  - Props: `{ content: string; entities?: Entity[] }`
  - 文本解析：按实体名长度降序排列后用正则切分，生成 Segment 列表
  - 点击行为：`Herb` 类型导航至 `/herb/:id`，其他类型导航至 `/graph/:name`
- **ProvenanceDrawer** (`packages/web/src/components/chat/MessageList.tsx:54-86`): Ant Design Drawer 封装，内嵌 LineageChain + EvidenceList
  - Props: `{ entityId?, entityName?, open, onClose }`
  - 通过 `useProvenance(entityId, { enabled: open && !!entityId })` 懒加载数据
- **extractEntitiesFromSources** (`packages/web/src/components/chat/MessageList.tsx:39-46`): fallback helper，当 `msg.entities` 为空时从 sources 中构造 Herb 类型实体列表
- **renderSources** (MessageList 内部方法): 增加"查看溯源" Button，点击打开 ProvenanceDrawer

## Outputs for Dependent Tasks

### Available Components

```typescript
// EntityHighlighter - 实体高亮渲染
import EntityHighlighter from 'packages/web/src/components/chat/EntityHighlighter';
// <EntityHighlighter content={text} entities={entities} />

// Entity 类型
import type { Entity } from 'packages/web/src/types/chat';
```

### Integration Points

- **Entity 类型**: `packages/web/src/types/chat.ts` 中导出 `Entity`，可在任何需要实体结构的地方复用
- **useProvenance**: `entityId` 驱动查询，`enabled` 参数支持按需懒加载
- **MessageList**: 已集成完整溯源链路，IMPL-7（提交审查）可在 `renderSources` 区域附近新增按钮

### Usage Examples

```typescript
// 实体高亮
<EntityHighlighter content="陈皮具有健脾化痰的功效" entities={[{ name: "陈皮", type: "Herb", id: "herb_1" }]} />

// 溯源 Drawer（已内嵌于 MessageList，按需也可独立使用）
<ProvenanceDrawer entityId="herb_1" entityName="陈皮" open={open} onClose={() => setOpen(false)} />
```

## Verification Results

| 验收项 | 结果 |
|--------|------|
| EntityHighlighter.tsx 文件存在 | PASS |
| MessageList 不再直接渲染 msg.content 纯文本 | PASS (EntityHighlighter 替代) |
| Message 类型新增 entities 字段 | PASS (3 处命中) |
| "查看溯源"按钮存在 | PASS |
| 实体点击导航逻辑存在 | PASS (navigate /herb + /graph) |
| EvidenceList + LineageChain 被导入使用 | PASS (4 处命中) |
| vp build 无编译错误 | PASS (exit 0) |

## Status: Complete
