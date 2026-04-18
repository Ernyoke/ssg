import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup

from ssg.config.config import Config, Frame as ConfigFrame, Matcher, Meta, MetaFields
from ssg.engine.engine import Engine, create_directory_tree, get_last_edited_for_markdown_files

MINIMAL_FRAME_HTML = """\
<!DOCTYPE html>
<html>
<head>
    <title>Test Site</title>
</head>
<body>
    <article id="main-content"></article>
</body>
</html>
"""

SAMPLE_MARKDOWN = """\
# Hello World

This is a test article.

## Section One

Some content here.
"""

class TestEngineBase(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.workspace_dir = Path(self.temp_dir.name)
        self.source_dir = self.workspace_dir / "source"
        self.destination_dir = self.workspace_dir / "destination"
        self.source_dir.mkdir()
        self.destination_dir.mkdir()

        self.frame_file = Path("frame.html")
        self.md_file = Path("test.md")
        self._write_source_file(self.frame_file, MINIMAL_FRAME_HTML)
        self._write_source_file(self.md_file, SAMPLE_MARKDOWN)

    def _write_source_file(self, relative_path: Path | str, content: str) -> Path:
        relative_path = Path(relative_path)
        path = self.source_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def _make_config(self, extra_matchers=None, exclude=None) -> Config:
        default_meta = MetaFields(
            title="Test Site",
            image="images/cover.png",
            description="Test description.",
            url="https://example.com",
            twitter_handle="@test",
        )
        matchers = [Matcher(file="*.md", action="TAKE_FROM_CONTENT", meta_fields=None)]
        if extra_matchers:
            matchers = extra_matchers + matchers
        meta = Meta(default=default_meta, matchers=matchers)
        frame = ConfigFrame(file="*.md", frame=self.frame_file)
        return Config(
            source=self.source_dir,
            destination=self.destination_dir,
            base_href="https://example.com/",
            hostname="example.com",
            exclude=exclude or [],
            meta=meta,
            frames=[frame],
        )

    @staticmethod
    def _run_engine(config: Config, git_timestamps=None):
        """Run SSG with the git client mocked out."""
        with patch("ssg.engine.engine.git.GitClient") as mock_class:
            mock_instance = MagicMock()
            mock_instance.get_last_edit_time_for_files.return_value = git_timestamps or {}
            mock_class.return_value = mock_instance
            Engine().run(config)

    def _read_output(self, relative_path: Path | str) -> str:
        return (self.destination_dir / relative_path).read_text(encoding="utf-8")


class TestEngineRun(TestEngineBase):
    def test_markdown_is_converted_to_html(self):
        """A Markdown file in the source directory must be rendered as an HTML file."""
        self._run_engine(self._make_config())

        output_file = self.destination_dir / "test.html"
        self.assertTrue(output_file.exists(), f"Expected output file {output_file} to exist")
        content = output_file.read_text(encoding="utf-8")
        self.assertIn("Hello World", content)
        self.assertIn("Section One", content)
        self.assertIn("Some content here", content)

    def test_output_html_contains_og_meta_tags(self):
        """Rendered HTML must contain Open Graph meta tags from the config."""
        self._run_engine(self._make_config())

        content = self._read_output("test.html")
        self.assertIn("og:title", content)
        self.assertIn("og:description", content)
        self.assertIn("og:url", content)
        self.assertIn("og:image", content)

    def test_output_html_title_derived_from_markdown_heading(self):
        """With TAKE_FROM_CONTENT matcher the <title> tag must be set from the first heading."""
        self._run_engine(self._make_config())

        soup = BeautifulSoup(self._read_output("test.html"), "lxml")
        title_tag = soup.find("title")
        self.assertIsNotNone(title_tag)
        self.assertIn("Hello World", title_tag.text)

    def test_static_meta_matcher_overrides_title(self):
        """With a STATIC matcher the og:title must be taken from the matcher's meta_fields."""
        static_meta = MetaFields(
            title="Overridden Title",
            image=None,
            description=None,
            url=None,
            twitter_handle=None,
        )
        static_matcher = Matcher(file="test.md", action="STATIC", meta_fields=static_meta)
        self._run_engine(self._make_config(extra_matchers=[static_matcher]))

        self.assertIn("Overridden Title", self._read_output("test.html"))

    def test_markdown_links_converted_to_html_links(self):
        """Hyperlinks pointing to .md files must be rewritten to .html in the output."""
        self._write_source_file("linked.md", "# Linked Page\n\n[Go to test](test.md)")
        self._run_engine(self._make_config())

        content = self._read_output("linked.html")
        self.assertIn("test.html", content)
        self.assertNotIn("test.md", content)

    def test_non_markdown_file_is_copied(self):
        """Non-Markdown files (e.g. CSS, images) must be copied verbatim to the destination."""
        css_content = "body { margin: 0; }"
        self._write_source_file("style.css", css_content)
        self._run_engine(self._make_config())

        copied = self.destination_dir / "style.css"
        self.assertTrue(copied.exists())
        self.assertEqual(copied.read_text(encoding="utf-8"), css_content)

    def test_frame_file_is_not_copied_to_destination(self):
        """Frame HTML files must be excluded from the destination directory."""
        self._run_engine(self._make_config())
        self.assertFalse((self.destination_dir / "frame.html").exists())

    def test_excluded_file_is_not_copied(self):
        """Files listed in config.exclude must not appear in the destination."""
        self._write_source_file("README.md", "# README")
        self._run_engine(self._make_config(exclude=["README.md"]))

        self.assertFalse((self.destination_dir / "README.md").exists())
        self.assertFalse((self.destination_dir / "README.html").exists())

    def test_excluded_directory_is_skipped(self):
        """Directories listed in config.exclude must be skipped entirely."""
        self._write_source_file("ignored/secret.md", "# Secret")
        self._run_engine(self._make_config(exclude=["ignored"]))

        self.assertFalse((self.destination_dir / "ignored").exists())

    def test_subdirectory_structure_is_mirrored_in_destination(self):
        """The output destination must mirror the subdirectory structure of the source."""
        self._write_source_file("articles/article.md", "# My Article\n\nContent here.")
        self._run_engine(self._make_config())

        self.assertTrue((self.destination_dir / "articles").is_dir())
        self.assertTrue((self.destination_dir / "articles" / "article.html").exists())

    def test_multiple_markdown_files_all_rendered(self):
        """All Markdown files in the source directory must be rendered to the destination."""
        self._write_source_file("page_a.md", "# Page A\n\nContent A.")
        self._write_source_file("page_b.md", "# Page B\n\nContent B.")
        self._run_engine(self._make_config())

        self.assertTrue((self.destination_dir / "test.html").exists())
        self.assertTrue((self.destination_dir / "page_a.html").exists())
        self.assertTrue((self.destination_dir / "page_b.html").exists())

    def test_last_edited_meta_tag_present_when_git_returns_timestamp(self):
        """When the git client returns a timestamp, a 'last-updated' meta tag must appear in the output."""
        timestamp = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
        self._run_engine(
            self._make_config(),
            git_timestamps={self.source_dir / self.md_file: timestamp},
        )

        content = self._read_output("test.html")
        self.assertIn("last-updated", content)
        self.assertIn("2025-06-15", content)

    def test_last_edited_meta_tag_absent_when_git_returns_no_timestamp(self):
        """When the git client returns no timestamp, no 'last-updated' meta tag should appear."""
        self._run_engine(self._make_config())

        self.assertNotIn("last-updated", self._read_output("test.html"))


class TestGetLastEditedForMarkdownFiles(TestEngineBase):
    def test_get_last_edited_only_passes_markdown_files_to_git(self):
        """Only .md file paths are forwarded to the git client; other files are ignored."""
        self._write_source_file("page.md", "# Page")
        self._write_source_file("style.css", "body {}")

        root = create_directory_tree(self.source_dir)

        with patch("ssg.engine.engine.git.GitClient") as mock_class:
            mock_instance = MagicMock()
            mock_instance.get_last_edit_time_for_files.return_value = {}
            mock_class.return_value = mock_instance

            get_last_edited_for_markdown_files(root, self.source_dir)

            passed_paths = mock_instance.get_last_edit_time_for_files.call_args[0][0]
            self.assertTrue(all(p.suffix == ".md" for p in passed_paths))
            self.assertTrue(any(p.name == "page.md" for p in passed_paths))
            self.assertFalse(any(p.name == "style.css" for p in passed_paths))

    def test_get_last_edited_returns_git_client_result(self):
        """The return value is exactly what the git client returns."""
        md_file = self._write_source_file("page.md", "# Page")
        timestamp = datetime(2024, 3, 10, 9, 0, 0, tzinfo=UTC)

        root = create_directory_tree(self.source_dir)

        with patch("ssg.engine.engine.git.GitClient") as mock_class:
            mock_instance = MagicMock()
            mock_instance.get_last_edit_time_for_files.return_value = {md_file: timestamp}
            mock_class.return_value = mock_instance

            result = get_last_edited_for_markdown_files(root, self.source_dir)

            self.assertEqual(result, {md_file: timestamp})

    def test_get_last_edited_traverses_subdirectories(self):
        """Markdown files nested in subdirectories are included in the paths sent to git."""
        self._write_source_file("articles/article.md", "# Article")
        self._write_source_file("index.md", "# Index")

        root = create_directory_tree(self.source_dir)

        with patch("ssg.engine.engine.git.GitClient") as mock_class:
            mock_instance = MagicMock()
            mock_instance.get_last_edit_time_for_files.return_value = {}
            mock_class.return_value = mock_instance

            get_last_edited_for_markdown_files(root, self.source_dir)

            passed_paths = mock_instance.get_last_edit_time_for_files.call_args[0][0]
            self.assertTrue(any(p.name == "index.md" for p in passed_paths))
            self.assertTrue(any(p.name == "article.md" for p in passed_paths))
