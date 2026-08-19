---
type: Data Source Inventory
title: BaiCao 数据源与质量校验清单
description: 汇总已登记数据源、本地候选源、许可边界、已知风险和人工质量审阅结论。
resource: docs/architecture/data-sources.md
tags: [data-sources, knowledge-graph, data-ingestion, quality-review]
timestamp: 2026-08-19T00:00:00+08:00
doc_kind: architecture
status: review
summary: BaiCao 当前持有数据源的单一质量审阅入口
audience: developer, data-team
---

# BaiCao 数据源与质量校验清单

截至 2026-08-19，BaiCao 有 13 个正式登记源、0 个未处理的本地候选源。另有重复目录、辅助仓库和明确未持有的资源，它们不计入独立数据源数量。是否纳入图谱或 public，以「纳入决策」节为准。本地已收录候选已全部审计完毕。

本文档是逐源质量校验的单一入口，不替代以下事实真源：

- 已登记源状态、产量和发布开关：[`datasets/baicao-knowledge/catalog.json`](../../datasets/baicao-knowledge/catalog.json)
- 每个已登记源的身份与边界：`datasets/baicao-knowledge/sources/*/SOURCE.md`
- 原始候选文件：`tmp/qibo-datasets/`，只读、本地保留、不提交 Git
- 图模型与关系语义：[`packages/knowledge_model/`](../../packages/knowledge_model/)

## 状态口径

| 字段 | 允许值 | 含义 |
|---|---|---|
| 持有状态 | `published` / `imported` / `cleaned_local` / `staged_local` / `not_held` | 当前实际处理位置 |
| 结构质量 | `pass` / `partial` / `pending` | 能否稳定解析、是否有坏端点、缺失或重复 |
| 语义质量 | `pass` / `conditional` / `pending` / `blocked` | 实体、关系和属性是否符合中医药语义 |
| 许可状态 | `confirmed` / `restricted` / `unverified` / `unlicensed` | 能否复制、派生和公开发布 |
| 审阅结论 | `accept` / `conditional` / `reject` / `pending` | 人工质量校验的最终决定 |

`public` 不是质量结论。任何源只有在许可、结构、语义、证据和隐私边界都明确后，才可在 catalog 中设置 `publish: true`。

## 纳入决策

这里回答「这份数据集要不要进白草数据源」。三列必须分开看：

| 列 | 含义 |
|---|---|
| 纳入登记 | 是否进入 catalog / 本清单，作为已处理或候选源跟踪 |
| 纳入图谱 | 是否把实体或关系写入本地 Neo4j 知识图 |
| 纳入 public | 是否进入 public Hugging Face `ticoAg/baicao-knowledge` |

### 已处理源

