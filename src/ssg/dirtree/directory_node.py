from pathlib import Path
from typing import TypeVar, overload, Literal, Iterator

from ssg.dirtree.file_node import FileNode
from ssg.dirtree.node import Node, NodeType

T = TypeVar('T', bound=NodeType)

class DirectoryNode(Node):
    def __init__(self, path: Path):
        super().__init__(path)
        self.directories: list[DirectoryNode] = []
        self.files: list[FileNode] = []

    def add_directory(self, child: 'DirectoryNode'):
        self.directories.append(child)

    def add_file(self, file: 'FileNode'):
        self.files.append(file)

    @overload
    def traverse(self, select_filter: Literal[NodeType.FILE]) -> Iterator[FileNode]:
        ...

    @overload
    def traverse(self, select_filter: Literal[NodeType.DIR]) -> Iterator['DirectoryNode']:
        ...

    @overload
    def traverse(self, select_filter: Literal[NodeType.ALL] = NodeType.ALL) -> Iterator[Node]:
        ...

    def traverse(self, select_filter: NodeType = NodeType.ALL) -> Iterator['Node']:
        if select_filter & NodeType.DIR:
            yield self

        def dfs(current_node):
            if current_node is not None:
                if select_filter & NodeType.FILE:
                    yield from current_node.files
                for directory in current_node.directories:
                    if select_filter & NodeType.DIR:
                        yield directory
                    yield from dfs(directory)

        yield from dfs(self)

    def mk_dir_tree(self, destination: Path):
        for directory in self.traverse(NodeType.DIR):
            relative_path = directory.path
            absolute_path = destination / relative_path
            absolute_path.mkdir(parents=True, exist_ok=True)

            if not absolute_path.is_dir():
                print(
                    f"Warning: Directory ${absolute_path.as_posix()} could not be created, because there is already a file having the same path!")


