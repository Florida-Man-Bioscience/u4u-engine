import io
import tempfile
import unittest
from email.generator import BytesGenerator
from email.message import EmailMessage
from pathlib import Path

import file_io


def multipart_body(files: list[tuple[str, bytes, str]]) -> tuple[bytes, str]:
    message = EmailMessage()
    message.set_type("multipart/form-data")
    for filename, payload, content_type in files:
        maintype, subtype = content_type.split("/", 1)
        message.add_attachment(
            payload,
            maintype=maintype,
            subtype=subtype,
            filename=filename,
        )
    message.set_type("multipart/form-data")
    with tempfile.NamedTemporaryFile() as out:
        BytesGenerator(out).flatten(message, unixfrom=False)
        out.seek(0)
        body = out.read()
    return body, message["Content-Type"]


def browser_multipart(files: list[tuple[str, bytes, str]]) -> tuple[bytes, str]:
    boundary = "----HermesFormBoundary7MA4YWxkTrZu0gW"
    chunks: list[bytes] = []
    for filename, payload, content_type in files:
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n"
                "\r\n"
            ).encode()
            + payload
            + b"\r\n"
        )
    body = b"".join(chunks) + f"--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


class FileIoTests(unittest.TestCase):
    def test_upload_sanitizes_name_and_writes_inside_uploads(self):
        with tempfile.TemporaryDirectory() as tmp:
            body, content_type = multipart_body(
                [("../../paper notes.pdf", b"PDF", "application/pdf")]
            )
            files = file_io.save_uploads(body, content_type, Path(tmp), max_request_bytes=1000)
            self.assertEqual(len(files), 1)
            record = files[0]
            self.assertEqual(record["name"], "paper notes.pdf")
            self.assertTrue((Path(tmp) / record["path"]).is_file())
            self.assertTrue(record["path"].startswith("uploads/"))

    def test_upload_rejects_oversized_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            body, content_type = multipart_body([("x.txt", b"12345", "text/plain")])
            with self.assertRaises(file_io.FileIoError) as ctx:
                file_io.save_uploads(body, content_type, Path(tmp), max_request_bytes=4)
            self.assertEqual(ctx.exception.code, "request_too_large")

    def test_resolve_rejects_traversal_and_outside_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "outputs").mkdir()
            (root / "outputs" / "answer.txt").write_text("answer")
            self.assertEqual(
                file_io.resolve_workspace_file(root, "outputs/answer.txt").read_text(),
                "answer",
            )
            with self.assertRaises(file_io.FileIoError):
                file_io.resolve_workspace_file(root, "../secret.txt")

    def test_list_includes_uploads_and_outputs_without_hidden_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "uploads").mkdir()
            (root / "outputs").mkdir()
            (root / "uploads" / "input.txt").write_text("input")
            (root / "outputs" / "answer.md").write_text("answer")
            (root / "outputs" / ".hidden").write_text("hidden")
            records = file_io.list_workspace_files(root)
            self.assertEqual([r["path"] for r in records], ["outputs/answer.md", "uploads/input.txt"])

    def test_list_and_resolve_ignore_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "outputs").mkdir()
            outside = root / "outside.txt"
            outside.write_text("secret")
            link = root / "outputs" / "link.txt"
            link.symlink_to(outside)
            self.assertEqual(file_io.list_workspace_files(root), [])
            with self.assertRaises(file_io.FileIoError):
                file_io.resolve_workspace_file(root, "outputs/link.txt")

    def test_upload_rejects_too_many_parts_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            body, content_type = multipart_body(
                [(f"file-{i}.txt", b"", "text/plain") for i in range(33)]
            )
            with self.assertRaises(file_io.FileIoError) as ctx:
                file_io.save_uploads(body, content_type, Path(tmp), max_request_bytes=10000)
            self.assertEqual(ctx.exception.code, "too_many_files")
            self.assertFalse((Path(tmp) / "uploads").exists())

    def test_upload_rejects_symlinked_upload_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside"
            outside.mkdir()
            (root / "uploads").symlink_to(outside, target_is_directory=True)
            body, content_type = multipart_body([("x.txt", b"x", "text/plain")])
            with self.assertRaises(file_io.FileIoError) as ctx:
                file_io.save_uploads(body, content_type, root, max_request_bytes=1000)
            self.assertEqual(ctx.exception.code, "invalid_workspace")
            self.assertEqual(list(outside.iterdir()), [])

    def test_multi_file_upload_is_atomic_when_later_file_is_too_large(self):
        with tempfile.TemporaryDirectory() as tmp:
            body, content_type = multipart_body(
                [("first.txt", b"ok", "text/plain"), ("second.txt", b"too-big", "text/plain")]
            )
            with self.assertRaises(file_io.FileIoError) as ctx:
                file_io.save_uploads(
                    body,
                    content_type,
                    Path(tmp),
                    max_request_bytes=1000,
                    max_file_bytes=3,
                )
            self.assertEqual(ctx.exception.code, "file_too_large")
            self.assertFalse((Path(tmp) / "uploads").exists())

    def test_open_workspace_file_rejects_symlink_without_following_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "outputs").mkdir()
            outside = root / "secret.txt"
            outside.write_text("secret")
            (root / "outputs" / "link.txt").symlink_to(outside)
            with self.assertRaises(file_io.FileIoError):
                file_io.open_workspace_file(root, "outputs/link.txt")

    def test_listing_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "outputs").mkdir()
            (root / "outputs" / "one.txt").write_text("1")
            (root / "outputs" / "two.txt").write_text("2")
            with self.assertRaises(file_io.FileIoError) as ctx:
                file_io.list_workspace_files(root, max_files=1)
            self.assertEqual(ctx.exception.code, "listing_too_large")

    def test_download_url_encodes_relative_path(self):
        record = file_io.record_named_file("outputs/a #1.txt", 1)
        self.assertIn("path=outputs%2Fa+%231.txt", record["download_url"])

    def test_stream_upload_sanitizes_name_and_writes_inside_uploads(self):
        with tempfile.TemporaryDirectory() as tmp:
            body, content_type = browser_multipart(
                [("../../paper notes.pdf", b"PDF", "application/pdf")]
            )
            files = file_io.save_uploads_from_stream(
                io.BytesIO(body), len(body), content_type, Path(tmp), max_request_bytes=1000
            )
            self.assertEqual(len(files), 1)
            record = files[0]
            self.assertEqual(record["name"], "paper notes.pdf")
            stored = Path(tmp) / record["path"]
            self.assertTrue(stored.is_file())
            self.assertEqual(stored.read_bytes(), b"PDF")
            self.assertTrue(record["path"].startswith("uploads/"))

    def test_stream_upload_rejects_oversized_request_before_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            body, content_type = browser_multipart([("x.txt", b"12345", "text/plain")])
            with self.assertRaises(file_io.FileIoError) as ctx:
                file_io.save_uploads_from_stream(
                    io.BytesIO(body), len(body), content_type, Path(tmp), max_request_bytes=4
                )
            self.assertEqual(ctx.exception.code, "request_too_large")
            self.assertFalse((Path(tmp) / "uploads").exists())

    def test_stream_multi_file_upload_is_atomic_when_later_file_is_too_large(self):
        with tempfile.TemporaryDirectory() as tmp:
            body, content_type = browser_multipart(
                [("first.txt", b"ok", "text/plain"), ("second.txt", b"too-big", "text/plain")]
            )
            with self.assertRaises(file_io.FileIoError) as ctx:
                file_io.save_uploads_from_stream(
                    io.BytesIO(body),
                    len(body),
                    content_type,
                    Path(tmp),
                    max_request_bytes=1000,
                    max_file_bytes=3,
                )
            self.assertEqual(ctx.exception.code, "file_too_large")
            self.assertFalse((Path(tmp) / "uploads").exists())

    def test_stream_upload_rejects_too_many_parts_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            body, content_type = browser_multipart(
                [(f"file-{i}.txt", b"", "text/plain") for i in range(33)]
            )
            with self.assertRaises(file_io.FileIoError) as ctx:
                file_io.save_uploads_from_stream(
                    io.BytesIO(body), len(body), content_type, Path(tmp), max_request_bytes=20000
                )
            self.assertEqual(ctx.exception.code, "too_many_files")
            self.assertFalse((Path(tmp) / "uploads").exists())

    def test_stream_upload_rejects_symlinked_upload_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside"
            outside.mkdir()
            (root / "uploads").symlink_to(outside, target_is_directory=True)
            body, content_type = browser_multipart([("x.txt", b"x", "text/plain")])
            with self.assertRaises(file_io.FileIoError) as ctx:
                file_io.save_uploads_from_stream(
                    io.BytesIO(body), len(body), content_type, root, max_request_bytes=1000
                )
            self.assertEqual(ctx.exception.code, "invalid_workspace")
            self.assertEqual(list(outside.iterdir()), [])

    def test_stream_upload_accepts_closing_boundary_split_across_64kib_chunk(self):
        class Chunked(io.RawIOBase):
            def __init__(self, data: bytes, size: int) -> None:
                self._buf = io.BytesIO(data)
                self._size = size

            def read(self, size: int = -1) -> bytes:  # noqa: A003
                n = self._size if size is None or size < 0 else min(size, self._size)
                return self._buf.read(n)

        payload = b"P" * 65348
        body, content_type = browser_multipart([("split.bin", payload, "application/octet-stream")])
        with tempfile.TemporaryDirectory() as tmp:
            files = file_io.save_uploads_from_stream(
                Chunked(body, 64 * 1024),
                len(body),
                content_type,
                Path(tmp),
                max_request_bytes=len(body) + 16,
            )
            stored = Path(tmp) / files[0]["path"]
            self.assertEqual(stored.read_bytes(), payload)

    def test_stream_upload_accepts_one_byte_reads(self):
        class OneByte(io.RawIOBase):
            def __init__(self, data: bytes) -> None:
                self._buf = io.BytesIO(data)

            def read(self, size: int = -1) -> bytes:  # noqa: A003
                if size == 0:
                    return b""
                return self._buf.read(1)

        body, content_type = browser_multipart([("tiny.txt", b"hello", "text/plain")])
        with tempfile.TemporaryDirectory() as tmp:
            files = file_io.save_uploads_from_stream(
                OneByte(body), len(body), content_type, Path(tmp), max_request_bytes=1000
            )
            stored = Path(tmp) / files[0]["path"]
            self.assertEqual(stored.read_bytes(), b"hello")


if __name__ == "__main__":
    unittest.main()
