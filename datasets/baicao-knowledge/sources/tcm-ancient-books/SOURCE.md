# TCM-Ancient-Books

## 身份

- `source_id`: `tcm-ancient-books`
- 上游仓库：[xiaopangxia/TCM-Ancient-Books](https://github.com/xiaopangxia/TCM-Ancient-Books)
- 本地只读入口：`.cache/github/xiaopangxia/TCM-Ancient-Books/`
- 状态：`imported`（书目 + 正文词表提及）；`publish: false`，不得进入 public Hugging Face Parquet

GitHub API 与本地仓库均无 LICENSE。原书多数可视为公版，但当前 TXT 是现代数字整理本。2026-08-20 已对编号书正文做词表提及抽取；记录保持 `pending`，不把 OCR/整理本当已验证事实。

## 输入与处理链

```text
NNN-书名.txt（只读，UTF-8 / GB18030 / 替换解码）
  -> 每本一条 NodeType.来源
  -> 正文最长词表匹配 → 药材/方剂/病证/治法 + 来源于
  -> processed/latest/records.jsonl
```

## 消费文件

| 类别 | 数量 | 本轮用途 |
|---|---:|---|
| `000`–`699` 编号 TXT | 700 | 来源节点 + 正文词表提及 |
| `203-婴童类萃.txt` | 1 | 非法字节用 gb18030-replace 抽提及 |
| `700.李培生老中医经验集.txt` | 1 | 未编号现代医论，来源 + 提及 |
| `*.baiduyun.downloading*` | 2 | 已删除残留 |

## 实体与消歧门禁

节点类型为共享枚举 `来源`。`stable_id` / `term_code` 为三位编号。不因书名近似、繁简或「某某全书 / 某某秘传」自动合并。全文抽取必须另立任务。

## 关系映射

正文词表命中生成 `来源于` 边，指向该书 `来源` 节点。共现不是组成或疗效事实。

## 质量边界

2026-08-20 正文词表抽取：9188 records / 464834 条 `来源于`。来源 701（700 编号书含 203 替换解码 + 李培生）。OCR、异体字、现代标点和是否为足本均未核验；提及保持 pending。

## 筛选

| 字段 | 值 |
|---|---|
| `source_provider` | `github` |
| `dataset_name` | `xiaopangxia/TCM-Ancient-Books` |
| `file_path` | `NNN-书名.txt` |
| `import_scope_key` | `github:xiaopangxia/TCM-Ancient-Books` |
| `batch_id` | `2026-08-20-ancient-mentions-v1` |
| `processor` | `tcm_ancient_books_mentions` |

## 外部依据

- [TCM-Ancient-Books](https://github.com/xiaopangxia/TCM-Ancient-Books)：近 700 项中医药文本；无许可证
