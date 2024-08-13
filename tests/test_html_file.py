from unittest import TestCase

from bs4 import BeautifulSoup

from ssg.fileprocessor.html_file import HTMLFile


class TestHTMLFile(TestCase):
    def test__replace_md_with_html(self):
        html_file = HTMLFile(BeautifulSoup('<a href="asd.md"></a><a href="x.html"></a>', 'html.parser'))
        self.assertEqual(str(html_file.soup),
                         '<a href="asd.html"></a><a href="x.html"></a>')
