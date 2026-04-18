import os
from datetime import UTC, datetime
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pygit2

from ssg.git import GitClient


class TestGitClient(TestCase):

    def setUp(self):
        # Use Path.cwd() as the repo root so all paths are absolute and
        # portable across operating systems without needing a real repo on disk.
        self.repo_root = Path.cwd()

        with patch('pygit2.Repository') as MockRepo:
            self.mock_repo = MockRepo.return_value
            # pygit2's workdir always ends with a path separator
            self.mock_repo.workdir = str(self.repo_root) + os.sep
            self.client = GitClient(self.repo_root)

    @staticmethod
    def _make_patch(repo_relative_path: str) -> MagicMock:
        """Return a mock pygit2 diff patch for the given repo-relative path."""
        p = MagicMock()
        p.delta.new_file.path = repo_relative_path
        return p

    @staticmethod
    def _make_commit(commit_time: int, parent: MagicMock | None = None) -> tuple[MagicMock, MagicMock|None]:
        """Return (commit, parent) mocks with a single parent."""
        parent = parent or MagicMock()
        commit = MagicMock()
        commit.commit_time = commit_time
        commit.parents = [parent]
        return commit, parent

    def test_get_last_edit_time_single_file(self):
        """A file touched by a commit receives that commit's UTC timestamp."""
        file_path = self.repo_root / 'src' / 'index.md'
        ts = 1_700_000_000
        commit, parent = self._make_commit(ts)

        self.mock_repo.status.return_value = {}
        self.mock_repo.walk.return_value = iter([commit])
        self.mock_repo.diff.return_value = [self._make_patch('src/index.md')]

        result = self.client.get_last_edit_time_for_files({file_path})

        self.assertEqual(result[file_path], datetime.fromtimestamp(ts, UTC))

    def test_get_last_edit_time_file_not_in_history(self):
        """A file not touched by any commit is absent from the result."""
        file_path = self.repo_root / 'src' / 'ghost.md'
        commit, _ = self._make_commit(1_700_000_000)

        self.mock_repo.status.return_value = {}
        self.mock_repo.walk.return_value = iter([commit])
        self.mock_repo.diff.return_value = [self._make_patch('src/other.md')]

        result = self.client.get_last_edit_time_for_files({file_path})

        self.assertNotIn(file_path, result)

    def test_get_last_edit_time_uncommitted_file_excluded(self):
        """An uncommitted file is excluded from the history walk and absent from the result."""
        file_path = self.repo_root / 'src' / 'new.md'
        self.mock_repo.status.return_value = {'src/new.md': pygit2.GIT_STATUS_WT_NEW}
        self.mock_repo.walk.return_value = iter([])

        result = self.client.get_last_edit_time_for_files({file_path})

        self.assertNotIn(file_path, result)

    def test_get_last_edit_time_root_commit_skipped(self):
        """A root commit (no parents) is silently skipped and diff is never called."""
        file_path = self.repo_root / 'src' / 'index.md'
        root_commit = MagicMock()
        root_commit.parents = []

        self.mock_repo.status.return_value = {}
        self.mock_repo.walk.return_value = iter([root_commit])

        result = self.client.get_last_edit_time_for_files({file_path})

        self.assertNotIn(file_path, result)
        self.mock_repo.diff.assert_not_called()

    def test_get_last_edit_time_multiple_files_in_different_commits(self):
        """Files found in separate commits each receive the correct timestamp."""
        file_a = self.repo_root / 'src' / 'a.md'
        file_b = self.repo_root / 'src' / 'b.md'
        ts_a, ts_b = 1_700_000_100, 1_700_000_000
        commit_a, parent_a = self._make_commit(ts_a)
        commit_b, parent_b = self._make_commit(ts_b)

        def diff_side_effect(_, commit):
            if commit is commit_a:
                return [self._make_patch('src/a.md')]
            if commit is commit_b:
                return [self._make_patch('src/b.md')]
            return []

        self.mock_repo.diff.side_effect = diff_side_effect
        self.mock_repo.walk.return_value = iter([commit_a, commit_b])
        self.mock_repo.status.return_value = {}

        result = self.client.get_last_edit_time_for_files({file_a, file_b})

        self.assertEqual(result[file_a], datetime.fromtimestamp(ts_a, UTC))
        self.assertEqual(result[file_b], datetime.fromtimestamp(ts_b, UTC))

    def test_get_last_edit_time_empty_input(self):
        """An empty input set returns an empty dict without walking any commits."""
        self.mock_repo.status.return_value = {}
        self.mock_repo.walk.return_value = iter([])

        result = self.client.get_last_edit_time_for_files(set())

        self.assertEqual(result, {})
        self.mock_repo.diff.assert_not_called()

    def test_get_last_edit_time_early_exit(self):
        """The commit walk stops as soon as all requested files are found."""
        file_path = self.repo_root / 'src' / 'index.md'
        ts = 1_700_000_000
        first_commit, first_parent = self._make_commit(ts)

        # Second commit intentionally has a parent so it WOULD be diffed if reached.
        second_commit, second_parent = self._make_commit(ts - 1000)

        def diff_side_effect(_, commit):
            if commit is first_commit:
                return [self._make_patch('src/index.md')]
            return []

        self.mock_repo.diff.side_effect = diff_side_effect
        self.mock_repo.walk.return_value = iter([first_commit, second_commit])
        self.mock_repo.status.return_value = {}

        result = self.client.get_last_edit_time_for_files({file_path})

        self.assertIn(file_path, result)
        # Diff must have been called exactly once — the loop broke before second_commit
        self.mock_repo.diff.assert_called_once_with(first_parent, first_commit)
