# 药典条目图谱化 Wave 1 Implementation Plan

> **Status:** done（2026-04）。处理器与模型扩展已落地。全量收口走 `2026-08-16-baicao-knowledge-dataset.md`。下方 checkbox 是历史拆解，不要再执行。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt` 落地一条 protocol-first、模块化、边界单次校验的图谱化处理链，稳定产出 `药材 / 饮片 / 证据 / 性味 / 归经 / 功效` 及其中文关系。

**Architecture:** 先扩展 `packages/knowledge_model/` 的共享中文真源，再在 `packages/data_ingestion/` 建立文件路由与处理器协议，随后实现 `2022年中药药典.txt` 专属处理器，最后把统一 bundle 接入 API pipeline 预览与导出主链路。整个链路只在“原文 -> 条目块”“条目块 -> 文件专属抽取结果”“抽取结果 -> 共享图谱模型”三个边界做一次 Pydantic 校验。

**Tech Stack:** Python 3.12, Pydantic v2, FastAPI, LangChain chat model adapter, pytest, Neo4j export bundle

---

### Task 1: 扩展共享中文图谱真源

**Files:**
- Modify: `packages/knowledge_model/knowledge_model/constants.py`
- Modify: `packages/knowledge_model/knowledge_model/labels.py`
- Modify: `packages/knowledge_model/knowledge_model/node_models.py`
- Modify: `packages/knowledge_model/knowledge_model/edge_models.py`
- Modify: `packages/knowledge_model/knowledge_model/schema.py`
- Modify: `packages/knowledge_model/knowledge_model/import_records.py`
- Modify: `packages/knowledge_model/knowledge_model/__init__.py`
- Test: `packages/knowledge_model/tests/test_constants.py`
- Test: `packages/knowledge_model/tests/test_schema.py`

- [ ] **Step 1: 先写失败测试，固定中文节点/关系真源和新模型边界**

```python
# packages/knowledge_model/tests/test_constants.py
def test_node_type_exposes_prepared_piece_and_evidence():
    assert NodeType.PREPARED_HERB == "饮片"
    assert NodeType.EVIDENCE == "证据"


def test_edge_type_exposes_chinese_content_relations():
    assert EdgeType.HAS_PREPARED_FORM == "具有饮片"
    assert EdgeType.SUPPORTED_BY == "由证据支持"
```

```python
# packages/knowledge_model/tests/test_schema.py
from knowledge_model.node_models import EvidenceNodeModel, PreparedHerbNodeModel


def test_prepared_herb_node_model_accepts_parent_reference():
    node = PreparedHerbNodeModel(
        id="饮片:一枝黄花饮片",
        name="一枝黄花饮片",
        source="huggingface",
        prepared_from_herb="一枝黄花",
    )
    assert node.type == NodeType.PREPARED_HERB


def test_evidence_node_model_requires_source_location_fields():
    node = EvidenceNodeModel(
        id="证据:test",
        name="一枝黄花条目证据",
        source="huggingface",
        raw_text="一枝黄花\\nYizhihuanghua",
        source_provider="huggingface",
        dataset_name="ZJUFanLab/TCMChat-dataset-600k",
        file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
        entry_title="一枝黄花",
        line_start=1,
        line_end=21,
        chunk_hash="abc123",
    )
    assert node.type == NodeType.EVIDENCE
```

- [ ] **Step 2: 运行测试确认当前实现尚未覆盖这些对象**

Run:

```bash
cd packages/knowledge_model && uv run pytest tests/test_constants.py tests/test_schema.py -q
```

Expected:

- `NodeType.PREPARED_HERB` / `NodeType.EVIDENCE` 不存在
- `EdgeType.HAS_PREPARED_FORM` / `EdgeType.SUPPORTED_BY` 不存在
- `PreparedHerbNodeModel` / `EvidenceNodeModel` 未定义

- [ ] **Step 3: 扩展常量、标签和共享节点模型**

```python
# packages/knowledge_model/knowledge_model/constants.py
class NodeType(StrEnum):
    HERB = "药材"
    PREPARED_HERB = "饮片"
    COMPONENT = "成分"
    VARIANT = "品种"
    PROCESS = "工艺"
    TRAIT = "性状"
    EFFICACY = "功效"
    FLAVOR = "性味"
    MERIDIAN = "归经"
    DISEASE = "病证"
    TIMEPOINT = "时间点"
    SOURCE = "来源"
    EVIDENCE = "证据"


