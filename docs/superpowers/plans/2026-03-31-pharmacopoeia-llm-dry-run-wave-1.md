# 药典条目 LLM dry-run Wave 1 Implementation Plan

> **Status:** done（2026-04）。dry-run CLI 已落地。下方 checkbox 是历史拆解，不要再执行。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `2022年中药药典.txt` 实现一个独立的 `CLI dry-run`，抽样 `10` 条条目执行规则切段、section 解析、LLM 抽取、Pydantic 校验与图谱映射，并把每个环节的中间结果完整落盘。

**Architecture:** 保持 dry-run 主体在 `packages/data_ingestion/`，不直接替换正式 pipeline。通过 `llm_extraction.py` 封装单条条目的 LLM 边界，用 `dry_run.py` 串联切段、解析、抽取、校验和映射，再由 `cli/pharmacopoeia_dry_run.py` 作为触发层输出 `tmp/pharmacopoeia-dry-run/<timestamp>/` 目录。整个链路只在“section payload -> LLM JSON”“LLM JSON -> 文件专属抽取模型”“抽取模型 -> 共享图谱 bundle”三个边界做一次校验。

**Tech Stack:** Python 3.12, Pydantic v2, pytest, LangChain chat model adapter, JSONL artifacts

---

### Task 1: 扩展药典文件专属抽取模型与 prompt 契约

**Files:**
- Modify: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/extraction_models.py`
- Modify: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/prompts.py`
- Create: `packages/data_ingestion/tests/test_pharmacopoeia_llm_contract.py`

- [ ] **Step 1: 先写失败测试，固定 LLM 输入输出契约**

```python
# packages/data_ingestion/tests/test_pharmacopoeia_llm_contract.py
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.extraction_models import (
    PharmacopoeiaEntrySections,
    PharmacopoeiaExtractionResult,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.prompts import (
    build_pharmacopoeia_user_payload,
)


def test_prompt_payload_prefers_piece_sections():
    sections = PharmacopoeiaEntrySections(
        title_zh="一枝黄花",
        header_lines=["Yizhihuanghua", "SOLIDAGINISHERBA"],
        base_description="本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。",
        sections={"性状": "本品长30～100cm。"},
        piece_sections={"性味与归经": "辛、苦，凉。归肺、肝经。"},
        raw_text="一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。\n饮片\n【性味与归经】辛、苦，凉。归肺、肝经。",
    )

    payload = build_pharmacopoeia_user_payload(sections)

    assert payload["entry_title"] == "一枝黄花"
    assert payload["piece_sections"]["性味与归经"].startswith("辛、苦")


def test_extraction_result_accepts_piece_usage_storage_and_notes():
    result = PharmacopoeiaExtractionResult.model_validate(
        {
            "herb": {
                "herb_name": "一枝黄花",
                "pinyin_name": "Yizhihuanghua",
                "latin_name": "SOLIDAGINISHERBA",
                "base_description": "本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。",
            },
            "prepared_piece": {
                "piece_name": "一枝黄花饮片",
                "parent_herb_name": "一枝黄花",
                "processing_text": "除去杂质，喷淋清水，切段，干燥。",
                "flavors": ["辛", "苦"],
                "nature": "凉",
                "meridians": ["肺经", "肝经"],
                "efficacies": ["清热解毒", "疏散风热"],
                "usage_text": "9～15g。",
                "storage_text": "置干燥处。",
                "caution_text": None,
            },
            "warnings": [],
            "confidence_notes": "饮片 section 信息完整。",
        }
    )

    assert result.prepared_piece is not None
    assert result.prepared_piece.usage_text == "9～15g。"
```

- [ ] **Step 2: 运行测试确认当前模型和 prompt 还不够用**

Run:

```bash
cd packages/data_ingestion && uv run --with pytest pytest tests/test_pharmacopoeia_llm_contract.py -q
```

Expected:

- `build_pharmacopoeia_user_payload` 未定义
- `base_description`、`usage_text`、`storage_text`、`caution_text`、`warnings`、`confidence_notes` 尚未进入模型

- [ ] **Step 3: 扩展文件专属模型与 prompt builder**

