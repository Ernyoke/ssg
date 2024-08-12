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
            hostname='base.dev',
            exclude=[],
            frames=[],
            meta=meta
        )

        md_file_processor = MarkdownFileProcessor(
            directory=Path('/tmp/'),
            file_name='test.md',
            destination_dir=Path('/tmp/dest'),
            config=config,
            frames_cache=dict()
        )

        md_file_processor.soup = BeautifulSoup(page, 'html.parser')

        md_file_processor._insert_og_meta(meta=None)

        head = md_file_processor.soup.find('head')

        meta = [element for element in head.find_all('meta')]
        self.assertEqual(len(meta), 4)

        properties = [m['property'] for m in meta]
        self.assertIn('og:title', properties)
        self.assertIn('og:description', properties)
        self.assertIn('og:url', properties)
        self.assertIn('og:image', properties)

    def test_get_title_from_doc_h1(self):
        page = """
        <html>
            <body>
                <div>date</div>
                <h1>H1</h1>
                <h2>H2</h2>
            </body>
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
            hostname='base.dev',
            exclude=[],
            frames=[],
            meta=meta
        )

        md_file_processor = MarkdownFileProcessor(
            directory=Path('/tmp/'),
            file_name='test.md',
            destination_dir=Path('/tmp/dest'),
            config=config,
            frames_cache=dict()
        )

        md_file_processor.soup = BeautifulSoup(page, 'html.parser')

        h1 = md_file_processor._get_title_from_page()
        self.assertEqual('H1', h1)

    def test_get_title_from_doc_h2(self):
        page = """
        <html>
            <body>
                <div>date</div>
                <h2>H2</h2>
                <h1>H1</h1>
            </body>
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
            hostname='base.dev',
            exclude=[],
            frames=[],
            meta=meta
        )

        md_file_processor = MarkdownFileProcessor(
            directory=Path('/tmp/'),
            file_name='test.md',
            destination_dir=Path('/tmp/dest'),
            config=config,
            frames_cache=dict()
        )

        md_file_processor.soup = BeautifulSoup(page, 'html.parser')

        h2 = md_file_processor._get_title_from_page()
        self.assertEqual('H2', h2)

    def test_get_title_from_doc_none(self):
        page = """
        <html>
            <body>
                <div>date</div>
            </body>
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
            hostname='base.dev',
            exclude=[],
            frames=[],
            meta=meta
        )

        md_file_processor = MarkdownFileProcessor(
            directory=Path('/tmp/'),
            file_name='test.md',
            destination_dir=Path('/tmp/dest'),
            config=config,
            frames_cache=dict()
        )

        md_file_processor.soup = BeautifulSoup(page, 'html.parser')

        self.assertIsNone(md_file_processor._get_title_from_page())
