from __future__ import annotations

from pathlib import Path

from data_ingestion.national_standard_terms import clean_directory, write_clean_outputs


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def make_dataset(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    write(
        root / "中医临床诊疗术语疾病.txt",
        """3.1
外感时令类病
泛指时令外邪引起的一类外感病。
3.1.1
感冒
伤风轻症
因时令外邪侵袭肺表所致。
12.4.13.1
痞气
因喂养不当所致的小儿痞病。
18.1.5
痞气
脾积气
因脾虚气郁所致的积聚病。
""",
    )
    write(
        root / "中医临床诊疗术语证候.txt",
        """3.1
阴证
与阳证相对的一类证候。
3.5.1
表寒证
因风寒侵袭肌表所致。
""",
    )
    write(
        root / "中药成方制剂.txt",
        """各论
表实感冒颗粒
BiaoshiGanmaoKeli
【药物组成】麻黄、桂枝。
【功能与主治】发汗解表。
山东阿胶膏
ShandongEjiaoGao
【药物组成】阿胶。
【功能与主治】补血。
同仁堂乌鸡白凤丸
TongrentangWujiBaifengWan
【药物组成】乌鸡。
【功能与主治】补气养血。
""",
    )


def test_clean_qualifies_collision_and_quarantines_brand(tmp_path: Path):
    root = tmp_path / "national_standard"
    make_dataset(root)
    records, report = clean_directory(root)
    names = {record.node_name for record in records}
    assert names >= {"痞气〔12.4.13.1〕", "痞气〔18.1.5〕", "感冒", "表寒证", "表实感冒颗粒"}
    pi_qi = [record for record in records if record.node_name.startswith("痞气")]
    assert {record.properties["term_code"] for record in pi_qi} == {"12.4.13.1", "18.1.5"}
    assert "同仁堂乌鸡白凤丸" in report["brand_quarantine"]
    assert all(record.node_name != "同仁堂乌鸡白凤丸" for record in records)
    assert any(record.node_name == "表实感冒颗粒" for record in records)
    result = write_clean_outputs(records, report, tmp_path / "out")
    assert result["publish"] is False
    dumped = (tmp_path / "out" / "records.jsonl").read_text(encoding="utf-8")
    assert "同仁堂" not in dumped
