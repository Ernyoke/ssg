import fnmatch
import os
import shutil
from datetime import datetime
from pathlib import Path

from ssg.dirtree.create_directory_tree import create_directory_tree
from ssg.engine.meta import get_meta
from ssg.git import git
from ssg.config import Config
from ssg.content.article import Article
from ssg.dirtree.directory_node import DirectoryNode, FileNode
from ssg.dirtree.node import NodeType
from ssg.content.frame import Frame
from ssg.content.html_file import HTMLFile
from ssg.content.markdown_file import MarkDownFile


class Engine:
    """

    Usage:
    engine = Engine()
    engine.run(config)
    """

    def __init__(self):
        self.frames_cache = dict()

    def run(self, config: Config) -> None:
        """
        Entry point. Generate a new static site project by traversing the source directory and transforming Markdown files
        into HTML.
        :return: None
        """
        root = create_directory_tree(config.source, frozenset(config.exclude))
        last_edited = get_last_edited_for_markdown_files(root, config.source)
        root.mk_dir_tree(config.destination)
        frames_to_exclude = set(frame.frame for frame in config.frames)

        for file in root.traverse(NodeType.FILE):
            if file.is_markdown():
                resolved = get_meta(file, config.meta, config.base_href)
                markdown = MarkDownFile.read_from_file(config.source / file.path)
                article = Article(
                    markdown_file=markdown,
                    title=resolved.title if resolved.title is not None else markdown.get_title(),
                    description=resolved.description,
                    cover_image=resolved.cover_image,
                    url=resolved.url,
                    last_edited=last_edited.get(config.source / file.path),
                    twitter_handle=resolved.twitter_handle
                )
                frame = self._get_frame(file, config)
                html_file = HTMLFile.from_article(article,
                                                  frame,
                                                  base_href=config.base_href,
                                                  hostname=config.hostname)
                destination_path = config.destination / file.path.parent / Path(f'{file.name}.html')
                html_file.write(destination_path)
                print(f'Created {destination_path.as_posix()}')
            else:
                if file.path not in frames_to_exclude:
                    shutil.copyfile(config.source / file.path, config.destination / file.path)
                    print(f'Copied {(config.destination / file.path).as_posix()}')

    def _get_frame(self, file: FileNode, config: Config) -> Frame:
        frame_path = None
        for f in config.frames:
            if fnmatch.fnmatch(file.path.as_posix(), f.file):
                frame_path = f.frame
                break

        if not frame_path:
            raise AssertionError(f'No frame found for {file.path.as_posix()}')

        if frame_path in self.frames_cache:
            return self.frames_cache[frame_path]

        frame = Frame.read_from_file(config.source / frame_path)
        frame.set_base_path(config.base_href)
        self.frames_cache[frame_path] = frame
        return self.frames_cache[frame_path]


def get_last_edited_for_markdown_files(root: DirectoryNode, source_dir: Path) -> dict[Path, datetime]:
    git_client = git.GitClient(source_dir)

    markdown_file_paths = {
        source_dir / file.path for file in root.traverse(NodeType.FILE) if file.is_markdown()
    }
    return git_client.get_last_edit_time_for_files(markdown_file_paths)  # bytes preserved
