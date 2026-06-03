from datetime import datetime
import re
from pathlib import Path
from typing import Optional

import markdown

class MarkDownFile:
    def __init__(self, path: Path, content: str):
        self.path = path
        self.content = content
        self.extensions = ['extra',
                           'sane_lists',
                           'smarty',
                           'pymdownx.tilde',
                           'meta']
        self.md = markdown.Markdown(extensions=self.extensions)
        self.html = self.md.convert(content)

    def get_title(self) -> Optional[str]:
        title_list = self.md.Meta.get('title', [])
        if len(title_list) > 0:
            return title_list[0]
        return None

    def get_summary(self) -> Optional[str]:
        summary_list = self.md.Meta.get('summary', [])
        if len(summary_list) > 0:
            return summary_list[0]
        return None

    def get_author(self) -> Optional[str]:
        author = self.md.Meta.get('author', [])
        if len(author) > 0:
            return author[0]
        return None

    def get_twitter_handle(self) -> Optional[str]:
        twitter_handle = self.md.Meta.get('twitter', [])
        if len(twitter_handle) > 0:
            return twitter_handle[0]
        return None

    def get_email(self) -> Optional[str]:
        email = self.md.Meta.get('email', [])
        if len(email) > 0:
            return email[0]
        return None

    def get_github_handle(self) -> Optional[str]:
        github = self.md.Meta.get('github', [])
        if len(github) > 0:
            return github[0]
        return None

    def get_tags(self) -> list[str]:
        return self.md.Meta.get('tags', [])

    def get_publish_date(self) -> Optional[datetime]:
        date_list = self.md.Meta.get('date', [])
        if not date_list:
            return None
        raw = re.sub(r'\s+', ' ', date_list[0].strip())
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            print(f"Invalid publish date format '{raw}' for file '{self.path.as_posix()}'")
            return None

    def get_cover_image(self) -> Optional[str]:
        cover_image = self.md.Meta.get('cover', [])
        if len(cover_image) > 0:
            return cover_image[0]
        return None

    def convert_to_html(self) -> str:
        return self.html

    @staticmethod
    def read_from_file(path: Path):
        with open(path, encoding='utf-8') as file:
            return MarkDownFile(path, file.read())