```python
# extraction_models.py
class PharmacopoeiaHerbExtraction(BaseModel):
    herb_name: str = Field(description="药材名称")
    pinyin_name: str | None = Field(default=None, description="拼音名")
    latin_name: str | None = Field(default=None, description="拉丁名或规范名")
    base_description: str | None = Field(default=None, description="基础描述文本")


class PharmacopoeiaPreparedPieceExtraction(BaseModel):
    piece_name: str = Field(description="饮片名称")
    parent_herb_name: str = Field(description="对应药材名称")
    processing_text: str | None = Field(default=None, description="炮制文本")
    flavors: list[str] = Field(default_factory=list, description="性味列表")
    nature: str | None = Field(default=None, description="药性")
    meridians: list[str] = Field(default_factory=list, description="归经列表")
    efficacies: list[str] = Field(default_factory=list, description="功效列表")
    usage_text: str | None = Field(default=None, description="用法与用量")
    storage_text: str | None = Field(default=None, description="贮藏")
    caution_text: str | None = Field(default=None, description="注意事项")


class PharmacopoeiaExtractionResult(BaseModel):
    herb: PharmacopoeiaHerbExtraction = Field(description="药材抽取结果")
    prepared_piece: PharmacopoeiaPreparedPieceExtraction | None = Field(default=None, description="饮片抽取结果")
    warnings: list[str] = Field(default_factory=list, description="抽取警告")
    confidence_notes: str | None = Field(default=None, description="抽取置信说明")
```

```python
# prompts.py
def build_pharmacopoeia_user_payload(sections: PharmacopoeiaEntrySections) -> dict[str, object]:
    return {
        "entry_title": sections.title_zh,
        "header_lines": sections.header_lines,
        "base_description": sections.base_description,
        "sections": sections.sections,
        "piece_sections": sections.piece_sections,
        "raw_text": sections.raw_text,
    }
```

- [ ] **Step 4: 回跑契约测试**

Run:

```bash
cd packages/data_ingestion && uv run --with pytest pytest tests/test_pharmacopoeia_llm_contract.py -q
```

Expected:

- prompt payload 含 `piece_sections`
- 扩展后的抽取模型能通过校验

- [ ] **Step 5: Commit**

```bash
git add packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/extraction_models.py packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/prompts.py packages/data_ingestion/tests/test_pharmacopoeia_llm_contract.py
git commit -m "feat(data-ingestion): define pharmacopoeia llm extraction contract"
```

### Task 2: 实现单条条目的 LLM 抽取边界

**Files:**
- Create: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/llm_extraction.py`
- Modify: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/__init__.py`
- Create: `packages/data_ingestion/tests/test_pharmacopoeia_llm_extraction.py`

- [ ] **Step 1: 写失败测试，锁定 LLM JSON 校验与错误分类**

```python
# packages/data_ingestion/tests/test_pharmacopoeia_llm_extraction.py
import pytest

from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.extraction_models import (
    PharmacopoeiaEntrySections,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.llm_extraction import (
    FakeExtractionTransport,
    extract_entry_with_llm,
)


@pytest.mark.asyncio
async def test_extract_entry_with_llm_returns_validated_result():
    sections = PharmacopoeiaEntrySections(
        title_zh="一枝黄花",
        header_lines=["Yizhihuanghua", "SOLIDAGINISHERBA"],
        base_description="本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。",
        sections={},
        piece_sections={"性味与归经": "辛、苦，凉。归肺、肝经。"},
        raw_text="一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。",
    )
    transport = FakeExtractionTransport(
        response_text='{"herb":{"herb_name":"一枝黄花"},"prepared_piece":null,"warnings":[],"confidence_notes":"ok"}'
    )

    result = await extract_entry_with_llm(sections, transport)

    assert result.status == "success"
    assert result.validated_extraction is not None
    assert result.validated_extraction.herb.herb_name == "一枝黄花"


@pytest.mark.asyncio
async def test_extract_entry_with_llm_marks_invalid_json():
    sections = PharmacopoeiaEntrySections(
        title_zh="一枝黄花",
        header_lines=[],
        base_description=None,
        sections={},
        piece_sections={},
        raw_text="一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA",
    )
    transport = FakeExtractionTransport(response_text='not-json')

    result = await extract_entry_with_llm(sections, transport)

    assert result.status == "llm_json_invalid"
    assert result.validated_extraction is None
    assert result.error_message
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd packages/data_ingestion && uv run --with pytest pytest tests/test_pharmacopoeia_llm_extraction.py -q
```

