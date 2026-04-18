from datetime import UTC, datetime
from pathlib import Path

import pygit2
from pygit2.enums import SortMode


class GitClient:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.repo = pygit2.Repository(repo_path)
        # repo.workdir is the absolute path to the repo root (ends with a separator)
        self.repo_root = Path(self.repo.workdir)

    def _to_repo_relative(self, path: Path) -> Path:
        """
        Normalize a path to be relative to the repository working directory.
        Works for both absolute paths and relative paths (resolved against CWD).
        """
        resolved = path if path.is_absolute() else path.resolve()
        return resolved.relative_to(self.repo_root)

    def get_last_edit_time_for_files(self, file_paths: set[Path]) -> dict[Path, datetime]:
        """
        Return the last-committed timestamp for each of the given file paths.

        For each path the git history is walked in reverse-chronological order
        (topological + time sorted). The first commit that touches a file is
        considered its last-edit time. The initial (root) commit is also
        inspected so that files that were added in the root commit and never
        modified afterwards still receive a timestamp. For merge commits, the
        diff against the first parent is used.

        Uncommitted files (new, never-committed) are excluded from the walk and
        will not appear in the returned dictionary. If the repository has no
        commits, an empty dictionary is returned.

        :param file_paths: set of file paths (absolute or relative to CWD) to look up.
        :return: dict mapping each found path to its last-committed datetime (UTC).
               Paths that are uncommitted or have no history are not included.
        """
        last_edited: dict[Path, datetime] = {}

        if not file_paths:
            return last_edited

        # Map repo-relative path -> original caller path so we can return
        # results keyed by the same paths the caller passed in.
        relative_to_original: dict[Path, Path] = {
            self._to_repo_relative(p): p for p in file_paths
        }

        uncommitted_relative = {
            self._to_repo_relative(p)
            for p in self._identify_uncommitted_files(file_paths)
        }
        to_find = set(relative_to_original.keys()) - uncommitted_relative

        if not to_find:
            return last_edited

        try:
            head_target = self.repo.head.target
        except pygit2.GitError:
            # Unborn HEAD / empty repository: nothing to walk.
            return last_edited

        walker = self.repo.walk(head_target, SortMode.TOPOLOGICAL | SortMode.TIME)

        for commit in walker:
            if not to_find:
                break

            if commit.parents:
                # For merge commits we only diff against the first parent, which
                # mirrors the behavior of `git log` without `-m`.
                parent = commit.parents[0]
                diff = self.repo.diff(parent, commit)
            else:
                # Root commit: diff the tree against an empty tree so that files
                # introduced in the initial commit are also picked up.
                diff = commit.tree.diff_to_tree(swap=True)

            commit_time = datetime.fromtimestamp(commit.commit_time, UTC)

            for patch in diff:
                delta = patch.delta
                new_path = delta.new_file.path
                if not isinstance(new_path, str) or not new_path:
                    continue
                file_path = Path(new_path)
                if file_path in to_find:
                    original_path = relative_to_original[file_path]
                    last_edited[original_path] = commit_time
                    to_find.remove(file_path)

        return last_edited

    def _identify_uncommitted_files(self, file_paths: set[Path]):
        """
        Return the subset of file paths that have never been committed to the repository.

        A file is considered uncommitted if its git status is either:
        - GIT_STATUS_WT_NEW:    present in the working tree but not staged.
        - GIT_STATUS_INDEX_NEW: staged in the index but not yet committed.

        Files that are not tracked at all by git (absent from the status dict) are
        not treated as uncommitted here — they are simply ignored.

        :param file_paths: set of file paths (absolute or relative to CWD) to check.
        :return: subset of file_paths whose files have never been committed.
        """
        status = self.repo.status()

        # Bitwise OR the flags into a single mask. Using sum() happens to work
        # only because these particular flags do not overlap, but bitwise OR
        # is the semantically correct way to combine bitmask flags.
        uncommitted_mask = (
            pygit2.GIT_STATUS_WT_NEW       # New files in working tree
            | pygit2.GIT_STATUS_INDEX_NEW  # New files in index (staged but not committed)
        )

        uncommitted_files = set()

        for file_path in file_paths:
            # Normalize to repo-relative so it matches pygit2 status() keys
            repo_relative_str = self._to_repo_relative(file_path).as_posix()
            if status.get(repo_relative_str, 0) & uncommitted_mask:
                uncommitted_files.add(file_path)

        return uncommitted_files

