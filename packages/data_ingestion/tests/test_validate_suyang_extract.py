from data_ingestion.cli.validate_suyang_extract import validate
from data_ingestion.dataset_records import DatasetEdge, DatasetRecord

BATCH = "2026-08-16-suyang-v3-b01"


def rec(**overrides: object) -> DatasetRecord:
    data = {
        "source_id": "daoyi-suyang",
        "batch_id": BATCH,
        "unit_id": "chapter-002",
        "unit_title": "第2章 第一个患者",
        "processor": "test",
        "extracted_at": "2026-08-16T18:00:00+00:00",
        "node_type": "来源",
        "node_name": "道医苏子阳",
        "source": "daoyi-suyang",
        "status": "pending",
        "evidence_refs": [],
        "evidence_text": "",
        "properties": {
            "import_source_id": "daoyi-suyang",
            "import_batch_id": BATCH,
            "import_unit_id": "chapter-002",
        },
        "edges": [],
    }
    data.update(overrides)
    record = DatasetRecord.model_validate(data)
    record.validate_types()
    return record


def knowledge_edges(target_evidence: str = "证据:daoyi-suyang:chapter-002") -> list[DatasetEdge]:
    return [
        DatasetEdge(type="来源于", target="道医苏子阳"),
        DatasetEdge(type="由证据支持", target=target_evidence),
    ]


def valid_case_records() -> list[DatasetRecord]:
    return [
        rec(),
        rec(
            node_type="证据",
            node_name="证据:daoyi-suyang:chapter-002",
            evidence_text="风寒袭肺，止嗽散",
            edges=[{"type": "来源于", "target": "道医苏子阳"}],
        ),
        rec(
            node_type="病证",
            node_name="风寒咳嗽",
            evidence_refs=["证据:daoyi-suyang:chapter-002"],
            evidence_text="咳嗽咽痒",
            edges=knowledge_edges()
            + [DatasetEdge(type="记载于医案", target="医案:chapter-002")],
        ),
        rec(
            node_type="药材",
            node_name="桔梗",
            evidence_refs=["证据:daoyi-suyang:chapter-002"],
            evidence_text="桔梗4g",
            edges=knowledge_edges(),
        ),
        rec(
            node_type="方剂",
            node_name="止嗽散",
            evidence_refs=["证据:daoyi-suyang:chapter-002"],
            evidence_text="桔梗4g、荆芥4g",
            edges=knowledge_edges()
            + [
                DatasetEdge(type="组成药材", target="桔梗", properties={"dosage": "4g"}),
                DatasetEdge(type="治疗病证", target="风寒咳嗽"),
            ],
        ),
        rec(
            node_type="医案",
            node_name="医案:chapter-002",
            evidence_refs=["证据:daoyi-suyang:chapter-002"],
            evidence_text="风寒袭肺，止嗽散",
            edges=knowledge_edges()
            + [
                DatasetEdge(type="治疗病证", target="风寒咳嗽"),
                DatasetEdge(type="使用方剂", target="止嗽散"),
            ],
        ),
    ]


def test_valid_clinical_chapter_passes():
    failures = validate(valid_case_records(), {"chapter-002"}, BATCH)
    assert failures == []


def test_high_skip_rate_is_allowed():
    records = [
        rec(
            unit_id=f"chapter-{index:03d}",
            properties={
                "import_source_id": "daoyi-suyang",
                "import_batch_id": BATCH,
                "import_unit_id": f"chapter-{index:03d}",
                "skip_reason": "no_clinical_knowledge",
            },
        )
        for index in range(1, 5)
    ]
    failures = validate(records, {f"chapter-{index:03d}" for index in range(1, 5)}, BATCH)
    assert failures == []


def test_skip_chapter_cannot_carry_knowledge():
    records = [
        rec(
            properties={
                "import_source_id": "daoyi-suyang",
                "import_batch_id": BATCH,
                "import_unit_id": "chapter-002",
                "skip_reason": "no_clinical_knowledge",
            }
        ),
        rec(
            node_type="病证",
            node_name="风寒咳嗽",
            evidence_refs=["证据:daoyi-suyang:chapter-002"],
            edges=knowledge_edges(),
        ),
    ]
    failures = validate(records, {"chapter-002"}, BATCH)
    assert any("skip unit has knowledge" in item for item in failures)


def test_disease_cannot_emit_treat_edge():
    records = valid_case_records()
    for item in records:
        if item.node_name == "风寒咳嗽":
            item.edges.append(DatasetEdge(type="治疗病证", target="风寒咳嗽"))
    failures = validate(records, {"chapter-002"}, BATCH)
    assert any("病证 emitted 治疗病证" in item for item in failures)


def test_case_requires_disease_and_intervention():
    records = [
        rec(),
        rec(
            node_type="证据",
            node_name="证据:daoyi-suyang:chapter-002",
            edges=[{"type": "来源于", "target": "道医苏子阳"}],
        ),
        rec(
            node_type="医案",
            node_name="医案:chapter-002",
            evidence_refs=["证据:daoyi-suyang:chapter-002"],
            edges=knowledge_edges(),
        ),
    ]
    failures = validate(records, {"chapter-002"}, BATCH)
    assert any("医案 missing 治疗病证" in item for item in failures)
    assert any("医案 missing intervention" in item for item in failures)


def test_formula_with_dosage_must_have_composition():
    records = valid_case_records()
    for item in records:
        if item.node_name == "止嗽散":
            item.edges = [
                edge for edge in item.edges if edge.type != "组成药材"
            ]
    failures = validate(records, {"chapter-002"}, BATCH)
    assert any("方剂 missing 组成药材" in item for item in failures)


def test_vague_disease_and_forbidden_method_fail():
    records = valid_case_records() + [
        rec(
            node_type="病证",
            node_name="内科杂病",
            evidence_refs=["证据:daoyi-suyang:chapter-002"],
            edges=knowledge_edges()
            + [DatasetEdge(type="记载于医案", target="医案:chapter-002")],
        ),
        rec(
            node_type="治法",
            node_name="铁布衫",
            evidence_refs=["证据:daoyi-suyang:chapter-002"],
            edges=knowledge_edges(),
        ),
    ]
    failures = validate(records, {"chapter-002"}, BATCH)
    assert any("vague 病证" in item for item in failures)
    assert any("forbidden 治法" in item for item in failures)


def test_edge_target_type_must_match():
    records = valid_case_records() + [
        rec(
            node_type="工艺",
            node_name="水飞",
            evidence_refs=["证据:daoyi-suyang:chapter-002"],
            edges=knowledge_edges(),
        )
    ]
    for item in records:
        if item.node_type == "医案":
            item.edges.append(DatasetEdge(type="采用治法", target="水飞"))
    failures = validate(records, {"chapter-002"}, BATCH)
    assert any("采用治法 target not 治法" in item for item in failures)
