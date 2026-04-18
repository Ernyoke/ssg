from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup, Tag
from lxml import html, etree
from slugify import slugify

from content.article import Article
from fileprocessor.frame import Frame


class HTMLFile:
    @staticmethod
    def from_article(article: Article, frame: Frame, base_href: str) -> 'HTMLFile':
        soup = BeautifulSoup(article.markdown.convert_to_html(), 'lxml')
        html_file = HTMLFile(frame.embed_content(soup))
        html_file._replace_md_with_html()
        html_file.set_title(article.title)
        html_file.add_target_blank_to_external_urls(base_href)
        html_file.add_anchor_links()

        cover_image = article.get_cover_image()
        html_file.insert_og_meta(title=article.get_title(),
                                 description=article.get_description(),
                                 url=article.url,
                                 cover_image=cover_image.as_posix() if cover_image else None,
                                 twitter_handle=article.get_twitter_handle(),
                                 base_href=base_href,
                                 last_edited_time=article.get_last_edited())

        return html_file

    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
        self._replace_md_with_html()

    def _replace_md_with_html(self):
        """
        Replace href attributes which end with .md (Markdown) with attributes which end with .html.
        """
        for a in self.soup.find_all('a'):
            if isinstance(a, Tag) and 'href' in a.attrs:
                url = a['href']
                if isinstance(url, str) and url.endswith('.md'):
                    a['href'] = url.replace('.md', '.html')

    def add_target_blank_to_external_urls(self, base_href: str):
        """
        Add target="_blank" to <a> tags.
        :return: HTML document as a string
        """
        for a in self.soup.find_all('a'):
            if isinstance(a, Tag) and 'href' in a.attrs:
                url = a['href']
                # Check if url is absolute and does not start with a base path
                if isinstance(url, str) and (bool(urlparse(url).netloc) and not url.startswith(base_href)):
                    a['target'] = '_blank'

    def add_anchor_links(self):
        """
        Add anchor links to headings.
        """
        for title in self.soup.find_all('h2'):
            if isinstance(title, Tag):
                anchor_tag = self.soup.new_tag('a', attrs={'class': 'anchor-link',
                                                           'href': f'#{slugify(title.text)}',
                                                           'id': f'{slugify(title.text)}'})
                anchor_tag.string = '<<'
                title.append(anchor_tag)

    def insert_og_meta(self,
                       title: str|None,
                       description: str|None,
                       url: str|None,
                       cover_image: str|None,
                       twitter_handle: str | None,
                       base_href: str,
                       last_edited_time: Optional[datetime]):
        """
        Add og:meta fields to the header of an HTML page.
        """
        head = self.soup.find('head')
        if head is None or not isinstance(head, Tag):
            print(f'Warning! Could not find head tag in HTML document. Skipping adding og:meta fields.')
            return

        meta_title = self.soup.new_tag('meta', attrs={
            'property': 'og:title',
            'content': title or ''
        })
        head.append(meta_title)

        meta_description = self.soup.new_tag('meta', attrs={
            'property': 'og:description',
            'content': description or ''
        })
        head.append(meta_description)

        meta_url = self.soup.new_tag('meta', attrs={
            'property': 'og:url',
            'content': url or ''
        })
        head.append(meta_url)

        meta_image = self.soup.new_tag('meta', attrs={
            'property': 'og:image',
            'content': urljoin(base_href, cover_image) if cover_image else ''
        })
        head.append(meta_image)

        # Twitter specific meta tags
        twitter_meta_title = self.soup.new_tag('meta', attrs={
            'property': 'twitter:title',
            'content': title or ''
        })
        head.append(twitter_meta_title)

        twitter_meta_description = self.soup.new_tag('meta', attrs={
            'property': 'twitter:description',
            'content': description or ''
        })
        head.append(twitter_meta_description)

        twitter_meta_site = self.soup.new_tag('meta', attrs={
            'property': 'twitter:site',
            'content': twitter_handle or ''
        })
        head.append(twitter_meta_site)

        twitter_meta_creator = self.soup.new_tag('meta', attrs={
            'property': 'twitter:creator',
            'content': twitter_handle or ''
        })
        head.append(twitter_meta_creator)

        twitter_meta_image = self.soup.new_tag('meta', attrs={
            'property': 'twitter:image',
            'content': urljoin(base_href, cover_image) if cover_image else ''
        })
        head.append(twitter_meta_image)

        twitter_meta_card = self.soup.new_tag('meta', attrs={
            'property': 'twitter:card',
            'content': 'summary_large_image'
        })
        head.append(twitter_meta_card)

        if last_edited_time:
            last_updated = self.soup.new_tag('meta', attrs={
                'name': 'last-updated',
                'content': last_edited_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            })
            head.append(last_updated)

    def set_title(self, title, hostname=None):
        """
        Set the HTML title from the head of the document.
        :param title: HTML title
        :param hostname: hostname
        """
        composed_title = title
        if hostname is not None:
            composed_title = f'{title} - {hostname}'
        for titleElement in self.soup.find_all('title'):
            titleElement.string = composed_title

    def write(self, destination_path: Path):
        """
        Write the HTML page to a file.
        :param destination_path: destination path where to write the HTML page
        """
        with open(destination_path, mode='w', newline='\n', encoding='utf-8') as destination_file:
            # Parse the HTML string
            tree = html.fromstring(str(self.soup))

            # Convert to a pretty-printed string
            formatted_html = etree.tostring(tree, pretty_print=True, method="html", encoding="unicode")  # type: ignore[arg-type]

            # Output the formatted HTML
            destination_file.write(formatted_html)
