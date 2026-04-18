import tempfile
from pathlib import Path
from unittest import TestCase

from ssg.dirtree.create_directory_tree import create_directory_tree

class TestCreateDirectoryTreeBase(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.source_dir = Path(self.temp_dir.name) / "source"
        self.source_dir.mkdir()

    def _write_file(self, relative_path: Path | str, content: str) -> Path:
        relative_path = Path(relative_path)
        path = self.source_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def _mkdir(self, relative_path: Path | str) -> Path:
        path = self.source_dir / Path(relative_path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _all_paths(tree) -> set[Path]:
        return {node.path for node in tree.traverse()}


class TestCreateDirectoryTreeBasics(TestCreateDirectoryTreeBase):
    def test_create_directory_tree_returns_root_with_empty_path(self):
        """The root node returned must be a DirectoryNode whose path is empty (relative to source)."""
        tree = create_directory_tree(self.source_dir)
        self.assertEqual(tree.path, Path(""))

    def test_create_directory_tree_empty_source(self):
        """An empty source directory yields a root with no files and no subdirectories."""
        tree = create_directory_tree(self.source_dir)
        self.assertEqual(tree.files, [])
        self.assertEqual(tree.directories, [])

    def test_create_directory_tree_includes_top_level_files(self):
        """Files at the root of the source directory are added as FileNodes with relative paths."""
        self._write_file("a.md", "a")
        self._write_file("b.txt", "b")

        tree = create_directory_tree(self.source_dir)

        file_paths = {f.path for f in tree.files}
        self.assertEqual(file_paths, {Path("a.md"), Path("b.txt")})

    def test_create_directory_tree_includes_subdirectories(self):
        """Subdirectories are added as DirectoryNodes with paths relative to source."""
        self._mkdir("dir1")
        self._mkdir("dir2")

        tree = create_directory_tree(self.source_dir)

        dir_paths = {d.path for d in tree.directories}
        self.assertEqual(dir_paths, {Path("dir1"), Path("dir2")})

    def test_create_directory_tree_traverses_nested_directories(self):
        """Nested directories and their files appear in traversal with correct relative paths."""
        self._write_file("dir1/dir3/deep.md", "# Deep")

        tree = create_directory_tree(self.source_dir)

        all_paths = self._all_paths(tree)
        self.assertIn(Path("dir1"), all_paths)
        self.assertIn(Path("dir1/dir3"), all_paths)
        self.assertIn(Path("dir1/dir3/deep.md"), all_paths)

    def test_create_directory_tree_no_exclude_includes_everything(self):
        """Without any exclude patterns, every file and directory is present in the tree."""
        self._write_file("a.md", "a")
        self._write_file("sub/b.md", "b")

        tree = create_directory_tree(self.source_dir)

        all_paths = self._all_paths(tree)
        self.assertIn(Path("a.md"), all_paths)
        self.assertIn(Path("sub"), all_paths)
        self.assertIn(Path("sub/b.md"), all_paths)


class TestCreateDirectoryTreeExclusions(TestCreateDirectoryTreeBase):
    def test_create_directory_tree_excludes_directory_by_name(self):
        """Directories whose name matches an exclude pattern are skipped entirely."""
        self._write_file("ignored/inside.md", "# Inside")
        self._mkdir("kept")

        tree = create_directory_tree(self.source_dir, exclude=frozenset(["ignored"]))

        all_paths = self._all_paths(tree)
        self.assertNotIn(Path("ignored"), all_paths)
        self.assertNotIn(Path("ignored/inside.md"), all_paths)
        self.assertIn(Path("kept"), all_paths)

    def test_create_directory_tree_excludes_file_by_glob(self):
        """Files matching a glob exclude pattern are not added, even in nested directories."""
        self._write_file("dir1/dir3/secret.md", "# Secret")
        self._write_file("dir1/dir3/public.md", "# Public")

        tree = create_directory_tree(self.source_dir, exclude=frozenset(["**/secret.*"]))

        all_paths = self._all_paths(tree)
        self.assertNotIn(Path("dir1/dir3/secret.md"), all_paths)
        self.assertIn(Path("dir1/dir3/public.md"), all_paths)

    def test_create_directory_tree_excludes_file_by_name_pattern(self):
        """A simple filename pattern excludes matching files at any depth."""
        self._write_file("keep.md", "k")
        self._write_file("drop.tmp", "d")
        self._write_file("sub/also.tmp", "d")

        tree = create_directory_tree(self.source_dir, exclude=frozenset(["*.tmp"]))

        all_paths = self._all_paths(tree)
        self.assertIn(Path("keep.md"), all_paths)
        self.assertNotIn(Path("drop.tmp"), all_paths)
        self.assertNotIn(Path("sub/also.tmp"), all_paths)

    def test_create_directory_tree_combined_exclusions(self):
        """Multiple exclude patterns (directory name + file glob) all apply simultaneously."""
        self._write_file("ignored/x.md", "x")
        self._write_file("dir1/dir3/secret.md", "# Secret")
        self._write_file("dir1/dir3/visible.md", "# Visible")
        self._mkdir("dir2")

        tree = create_directory_tree(
            self.source_dir, exclude=frozenset(["ignored", "**/secret.*"])
        )

        all_paths = self._all_paths(tree)
        self.assertIn(Path("dir1"), all_paths)
        self.assertIn(Path("dir2"), all_paths)
        self.assertIn(Path("dir1/dir3"), all_paths)
        self.assertIn(Path("dir1/dir3/visible.md"), all_paths)
        self.assertNotIn(Path("ignored"), all_paths)
        self.assertNotIn(Path("dir1/dir3/secret.md"), all_paths)


class TestCreateDirectoryTreeRelationships(TestCreateDirectoryTreeBase):
    def test_create_directory_tree_file_nodes_have_parent_reference(self):
        """FileNodes are attached to their parent DirectoryNode."""
        self._write_file("sub/child.md", "c")

        tree = create_directory_tree(self.source_dir)

        sub_node = next(d for d in tree.directories if d.path == Path("sub"))
        self.assertEqual(len(sub_node.files), 1)
        self.assertEqual(sub_node.files[0].path, Path("sub/child.md"))
        self.assertIs(sub_node.files[0].parent, sub_node)
