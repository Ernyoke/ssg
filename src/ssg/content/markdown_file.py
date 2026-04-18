import re
from typing import Optional

import markdown

# ATX heading: 1–6 leading '#', a space, then the title text. Trailing '#'s are stripped.
_ATX_HEADING_RE = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')
# Fenced code block delimiter: ``` or ~~~ (optionally followed by an info string).
_FENCE_RE = re.compile(r'^(?:`{3,}|~{3,})')


class MarkDownFile:
    def __init__(self, content: str):
        self.content = content
        self.extensions = ['extra',
                           'sane_lists',
                           'smarty',
                           'pymdownx.tilde']

    def convert_to_html(self) -> str:
        html_content = markdown.markdown(self.content,
                                         extensions=self.extensions)
        return html_content

    def get_title(self) -> Optional[str]:
        """
        Infer the page title from the Markdown content.

        Walks the document once and returns:
          - the first level-1 ATX heading ('# Title') if found, otherwise
          - the first ATX heading of any level, otherwise
          - ``None``.

        Lines inside fenced code blocks (``` or ~~~) are ignored.
        """
        first_heading: Optional[str] = None
        in_fence = False

        for line in self.content.splitlines():
            stripped = line.strip()

            if _FENCE_RE.match(stripped):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            match = _ATX_HEADING_RE.match(stripped)
            if not match:
                continue

            text = match.group(2).strip()
            if not text:
                continue

            if len(match.group(1)) == 1:
                return text
            if first_heading is None:
                first_heading = text

        return first_heading

    @staticmethod
    def read_from_file(path):
        with open(path, encoding='utf-8') as file:
            return MarkDownFile(file.read())
