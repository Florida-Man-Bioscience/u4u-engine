"""Bounded, workspace-scoped file I/O for the Discovery Informatics lab jail."""
from __future__ import annotations

import mimetypes
import os
import re
import stat
import uuid
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

DEFAULT_MAX_FILE_BYTES = 1024 * 1024 * 1024
DEFAULT_MAX_REQUEST_BYTES = DEFAULT_MAX_FILE_BYTES + 32 * 1024 * 1024
DEFAULT_MAX_UPLOAD_FILES = 32
DEFAULT_MAX_DOWNLOAD_BYTES = DEFAULT_MAX_FILE_BYTES
DEFAULT_MAX_LIST_FILES = 500
DEFAULT_MAX_LIST_DEPTH = 8
_ALLOWED_ROOTS = {"uploads", "outputs"}


class FileIoError(ValueError):
    """A client-safe file I/O error."""

    def __init__(self, code: str, message: str | None = None):
        self.code = code
        super().__init__(message or code)


def _safe_name(name: str) -> str:
    raw = (name or "").replace("\\", "/")
    name = Path(raw).name.strip()
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name)
    name = name.strip(" .")
    if not name or name in {".", ".."}:
        raise FileIoError("invalid_filename")
    return name[:160]


def _display_name(name: str) -> str:
    return re.sub(r"^[0-9a-f]{32}-", "", name)


def record_named_file(
    relative: str,
    size: int,
    *,
    name: str | None = None,
    content_type: str | None = None,
) -> dict[str, Any]:
    filename = Path(relative).name
    guessed = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return {
        "path": relative,
        "name": name or _display_name(filename),
        "size": size,
        "content_type": guessed,
        "download_url": f"/api/lab/files?{urlencode({'path': relative})}",
    }


def record_file(path: Path, workspace: Path, *, name: str | None = None, content_type: str | None = None) -> dict[str, Any]:
    relative = path.relative_to(workspace).as_posix()
    return record_named_file(relative, path.stat().st_size, name=name, content_type=content_type)


_HEADER_LIMIT = 64 * 1024
_STREAM_CHUNK = 64 * 1024
_FILENAME_RE = re.compile(r'filename\*?=(?:(?:UTF-8|utf-8)\'\')?"?([^";\r\n]+)"?', re.IGNORECASE)


class _LimitedReader:
    def __init__(self, source: Any, remaining: int) -> None:
        self._source = source
        self.remaining = remaining

    def read(self, size: int = -1) -> bytes:
        if self.remaining <= 0:
            return b""
        if size < 0 or size > self.remaining:
            size = self.remaining
        data = self._source.read(size)
        if not data:
            return b""
        self.remaining -= len(data)
        return data


def _multipart_boundary(content_type: str) -> bytes:
    if not content_type.lower().startswith("multipart/form-data"):
        raise FileIoError("multipart_required")
    boundary = ""
    for part in content_type.split(";"):
        piece = part.strip()
        if piece.lower().startswith("boundary="):
            boundary = piece.split("=", 1)[1].strip().strip('"')
            break
    if not boundary:
        raise FileIoError("bad_multipart")
    try:
        return boundary.encode("ascii")
    except UnicodeEncodeError as exc:
        raise FileIoError("bad_multipart") from exc


def _part_filename(headers: bytes) -> tuple[str | None, str]:
    text = headers.decode("utf-8", "replace")
    filename = None
    content_type = "application/octet-stream"
    for raw_line in text.splitlines():
        if ":" not in raw_line:
            continue
        name, value = raw_line.split(":", 1)
        key = name.strip().lower()
        value = value.strip()
        if key == "content-disposition":
            match = _FILENAME_RE.search(value)
            if match:
                filename = match.group(1)
        elif key == "content-type":
            content_type = value.split(";", 1)[0].strip() or content_type
    return filename, content_type


