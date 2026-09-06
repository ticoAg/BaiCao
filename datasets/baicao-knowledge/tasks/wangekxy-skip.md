# wangekxy 跳过记录

判定日期: 2026-08-20。这些资源**不建 catalog 源、不写 cleaner、不入图**。

## NLP 集（不是图谱事实）

| HF id | 原因 |
|---|---|
| `wangekxy/classical-chinese-punctuation` | 文言断句 SFT。标签是标点位置，不是药材/方剂/病证事实。 |
| `wangekxy/classical-chinese-variant-collation` | 异体字/四库对照。校勘对齐任务，不能映射现有 `NodeType`。 |

## 未购买的商业全量

HF 各专题 Dataset Card 只公开 `sample.jsonl`（通常 3 部；类书为 3 卷切片）。下列全量包 **unpaid-full-set-not-held**：

| HF id | 宣称全量 | 已入图范围 |
|---|---|---|
| `wangekxy/classical-tcm-canon` | 115 部全文 | 已持有 parquet，already-imported |
| `wangekxy/tcm-formulary` | 91 部 | 仅 3 部公开样本 already-imported |
| `wangekxy/tcm-materia-medica` | 59 部 | 仅 3 部 sample，判定 go |
| `wangekxy/tcm-case-records` | 33 部 | 仅 3 部 sample，判定 go |
| `wangekxy/tcm-acupuncture-classics` | 33 部 | 仅 3 部 sample，判定 go |
| `wangekxy/tcm-diagnostics` | 42 部 | 仅 3 部 sample，判定 go |
| `wangekxy/tcm-gynecology-pediatrics` | 69 部 | 仅 3 部 sample，判定 go |
| `wangekxy/tcm-external-surgical` | 50 部 | 仅 3 部 sample，判定 go |
| `wangekxy/tcm-collected-works` | 171 部 | 仅 3 部 sample，判定 go |
| `wangekxy/tcm-health-cultivation` | 18 部 | 仅 3 部 sample，判定 go |
| `wangekxy/tcm-reference-compendia` | 14 部 | 仅 3 卷切片，判定 go |

不购买、不下载、不入图上述 unpaid 全量。
