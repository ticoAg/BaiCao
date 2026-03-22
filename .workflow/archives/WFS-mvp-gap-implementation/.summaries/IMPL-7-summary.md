# IMPL-7 Summary: 从答案提交审查申请

## 状态: completed

## 完成的工作

### 新增文件
- `packages/web/src/components/chat/ReviewRequestModal.tsx` — 审查申请弹窗，含实体类型选择、实体ID、审查内容、来源ID字段，调用 verificationApi.create 提交

### 修改文件
- `packages/web/src/components/chat/MessageList.tsx`:
  - 新增 reviewOpen/reviewPrefill 状态
  - 新增 handleOpenReview(sources, content) 函数
  - renderSources 增加"申请审查"按钮（FormOutlined 图标）
  - return 末尾加入 ReviewRequestModal 渲染

## 功能验证
```bash
grep '申请审查' packages/web/src/components/chat/MessageList.tsx
grep 'ReviewRequestModal' packages/web/src/components/chat/MessageList.tsx
vp build  # exit 0
```

## US 覆盖
- US-010: 专家提交审查 ✅（从答案页面申请，表单预填充答案内容）
