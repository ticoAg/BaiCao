import json
from pathlib import Path

from knowledge_model.constants import EdgeType, NodeType

from data_ingestion.pending_extract import (
    extract_ancient_sources,
    extract_chatmed_mentions,
    extract_daiy_terms,
    extract_sft_knowledge,
    extract_sylvanl_entries,
    list_decodable_numbered_books,
)
from data_ingestion.organize_workflow import finalize_drafts


def _records(drafts):
    records, _quarantined, _report = finalize_drafts(
        drafts,
        source_id="test",
        batch_id="b",
        import_scope_key="s",
        processor="pending_extract",
    )
    return records


def test_sft_knowledge_extracts_formula_and_herb(tmp_path: Path):
    path = tmp_path / "knowledge.json"
    path.write_text(
        """[
      {"instruction":"方剂-介绍","input":"请对桂枝汤成药说明？","output":"【类别】解表剂\\n【处方】桂枝、白芍"},
      {"instruction":"介绍","input":"中药陈皮介绍？","output":"【性味归经】辛、苦，温"},
      {"instruction":"方剂-基因","input":"请对桂枝汤说明？","output":"忽略"}
    ]""",
        encoding="utf-8",
    )
    drafts, extra = extract_sft_knowledge(path)
    records = _records(drafts)
    names = {item.node_name: item.node_type for item in records}
    assert names["桂枝汤"] == NodeType.FORMULA.value
    assert names["陈皮"] == NodeType.HERB.value
    assert extra["unique_entries"] == 2
    assert extra["mention_entries"] == 0
    assert all(item.source_id == "test" and item.batch_id == "b" for item in records)


