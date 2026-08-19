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
