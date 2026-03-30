from __future__ import annotations

import shutil
import tarfile
import hashlib
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


class MaterializedSource(BaseModel):
    run_workdir: str
    source_dir: str
    extracted_dir: str | None = None
    cache_hit: bool = False
    is_archive: bool = False
    archive_format: str | None = None
    readme_path: str | None = None
    readme_content: str | None = None
    candidate_files: list[str] = Field(default_factory=list)
    repo_url: str | None = None
    readme_url: str | None = None

    model_config = ConfigDict(use_enum_values=False)


class SourceMaterializationService:
    def __init__(self, storage_root: str, huggingface_cache_root: str | None = None) -> None:
        repo_root = get_repo_root()
        self.storage_root = self._resolve_root(storage_root, repo_root)
        self.huggingface_cache_root = self._resolve_root(
            huggingface_cache_root or ".cache/huggingface",
            repo_root,
        )

    def _resolve_root(self, value: str, repo_root: Path) -> Path:
        path = Path(value).expanduser()
        if path.is_absolute():
            return path
        return repo_root / path

    async def materialize(
        self,
        run_id: str,
        source_type: str,
        source_input: dict[str, object],
    ) -> MaterializedSource:
        if source_type == "local_upload":
            return self._materialize_local_upload(run_id, source_input)
        if source_type == "remote_url":
            return self._materialize_remote_url(run_id, source_input)
        if source_type == "huggingface_repo":
            return self._materialize_huggingface_repo(run_id, source_input)
        raise ValueError(f"unsupported source_type: {source_type}")

    def build_huggingface_metadata(self, repo_id: str) -> dict[str, str]:
        repo = repo_id.strip()
        return {
            "repo_url": f"https://huggingface.co/datasets/{repo}",
            "readme_url": f"https://huggingface.co/datasets/{repo}/resolve/main/README.md",
        }

    def _materialize_local_upload(
        self,
        run_id: str,
        source_input: dict[str, object],
    ) -> MaterializedSource:
        stored_path = Path(str(source_input.get("stored_path", ""))).expanduser()
        if not stored_path.exists():
            raise ValueError(f"uploaded source file not found: {stored_path}")

        run_workdir = self.storage_root / "runs" / run_id
        source_dir = run_workdir / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        copied_path = source_dir / stored_path.name
        shutil.copy2(stored_path, copied_path)
        return self._build_materialized_result(run_workdir, source_dir, copied_path, cache_hit=False)

    def _materialize_remote_url(
        self,
        run_id: str,
        source_input: dict[str, object],
    ) -> MaterializedSource:
        url = str(source_input.get("url", "")).strip()
        if not url.startswith(("http://", "https://")):
            raise ValueError("remote_url only supports http/https")

        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        cache_dir = self.storage_root / "cache" / "remote" / url_hash
        cache_file = cache_dir / self._remote_filename(url)
        cache_hit = cache_file.exists()
        if not cache_hit:
            self._download_remote_url(url, cache_file)

        run_workdir = self.storage_root / "runs" / run_id
        source_dir = run_workdir / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        copied_path = source_dir / cache_file.name
        shutil.copy2(cache_file, copied_path)
        return self._build_materialized_result(run_workdir, source_dir, copied_path, cache_hit=cache_hit)

    def _materialize_huggingface_repo(
        self,
        run_id: str,
        source_input: dict[str, object],
    ) -> MaterializedSource:
        repo_id = str(source_input.get("repo_id", "")).strip()
        if not repo_id:
            raise ValueError("repo_id is required for huggingface_repo")

        metadata = self.build_huggingface_metadata(repo_id)
        cache_dir = self.huggingface_cache_root / repo_id
        cache_hit = cache_dir.exists() and any(cache_dir.iterdir())
        if not cache_hit:
            self._download_huggingface_repo(repo_id, cache_dir)

        run_workdir = self.storage_root / "runs" / run_id
        source_dir = run_workdir / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        self._copy_repo_contents(cache_dir, source_dir)

        readme_path = self._find_readme(source_dir)
        candidate_files = self._find_candidate_files(source_dir)

        return MaterializedSource(
            run_workdir=str(run_workdir),
            source_dir=str(source_dir),
            cache_hit=cache_hit,
            readme_path=str(readme_path) if readme_path else None,
            readme_content=readme_path.read_text(encoding="utf-8") if readme_path else None,
            candidate_files=[str(path) for path in candidate_files],
            repo_url=metadata["repo_url"],
            readme_url=metadata["readme_url"],
        )

    def _copy_repo_contents(self, cache_dir: Path, source_dir: Path) -> None:
        for item in cache_dir.iterdir():
            if item.name == ".cache":
                continue
            target = source_dir / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target)

    def _build_materialized_result(
        self,
        run_workdir: Path,
        source_dir: Path,
        copied_path: Path,
        *,
        cache_hit: bool,
    ) -> MaterializedSource:
        extracted_dir = run_workdir / "extracted"

        archive_format = self._detect_archive_format(copied_path)
        is_archive = archive_format is not None
        if is_archive:
            extracted_dir.mkdir(parents=True, exist_ok=True)
            assert archive_format is not None
            self._extract_archive(copied_path, extracted_dir, archive_format)

        content_root = extracted_dir if is_archive else source_dir
        readme_path = self._find_readme(content_root)
        candidate_files = self._find_candidate_files(content_root)

        return MaterializedSource(
            run_workdir=str(run_workdir),
            source_dir=str(source_dir),
            cache_hit=cache_hit,
            extracted_dir=str(extracted_dir) if is_archive else None,
            is_archive=is_archive,
            archive_format=archive_format,
            readme_path=str(readme_path) if readme_path else None,
            readme_content=readme_path.read_text(encoding="utf-8") if readme_path else None,
            candidate_files=[str(path) for path in candidate_files],
        )

    def _detect_archive_format(self, path: Path) -> str | None:
        name = path.name.lower()
        if name.endswith(".zip"):
            return "zip"
        if name.endswith(".tar.gz") or name.endswith(".tgz"):
            return "tar.gz"
        return None

    def _remote_filename(self, url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        name = Path(parsed.path).name
        return name or "download.bin"

    def _download_remote_url(self, url: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url) as response:
            destination.write_bytes(response.read())

    def _download_huggingface_repo(self, repo_id: str, cache_dir: Path) -> None:
        from huggingface_hub import snapshot_download

        cache_dir.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            local_dir=str(cache_dir),
        )

    def _extract_archive(self, source: Path, target_dir: Path, archive_format: str) -> None:
        if archive_format == "zip":
            with zipfile.ZipFile(source) as archive:
                for member in archive.infolist():
                    self._assert_safe_member(target_dir, Path(member.filename))
                archive.extractall(target_dir)
            return

        with tarfile.open(source, "r:gz") as archive:
            for member in archive.getmembers():
                self._assert_safe_member(target_dir, Path(member.name))
            archive.extractall(target_dir, filter="data")

    def _assert_safe_member(self, target_dir: Path, member_path: Path) -> None:
        resolved = (target_dir / member_path).resolve()
        root = target_dir.resolve()
        if root not in resolved.parents and resolved != root:
            raise ValueError(f"unsafe archive member path: {member_path}")

    def _find_readme(self, root: Path) -> Path | None:
        direct = root / "README.md"
        if direct.exists():
            return direct
        for path in sorted(root.rglob("README.md")):
            if path.is_file():
                return path
        return None

    def _find_candidate_files(self, root: Path) -> list[Path]:
        priority = {".jsonl": 0, ".csv": 1, ".txt": 2, ".md": 3}
        files = [
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in priority and path.name != "README.md"
        ]
        return sorted(files, key=lambda path: (priority[path.suffix.lower()], str(path)))
