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


if __name__ == "__main__":
    unittest.main()
