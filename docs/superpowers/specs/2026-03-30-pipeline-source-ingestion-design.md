# 数据处理工作台统一来源录入设计

## 背景

当前 `/data/pipeline` 已具备固定七步工作台与最小预览链路，但来源录入能力仍停留在“字符串 locator + 摘要预览”阶段：

- `huggingface` 目前只校验 `owner/dataset` 形式并返回 `remote_locator` 摘要
- `csv` / `jsonl` 依赖用户手工提供本地路径
- 页面没有真正的“录入数据”入口，无法在工作台内完成下载、上传、解压和 README 预览

这使得工作台还不能承担真实的数据接入主路径。用户已经明确希望：

- `/data/pipeline` 先提供统一的数据源录入能力
- 第一版同时支持 `huggingface repo`、`远程直链`、`本地上传文件/压缩包`
- 后端使用一个固定配置的数据目录保存要处理的数据集
- 进入预览时优先复用缓存；没有缓存时再下载或复制到工作目录
- 页面内能直接预览来源 README 与落盘后的本地内容

## 目标

### 主要目标

1. 在 `/data/pipeline` 的 `source_ingest` 阶段提供统一来源录入入口
2. 第一版同时支持三类来源：
   - `huggingface repo`
   - `remote url`
   - `local upload`
3. 所有来源在后端统一物化到固定数据目录下的 run 工作目录
4. 支持 `zip`、`tar.gz`、`tgz` 的自动解压
5. 在页面内展示来源落盘结果、README 预览、候选文件列表和 Hugging Face 仓库链接

### 非目标

- 第一版不做任意压缩格式支持
- 第一版不做后台异步队列、断点续传或分片上传
- 第一版不做复杂的数据主文件人工切换器
- 第一版不做来源目录自定义；目录由后端配置固定提供
- 第一版不把 pipeline 拆成独立“导入中心”子系统

## 用户确认后的边界

本轮已确认：

- 数据集存储目录采用**后端固定配置**，前端不提供目录编辑
- 加载策略采用**懒下载 + 缓存复用**：首次预览时检查缓存，不存在才下载
- 第一版必须同时支持：
  - Hugging Face repo 标识，例如 `ZJUFanLab/TCMChat-dataset-600k`
  - `http/https` 远程直链
  - 本地上传文件与压缩包
- 第一版支持的文件 / 压缩格式边界为：
  - 文件：`csv`、`jsonl`、`txt`、`md`
  - 压缩包：`zip`、`tar.gz`、`tgz`

## 方案对比

### 方案 1：在现有 `sourceLocator` 字符串上继续打补丁

做法：

- 继续复用 `sourceType + sourceLocator`
- repo、URL、上传文件引用都塞进 `sourceLocator`
- 后端按 `sourceType` 自行分支判断、下载、解压、预览

优点：

- 局部实现最快
- 复用现有页面状态模型

缺点：

- 契约会持续变脆
- 前后端都容易堆积来源分支和隐式约定
- 上传场景会被迫引入更多“临时 locator 语义”

### 方案 2：引入统一来源录入契约，并在 `source_ingest` 中统一物化

做法：

- 创建 run 时提交结构化来源对象，而不是纯字符串 locator
- 后端在 `source_ingest` 里把不同来源统一下载 / 复制 / 解压到固定工作目录
- 后续步骤只消费本地工作目录，不再直接关心来源差异

优点：

- 边界清晰，适合同时支持 repo、URL、上传
- 符合仓库的 contract-first 路径
- 后续扩展新的来源类型成本更低

缺点：

- 需要同时更新 `shared`、`api`、`web`

### 方案 3：先做独立导入中心，pipeline 只消费现成目录

做法：

- 把来源录入、缓存、下载、解压做成独立系统
- pipeline 页面只选择已有目录进入处理

优点：

- 长期架构更独立

缺点：

- 第一版范围显著扩大
- 不符合当前用户希望直接在 `/data/pipeline` 完成来源录入的目标

## 推荐方案

推荐采用**方案 2：统一来源录入契约 + `source_ingest` 统一物化**。

原因：

1. 它直接匹配本轮用户目标，不需要额外子系统
2. 它能让三类来源都收敛成“本地工作目录”这一统一消费边界
3. 它最符合仓库当前的 contract-first 与小步清晰边界原则

## 设计决策

### 决策 1：统一来源录入仍落在 `/data/pipeline`

不新增独立页面或独立模块，继续复用现有三栏工作台：

