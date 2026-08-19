---
type: Implementation Plan
title: 数据源逐源质量清洗与入图计划
description: 逐个核实、清洗和验收 BaiCao 已持有候选数据源，统一处理许可、实体消歧、图模型映射与发布门禁。
resource: docs/superpowers/plans/2026-08-19-data-source-quality-ingestion.md
tags: [data-sources, data-ingestion, entity-resolution, knowledge-graph]
timestamp: 2026-08-19T00:00:00+08:00
status: active
---

# 数据源逐源质量清洗与入图计划

**Goal:** 逐个把已持有候选源转成可追溯、可复核、符合 BaiCao 中医药图模型的本地结构化数据；许可允许时才进入 public dataset。

**Architecture:** 原始文件保留在 `tmp/qibo-datasets/` 且只读。每个源单独完成许可核实、契约映射、实体消歧、清洗、测试和隔离 Neo4j smoke，再更新 `docs/architecture/data-sources.md` 与 dataset 台账。不同源不共用未经验证的别名字典或启发式分类结果。

**Status:** done（tmp 候选已审计；TCMChat-600k 其余子集已补登，待按新隐私原则分批清洗）

## 全局门禁

- 不把 GitHub/Hugging Face 公开可见等同于允许复制、派生或公开发布。
- 疾病、症状、证候、药材、饮片和方剂只按确定证据分类；类型不明时保留待审，不用名称后缀、编辑距离或 LLM 猜测自动归类。
- 只允许同类型、规范名一致或有可信标准标识支撑的确定性合并；跨类型、跨语言和模糊近似进入人工队列。
- 每条关系保留源、批次、原始行或记录定位；模型推断、共现和外部补充知识不得伪装成原始事实。
- 任一源出现许可、隐私或临床语义 `critical` 问题时保持 `publish: false`，不进入 public Parquet。

## 串行顺序

1. `CAND-01` ShenNong TCM-KG
2. `CAND-02` tcm-db
3. `CAND-03` DragonTCM
4. `CAND-04` TCM-MKG
5. `CAND-05` TCM-SD / ZY-BERT
6. `CAND-06` 至 `CAND-10` 按 `docs/architecture/data-sources.md` 的质量与许可结论逐个推进

每个源固定执行：`许可确认 -> 契约映射 -> 消歧门禁 -> 清洗 -> 测试 -> Neo4j smoke -> 质量结论 -> 独立提交`。

## 已完成源：CAND-01 ShenNong TCM-KG

### 已确认事实

- 本地 `TCM-KG_triples.txt` 与 `michael-wzhu/ShenNong-TCM-LLM` 官方仓库 `src/TCM-KG_triples.txt` 的 SHA-256 相同。
- 文件共 123,358 行，每行是 `head<TAB>tail<TAB>relation`；无空端点、坏列或精确重复。
- 官方 README 指向 `ywjawmw/TCM_KG` 上游；两个仓库根目录当前都没有 `LICENSE`、`COPYING` 或 `NOTICE`。
- `symmap_chemical` 与 `chemical_MM` 共 67,481 行，不进入当前中医临床主域清洗结果。

### Tasks

- [x] 建立单一 active plan 和逐源执行顺序
- [x] 完成三路 Grok 许可、关系契约与实体消歧独立审查
- [x] 用 AnySearch 和官方一手来源核实上游、许可及疾病/证候术语边界
- [x] 决定症状到证候关系的最小共享契约，明确是否需要拆分 `病证`
- [x] 实现来源专用 parser/CLI；坏行、未知关系和类型冲突显式失败或进入拒绝统计
- [x] 为合并门禁、关系方向、属性化和排除关系补最小测试
- [x] 生成本地 `records.jsonl`、`stats.json` 和质量报告，不加入 public 发布
- [x] 运行 importer dry-run 与隔离 Neo4j smoke，验证无 dangling edge 和跨类型误合并
- [x] 更新 catalog/ledger、数据源清单、稳定架构与验收证据
- [x] 独立提交 `CAND-01`，再把当前源切换为 `CAND-02`

### 当前实现证据