| ID | 数据集 | 纳入登记 | 纳入图谱 | 纳入 public | 原因 |
|---|---|---|---|---|---|
| `BC-01` | 2022 年中药药典 | 是 | 是 | 是，仅脱敏结构化结果 | 国家标准条目，结构稳定，已入图；原文载体条款仍需独立复核，故公开面不含原文 |
| `BC-02` | 道医苏子阳 | 是 | 是 | 是，仅脱敏结构化结果 | 项目自有医案抽取，已入图；原文未获转载授权，公开面不含全文 |
| `BC-03` | Knowlegde_Graph_TCM | 是 | 是，仅本地 | 否 | 中文药材/方剂边可本地使用；上游无许可证，禁止公开逐条派生 |
| `BC-04` | ShenNong TCM-KG | 是 | 是，仅本地且排除化学边 | 否 | 三元组可映射中性关联；两仓库无许可证且限定学术研究 |
| `BC-05` | tcm-db | 是 | 是，仅本地 | 否 | 显式实体/关系表可用；混合上游权利链未闭合 |
| `BC-06` | DragonTCM | 是 | 是，仅本地且限 SNOMED disorder | 否 | 英文方剂库可补对照；CC-BY-NC-4.0 且书籍/SNOMED 条款未闭合 |
| `BC-07` | TCM-MKG V1.0 | 是 | 是，仅本地主域子图 | 否 | D1-D7/D18 可映射方剂/饮片/病证；Zenodo NC、WHO NC-SA/ND 与其他上游不兼容 public |
| `BC-08` | TCM-SD / ZY-BERT | 是 | 有限：只入 148 个证候术语 | 否 | 监督学习语料不是病-证知识；CC-BY-NC-SA-4.0，且病历文本仍有残留标识 |
| `BC-09` | TCM-NER / DeepNER | 是 | 否 | 否 | 竞赛镜像无许可证；NER 跨度噪声大、260 个跨类型同名，只作抽取评测审计 |
| `BC-10` | TCM-Ancient-Books | 是 | 否 | 否 | 可作后续原文证据库；仓库无许可证，数字整理版权不明，全文与未完成下载均不入图 |
| `BC-11` | classical-tcm-canon | 是 | 否 | 否 | 115 部经典可作后续证据库；Dataset Card 为 `proprietary-commercial`，全文不入图不公开 |
| `BC-12` | SylvanL TCM Pretrain | 是 | 否 | 否 | 仅 `{text}` 自由文本，含西药、美容和串文；医案文件未持有，不能当知识图 |
| `BC-13` | ZY-BERT 预训练语料 | 是 | 否 | 否 | 无标注混合文本且许可不继承 TCM-SD；本轮只清单不解压 |

### 明确不纳入独立数据源

| 资源 | 纳入登记 | 原因 |
|---|---|---|
| `Knowlegde_Graph_TCM/` 原始目录 | 否，附属 `BC-03` | 只读输入，禁止双计数 |
| `TCM_KG/` 示例仓 | 否 | 几乎只有示例，完整图已是 `BC-04` |
| `TCM-SD-repo/` | 否，附属 `BC-08` | 上游快照，解压数据在 `TCM-SD/` |
| `fangji-extra/` 聚合目录 | 否，只登记其中 `tcm-db` | 其他文件不是独立源 |
| TCM-MKG `original_kg/edges.tsv` | 否 | 未持有完整边文件 |
| 天池 TCM-NER / TCM-SD 官方包 | 否 | 未取得 |
| 对话/SFT 问答集 | 否 | 不是图谱事实源 |
| `wangekxy/tcm-formulary` 商业全量 | 否 | 未购买、未持有 |

## 正式登记源