- 左侧步骤轨不变
- 中部在 `source_ingest` 展示真正可用的来源录入表单
- 右侧展示结构化来源预览，而不是只打印 JSON

### 决策 2：所有来源先统一物化到固定本地目录

后端新增固定配置，例如：

- `PIPELINE_SOURCE_STORAGE_DIR`

所有来源在进入 `source_ingest` 预览时先被物化为本地工作目录。后续 `source_preview`、`normalize`、`extract` 默认只读取本地结果，不再依赖远端来源或浏览器上传状态。

### 决策 3：采用懒下载 + 缓存复用

`huggingface repo` 与 `remote url` 进入预览时：

- 先检查对应缓存目录是否存在
- 存在则复用缓存
- 不存在才执行下载

本地上传来源：

- 先落到上传区
- 再复制或移动到当前 run 的工作目录

### 决策 4：压缩包统一进入解压目录

若来源是 `zip`、`tar.gz`、`tgz`：

- 原始文件保留在 `source/`
- 解压内容进入 `extracted/`
- 后续文件候选和 README 检测优先看 `extracted/`

### 决策 5：README 与候选主文件使用自动识别

第一版不引入复杂文件选择交互，先采用自动识别：

- README 优先匹配 `README.md`
- 数据文件优先级：`jsonl > csv > txt > md`
- 优先从 `extracted/` 识别，再回退到 `source/`

## 统一来源契约

第一版建议引入结构化来源对象，替代“所有语义都塞进字符串 locator”。

### 来源类型

- `huggingface_repo`
- `remote_url`
- `local_upload`

### 输入对象

#### `huggingface_repo`

- `repo_id`

示例：

```json
{
  "source_type": "huggingface_repo",
  "source_input": {
    "repo_id": "ZJUFanLab/TCMChat-dataset-600k"
  }
}
```

#### `remote_url`

- `url`

示例：

```json
{
  "source_type": "remote_url",
  "source_input": {
    "url": "https://example.com/dataset.zip"
  }
}
```

#### `local_upload`

- `upload_token`

说明：

- 页面先通过上传接口把文件传到后端
- 创建 run 时只引用上传结果，不在创建 run 请求里直接传二进制

示例：

```json
{
  "source_type": "local_upload",
  "source_input": {
    "upload_token": "upload-abc123"
  }
}
```

### 兼容策略

为减少改动冲击，本轮可以在 API 层短期兼容原有 `source_type` / `source_locator` 形态，但内部应统一转换到新的结构化来源对象。前端工作台主路径改为只发送新契约。

## 后端目录模型

固定数据目录建议使用如下结构：

```text
<PIPELINE_SOURCE_STORAGE_DIR>/
  uploads/
  cache/
    huggingface/<repo_id>/
    remote/<url_hash>/
  runs/<run_id>/
    manifest.json
    source/
    extracted/
    preview/
```

### 目录职责

- `uploads/`
  存放用户刚上传的原始文件
- `cache/huggingface/`
  存放 repo 下载缓存
- `cache/remote/`
  存放远程直链缓存
- `runs/<run_id>/source/`
  存放当前 run 使用的原始内容
- `runs/<run_id>/extracted/`
  存放解压后的内容
- `runs/<run_id>/preview/`
  存放必要的预览中间产物
- `manifest.json`
  记录来源和物化结果真相

### `manifest.json` 建议字段

- `source_type`
- `source_input`
- `cache_hit`
- `cache_path`
- `source_path`
- `extracted_path`
- `readme_path`
- `candidate_files`
- `download_status`
- `extract_status`
- `errors`
- `warnings`

## 步骤行为设计

### `source_ingest`

职责：

- 验证结构化来源输入
- 根据来源类型完成下载 / 复制 / 解压
- 产出统一本地工作目录
- 生成结构化物化摘要

对三类来源的行为：

- `huggingface_repo`
  - 校验 repo id
  - 检查缓存
  - 无缓存时拉取 repo 内容到缓存目录
  - 复制或链接到当前 run 工作目录
  - 识别仓库页链接与 `README.md`
- `remote_url`
  - 校验 `http/https`
  - 检查 URL 哈希缓存
  - 无缓存时下载原始文件
  - 若为支持的压缩包则解压
- `local_upload`
  - 根据 `upload_token` 找到上传文件
  - 复制或移动到当前 run 工作目录
  - 若为支持的压缩包则解压

`source_ingest.preview_payload` 第一版建议至少包含：

