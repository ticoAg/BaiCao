# TCM-Ancient-Books

## 身份

- `source_id`: `tcm-ancient-books`
- 上游仓库：[xiaopangxia/TCM-Ancient-Books](https://github.com/xiaopangxia/TCM-Ancient-Books)
- 本地只读入口：`.cache/github/xiaopangxia/TCM-Ancient-Books/`
- 状态：`cleaned_local`；`publish: false`，不得进入 public Hugging Face Parquet

GitHub API 与本地仓库均无 LICENSE。原书多数可视为公版，但当前 TXT 是现代数字整理本。本轮只提升可解码编号书的书目来源节点，不发布全文，也不把正文抽成图关系。

## 输入与处理链

```text
NNN-书名.txt（只读，UTF-8 或 GB18030）
  -> 编号文件名 + 可解码
  -> 每本一条 NodeType.来源
  -> processed/latest/records.jsonl（699 条书目）+ stats.json
```

未编号文件和解码失败文件不进入 records。

## 消费文件

| 类别 | 数量 | 本轮用途 |
|---|---:|---|
| `000`–`699` 编号 TXT | 700 | 可解码 699 本各一条来源节点 |
| `203-婴童类萃.txt` | 1 | UTF-8/GB18030 均失败，跳过 |
| `700.李培生老中医经验集.txt` | 1 | 非编号现代医论，跳过 |
| `*.baiduyun.downloading*` | 2 | 未完成下载残留；`290-外科证治全书.txt` 正文本身已存在 |

## 实体与消歧门禁

节点类型为共享枚举 `来源`。`stable_id` / `term_code` 为三位编号。不因书名近似、繁简或「某某全书 / 某某秘传」自动合并。全文抽取必须另立任务。

## 关系映射

本轮不生成边。USAGE 中「从古籍正文抽组成/功效」是后续抽取任务，不是本源已验证事实。

## 质量边界

结构清洗输出 699 records / 0 edges，全部为书目来源节点。1 本解码失败、1 本未编号现代医论隔离。OCR、异体字、现代标点和是否为足本均未核验。

## 筛选

| 字段 | 值 |
|---|---|
| `source_provider` | `github` |
| `dataset_name` | `xiaopangxia/TCM-Ancient-Books` |
| `file_path` | `NNN-书名.txt` |
| `import_scope_key` | `github:xiaopangxia/TCM-Ancient-Books` |
| `batch_id` | `2026-08-19-ancient-sources-v1` |
| `processor` | `pending_extract` |

## 外部依据

- [TCM-Ancient-Books](https://github.com/xiaopangxia/TCM-Ancient-Books)：近 700 项中医药文本；无许可证