- 输出：19,066 records / 52,247 edges；3,278 个来源标注证候，12,687 个未分类临床概念
- 中性关联：`关联证候=35,444`、`关联药材=7,832`、`关联治法=2,606`
- 排除与隔离：化学关系 67,481，`TS_MS` 245，功能/临床类型冲突 337，证候自环 9
- 合并门禁：只在同类型内按规范名精确聚合；不使用编辑距离、跨语言映射或 LLM 猜测
- 发布门禁：两个上游仓库无许可证文件，ShenNong README 又限定仅供学术研究和禁止商业用途，固定 `publish: false`

提交证据：`5188a09 feat: clean ShenNong TCM-KG source`

### CAND-01 残余风险

- 原始 head 没有疾病、症状或证候类型，当前只能保留为 `未分类临床概念`；source-labeled syndrome 也只保留为 `来源标注证候`，同名异实需后续标准标识或人工证据才能拆分。
- 上游 `中药`、`治法`、`证候` 同时承担 tail label 和关系名，因此只映射为中性关联，不得作为治疗、诊断或因果事实。
- `TS_MS` 和功能/临床冲突已隔离但尚未人工逐条复核，不参与当前图谱合并。
- 许可不足以支持再发布；本地清洗结果和逐条派生关系不得进入 public dataset。

## 已完成源：CAND-02 tcm-db

### 已确认事实

- 本地仓库与远端 `main` 均固定在 commit `e29028be9a4b4a70a49a7adfaaf268e2f1b7999f`；SQLite SHA-256 为 `a9ff634e621ed47869c4ab2628e145b7da48afe922205bcf6f7983415a72966c`。
- 目标主域表为 472 药材、234 方剂、727 症状、194 证候、119 治法；显式关系为 `formula_herbs=196`、`formula_syndromes=19`、`syndrome_symptoms=440`，无悬空外键。
- `tcm-db` 本身和 6 个上游没有 GitHub 可识别许可证；仅 `9527qingfeng/hantang-nihaixia-follower` 为 MulanPSL-2.0，无法覆盖混合数据库中的其他来源。
- 29 个唯一方剂行命中描述句或多方合并 warning；药材“白芷”两行同名但属性冲突；症状与证候存在乳癌、肾衰竭、胰脏癌 3 个跨类型同名。
- 现有模型缺少独立 `症状` 节点；最小契约为新增 `症状` 与 `关联症状`，其余复用 `药材`、`方剂`、`病证`、`组成药材`、`关联证候`。

### Tasks

- [x] 用 AnySearch、GitHub 官方 API 和本地 commit 核实来源与许可链
- [x] 完成三路 Grok 许可、关系契约与实体消歧独立审查
- [x] 决定最小共享契约：新增 `症状` 节点和 `关联症状` 边
- [x] 决定消歧门禁：异常方剂和属性冲突同名药材隔离，症状/证候跨类型同名保持独立
- [x] 实现只读 SQLite parser/CLI，只消费主域实体和三张显式关系表
- [x] 为 schema 门禁、关系方向、隔离统计和跨类型不合并补测试
- [x] 生成本地 records/stats/质量报告，固定 `publish: false`
- [x] 运行 importer dry-run 与隔离 Neo4j smoke
- [x] 更新 catalog/ledger、数据源清单、稳定架构与验收证据
- [x] 独立提交 `CAND-02`，再把当前源切换为 `CAND-03`

### 当前实现证据

- 输出：1,715 records / 654 edges；药材 470、方剂 205、症状 727、病证 194、治法 119
- 显式关系：`组成药材=196`、`关联证候=19`、`关联症状=439`
- 隔离：29 个异常方剂行、2 条冲突白芷和 1 条同名跨类型边
- 合并门禁：仅同类型规范名精确且非空属性无冲突时聚合；跨类型同名 3 组保持独立
- 溯源：每条节点和关系可定位到 `tcm_knowledge.db:<table>:<id/rowid>`
- 入图验收：1,715 节点 / 654 边；端点类型、同名边、治疗事实提升、缺失证据定位和 scope 错误均为 0
- 发布门禁：混合数据库许可链不完整，固定 `publish: false`

### CAND-02 残余风险

- 29 个异常方剂和两条冲突白芷仍需人工逐条裁定；当前隔离优先于猜测修复。
- `乳癌`、`肾衰竭`、`胰脏癌` 的症状表记录疑似类型误入，但除唯一同名边外仍保留源记录，等待专家确认。
- 方剂组成关系缺少剂量且角色全为“未知”；不能用于剂量或配伍角色推断。
- 医学内容仍为 `pending`，结构通过不等于疗效、主治、证候或治法已经验证。

