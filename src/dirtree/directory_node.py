from pathlib import Path
from typing import Callable, TypeVar, overload, Literal, Iterator

from dirtree.file_node import FileNode
from dirtree.node import Node, NodeType

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

    def traverse_and_filter_files(self, predicate: Callable[['FileNode'], bool]):
        content = []

        def dfs(current_node):
            if current_node is not None:
                for file in current_node.files:
                    if predicate(file):
                        content.append(file)
                for directory in current_node.directories:
                    dfs(directory)

        dfs(self)
        return content

    def traverse_and_apply_to_each_dir(self, function: Callable[['DirectoryNode'], None]):
        def dfs(current_node):
            if current_node is not None:
                for directory in current_node.directories:
                    function(directory)
                    dfs(directory)

        dfs(self)

