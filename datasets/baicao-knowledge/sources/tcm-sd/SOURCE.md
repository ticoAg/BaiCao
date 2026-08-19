# TCM-SD / ZY-BERT

## 身份

- `source_id`: `tcm-sd`
- 上游仓库：[Borororo/ZY-BERT](https://github.com/Borororo/ZY-BERT)
- 论文：[TCM-SD: A Benchmark for Probing Syndrome Differentiation via Natural Language Processing](https://aclanthology.org/2022.ccl-1.80/)（arXiv:2203.10839）
- 本地只读入口：`.cache/github/Borororo/ZY-BERT/TCM-SD/`
- 上游仓库快照：`.cache/github/Borororo/ZY-BERT/repo/`，禁止与解压数据双计数
- 天池 139034 官方包未持有
- 状态：`cleaned_local`；`publish: false`，不得进入 public Hugging Face Parquet

GitHub 仓库 `LICENSE` 与 API 标记为 MIT，但正文只覆盖 Software。README 单独声明数据集为 `CC BY-NC-SA 4.0`。论文本身为 `CC BY-NC-ND 4.0`，不能替代数据集许可。`CAND-10` 预训练语料不得继承本源条款。

论文致谢声称已排除姓名、年龄、电话并完成脱敏。本地审计否定该声明：标注集中至少 1 条自由文本含手机号与人名拼接，三份 split 合计 77 条含住院号，医院名出现在 11,626 条记录中。因此只允许本地结构清洗和隔离入图验证，不发布原始病历、聚合病-证对或逐条派生关系。

## 输入与处理链

```text
TCM-SD/syndrome_vocab.txt + train/dev/test.json（只读）
  -> JSONL schema、词表成员、split 泄漏与残留标识扫描
  -> 只提升 148 个证候术语
  -> DatasetRecord
  -> processed/latest/records.jsonl + stats.json
```

`syndrome_knowledge.json`（1,027 条网络爬取定义）和 `test_no_answer.json`（无标签测试副本）只做审计，不进入图记录。

## 消费文件与主域映射

| 文件 | 记录 | 本轮用途 |
|---|---:|---|
| `syndrome_vocab.txt` | 148 | 证候术语真源，映射为 `病证`，`tcm_type=来源标注证候` |
| `train.json` | 43,180 | 只读审计：schema、标签、泄漏、残留标识 |
| `dev.json` | 5,486 | 同上 |
| `test.json` | 5,486 | 同上 |
| `test_no_answer.json` | 5,486 | 确认与 test 去标签对应，禁止带标签 |
| `syndrome_knowledge.json` | 1,027 | 隔离；879 条不在 148 词表内 |

## 实体与消歧门禁

- 图节点身份只使用 `病证 + 规范证候名`；名称来自词表，不从病例文本猜测。
- 标注身份使用 `norm_syndrome`。原始 `syndrome` 只作别名审计；`脾虚证` 会规范到 `脾气虚证` 或 `脾虚湿盛证`，不能当唯一键。
- 病名按 `lcd_name` / `lcd_id` 只进入统计。规范化后 451 个病名、481 个编码；6 个编码对应多个病名，34 个病名对应多个编码。名称键图无法安全承载这些冲突，故不生成病名节点。
- `风寒湿痹证` 同时出现在病名和证候词表中，只保留证候节点。
- `中风病` 与 `中风-中经络`、`喘证` 与 `喘症` 等近义表面变体不自动合并。
- 不使用编辑距离、后缀、拼音、跨语言映射或 LLM 猜测合并。
- `user_id` 不是稳定病例键：50 个跨 split 复用，train 内大量同一用户对应不同病/证。

## 关系映射

本轮不生成任何边。病例上的 `lcd_name + norm_syndrome` 是单次就诊标注，不是“该病定义上关联该证”。把 2,023 个共现对提升为 `关联证候` 会把医院实践频率伪装成知识；写入 `医案` 则会带入残留标识。`治疗病证=0`。

## 质量边界

结构清洗输出 148 records / 0 edges。标注行 54,152，与论文一致。`syndrome ≠ norm_syndrome`：train 5,382、dev 691、test 652。精确重复 5 组共 9 条多余副本。全文跨 split 626 条。知识库 1,027 条含方剂建议，不进入当前契约。

结构通过不等于医学内容通过。148 个证候名仍为 `pending`，只证明词表可解析，不证明证候定义、鉴别或临床适用已经验证。

## 筛选

| 字段 | 值 |
|---|---|
| `source_provider` | `github` |
| `dataset_name` | `Borororo/ZY-BERT` |
| `file_path` | `TCM-SD/syndrome_vocab.txt` |
| `import_scope_key` | `github:Borororo/ZY-BERT:TCM-SD` |
| `batch_id` | `2026-08-19-tcm-sd-v1` |

## 外部依据

- [ZY-BERT](https://github.com/Borororo/ZY-BERT)：仓库 README 声明数据集 `CC BY-NC-SA 4.0`，LICENSE 为 MIT
- [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans)：非商业、相同方式共享
- [TCM-SD 论文](https://aclanthology.org/2022.ccl-1.80/)：54,152 条真实临床记录、148 证候；致谢中的脱敏声明已被本地审计否定
