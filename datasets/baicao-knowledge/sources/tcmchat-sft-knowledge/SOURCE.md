# TCMChat SFT knowledge.json

## 身份

- `source_id`: `tcmchat-sft-knowledge`
- 载体：`.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/sft/train/knowledge.json`（70,309 条指令）
- 状态：`imported`（已入本地图，不当已验证事实）；结构化介绍/处方/证候等已扩抽
- `publish: false`；不当已验证临床事实

## 抽取口径

不只吃「方剂-介绍 / 中药介绍」。同文件里的处方、功效主治、证候、性味归经、配伍一并抽取。跳过基因、西医疾病、单体化合物、药理、简单成分、效用分析和「以下是」自由文本。名称含「注射」或品牌丢弃。

产量见 `processed/latest/stats.json`：7,459 records（方剂 5,906、药材 659、词表病证提及 894），边 75,949。整理时滤品牌与 PII。
