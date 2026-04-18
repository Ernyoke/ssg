import fnmatch
import glob
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

from ssg.git import git
from ssg.config import Config, Meta
from ssg.content.article import Article
from ssg.dirtree.directory_node import DirectoryNode, FileNode
from ssg.dirtree.node import NodeType
from ssg.content.frame import Frame
from ssg.content.html_file import HTMLFile
from ssg.content.markdown_file import MarkDownFile


@dataclass(frozen=True)
class ResolvedMeta:
    """Resolved per-article metadata produced by ``Engine._get_meta``."""
    title: str | None = None
    cover_image: Path | None = None
    url: str | None = None
    twitter_handle: str | None = None


class Engine:
    """
    SSG (Static Site Generate) engine class.

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
        root = Engine._create_directory_tree(config.source, frozenset(config.exclude))

        last_edited = Engine._get_last_edited_for_markdown_files(root, config.source)

        root.mk_dir_tree(config.destination)

        frames_to_exclude = set(frame.frame for frame in config.frames)

        for file in root.traverse(NodeType.FILE):
            if file.is_markdown():
                resolved = Engine._get_meta(file, config.meta, config.base_href, config.source)
                markdown = MarkDownFile.read_from_file(config.source / file.path)
                article = Article(
                    markdown_file=markdown,
                    title=resolved.title if resolved.title is not None else markdown.get_title(),
                    cover_image=resolved.cover_image,
                    url=resolved.url,
                    last_edited=last_edited.get(config.source / file.path),
                    twitter_handle=resolved.twitter_handle
                )
                frame = self._get_frame(file, config)
                html_file = HTMLFile.from_article(article, frame, base_href=config.base_href)
                destination_path = config.destination / file.path.parent / Path(f'{file.name}.html')
                html_file.write(destination_path)
                print(f'Created {destination_path.as_posix()}')
            else:
                if file.path not in frames_to_exclude:
                    Engine._copy_file(config.source / file.path, config.destination / file.path)
                    print(f'Copied {(config.destination / file.path).as_posix()}')

    @staticmethod
    def _create_directory_tree(path: Path,
                               exclude: frozenset[str] = frozenset()) -> DirectoryNode:
        root = DirectoryNode(Path(''))
        dir_nodes = {path: root}
        for current_dir_path, sub_directories, file_names in os.walk(path):
            # Exclude directories whose name or relative path matches any pattern
            sub_directories[:] = [
                d for d in sub_directories
                if not any(
                    fnmatch.fnmatch(d, pattern) or
                    fnmatch.fnmatch(
                        (Path(current_dir_path) / d).relative_to(path).as_posix(),
                        pattern
                    )
                    for pattern in exclude
                )
            ]

            # Retrieve current node from the cache. This should have been populated before we reach this point
            # because we add all the subdirectories for a parent directory
            current_node = dir_nodes[Path(current_dir_path)]

            for file_name in file_names:
                file_path = Path(current_dir_path) / file_name
                relative = file_path.relative_to(path)
                if not any(
                        fnmatch.fnmatch(file_name, pattern) or
                        fnmatch.fnmatch(relative.as_posix(), pattern)
                        for pattern in exclude
                ):
                    current_node.add_file(FileNode(relative))

            for sub_directory in sub_directories:
                dir_path = Path(current_dir_path) / sub_directory
                relative = dir_path.relative_to(path)
                node = DirectoryNode(relative)
                dir_nodes[dir_path] = node
                current_node.add_directory(node)
        return root

    @staticmethod
    def _get_last_edited_for_markdown_files(root: DirectoryNode, source_dir: Path) -> dict[Path, datetime]:
        git_client = git.GitClient(source_dir)

        markdown_file_paths = {
            source_dir / file.path for file in root.traverse(NodeType.FILE) if file.is_markdown()
        }
        return git_client.get_last_edit_time_for_files(markdown_file_paths)

    @staticmethod
    def _get_meta(file: FileNode, meta: Meta|None, base_href: str, source: Path) -> ResolvedMeta:
        if meta is None:
            return ResolvedMeta()

        twitter_handle = meta.default.twitter_handle
        for matcher in meta.matchers:
            if not fnmatch.fnmatch(file.path.as_posix(), matcher.file):
                continue

            if matcher.action == 'TAKE_FROM_CONTENT':
                return ResolvedMeta(
                    cover_image=Engine._get_cover_image(file, source),
                    url=urljoin(base_href, f'{file.name}.html'),
                    twitter_handle=twitter_handle,
                )

            if matcher.action == 'STATIC':
                title: str | None = None
                cover_image: Path | None = None
                url = meta.default.url
                if matcher.meta_fields is not None:
                    if matcher.meta_fields.title is not None:
                        title = matcher.meta_fields.title
                    if matcher.meta_fields.image is not None:
                        cover_image = Path(matcher.meta_fields.image)
                    if matcher.meta_fields.url is not None:
                        url = matcher.meta_fields.url
                    if matcher.meta_fields.twitter_handle is not None:
                        twitter_handle = matcher.meta_fields.twitter_handle
                return ResolvedMeta(
                    title=title,
                    cover_image=cover_image,
                    url=url,
                    twitter_handle=twitter_handle,
                )

            if matcher.action == 'USE_DEFAULT':
                image = Path(meta.default.image) if meta.default.image is not None else None
                return ResolvedMeta(
                    title=meta.default.title,
                    cover_image=image,
                    url=meta.default.url,
                    twitter_handle=meta.default.twitter_handle,
                )

        return ResolvedMeta(twitter_handle=twitter_handle)

    @staticmethod
    def _get_cover_image(file: FileNode, source: Path) -> Optional[Path]:
        """
        Returns the path of the cover image if it exists.
        :return: relative path to the cover image if it exists
        """
        accepted_image_extensions = ('.tif', '.tiff', '.jpg', '.jpeg', '.gif', '.png', '.eps', ".bmp", '.ppm',
                                     '.heif',
                                     '.avif')
        img_folder_path = source / Path(f'img-{file.name}')
        pattern = img_folder_path / Path('cover.*')
        files = glob.glob(pattern.as_posix())
        covers = []
        for f in files:
            for extension in accepted_image_extensions:
                if f.endswith(extension):
                    covers.append(Path(f).name)

        if len(covers) == 0:
            return None

        if len(covers) > 1:
            print(f'Warning! Multiple cover images found for {file.path}! Choosing {covers[0]}')

        return Path(f'img-{file.name}') / Path(covers[0])

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

    @staticmethod
    def _copy_file(source_path: Path, destination_path: Path) -> None:
        """
        Copy a file from the source location to a target location.
        :param source_path: source location
        :param destination_path: target location
        :return: None
        """
        with open(source_path, 'rb') as source:
            with open(destination_path, 'wb') as destination:
                destination.write(source.read())
