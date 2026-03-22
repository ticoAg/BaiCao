# IMPL-1 Summary: 独立药材详情页 (HerbDetailPage)

## 状态: completed

## 完成的工作

### 新增文件
- `packages/web/src/pages/HerbDetailPage.tsx` — 完整药材详情页，展示：基本信息、功效、性味归经、用法用量、禁忌、关联证据
- `packages/web/src/pages/HerbDetailPage.test.tsx` — 页面测试文件
- `packages/web/src/hooks/useHerbDetail.ts` — TanStack Query hook，加载药材详情 + 关联证据

### 修改文件
- `packages/web/src/App.tsx` — 新增 `/herb/:id` 路由
- `packages/web/src/services/api.ts` — 扩展 `Herb` 接口（alias, efficacy, flavor, meridian, dosage, contraindications）

## 功能验证
- 路由：`/herb/:id` → HerbDetailPage
- 数据：herbApi.get(id) + provenanceApi.getEntityEvidence(id)
- 导航：面包屑 + 查看图谱按钮（跳至 /graph/:name）

## US 覆盖
- US-005: 药材详情查看 ✅