class EdgeType(StrEnum):
    HAS_PREPARED_FORM = "具有饮片"
    HAS_FLAVOR = "具有性味"
    ENTERS_MERIDIAN = "归于经脉"
    HAS_EFFICACY = "具有功效"
    SUPPORTED_BY = "由证据支持"
    CONTAINS = "包含成分"
    EXTRACTED_FROM = "提取自"
    HAS_VARIANT = "具有品种"
    VARIANT_OF = "属于药材"
    PROCESSED_BY = "经过工艺"
    APPLIES_TO = "适用于"
    STORED_FOR = "储存时间"
    HAS_TRAIT = "具有性状"
    OBSERVED_IN = "观察于"
    TREATS = "治疗病证"
    INTERACTS_WITH = "相互作用"
    SIMILAR_TO = "相似于"
    ORIGINATED_FROM = "来源于"
```

```python
# packages/knowledge_model/knowledge_model/node_models.py
class PreparedHerbNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.PREPARED_HERB, description="节点类型：饮片")
    prepared_from_herb: str | None = Field(default=None, description="对应药材名称")
    processing_method_text: str | None = Field(default=None, description="炮制方法原文")
    description: str | None = Field(default=None, description="饮片说明")


class EvidenceNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.EVIDENCE, description="节点类型：证据")
    raw_text: str = Field(description="证据原文")
    source_provider: str = Field(description="来源提供方")
    dataset_name: str = Field(description="来源数据集名称")
    file_path: str = Field(description="来源文件路径")
    entry_title: str = Field(description="条目标题")
    line_start: int = Field(description="起始行号")
    line_end: int = Field(description="结束行号")
    chunk_hash: str = Field(description="证据块哈希")
```

```python
# packages/knowledge_model/knowledge_model/schema.py
GraphNodeModel = Annotated[
    HerbNodeModel
    | PreparedHerbNodeModel
    | ComponentNodeModel
    | VariantNodeModel
    | EfficacyNodeModel
    | FlavorNodeModel
    | MeridianNodeModel
    | DiseaseNodeModel
    | TimePointNodeModel
    | EvidenceNodeModel,
    Field(discriminator="type"),
]
```

- [ ] **Step 4: 让导入记录能承载证据引用**

```python
# packages/knowledge_model/knowledge_model/import_records.py
class GraphImportEdge(BaseModel):
    type: EdgeType = Field(description="导入边类型")
    target: str = Field(description="目标节点名称或标识")
    properties: dict[str, object] = Field(default_factory=dict, description="边属性集合")


class GraphImportRecord(BaseModel):
    node_type: NodeType | None = Field(default=None, description="导入节点类型")
    node_name: str = Field(description="导入节点名称")
    source: str = Field(description="导入数据来源")
    evidence_refs: list[str] = Field(default_factory=list, description="关联证据标识列表")
    properties: dict[str, object] = Field(default_factory=dict, description="节点属性集合")
    edges: list[GraphImportEdge] = Field(default_factory=list, description="与当前节点关联的边列表")
