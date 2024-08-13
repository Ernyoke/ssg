from unittest import TestCase

from ssg.fileprocessor.markdown_file import MarkDownFile


class TestMarkDownFile(TestCase):
    def test_get_title_h1(self):
        md = MarkDownFile("""# This is a title
        ## This is another one""")
        self.assertEqual(md.get_title(),
                         'This is a title')

    def test_get_title_h2(self):
        md = MarkDownFile("""## This is a title
        # This is another one""")
        self.assertEqual(md.get_title(),
                         'This is a title')

    def test_get_title_none(self):
        md = MarkDownFile("""No title""")
        self.assertIsNone(md.get_title())
