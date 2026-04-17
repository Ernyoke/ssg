from datetime import datetime
from pathlib import Path

from fileprocessor.markdown_file import MarkDownFile


class Article:
    def __init__(self, markdown_file: MarkDownFile, title: str, cover_image: Path|None, url: str|None, last_edited: datetime|None):
        self.markdown = markdown_file
        self.title = title
        self.cover_image = cover_image
        self.url = url
        self.last_edited = last_edited