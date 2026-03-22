# Task: IMPL-6 关系路径探索 UI (GraphPage 增强)

## Implementation Summary

### Files Modified
- `packages/web/src/types/graph.ts`: 新增 PathItem 和 PathResult 类型定义
- `packages/web/src/services/api.ts`: 导入 PathResult 类型，在 graphApi 新增 getPath 方法，重新导出 PathResult
- `packages/web/src/pages/GraphPage.tsx`: 导入 Collapse 和 PathExplorer，在左侧面板 GraphQueryPanel 下方集成路径探索区块

### Files Created
- `packages/web/src/components/graph/PathExplorer.tsx`: 路径探索面板组件

### Content Added

#### Types (`packages/web/src/types/graph.ts:125-133`)
- **PathItem**: `{ path: Record<string, unknown>[] }` - 单条路径，path 数组为后端 Neo4j path 序列化节点列表
- **PathResult**: `{ paths: PathItem[] }` - 后端 GET /graph/path 的响应类型

#### API Method (`packages/web/src/services/api.ts:76-82`)
- **graphApi.getPath(fromName, toName, maxDepth?)**: 调用 `GET /graph/path`，参数映射为 `from_name/to_name/max_depth`（与后端实际参数名匹配）

#### Component (`packages/web/src/components/graph/PathExplorer.tsx`)
- **PathExplorer**: 路径探索面板
  - Props: `{ loading?: boolean }`
  - 两个 AutoComplete 输入（起点/终点），onSearch 调用 graphApi.search 获取候选
  - "查找路径"按钮，调用 graphApi.getPath
  - 结果区：展示至多 5 条路径，每条用 Ant Design Steps 垂直展示节点序列，关系类型用 relTypeLabels 中文映射标注
  - 无路径时显示 Alert 提示
  - 默认折叠，查询前显示说明文字

## Outputs for Dependent Tasks

### Available Components
```typescript
import PathExplorer from 'packages/web/src/components/graph/PathExplorer';
import type { PathResult, PathItem } from 'packages/web/src/types/graph';
// or from services/api.ts:
import type { PathResult } from 'packages/web/src/services/api';
```

### Integration Points
- **graphApi.getPath**: `getPath(fromName: string, toName: string, maxDepth?: number): Promise<PathResult>` — 查找节点间路径
- **PathExplorer**: 无状态依赖，直接在任意页面使用，通过内部 state 管理输入和结果

### Backend Endpoint
- `GET /api/v1/graph/path?from_name=xxx&to_name=yyy&max_depth=4`
- 返回 `{ paths: [{ path: [...nodes] }, ...] }`

## Verification

- `grep 'getPath' packages/web/src/services/api.ts` — 命中 1 条
- `ls packages/web/src/components/graph/PathExplorer.tsx` — 文件存在
- `grep 'PathExplorer' packages/web/src/pages/GraphPage.tsx` — 命中 2 条 (import + render)
- `grep 'relTypeLabels' packages/web/src/components/graph/PathExplorer.tsx` — 命中 2 条
- `vp build` — exit code 0 (635ms)

## Status: Complete