```

- [ ] **Step 5: 重新运行共享模型测试**

Run:

```bash
cd packages/knowledge_model && uv run pytest tests/test_constants.py tests/test_schema.py -q
```

Expected:

- 新节点类型与关系类型测试通过
- `PreparedHerbNodeModel` / `EvidenceNodeModel` schema 描述存在
- `GraphImportRecord` 能承载 `evidence_refs`

- [ ] **Step 6: Commit**

```bash
git add packages/knowledge_model/knowledge_model/constants.py packages/knowledge_model/knowledge_model/labels.py packages/knowledge_model/knowledge_model/node_models.py packages/knowledge_model/knowledge_model/edge_models.py packages/knowledge_model/knowledge_model/schema.py packages/knowledge_model/knowledge_model/import_records.py packages/knowledge_model/knowledge_model/__init__.py packages/knowledge_model/tests/test_constants.py packages/knowledge_model/tests/test_schema.py
git commit -m "feat(knowledge-model): add prepared herb and evidence graph types"
```

### Task 2: 建立 data_ingestion 协议层与路由注册表

**Files:**
- Create: `packages/data_ingestion/data_ingestion/source_models.py`
- Create: `packages/data_ingestion/data_ingestion/bundles.py`
- Create: `packages/data_ingestion/data_ingestion/protocols.py`
- Create: `packages/data_ingestion/data_ingestion/routing.py`
- Modify: `packages/data_ingestion/data_ingestion/__init__.py`
- Modify: `packages/data_ingestion/tests/test_models.py`
- Create: `packages/data_ingestion/tests/test_routing.py`

- [ ] **Step 1: 写失败测试，固定 route key 与处理器协议**

```python
# packages/data_ingestion/tests/test_routing.py
from data_ingestion.routing import FileRouteKey, ProcessorRegistry


def test_registry_prefers_exact_file_match():
    registry = ProcessorRegistry()
    registry.register(
        FileRouteKey(
            provider="huggingface",
            dataset="ZJUFanLab/TCMChat-dataset-600k",
            file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
        ),
        object,
    )

    resolved = registry.resolve(
        provider="huggingface",
        dataset="ZJUFanLab/TCMChat-dataset-600k",
        file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
    )
    assert resolved is object
```

```python
# packages/data_ingestion/tests/test_models.py
from data_ingestion.source_models import RawEntryBlock, SourceFileContext


def test_raw_entry_block_keeps_source_context():
    context = SourceFileContext(
        provider="huggingface",
        dataset="ZJUFanLab/TCMChat-dataset-600k",
        file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
        local_abspath="/tmp/2022.txt",
        file_size=10,
        line_count=20,
    )
    block = RawEntryBlock(
        entry_id="entry-1",
        entry_title="一枝黄花",
        raw_text="一枝黄花\\nYizhihuanghua",
        start_line=1,
        end_line=21,
        context=context,
    )
    assert block.context.dataset == "ZJUFanLab/TCMChat-dataset-600k"
```

- [ ] **Step 2: 运行测试确认协议层尚未落地**

Run:

```bash
cd packages/data_ingestion && uv run pytest tests/test_models.py tests/test_routing.py -q
```

Expected:

- `source_models.py` / `routing.py` 不存在
- `FileRouteKey` / `ProcessorRegistry` / `RawEntryBlock` 未定义

- [ ] **Step 3: 实现共享 source models、bundle 和协议**

```python
# packages/data_ingestion/data_ingestion/source_models.py
class SourceFileContext(BaseModel):
    provider: str = Field(description="来源提供方")
    dataset: str = Field(description="来源数据集")
    file_path: str = Field(description="来源文件路径")
    local_abspath: str = Field(description="本地文件绝对路径")
    file_size: int = Field(description="文件大小")
    line_count: int = Field(description="文件总行数")


class RawEntryBlock(BaseModel):
    entry_id: str = Field(description="条目标识")
    entry_title: str = Field(description="条目标题")
    raw_text: str = Field(description="条目原文")
    start_line: int = Field(description="起始行号")
    end_line: int = Field(description="结束行号")
    context: SourceFileContext = Field(description="来源上下文")
```

```python
# packages/data_ingestion/data_ingestion/protocols.py
class FileProcessor(Protocol):
    route_key: FileRouteKey

    def segment(self, context: SourceFileContext) -> list[RawEntryBlock]:
        raise NotImplementedError

    def process_entry(self, block: RawEntryBlock) -> UnifiedGraphBundle:
        raise NotImplementedError
```

```python
# packages/data_ingestion/data_ingestion/routing.py
@dataclass(frozen=True)
class FileRouteKey:
    provider: str
    dataset: str
    file_path: str


