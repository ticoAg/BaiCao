# 白草药坛 - 项目初始化规划

## 1. 项目概述

**项目名称**: 白草药坛 (BaiCao ShiTan)
**项目类型**: 中药材知识图谱智能问答系统
**核心价值**: 构建可溯源的中药材知识图谱，支持智能问答和推理链展示

## 2. Monorepo 项目结构

```
bai-cao-shi-tan/
├── packages/
│   ├── api/                    # Python FastAPI 后端
│   │   ├── app/
│   │   │   ├── api/           # API路由
│   │   │   ├── core/          # 核心配置
│   │   │   ├── models/        # 数据模型
│   │   │   ├── services/      # 业务逻辑
│   │   │   ├── kg/            # 知识图谱相关
│   │   │   └──溯源/           # 数据溯源模块
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   ├── web/                    # React 前端
│   │   ├── src/
│   │   │   ├── components/    # 组件
│   │   │   ├── pages/         # 页面
│   │   │   ├── hooks/         # 自定义hooks
│   │   │   ├── stores/        # 状态管理
│   │   │   ├── services/      # API调用
│   │   │   └── types/         # 类型定义
│   │   ├── package.json
│   │   └── Dockerfile
│   │
│   ├── shared/                 # 共享类型和工具
│   │   ├── types/             # TypeScript类型
│   │   ├── constants/         # 常量
│   │   └── utils/              # 工具函数
│   │
│   └── db/                     # 数据库脚本和迁移
│       ├── migrations/         # Alembic迁移
│       ├── neo4j/             # Neo4j Cypher脚本
│       └── seed/              # 种子数据
│
├── infra/                      # 基础设施
│   ├── docker-compose.yml     # 主编排文件
│   ├── postgres/              # PostgreSQL配置
│   ├── neo4j/                 # Neo4j配置
│   ├── nginx/                 # Nginx配置
│   └── redis/                 # Redis配置(可选缓存)
│
├── docs/                      # 文档
├── .gitignore
├── pnpm-workspace.yaml        # pnpm workspace配置
├── turbo.json                # Turborepo配置(可选)
└── README.md
```

## 3. 技术栈选型

### 后端
- **语言**: Python 3.11+
- **框架**: FastAPI + Uvicorn
- **ORM**: SQLAlchemy 2.0 (异步)
- **图数据库驱动**: py2neo / neo4j-driver
- **AI/LLM**: LangChain + OpenAI (或本地模型)
- **验证**: Pydantic v2
- **测试**: pytest + pytest-asyncio

### 前端
- **框架**: React 18 + TypeScript
- **构建**: Vite
- **UI库**: Ant Design 5
- **图可视化**: @ant-design/charts (G6) / reactflow
- **状态管理**: Zustand
- **HTTP客户端**: TanStack Query (React Query)
- **路由**: React Router 6

### 基础设施
- **数据库**: PostgreSQL 15 (关系数据)
- **图数据库**: Neo4j 5 (知识图谱)
- **容器**: Docker + Docker Compose
- **反向代理**: Nginx

## 4. 数据模型设计

### 4.1 核心实体

#### Herb (中药材)
```python
class Herb:
    id: UUID
    name: str                    # 名称（如"人参"）
    latin_name: str              # 拉丁名
    english_name: str            # 英文名
    alias: List[str]             # 别名
    category: str                # 分类（补气药、清热药...）
    description: str              # 描述
    efficacy: List[str]          # 功效
    flavor: List[str]            # 性味（甘、温）
    meridian: List[str]          # 归经
    dosage: str                  # 用法用量
    contraindications: str       # 禁忌
    images: List[Image]          # 图片
    created_at: datetime
    updated_at: datetime
```

#### Source (数据来源)
```python
class Source:
    id: UUID
    name: str                    # 来源名称
    type: str                    # 来源类型（典籍/现代研究/专利）
    author: str                  # 作者
    publication_date: str        # 发表日期
    url: Optional[str]           # 原始链接
    citation: str                # 引用格式
    description: str             # 描述
```

#### Evidence (证据/溯源)
```python
class Evidence:
    id: UUID
    herb_id: UUID
    source_id: UUID
    content: str                 # 具体内容
    page_number: Optional[str]   # 页码
    chapter: Optional[str]       # 章节
    quote: str                   # 原文引用
    verification_status: str     # 验证状态
```

### 4.2 关系定义

```
(Herb)-[:HAS_EFFICACY]->(Efficacy)
(Herb)-[:HAS_FLAVOR]->(Flavor)
(Herb)-[:ENTERS_MERIDIAN]->(Meridian)
(Herb)-[:TREATS]->(Disease)
(Herb)-[:CONTAINS]->(Component)
(Herb)-[:SIMILAR_TO]->(Herb)
(Herb)-[:SOURCE_OF]->(Evidence)
(Source)-[:PROVIDES_EVIDENCE]->(Evidence)
```

### 4.3 溯源模型

```python
class ProvenanceRecord:
    """数据溯源记录"""
    id: UUID
    entity_type: str             # 实体类型
    entity_id: UUID              # 实体ID
    source_id: UUID              # 来源ID
    field_name: str              # 字段名
    original_value: str          # 原始值
    extracted_at: datetime       # 提取时间
    extraction_method: str       # 提取方法（人工/AI/爬虫）
    confidence_score: float      # 置信度
    verification_status: str     # verified/pending/rejected
```

