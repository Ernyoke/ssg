from typing import Optional

import markdown
from bs4 import BeautifulSoup

from fileprocessor.html_file import HTMLFile


class MarkDownFile:
    def __init__(self, content: str):
        self.content = content
        self.extensions = ['extra',
                           'sane_lists']

    def read(self, path):
        with open(path) as file:
            self.content = file.read()

    def convert_to_html(self) -> HTMLFile:
        html_content = markdown.markdown(self.content,
                                         extensions=self.extensions)
        return HTMLFile(BeautifulSoup(html_content, 'lxml'))

    def get_title(self) -> Optional[str]:
        """
        Attempts to infer the title from the HTML page. It will look for h1, h2...h6 tags and return the first one found
        in the page.
        :return: Title of the page as a string
        """
        html_content = markdown.markdown(self.content, extensions=self.extensions)
        soup = BeautifulSoup(html_content, 'lxml')
        element = soup.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if element is not None:
            return element.text
        return None

    @staticmethod
    def read_from_file(path):
        with open(path) as file:
            return MarkDownFile(file.read())
