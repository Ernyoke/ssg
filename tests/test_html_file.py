import tempfile
from datetime import datetime, UTC
from pathlib import Path
from unittest import TestCase

from bs4 import BeautifulSoup

from ssg.template.html_file import HTMLFile

BASE_HTML = """\
<!DOCTYPE html>
<html>
<head>
    <title>Original Title</title>
</head>
<body>
    <article id="main-content"></article>
</body>
</html>
"""


def _make_html_file(html: str = BASE_HTML) -> HTMLFile:
    soup = BeautifulSoup(html, 'lxml')
    return HTMLFile(soup)


class TestReplaceMdWithHtml(TestCase):
    def test_md_link_replaced_with_html(self):
        soup = BeautifulSoup('<a href="page.md">link</a>', 'lxml')
        hf = HTMLFile(soup)
        a = hf.soup.find('a')
        self.assertEqual(a['href'], 'page.html')

    def test_non_md_link_unchanged(self):
        soup = BeautifulSoup('<a href="page.html">link</a>', 'lxml')
        hf = HTMLFile(soup)
        a = hf.soup.find('a')
        self.assertEqual(a['href'], 'page.html')

    def test_external_link_unchanged(self):
        soup = BeautifulSoup('<a href="https://example.com">link</a>', 'lxml')
        hf = HTMLFile(soup)
        a = hf.soup.find('a')
        self.assertEqual(a['href'], 'https://example.com')

    def test_multiple_md_links_all_replaced(self):
        html = '<a href="a.md">a</a><a href="b.md">b</a>'
        soup = BeautifulSoup(html, 'lxml')
        hf = HTMLFile(soup)
        hrefs = [a['href'] for a in hf.soup.find_all('a')]
        self.assertEqual(hrefs, ['a.html', 'b.html'])

    def test_link_without_href_not_broken(self):
        soup = BeautifulSoup('<a name="anchor">anchor</a>', 'lxml')
        # Should not raise
        hf = HTMLFile(soup)
        a = hf.soup.find('a')
        self.assertNotIn('href', a.attrs)

    def test_md_in_middle_of_url_not_replaced(self):
        # Only trailing .md should be replaced
        soup = BeautifulSoup('<a href="https://example.com/readme.md.bak">link</a>', 'lxml')
        hf = HTMLFile(soup)
        a = hf.soup.find('a')
        self.assertEqual(a['href'], 'https://example.com/readme.md.bak')


class TestAddTargetBlankToExternalUrls(TestCase):
    BASE_HREF = 'https://example.com'

    def test_external_link_gets_target_blank(self):
        soup = BeautifulSoup('<a href="https://other.com/page">link</a>', 'lxml')
        hf = HTMLFile(soup)
        hf.add_target_blank_to_external_urls(self.BASE_HREF)
        a = hf.soup.find('a')
        self.assertEqual(a.get('target'), '_blank')

    def test_internal_absolute_link_no_target_blank(self):
        soup = BeautifulSoup('<a href="https://example.com/page">link</a>', 'lxml')
        hf = HTMLFile(soup)
        hf.add_target_blank_to_external_urls(self.BASE_HREF)
        a = hf.soup.find('a')
        self.assertNotIn('target', a.attrs)

    def test_relative_link_no_target_blank(self):
        soup = BeautifulSoup('<a href="/about">link</a>', 'lxml')
        hf = HTMLFile(soup)
        hf.add_target_blank_to_external_urls(self.BASE_HREF)
        a = hf.soup.find('a')
        self.assertNotIn('target', a.attrs)

    def test_link_without_href_not_broken(self):
        soup = BeautifulSoup('<a name="anchor">anchor</a>', 'lxml')
        hf = HTMLFile(soup)
        # Should not raise
        hf.add_target_blank_to_external_urls(self.BASE_HREF)
        a = hf.soup.find('a')
        self.assertNotIn('target', a.attrs)

    def test_multiple_links_only_external_get_target(self):
        html = (
            '<a href="https://other.com">ext</a>'
            '<a href="https://example.com/page">int</a>'
            '<a href="/relative">rel</a>'
        )
        soup = BeautifulSoup(html, 'lxml')
        hf = HTMLFile(soup)
        hf.add_target_blank_to_external_urls(self.BASE_HREF)
        links = hf.soup.find_all('a')
        self.assertEqual(links[0].get('target'), '_blank')
        self.assertNotIn('target', links[1].attrs)
        self.assertNotIn('target', links[2].attrs)


