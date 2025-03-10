import copy
from pathlib import Path
from urllib.parse import urlparse, urljoin

import bs4
from bs4 import BeautifulSoup

from fileprocessor.html_file import HTMLFile


class Frame:
    """
    Used to process a frame.
    A frame is an HTML file with a placeholder for embedding other HTML content, such as an article.
    """

    def __init__(self, content: str):
        self.soup = BeautifulSoup(content, 'lxml')

    @staticmethod
    def read_from_file(path: Path):
        """
        Read a frame from a file.
        :param path: Path to the file.
        """
        with open(path) as file:
            return Frame(file.read())

    def embed_content(self, html_file: HTMLFile, content_element_id="main-content") -> BeautifulSoup:
        """
        Embed HTML content into the current frame.
        :param html_file: HTML file.
        :param content_element_id: ID of HTML element where the embedding should happen.
        """
        soup_copy = copy.deepcopy(self.soup)
        article = soup_copy.find('article', id=content_element_id)
        article.clear()
        article.append(html_file.soup)
        return soup_copy

    def set_base_path(self, base_href: str):
        """
        Set base path for each link (href).
        :param base_href: base href
        :return: updated HTML content as string
        """
        element_to_attribute = {
            'a': 'href',
            'link': 'href',
            'script': 'src',
            'img': 'src'
        }
        for element, attribute in element_to_attribute.items():
            self._set_base_path_for_elements(self.soup.find_all(element), attribute, base_href)

    @staticmethod
    def _set_base_path_for_elements(elements: bs4.element.ResultSet, attribute: str, base_href: str):
        """
        Set the base path for the content of the attribute (href, src)
        :param elements: HTML element, can be <a>, <link>, <script>, <img>
        :param attribute: Attribute of the HTML element (href, src)
        :return: None
        """
        for element in filter(lambda elem: elem.has_attr(attribute), elements):
            url = element[attribute]
            if not bool(urlparse(url).netloc):
                element[attribute] = urljoin(base_href, url)
