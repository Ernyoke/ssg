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

    def get_last_edit_time_for_files(self, file_paths: set[Path]):
        """
        Return the last-committed timestamp for each of the given file paths.

        For each path the git history is walked in reverse-chronological order.
        The first commit that touches a file is considered its last-edit time.
        Uncommitted files (new, never-committed) are excluded from the walk and
        will not appear in the returned dictionary.

        :param file_paths: set of file paths (absolute or relative to CWD) to look up.
        :return: dict mapping each found path to its last-committed datetime (UTC).
               Paths that are uncommitted or have no history are not included.
        """
        walker = self.repo.walk(self.repo.head.target, SortMode.TIME)

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

        last_edited = {}

        for commit in walker:
            if not to_find:
                break

            if commit.parents:
                parent = commit.parents[0]
                diff = self.repo.diff(parent, commit)

                for patch in diff:
                    file_path = Path(patch.delta.new_file.path)
                    if file_path in to_find:
                        original_path = relative_to_original[file_path]
                        last_edited[original_path] = datetime.fromtimestamp(commit.commit_time, UTC)
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

        uncommitted_statuses = {
            pygit2.GIT_STATUS_WT_NEW,       # New files in working tree
            pygit2.GIT_STATUS_INDEX_NEW     # New files in index (staged but not committed)
        }

        uncommitted_files = set()

        for file_path in file_paths:
            # Normalize to repo-relative so it matches pygit2 status() keys
            repo_relative_str = self._to_repo_relative(file_path).as_posix()
            if repo_relative_str in status and status[repo_relative_str] & sum(uncommitted_statuses):
                uncommitted_files.add(file_path)

        return uncommitted_files

