from pathlib import Path

from dirtree.node import Node


class FileNode(Node):
    """Represents a file in the source directory, along with its metadata."""

    def __init__(self, path: Path):
        super().__init__(path)
        self.name: str = path.stem

    def is_markdown(self):
        return self.path.suffix == '.md'