def _read_until(reader: _LimitedReader, buf: bytes, marker: bytes, *, limit: int) -> tuple[bytes, bytes]:
    while True:
        index = buf.find(marker)
        if index != -1:
            return buf[:index], buf[index + len(marker) :]
        if len(buf) > limit:
            raise FileIoError("bad_multipart")
        chunk = reader.read(_STREAM_CHUNK)
        if not chunk:
            raise FileIoError("bad_multipart")
        buf += chunk


def _need(reader: _LimitedReader, buf: bytes, n: int) -> bytes:
    while len(buf) < n:
        chunk = reader.read(n - len(buf))
        if not chunk:
            break
        buf += chunk
    return buf


def _skip_boundary_line(reader: _LimitedReader, buf: bytes) -> tuple[bool, bytes]:
    """Return (is_terminator, remainder after CRLF or --)."""
    buf = _need(reader, buf, 2)
    if buf.startswith(b"--"):
        return True, buf[2:]
    if buf.startswith(b"\r\n"):
        return False, buf[2:]
    if buf.startswith(b"\n"):
        return False, buf[1:]
    raise FileIoError("bad_multipart")


def _write_part_body(
    reader: _LimitedReader,
    buf: bytes,
    dest,
    marker: bytes,
    max_file_bytes: int,
) -> tuple[int, bytes]:
    written = 0
    keep = len(marker) - 1
    while True:
        index = buf.find(marker)
        if index != -1:
            payload = buf[:index]
            written += len(payload)
            if written > max_file_bytes:
                raise FileIoError("file_too_large")
            dest.write(payload)
            return written, buf[index + len(marker) :]
        if len(buf) > keep:
            payload = buf[:-keep]
            written += len(payload)
            if written > max_file_bytes:
                raise FileIoError("file_too_large")
            dest.write(payload)
            buf = buf[-keep:]
        chunk = reader.read(_STREAM_CHUNK)
        if not chunk:
            raise FileIoError("bad_multipart")
        buf += chunk


def save_uploads_from_stream(
    source: Any,
    length: int,
    content_type: str,
    workspace: Path,
    *,
    max_request_bytes: int = DEFAULT_MAX_REQUEST_BYTES,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_files: int = DEFAULT_MAX_UPLOAD_FILES,
) -> list[dict[str, Any]]:
    if length < 0 or length > max_request_bytes:
        raise FileIoError("request_too_large")
    boundary = _multipart_boundary(content_type)
    dash = b"--" + boundary
    reader = _LimitedReader(source, length)
    workspace = workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    staging = workspace / f".upload-stage-{uuid.uuid4().hex}"
    staging.mkdir()
    staged: list[tuple[Path, str, str, int]] = []
    try:
        buf = b""
        header, buf = _read_until(reader, buf, dash, limit=_HEADER_LIMIT)
        del header
        done, buf = _skip_boundary_line(reader, buf)
        if done:
            raise FileIoError("file_required")
        while True:
            headers, buf = _read_until(reader, buf, b"\r\n\r\n", limit=_HEADER_LIMIT)
            filename, part_type = _part_filename(headers)
            crlf_marker = b"\r\n" + dash
            if filename:
                if len(staged) >= max_files:
                    raise FileIoError("too_many_files")
                safe_name = _safe_name(filename)
                temp_path = staging / f"{uuid.uuid4().hex}-{safe_name}"
                with temp_path.open("wb") as handle:
                    size, buf = _write_part_body(
                        reader, buf, handle, crlf_marker, max_file_bytes
                    )
                staged.append((temp_path, safe_name, part_type, size))
            else:
                with open(os.devnull, "wb") as handle:
                    _, buf = _write_part_body(reader, buf, handle, crlf_marker, max_file_bytes)
            done, buf = _skip_boundary_line(reader, buf)
            if done:
                break
        if not staged:
            raise FileIoError("file_required")
        return _commit_staged_uploads(workspace, staged)
    except Exception:
        try:
            while reader.read(_STREAM_CHUNK):
                pass
        except Exception:
            pass
        for path, *_rest in staged:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        raise
    finally:
        try:
            for leftover in staging.iterdir():
                leftover.unlink()
            staging.rmdir()
        except OSError:
            pass