| ID | 数据源 | 形态与规模 | 当前状态 | 许可与发布边界 | 已知质量事实 | 审阅结论 |
|---|---|---|---|---|---|---|
| `BC-01` | [2022 年中药药典](../../datasets/baicao-knowledge/sources/national-standard-2022-pharmacopoeia/SOURCE.md) | 605 条目；3,431 条抽取记录 | `imported`；`publish: true` | 原始载体为 `ZJUFanLab/TCMChat-dataset-600k`；公开面只含脱敏结构化结果；上游具体再发布条款仍需独立复核 | 605/605 条目成功；Neo4j 触达 3,427 节点、7,548 边；4 个近重复词条已合并；LLM 语义仍需专家抽样 | `pending` |
| `BC-02` | [道医苏子阳](../../datasets/baicao-knowledge/sources/daoyi-suyang/SOURCE.md) | 389 章叙事医案；1,687 条抽取记录 | `imported`；`publish: true` | 原文未获公开转载授权；原文仅本地保存，公开面只含脱敏结构化结果 | v3 已合并入图；262 章因无可用临床知识跳过；叙事抽取、同名实体和诊疗语义需专家抽样 | `pending` |
| `BC-03` | [fengxi177/Knowlegde_Graph_TCM](../../datasets/baicao-knowledge/sources/fengxi177-knowledge-graph-tcm/SOURCE.md) | 19,923 条原始关系；4,996 records / 11,445 edges | `cleaned_local`；`publish: false` | 上游无 LICENSE，状态为 `unlicensed_upstream`；禁止公开逐条派生关系 | 结构校验通过；737 条组成无可绑定剂量；存在疑似截断词、剂量混入药名和一对多别名；全部保持 `pending` | `blocked` |
| `BC-04` | [ShenNong TCM-KG](../../datasets/baicao-knowledge/sources/shennong-tcm-kg/SOURCE.md) | 123,358 条原始三元组；19,066 records / 52,247 edges | `cleaned_local`；`publish: false` | 两个上游仓库均无许可证文件；ShenNong README 限定仅供学术研究、禁止商业用途；无充分再发布授权 | 中药/治法/证候只保留中性关联；化学关系 67,481 条排除；`TS_MS` 245 条、功能冲突 337 条隔离；3,278 个来源标注证候，12,687 个未分类临床概念 | `blocked` |
| `BC-05` | [tcm-db](../../datasets/baicao-knowledge/sources/tcm-db/SOURCE.md) | 1,746 个主域实体行、655 条显式关系；1,715 records / 654 edges | `cleaned_local`；`publish: false` | 混合数据库仅 1 个上游核实为 MulanPSL-2.0，其余来源缺少明确再发布许可 | 29 个异常方剂、2 条冲突白芷和 1 条同名跨类型边隔离；症状/证候保持独立，逐边保留表行定位 | `blocked` |
| `BC-06` | [DragonTCM](../../datasets/baicao-knowledge/sources/dragontcm/SOURCE.md) | 4,743 个实体行、28,735 条源关系；11,598 records / 46,666 edges | `cleaned_local`；`publish: false` | `CC-BY-NC-4.0` 非商业限制；American Dragon、书籍和 SNOMED CT 的完整上游权利链未闭合 | 仅 803 个 disorder 映射病证；316 个非 disorder 和 11,930 条不安全关系隔离；中英文 alias 不自动合并 | `blocked` |
| `BC-07` | [TCM-MKG V1.0](../../datasets/baicao-knowledge/sources/tcm-mkg/SOURCE.md) | D1-D7/D18 共 213,655 行；19,519 records / 177,672 edges | `cleaned_local`；`publish: false` | Zenodo 为 `CC-BY-NC-4.0`；WHO 术语与 ICD-11 另有 NC-SA / ND 条款，其他聚合上游权利链未闭合 | 仅取方剂、饮片、病证、治法、性味、归经；D3/D5 降级为中性关联；13 组方剂/饮片同名隔离，10 个 TCMT/ICD 精确同名合并 | `blocked` |
| `BC-08` | [TCM-SD / ZY-BERT](../../datasets/baicao-knowledge/sources/tcm-sd/SOURCE.md) | train/dev/test 共 54,152 条标注；148 records / 0 edges | `cleaned_local`；`publish: false` | 数据集为 `CC-BY-NC-SA-4.0`；仓库 MIT 只覆盖代码；论文脱敏声明被本地残留标识否定 | 只提升 148 个证候术语；病例原文、病名节点和 2,023 个病-证共现全部隔离 | `blocked` |
| `BC-09` | [TCM-NER / DeepNER](../../datasets/baicao-knowledge/sources/tcm-ner/SOURCE.md) | train 850、dev 150、test 500、stack 1000；0 records / 0 edges | `cleaned_local`；`publish: false` | 仓库无许可证；天池/OpenKG 官方包未持有 | 17,757 条跨度与 260 个跨类型同名全部隔离；不把说明书共现当图事实 | `blocked` |
| `BC-10` | [TCM-Ancient-Books](../../datasets/baicao-knowledge/sources/tcm-ancient-books/SOURCE.md) | 700 个编号 TXT + 1 个未编号现代医论；0 records / 0 edges | `cleaned_local`；`publish: false` | 仓库无许可证；数字整理版权未核实 | 699 本 GB18030 可解码；`203-婴童类萃` 解码失败；全文与未完成下载不入图 | `blocked` |
| `BC-11` | [classical-tcm-canon](../../datasets/baicao-knowledge/sources/classical-tcm-canon/SOURCE.md) | 115 部、9,401,166 字 Parquet；0 records / 0 edges | `cleaned_local`；`publish: false` | `license: other` / `proprietary-commercial`；原作公版声明不能覆盖数字整理本 | 标题与 id 唯一，全文隔离 | `blocked` |
| `BC-12` | [SylvanL TCM Pretrain](../../datasets/baicao-knowledge/sources/sylvanl-tcm-pretrain/SOURCE.md) | 177,054 条 `{text}`；0 records / 0 edges | `cleaned_local`；`publish: false` | Card 为 Apache-2.0，但内容混杂且医案文件未持有 | 串文 `source2` index 11949；西药/美容/问答与中药条目并列 | `blocked` |
| `BC-13` | [ZY-BERT 预训练语料](../../datasets/baicao-knowledge/sources/zybert-pretrain-corpus/SOURCE.md) | RAR 218 MB，成员 1 个约 821 MB TXT；0 records / 0 edges | `cleaned_local`；`publish: false` | 许可不继承 TCM-SD；Dropbox 包未单独授权 | 只清单不解压 | `blocked` |