Expected:

- `llm_extraction.py` 不存在
- `extract_entry_with_llm` / `FakeExtractionTransport` 未定义

- [ ] **Step 3: 实现 LLM transport 协议、结果对象与校验逻辑**

```python
# llm_extraction.py
class ExtractionTransport(Protocol):
    async def extract_json_text(self, *, system_prompt: str, user_payload: dict[str, object]) -> str:
        raise NotImplementedError


class FakeExtractionTransport:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text

    async def extract_json_text(self, *, system_prompt: str, user_payload: dict[str, object]) -> str:
        return self.response_text


class PharmacopoeiaLLMExtractionRecord(BaseModel):
    entry_title: str
    status: Literal["llm_json_invalid", "llm_schema_invalid", "success"]
    raw_response: str
    error_message: str | None = None
    validated_extraction: PharmacopoeiaExtractionResult | None = None
```

说明：

- 这里的 `status` 只覆盖 LLM 边界本身
- dry-run 总表里的 `mapping_invalid` 由 Task 3 的编排层补记，不塞回单条 LLM transport 结果对象

```python
# llm_extraction.py
async def extract_entry_with_llm(
    sections: PharmacopoeiaEntrySections,
    transport: ExtractionTransport,
) -> PharmacopoeiaLLMExtractionRecord:
    payload = build_pharmacopoeia_user_payload(sections)
    raw_response = await transport.extract_json_text(
        system_prompt=PHARMACOPOEIA_EXTRACTION_SYSTEM_PROMPT,
        user_payload=payload,
    )
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        return PharmacopoeiaLLMExtractionRecord(
            entry_title=sections.title_zh,
            status="llm_json_invalid",
            raw_response=raw_response,
            error_message=str(exc),
        )

    try:
        validated = PharmacopoeiaExtractionResult.model_validate(parsed)
    except ValidationError as exc:
        return PharmacopoeiaLLMExtractionRecord(
            entry_title=sections.title_zh,
            status="llm_schema_invalid",
            raw_response=raw_response,
            error_message=str(exc),
        )

    return PharmacopoeiaLLMExtractionRecord(
        entry_title=sections.title_zh,
        status="success",
        raw_response=raw_response,
        validated_extraction=validated,
    )
```

- [ ] **Step 4: 回跑 LLM 边界测试**

Run:

```bash
cd packages/data_ingestion && uv run --with pytest pytest tests/test_pharmacopoeia_llm_extraction.py -q
```

Expected:

- 合法 JSON 可转成 `PharmacopoeiaExtractionResult`
- 非法 JSON 被标为 `llm_json_invalid`
- schema 不合法可被标为 `llm_schema_invalid`

- [ ] **Step 5: Commit**

```bash
git add packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/llm_extraction.py packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/__init__.py packages/data_ingestion/tests/test_pharmacopoeia_llm_extraction.py
git commit -m "feat(data-ingestion): add pharmacopoeia llm extraction boundary"
```

### Task 3: 实现 10 条 dry-run 编排与结果落盘

**Files:**
- Create: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/dry_run.py`
- Modify: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/mapping.py`
- Create: `packages/data_ingestion/tests/test_pharmacopoeia_dry_run.py`

- [ ] **Step 1: 写失败测试，锁定 dry-run 输出目录与 10 条限制**

```python
# packages/data_ingestion/tests/test_pharmacopoeia_dry_run.py
from pathlib import Path

from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.dry_run import (
    run_pharmacopoeia_dry_run,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.llm_extraction import (
    FakeExtractionTransport,
)


def test_dry_run_writes_expected_artifacts(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_text(
        "一枝黄花\\nYizhihuanghua\\nSOLIDAGINISHERBA\\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。\\n饮片\\n【炮制】除去杂质。\\n【性味与归经】辛、苦，凉。归肺、肝经。\\n【功能与主治】清热解毒，疏散风热。\\n"
        * 2,
        encoding="utf-8",
    )
    transport = FakeExtractionTransport(
        response_text='{"herb":{"herb_name":"一枝黄花"},"prepared_piece":null,"warnings":[],"confidence_notes":"ok"}'
    )

    result = run_pharmacopoeia_dry_run(
        local_path=source,
        output_dir=tmp_path / "out",
        limit=1,
        transport=transport,
    )

    assert result.summary["entries_attempted"] == 1
    assert (result.output_dir / "entries.jsonl").exists()
    assert (result.output_dir / "parsed_sections.jsonl").exists()
    assert (result.output_dir / "llm_requests.jsonl").exists()
    assert (result.output_dir / "llm_responses.jsonl").exists()
    assert (result.output_dir / "validated_extractions.jsonl").exists()
    assert (result.output_dir / "graph_bundles.jsonl").exists()
    assert (result.output_dir / "summary.json").exists()
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd packages/data_ingestion && uv run --with pytest pytest tests/test_pharmacopoeia_dry_run.py -q
```

