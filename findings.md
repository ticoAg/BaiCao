# Findings: BaiCao 全阶段补齐

## 差距分析（2026-03-21）

### Phase 2 后端基础缺口
- **HerbModel 字段缺失**: 当前仅 id, name, latin_name, category, description, created_at, updated_at。缺 alias, english_name, efficacy, flavor, meridian, dosage, contraindications, images
- **Evidence 独立模型缺失**: 只有 VerificationEvidence（审核附件），无溯源 Evidence 模型
- **Alembic 未初始化**: pyproject.toml 已有 alembic 依赖但未 init。表创建依赖 create_all

### Phase 4 知识图谱缺口
- **ProvenanceService 已完整实现** (`packages/api/app/provenance/__init__.py`, ~180 行) 且已暴露 REST API 端点
- **GraphService 缺少**: TREATS, SIMILAR_TO 关系方法和 Disease 节点创建
- 溯源服务 89% 测试覆盖率，功能健全

### Phase 5 对话与可视化缺口
- **ChatService 是规则 stub**: 基于关键词匹配，未接入 LLM。注释写"简化版本，实际应调用 LLM"
- **SSE 流式完全缺失**: 无 EventSource、StreamingResponse、streaming 相关代码
- **推理链是模板生成**: 固定步骤，非真实推理
- langchain + langchain-openai 已在依赖中，config.py 有 openai_api_key/openai_model 配置字段

### 前端工程化缺口
- 无 hooks/ 目录（API 逻辑内联在页面 useEffect 中）
- 无 stores/ 目录（无 Zustand 状态管理）
- 无 types/ 目录（类型散落在 api.ts 和页面中）
- 仅 Header.tsx 一个独立组件
- 未使用 TanStack Query
- ChatPage 350 行、GraphPage 350+ 行，偏大

### 已有基础设施（可复用）
- conftest.py 中 mock_neo4j_driver fixture（IMPL-001 产出）
- 146 个测试全部通过（5 模块 TDD 完成）
- shared/types/index.ts 330 行 SSOT 类型
- docker-compose.yml 完整（postgres, neo4j, redis, api, web, nginx）
- Neo4j 种子数据 seed_chenpi.cql（陈皮完整图谱）

## 技术约束

- Python 3.12+, FastAPI, SQLAlchemy 2.0 async, neo4j async driver
- React 18, TypeScript, vite-plus (vp) 工具链
- pnpm workspace monorepo
- 前端命令: `vp dev` / `vp build` / `vp test`
