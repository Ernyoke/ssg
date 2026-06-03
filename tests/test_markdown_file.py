from datetime import datetime
from pathlib import Path
from unittest import TestCase

from ssg.content.markdown_file import MarkDownFile


def _make(content: str) -> MarkDownFile:
    return MarkDownFile(Path("test.md"), content)


class TestMarkDownFile(TestCase):
    def test_get_title_from_meta(self):
        md = _make("title: This is a title\n\n# Heading\n")
        self.assertEqual(md.get_title(), 'This is a title')

    def test_get_title_none_when_absent(self):
        md = _make("# Heading\n\nNo metadata here.")
        self.assertIsNone(md.get_title())

    def test_get_summary_from_meta(self):
        md = _make("summary: A short summary\n\nbody")
        self.assertEqual(md.get_summary(), 'A short summary')

    def test_get_summary_none_when_absent(self):
        md = _make("body only")
        self.assertIsNone(md.get_summary())

    def test_get_author_from_meta(self):
        md = _make("author: Jane Doe\n\nbody")
        self.assertEqual(md.get_author(), 'Jane Doe')

    def test_get_email_from_meta(self):
        md = _make("email: jane@example.com\n\nbody")
        self.assertEqual(md.get_email(), 'jane@example.com')

    def test_get_twitter_handle_from_meta(self):
        md = _make("twitter: @jane\n\nbody")
        self.assertEqual(md.get_twitter_handle(), '@jane')

    def test_get_github_handle_from_meta(self):
        md = _make("github: janedoe\n\nbody")
        self.assertEqual(md.get_github_handle(), 'janedoe')

    def test_get_cover_image_from_meta(self):
        md = _make("cover: cover.png\n\nbody")
        self.assertEqual(md.get_cover_image(), 'cover.png')

    def test_get_tags_returns_list(self):
        md = _make("tags: python\n\nbody")
        self.assertEqual(md.get_tags(), ['python'])

    def test_get_tags_empty_when_absent(self):
        md = _make("body only")
        self.assertEqual(md.get_tags(), [])

    def test_get_publish_date_parsed(self):
        md = _make("date: 2025-01-15\n\nbody")
        self.assertEqual(md.get_publish_date(), datetime(2025, 1, 15))

    def test_get_publish_date_none_when_absent(self):
        md = _make("body only")
        self.assertIsNone(md.get_publish_date())

    def test_get_publish_date_invalid_returns_none(self):
        md = _make("date: not-a-date\n\nbody")
        self.assertIsNone(md.get_publish_date())

    def test_convert_to_html(self):
        md = _make("# Real Title\n\nSome text.")
        html = md.convert_to_html()
        self.assertIn('<h1>Real Title</h1>', html)
        self.assertIn('Some text.', html)