class ProcessorRegistry:
    def __init__(self) -> None:
        self._entries: list[tuple[FileRouteKey, type[FileProcessor]]] = []
```

- [ ] **Step 4: 导出新协议并补齐 schema 描述测试**

Run:

```bash
cd packages/data_ingestion && uv run pytest tests/test_models.py tests/test_routing.py -q
```

Expected:

- `SourceFileContext` / `RawEntryBlock` schema 描述存在
- `ProcessorRegistry.resolve()` 能返回精确文件级匹配

- [ ] **Step 5: Commit**

```bash
git add packages/data_ingestion/data_ingestion/source_models.py packages/data_ingestion/data_ingestion/bundles.py packages/data_ingestion/data_ingestion/protocols.py packages/data_ingestion/data_ingestion/routing.py packages/data_ingestion/data_ingestion/__init__.py packages/data_ingestion/tests/test_models.py packages/data_ingestion/tests/test_routing.py
git commit -m "feat(data-ingestion): add routing and shared processing protocols"
```

### Task 3: 落地药典文件专属切段与章节解析处理器

**Files:**
- Create: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/shared.py`
- Create: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/__init__.py`
- Create: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/segmentation.py`
- Create: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/parsing.py`
- Create: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/extraction_models.py`
- Create: `packages/data_ingestion/tests/test_pharmacopoeia_segmentation.py`
- Create: `packages/data_ingestion/tests/test_pharmacopoeia_parsing.py`

- [ ] **Step 1: 写失败测试，固定“一枝黄花”条目切段边界与 `饮片` 解析结果**

```python
# packages/data_ingestion/tests/test_pharmacopoeia_segmentation.py
def test_segmenter_extracts_first_herb_entry_from_sample(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_text(
        "一枝黄花\\nYizhihuanghua\\nSOLIDAGINISHERBA\\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。\\n饮片\\n【炮制】除去杂质\\n【性味与归经】辛、苦，凉。归肺、肝经。\\n丁香\\nDingxiang\\n",
        encoding="utf-8",
    )
    context = SourceFileContext(
        provider="huggingface",
        dataset="ZJUFanLab/TCMChat-dataset-600k",
        file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
        local_abspath=str(source),
        file_size=source.stat().st_size,
        line_count=source.read_text(encoding="utf-8").count("\\n") + 1,
    )
    blocks = segment_pharmacopoeia_entries(context)
    assert blocks[0].entry_title == "一枝黄花"
    assert "饮片" in blocks[0].raw_text
    assert blocks[0].end_line < context.line_count
```

```python
# packages/data_ingestion/tests/test_pharmacopoeia_parsing.py
def test_parser_extracts_piece_sections():
    block = RawEntryBlock(
        entry_id="entry-1",
        entry_title="一枝黄花",
        raw_text="一枝黄花\\nYizhihuanghua\\nSOLIDAGINISHERBA\\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。\\n饮片\\n【炮制】除去杂质\\n【性味与归经】辛、苦，凉。归肺、肝经。\\n【功能与主治】清热解毒，疏散风热。",
        start_line=1,
        end_line=8,
        context=SourceFileContext(
            provider="huggingface",
            dataset="ZJUFanLab/TCMChat-dataset-600k",
            file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
            local_abspath="/tmp/sample.txt",
            file_size=128,
            line_count=8,
        ),
    )
    parsed = parse_pharmacopoeia_entry(block)
    assert parsed.title_zh == "一枝黄花"
    assert parsed.piece_sections["炮制"] == "除去杂质"
    assert parsed.piece_sections["性味与归经"].startswith("辛、苦")
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd packages/data_ingestion && uv run pytest tests/test_pharmacopoeia_segmentation.py tests/test_pharmacopoeia_parsing.py -q
```

Expected:

- `segment_pharmacopoeia_entries` / `parse_pharmacopoeia_entry` 不存在
- 药典文件专属模型未定义

- [ ] **Step 3: 实现切段器与条目解析器**