当前 public Hugging Face 数据集只汇总 `BC-01` 和 `BC-02`，共 `5,118 records / 11,202 edges`。`BC-03` 只发布 SOURCE/VIEW 元数据；`BC-04` 至 `BC-13` 尚未触发远端重发，后续即使重发也只允许发布元数据。

## 本地候选源

本地 `tmp/qibo-datasets/` 中已收录的独立候选源已全部完成许可/结构审计并进入 catalog。当前没有下一个待清洗的已持有源。

## 重复目录与辅助材料

这些路径保留用于来源追踪或复现，不作为独立数据源重复计数。

| 路径 | 处理口径 |
|---|---|
| `tmp/qibo-datasets/Knowlegde_Graph_TCM/` | `BC-03` 的只读原始输入，不再作为候选源重复登记 |
| `tmp/qibo-datasets/TCM_KG/` | 只有约 1.5 KB 示例三元组和建图脚本；完整图已登记为 `BC-04`，禁止重复导入 |
| `tmp/qibo-datasets/TCM-SD-repo/` | `BC-08` 的上游仓库快照；实际 train/dev/test 使用 `TCM-SD/`，禁止双计数 |
| `tmp/qibo-datasets/fangji-extra/` | 聚合目录；当前只把其中 `tcm-db` 作为 `BC-05` 的只读原始输入 |
| `tmp/qibo-datasets/README.md`、`STATUS.json`、`USAGE.md` | 下载状态、来源说明和本地用法，不是业务数据 |

## 明确未持有或有意跳过

| 资源 | 状态与原因 |
|---|---|
| TCM-MKG `original_kg/edges.tsv` | 未下载；约 5.64 GB / 48,849,793 条边，先用 D1-D24 验证子图价值 |
| 天池 TCM-NER 86819 官方 brat 包 | 未取得；需要登录，当前只有 DeepNER JSON 镜像 |
| 天池 TCM-SD 139034 官方下载 | 未取得；本地数据来自 GitHub ZY-BERT 仓库 |
| Qibo 未公开约 2 GB 预训练混合语料 | 从未公开，未持有 |
| ShenNong/ChatMed SFT、CMtMedQA 等对话数据 | 按当前知识图谱范围有意跳过，不作为事实源 |
| `wangekxy/tcm-formulary` 商业全量 | 未购买、未持有；仅知道公开样例存在 |
| `AIeathumberger/TCMKG` Neo4j store | 仅完成历史调研，当前未下载；导出格式和图模型未知 |
| `michaelwzhu/ShenNong_TCM_Dataset`、`xihao1/Traditional-Chinese-Medicine-Knowledge` | 仅完成历史调研，当前未持有；均偏问答语料，不作为图谱真源 |
| `TCMNER/TCMNER2025` | 仅完成历史调研，当前未持有；定位为抽取器辅助数据 |

