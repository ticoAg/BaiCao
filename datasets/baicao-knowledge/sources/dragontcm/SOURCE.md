# DragonTCM

## 身份

- `source_id`: `dragontcm`
- 直接上游：[f-galkin/DragonTCM](https://huggingface.co/datasets/f-galkin/DragonTCM)
- 本地只读入口：`tmp/qibo-datasets/DragonTCM/`
- 核对 revision：`57e19c6bb7aaf62feacbba97aa84d9baecd05582`
- 输入：1,044 herbs、2,580 formulas、1,119 conditions、28,735 relations
- 许可：Dataset Card 标记 `CC-BY-NC-4.0`；American Dragon 网站、Joel Penner 1994 年著作和 SNOMED CT 内容的完整上游授权链未得到证明
- 状态：`cleaned_local`；`publish: false`，不得进入 public Hugging Face Parquet

`CC-BY-NC-4.0` 本身限制商业使用，也不能自动覆盖上游网站、书籍或 SNOMED CT 的独立权利。当前只允许本地清洗、质量评估和隔离入图验证；取得完整上游授权并单独核实 SNOMED 发布要求前，不公开逐条派生内容。

## 输入与处理链

```text
herbs / formulas / conditions / relations Parquet（只读）
  -> DragonTCM 严格 schema 与嵌套 JSON 校验
  -> condition 类型门禁、实体聚合与关系降级/隔离
  -> DatasetRecord / DatasetEdge
  -> processed/latest/records.jsonl + stats.json
```

四个 Parquet 的 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `herbs/train-00000-of-00001.parquet` | `d702bb32cb0c1225ec3d7c3dfcbc3dd63fc17ce1d763fc2a2fef36766a61db4c` |
| `formulas/train-00000-of-00001.parquet` | `eead008f85a677850aa1d52bbfc085f4ed9d6e95c70622af772a4cb9b088c50f` |
| `conditions/train-00000-of-00001.parquet` | `f6bac71e68c8c02167d469d9b7ba2954acba37bd97fde75b0ba3d163f4b6a684` |
| `relations/train-00000-of-00001.parquet` | `242299d7944f45bdbabae6105f3b126e306f046b0d606e43261e3956a8fd8759` |

## 实体与消歧门禁

- 基础端点键只做 `NFKC + trim + casefold`；同类型表面重复另用共享 punctuation/whitespace key 审计
- 不用编辑距离、拼音、中文别名、跨语言映射或 LLM 判断自动合并
- 20 个 herb/formula 跨类型同名保持独立
- 药材 18 组表面重复中，17 组无非空属性冲突并合并；`FUSHI` / `FU SHI` 因 synonyms/actions 冲突保留两个节点
- 方剂 6 组表面重复全部无冲突并合并
- 中文 aliases 只作属性，不参与实体合并
- 只有名称后缀为 `(disorder)` 的 803 个 condition 映射为 `病证`；其他 316 行按来源语义标签隔离
- 合法 SNOMED ID 只从源字段提取：入图病证中 227 个有 ID、576 个无 ID；缺失 ID 不生成、不猜测

## 关系映射

| 源关系或字段 | BaiCao 映射 | 处理边界 |
|---|---|---|
| `formula -> herb contains` | `组成药材` | 保留显式方向、剂量和逐行定位 |
| `condition(disorder) -> herb treats` | `关联药材` | 降级为中性关联，不声称治疗事实 |
| `condition -> formula treats` | 隔离 | 当前没有中性方剂关联契约，不反转为 `治疗病证` |
| `clinical_manifestations` | `病证 -> 症状` 的 `关联症状` | 只投影 disorder；原始嵌套 JSON、pattern 和逐项定位均保留 |

`clinical_manifestations` 同时可能包含症状与体征，当前节点分类写为“DragonTCM 临床表现（含体征）”。该投影只表达来源显式关联，不是因果、诊断标准或已验证医学事实。空值、坏 schema 和截断文本全部隔离；formula 的 syndromes/actions/treats 及 condition 的 nested pattern 不提升为额外节点或关系。

## 质量边界

结构清洗输出 11,598 records / 46,666 edges：药材 1,027、方剂 2,574、病证 803、症状/临床表现 7,194；组成药材 14,608、关联药材 2,197、关联症状 29,861。

全部内容状态为 `pending`。源数据由 AI agents 从上游材料结构化，组成、剂量、适应证、禁忌和临床表现仍需专家抽样回到原始材料核实。

## 筛选

| 字段 | 值 |
|---|---|
| `source_provider` | `huggingface` |
| `dataset_name` | `f-galkin/DragonTCM` |
| `file_path` | 四个固定 revision Parquet |
| `import_scope_key` | `huggingface:f-galkin/DragonTCM@57e19c6bb7aaf62feacbba97aa84d9baecd05582` |
| `batch_id` | `2026-08-19-dragontcm-v1` |
| `prompt_hash` | `sha256:efa323dda8ac` |

## 外部依据

- [DragonTCM Dataset Card](https://huggingface.co/datasets/f-galkin/DragonTCM)：源规模、来源声明和 Dataset Card 许可
- [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)：署名、非商业和再分发条款
- [American Dragon](https://www.americandragon.com/)：Dataset Card 声明的主要内容来源之一
- [SNOMED CT licensing](https://docs.snomed.org/snomed-ct-practical-guides/snomed-nrc-guide/the-role-of-nrcs-related-to-snomed-ct-licensing)：SNOMED CT 独立许可边界
- [NCI symptom definition](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/symptom)：症状与体征的医学语义边界