- `resolved_source_type`
- `display_name`
- `storage_root`
- `run_workdir`
- `source_dir`
- `extracted_dir`
- `cache_hit`
- `is_archive`
- `archive_format`
- `readme_found`
- `readme_path`
- `candidate_files`
- `repo_url`
- `readme_url`

### `source_preview`

职责：

- 从本地工作目录读取 README 与候选文件
- 输出可直接在页面展示的文本预览

`source_preview.preview_payload` 第一版建议至少包含：

- `readme_path`
- `readme_content`
- `readme_truncated`
- `content_root`
- `file_inventory`
- `primary_candidate`
- `content_preview`
- `line_samples`

说明：

- 如果存在 `README.md`，页面优先显示 `readme_content`
- 如果不存在 README，则回退展示主候选文件内容
- 若没有任何可读文本文件，应显式返回结构化错误

## 前端交互设计

### 中部来源录入表单

`source_ingest` 阶段新增来源录入 UI：

- 来源类型选择器：
  - `Hugging Face Repo`
  - `远程直链`
  - `本地上传`
- 按来源类型动态切换输入控件

各类型输入控件：

- `Hugging Face Repo`
  - 单行输入 `repo id`
- `远程直链`
  - 单行输入 `http/https URL`
- `本地上传`
  - 文件上传控件，接受普通文件与压缩包

表单提交行为：

- 上传文件时先调用上传接口拿到 `upload_token`
- 再创建 pipeline run
- 创建成功后默认停留在 `source_ingest`
- 用户点击“运行预览”时触发来源物化

### 右侧预览区

预览区不再只显示原始 JSON，第一版按结构化卡片渲染：

在 `source_ingest` 展示：

- 来源类型
- 原始输入
- 缓存命中情况
- 本地工作目录
- 是否识别为压缩包
- 解压状态
- README 是否存在
- 候选文件列表
- 若为 Hugging Face，展示：
  - repo 页链接
  - README 链接

在 `source_preview` 展示：

- README 文本预览
- 文件清单预览
- 主候选文件内容预览
- 明确说明当前内容来自 `source/` 或 `extracted/`

## 安全与错误处理

### 下载与输入边界

- `remote_url` 第一版只允许 `http/https`
- 非法 repo id、非法 URL、空上传结果都必须返回显式错误
- 预览失败不能伪造成“空预览成功”

### 压缩包处理

- 仅支持 `zip`、`tar.gz`、`tgz`
- 解压时必须防止路径穿越
- 遇到不支持的压缩格式时返回结构化错误

### README 与文本预览

- README 预览应限制最大返回长度，避免单次 payload 过大
- 不可读或二进制文件不直接作为文本预览返回

## 测试与验证边界

### API / 领域测试

应新增或扩展：

- `huggingface_repo` 来源物化单测
- `remote_url` 下载与缓存单测
- `local_upload` 复制 / 移动单测
- `zip`、`tar.gz`、`tgz` 解压单测
- README 识别与候选文件自动选择单测
- `source_ingest` / `source_preview` 结构化 payload 单测

### API / Contract 测试

应覆盖：

- 上传接口返回 `upload_token`
- 创建 run 使用结构化来源对象
- `source_ingest` 返回本地目录、缓存状态、README 路径
- `source_preview` 返回 README 内容或主候选文件内容

### 前端测试

应覆盖：

- 来源类型切换后展示不同输入控件
- 上传来源的表单提交流程
- `source_ingest` 结构化预览显示
- `source_preview` README 预览显示
- Hugging Face 链接展示

## 实施顺序

建议顺序：

1. 更新共享契约与 API schema
2. 增加上传接口与固定数据目录配置
3. 实现来源物化、缓存、解压和 README / 候选文件识别
4. 改造 `source_ingest` 与 `source_preview`
5. 改造 `/data/pipeline` 录入表单与预览面板
6. 补齐 API、contract、web 测试

## 风险

- Hugging Face repo 首次拉取可能较慢
- 远程直链下载需要最小限度的类型识别与失败恢复
- 上传接口会引入新的文件生命周期与清理问题
- README 或文本内容过大时需要截断，避免预览 payload 失控

## 结论

第一版应把 `/data/pipeline` 的 `source_ingest` 从“locator 摘要预览”升级为“统一来源录入 + 固定目录物化入口”，让 `huggingface repo`、`remote url`、`local upload` 三类来源都先沉淀为本地工作目录，再由 `source_preview` 和后续步骤统一消费。这既满足当前数据录入目标，也为后续真正的数据处理主链路打下清晰边界。
