from datetime import UTC, datetime
from pathlib import Path

import pygit2


class GitClient:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.repo = pygit2.Repository(repo_path)

    def get_last_edit_time_for_files(self, file_paths: set[Path]):
        walker = self.repo.walk(self.repo.head.target, pygit2.GIT_SORT_TIME)

        last_edited = {}
        to_find_date = file_paths - self.identify_uncommitted_files(file_paths)

        for commit in walker:
            if not to_find_date:
                break

            if commit.parents:
                parent = commit.parents[0]
                diff = self.repo.diff(parent, commit)

                for patch in diff:
                    file_path = Path(patch.delta.new_file.path)
                    if file_path in to_find_date:
                        last_edited[file_path] = datetime.fromtimestamp(commit.commit_time, UTC)
                        to_find_date.remove(file_path)

        return last_edited


    def identify_uncommitted_files(self, file_paths: set[Path]):
        status = self.repo.status()

        uncommitted_statuses = {
            pygit2.GIT_STATUS_WT_NEW,  # New files in working tree
            pygit2.GIT_STATUS_INDEX_NEW  # New files in index (staged but not committed)
        }

        uncommitted_files = set()

        for file_path in file_paths:
            file_path_str = file_path.as_posix()
            if file_path_str in status and status[file_path_str] & sum(uncommitted_statuses):
                uncommitted_files.add(file_path)

        return uncommitted_files