def test_sft_knowledge_merges_intro_and_prescription(tmp_path: Path):
    path = tmp_path / "knowledge.json"
    path.write_text(
        json.dumps(
            [
                {
                    "instruction": "方剂-介绍",
                    "input": "请对桂枝汤成药说明？",
                    "output": "桂枝汤是一种方剂。\n【类别】解表剂\n【处方】桂枝、白芍",
                },
                {
                    "instruction": "方剂-处方",
                    "input": "请给出桂枝汤的方子？",
                    "output": "桂枝汤是一种方剂。其处方由桂枝、白芍、甘草组成。",
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    drafts, extra = extract_sft_knowledge(path)
    records = _records(drafts)
    assert extra["unique_entries"] == 1
    assert len(records) == 1
    record = records[0]
    assert record.node_name == "桂枝汤"
    assert record.node_type == NodeType.FORMULA.value
    assert record.properties["tcm_type"] == "来源SFT知识"
    targets = {(edge.type, edge.target) for edge in record.edges}
    assert (EdgeType.CONTAINS_HERB.value, "桂枝") in targets
    assert (EdgeType.CONTAINS_HERB.value, "白芍") in targets
    assert (EdgeType.CONTAINS_HERB.value, "甘草") in targets
    assert all(item.node_type == NodeType.FORMULA.value for item in records)


def test_sft_knowledge_skips_formula_gene(tmp_path: Path):
    path = tmp_path / "knowledge.json"
    path.write_text(
        json.dumps(
            [
                {
                    "instruction": "方剂-基因",
                    "input": "方剂桂枝汤治疗哪些靶点",
                    "output": "桂枝汤是一种方剂。其靶点基因有ALPL。\n【处方】桂枝、白芍",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    drafts, extra = extract_sft_knowledge(path)
    assert drafts == []
    assert extra["unique_entries"] == 0
    assert _records(drafts) == []


def test_sft_knowledge_skips_injection_name(tmp_path: Path):
    path = tmp_path / "knowledge.json"
    path.write_text(
        json.dumps(
            [
                {
                    "instruction": "方剂-介绍",
                    "input": "请对丹参注射液成药说明？",
                    "output": "丹参注射液是一种方剂。\n【处方】丹参",
                },
                {
                    "instruction": "方剂-介绍",
                    "input": "请对注射用血塞通成药说明？",
                    "output": "注射用血塞通是一种方剂。\n【处方】三七",
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    drafts, extra = extract_sft_knowledge(path)
    assert drafts == []
    assert extra["unique_entries"] == 0


def test_sft_knowledge_drops_ellipsis_prescription_token(tmp_path: Path):
    path = tmp_path / "knowledge.json"
    path.write_text(
        json.dumps(
            [
                {
                    "instruction": "方剂-介绍",
                    "input": "请对七厘散成药说明？",
                    "output": "七厘散是一种方剂。\n【处方】丁香等11种中药组成",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    records = _records(extract_sft_knowledge(path)[0])
    assert [item.node_name for item in records] == ["七厘散"]
    assert records[0].edges == []
    assert not any("等" in edge.target for edge in records[0].edges)


def test_sft_knowledge_lexicon_syndrome_creates_mention(tmp_path: Path):
    path = tmp_path / "knowledge.json"
    path.write_text(
        json.dumps(
            [
                {
                    "instruction": "方剂-介绍",
                    "input": "请对桂枝汤成药说明？",
                    "output": "桂枝汤是一种方剂。\n【证候】风寒表证、不是词表证",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    drafts, extra = extract_sft_knowledge(
        path, lexicon={"风寒表证": NodeType.DISEASE.value}
    )
    records = _records(drafts)
    by_name = {item.node_name: item for item in records}
    assert extra["unique_entries"] == 1
    assert extra["mention_entries"] == 1
    assert set(by_name) == {"桂枝汤", "风寒表证"}
    formula = by_name["桂枝汤"]
    mention = by_name["风寒表证"]
    assert formula.node_type == NodeType.FORMULA.value
    assert (EdgeType.RELATED_SYNDROME.value, "风寒表证") in {
        (edge.type, edge.target) for edge in formula.edges
    }
    assert (EdgeType.RELATED_SYNDROME.value, "不是词表证") not in {
        (edge.type, edge.target) for edge in formula.edges
    }
    assert mention.node_type == NodeType.DISEASE.value
    assert mention.properties["tcm_type"] == "来源SFT知识提及"
    assert mention.edges == []


def test_daiy_keeps_named_diseases_only(tmp_path: Path):
    path = tmp_path / "daiy_data.txt"
    path.write_text(
        "外感咳嗽病，中医病名。肺系疾患。\n请携带身份证、医保卡。\n阴虚证，中医病证名。是指阴液不足。\n",
        encoding="utf-8",
    )
    drafts, extra = extract_daiy_terms(path)
    records = _records(drafts)
    assert {item.node_name for item in records} == {"外感咳嗽病", "阴虚证"}
    assert extra["kept_term_lines"] == 2


def test_chatmed_lexicon_mentions_and_brand_gate():
    drafts, extra = extract_chatmed_mentions(
        Path("/dev/null"),
        {},
    )
    assert extra["scanned_lines"] == 0
    assert drafts == []


def test_chatmed_hits_long_names(tmp_path: Path):
    path = tmp_path / "chatmed.txt"
    path.write_text(
        "患者可用桂枝汤治疗太阳病，也可用同仁堂乌鸡白凤丸，但本句足够长以便扫描通过。\n短\n",
        encoding="utf-8",
    )
    drafts, extra = extract_chatmed_mentions(
        path, {"桂枝汤": "方剂", "太阳病": "病证", "同仁堂乌鸡白凤丸": "方剂"}
    )
    records = _records(drafts)
    names = {item.node_name for item in records}
    assert "桂枝汤" in names
    assert "太阳病" in names
    assert "同仁堂乌鸡白凤丸" not in names
    assert extra["scanned_lines"] == 1


def test_ancient_sources_emits_source_nodes_and_skips_bad_files(tmp_path: Path):
    root = tmp_path / "TCM-Ancient-Books"
    root.mkdir()
    (root / "000-伤寒论.txt").write_bytes("伤寒论正文".encode("gb18030"))
    (root / "001-本草纲目.txt").write_text("本草纲目正文\n", encoding="utf-8")
    (root / "203-婴童类萃.txt").write_bytes(b"\xff\xfe\x00\x80bad")
    (root / "700.李培生老中医经验集.txt").write_text("现代医论\n", encoding="utf-8")
    books, listing = list_decodable_numbered_books(root)
    skipped = {item["file"]: item["reason"] for item in listing["skipped"]}
    assert skipped["203-婴童类萃.txt"] == "undecodable"
    assert skipped["700.李培生老中医经验集.txt"] == "unnumbered"
    assert [item["title"] for item in books] == ["伤寒论", "本草纲目"]
    drafts = extract_ancient_sources(books)
    records = _records(drafts)
    assert {item.node_name: item.node_type for item in records} == {
        "伤寒论": NodeType.SOURCE.value,
        "本草纲目": NodeType.SOURCE.value,
    }
    assert all(item.source_id == "test" and item.batch_id == "b" for item in records)
    assert {item.properties["term_code"] for item in records} == {"000", "001"}
    assert all(item.properties["tcm_type"] == "来源古籍书目" for item in records)
    assert all(item.edges == [] for item in records)


def test_sylvanl_prefix_entries(tmp_path: Path):
    path = tmp_path / "k.json"
    path.write_text(
        """[
      {"text":"方剂:二仙汤\\n介绍:温肾阳。"},
      {"text":"药名:注射用亚锡葡庚糖酸钠Ⅰ\\n西药。"},
      {"text":"随便一段没有前缀"}
    ]""",
        encoding="utf-8",
    )
    drafts, extra = extract_sylvanl_entries(path)
    records = _records(drafts)
    assert [item.node_name for item in records] == ["二仙汤"]
    assert extra["kept"] == 1