def _commit_staged_uploads(
    workspace: Path, staged: list[tuple[Path, str, str, int]]
) -> list[dict[str, Any]]:
    upload_dir = workspace / "uploads"
    if upload_dir.exists() and (upload_dir.is_symlink() or not upload_dir.is_dir()):
        raise FileIoError("invalid_workspace")
    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
        upload_fd = os.open(
            upload_dir,
            os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as exc:
        raise FileIoError("invalid_workspace") from exc
    records: list[dict[str, Any]] = []
    created_names: list[str] = []
    try:
        for temp_path, safe_name, part_content_type, size in staged:
            storage_name = f"{uuid.uuid4().hex}-{safe_name}"
            temporary_name = f".upload-{uuid.uuid4().hex}"
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(temporary_name, flags, 0o600, dir_fd=upload_fd)
            try:
                with os.fdopen(fd, "wb") as handle, temp_path.open("rb") as src:
                    while chunk := src.read(_STREAM_CHUNK):
                        handle.write(chunk)
                os.replace(
                    temporary_name,
                    storage_name,
                    src_dir_fd=upload_fd,
                    dst_dir_fd=upload_fd,
                )
            except Exception:
                try:
                    os.unlink(temporary_name, dir_fd=upload_fd)
                except FileNotFoundError:
                    pass
                raise
            created_names.append(storage_name)
            records.append(
                record_named_file(
                    f"uploads/{storage_name}",
                    size,
                    name=safe_name,
                    content_type=part_content_type,
                )
            )
    except OSError as exc:
        for name in created_names:
            try:
                os.unlink(name, dir_fd=upload_fd)
            except FileNotFoundError:
                pass
        raise FileIoError("storage_error") from exc
    finally:
        os.close(upload_fd)
    return records


def save_uploads(
    body: bytes,
    content_type: str,
    workspace: Path,
    *,
    max_request_bytes: int = DEFAULT_MAX_REQUEST_BYTES,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_files: int = DEFAULT_MAX_UPLOAD_FILES,
) -> list[dict[str, Any]]:
    if len(body) > max_request_bytes:
        raise FileIoError("request_too_large")
    if not content_type.lower().startswith("multipart/form-data"):
        raise FileIoError("multipart_required")
    envelope = (
        f"Content-Type: {content_type}\r\n"
        "MIME-Version: 1.0\r\n\r\n"
    ).encode() + body
    try:
        parsed = BytesParser(policy=policy.default).parsebytes(envelope)
    except Exception as exc:  # pragma: no cover - parser-specific defensive guard
        raise FileIoError("bad_multipart") from exc
    if not parsed.is_multipart():
        raise FileIoError("bad_multipart")

    pending: list[tuple[str, bytes, str]] = []
    for part in parsed.iter_parts():
        filename = part.get_filename()
        if not filename:
            continue
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes):
            payload = b""
        if len(payload) > max_file_bytes:
            raise FileIoError("file_too_large")
        pending.append((_safe_name(filename), payload, part.get_content_type()))
        if len(pending) > max_files:
            raise FileIoError("too_many_files")
    if not pending:
        raise FileIoError("file_required")

    workspace = workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    upload_dir = workspace / "uploads"
    if upload_dir.exists() and (upload_dir.is_symlink() or not upload_dir.is_dir()):
        raise FileIoError("invalid_workspace")
    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
        upload_fd = os.open(
            upload_dir,
            os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as exc:
        raise FileIoError("invalid_workspace") from exc

    records: list[dict[str, Any]] = []
    created_names: list[str] = []
    try:
        for safe_name, payload, part_content_type in pending:
            storage_name = f"{uuid.uuid4().hex}-{safe_name}"
            temporary_name = f".upload-{uuid.uuid4().hex}"
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(temporary_name, flags, 0o600, dir_fd=upload_fd)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(payload)
                os.replace(
                    temporary_name,
                    storage_name,
                    src_dir_fd=upload_fd,
                    dst_dir_fd=upload_fd,
                )
            except Exception:
                try:
                    os.unlink(temporary_name, dir_fd=upload_fd)
                except FileNotFoundError:
                    pass
                raise
            created_names.append(storage_name)
            records.append(
                record_named_file(
                    f"uploads/{storage_name}",
                    len(payload),
                    name=safe_name,
                    content_type=part_content_type,
                )
            )
    except OSError as exc:
        for name in created_names:
            try:
                os.unlink(name, dir_fd=upload_fd)
            except FileNotFoundError:
                pass
        raise FileIoError("storage_error") from exc
    finally:
        os.close(upload_fd)
    return records


def _validate_relative_path(relative_path: str) -> Path:
    raw = str(relative_path or "")
    if "\x00" in raw or "\\" in raw:
        raise FileIoError("invalid_file_path")
    relative = Path(raw)
    if relative.is_absolute() or not relative.parts or relative.parts[0] not in _ALLOWED_ROOTS:
        raise FileIoError("invalid_file_path")
    if ".." in relative.parts or any(part.startswith(".") for part in relative.parts):
        raise FileIoError("invalid_file_path")
    return relative


def open_workspace_file(workspace: Path, relative_path: str) -> tuple[int, dict[str, Any]]:
    """Open a regular workspace file without following symlinked path components."""
    relative = _validate_relative_path(relative_path)
    root = workspace.resolve()
    try:
        current_fd = os.open(
            root,
            os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as exc:
        raise FileIoError("file_not_found") from exc
    try:
        for index, part in enumerate(relative.parts):
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            if index < len(relative.parts) - 1:
                flags |= os.O_DIRECTORY
            next_fd = os.open(part, flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        metadata = os.fstat(current_fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > DEFAULT_MAX_DOWNLOAD_BYTES:
            raise FileIoError("file_not_found" if not stat.S_ISREG(metadata.st_mode) else "file_too_large")
        record = record_named_file(relative.as_posix(), metadata.st_size)
        return current_fd, record
    except FileIoError:
        os.close(current_fd)
        raise
    except OSError as exc:
        os.close(current_fd)
        raise FileIoError("file_not_found") from exc


def resolve_workspace_file(workspace: Path, relative_path: str) -> Path:
    relative = _validate_relative_path(relative_path)
    root = workspace.resolve()
    unresolved = root / relative
    if unresolved.is_symlink() or any(parent.is_symlink() for parent in unresolved.parents):
        raise FileIoError("invalid_file_path")
    candidate = unresolved.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise FileIoError("invalid_file_path") from exc
    if not candidate.is_file():
        raise FileIoError("file_not_found")
    return candidate


def list_workspace_files(
    workspace: Path,
    *,
    max_files: int = DEFAULT_MAX_LIST_FILES,
    max_depth: int = DEFAULT_MAX_LIST_DEPTH,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    workspace_root = workspace.resolve()
    for root_name in sorted(_ALLOWED_ROOTS):
        root = workspace_root / root_name
        if root.is_symlink() or not root.is_dir():
            continue
        pending: list[tuple[Path, str, int]] = [(root, root_name, 0)]
        while pending:
            directory, relative_dir, depth = pending.pop()
            try:
                entries = os.scandir(directory)
            except OSError as exc:
                raise FileIoError("listing_failed") from exc
            with entries:
                for entry in entries:
                    if entry.name.startswith(".") or entry.is_symlink():
                        continue
                    relative = f"{relative_dir}/{entry.name}"
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if depth >= max_depth:
                                raise FileIoError("listing_too_deep")
                            pending.append((Path(entry.path), relative, depth + 1))
                        elif entry.is_file(follow_symlinks=False):
                            metadata = entry.stat(follow_symlinks=False)
                            records.append(record_named_file(relative, metadata.st_size))
                            if len(records) > max_files:
                                raise FileIoError("listing_too_large")
                    except FileIoError:
                        raise
                    except OSError:
                        continue
    return sorted(records, key=lambda item: item["path"])
