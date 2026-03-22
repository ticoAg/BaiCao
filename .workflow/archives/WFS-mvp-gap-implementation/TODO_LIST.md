# TODO List: WFS-mvp-gap-implementation

## Tasks

### Phase 1: 独立组件/页面 (可并行)
- [x] **IMPL-1**: 独立药材详情页 (HerbDetailPage) [US-005] [Must Have] → [.summaries/IMPL-1-summary.md](./.summaries/IMPL-1-summary.md)
- [x] **IMPL-2**: 前端溯源展示组件 (ProvenanceDisplay) [US-007/008] [Must Have] → [.summaries/IMPL-2-summary.md](./.summaries/IMPL-2-summary.md)

### Phase 2: 集成到现有页面
- [x] **IMPL-3**: 答案实体高亮 + 溯源按钮 [US-001] [Must Have] → [.summaries/IMPL-3-summary.md](./.summaries/IMPL-3-summary.md)
- [x] **IMPL-4**: 推理链实体可点击 [US-002] [Must Have] → [.summaries/IMPL-4-summary.md](./.summaries/IMPL-4-summary.md)

### Phase 3: 独立增强功能
- [x] **IMPL-5**: 追问与上下文延续 [US-003] [Should Have] → [.summaries/IMPL-5-summary.md](./.summaries/IMPL-5-summary.md)
- [x] **IMPL-6**: 关系路径探索 UI [US-006] [Should Have] → [.summaries/IMPL-6-summary.md](./.summaries/IMPL-6-summary.md)

### Phase 4: 跨模块功能
- [x] **IMPL-7**: 从答案提交审查申请 [US-010] [Should Have] → [.summaries/IMPL-7-summary.md](./.summaries/IMPL-7-summary.md)
  - depends on: IMPL-3
- [x] **IMPL-8**: 审查结果通知 [US-012] [Should Have] → [.summaries/IMPL-8-summary.md](./.summaries/IMPL-8-summary.md)
  - depends on: IMPL-7

## Execution Order
```
Batch 1: IMPL-1 + IMPL-2 (parallel)
Batch 2: IMPL-3 (after Batch 1) + IMPL-4, IMPL-5, IMPL-6 (parallel)
Batch 3: IMPL-7 (after IMPL-3)
Batch 4: IMPL-8 (after IMPL-7)
```

## Progress: 8/8 completed

## Status Legend
- `- [ ]` = Pending task
- `- [x]` = Completed task → link changes to [.summaries/IMPL-X-summary.md]
