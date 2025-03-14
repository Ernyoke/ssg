import os
import pprint
from datetime import datetime, UTC
from pathlib import Path

import git.git
from config import Config
from fileprocessor.markdown_file_processor import MarkdownFileProcessor


class SSG:
    """
    SSG (Static Site Generate) runner class.

    Usage:
    ssg = SSG(config)
    ssg.run()
    """
    frames_cache = dict()

    def __init__(self, config: Config):
        self.config = config

    def run(self) -> None:
        """
        Entry point. Generate a new static site project by traversing the source directory and transforming Markdown files
        into HTML.
        :return: None
        """
        self._traverse_directory()

    def _traverse_directory(self) -> None:
        """
        Traverse source directory. Transform markdown (.md) files into HTML files. Render this files into the source
        directory. Copy other non-excluded files into source_directory.
        :return: None
        """
        last_edited_times = self._traverse_and_get_last_edited_timestamps()

        frames_to_exclude = set([frame.frame for frame in self.config.frames])
        print(f'Frames to exclude: {pprint.pformat(frames_to_exclude)}')

        for current_directory, sub_directories, file_list in os.walk(self.config.source):
            current_directory = Path(current_directory)

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

            for file_name in filter(lambda name: name not in self.config.exclude, file_list) and filter(
                    lambda name: current_directory / Path(name) not in frames_to_exclude, file_list):
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
        Traverse source directory and get last edited timestamps for markdown (.md) files.
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
