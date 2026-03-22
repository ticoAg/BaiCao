# Task: IMPL-4 推理链实体可点击 (ReasoningChain 增强)

## Implementation Summary

### Files Modified
- `packages/web/src/components/chat/ReasoningChain.tsx`: 将纯文本推理步骤增强为支持实体/关系 Tag 展示，实体可点击导航

### Content Added

- **useNavigate import** (`ReasoningChain.tsx:4`): 从 react-router-dom 引入导航 hook
- **navigate** (`ReasoningChain.tsx:14`): 组件内实例化 navigate，组件由箭头函数改为函数体以支持 hook
- **entities 渲染块** (`ReasoningChain.tsx:51-69`): 当 `item.entities` 非空时，在步骤行下方渲染蓝色可点击 Tag 列表，前缀"实体:"；点击跳转 `/graph/${encodeURIComponent(entity)}`
- **relations 渲染块** (`ReasoningChain.tsx:70-83`): 当 `item.relations` 非空时，渲染 geekblue Tag 列表（不可点击），前缀"关系:"
- **Space direction="vertical"** (`ReasoningChain.tsx:32`): List.Item 内层从单行 Space 改为垂直 Space，支持多行布局

### Layout Change
```
Before:
  [step Tag] [description Text] [confidence Tag]

After:
  [step Tag] [description Text] [confidence Tag]
  实体: [entity1 Tag(clickable)] [entity2 Tag(clickable)] ...
  关系: [relation1 Tag] [relation2 Tag] ...
```

## Outputs for Dependent Tasks

### Navigation Target
- 实体点击导航到 `/graph/:name`（图谱页面），使用 `encodeURIComponent` 编码实体名

### No New Exports
- 本次修改为组件内部增强，无新增导出接口

## Verification Results

- `grep useNavigate|navigate` 命中 2 行 (import + 实例化)
- `grep entities|relations` 命中 5 行
- `vp build` exit code 0，665ms，无编译错误

## Status: Complete
