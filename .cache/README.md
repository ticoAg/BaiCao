# 本地原始数据缓存

本目录不进 Git。原始语料按平台分开放，脚本默认从这里读。

| 平台 | 路径 |
|---|---|
| Hugging Face | `.cache/huggingface/{org}/{dataset}/` |
| GitHub | `.cache/github/{owner}/{repo}/` |
| Dropbox | `.cache/dropbox/{name}/` |
| Zenodo | `.cache/zenodo/{record}/` |

`tmp/qibo-datasets/` 只保留下载说明指针，不再存放正文。
