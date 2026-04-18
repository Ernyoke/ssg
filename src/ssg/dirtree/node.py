from pathlib import Path
from enum import auto, IntFlag


class NodeType(IntFlag):
    FILE = auto()
    DIR = auto()
    ALL = FILE | DIR

class Node:
    def __init__(self, path: Path):
        self.path = path