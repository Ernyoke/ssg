import fnmatch
import os
from pathlib import Path

from ssg.dirtree.directory_node import DirectoryNode
from ssg.dirtree.file_node import FileNode

def create_directory_tree(path: Path,
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
                current_node.add_file(FileNode(relative, current_node))

        for sub_directory in sub_directories:
            dir_path = Path(current_dir_path) / sub_directory
            relative = dir_path.relative_to(path)
            node = DirectoryNode(relative)
            dir_nodes[dir_path] = node
            current_node.add_directory(node)
    return root