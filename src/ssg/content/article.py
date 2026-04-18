from datetime import datetime
from pathlib import Path

from ssg.content.markdown_file import MarkDownFile


class Article:
    def __init__(self,
                 markdown_file: MarkDownFile,
                 title: str,
                 cover_image: Path|None,
                 url: str|None,
                 last_edited: datetime|None,
                 twitter_handle: str|None):
        self.markdown = markdown_file
        self.title = title
        self.cover_image = cover_image
        self.url = url
        self.last_edited = last_edited
        self.twitter_handle = twitter_handle

    def get_title(self) -> str|None:
        return self.title if self.title else self.markdown.get_title()

    def get_description(self) -> str:
        return f'{self.title}: {self.url}'

    def get_cover_image(self) -> Path|None:
        return self.cover_image

    def get_url(self) -> str|None:
        return self.url

    def get_last_edited(self) -> datetime|None:
        return self.last_edited

    def get_twitter_handle(self) -> str|None:
        return self.twitter_handle