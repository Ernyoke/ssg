import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from ssg.content.article import Author
from ssg.rss.rss_feed_generator import RssFeedGenerator
from ssg.dirtree.create_directory_tree import create_directory_tree
from ssg.git import git
from ssg.config import Config
from ssg.content.article import Article
from ssg.dirtree.directory_node import DirectoryNode, FileNode
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
                markdown = MarkDownFile.read_from_file(self.config.source / file.path)
                url_computed = urljoin(self.config.baseHref, file.path.with_suffix('.html').as_posix())
                article = Article(
                    markdown=markdown,
                    title=markdown.get_title(),
                    description=markdown.get_summary(),
                    cover_image=compute_cover_image_path(markdown, file, self.config.baseHref),
                    url=urljoin(self.config.baseHref, url_computed),
                    last_edited=last_edited.get(self.config.source / file.path),
                    publish_date=markdown.get_publish_date(),
                    author=Author(
                        name=markdown.get_author(),
                        email=markdown.get_email(),
                        twitter_handle=markdown.get_twitter_handle(),
                        github_handle=markdown.get_github_handle()
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

def compute_cover_image_path(markdown: MarkDownFile, file: FileNode, base_href: str):
    cover_image = markdown.get_cover_image()
    cover_image_computed = None
    if cover_image is not None and file.parent is not None:
        cover_image_path = file.parent.path / cover_image
        cover_image_path.resolve()
        cover_image_computed = urljoin(base_href, cover_image_path.as_posix())

    return cover_image_computed
