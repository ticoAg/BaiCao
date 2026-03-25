from .base import SourceDescriptor, describe_local_text_file


class JSONLSourceAdapter:
    source_type = "jsonl"

    def describe(self, source_locator: str) -> SourceDescriptor:
        return describe_local_text_file(
            self.source_type,
            source_locator,
            format_name="jsonl",
        )