```python
# segmentation.py
ENTRY_HEADER_RE = re.compile(r"^[一-龥]{2,20}$")


def segment_pharmacopoeia_entries(context: SourceFileContext) -> list[RawEntryBlock]:
    lines = Path(context.local_abspath).read_text(encoding="utf-8").splitlines()
    starts = [index for index, line in enumerate(lines) if _looks_like_entry_title(line)]
    blocks: list[RawEntryBlock] = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] - 1 if idx + 1 < len(starts) else len(lines) - 1
        chunk = "\\n".join(lines[start : end + 1]).strip()
        blocks.append(
            RawEntryBlock(
                entry_id=f"{context.dataset}:{context.file_path}:{lines[start]}:{start + 1}",
                entry_title=lines[start].strip(),
                raw_text=chunk,
                start_line=start + 1,
                end_line=end + 1,
                context=context,
            )
        )
    return blocks
```

```python
# parsing.py
SECTION_RE = re.compile(r"【([^】]+)】")


def parse_pharmacopoeia_entry(block: RawEntryBlock) -> PharmacopoeiaEntrySections:
    before_piece, piece_text = _split_piece_text(block.raw_text)
    return PharmacopoeiaEntrySections(
        title_zh=block.entry_title,
        header_lines=_extract_header_lines(before_piece),
        base_description=_extract_base_description(before_piece),
        sections=_extract_sections(before_piece),
        piece_sections=_extract_sections(piece_text) if piece_text else {},
        raw_text=block.raw_text,
    )
```

- [ ] **Step 4: 重新运行切段与解析测试**

Run:

```bash
cd packages/data_ingestion && uv run pytest tests/test_pharmacopoeia_segmentation.py tests/test_pharmacopoeia_parsing.py -q
```

Expected:

- 能稳定切出 `一枝黄花` 条目块
- 解析器能把 `饮片` 内的 `炮制 / 性味与归经 / 功能与主治` 拆开

- [ ] **Step 5: Commit**

```bash
git add packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/shared.py packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/__init__.py packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/segmentation.py packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/parsing.py packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/extraction_models.py packages/data_ingestion/tests/test_pharmacopoeia_segmentation.py packages/data_ingestion/tests/test_pharmacopoeia_parsing.py
git commit -m "feat(data-ingestion): add pharmacopoeia entry segmentation"
```

### Task 4: 实现条目级 LLM 抽取、证据节点构造与图谱映射

