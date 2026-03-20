# Integration Tests

`packages/api/tests/integration/` 预留给真实依赖联调测试。

约束：

- 必须连接真实 PostgreSQL / Neo4j / Redis，或真实应用进程
- 不允许以全 mock 方式伪装成 integration
- 在进入默认 CI 前，需要先验证稳定性和可重复性
