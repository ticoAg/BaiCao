# 白草药坛 - 初始化任务清单

## 项目阶段

### Phase 1: 项目骨架
- [ ] IMPL-001: 创建Monorepo项目骨架

### Phase 2: 后端基础
- [ ] IMPL-002: 后端核心功能开发

### Phase 3: 前端基础
- [ ] IMPL-003: 前端核心功能开发

### Phase 4: 知识图谱核心
- [ ] IMPL-004: 知识图谱核心模块

### Phase 5: 对话与可视化
- [ ] IMPL-005: 对话界面与可视化

### Phase 6: 基础设施
- [ ] IMPL-006: Docker基础设施配置

---

## 任务状态

| 任务ID | 任务名称 | 状态 | 优先级 | 依赖 |
|--------|---------|------|--------|------|
| IMPL-001 | 创建Monorepo项目骨架 | pending | high | - |
| IMPL-002 | 后端核心功能开发 | pending | high | IMPL-001 |
| IMPL-003 | 前端核心功能开发 | pending | high | IMPL-001 |
| IMPL-004 | 知识图谱核心模块 | pending | high | IMPL-002 |
| IMPL-005 | 对话界面与可视化 | pending | high | IMPL-003, IMPL-004 |
| IMPL-006 | Docker基础设施配置 | pending | high | IMPL-001 |

---

## 快速开始

```bash
# 克隆项目
git clone <repo-url> bai-cao-shi-tan
cd bai-cao-shi-tan

# 安装依赖
pnpm install

# 启动基础设施
cd infra && docker-compose up -d

# 启动开发服务
pnpm --filter api dev &
pnpm --filter web dev
```

---

*最后更新: 2026-03-19*
