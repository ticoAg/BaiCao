# IMPL-2 Summary: 前端溯源展示组件 (ProvenanceDisplay)

## 状态: completed

## 完成的工作

### 新增文件
- `packages/web/src/components/provenance/EvidenceList.tsx` — 证据列表组件，展示 content/source_name/page_reference/status
- `packages/web/src/components/provenance/EvidenceDetail.tsx` — 单条证据详情展开组件
- `packages/web/src/components/provenance/LineageChain.tsx` — 溯源链路可视化组件（entity→evidence→source）
- `packages/web/src/hooks/useProvenance.ts` — TanStack Query hook，封装 lineage/evidence/completeness 三个查询

## 功能验证
- `useProvenance(entityId)` → { lineage, evidence, evidenceCount, completeness, loading }
- `EvidenceList` 接受 `evidence: EvidenceItem[]` prop，支持展开详情
- `LineageChain` 接受 `lineage: LineageChain` prop，Timeline 展示链路

## US 覆盖
- US-007: 查看答案证据 ✅
- US-008: 跳转来源查看 ✅（source_name 显示，page_reference 展示）