### 当前风险

- 数据库是不可由现存脚本完整重建的权威产物，且缺少逐表/逐字段上游许可映射；不得发布整库或逐条派生 public 数据。
- `indication`、`composition`、`representative_formulas` 和 `related_*` 是长文本或列表字段，不得直接提升为治疗、组成、诊断或因果关系。
- `formula_herbs` 的 dosage 全空、role 全为“未知”；关系可保留成员事实，但不能伪造剂量或君臣佐使。
- 临床医案存在来源身份键问题且不在本轮中医药/疾病/症状显式关系范围内，保持排除。

提交证据：`4c87231 feat: clean tcm-db source`

## 已完成源：CAND-03 DragonTCM

### 已确认事实

- 本地只读副本位于 `tmp/qibo-datasets/DragonTCM/`，包含 herbs、formulas、conditions、relations 四个 Parquet 配置和一个上游 connector 快照。
- Dataset Card 标注 1,044 herbs、2,580 formulas、1,119 conditions、28,735 relations，许可声明为 `CC-BY-NC-4.0`。
- 数据以英文为主，Dataset Card 声明来源为 American Dragon 网站和 Joel Penner 的著作，并明确说明结构化过程由 AI agents 自动完成、可能不准确。
- Dataset Card 声称 conditions 映射 SNOMED disease ontology，但公开 schema 没有独立标准标识字段，必须从实际内容核实，不能按声明自动接受对齐。

### Tasks

- [x] 用 AnySearch、Hugging Face 官方页面和上游一手来源核实许可、署名及再利用边界
- [x] 完成三路 Grok 许可、关系契约与实体消歧独立审查
- [x] 审计四个 Parquet 的 schema、空值、重复、端点完整性、关系类型和方向
- [x] 决定中英文实体、SNOMED 声称、condition/症状/证候边界和同名实体的合并门禁
- [x] 实现来源专用只读 parser/CLI，只提升有原始显式边支撑且符合共享图模型的事实
- [x] 为 schema 门禁、关系方向、跨语言不自动合并和隔离统计补最小测试
- [x] 生成本地 records/stats/质量报告，并按许可与来源链结论设置发布门禁
- [x] 运行 importer dry-run 与隔离 Neo4j smoke
- [x] 更新 catalog/ledger、数据源清单、稳定架构与验收证据
- [x] 独立提交 `CAND-03`，再把当前源切换为 `CAND-04`

### 当前实现证据

- 输出：11,598 records / 46,666 edges；药材 1,027、方剂 2,574、病证 803、症状/临床表现 7,194
- 显式/中性关系：`组成药材=14,608`、`关联药材=2,197`、`关联症状=29,861`；`治疗病证=0`
- condition 门禁：仅 803 个 disorder 入图；257 finding、40 morphologic abnormality、12 observable entity、4 qualifier value、2 procedure 和 1 个无合法标签行隔离
- SNOMED：入图病证 227 个有合法 ID，576 个无 ID；无 ID 不生成、不猜测
- 合并门禁：药材 17 组、方剂 6 组无冲突表面重复合并；`FUSHI` / `FU SHI` 冲突组和 20 个 herb/formula 跨类型同名保持独立
- 隔离：被隔离 condition 端点关系 5,576，condition 到 formula 关系 6,354，坏或截断 manifestation 51；重复病证/症状边折叠 7,281
- 入图验收：11,598 节点 / 46,666 边；端点类型、证据定位、scope、同标签重复和状态错误均为 0
- 发布门禁：Dataset Card 为 `CC-BY-NC-4.0`，但上游网站、书籍和 SNOMED CT 权利链未闭合，固定 `publish: false`

### CAND-03 残余风险

- clinical manifestations 可能混合患者症状与临床体征；当前只保留中性 `关联症状` 和逐项证据定位，仍需专家抽检。
- 20 组跨类型同名和大量中英文 aliases 尚未做标准标识对齐；没有可信来源前不得跨类型或跨语言自动合并。
- formula 的 syndromes/actions/treats、condition 的 nested pattern 和 condition-to-formula `treats` 未提升为图事实，等待图模型契约和医学证据共同确认。
- AI 自动解析的组成、剂量、适应证、禁忌和关系需抽样回到原始来源；未经专家确认的医学内容保持 `pending`。
- 许可不足以支持 public 再发布；本地清洗结果和逐条派生关系不得进入 public dataset。

