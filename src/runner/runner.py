import fnmatch
import glob
import os
import pprint
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import git.git
from config import Config, Meta
from content.article import Article
from dirtree.directory_node import DirectoryNode, FileNode
from dirtree.node import NodeType
from fileprocessor.frame import Frame
from fileprocessor.html_file import HTMLFile
from fileprocessor.markdown_file import MarkDownFile
from fileprocessor.markdown_file_processor import MarkdownFileProcessor


class SSG:
    """
    SSG (Static Site Generate) runner class.

    Usage:
    ssg = SSG(config)
    ssg.run()
    """

    def __init__(self, config: Config):
        self.config = config
        self.frames_cache = dict()

    def run(self) -> None:
        """
        Entry point. Generate a new static site project by traversing the source directory and transforming Markdown files
        into HTML.
        :return: None
        """
        # self._traverse_directory()

        root = SSG._create_directory_tree(self.config.source, frozenset(self.config.exclude))

        last_edited = SSG._get_last_edited_for_markdown_files(root)

        def mkdir(directory: DirectoryNode):
            relative_path = directory.path
            absolute_path = self.config.destination / relative_path
            absolute_path.mkdir(parents=False, exist_ok=True)

            if not absolute_path.is_dir():
                print(
                    f"Warning: Directory ${absolute_path.as_posix()} could not be created, because there is already a file having the same path!")

        root.traverse_and_apply_to_each_dir(mkdir)

        frames_to_exclude = set(frame.frame for frame in self.config.frames)

        for file in root.traverse(NodeType.FILE):
            if file.is_markdown():
                title, cover_image, url = SSG._get_meta(file, self.config.meta, self.config.base_href)
                markdown = MarkDownFile.read_from_file(self.config.source / file.path)
                article = Article(
                    markdown_file=markdown,
                    title=title if title is not None else markdown.get_title(),
                    cover_image=cover_image,
                    url=url,
                    last_edited=last_edited.get(file.path)
                )
                frame = self._get_frame(file, self.config.source)
                html_file = HTMLFile.from_article(article, frame, base_href=self.config.base_href)
                destination_path = self.config.destination / file.path.parent / Path(f'{file.name}.html')
                html_file.write(destination_path)
            else:
                if file.path not in frames_to_exclude:
                    SSG._copy_file(self.config.source / file.path, self.config.destination / file.path)

    @staticmethod
    def _create_directory_tree(path: Path,
                               exclude: frozenset[str] = frozenset()) -> DirectoryNode:
        root = DirectoryNode(path)
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
                node = DirectoryNode(dir_path)
                dir_nodes[dir_path] = node
                current_node.add_directory(node)
        return root

    @staticmethod
    def _get_last_edited_for_markdown_files(root: DirectoryNode):
        git_client = git.GitClient(root.path)

        markdown_file_paths = {
            file.path for file in root.traverse(NodeType.FILE) if file.is_markdown()
        }
        return git_client.get_last_edit_time_for_files(markdown_file_paths)

    @staticmethod
    def _get_meta(file: FileNode, meta: Meta|None, base_href: str) -> tuple[str|None, Path|None, str|None]:
        title, cover_image, url = None, None, None
        if meta:
            for matcher in meta.matchers:
                if fnmatch.fnmatch(file.path.as_posix(), matcher.file):
                    if matcher.action == 'TAKE_FROM_CONTENT':
                        cover_image = SSG._get_cover_image(file)
                        url = urljoin(base_href, f'{file.name}.html')
                        return title, cover_image, url

                    elif matcher.action == 'STATIC':
                        if matcher.meta_fields is not None and matcher.meta_fields.title is not None:
                            title = matcher.meta_fields.title
                        if matcher.meta_fields is not None and matcher.meta_fields.image is not None:
                            cover_image = Path(matcher.meta_fields.image)
                        return title, cover_image, meta.default.url

        return None, None, None

    @staticmethod
    def _get_cover_image(file: FileNode) -> Optional[Path]:
        """
        Returns the path of the cover image if it exists.
        :return: relative path to the cover image if it exists
        """
        accepted_image_extensions = ('.tif', '.tiff', '.jpg', '.jpeg', '.gif', '.png', '.eps', ".bmp", '.ppm',
                                     '.heif',
                                     '.avif')
        img_folder_path = file.path.parent.absolute() / Path(f'img-{file.name}')
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

    def _get_frame(self, file: FileNode, base_path: Path):
        frame_path = None
        for f in self.config.frames:
            if fnmatch.fnmatch(file.path.as_posix(), f.file):
                frame_path = f.frame
                break

        if not frame_path:
            raise AssertionError(f'No frame found for {file.path.as_posix()}')

        if frame_path in self.frames_cache:
            return self.frames_cache[frame_path]

        frame = Frame.read_from_file(base_path / frame_path)
        frame.set_base_path(self.config.base_href)
        self.frames_cache[frame_path] = frame
        return self.frames_cache[frame_path]


    def _traverse_directory(self) -> None:
        """
        Traverse source directory. Transform Markdown (.md) files into HTML files. Render this files into the source
        directory. Copy other non-excluded files into source_directory.
        :return: None
        """
        last_edited_times = self._traverse_and_get_last_edited_timestamps()

        frames_to_exclude = set([frame.frame for frame in self.config.frames])
        print(f'Frames to exclude: {pprint.pformat(frames_to_exclude)}')

        for dir_path, sub_directories, file_list in os.walk(self.config.source):
            current_directory = Path(dir_path)

            # Filter excluded directories
            if current_directory.name in self.config.exclude:
                print(f'Excluded directory: {current_directory}')
                continue

            # Create the destination directories
            directory_to_create = self.config.destination
            relative_destination_dir = current_directory.relative_to(self.config.source)
            if current_directory != self.config.source:
                directory_to_create = self.config.destination / relative_destination_dir

            if not directory_to_create.exists():
                directory_to_create.mkdir()

            for file_name in filter(
                    lambda name: current_directory / Path(name) not in frames_to_exclude,
                    filter(lambda name: name not in self.config.exclude, file_list)
            ):
                if file_name.endswith('.md'):
                    file_path = Path(current_directory / Path(file_name))
                    md_file_processor = MarkdownFileProcessor(path=file_path,
                                                              file_name=file_name,
                                                              last_edited_time=last_edited_times.get(file_path),
                                                              destination_dir=directory_to_create,
                                                              config=self.config,
                                                              frames_cache=self.frames_cache)
                    md_file_processor.render_html(relative_destination_dir)
                else:
                    SSG._copy_file(current_directory / file_name, directory_to_create / file_name)
                    print(f'Copied {directory_to_create / file_name}')

    def _traverse_and_get_last_edited_timestamps(self):
        """
        Traverse source directory and get last edited timestamps for Markdown (.md) files.
        """
        markdown_file_paths = set()

        for current_directory, sub_directories, file_list in os.walk(self.config.source):
            current_directory = Path(current_directory)

            # Filter excluded directories
            if current_directory.name in self.config.exclude:
                print(f'Excluded directory: {current_directory}')
                continue

            for file_name in filter(lambda name: name not in self.config.exclude, file_list):
                if file_name.endswith('.md'):
                    markdown_file_paths.add(current_directory / Path(file_name))

        git_client = git.GitClient(self.config.source)
        return git_client.get_last_edit_time_for_files(markdown_file_paths)

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
