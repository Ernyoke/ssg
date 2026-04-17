from typing import Optional

import markdown


class MarkDownFile:
    def __init__(self, content: str):
        self.content = content
        self.extensions = ['extra',
                           'sane_lists',
                           'smarty',
                           'pymdownx.tilde']

    def read(self, path):
        with open(path, encoding='utf-8') as file:
            self.content = file.read()

    def convert_to_html(self) -> str:
        html_content = markdown.markdown(self.content,
                                         extensions=self.extensions)
        return html_content

    def get_title(self) -> Optional[str]:
        """
        Attempts to infer the title from the Markdown content. It will look for the first
        ATX-style heading (e.g. # Title, ## Title) and return its text.
        :return: Title of the page as a string
        """
        for line in self.content.splitlines():
            stripped = line.strip()
            if stripped.startswith('#'):
                return stripped.lstrip('#').strip()
        return None

    @staticmethod
    def read_from_file(path):
        with open(path, encoding='utf-8') as file:
            return MarkDownFile(file.read())
