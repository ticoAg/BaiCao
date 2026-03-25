from .base import SourceDescriptor


class ManualSourceAdapter:
    source_type = "manual"

    def describe(self, source_locator: str) -> SourceDescriptor:
        raw_text = source_locator.strip()
        return SourceDescriptor(
            adapter=self.source_type,
            source_type=self.source_type,
            locator=source_locator,
            source_summary={
                "kind": "text",
                "character_count": len(raw_text),
                "excerpt": raw_text[:80],
                "is_valid": bool(raw_text),
            },
            raw_text=raw_text,
            errors=[] if raw_text else ["手工输入内容不能为空"],
        )