class TestAddAnchorLinks(TestCase):
    def test_anchor_link_added_to_h2(self):
        soup = BeautifulSoup('<h2>Section One</h2>', 'lxml')
        hf = HTMLFile(soup)
        hf.add_anchor_links()
        anchor = hf.soup.find('a', class_='anchor-link')
        self.assertIsNotNone(anchor)
        self.assertEqual(anchor.get('href'), '#section-one')
        self.assertEqual(anchor.get('id'), 'section-one')
        self.assertEqual(anchor.string, '<<')

    def test_no_anchor_link_added_to_h1(self):
        soup = BeautifulSoup('<h1>Main Title</h1>', 'lxml')
        hf = HTMLFile(soup)
        hf.add_anchor_links()
        anchor = hf.soup.find('a', class_='anchor-link')
        self.assertIsNone(anchor)

    def test_multiple_h2_each_get_anchor(self):
        html = '<h2>First Section</h2><h2>Second Section</h2>'
        soup = BeautifulSoup(html, 'lxml')
        hf = HTMLFile(soup)
        hf.add_anchor_links()
        anchors = hf.soup.find_all('a', class_='anchor-link')
        self.assertEqual(len(anchors), 2)
        self.assertEqual(anchors[0].get('href'), '#first-section')
        self.assertEqual(anchors[1].get('href'), '#second-section')

    def test_anchor_id_is_slugified(self):
        soup = BeautifulSoup('<h2>Hello World! 123</h2>', 'lxml')
        hf = HTMLFile(soup)
        hf.add_anchor_links()
        anchor = hf.soup.find('a', class_='anchor-link')
        self.assertIsNotNone(anchor)
        self.assertEqual(anchor.get('id'), 'hello-world-123')


class TestInsertOgMeta(TestCase):
    BASE_HREF = 'https://example.com/'

    def _insert(self, hf: HTMLFile, **overrides):
        """Call insert_og_meta with sensible defaults, allowing per-test overrides."""
        kwargs = dict(
            title='My Title',
            description='My description',
            url='https://example.com/page',
            cover_image='images/cover.png',
            twitter_handle='@myhandle',
            base_href=self.BASE_HREF,
            last_edited_time=None,
        )
        kwargs.update(overrides)
        hf.insert_og_meta(**kwargs)

    def test_og_title_inserted(self):
        hf = _make_html_file()
        self._insert(hf)
        tag = hf.soup.find('meta', attrs={'property': 'og:title'})
        self.assertIsNotNone(tag)
        self.assertEqual(tag['content'], 'My Title')

    def test_og_description_inserted(self):
        hf = _make_html_file()
        self._insert(hf)
        tag = hf.soup.find('meta', attrs={'property': 'og:description'})
        self.assertIsNotNone(tag)
        self.assertEqual(tag['content'], 'My description')

    def test_og_url_inserted(self):
        hf = _make_html_file()
        self._insert(hf)
        tag = hf.soup.find('meta', attrs={'property': 'og:url'})
        self.assertIsNotNone(tag)
        self.assertEqual(tag['content'], 'https://example.com/page')

    def test_og_image_inserted_with_base_href(self):
        hf = _make_html_file()
        self._insert(hf, cover_image='images/cover.png')
        tag = hf.soup.find('meta', attrs={'property': 'og:image'})
        self.assertIsNotNone(tag)
        self.assertEqual(tag['content'], 'https://example.com/images/cover.png')

    def test_twitter_title_inserted(self):
        hf = _make_html_file()
        self._insert(hf)
        tag = hf.soup.find('meta', attrs={'property': 'twitter:title'})
        self.assertIsNotNone(tag)
        self.assertEqual(tag['content'], 'My Title')

    def test_twitter_description_inserted(self):
        hf = _make_html_file()
        self._insert(hf)
        tag = hf.soup.find('meta', attrs={'property': 'twitter:description'})
        self.assertIsNotNone(tag)
        self.assertEqual(tag['content'], 'My description')

    def test_twitter_site_inserted(self):
        hf = _make_html_file()
        self._insert(hf)
        tag = hf.soup.find('meta', attrs={'property': 'twitter:site'})
        self.assertIsNotNone(tag)
        self.assertEqual(tag['content'], '@myhandle')

    def test_twitter_creator_inserted(self):
        hf = _make_html_file()
        self._insert(hf)
        tag = hf.soup.find('meta', attrs={'property': 'twitter:creator'})
        self.assertIsNotNone(tag)
        self.assertEqual(tag['content'], '@myhandle')

    def test_twitter_card_inserted(self):
        hf = _make_html_file()
        self._insert(hf)
        tag = hf.soup.find('meta', attrs={'property': 'twitter:card'})
        self.assertIsNotNone(tag)
        self.assertEqual(tag['content'], 'summary_large_image')

    def test_last_updated_inserted_when_datetime_provided(self):
        hf = _make_html_file()
        dt = datetime(2025, 3, 10, 9, 30, 0, tzinfo=UTC)
        self._insert(hf, last_edited_time=dt)
        tag = hf.soup.find('meta', attrs={'name': 'last-updated'})
        self.assertIsNotNone(tag)
        self.assertIn('2025-03-10', tag['content'])

    def test_last_updated_not_inserted_when_datetime_is_none(self):
        hf = _make_html_file()
        self._insert(hf, last_edited_time=None)
        tag = hf.soup.find('meta', attrs={'name': 'last-updated'})
        self.assertIsNone(tag)

    def test_none_title_defaults_to_empty_string(self):
        hf = _make_html_file()
        self._insert(hf, title=None)
        tag = hf.soup.find('meta', attrs={'property': 'og:title'})
        self.assertIsNone(tag)

    def test_none_description_defaults_to_missing_description(self):
        hf = _make_html_file()
        self._insert(hf, description=None)
        tag = hf.soup.find('meta', attrs={'property': 'og:description'})
        self.assertIsNone(tag)


