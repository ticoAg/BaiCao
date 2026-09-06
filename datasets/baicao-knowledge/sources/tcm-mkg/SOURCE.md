# TCM-MKG V1.0

## 身份

- `source_id`: `tcm-mkg`
- 原始记录：[Zenodo 13763953](https://zenodo.org/records/13763953)
- Hugging Face 镜像：[JX-Lab/TCM-MKG](https://huggingface.co/datasets/JX-Lab/TCM-MKG)
- 本地只读入口：`.cache/huggingface/JX-Lab/TCM-MKG/`
- 固定版本：Zenodo `V1.0`，DOI `10.5281/zenodo.13763953`
- 已持有：D1–D7、D18、开放文档 PDF
- 2026-08-20 本机已删除：`original_kg/edges.tsv`、`original_kg/nodes.tsv`、D8–D17、D19–D24、SD1（基因/PPI/化合物/预测边，不入图）
- 状态：`imported`（已入本地图）；`publish: false`，不得进入 public Hugging Face Parquet

Zenodo API 对 V1.0 声明 `CC-BY-NC-4.0`，而 Hugging Face Dataset Card 标记为 `CC-BY-4.0`。本项目采用更严格的原始记录条款。D1/D3 引用的 WHO 中医术语另受 `CC-BY-NC-SA-3.0-IGO` 约束，D5/D18 的 ICD-11 内容另受 `CC-BY-ND-3.0-IGO` 约束；D2-D7 还引用中国药典 2020 与 dayi.org.cn 等上游。聚合记录的许可不能覆盖这些独立权利，因此只允许本地质量清洗和隔离入图验证。

## 输入与处理链

```text
D1-D7 + D18 TSV（只读）
  -> 标准 csv TSV 解析（支持 quoted multiline）
  -> 固定 schema、稳定 ID、端点与字段语义校验
  -> 主域筛选、精确同名合并、跨类型隔离、关系降级
  -> DatasetRecord / DatasetEdge
  -> processed/latest/records.jsonl + stats.json
```

`original_kg` 与 D8–D17 / D19–D24 / SD1 已从本机删除，不再作为输入。历史盘点：`nodes.tsv` 用标准 CSV 逻辑解析为 369,911 个逻辑记录；`edges.tsv` 约 4,800 万条化学/靶点边。中医主域只消费 D1–D7 + D18 分表。

## 消费表与主域映射

| 表 | 逻辑记录 | 本轮用途 |
|---|---:|---|
| D1 TCM terminology | 1,810 | 传统医学疾病、证候、治法/治则，以及 D7 使用的性味、归经术语 |
| D2 Chinese patent medicine | 8,977 | 中成药映射为方剂 |
| D3 CPM-TCMT | 11,185 | 方剂到传统医学疾病、证候、治法/治则的显式关联 |
| D4 CPM-CHP | 74,084 | 方剂组成饮片，保留 `dosage_ratio` |
| D5 CPM-ICD11 | 69,431 | 方剂 indication 到 ICD-11 chapter 1-20 的中性关联 |
| D6 Chinese herbal pieces | 6,207 | 饮片及稳定 `CHP_ID` |
| D7 medicinal properties | 23,517 | 饮片到性味、归经 |
| D18 ICD-11 | 18,444 | 为 D5 端点提供规范病名、代码和 chapter |

D8–D17、D19–D24、SD1 以及两个 `original_kg` 文件不进入输出，并已从本机删除。化学成分、天然产物、靶点和跨本体映射超出当前中医药主域；SD1 是预测关系，不得写成已验证事实。

## 实体与消歧门禁

- 节点身份只使用 `节点类型 + NFKC/trim/casefold 后规范中文名`；拼音、英文、alias、编辑距离和 LLM 判断不参与自动合并。
- `CPM_ID`、`CHP_ID`、`TCMT_ID` 与 `ICD11_code` 先做格式和唯一性校验，再作为节点属性保留。
- 同类型同规范名仅在非空属性无冲突时聚合；冲突直接失败，不静默覆盖。
- 10 个 TCMT/ICD-11 同名病证精确合并，并同时保留两个稳定 ID；这只代表规范名一致，不声明两个本体整体等价。
- 13 组方剂/饮片跨类型同名保持两个节点，不跨类型合并。
- D3 有 982 行仅冗余 `Synonyms` 与 D1 不同；D1 的 `TCMT_ID` 行是术语真源，D3 不覆盖实体属性。
- D6 仅 `record:1717`（`CHP01717 黄芪`）多出一个 tab；通过唯一、可计数的固定字段错位模式修复，其他额外列仍直接失败。

## 关系映射

| 源事实 | BaiCao 关系 | 边界 |
|---|---|---|
| D3 传统医学疾病 | 方剂 `适用于` 病证 | 中性适用关联，不提升为疗效或治疗事实 |
| D3 传统医学证候 | 方剂 `关联证候` 病证 | 保留来源类型，不声明诊断或治疗 |
| D3 治则/治法 | 方剂 `采用治法` 治法 | 治则与治法共用现有治法节点契约 |
| D4 CPM-CHP | 方剂 `组成药材` 饮片 | 保留来源剂量比例字符串 |
| D5 CPM-ICD11 | 方剂 `适用于` 病证 | 只接受 chapter 1-20；chapter 21 症状与 chapter 22 损伤隔离 |
| D7 flavor/nature | 饮片 `具有性味` 性味 | D1 英文术语必须与 D7 class 确定匹配 |
| D7 meridian | 饮片 `归于经脉` 归经 | 不从名称猜测经脉 |

没有生成 `治疗病证`。D3/D5 的 `适用于` 只表达上游明确关联，不代表已验证疗效、因果或临床建议。全部节点和关系状态为 `pending`，每条边保留对应 TSV `record:<n>` 定位。

## 质量边界

结构清洗输出 19,519 records / 177,672 edges：方剂 8,977、饮片 6,207、病证 3,963、治法 349、性味 11、归经 12。D5 chapter 21 隔离 13 条、chapter 22 隔离 421 条；D3 重复 pair 1 条，跨 D3/D5 重复适用边 23 条均确定性折叠并合并证据定位。

结构通过不等于医学内容通过。中成药组成、剂量比例、适应关联、证候、治法和药性仍需专家抽样回到源表与上游规范核实。

## 筛选

| 字段 | 值 |
|---|---|
| `source_provider` | `zenodo` |
| `dataset_name` | `TCM-MKG V1.0` |
| `source_revision` | `zenodo:13763953:V1.0` |
| `import_scope_key` | `zenodo:10.5281/zenodo.13763953@V1.0` |
| `batch_id` | `2026-08-19-tcm-mkg-v1` |
| `prompt_hash` | `sha256:2229708fcfbf` |

八个消费表的 SHA-256 保存在 `processed/latest/stats.json`；清洗器每次运行都会重新计算，用于确认只读输入没有漂移。

## 外部依据

- [Zenodo TCM-MKG V1.0](https://zenodo.org/records/13763953)：原始记录、版本、文件和上游来源声明
- [Zenodo record API](https://zenodo.org/api/records/13763953)：V1.0 的 `cc-by-nc-4.0` 许可元数据
- [WHO international standard terminologies on traditional Chinese medicine](https://www.who.int/publications/i/item/9789240042322)：D1/D3 术语上游与 `CC-BY-NC-SA-3.0-IGO`
- [WHO ICD-11 License](https://icd.who.int/docs/icd-api/license/)：D5/D18 的 `CC-BY-ND-3.0-IGO` 边界
- [TCM-MKG Dataset Card](https://huggingface.co/datasets/JX-Lab/TCM-MKG)：镜像说明及与原始记录不一致的许可标记
