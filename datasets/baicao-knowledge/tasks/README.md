# 数据集任务台账

这里记的是**数据处理产量**，不是仓库代码任务。

- 机器可读：`ledger.json`
- 最近完成计划：`docs/superpowers/plans/archive/2026-08-19-fengxi177-tcm-kg-cleaning.md`
- 源注册与总量：`../catalog.json`
- 只有 catalog 中显式 `publish: true` 的源才进入 Hugging Face 汇总；许可不明的本地清洗源必须保持 false

| task_id | 源 | 状态 | 计划 | 完成 |
|---------|----|------|------|------|
| `pharmacopoeia-segment-605` | 药典 2022 | done | 605 entries | 605 |
| `pharmacopoeia-extract-605` | 药典 2022 | in_progress | 605 entries | ~595 |
| `pharmacopoeia-merge-latest` | 药典 2022 | planned | 1 latest snapshot | 0 |
| `daoyi-suyang-collect` | 道医苏子阳 | in_progress | 389 chapters 收源 | 0（文件已定位，未拷进 staging） |
| `daoyi-suyang-extract-wave-1` | 道医苏子阳 | planned | 切段后定抽取单元 | 0 |
| `fengxi177-tcm-kg-structural-clean` | Knowlegde_Graph_TCM | done | 19923 relations | 19923 / 4996 records |
| `fengxi177-tcm-kg-public-release` | Knowlegde_Graph_TCM | blocked | 1 source | 0（无许可证） |
| `tcm-sd-structural-clean` | TCM-SD / ZY-BERT | done | 54152 labeled rows | 148 records / 0 edges |
| `tcm-sd-public-release` | TCM-SD / ZY-BERT | blocked | 1 source | 0（CC-BY-NC-SA-4.0 且残留标识） |
| `tcm-ner-structural-clean` | TCM-NER / DeepNER | done | 1000 labeled docs | 0 records / 0 edges |
| `tcm-ner-public-release` | TCM-NER / DeepNER | blocked | 1 source | 0（竞赛镜像无许可证） |
| `tcm-ancient-books-structural-clean` | TCM-Ancient-Books | done | 700 numbered books | 0 records / 0 edges |
| `tcm-ancient-books-public-release` | TCM-Ancient-Books | blocked | 1 source | 0（无许可证） |
| `classical-tcm-canon-structural-clean` | classical-tcm-canon | done | 115 works | 0 records / 0 edges |
| `classical-tcm-canon-public-release` | classical-tcm-canon | blocked | 1 source | 0（proprietary-commercial） |
| `sylvanl-tcm-pretrain-structural-clean` | SylvanL pretrain | done | 177054 text rows | 0 records / 0 edges |
| `sylvanl-tcm-pretrain-public-release` | SylvanL pretrain | blocked | 1 source | 0（内容混杂） |
| `zybert-pretrain-structural-clean` | ZY-BERT rar | done | 1 archive | 0 records / 0 edges |
| `zybert-pretrain-public-release` | ZY-BERT rar | blocked | 1 source | 0（许可不继承） |
| `tcmchat-600k-inventory` | TCMChat-600k | done | 61 files | 0 records / 盘点完成 |
| `tcmchat-600k-public-release` | TCMChat-600k | blocked | 1 source | 0（原文不进 public） |
| `national-standard-terms-structural-clean` | 国标术语/成方 | done | 5219 | 5219 / 0 edges |
| `national-standard-terms-public-release` | 国标术语/成方 | blocked | 1 source | 0（原文不进 public） |
