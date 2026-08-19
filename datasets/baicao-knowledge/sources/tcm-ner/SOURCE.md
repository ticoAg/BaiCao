# TCM-NER / DeepNER

## 身份

- `source_id`: `tcm-ner`
- 本地镜像：[z814081807/DeepNER](https://github.com/z814081807/DeepNER) 的 `data/raw_data/`
- 官方来源：天池竞赛 [531824](https://tianchi.aliyun.com/competition/entrance/531824/information) / 数据集 [86819](https://tianchi.aliyun.com/dataset/86819)；OpenKG `tcm-ner` 未取得
- 本地只读入口：`.cache/github/z814081807/DeepNER/data/raw_data/`
- 状态：`cleaned_local`；`publish: false`，不得进入 public Hugging Face Parquet

GitHub 仓库无 `license` 字段，也没有 LICENSE 文件。官方 brat 原包未持有。当前文件是竞赛冠军方案转换后的 JSON，不能把公开可见当成再发布授权。说明书正文含药品商品名和药厂名，也不得进入 public 导出。

## 输入与处理链

```text
train.json + dev.json（只读）
  -> JSON 数组 schema、13 类标签、跨度对齐、stack 去重
  -> 不提升任何节点或边
  -> processed/latest/records.jsonl（空）+ stats.json
```

`stack.json` 是 train+dev 的精确并集，禁止双计数。`test.json` 500 篇无标签，只作拆分审计。`candidate_entities` 是未校验候选串，不消费。

## 消费文件

| 文件 | 篇数 | 本轮用途 |
|---|---:|---|
| `train.json` | 850 | 只读审计 |
| `dev.json` | 150 | 只读审计 |
| `test.json` | 500 | 确认无标签，隔离 |
| `stack.json` | 1,000 | 确认等于 train∪dev，隔离 |

标注跨度 17,757；13 类标签的跨度均与原文切片一致。

## 实体与消歧门禁

NER 跨度只证明文本里出现过这段字，不证明实体类型正确，更不证明实体之间有关系。本地抽查已看到明显类型噪声：

- `SYNDROME` 含「人参茎叶总皂苷」「乳腺增生症」
- `DRUG` 含西药名、商品名，以及「头晕」
- `DRUG_TASTE` 含「脾虚」「液体」「褐色」
- `DRUG_INGREDIENT` 含「共奏」「共研细粉」
- 260 个表面串跨类型，例如「糖尿病」同时标成疾病、疾病组、食物组、人群和症状

因此不按表面串生成 `病证`、`症状`、`药材`、`功效` 或任何其他节点。同篇共现也不生成边。

## 关系映射

本轮不生成任何边。USAGE 中「同一说明书共现可抽药物–功效/主治」是共现启发式，不是源事实。`治疗病证=0`。

## 质量边界

结构清洗输出 0 records / 0 edges。这是有意结果，不是解析失败。说明书原文、17,757 条跨度、3,746 个按类型计的表面词和 500 篇无标签测试全部隔离。904 / 1,000 篇标注文本含药厂或公司名。

结构通过不等于医学内容通过。该源只适合后续抽取器评测或人工抽检，不能作为图谱真源。

## 筛选

| 字段 | 值 |
|---|---|
| `source_provider` | `github` |
| `dataset_name` | `z814081807/DeepNER` |
| `file_path` | `data/raw_data` |
| `import_scope_key` | `github:z814081807/DeepNER:data/raw_data` |
| `batch_id` | `2026-08-19-tcm-ner-v1` |

## 外部依据

- [DeepNER](https://github.com/z814081807/DeepNER)：竞赛方案与转换 JSON；仓库无许可证
- [天池 86819](https://tianchi.aliyun.com/dataset/86819)：官方数据集页，需登录；官方包未持有
- [天池竞赛 531824](https://tianchi.aliyun.com/competition/entrance/531824/information)：中药说明书实体识别挑战
