import re

from .base import SourceDescriptor


HUGGINGFACE_DATASET_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class HuggingFaceSourceAdapter:
    source_type = "huggingface"

    def describe(self, source_locator: str) -> SourceDescriptor:
        locator = source_locator.strip()
        is_valid = bool(HUGGINGFACE_DATASET_PATTERN.match(locator))
        errors = [] if is_valid else ["HuggingFace locator 必须是 owner/dataset 形式"]
        return SourceDescriptor(
            adapter=self.source_type,
            source_type=self.source_type,
            locator=source_locator,
            source_summary={
                "kind": "remote_locator",
                "provider": "huggingface",
                "dataset": locator,
                "is_valid": is_valid,
            },
            raw_text=locator,
            errors=errors,
        )