class TestSetTitle(TestCase):
    def test_title_set_without_hostname(self):
        hf = _make_html_file()
        hf.set_page_title('New Title')
        title_tag = hf.soup.find('title')
        self.assertEqual(title_tag.string, 'New Title')

    def test_title_set_with_hostname(self):
        hf = _make_html_file()
        hf.set_page_title('My Page', hostname='example.com')
        title_tag = hf.soup.find('title')
        self.assertEqual(title_tag.string, 'My Page - example.com')

    def test_title_none_hostname_omitted(self):
        hf = _make_html_file()
        hf.set_page_title('Only Title', hostname=None)
        title_tag = hf.soup.find('title')
        self.assertEqual(title_tag.string, 'Only Title')

    def test_multiple_title_tags_all_updated(self):
        html = '<html><head><title>A</title><title>B</title></head><body></body></html>'
        soup = BeautifulSoup(html, 'lxml')
        hf = HTMLFile(soup)
        hf.set_page_title('Updated')
        titles = [t.string for t in hf.soup.find_all('title')]
        self.assertTrue(all(t == 'Updated' for t in titles))


class TestWrite(TestCase):
    def test_write_creates_file(self):
        hf = _make_html_file()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'output.html'
            hf.write(dest)
            self.assertTrue(dest.exists())

    def test_write_content_is_valid_html(self):
        hf = _make_html_file()
        hf.set_page_title('Written Page')
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'output.html'
            hf.write(dest)
            content = dest.read_text(encoding='utf-8')
            self.assertIn('Written Page', content)

    def test_write_uses_utf8_encoding(self):
        html = '<html><head><title>Tëst</title></head><body><p>Héllo</p></body></html>'
        soup = BeautifulSoup(html, 'lxml')
        hf = HTMLFile(soup)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'output.html'
            hf.write(dest)
            content = dest.read_text(encoding='utf-8')
            self.assertIn('Tëst', content)
            self.assertIn('Héllo', content)

    def test_write_uses_unix_line_endings(self):
        hf = _make_html_file()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'output.html'
            hf.write(dest)
            raw = dest.read_bytes()
            self.assertNotIn(b'\r\n', raw)

