from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ssg.content.markdown_file import MarkDownFile

@dataclass
class Author:
    name: str | None = None
    email: str | None = None
    twitter_handle: str | None = None
    github_handle: str | None = None


@dataclass
class Article:
    markdown: MarkDownFile
    title: str
    url: str
    author: Author
    cover_image: str | None = None
    description: str | None = None
    last_edited: datetime | None = None