Expected:

- `dry_run.py` 不存在
- `run_pharmacopoeia_dry_run()` 未定义

- [ ] **Step 3: 实现 dry-run 编排器与 JSONL writer**

```python
# dry_run.py
class DryRunResult(BaseModel):
    output_dir: Path
    summary: dict[str, object]


def run_pharmacopoeia_dry_run(
    *,
    local_path: Path,
    output_dir: Path,
    limit: int,
    entry_offset: int = 0,
    transport: ExtractionTransport,
    provider: str = "huggingface",
    dataset: str = DATASET_NAME,
    file_path: str = PHARMACOPOEIA_2022_FILE_PATH,
    model_name: str | None = None,
    git_commit: str | None = None,
) -> DryRunResult:
    context = SourceFileContext(
        provider=provider,
        dataset=dataset,
        file_path=file_path,
        local_abspath=str(local_path),
        file_size=local_path.stat().st_size,
        line_count=local_path.read_text(encoding="utf-8").count("\\n") + 1,
    )
    all_blocks = segment_pharmacopoeia_entries(context)
    blocks = all_blocks[entry_offset : entry_offset + limit]
    parsed_sections = [parse_pharmacopoeia_entry(block) for block in blocks]
    llm_results = [asyncio.run(extract_entry_with_llm(section, transport)) for section in parsed_sections]
    mapping_records: list[dict[str, object]] = []
    bundles = []
    for block, section, result in zip(blocks, parsed_sections, llm_results, strict=False):
        if result.validated_extraction is None:
            mapping_records.append(
                {
                    "entry_key": f"{block.entry_title}:{block.start_line}-{block.end_line}",
                    "entry_title": block.entry_title,
                    "status": result.status,
                    "error_type": result.status,
                    "error_message": result.error_message,
                    "validated_extraction": None,
                }
            )
            continue
        try:
            bundle = build_pharmacopoeia_bundle(block, section, result.validated_extraction)
        except Exception as exc:
            mapping_records.append(
                {
                    "entry_key": f"{block.entry_title}:{block.start_line}-{block.end_line}",
                    "entry_title": block.entry_title,
                    "status": "mapping_invalid",
                    "error_type": "mapping_invalid",
                    "error_message": str(exc),
                    "validated_extraction": result.validated_extraction.model_dump(mode="json"),
                }
            )
            continue
        bundles.append(bundle)
        mapping_records.append(
            {
                "entry_key": f"{block.entry_title}:{block.start_line}-{block.end_line}",
                "entry_title": block.entry_title,
                "status": "success",
                "error_type": None,
                "error_message": None,
                "validated_extraction": result.validated_extraction.model_dump(mode="json"),
            }
        )
    return write_dry_run_artifacts(
        output_dir=output_dir,
        context=context,
        all_blocks=all_blocks,
        blocks=blocks,
        parsed_sections=parsed_sections,
        llm_results=llm_results,
        mapping_records=mapping_records,
        bundles=bundles,
        limit=limit,
        entry_offset=entry_offset,
        model_name=model_name,
        git_commit=git_commit,
    )
```

```python
# dry_run.py
def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "\\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\\n",
        encoding="utf-8",
    )
```

`run_pharmacopoeia_dry_run()` 需要至少写出：

- `run_config.json`
- `entries.jsonl`
- `parsed_sections.jsonl`
- `llm_requests.jsonl`
- `llm_responses.jsonl`
- `validated_extractions.jsonl`
- `graph_bundles.jsonl`
- `summary.json`
- `README.md`

额外要求：

