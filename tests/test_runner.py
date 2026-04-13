import shutil
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

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


class TestSSGIntegration(TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.test_dir) / 'source'
        self.destination_dir = Path(self.test_dir) / 'destination'
        self.source_dir.mkdir()
        self.destination_dir.mkdir()

        # Create frame file (absolute path so frames_to_exclude check works)
        self.frame_path = self.source_dir / 'frame.html'
        self.frame_path.write_text(MINIMAL_FRAME_HTML, encoding='utf-8')

        # Create a sample Markdown file
        self.md_file = self.source_dir / 'test.md'
        self.md_file.write_text(SAMPLE_MARKDOWN, encoding='utf-8')

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _make_config(self, extra_matchers=None, exclude=None):
        default_meta = MetaFields(
            title='Test Site',
            image='images/cover.png',
            description='Test description.',
            url='https://example.com',
            twitter_handle='@test'
        )
        matchers = [Matcher(file='*.md', action='TAKE_FROM_CONTENT', meta_fields=None)]
        if extra_matchers:
            matchers = extra_matchers + matchers
        meta = Meta(default=default_meta, matchers=matchers)
        # Use absolute frame path so that frames_to_exclude correctly filters the frame file
        frame = ConfigFrame(file='*.md', frame=self.frame_path)
        return Config(
            source=self.source_dir,
            destination=self.destination_dir,
            base_href='https://example.com/',
            hostname='example.com',
            exclude=exclude or [],
            meta=meta,
            frames=[frame]
        )

    def _run_ssg(self, config):
        """Helper that runs SSG with the git client mocked out."""
        with patch('git.GitClient') as mock_git_client_class:
            mock_instance = MagicMock()
            mock_instance.get_last_edit_time_for_files.return_value = {}
            mock_git_client_class.return_value = mock_instance
            SSG(config).run()

    # ------------------------------------------------------------------
    # Core rendering
    # ------------------------------------------------------------------

    def test_markdown_is_converted_to_html(self):
        """A Markdown file in the source directory must be rendered as an HTML file."""
        config = self._make_config()
        self._run_ssg(config)

        output_file = self.destination_dir / 'test.html'
        self.assertTrue(output_file.exists(), f'Expected output file {output_file} to exist')
        content = output_file.read_text(encoding='utf-8')
        self.assertIn('Hello World', content)
        self.assertIn('Section One', content)
        self.assertIn('Some content here', content)

    def test_output_html_contains_og_meta_tags(self):
        """Rendered HTML must contain Open Graph meta tags from the config."""
        config = self._make_config()
        self._run_ssg(config)

        content = (self.destination_dir / 'test.html').read_text(encoding='utf-8')
        self.assertIn('og:title', content)
        self.assertIn('og:description', content)
        self.assertIn('og:url', content)
        self.assertIn('og:image', content)

    def test_output_html_title_derived_from_markdown_heading(self):
        """With TAKE_FROM_CONTENT matcher the <title> tag must be set from the first heading."""
        config = self._make_config()
        self._run_ssg(config)

        content = (self.destination_dir / 'test.html').read_text(encoding='utf-8')
        soup = BeautifulSoup(content, 'lxml')
        title_tag = soup.find('title')
        self.assertIsNotNone(title_tag)
        self.assertIn('Hello World', title_tag.text)
        self.assertIn('example.com', title_tag.text)

    def test_static_meta_matcher_overrides_title(self):
        """With a STATIC matcher the og:title must be taken from the matcher's meta_fields."""
        static_meta = MetaFields(
            title='Overridden Title',
            image=None,
            description=None,
            url=None,
            twitter_handle=None
        )
        static_matcher = Matcher(file='*/test.md', action='STATIC', meta_fields=static_meta)
        config = self._make_config(extra_matchers=[static_matcher])
        self._run_ssg(config)

        content = (self.destination_dir / 'test.html').read_text(encoding='utf-8')
        self.assertIn('Overridden Title', content)

    def test_markdown_links_converted_to_html_links(self):
        """Hyperlinks pointing to .md files must be rewritten to .html in the output."""
        (self.source_dir / 'linked.md').write_text(
            '# Linked Page\n\n[Go to test](test.md)', encoding='utf-8'
        )
        config = self._make_config()
        self._run_ssg(config)

        content = (self.destination_dir / 'linked.html').read_text(encoding='utf-8')
        self.assertIn('test.html', content)
        self.assertNotIn('test.md', content)

    # ------------------------------------------------------------------
    # File copying
    # ------------------------------------------------------------------

    def test_non_markdown_file_is_copied(self):
        """Non-Markdown files (e.g. CSS, images) must be copied verbatim to the destination."""
        css_file = self.source_dir / 'style.css'
        css_content = 'body { margin: 0; }'
        css_file.write_text(css_content, encoding='utf-8')

        config = self._make_config()
        self._run_ssg(config)

        copied = self.destination_dir / 'style.css'
        self.assertTrue(copied.exists())
        self.assertEqual(copied.read_text(encoding='utf-8'), css_content)

    def test_frame_file_is_not_copied_to_destination(self):
        """Frame HTML files must be excluded from the destination directory."""
        config = self._make_config()
        self._run_ssg(config)

        self.assertFalse((self.destination_dir / 'frame.html').exists())

    # ------------------------------------------------------------------
    # Exclusions
    # ------------------------------------------------------------------

    def test_excluded_file_is_not_copied(self):
        """Files listed in config.exclude must not appear in the destination."""
        excluded = self.source_dir / 'README.md'
        excluded.write_text('# README', encoding='utf-8')

        config = self._make_config(exclude=['README.md'])
        self._run_ssg(config)

        self.assertFalse((self.destination_dir / 'README.md').exists())
        self.assertFalse((self.destination_dir / 'README.html').exists())

    def test_excluded_directory_is_skipped(self):
        """Directories listed in config.exclude must be skipped entirely."""
        ignored_dir = self.source_dir / 'ignored'
        ignored_dir.mkdir()
        (ignored_dir / 'secret.md').write_text('# Secret', encoding='utf-8')

        config = self._make_config(exclude=['ignored'])
        self._run_ssg(config)

        self.assertFalse((self.destination_dir / 'ignored').exists())

    # ------------------------------------------------------------------
    # Subdirectory traversal
    # ------------------------------------------------------------------

    def test_subdirectory_structure_is_mirrored_in_destination(self):
        """The output destination must mirror the subdirectory structure of the source."""
        sub_dir = self.source_dir / 'articles'
        sub_dir.mkdir()
        (sub_dir / 'article.md').write_text('# My Article\n\nContent here.', encoding='utf-8')

        config = self._make_config()
        self._run_ssg(config)

        self.assertTrue((self.destination_dir / 'articles').is_dir())
        self.assertTrue((self.destination_dir / 'articles' / 'article.html').exists())

    def test_multiple_markdown_files_all_rendered(self):
        """All Markdown files in the source directory must be rendered to the destination."""
        (self.source_dir / 'page_a.md').write_text('# Page A\n\nContent A.', encoding='utf-8')
        (self.source_dir / 'page_b.md').write_text('# Page B\n\nContent B.', encoding='utf-8')

        config = self._make_config()
        self._run_ssg(config)

        self.assertTrue((self.destination_dir / 'test.html').exists())
        self.assertTrue((self.destination_dir / 'page_a.html').exists())
        self.assertTrue((self.destination_dir / 'page_b.html').exists())

    # ------------------------------------------------------------------
    # Git last-edited timestamp
    # ------------------------------------------------------------------

    def test_last_edited_meta_tag_present_when_git_returns_timestamp(self):
        """When the git client returns a timestamp, a 'last-updated' meta tag must appear in the output."""
        from datetime import datetime, UTC

        timestamp = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)

        with patch('git.GitClient') as mock_git_client_class:
            mock_instance = MagicMock()
            mock_instance.get_last_edit_time_for_files.return_value = {
                self.md_file: timestamp
            }
            mock_git_client_class.return_value = mock_instance
            SSG(self._make_config()).run()

        content = (self.destination_dir / 'test.html').read_text(encoding='utf-8')
        self.assertIn('last-updated', content)
        self.assertIn('2025-06-15', content)

    def test_last_edited_meta_tag_absent_when_git_returns_no_timestamp(self):
        """When the git client returns no timestamp, no 'last-updated' meta tag should appear."""
        config = self._make_config()
        self._run_ssg(config)

        content = (self.destination_dir / 'test.html').read_text(encoding='utf-8')
        self.assertNotIn('last-updated', content)

