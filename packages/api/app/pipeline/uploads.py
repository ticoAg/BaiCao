from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict

from .materialization import get_repo_root


class UploadedSourceFile(BaseModel):
    upload_token: str
    filename: str
    stored_path: str
    content_type: str | None = None

    model_config = ConfigDict(use_enum_values=False)


class SourceUploadService:
    def __init__(self, storage_root: str) -> None:
        root = Path(storage_root).expanduser()
        if not root.is_absolute():
            root = get_repo_root() / root
        self.upload_root = root / "uploads"

    async def save_upload(self, upload_file: UploadFile) -> UploadedSourceFile:
        suffix = Path(upload_file.filename or "upload.bin").suffix
        upload_token = f"upload-{uuid4().hex}{suffix}"
        target = self.upload_root / upload_token
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(await upload_file.read())
        return UploadedSourceFile(
            upload_token=upload_token,
            filename=upload_file.filename or upload_token,
            stored_path=str(target),
            content_type=upload_file.content_type,
        )