**Files:**
- Create: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/prompts.py`
- Create: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/normalization.py`
- Create: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/mapping.py`
- Create: `packages/data_ingestion/tests/test_pharmacopoeia_mapping.py`
- Modify: `packages/data_ingestion/data_ingestion/bundles.py`
- Modify: `packages/data_ingestion/data_ingestion/protocols.py`

- [ ] **Step 1: 先写失败测试，固定 `一枝黄花` 的 bundle 输出**

```python
# packages/data_ingestion/tests/test_pharmacopoeia_mapping.py
def test_mapping_builds_herb_piece_evidence_bundle():
    parsed = PharmacopoeiaEntrySections(
        title_zh="一枝黄花",
        header_lines=["Yizhihuanghua", "SOLIDAGINISHERBA"],
        base_description="本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。",
        sections={},
        piece_sections={
            "炮制": "除去杂质，喷淋清水，切段，干燥。",
            "性味与归经": "辛、苦，凉。归肺、肝经。",
            "功能与主治": "清热解毒，疏散风热。",
        },
        raw_text="一枝黄花\\nYizhihuanghua\\nSOLIDAGINISHERBA\\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。\\n饮片\\n【炮制】除去杂质，喷淋清水，切段，干燥。\\n【性味与归经】辛、苦，凉。归肺、肝经。\\n【功能与主治】清热解毒，疏散风热。",
    )
    block = RawEntryBlock(
        entry_id="entry-1",
        entry_title="一枝黄花",
        raw_text=parsed.raw_text,
        start_line=1,
        end_line=8,
        context=SourceFileContext(
            provider="huggingface",
            dataset="ZJUFanLab/TCMChat-dataset-600k",
            file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
            local_abspath="/tmp/2022.txt",
            file_size=512,
            line_count=8,
        ),
    )
    extraction = PharmacopoeiaExtractionResult(
        herb=PharmacopoeiaHerbExtraction(herb_name="一枝黄花"),
        prepared_piece=PharmacopoeiaPreparedPieceExtraction(
            piece_name="一枝黄花饮片",
            parent_herb_name="一枝黄花",
            processing_text="除去杂质，喷淋清水，切段，干燥。",
            flavors=["辛", "苦"],
            nature="凉",
            meridians=["肺经", "肝经"],
            efficacies=["清热解毒", "疏散风热"],
        ),
    )
    bundle = build_pharmacopoeia_bundle(block, parsed, extraction)
    assert {node.name for node in bundle.nodes} >= {"一枝黄花", "一枝黄花饮片", "辛", "苦", "肺经", "肝经"}
    assert any(edge.type == EdgeType.HAS_PREPARED_FORM for edge in bundle.edges)
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd packages/data_ingestion && uv run pytest tests/test_pharmacopoeia_mapping.py -q
```

Expected:

- `build_pharmacopoeia_bundle` 不存在
- `UnifiedGraphBundle` 尚未承载共享节点 / 边集合

- [ ] **Step 3: 实现文件专属抽取模型、prompt 与归一化**

```python
# prompts.py
PHARMACOPOEIA_EXTRACTION_SYSTEM_PROMPT = """
你是白草药坛的数据抽取助手。
只根据输入条目抽取结构化字段，不补充常识，不生成未出现的字段。
无法确定时返回 null 或空数组。
"""
```

```python
# normalization.py
def normalize_flavors_and_nature(text: str) -> tuple[list[str], str | None]:
    parts = [part.strip() for part in re.split(r"[、，,]", text.split("。", 1)[0]) if part.strip()]
    flavors = [part for part in parts if part in {"辛", "甘", "苦", "酸", "咸", "淡", "涩"}]
    nature = next((part for part in parts if part in {"寒", "热", "温", "凉", "平", "微寒", "微温"}), None)
    return flavors, nature
```

- [ ] **Step 4: 实现证据节点与统一 bundle 映射**

```python
# mapping.py
def build_pharmacopoeia_bundle(
    block: RawEntryBlock,
    parsed: PharmacopoeiaEntrySections,
    extraction: PharmacopoeiaExtractionResult,
) -> UnifiedGraphBundle:
    evidence = EvidenceNodeModel(
        id=build_evidence_id(block),
        name=f"{block.entry_title}条目证据",
        source=block.context.provider,
        raw_text=block.raw_text,
        source_provider=block.context.provider,
        dataset_name=block.context.dataset,
        file_path=block.context.file_path,
        entry_title=block.entry_title,
        line_start=block.start_line,
        line_end=block.end_line,
        chunk_hash=hash_text(block.raw_text),
    )
    herb = HerbNodeModel(id=f"药材:{extraction.herb.herb_name}", name=extraction.herb.herb_name, source=block.context.provider)
    piece = PreparedHerbNodeModel(
        id=f"饮片:{extraction.prepared_piece.piece_name}",
        name=extraction.prepared_piece.piece_name,
        source=block.context.provider,
        prepared_from_herb=extraction.herb.herb_name,
        processing_method_text=extraction.prepared_piece.processing_text,
    )
    return UnifiedGraphBundle(
        nodes=[evidence, herb, piece, *build_flavor_nodes(extraction), *build_meridian_nodes(extraction), *build_efficacy_nodes(extraction)],
        edges=build_relation_edges(herb=herb, piece=piece, evidence=evidence, extraction=extraction),
        records=build_import_records(herb=herb, piece=piece, evidence=evidence, extraction=extraction),
        warnings=[],
        errors=[],
        stats={"entries_processed": 1, "entry_titles": [block.entry_title]},
    )
