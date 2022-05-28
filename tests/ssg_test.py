import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from ssg.config import Config, Meta
from ssg.runner import ssg


class MyTestCase(unittest.TestCase):
    def test_replace_md_with_html(self):
        self.assertEqual(ssg.replace_md_with_html('<a href="asd.md"></a><a href="x.html"></a>'),
                         '<a href="asd.html"></a><a href="x.html"></a>')

    def test_add_og_meta(self):
        page = """
        <html>
            <head></head>
        </html>
        """
        config = Config(
            meta=Meta(title='Title', description='Description', url='http://example.dev', image='image/dev.jpg'),
            source=Path(), destination=Path(), base_href='http://base.dev', exclude=[], frame_name=''
        )
        rendered = BeautifulSoup(ssg.insert_og_meta(page, config), 'html.parser')
        head = rendered.find('head')

        meta = [element for element in head.find_all('meta')]
        self.assertEqual(len(meta), 4)

        properties = [m['property'] for m in meta]
        self.assertIn('og:title', properties)
        self.assertIn('og:description', properties)
        self.assertIn('og:url', properties)
        self.assertIn('og:image', properties)


if __name__ == '__main__':
    unittest.main()
