# ShenNong TCM-KG

## 身份

- `source_id`: `shennong-tcm-kg`
- 直接上游：[michael-wzhu/ShenNong-TCM-LLM](https://github.com/michael-wzhu/ShenNong-TCM-LLM) `src/TCM-KG_triples.txt`
- 原始图谱上游：[ywjawmw/TCM_KG](https://github.com/ywjawmw/TCM_KG)
- 本地只读入口：`.cache/github/michael-wzhu/ShenNong-TCM-LLM/src/TCM-KG_triples.txt`
- 核对 commit：`dfa372736777c26fee022ff869a929a2ab8911db`
- SHA-256：`e2b42d9e93da44203f526bd6f3f23a2275613ab02e5952381dfa943032fcfec4`
- 许可：两个上游仓库均未提供 `LICENSE` / `COPYING` / `NOTICE`；ShenNong README 限定相关资源仅供学术研究且禁止商业用途
- 状态：`imported`（已入本地图）；`publish: false`，不得进入 public Hugging Face Parquet

公开可见和“开源”表述不构成明确的复制、派生或再发布许可。本源只在本地完成结构清洗、质量评估和隔离入图验证；取得明确授权前，不发布原始三元组或逐条派生记录。

## 输入与处理链

```text
TCM-KG_triples.txt（head<TAB>tail<TAB>relation）
  -> shennong_tcm_kg 严格解析、类型映射与隔离
  -> DatasetRecord / DatasetEdge
  -> processed/latest/records.jsonl + stats.json
```

- 上游 `Create_Graph.py` 把第三列 relation 同时用作 tail label 和关系名；head 没有显式类型
- `中药`、`治法`、`证候` 分别保留为 `关联药材`、`关联治法`、`关联证候`，方向保持 clinical head 指向带来源类型的 tail
- 不把来源中的类型关联提升为“治疗”或诊断因果关系
- source relation 标为 `证候` 的 tail 保留 `tcm_type=来源标注证候`；其他临床 head 保留 `tcm_type=未分类临床概念`
- 不按名称后缀、编辑距离、繁简体或 LLM 猜测自动拆分疾病、症状和证候
- `TS_MS` 的 245 条跨语言候选全部隔离，不参与别名或实体合并
- `symmap_chemical`、`chemical_MM` 共 67,481 行不属于当前中医临床主域，全部排除
- 337 条“功能” tail 同时出现在临床概念集合，因类型冲突隔离
- 每条图关系保留 source、batch、scope 和 `import_unit_id`；可由 record 的 `evidence_refs` 回到原始行

## 实体合并与消歧门禁

- 只在同一节点类型内按规范化后的精确名称聚合
- 药材与病证即使同名也不跨类型合并；本批次实测跨类型同名为 0
- 不使用模糊匹配、编辑距离、未经核实的中英文映射或模型推断
- 同时作为 syndrome tail 和 clinical head 的 122 个名称保留为同一 `病证` 节点，并以 `tcm_type=来源标注证候` 标记
- 后续只有在其他来源提供显式类型或可信标准标识时，才进一步拆分疾病、症状和证候

## 质量边界

结构清洗已通过：123,358 行输入无坏列、空端点或精确重复；输出 19,066 records / 52,247 edges，无悬空端点。内容仍为 `pending`：原始 head 未显式区分疾病、症状和证候，上游标为 `证候` 的 tail 也存在“舌质红”“发热”等需复核类型，另有 337 条功能冲突、245 条跨语言映射尚未人工逐条复核。

因此本源可用于本地候选图谱和后续人工消歧，不可标为 trusted，也不可公开发布。

## 筛选

| 字段 | 值 |
|------|-----|
| `source_provider` | `github` |
| `dataset_name` | `michael-wzhu/ShenNong-TCM-LLM` |
| `file_path` | `src/TCM-KG_triples.txt` |
| `import_scope_key` | `github:michael-wzhu/ShenNong-TCM-LLM:src/TCM-KG_triples.txt` |

## 外部依据

- [ShenNong-TCM-LLM README](https://github.com/michael-wzhu/ShenNong-TCM-LLM)：图谱来源与仅限学术研究声明
- [TCM_KG](https://github.com/ywjawmw/TCM_KG)：原始图谱仓库和建图脚本
- [WHO ICD-11 Traditional Medicine FAQ](https://www.who.int/standards/classifications/frequently-asked-questions/traditional-medicine)：传统医学诊断分类需使用标准化诊断类别，不能由字符串启发式替代