```

- [ ] **Step 5: 重新运行映射测试**

Run:

```bash
cd packages/data_ingestion && uv run pytest tests/test_pharmacopoeia_mapping.py -q
```

Expected:

- bundle 中包含 `药材 / 饮片 / 证据 / 性味 / 归经 / 功效`
- 边中包含 `具有饮片` 与 `由证据支持`
- 输出记录可映射为 `GraphImportRecord`

- [ ] **Step 6: Commit**

```bash
git add packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/prompts.py packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/normalization.py packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/mapping.py packages/data_ingestion/data_ingestion/bundles.py packages/data_ingestion/data_ingestion/protocols.py packages/data_ingestion/tests/test_pharmacopoeia_mapping.py
git commit -m "feat(data-ingestion): map pharmacopoeia entries to graph bundle"
```

### Task 5: 接入 API pipeline 预览、导出与最小验收闭环

**Files:**
- Create: `packages/api/app/pipeline/structured_extraction.py`
- Create: `packages/api/app/pipeline/processor_runtime.py`
- Modify: `packages/api/app/api/pipeline_dependencies.py`
- Modify: `packages/api/app/pipeline/service.py`
- Modify: `packages/api/app/pipeline/steps/source_preview.py`
- Modify: `packages/api/app/pipeline/steps/normalize.py`
- Modify: `packages/api/app/pipeline/steps/extract.py`
- Modify: `packages/api/app/pipeline/steps/map_to_knowledge_model.py`
- Modify: `packages/api/app/export/service.py`
- Modify: `packages/api/tests/unit/pipeline/test_service.py`
- Create: `packages/api/tests/unit/pipeline/test_processor_runtime.py`
- Modify: `packages/api/tests/contract/test_import_record_contract.py`
- Modify: `docs/acceptance/data-ingestion-and-knowledge-model.md`

- [ ] **Step 1: 写失败测试，固定 pipeline 对专属处理器的消费边界**

```python
# packages/api/tests/unit/pipeline/test_processor_runtime.py
@pytest.mark.asyncio
async def test_runtime_resolves_pharmacopoeia_processor_for_cached_file(tmp_path):
    runtime = build_processor_runtime()
    context = runtime.build_file_context(
        provider="huggingface",
        dataset="ZJUFanLab/TCMChat-dataset-600k",
        file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
        local_abspath=str(tmp_path / "2022.txt"),
    )
    processor = runtime.resolve_processor(context)
    assert processor.route_key.file_path.endswith("2022年中药药典.txt")
```

```python
# packages/api/tests/unit/pipeline/test_service.py
@pytest.mark.asyncio
async def test_mapping_step_returns_bundle_nodes_for_pharmacopoeia_entry(tmp_path, monkeypatch):
    source = tmp_path / "2022.txt"
    source.write_text(
        "一枝黄花\\nYizhihuanghua\\nSOLIDAGINISHERBA\\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。\\n饮片\\n【炮制】除去杂质，喷淋清水，切段，干燥。\\n【性味与归经】辛、苦，凉。归肺、肝经。\\n【功能与主治】清热解毒，疏散风热。\\n",
        encoding="utf-8",
    )
    service = PipelineService()
    run = await service.create_run(
        source_type="huggingface_repo",
        source_locator="ZJUFanLab/TCMChat-dataset-600k",
        source_payload={
            "source_type": "huggingface_repo",
            "source_input": {"repo_id": "ZJUFanLab/TCMChat-dataset-600k"},
        },
    )
    preview = await service.preview_step(run.id, PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL)
    assert preview.preview_kind == "graph_mapping"
    assert any(node["type"] == "证据" for node in preview.preview_payload["nodes"])
    assert any(edge["type"] == "具有饮片" for edge in preview.preview_payload["edges"])
```

- [ ] **Step 2: 运行 API 侧失败测试**

Run:

```bash
cd packages/api && uv run pytest tests/unit/pipeline/test_processor_runtime.py tests/unit/pipeline/test_service.py tests/contract/test_import_record_contract.py -q
```

Expected:

- `processor_runtime.py` / `structured_extraction.py` 不存在
- `MAP_TO_KNOWLEDGE_MODEL` 预览还不会返回条目级 bundle

- [ ] **Step 3: 创建 API 侧运行时适配器，复用现有 LLM client**

```python
# packages/api/app/pipeline/structured_extraction.py
class PipelineStructuredExtractionClient:
    async def extract_json(self, system_prompt: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        model = get_chat_model()
        if model is None:
            raise ValueError("LLM provider unavailable for pharmacopoeia extraction")
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=json.dumps(user_payload, ensure_ascii=False)),
        ]
        response = await model.ainvoke(messages)
        content = _normalize_chunk_content(response.content)
        return cast(dict[str, Any], json.loads(content))
