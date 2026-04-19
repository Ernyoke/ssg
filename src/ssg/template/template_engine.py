"""Template selection and HTML rendering for generated site content."""

import fnmatch
from pathlib import Path

from ssg.config import Config
from ssg.content.article import Article
from ssg.dirtree.file_node import FileNode
from ssg.template import Template
from ssg.template.html_file import HTMLFile


class TemplateEngine:
    """
    Resolve frames for source files and reuse parsed templates while rendering articles.
    """

    def __init__(self, config: Config):
        """
        Create a template engine bound to the site configuration.
        :param config: Site configuration containing frame mappings and output settings.
        """
        self.cache = {}
        self.config = config

    def get_template(self, file: FileNode) -> Template:
        """
        Return the template that matches the given file path.

        The first matching frame pattern from ``config.frames`` is used. Parsed templates are cached by their
        frame path so repeated renders do not reload the same file.

        :param file: Source file whose path is matched against configured frame patterns.
        :return: Parsed template for the matching frame.
        :raises AssertionError: If no configured frame matches the file path.
        """
        template_path = None
        for f in self.config.frames:
            if fnmatch.fnmatch(file.path.as_posix(), f.file):
                template_path = f.frame
                break

        if not template_path:
            raise AssertionError(f'No frame found for {file.path.as_posix()}')

        if template_path in self.cache:
            return self.cache[template_path]

        template = Template.read_from_file(self.config.source / template_path)
        template.set_base_path(self.config.baseHref)
        self.cache[template_path] = template
        return self.cache[template_path]

    def render(self, file: FileNode, article: Article, destination_path: Path):
        """
        Render an article into an HTML file using the template selected for the source file.

        :param file: Source file used to choose the template.
        :param article: Article content and metadata to inject into the selected template.
        :param destination_path: Output path for the rendered HTML file.
        """
        template = self.get_template(file)
        html_file = HTMLFile.from_article(article,
                                          template,
                                          base_href=self.config.baseHref,
                                          hostname=self.config.hostname)
        html_file.write(destination_path)
