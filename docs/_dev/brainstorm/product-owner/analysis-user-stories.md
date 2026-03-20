# User Stories & Acceptance Criteria: 中药材知识图谱问答产品

## 1. 用户故事总览

### 1.1 Epic 结构

```
Epic: 中药材知识图谱问答
├── Feature: 智能问答
│   ├── US-001: 用户提问获取答案
│   ├── US-002: 查看推理链详情
│   └── US-003: 追问与上下文延续
├── Feature: 知识图谱探索
│   ├── US-004: 可视化图谱浏览
│   ├── US-005: 药材详情查看
│   └── US-006: 关系路径探索
├── Feature: 溯源与证据
│   ├── US-007: 查看答案证据
│   ├── US-008: 跳转来源查看
│   └── US-009: 证据关联查看
├── Feature: 专家审查
│   ├── US-010: 专家提交审查
│   ├── US-011: 专家审查答案
│   └── US-012: 审查结果通知
└── Feature: 搜索与筛选
    ├── US-013: 药材搜索
    └── US-014: 高级筛选
```

---

## 2. 核心用户故事

### 2.1 智能问答

#### US-001: 用户提问获取答案
```
Title: 用户提问获取知识图谱支撑的答案

As a [用户]
I want [输入自然语言问题获取答案]
So that [快速获得可溯源的中药材知识]

Acceptance Criteria:
- Given 用户在问答界面
  When 输入问题 "人参的功效有哪些？"
  Then 系统返回答案，包含人参的功效列表

- Given 答案包含知识图谱实体
  When 答案展示时
  Then 显示可点击的实体标签，可跳转详情页

- Given 答案可以关联到证据
  When 答案展示时
  Then 显示"查看溯源"按钮

- Given 用户未登录
  When 提问
  Then 允许匿名提问，限制每分钟5次

Story Points: 8
Priority: Must Have
Dependencies: None
```

#### US-002: 查看推理链详情
```
Title: 用户查看完整推理过程

As a [中医师]
I want [查看答案的推理链]
So that [理解答案是如何得出的，验证准确性]

Acceptance Criteria:
- Given 用户查看了答案
  When 点击"查看推理链"
  Then 展示推理过程的可视化链路图

- Given 推理链包含多个节点
  When 展示推理链路
  Then 每个节点显示：实体名称、关系类型、证据摘要

- Given 推理链路较长
  When 展示推理链
  Then 支持展开/折叠节点详情

- Given 推理链路中的实体
  When 用户点击实体节点
  Then 跳转至该实体的详情页

Story Points: 5
Priority: Must Have
Dependencies: US-001
```

#### US-003: 追问与上下文延续
```
Title: 用户追问延续对话上下文

As a [用户]
I want [在同一个对话中追问]
So that [深入探索相关问题]

Acceptance Criteria:
- Given 用户发起了一个问题
  When 在60分钟内继续提问
  Then 系统保持对话上下文

- Given 用户在对话中追问
  When 输入"为什么？"或类似追问
  Then 系统基于上一轮答案进行深入解释

- Given 用户想开启新话题
  When 输入"新话题："开头
  Then 系统开启新的对话上下文

Story Points: 5
Priority: Should Have
Dependencies: US-001
```

---

### 2.2 知识图谱探索

#### US-004: 可视化图谱浏览
```
Title: 用户浏览知识图谱

As a [研究者]
I want [可视化浏览中药材知识图谱]
So that [发现药材之间的关联]

Acceptance Criteria:
- Given 用户在图谱探索页面
  When 进入页面
  Then 默认展示核心药材的中心图谱

- Given 图谱展示中
  When 用户双击节点
  Then 以该节点为中心展开子图

- Given 图谱展示中
  When 用户拖拽节点
  Then 节点位置更新，其他关系保持

- Given 图谱展示中
  When 用户滚动鼠标
  Then 图谱缩放适应视野

- Given 用户想保存探索状态
  When 点击"保存视图"
  Then 系统保存当前图谱快照，可后续恢复

Story Points: 8
Priority: Must Have
Dependencies: None
```

#### US-005: 药材详情查看
```
Title: 用户查看药材详细信息

As a [用户]
I want [查看药材的完整信息]
So that [了解药材的属性、功效、用法等]

Acceptance Criteria:
- Given 用户在图谱中点击药材节点
  When 点击节点
  Then 右侧滑出药材详情面板

- Given 药材详情页
  When 加载完成
  Then 显示：基本信息、功效、主治、用量、禁忌、来源

- Given 药材详情页
  When 有关联证据时
  Then 每个信息项显示证据来源图标

- Given 用户想看更详细信息
  When 点击"查看完整报告"
  Then 跳转至药材完整详情页

Story Points: 3
Priority: Must Have
Dependencies: US-004
```

#### US-006: 关系路径探索
```
Title: 用户探索实体间的关系路径

As a [研究者]
I want [查看两个药材之间的关系路径]
So that [理解药材之间的关联逻辑]

Acceptance Criteria:
- Given 用户在图谱页面
  When 选择起始节点和终点节点
  Then 系统计算并展示最短关系路径

- Given 关系路径展示
  When 路径包含多个关系
  Then 每段关系显示关系类型和说明

- Given 用户想看更多路径
  When 点击"查看所有路径"
  Then 展示Top 5关系路径供选择

Story Points: 5
Priority: Should Have
Dependencies: US-004
```

---

### 2.3 溯源与证据