```

```python
# packages/api/app/pipeline/processor_runtime.py
class PipelineProcessorRuntime:
    def __init__(self, extraction_client: PipelineStructuredExtractionClient) -> None:
        self.registry = build_default_registry()
        self.extraction_client = extraction_client
```

- [ ] **Step 4: 让 pipeline 的 `normalize / extract / map_to_knowledge_model` 消费统一 bundle**

```python
# packages/api/app/pipeline/service.py
if self.processor_runtime is not None and materialized_source is not None:
    processed_bundle = await self.processor_runtime.process_materialized_source(
        run=run,
        materialized_source=materialized_source,
    )
```

```python
# packages/api/app/pipeline/steps/extract.py
if bundle is not None:
    return build_preview_response(
        context=context,
        step=PipelineStepKey.EXTRACT,
        summary="药典条目结构化抽取预览已生成",
        preview_kind="extraction_candidates",
        preview_payload={
            "bundle_stats": bundle.stats,
            "entry_count": bundle.stats["entries_processed"],
            "entry_titles": bundle.stats["entry_titles"],
        },
        warnings=[],
        errors=[],
        next_step_ready=True,
    )
```

```python
# packages/api/app/pipeline/steps/map_to_knowledge_model.py
if bundle is not None:
    return build_preview_response(
        context=context,
        step=PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL,
        summary="药典条目图谱映射预览已生成",
        preview_kind="graph_mapping",
        preview_payload={
            "nodes": [node.model_dump(mode="json") for node in bundle.nodes],
            "edges": [edge.model_dump(mode="json") for edge in bundle.edges],
            "validation": {"is_valid": True, "passed": len(bundle.nodes), "failed": 0},
        },
        warnings=[],
        errors=[],
        next_step_ready=True,
    )
```

- [ ] **Step 5: 补导出与验收文档**

Run:

```bash
cd packages/api && uv run pytest tests/unit/pipeline/test_processor_runtime.py tests/unit/pipeline/test_service.py tests/contract/test_import_record_contract.py -q
```

Expected:

- API 侧可以为药典文件命中专属处理器
- `map_to_knowledge_model` 预览能返回 `药材 / 饮片 / 证据` 等节点
- `GraphImportRecord` 兼容新的 `evidence_refs`

- [ ] **Step 6: 运行最小仓库级验证**

Run:

```bash
cd packages/knowledge_model && uv run pytest tests/test_constants.py tests/test_schema.py -q
cd packages/data_ingestion && uv run pytest tests -q
cd packages/api && uv run pytest tests/unit/pipeline/test_processor_runtime.py tests/unit/pipeline/test_service.py tests/contract/test_import_record_contract.py -q
```

Expected:

- 共享模型测试通过
- data_ingestion 协议与药典处理器测试通过
- API pipeline 与导出契约测试通过

- [ ] **Step 7: Commit**

```bash
git add packages/api/app/pipeline/structured_extraction.py packages/api/app/pipeline/processor_runtime.py packages/api/app/api/pipeline_dependencies.py packages/api/app/pipeline/service.py packages/api/app/pipeline/steps/source_preview.py packages/api/app/pipeline/steps/normalize.py packages/api/app/pipeline/steps/extract.py packages/api/app/pipeline/steps/map_to_knowledge_model.py packages/api/app/export/service.py packages/api/tests/unit/pipeline/test_service.py packages/api/tests/unit/pipeline/test_processor_runtime.py packages/api/tests/contract/test_import_record_contract.py docs/acceptance/data-ingestion-and-knowledge-model.md
git commit -m "feat(api): integrate pharmacopoeia graph ingestion pipeline"
```
