from unittest import TestCase

from ssg.content.markdown_file import MarkDownFile


class TestMarkDownFile(TestCase):
    def test_get_title_h1(self):
        md = MarkDownFile("""# This is a title
        ## This is another one""")
        self.assertEqual(md.get_title(), 'This is a title')

    def test_get_title_h2(self):
        # H1 is preferred even if an H2 appears first.
        md = MarkDownFile("""## This is a title
        # This is another one""")
        self.assertEqual(md.get_title(), 'This is another one')

    def test_get_title_only_h2_returns_h2(self):
        md = MarkDownFile("## Only subheading\n\nbody")
        self.assertEqual(md.get_title(), 'Only subheading')

    def test_get_title_none(self):
        md = MarkDownFile("""No title""")
        self.assertIsNone(md.get_title())

    def test_get_title_ignores_hash_in_fenced_code_block(self):
        md = MarkDownFile(
            "```python\n"
            "# this is a comment, not a title\n"
            "```\n"
            "\n"
            "# Real Title\n"
        )
        self.assertEqual(md.get_title(), 'Real Title')

    def test_get_title_requires_space_after_hash(self):
        md = MarkDownFile("#notaheading\n\n# Real Title\n")
        self.assertEqual(md.get_title(), 'Real Title')

    def test_get_title_strips_trailing_hashes(self):
        md = MarkDownFile("# Title ###\n")
        self.assertEqual(md.get_title(), 'Title')