#### US-007: 查看答案证据
```
Title: 用户查看答案的证据关联

As a [中医师]
I want [查看答案的证据来源]
So that [验证答案的可靠性和准确性]

Acceptance Criteria:
- Given 用户查看了答案
  When 点击"查看溯源"
  Then 展示答案关联的证据列表

- Given 证据列表
  When 每条证据包含
  Then 显示：证据类型、来源、摘要、关联度

- Given 用户想看证据详情
  When 点击证据项
  Then 展开证据详细内容

Story Points: 3
Priority: Must Have
Dependencies: US-001
```

#### US-008: 跳转来源查看
```
Title: 用户跳转查看原始来源

As a [研究者]
I want [跳转到原始文献或来源]
So that [获取更详细的参考信息]

Acceptance Criteria:
- Given 用户查看证据详情
  When 证据有外部来源
  Then 显示"查看来源"按钮

- Given 用户点击"查看来源"
  When 来源是内部文档
  Then 在新页面打开文档

- Given 用户点击"查看来源"
  When 来源是外部链接
  Then 在新标签页打开链接

Story Points: 2
Priority: Must Have
Dependencies: US-007
```

#### US-009: 证据关联查看
```
Title: 用户查看证据的关联网络

As a [执业药师]
I want [查看证据与其他药材的关联]
So that [全面评估用药安全]

Acceptance Criteria:
- Given 用户在证据详情页
  When 查看证据关联
  Then 展示该证据关联的所有药材实体

- Given 证据关联网络
  When 用户点击关联实体
  Then 跳转至该实体的详情页

Story Points: 3
Priority: Could Have
Dependencies: US-007
```

---

### 2.4 专家审查

#### US-010: 专家提交审查
```
Title: 用户提交答案供专家审查

As a [用户]
I want [对存疑答案提交专家审查]
So that [获得专业确认或修正]

Acceptance Criteria:
- Given 用户查看了答案
  When 点击"申请审查"
  Then 弹出审查申请表单

- Given 审查申请表单
  When 用户填写并提交
  Then 系统创建审查任务，通知专家

- Given 审查申请提交成功
  When 用户查看申请记录
  Then 显示申请状态：待审查/审查中/已完成

Story Points: 3
Priority: Should Have
Dependencies: US-001
```

#### US-011: 专家审查答案
```
Title: 专家审查用户提交的答案

As a [专家用户]
I want [审查用户提交的答案]
So that [确保知识质量，提供专业意见]

Acceptance Criteria:
- Given 专家登录系统
  When 进入审查工作台
  Then 显示待审查任务列表

- Given 专家选择审查任务
  When 查看答案及推理链
  Then 可对答案进行：批准/修正/驳回 操作

- Given 专家提交审查结果
  When 完成审查
  Then 系统通知原用户，系统更新答案状态

- Given 专家需要修正答案
  When 提交修正内容
  Then 修正内容记录历史，答案更新

Story Points: 8
Priority: Must Have
Dependencies: US-002, US-010
```

#### US-012: 审查结果通知
```
Title: 用户接收审查结果通知

As a [用户]
I want [接收审查结果通知]
So that [及时了解答案审查状态]

Acceptance Criteria:
- Given 用户提交了审查申请
  When 专家完成审查
  Then 系统发送通知：站内消息/邮件/短信

- Given 通知内容
  When 发送给用户
  Then 包含：审查结论、专家意见、可跳转查看链接

- Given 用户点击通知链接
  When 打开链接
  Then 跳转至原答案页面，显示审查结果

Story Points: 2
Priority: Should Have
Dependencies: US-011
```

---

### 2.5 搜索与筛选

#### US-013: 药材搜索
```
Title: 用户搜索药材

As a [用户]
I want [快速搜索药材]
So that [快速定位目标药材]

Acceptance Criteria:
- Given 用户在搜索框输入
  When 输入药材名称
  Then 实时显示匹配建议列表

- Given 搜索建议列表
  When 用户选择建议项
  Then 跳转至该药材详情页

- Given 用户回车提交
  When 搜索无匹配时
  Then 显示"未找到相关药材"提示

- Given 用户输入模糊关键词
  When 搜索时
  Then 支持模糊匹配和同义词扩展

Story Points: 3
Priority: Must Have
Dependencies: None
```

#### US-014: 高级筛选
```
Title: 用户使用高级筛选

As a [研究者]
I want [使用高级筛选功能]
So that [精准定位符合条件的药材]

Acceptance Criteria:
- Given 用户点击"高级筛选"
  When 打开筛选面板
  Then 可按：功效分类、药性、用法、来源、禁忌进行筛选

- Given 筛选条件组合
  When 用户设置多个筛选条件
  Then 筛选条件之间为AND关系

- Given 筛选结果
  When 用户点击药材项
  Then 跳转至该药材详情页

Story Points: 5
Priority: Could Have
Dependencies: US-013
```

---

## 3. 验收标准定义

### 3.1 Definition of Ready (DoR)

每个用户故事在进入开发前需满足：

- [ ] 描述清晰，无歧义
- [ ] 验收标准明确，可测试
- [ ] 界面原型或设计稿可用
- [ ] 技术依赖已识别
- [ ] 优先级已确认
- [ ] 故事点估算完成

### 3.2 Definition of Done (DoD)

每个用户故事完成需满足：

- [ ] 代码实现完成
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 代码审查通过
- [ ] 功能演示完成
- [ ] 文档更新完成
- [ ] 部署至测试环境验证

### 3.3 质量门禁

| 检查项 | 标准 |
|-------|------|
| 功能测试覆盖率 | >80% |
| API响应时间 | <500ms (P95) |
| 图谱渲染帧率 | >30fps |
| 溯源链路完整率 | >95% |
| 专家审查响应 | <24小时 |