## 建议校验顺序

| 优先级 | 数据源 | 目的 |
|---|---|---|
| P0 | `BC-01`、`BC-02` | 已公开，优先确认语义正确率、许可说明和脱敏边界 |
| P0 | `BC-03`、`BC-04` | 已完成结构清洗，确认是否值得继续争取授权或只保留本地 |
| P1 | `BC-06` | 专家抽检跨语言药材/方剂、condition 分类和临床表现投影 |
| P2 | `BC-08` | 专家抽检 148 个证候术语，以及残留标识是否还出现在下游消费面 |
| P3 | `BC-11` 至 `BC-13` | 已完成审计；仅当后续需要原文证据或抽取器时再单独立项 |

## 人工质量校验方法

每个源先做一次筛查抽检：随机 30 条，加上针对已知风险挑选的 20 条。该样本只用于发现明显问题，不代表统计学质量保证。

### 硬门禁

- [ ] 身份可追溯到上游 URL、版本或 commit，且本地文件与记录一致
- [ ] 许可明确覆盖当前使用方式；`unverified` 或 `unlicensed` 不得公开发布
- [ ] 原文、个人信息、医案隐私和受限内容没有进入公开导出
- [ ] 关系表达事实、引用或明确标注的推断；共现和模型猜测不得伪装成事实

### 结构检查

- [ ] 编码、分隔符、schema 和字段含义稳定
- [ ] 记录数与上游说明一致，缺失、坏行、空值和重复有统计
- [ ] 边端点存在且实体类型正确，关系方向符合共享图模型
- [ ] train/dev/test、镜像目录和聚合文件没有重复导入

### 语义与证据检查

- [ ] 药材、方剂、病、证候、症状、功效、治法等类型没有混淆
- [ ] 别名、异体字、繁简体和中英文映射不会造成错误合并
- [ ] 剂量、单位、炮制、禁忌和适应证没有被截断或挂错对象
- [ ] 每条高风险临床关系能回到原记录、章节、表行或上游标识
- [ ] 专家抽检记录包含样本键、错误类型、严重度和修正建议

严重度口径：`critical` 表示错误临床关系、隐私或许可违规；`major` 表示实体/关系挂错或大面积缺失；`minor` 表示格式、别名或非关键属性问题。出现 `critical` 时该源直接 `reject` 或保持 `publish: false`。

## 审阅记录

用户或专家完成抽检后直接填写本表；原始问题样例不要覆盖，应保留样本键和证据定位。