提交证据：`713fe46 feat: clean DragonTCM source`

## 已完成源：CAND-04 TCM-MKG

### 已确认事实

- 本地只读副本位于 `tmp/qibo-datasets/TCM-MKG/`，持有 D1-D24、SD1、开放文档 PDF 和按标准 CSV 逻辑解析为 369,911 个记录的 `original_kg/nodes.tsv`；Dataset Card 的 369,912 与实际文件相差 1。
- 48,849,793 行、约 5.64 GB 的 `original_kg/edges.tsv` 未下载；当前不得把完整图边写成已持有或已验证事实。
- Hugging Face Dataset Card 声明它是 Zenodo TCM-MKG V1.0 的格式转换与再分发，标记 `CC-BY-4.0`，并要求引用原作者和 DOI `10.5281/zenodo.13763953`。
- 数据跨越中医术语、中成药、饮片、药性、天然产物、靶点、疾病本体和预测关系；当前项目优先审计 D1-D7 的中医药主域实体及显式关系。

### Tasks

- [x] 用 AnySearch、Zenodo、Hugging Face 和各本体官方条款核实许可、署名与再分发边界
- [x] 完成三路 Grok 许可、关系契约与实体消歧独立审查
- [x] 审计 D1-D24、SD1 和 nodes.tsv 的 schema、行数、空值、重复、ID 与跨表端点
- [x] 限定 BaiCao 主域子图，区分源事实、标准本体映射、距离关系和 SD1 预测关系
- [x] 决定中成药/方剂、饮片/药材、疾病/症状/证候及中英文名称的实体合并门禁
- [x] 实现来源专用只读 parser/CLI，只消费许可与语义边界明确的主域表
- [x] 为 schema、ID 连接、关系方向、预测关系排除和跨类型不合并补最小测试
- [x] 生成本地 records/stats/质量报告，并按上游权利链结论设置发布门禁
- [x] 运行 importer dry-run 与隔离 Neo4j smoke
- [x] 更新 catalog/ledger、数据源清单、稳定架构与验收证据
- [x] 独立提交 `CAND-04`，再把当前源切换为 `CAND-05`

### 当前实现证据

- 输出：19,519 records / 177,672 edges；方剂 8,977、饮片 6,207、病证 3,963、治法 349、性味 11、归经 12
- 关系：`适用于=73,514`、`关联证候=2,032`、`采用治法=4,525`、`组成药材=74,084`、`具有性味=15,225`、`归于经脉=8,292`；`治疗病证=0`
- 主域边界：只消费 D1-D7 和 D18；D8-D17、D19-D24、SD1、original graph 全部排除
- 合并门禁：10 个 TCMT/ICD-11 同类型精确同名节点合并并保留双 ID；13 组方剂/饮片同名保持独立
- 结构修复与隔离：D6 黄芪错位 1 行确定性修复；D5 chapter 21 隔离 13、chapter 22 隔离 421；D3 冗余 synonym 差异 982 行不覆盖 D1 真源
- 发布门禁：Zenodo 为 `CC-BY-NC-4.0`，WHO 术语为 `CC-BY-NC-SA-3.0-IGO`，ICD-11 为 `CC-BY-ND-3.0-IGO`，其他聚合上游权利链未闭合，固定 `publish: false`

### CAND-04 残余风险

- D3/D5 的中成药关联已降级为中性 `适用于`，仍需专家抽样确认源表 indication 与目标病名是否挂接正确。
- 10 个 TCMT/ICD-11 精确同名合并只依据同类型规范中文名；当前保留双 ID 和逐表证据，但尚未证明两个本体概念在所有语境完全等价。
- D4 剂量比例和 D7 药性关系虽有稳定端点与逐行定位，仍需回到药典、WHO 术语或其他原始规范核实内容准确性。
- `original_kg/edges.tsv` 未持有；当前只证明 D1-D7/D18 子图，不代表完整 TCM-MKG 已清洗或验收。

提交证据：`0b8f0c6 feat: clean TCM-MKG source`

### 当前风险

