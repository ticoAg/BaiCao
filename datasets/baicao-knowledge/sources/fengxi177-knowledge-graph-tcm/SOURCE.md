# fengxi177/Knowlegde_Graph_TCM

## 身份

- `source_id`: `fengxi177-knowledge-graph-tcm`
- 上游：<https://github.com/fengxi177/Knowlegde_Graph_TCM>
- 本地只读入口：`.cache/github/fengxi177/Knowlegde_Graph_TCM/`
- 核对 commit：`2ccba36d1cd79706ddd01fc887af2854ead120da`
- 许可：上游 GitHub metadata `license=null`，仓库内无 `LICENSE` / `COPYING` / `NOTICE`
- 状态：`imported`（已入本地图）；`publish: false`，不得进入 public Hugging Face Parquet

GitHub 公开可见不等于授予再发布许可。本源可以在本地完成结构清洗与内部质量评估，但不能把原始 JSON 或逐条派生关系追加到 public dataset。

## 输入与处理链

```text
relations_zhongyao.json + relations_fangji.json
  -> qibo_tcm_kg 结构校验与映射
  -> DatasetRecord / DatasetEdge
  -> processed/latest/records.jsonl
```

- `方名` 只作聚合信息；742 个 `处方` 分别建为 `方剂`，用 `formula_name` 保留方名
- 6,521 条 `composition` 映射为 `组成药材`
- 5,784 条紧邻且药材一致的 `dose` 折叠为组成边 `dosage`
- 多处方且多来源的方名不向处方广播出处；最终保留 436 条可安全归属的 `来源于`
- 别名只写 `aliases`，不参与自动合并；产地写 `origin`
- 原始数据没有段落证据，不伪造 `证据` 节点或 `evidence_text`

## 质量边界

结构校验已通过：19,923 条输入关系无坏端点或未知关系，输出边无悬空或目标类型错误。内容仍为 `pending`：737 条组成没有可绑定剂量，且上游存在疑似截断词、剂量混入药名和一对多别名；这些记录不得标为 trusted。

## 筛选

| 字段 | 值 |
|------|-----|
| `source_provider` | `github` |
| `dataset_name` | `fengxi177/Knowlegde_Graph_TCM` |
| `import_scope_key` | `github:fengxi177/Knowlegde_Graph_TCM` |
