from pathlib import Path

import pytest

from ssg.dirtree.create_directory_tree import create_directory_tree

@pytest.fixture()
def source_dir(tmp_path):
    s = tmp_path / "source"
    s.mkdir()
    return s

def test_create_directory_tree_returns_root_with_empty_path(source_dir):
    """The root node returned must be a DirectoryNode whose path is empty (relative to source)."""
    tree = create_directory_tree(source_dir)
    assert tree.path == Path('')


def test_create_directory_tree_empty_source(source_dir):
    """An empty source directory yields a root with no files and no subdirectories."""
    tree = create_directory_tree(source_dir)
    assert tree.files == []
    assert tree.directories == []


def test_create_directory_tree_includes_top_level_files(source_dir):
    """Files at the root of the source directory are added as FileNodes with relative paths."""
    (source_dir / "a.md").write_text("a", encoding="utf-8")
    (source_dir / "b.txt").write_text("b", encoding="utf-8")

    tree = create_directory_tree(source_dir)

    file_paths = {f.path for f in tree.files}
    assert file_paths == {Path("a.md"), Path("b.txt")}


def test_create_directory_tree_includes_subdirectories(source_dir):
    """Subdirectories are added as DirectoryNodes with paths relative to source."""
    (source_dir / "dir1").mkdir()
    (source_dir / "dir2").mkdir()

    tree = create_directory_tree(source_dir)

    dir_paths = {d.path for d in tree.directories}
    assert dir_paths == {Path("dir1"), Path("dir2")}


def test_create_directory_tree_traverses_nested_directories(source_dir):
    """Nested directories and their files appear in traversal with correct relative paths."""
    nested = source_dir / "dir1" / "dir3"
    nested.mkdir(parents=True)
    (nested / "deep.md").write_text("# Deep", encoding="utf-8")

    tree = create_directory_tree(source_dir)

    all_paths = {node.path for node in tree.traverse()}
    assert Path("dir1") in all_paths
    assert Path("dir1/dir3") in all_paths
    assert Path("dir1/dir3/deep.md") in all_paths


def test_create_directory_tree_excludes_directory_by_name(source_dir):
    """Directories whose name matches an exclude pattern are skipped entirely."""
    ignored = source_dir / "ignored"
    ignored.mkdir()
    (ignored / "inside.md").write_text("# Inside", encoding="utf-8")
    (source_dir / "kept").mkdir()

    tree = create_directory_tree(source_dir, exclude=frozenset(["ignored"]))

    all_paths = {node.path for node in tree.traverse()}
    assert Path("ignored") not in all_paths
    assert Path("ignored/inside.md") not in all_paths
    assert Path("kept") in all_paths


def test_create_directory_tree_excludes_file_by_glob(source_dir):
    """Files matching a glob exclude pattern are not added, even in nested directories."""
    nested = source_dir / "dir1" / "dir3"
    nested.mkdir(parents=True)
    (nested / "secret.md").write_text("# Secret", encoding="utf-8")
    (nested / "public.md").write_text("# Public", encoding="utf-8")

    tree = create_directory_tree(source_dir, exclude=frozenset(["**/secret.*"]))

    all_paths = {node.path for node in tree.traverse()}
    assert Path("dir1/dir3/secret.md") not in all_paths
    assert Path("dir1/dir3/public.md") in all_paths


def test_create_directory_tree_excludes_file_by_name_pattern(source_dir):
    """A simple filename pattern excludes matching files at any depth."""
    (source_dir / "keep.md").write_text("k", encoding="utf-8")
    (source_dir / "drop.tmp").write_text("d", encoding="utf-8")
    sub = source_dir / "sub"
    sub.mkdir()
    (sub / "also.tmp").write_text("d", encoding="utf-8")

    tree = create_directory_tree(source_dir, exclude=frozenset(["*.tmp"]))

    all_paths = {node.path for node in tree.traverse()}
    assert Path("keep.md") in all_paths
    assert Path("drop.tmp") not in all_paths
    assert Path("sub/also.tmp") not in all_paths


def test_create_directory_tree_no_exclude_includes_everything(source_dir):
    """Without any exclude patterns, every file and directory is present in the tree."""
    (source_dir / "a.md").write_text("a", encoding="utf-8")
    sub = source_dir / "sub"
    sub.mkdir()
    (sub / "b.md").write_text("b", encoding="utf-8")

    tree = create_directory_tree(source_dir)

    all_paths = {node.path for node in tree.traverse()}
    assert Path("a.md") in all_paths
    assert Path("sub") in all_paths
    assert Path("sub/b.md") in all_paths


def test_create_directory_tree_combined_exclusions(source_dir):
    """Multiple exclude patterns (directory name + file glob) all apply simultaneously."""
    ignored = source_dir / "ignored"
    ignored.mkdir()
    (ignored / "x.md").write_text("x", encoding="utf-8")

    dir1 = source_dir / "dir1"
    dir3 = dir1 / "dir3"
    dir3.mkdir(parents=True)
    (dir3 / "secret.md").write_text("# Secret", encoding="utf-8")
    (dir3 / "visible.md").write_text("# Visible", encoding="utf-8")
    (source_dir / "dir2").mkdir()

    tree = create_directory_tree(
        source_dir, exclude=frozenset(["ignored", "**/secret.*"])
    )

    all_paths = {node.path for node in tree.traverse()}
    assert Path("dir1") in all_paths
    assert Path("dir2") in all_paths
    assert Path("dir1/dir3") in all_paths
    assert Path("dir1/dir3/visible.md") in all_paths
    assert Path("ignored") not in all_paths
    assert Path("dir1/dir3/secret.md") not in all_paths


def test_create_directory_tree_file_nodes_have_parent_reference(source_dir):
    """FileNodes are attached to their parent DirectoryNode."""
    sub = source_dir / "sub"
    sub.mkdir()
    (sub / "child.md").write_text("c", encoding="utf-8")

    tree = create_directory_tree(source_dir)

    sub_node = next(d for d in tree.directories if d.path == Path("sub"))
    assert len(sub_node.files) == 1
    assert sub_node.files[0].path == Path("sub/child.md")