- Dataset Card 的 `CC-BY-4.0` 不能自动替代 ICD-11、MeSH、DOID、蛋白互作库等上游资源的独立条款；许可链未闭合前保持 `publish: false`。
- D5/D18-D24 的疾病映射和 D11-D17 的化学/靶点标识可能是外部本体对齐，不等于中医临床治疗或因果事实。
- SD1 明确是 predicted links，不得与 D1-D24 的来源表事实混合，也不得进入默认临床知识图。
- 中成药、方剂、饮片、药材、病名、证候和症状必须按源类型与稳定 ID 区分；名称近似或跨语言 alias 不触发自动合并。

## 已完成源：CAND-05 TCM-SD / ZY-BERT

### 已确认事实

- 本地只读副本位于 `tmp/qibo-datasets/TCM-SD/`，包含 train 43,180、dev 5,486、test 5,486 条标注文本和 148 个证候标签。
- 上游仓库为 `Borororo/ZY-BERT`。仓库 `LICENSE` 与 GitHub API 为 MIT（Software）；README 单独声明数据集 `CC-BY-NC-SA-4.0`。论文本身为 `CC-BY-NC-ND-4.0`。
- 数据是疾病/临床文本到证候标签的监督学习语料；标签关联不等于治疗、因果、诊断标准或已验证患者事实。
- 论文致谢声称已脱敏。本地审计发现至少 1 条手机号+人名、77 条住院号、11,626 条医院名。

### Tasks

- [x] 用 AnySearch、上游仓库和数据文件核实许可、来源、去标识化与再利用边界
- [x] 审计三份 split 的 schema、编码、重复、文本泄漏、标签分布和 148 个证候定义
- [x] 决定该源只作为抽取器评测/术语清单，不生成病-证候选关系
- [x] 实现来源专用 parser/CLI、最小测试、dry-run 和隔离 Neo4j smoke
- [x] 更新 SOURCE/VIEW、catalog/ledger、稳定架构与验收证据后独立提交
- [ ] Grok 许可/契约/消歧三路审查：已发起但全部超时，未计作有效结论

### 当前实现证据

- 输出：148 records / 0 edges；全部为来源标注证候
- 隔离：临床文本 59,638 行、病名 451、病-证共现 2,023、知识库 1,027
- 合并门禁：不按 lcd_id/近义病名自动合并；`风寒湿痹证` 只保留证候节点
- 发布门禁：数据集 `CC-BY-NC-SA-4.0`，且残留病历标识，固定 `publish: false`

提交证据：`752bbb7 feat: clean TCM-SD source`

### CAND-05 残余风险

- 148 个证候术语尚未对照国家标准或专家词表逐条复核。
- 病例标签和知识库常见病/推荐方仍可能被下游误用为治疗或诊断事实，必须保持隔离。
- 残留标识证明论文脱敏声明不可信；下游不得回读原始 JSON 到问答或 public 导出。

## 已完成源：CAND-06 TCM-NER / DeepNER

### 已确认事实

- 本地只读副本位于 `tmp/qibo-datasets/TCM-NER/DeepNER-raw/`：train 850、dev 150、test 500、stack 1000。
- DeepNER 仓库无许可证；天池 86819 / OpenKG 官方 brat 包未持有。
- `stack.json` 与 train∪dev 内容完全一致；test 无标签。
- 13 类共 17,757 条跨度全部与原文切片对齐，但类型噪声和 260 个跨类型同名使其不能自动入图。

### Tasks

- [x] 用 GitHub API、天池页面和本地文件核实许可、镜像边界与再利用限制
- [x] 审计 train/dev/test/stack 的 schema、重复和标签边界
- [x] 决定该源只作抽取器评测审计，不生成实体清单或共现边
- [x] 实现来源专用 parser/CLI 和最小测试；空 records 不跑 importer / Neo4j
- [x] 更新 SOURCE/VIEW、catalog/ledger、稳定架构与验收证据后分开提交代码与数据文档
- [ ] Grok 独立审查：本轮不发起。上一源三路审查均超时，改为本地证据审查

### 当前实现证据

- 输出：0 records / 0 edges
- 隔离：标注篇 1,000、跨度 17,757、无标签测试 500、stack 1,000、药厂名 904 篇
- 发布门禁：竞赛镜像无许可证，固定 `publish: false`

提交证据：`fede603 feat: audit TCM-NER source without graph lift`

### CAND-06 残余风险

- 未对照官方 brat 包核验转换 JSON 是否完整或被改写。
- 跨度类型噪声未做专家重标；不得被下游当药品知识。

