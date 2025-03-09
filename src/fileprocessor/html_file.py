from pathlib import Path
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
from slugify import slugify

from config import MetaFields


class HTMLFile:
    """
    Used to process an HTML document.
    """

    def __init__(self, content: BeautifulSoup):
        self.soup = content
        self._replace_md_with_html()

    def _replace_md_with_html(self):
        """
        Replace href attributes which end with .md (Markdown) with attributes which end with .html.
        """
        for a in self.soup.find_all('a'):
            if 'href' in a.attrs:
                url = a['href']
                if url.endswith('.md'):
                    a['href'] = url.replace('.md', '.html')

    def add_target_blank_to_external_urls(self, base_href: str):
        """
        Add target="_blank" to <a> tags.
        :return: HTML document as a string
        """
        for a in self.soup.find_all('a'):
            if 'href' in a.attrs:
                url = a['href']
                # Check if url is absolute and does not start with a base path
                if bool(urlparse(url).netloc) and not url.startswith(base_href):
                    a['target'] = '_blank'

    def add_anchor_links(self):
        """
        Add anchor links to headings.
        """
        for title in self.soup.find_all('h2'):
            anchor_tag = self.soup.new_tag('a', attrs={'class': 'anchor-link',
                                                       'href': f'#{slugify(title.text)}',
                                                       'id': f'{slugify(title.text)}'})
            anchor_tag.string = '<<'
            title.append(anchor_tag)

    def insert_og_meta(self,
                       meta: MetaFields,
                       base_href: str):
        """
        Add og:meta fields to the header of an HTML page.
        :param meta: meta fields
        :param base_href: base url
        :return: updated HTML page as a string
        """
        head = self.soup.find('head')
        meta_title = self.soup.new_tag('meta', attrs={
            'property': 'og:title',
            'content': meta.title
        })
        head.append(meta_title)

        meta_description = self.soup.new_tag('meta', attrs={
            'property': 'og:description',
            'content': meta.description
        })
        head.append(meta_description)

        meta_url = self.soup.new_tag('meta', attrs={
            'property': 'og:url',
            'content': meta.url
        })
        head.append(meta_url)

        meta_image = self.soup.new_tag('meta', attrs={
            'property': 'og:image',
            'content': urljoin(base_href, meta.image)
        })
        head.append(meta_image)

        # Twitter specific meta tags
        twitter_meta_title = self.soup.new_tag('meta', attrs={
            'property': 'twitter:title',
            'content': meta.title
        })
        head.append(twitter_meta_title)

        twitter_meta_description = self.soup.new_tag('meta', attrs={
            'property': 'twitter:description',
            'content': meta.description
        })
        head.append(twitter_meta_description)

        twitter_meta_site = self.soup.new_tag('meta', attrs={
            'property': 'twitter:site',
            'content': meta.twitter_handle
        })
        head.append(twitter_meta_site)

        twitter_meta_creator = self.soup.new_tag('meta', attrs={
            'property': 'twitter:creator',
            'content': meta.twitter_handle
        })
        head.append(twitter_meta_creator)

        twitter_meta_image = self.soup.new_tag('meta', attrs={
            'property': 'twitter:image',
            'content': urljoin(base_href, meta.image)
        })
        head.append(twitter_meta_image)

        twitter_meta_card = self.soup.new_tag('meta', attrs={
            'property': 'twitter:card',
            'content': 'summary_large_image'
        })
        head.append(twitter_meta_card)


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
        with open(destination_path, mode='w', newline='\n') as destination_file:
            destination_file.write(str(self.soup))
