# TCM-Ancient-Books

## 身份

- `source_id`: `tcm-ancient-books`
- 上游仓库：[xiaopangxia/TCM-Ancient-Books](https://github.com/xiaopangxia/TCM-Ancient-Books)
- 本地只读入口：`.cache/github/xiaopangxia/TCM-Ancient-Books/`
- 状态：`cleaned_local`；`publish: false`，不得进入 public Hugging Face Parquet

GitHub API 与本地仓库均无 LICENSE。原书多数可视为公版，但当前 TXT 是现代数字整理本，繁简、标点和切分版权未核实。因此只允许本地书目审计，不发布全文，也不把正文抽成图关系。

## 输入与处理链

```text
NNN-书名.txt（只读，GB18030）
  -> 编号、书名唯一性、编码与空文件校验
  -> 不提升任何节点或边
  -> processed/latest/records.jsonl（空）+ stats.json
```

## 消费文件

| 类别 | 数量 | 本轮用途 |
|---|---:|---|
| `000`–`699` 编号 TXT | 700 | 书目审计；699 本可解码 |
| `203-婴童类萃.txt` | 1 | 无法用 UTF-8/GB18030 解码，隔离 |
| `700.李培生老中医经验集.txt` | 1 | 非编号现代医论，隔离 |
| `*.baiduyun.downloading*` | 2 | 未完成下载残留；`290-外科证治全书.txt` 正文本身已存在 |

编号连续，无缺号、无同名。可读文件全部为 GB18030。目录中可见现代书名：思考中医、中医之钥、余无言、李翰卿、名老中医之路。

## 实体与消歧门禁

本轮不生成 `来源` 节点或任何其他节点。书名只进入统计。不因书名近似、繁简或「某某全书 / 某某秘传」自动合并。全文抽取必须另立带原文定位的任务，不得把整书灌进图谱。

## 关系映射

本轮不生成任何边。USAGE 中「从古籍正文抽组成/功效」是后续抽取任务，不是本源已验证事实。

## 质量边界

结构清洗输出 0 records / 0 edges。这是有意结果。699 本可解码全文、1 本解码失败、1 本未编号现代医论和 2 个下载残留全部隔离。

结构通过不等于版本或文本可靠。OCR、异体字、现代标点和是否为足本均未核验。

## 筛选

| 字段 | 值 |
|---|---|
| `source_provider` | `github` |
| `dataset_name` | `xiaopangxia/TCM-Ancient-Books` |
| `file_path` | `NNN-书名.txt` |
| `import_scope_key` | `github:xiaopangxia/TCM-Ancient-Books` |
| `batch_id` | `2026-08-19-tcm-ancient-books-v1` |

## 外部依据

- [TCM-Ancient-Books](https://github.com/xiaopangxia/TCM-Ancient-Books)：近 700 项中医药文本；无许可证