## 已完成源：CAND-07 TCM-Ancient-Books

### 已确认事实

- 本地只读副本位于 `tmp/qibo-datasets/TCM-Ancient-Books/`：编号 `000`–`699` 共 700 本，另有未编号 `700.李培生老中医经验集.txt`。
- 上游仓库无许可证。可读编号书全部为 GB18030；`203-婴童类萃.txt` 解码失败。
- `290-外科证治全书.txt` 已存在，同时残留百度云下载文件。

### Tasks

- [x] 核实许可、版本来源与再利用边界
- [x] 审计目录、编码、重复和篇章边界
- [x] 决定本轮只建书目台账，不抽取全文
- [x] 实现来源专用 parser/CLI 和最小测试
- [x] 更新 SOURCE/VIEW、catalog/ledger、纳入决策与验收证据后分开提交

### 当前实现证据

- 输出：0 records / 0 edges
- 可解码 699；隔离解码失败 1、未编号 1、下载残留 2
- 发布门禁：无许可证，固定 `publish: false`

提交证据：`7ee591c feat: audit TCM-Ancient-Books bibliography only`

### CAND-07 残余风险

- 数字整理本是否为足本、OCR 与现代标点均未核验。
- 「思考中医」等现代书名仍在编号目录中，后续抽取必须单独标记。

## 已完成源：CAND-08 / CAND-09 / CAND-10

### 已确认事实

- `classical-tcm-canon`：115 部、9,401,166 字；`license: other` / `proprietary-commercial`。
- SylvanL 预训练：三份 `{text}` JSON 共 177,054 行；医案 4 文件未持有；source2 index 11949 串文。
- ZY-BERT rar：RAR v5，成员 `tcm_pretrain_corpus_a.txt` 约 821 MB，未解压；许可不继承 TCM-SD。

### Tasks

- [x] 核实三份已持有源的许可与载体
- [x] 审计 schema / 行数 / 归档成员
- [x] 决定均不入图、不进 public
- [x] 实现三份 parser/CLI 与最小测试
- [x] 回写纳入决策、catalog 与验收证据

### 当前实现证据

- 三源均为 0 records / 0 edges，`publish: false`
- 本地已收录独立候选源已全部处理，本计划不再有下一个当前源

提交证据：`1b13e39 feat: audit remaining locally held corpora`

## Verification

```bash
cd packages/data_ingestion
uv run --with pytest --with pyarrow pytest tests/test_remaining_local_sources.py -q
uvx ruff check data_ingestion/classical_tcm_canon.py \
  data_ingestion/sylvanl_tcm_pretrain.py data_ingestion/zybert_pretrain.py
```

共享契约发生变化时，额外执行知识模型/API contract 测试、`pnpm --dir packages/shared typecheck` 和至少一条 web 消费检查。隔离 Neo4j smoke 必须使用无持久卷容器，不修改现有图库。

## Citations

1. [数据源与质量校验清单](../../architecture/data-sources.md)
2. [共享知识模型与数据采集边界](../../architecture/knowledge-model-and-ingestion.md)
3. [ShenNong-TCM-LLM](https://github.com/michael-wzhu/ShenNong-TCM-LLM)
4. [TCM_KG](https://github.com/ywjawmw/TCM_KG)
5. [OKF v0.1 specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
6. [tcm-db](https://github.com/xiaogege6697/tcm-db)
7. [MulanPSL-2.0](https://spdx.org/licenses/MulanPSL-2.0.html)
8. [中医临床诊疗术语国家标准索引](https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D7B2C0D3A7E05397BE0A0AB82A)
9. [Zenodo TCM-MKG V1.0](https://zenodo.org/records/13763953)
10. [WHO TCM terminology](https://www.who.int/publications/i/item/9789240042322)
11. [WHO ICD-11 license](https://icd.who.int/docs/icd-api/license/)
12. [ZY-BERT](https://github.com/Borororo/ZY-BERT)
13. [DeepNER](https://github.com/z814081807/DeepNER)
14. [TCM-Ancient-Books](https://github.com/xiaopangxia/TCM-Ancient-Books)
15. [classical-tcm-canon](https://huggingface.co/datasets/wangekxy/classical-tcm-canon)
16. [SylvanL TCM Pretrain](https://huggingface.co/datasets/SylvanL/Traditional-Chinese-Medicine-Dataset-Pretrain)
