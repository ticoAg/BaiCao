# tcm-db

## 身份

- `source_id`: `tcm-db`
- 直接上游：[xiaogege6697/tcm-db](https://github.com/xiaogege6697/tcm-db)
- 本地只读入口：`.cache/github/xiaogege6697/tcm-db/tcm_knowledge.db`
- 核对 commit：`e29028be9a4b4a70a49a7adfaaf268e2f1b7999f`
- SQLite SHA-256：`a9ff634e621ed47869c4ab2628e145b7da48afe922205bcf6f7983415a72966c`
- 许可：tcm-db 本身和 6 个上游没有 GitHub 可识别许可证；仅 `9527qingfeng/hantang-nihaixia-follower` 为 MulanPSL-2.0，不能覆盖混合数据库中的其他来源
- 状态：`cleaned_local`；`publish: false`，不得进入 public Hugging Face Parquet

公开可见不等于允许复制、派生或再发布。本源只在本地做结构清洗、质量评估和隔离入图验证；取得全部上游明确授权前，不发布数据库、逐条派生记录或关系。

## 输入与处理链

```text
tcm_knowledge.db（SQLite，mode=ro + query_only）
  -> 5 个实体表 + 3 个显式关系表
  -> tcm_db 严格 schema 校验、实体聚合与隔离
  -> DatasetRecord / DatasetEdge
  -> processed/latest/records.jsonl + stats.json
```

只消费以下表：

| 来源表 | 映射 |
|---|---|
| `herbs` | `药材` |
| `formulas` | `方剂` |
| `symptoms` | `症状` |
| `syndromes` | `病证`，并标记 `中医类型=来源标注证候` |
| `treatment_methods` | `治法` |
| `formula_herbs` | `方剂 -[组成药材]-> 药材` |
| `formula_syndromes` | `方剂 -[关联证候]-> 病证` |
| `syndrome_symptoms` | `病证 -[关联症状]-> 症状` |

`indication`、`composition`、`representative_formulas`、`related_*` 等只保留为原始属性，不从长文本推导治疗、组成、诊断或因果关系。临床医案、穴位、经络、古籍和课程表不在本轮范围。

实体记录定位为 `tcm_knowledge.db:<table>:<id>`；关系使用关系表 `rowid` 形成同格式定位，并写入 Neo4j 关系的 `证据定位`。

## 实体合并与消歧门禁

- 只在同一节点类型内按规范化后的精确名称聚合
- 仅当同名行的非空属性不存在冲突时聚合；空值可由同名行的确定值补齐
- 不使用编辑距离、名称后缀、繁简转换、未经核实的别名或 LLM 投票自动合并
- 药材“白芷”两行同名但 `category`、`flavor`、`indication` 等非空属性冲突，两行全部隔离，不任选主记录
- `乳癌`、`肾衰竭`、`胰脏癌` 在症状与证候表中同名，仍作为不同标签的独立节点
- `乳癌(病证) -> 乳癌(症状)` 是来源内唯一同名跨类型边；国家卫健委诊疗指南把乳腺癌定义为疾病并另列临床症状，因此该边隔离，其他 439 条显式症状边不受影响
- 29 个方剂行命中上游审计的“长名含标点”或“多方合并”规则，共产生 32 个 warning，全部隔离；这些行没有 `formula_herbs` 或 `formula_syndromes` 关系

## 质量边界

结构清洗输出 1,715 records / 654 edges：药材 470、方剂 205、症状 727、病证 194、治法 119；组成药材 196、关联证候 19、关联症状 439。

内容状态继续为 `pending`。`formula_herbs` 的剂量全空、角色全为“未知”；方剂、证候、症状和治法的医学正确性仍需专家抽样。长文本属性保留来源原文，不表示 BaiCao 已验证其中的疗效或诊断主张。

## 筛选

| 字段 | 值 |
|---|---|
| `source_provider` | `github` |
| `dataset_name` | `xiaogege6697/tcm-db` |
| `file_path` | `tcm_knowledge.db` |
| `import_scope_key` | `github:xiaogege6697/tcm-db:tcm_knowledge.db` |

## 外部依据

- [tcm-db](https://github.com/xiaogege6697/tcm-db)：数据库、上游清单与当前 schema
- [MulanPSL-2.0](https://spdx.org/licenses/MulanPSL-2.0.html)：唯一已核实上游许可证
- [原发性乳腺癌规范化诊疗指南](https://www.nhc.gov.cn/ewebeditor/uploadfile/2013/07/20130725152900765.pdf)：将乳腺癌定义为恶性肿瘤，并把乳腺肿块、乳头溢液等另列为症状
