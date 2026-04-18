from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ssg.dirtree.node import Node

if TYPE_CHECKING:
    from ssg.dirtree.directory_node import DirectoryNode


class FileNode(Node):
    """Represents a file in the source directory, along with its metadata."""

    def __init__(self, path: Path, parent: Optional['DirectoryNode'] = None):
        super().__init__(path)
        self.name: str = path.stem
        self.name_with_extension: str = path.name
        self.parent = parent

    def is_markdown(self):
        return self.path.suffix == '.md'