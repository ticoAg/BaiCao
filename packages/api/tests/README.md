# API 测试分层

`packages/api/tests/` 现在按显式测试层级组织，不再沿用代码目录镜像：

- `contract/`
  - API 路由协议、状态码、响应结构
  - 允许 mock service，但不能模糊 HTTP 契约
- `unit/`
  - 纯业务逻辑、图谱查询拼装、溯源内部推导
  - 必须保持快速、隔离、无真实外部依赖
- `integration/`
  - 预留给真实 PostgreSQL / Neo4j / Redis 联调
  - 不允许把全 mock 测试放进这一层

当前目录结构：

```text
tests/
├── contract/
│   ├── test_health.py
│   ├── test_routes.py
│   └── test_verification.py
├── integration/
└── unit/
    ├── kg/
    ├── provenance/
    └── services/
```

执行约定：

```bash
./scripts/test_api.sh
```

后续新增测试时，每个测试文件必须且只能属于一层：

- `unit`
- `contract`
- `integration`

如果测试依赖 mock 数据库、mock 图数据库或 patch service，请优先放在 `unit/` 或 `contract/`，不要伪装成 `integration`。