- `entry_offset` 必须在切段结果上先切偏移，再应用 `limit`
- `run_config.json` 必须显式记录 `entry_offset`、`model_name`、`git_commit`
- `validated_extractions.jsonl` 以 `mapping_records` 为准，确保单条 bundle 映射失败时仍然继续处理剩余条目

- [ ] **Step 4: 回跑 dry-run 测试**

Run:

```bash
cd packages/data_ingestion && uv run --with pytest pytest tests/test_pharmacopoeia_dry_run.py -q
```

Expected:

- 输出目录创建成功
- 限制条目数生效
- 关键工件文件全部存在
- `summary["entries_attempted"] == limit`

- [ ] **Step 5: Commit**

```bash
git add packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/dry_run.py packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/mapping.py packages/data_ingestion/tests/test_pharmacopoeia_dry_run.py
git commit -m "feat(data-ingestion): add pharmacopoeia dry-run orchestration"
```

### Task 4: 实现 CLI 入口与最小手工验证

**Files:**
- Create: `packages/data_ingestion/data_ingestion/cli/__init__.py`
- Create: `packages/data_ingestion/data_ingestion/cli/pharmacopoeia_dry_run.py`
- Modify: `packages/data_ingestion/pyproject.toml`
- Modify: `packages/data_ingestion/README.md`
- Create: `packages/data_ingestion/tests/test_pharmacopoeia_cli.py`

- [ ] **Step 1: 写失败测试，固定 CLI 参数与默认值**

```python
# packages/data_ingestion/tests/test_pharmacopoeia_cli.py
from data_ingestion.cli.pharmacopoeia_dry_run import build_parser


def test_cli_parser_sets_limit_to_ten_by_default():
    parser = build_parser()
    args = parser.parse_args(
        [
            "--provider", "huggingface",
            "--dataset", "ZJUFanLab/TCMChat-dataset-600k",
            "--file-path", "pretrain/train/books/national_standard/2022年中药药典.txt",
            "--local-path", ".cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt",
        ]
    )

    assert args.limit == 10
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd packages/data_ingestion && uv run --with pytest pytest tests/test_pharmacopoeia_cli.py -q
```

Expected:

- `cli/pharmacopoeia_dry_run.py` 不存在
- `build_parser()` 未定义

- [ ] **Step 3: 实现 CLI 入口**

```python
# packages/data_ingestion/data_ingestion/cli/pharmacopoeia_dry_run.py
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="药典条目 LLM dry-run 工具")
    parser.add_argument("--provider", default="huggingface")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--file-path", required=True)
    parser.add_argument("--local-path", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output-dir", default="tmp/pharmacopoeia-dry-run")
    parser.add_argument("--entry-offset", type=int, default=0)
    return parser
```

同时在 `README.md` 增补一段用法：

```bash
cd packages/data_ingestion
uv run python -m data_ingestion.cli.pharmacopoeia_dry_run \
  --dataset ZJUFanLab/TCMChat-dataset-600k \
  --file-path pretrain/train/books/national_standard/2022年中药药典.txt \
  --local-path ../../.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt \
  --limit 10
```

- [ ] **Step 4: 回跑 CLI 测试**

Run:

```bash
cd packages/data_ingestion && uv run --with pytest pytest tests/test_pharmacopoeia_cli.py -q
```

Expected:

- 默认 `limit = 10`
- CLI 参数能被正确解析

- [ ] **Step 5: 执行最小手工 dry-run 验证**

Run:

```bash
cd packages/data_ingestion
uv run python -m data_ingestion.cli.pharmacopoeia_dry_run \
  --dataset ZJUFanLab/TCMChat-dataset-600k \
  --file-path pretrain/train/books/national_standard/2022年中药药典.txt \
  --local-path ../../.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt \
  --limit 10
```

Expected:

- 生成新的 `tmp/pharmacopoeia-dry-run/<timestamp>/`
- 终端输出 `entries_attempted=10`
- `summary.json`、`entries.jsonl`、`validated_extractions.jsonl` 存在

- [ ] **Step 6: Commit**

```bash
git add packages/data_ingestion/data_ingestion/cli/__init__.py packages/data_ingestion/data_ingestion/cli/pharmacopoeia_dry_run.py packages/data_ingestion/pyproject.toml packages/data_ingestion/README.md packages/data_ingestion/tests/test_pharmacopoeia_cli.py
git commit -m "feat(data-ingestion): add pharmacopoeia llm dry-run cli"
```