| ID | 审阅人 / 日期 | 样本范围 | 许可 | 结构 | 语义 | 结论 | 问题与证据定位 |
|---|---|---|---|---|---|---|---|
| `BC-01` | 待填写 | 待填写 | 待复核 | 已自动验证 | 待校验 | `pending` | |
| `BC-02` | 待填写 | 待填写 | 原文受限 | 已自动验证 | 待校验 | `pending` | |
| `BC-03` | 待填写 | 待填写 | 无许可证 | 已自动验证 | 待校验 | `blocked` | 737 条组成无剂量及异常词 |
| `BC-04` | 待填写 | 待填写 | 仅限学术研究、无再发布许可 | 已自动验证 | 待校验 | `blocked` | 3,278 个来源标注证候、245 条跨语言映射、337 条功能冲突和 12,687 个未分类临床概念待人工复核 |
| `BC-05` | 待填写 | 待填写 | 混合上游许可不完整 | 已自动验证 | 待校验 | `blocked` | 29 个异常方剂、冲突白芷和 3 组症状/证候跨类型同名待人工复核 |
| `BC-06` | 待填写 | 待填写 | CC-BY-NC-4.0；上游权利链未闭合 | 已自动验证 | 待校验 | `blocked` | 316 个非 disorder、11,930 条隔离关系、7,194 个临床表现和 20 组跨类型同名待人工复核 |
| `BC-07` | 待填写 | 待填写 | Zenodo CC-BY-NC-4.0；WHO NC-SA / ND；其他上游未闭合 | 已自动验证 | 待校验 | `blocked` | 10 个 TCMT/ICD 精确同名合并、13 组方剂/饮片同名、D3/D5 适用关系和 D6 黄芪错位修复待人工复核 |
| `BC-08` | 待填写 | 待填写 | CC-BY-NC-SA-4.0；残留病历标识 | 已自动验证 | 待校验 | `blocked` | 病例原文、2,023 个病-证共现、1,027 条知识库和跨类型同名“风寒湿痹证”待人工复核 |
| `BC-09` | 待填写 | 待填写 | 竞赛镜像无许可证；官方包未持有 | 已自动验证 | 待校验 | `blocked` | 17,757 条跨度、260 个跨类型同名和说明书商品名/药厂名待人工复核 |
| `BC-10` | 待填写 | 待填写 | 仓库无许可证；数字整理版权未核实 | 已自动验证 | 待校验 | `blocked` | 全文不入图；`203-婴童类萃` 解码失败；`700.李培生老中医经验集` 与 5 个现代书名待人工复核 |
| `BC-11` | 待填写 | 待填写 | other / proprietary-commercial | 已自动验证 | 待校验 | `blocked` | 115 部全文不入图 |
| `BC-12` | 待填写 | 待填写 | Apache-2.0 Card；内容混杂 | 已自动验证 | 待校验 | `blocked` | `source2` index 11949 亚锡葡庚糖酸钠Ⅰ串入氨苄西林/舒巴坦 |
| `BC-13` | 待填写 | 待填写 | 不继承 TCM-SD 条款 | 已自动验证 | 待校验 | `blocked` | 未解压的 821 MB 无标注文本 |

审阅完成后的落点：质量事实回写本文件和对应 `SOURCE.md`；正式接入时新增 catalog source、任务 ledger 和验收证据；只有明确允许公开的源才设置 `publish: true`。

## Citations

1. [BaiCao dataset catalog](../../datasets/baicao-knowledge/catalog.json)
2. [BaiCao knowledge dataset architecture](knowledge-dataset.md)
3. [本地候选源下载与规模记录](../../tmp/qibo-datasets/README.md)
4. [本地候选源状态记录](../../tmp/qibo-datasets/STATUS.json)
5. [OKF v0.1 specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
6. [ShenNong-TCM-LLM](https://github.com/michael-wzhu/ShenNong-TCM-LLM)
7. [TCM_KG](https://github.com/ywjawmw/TCM_KG)
8. [WHO ICD-11 Traditional Medicine FAQ](https://www.who.int/standards/classifications/frequently-asked-questions/traditional-medicine)
9. [tcm-db](https://github.com/xiaogege6697/tcm-db)
10. [原发性乳腺癌规范化诊疗指南](https://www.nhc.gov.cn/ewebeditor/uploadfile/2013/07/20130725152900765.pdf)
11. [DragonTCM](https://huggingface.co/datasets/f-galkin/DragonTCM)
12. [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)
13. [SNOMED CT licensing](https://docs.snomed.org/snomed-ct-practical-guides/snomed-nrc-guide/the-role-of-nrcs-related-to-snomed-ct-licensing)
14. [Zenodo TCM-MKG V1.0](https://zenodo.org/records/13763953)
15. [WHO TCM terminology](https://www.who.int/publications/i/item/9789240042322)
16. [WHO ICD-11 license](https://icd.who.int/docs/icd-api/license/)
17. [TCM-Ancient-Books](https://github.com/xiaopangxia/TCM-Ancient-Books)