## 5. 数据溯源机制

### 5.1 溯源层级

1. **来源层**: 典籍（《本草纲目》）、现代文献、专利、数据库
2. **实体层**: 每个Herb实体都标注来源
3. **属性层**: 每个属性值都可溯源到具体证据
4. **关系层**: 每条关系都有来源支撑

### 5.2 溯源查询

```python
# 查询某个药材功效的来源
def get_efficacy_provenance(herb_id: UUID, efficacy: str) -> List[Evidence]:
    """获取药材某个功效的溯源证据"""
    pass

# 查询完整的溯源链路
def get_full_provenance(entity_id: UUID) -> ProvenanceChain:
    """获取实体的完整溯源链路"""
    pass
```

### 5.3 多模态支持

```python
class MultiModalData:
    herb_id: UUID
    text_content: List[TextChunk]     # 文本内容
    images: List[ImageReference]       # 图片引用
    tables: List[TableData]           # 表格数据
    source_context: str                # 原始上下文
```

## 6. 前端功能设计

### 6.1 对话界面

- **Chat UI**: 基于Ant Design的对话组件
- **流式响应**: 支持SSE流式输出
- **上下文记忆**: 维护多轮对话上下文
- **快捷指令**: 预设常用查询模板

### 6.2 知识图谱可视化

- **图谱展示**: 使用G6/ReactFlow展示知识图谱
- **节点交互**: 点击节点查看详情
- **关系高亮**: 鼠标悬停高亮相关路径
- **布局切换**: 支持多种布局（力导向、树状、放射）

### 6.3 推理链展示

```
用户问题: 人参为什么能补气？

推理过程展示:
┌─────────────────────────────────────────────────────┐
│ 🔍 推理链                                              │
├─────────────────────────────────────────────────────┤
│ 步骤1: 识别问题类型                                     │
│        问题意图: 解释原因/机制                            │
│        关键实体: 人参                                   │
│                                                     │
│ 步骤2: 定位相关知识                                     │
│        → 找到实体: 人参                                 │
│        → 获取属性: 功效 = [大补元气, 益智宁神, ...]       │
│        → 获取归经: 脾, 肺, 心                            │
│                                                     │
│ 步骤3: 因果推理                                         │
│        人参 → 含有 → 人参皂苷 → 作用于 → 中枢神经系统      │
│                              ↓                        │
│                         补气效果 ←── 验证来源: 《本草纲目》  │
│                                                     │
│ 步骤4: 生成回答                                         │
│        基于上述推理链生成自然语言回答                     │
│        并标注: ⚠️ 推理置信度: 85%                        │
└─────────────────────────────────────────────────────┘
```

### 6.4 溯源展示

- **证据卡片**: 显示每个答案的数据来源
- **原文引用**: 展示原始文献内容
- **可验证性**: 链接到原始来源（如果有）

## 7. Docker Compose 基础设施

### 7.1 服务列表

```yaml
services:
  # PostgreSQL - 关系数据库
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: baicao
      POSTGRES_USER: baicao
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  # Neo4j - 图数据库
  neo4j:
    image: neo4j:5-community
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data
      - ./neo4j/conf:/conf
    ports:
      - "7474:7474"  # Browser
      - "7687:7687"  # Bolt

  # Redis - 缓存(可选)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # API 后端
  api:
    build: ./packages/api
    environment:
      DATABASE_URL: postgresql+asyncpg://baicao:${POSTGRES_PASSWORD}@postgres:5432/baicao
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: ${NEO4J_PASSWORD}
    depends_on:
      - postgres
      - neo4j
    ports:
      - "8000:8000"

  # Web 前端
  web:
    build: ./packages/web
    depends_on:
      - api
    ports:
      - "3000:80"  # Nginx

  # Nginx - 反向代理
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
    depends_on:
      - api
      - web
```

## 8. 初始化阶段目标（高层规划）

> 本文档保留项目阶段目标与高层路线，不再承担仓库级任务系统职责。
> 可执行任务拆解、勾选进度与验证步骤，统一写入 `docs/superpowers/plans/*.md`，由 `writing-plans` 生成。

### Phase 1: 项目骨架 (Day 1)
- monorepo 目录结构
- pnpm workspace
- Git 基础配置

### Phase 2: 后端基础 (Day 1-2)
- FastAPI 项目初始化
- SQLAlchemy 模型定义
- PostgreSQL 连接配置
- Neo4j 连接配置
- 基础 CRUD API

### Phase 3: 前端基础 (Day 2-3)
- React + Vite 项目初始化
- Ant Design 配置
- 基础页面布局
- API 服务封装

### Phase 4: 知识图谱核心 (Day 3-5)
- 知识图谱数据模型
- 图数据库初始化脚本
- 图谱查询服务
- 溯源机制实现

### Phase 5: 对话与可视化 (Day 5-7)
- Chat UI 组件
- 知识图谱可视化
- 推理链展示组件
- SSE 流式响应

## 9. 后续规划建议

1. **数据录入**: 开发数据导入工具，支持批量导入中药材数据
2. **LLM集成**: 接入大语言模型实现智能问答
3. **知识抽取**: 从文献中自动抽取知识构建图谱
4. **多语言**: 扩展支持英文、日文等语言界面
5. **移动端**: 开发小程序/移动端适配

---

*规划生成时间: 2026-03-19*
*Session: WFS-bai-cao-shi-tan*
