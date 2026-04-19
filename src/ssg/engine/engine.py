import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from ssg.content.article import Author
from ssg.rss.rss_feed_generator import RssFeedGenerator
from ssg.dirtree.create_directory_tree import create_directory_tree
from ssg.engine.meta import get_meta
from ssg.git import git
from ssg.config import Config
from ssg.content.article import Article
from ssg.dirtree.directory_node import DirectoryNode
from ssg.dirtree.node import NodeType
from ssg.content.markdown_file import MarkDownFile
from ssg.template.template_engine import TemplateEngine


class Engine:
    """

    Usage:
    engine = Engine(config)
    engine.run()
    """

    def __init__(self, config: Config):
        self.config = config
        self.template_engine = TemplateEngine(config)
        self.rssFeedGenerator = RssFeedGenerator(config.rssFeeds)

    def run(self) -> None:
        """
        Entry point. Generate a new static site project by traversing the source directory and transforming Markdown files
        into HTML.
        :return: None
        """
        root = create_directory_tree(self.config.source, frozenset(self.config.exclude))
        root.mk_dir_tree(self.config.destination)

        last_edited = get_last_edited_for_markdown_files(root, self.config.source)

        for file in root.traverse(NodeType.FILE):
            if file.is_markdown():
                resolved = get_meta(file, self.config.meta, self.config.baseHref)
                markdown = MarkDownFile.read_from_file(self.config.source / file.path)
                cover_image_path = resolved.cover_image.as_posix() if resolved.cover_image else None
                cover_image = urljoin(self.config.baseHref, cover_image_path) if cover_image_path else None
                article = Article(
                    markdown=markdown,
                    title=resolved.title if resolved.title is not None else markdown.get_title(),
                    description=resolved.description,
                    cover_image=cover_image,
                    url=resolved.url,
                    last_edited=last_edited.get(self.config.source / file.path),
                    author=Author(
                        name=resolved.author,
                        email=resolved.author_email,
                        twitter_handle=resolved.twitter_handle
                    )
                )
                self.rssFeedGenerator.add_to_feed(file, article)
                destination_path = self.config.destination / file.path.parent / Path(f'{file.name}.html')
                self.template_engine.render(file, article, destination_path)
                print(f'Created {destination_path.as_posix()}')
            else:
                if file.path not in frozenset(frame.frame for frame in self.config.frames):
                    shutil.copyfile(self.config.source / file.path, self.config.destination / file.path)
                    print(f'Copied {(self.config.destination / file.path).as_posix()}')

        self.rssFeedGenerator.generate_feeds(self.config.destination)


def get_last_edited_for_markdown_files(root: DirectoryNode, source_dir: Path) -> dict[Path, datetime]:
    git_client = git.GitClient(source_dir)

    markdown_file_paths = {
        source_dir / file.path for file in root.traverse(NodeType.FILE) if file.is_markdown()
    }
    return git_client.get_last_edit_time_for_files(markdown_file_paths)
