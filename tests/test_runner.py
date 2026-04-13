from datetime import datetime, UTC
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from config.config import Config, Meta, MetaFields, Matcher, Frame as ConfigFrame
from runner.runner import SSG

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

pytestmark = pytest.mark.integration


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture()
def source_dir(tmp_path):
    d = tmp_path / "source"
    d.mkdir()
    return d


@pytest.fixture()
def destination_dir(tmp_path):
    d = tmp_path / "destination"
    d.mkdir()
    return d


@pytest.fixture()
def frame_file(source_dir):
    """Write the minimal frame HTML and return its path."""
    p = source_dir / "frame.html"
    p.write_text(MINIMAL_FRAME_HTML, encoding="utf-8")
    return p


@pytest.fixture()
def md_file(source_dir):
    """Write the sample Markdown file and return its path."""
    p = source_dir / "test.md"
    p.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
    return p


def _make_config(source_dir, destination_dir, frame_path, extra_matchers=None, exclude=None):
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
    frame = ConfigFrame(file="*.md", frame=frame_path)
    return Config(
        source=source_dir,
        destination=destination_dir,
        base_href="https://example.com/",
        hostname="example.com",
        exclude=exclude or [],
        meta=meta,
        frames=[frame],
    )


def _run_ssg(config, git_timestamps=None):
    """Run SSG with the git client mocked out."""
    with patch("git.GitClient") as mock_class:
        mock_instance = MagicMock()
        mock_instance.get_last_edit_time_for_files.return_value = git_timestamps or {}
        mock_class.return_value = mock_instance
        SSG(config).run()


# ------------------------------------------------------------------
# Core rendering
# ------------------------------------------------------------------

def test_markdown_is_converted_to_html(source_dir, destination_dir, frame_file, md_file):
    """A Markdown file in the source directory must be rendered as an HTML file."""
    _run_ssg(_make_config(source_dir, destination_dir, frame_file))

    output_file = destination_dir / "test.html"
    assert output_file.exists(), f"Expected output file {output_file} to exist"
    content = output_file.read_text(encoding="utf-8")
    assert "Hello World" in content
    assert "Section One" in content
    assert "Some content here" in content


def test_output_html_contains_og_meta_tags(source_dir, destination_dir, frame_file, md_file):
    """Rendered HTML must contain Open Graph meta tags from the config."""
    _run_ssg(_make_config(source_dir, destination_dir, frame_file))

    content = (destination_dir / "test.html").read_text(encoding="utf-8")
    assert "og:title" in content
    assert "og:description" in content
    assert "og:url" in content
    assert "og:image" in content


def test_output_html_title_derived_from_markdown_heading(source_dir, destination_dir, frame_file, md_file):
    """With TAKE_FROM_CONTENT matcher the <title> tag must be set from the first heading."""
    _run_ssg(_make_config(source_dir, destination_dir, frame_file))

    soup = BeautifulSoup((destination_dir / "test.html").read_text(encoding="utf-8"), "lxml")
    title_tag = soup.find("title")
    assert title_tag is not None
    assert "Hello World" in title_tag.text
    assert "example.com" in title_tag.text


def test_static_meta_matcher_overrides_title(source_dir, destination_dir, frame_file, md_file):
    """With a STATIC matcher the og:title must be taken from the matcher's meta_fields."""
    static_meta = MetaFields(title="Overridden Title", image=None, description=None, url=None, twitter_handle=None)
    static_matcher = Matcher(file="*/test.md", action="STATIC", meta_fields=static_meta)
    _run_ssg(_make_config(source_dir, destination_dir, frame_file, extra_matchers=[static_matcher]))

    assert "Overridden Title" in (destination_dir / "test.html").read_text(encoding="utf-8")


def test_markdown_links_converted_to_html_links(source_dir, destination_dir, frame_file, md_file):
    """Hyperlinks pointing to .md files must be rewritten to .html in the output."""
    (source_dir / "linked.md").write_text("# Linked Page\n\n[Go to test](test.md)", encoding="utf-8")
    _run_ssg(_make_config(source_dir, destination_dir, frame_file))

    content = (destination_dir / "linked.html").read_text(encoding="utf-8")
    assert "test.html" in content
    assert "test.md" not in content


