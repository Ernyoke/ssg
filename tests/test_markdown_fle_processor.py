from pathlib import Path
from unittest import TestCase

from bs4 import BeautifulSoup

from ssg.config import MetaFields, Meta, Config
from ssg.fileprocessor.markdown_fle_processor import MarkdownFileProcessor


class TestMarkdownFileProcessor(TestCase):
    def test_replace_md_with_html(self):
        self.assertEqual(MarkdownFileProcessor._replace_md_with_html(
            html_doc='<a href="asd.md"></a><a href="x.html"></a>'),
                         '<a href="asd.html"></a><a href="x.html"></a>')

    def test_add_og_meta(self):
        page = """
        <html>
            <head></head>
        </html>
        """
        meta_fields = MetaFields(
            title='Title',
            description='Description',
            url='https://example.dev',
            image='image/dev.jpg'
        )
        meta = Meta(meta_fields, [])
        config = Config(
            source=Path(),
            destination=Path(),
            base_href='https://base.dev',
            exclude=[],
            frames=[],
            meta=meta
        )

        md_file_processor = MarkdownFileProcessor(
            directory=Path('/tmp/'),
            file_name='test.md',
            config=Config(source=Path('/tmp/config'),
                          destination=Path('/tmp/config'),
                          base_href='ervinszilagyi.test',
                          exclude=[],
                          frames=[],
                          meta=meta),
            frames_cache=dict()
        )

        rendered = BeautifulSoup(md_file_processor._insert_og_meta(page), 'html.parser')
        head = rendered.find('head')

        meta = [element for element in head.find_all('meta')]
        self.assertEqual(len(meta), 4)

        properties = [m['property'] for m in meta]
        self.assertIn('og:title', properties)
        self.assertIn('og:description', properties)
        self.assertIn('og:url', properties)
        self.assertIn('og:image', properties)

    def test_get_title_from_doc_h1(self):
        doc = """
        <html>
            <body>
                <div>date</div>
                <h1>H1</h1>
                <h2>H2</h2>
            </body>
        </html>
        """
        h1 = MarkdownFileProcessor._get_title_from_page(doc)
        self.assertEqual('H1', h1)

    def test_get_title_from_doc_h2(self):
        doc = """
        <html>
            <body>
                <div>date</div>
                <h2>H2</h2>
                <h1>H1</h1>
            </body>
        </html>
        """
        h2 = MarkdownFileProcessor._get_title_from_page(doc)
        self.assertEqual('H2', h2)

    def test_get_title_from_doc_none(self):
        doc = """
        <html>
            <body>
            </body>
        </html>
        """
        h1 = MarkdownFileProcessor._get_title_from_page(doc)
        self.assertIsNone(h1)