# ------------------------------------------------------------------
# File copying
# ------------------------------------------------------------------

def test_non_markdown_file_is_copied(source_dir, destination_dir, frame_file, md_file):
    """Non-Markdown files (e.g. CSS, images) must be copied verbatim to the destination."""
    css_content = "body { margin: 0; }"
    (source_dir / "style.css").write_text(css_content, encoding="utf-8")
    _run_ssg(_make_config(source_dir, destination_dir, frame_file))

    copied = destination_dir / "style.css"
    assert copied.exists()
    assert copied.read_text(encoding="utf-8") == css_content


def test_frame_file_is_not_copied_to_destination(source_dir, destination_dir, frame_file, md_file):
    """Frame HTML files must be excluded from the destination directory."""
    _run_ssg(_make_config(source_dir, destination_dir, frame_file))
    assert not (destination_dir / "frame.html").exists()


# ------------------------------------------------------------------
# Exclusions
# ------------------------------------------------------------------

def test_excluded_file_is_not_copied(source_dir, destination_dir, frame_file, md_file):
    """Files listed in config.exclude must not appear in the destination."""
    (source_dir / "README.md").write_text("# README", encoding="utf-8")
    _run_ssg(_make_config(source_dir, destination_dir, frame_file, exclude=["README.md"]))

    assert not (destination_dir / "README.md").exists()
    assert not (destination_dir / "README.html").exists()


def test_excluded_directory_is_skipped(source_dir, destination_dir, frame_file, md_file):
    """Directories listed in config.exclude must be skipped entirely."""
    ignored = source_dir / "ignored"
    ignored.mkdir()
    (ignored / "secret.md").write_text("# Secret", encoding="utf-8")
    _run_ssg(_make_config(source_dir, destination_dir, frame_file, exclude=["ignored"]))

    assert not (destination_dir / "ignored").exists()


# ------------------------------------------------------------------
# Subdirectory traversal
# ------------------------------------------------------------------

def test_subdirectory_structure_is_mirrored_in_destination(source_dir, destination_dir, frame_file, md_file):
    """The output destination must mirror the subdirectory structure of the source."""
    articles = source_dir / "articles"
    articles.mkdir()
    (articles / "article.md").write_text("# My Article\n\nContent here.", encoding="utf-8")
    _run_ssg(_make_config(source_dir, destination_dir, frame_file))

    assert (destination_dir / "articles").is_dir()
    assert (destination_dir / "articles" / "article.html").exists()


def test_multiple_markdown_files_all_rendered(source_dir, destination_dir, frame_file, md_file):
    """All Markdown files in the source directory must be rendered to the destination."""
    (source_dir / "page_a.md").write_text("# Page A\n\nContent A.", encoding="utf-8")
    (source_dir / "page_b.md").write_text("# Page B\n\nContent B.", encoding="utf-8")
    _run_ssg(_make_config(source_dir, destination_dir, frame_file))

    assert (destination_dir / "test.html").exists()
    assert (destination_dir / "page_a.html").exists()
    assert (destination_dir / "page_b.html").exists()


# ------------------------------------------------------------------
# Git last-edited timestamp
# ------------------------------------------------------------------

def test_last_edited_meta_tag_present_when_git_returns_timestamp(source_dir, destination_dir, frame_file, md_file):
    """When the git client returns a timestamp, a 'last-updated' meta tag must appear in the output."""
    timestamp = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
    _run_ssg(_make_config(source_dir, destination_dir, frame_file), git_timestamps={md_file: timestamp})

    content = (destination_dir / "test.html").read_text(encoding="utf-8")
    assert "last-updated" in content
    assert "2025-06-15" in content


def test_last_edited_meta_tag_absent_when_git_returns_no_timestamp(source_dir, destination_dir, frame_file, md_file):
    """When the git client returns no timestamp, no 'last-updated' meta tag should appear."""
    _run_ssg(_make_config(source_dir, destination_dir, frame_file))

    assert "last-updated" not in (destination_dir / "test.html").read_text(encoding="utf-8")

