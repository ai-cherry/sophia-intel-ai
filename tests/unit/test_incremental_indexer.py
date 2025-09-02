"""
Unit tests for the incremental indexer module.

Tests cover:
- Empty git diff handling
- Non-existent file handling
- Large file set warnings
- Git command failures
- Successful indexing flow
"""
import subprocess
from unittest.mock import Mock, patch

import pytest

from app.indexing.incremental_indexer import get_changed_files, incremental_index


class TestGetChangedFiles:
    """Test suite for get_changed_files function."""

    @patch('subprocess.run')
    def test_get_changed_files_empty_diff(self, mock_run):
        """Test handling of empty git diff output."""
        mock_run.return_value = Mock(
            stdout='',
            stderr='',
            returncode=0
        )

        result = get_changed_files()

        assert result == []
        mock_run.assert_called_once_with(
            ['git', 'diff', '--name-only', 'HEAD'],
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

    @patch('subprocess.run')
    def test_get_changed_files_with_changes(self, mock_run):
        """Test successful retrieval of changed files."""
        mock_run.return_value = Mock(
            stdout='file1.py\nfile2.txt\ndir/file3.md',
            stderr='',
            returncode=0
        )

        result = get_changed_files()

        assert result == ['file1.py', 'file2.txt', 'dir/file3.md']

    @patch('subprocess.run')
    @patch('logging.getLogger')
    def test_get_changed_files_large_changeset_warning(self, mock_logger, mock_run):
        """Test warning for large number of changed files."""
        # Create a mock logger
        logger_instance = Mock()
        mock_logger.return_value = logger_instance

        # Generate 1001 file changes
        large_file_list = '\n'.join([f'file{i}.py' for i in range(1001)])
        mock_run.return_value = Mock(
            stdout=large_file_list,
            stderr='',
            returncode=0
        )

        result = get_changed_files()

        assert len(result) == 1001
        # Verify warning was logged
        logger_instance.warning.assert_called()

    @patch('subprocess.run')
    def test_get_changed_files_git_error(self, mock_run):
        """Test handling of git command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=['git', 'diff', '--name-only', 'HEAD'],
            stderr='fatal: not a git repository'
        )

        result = get_changed_files()

        assert result == []

    @patch('subprocess.run')
    def test_get_changed_files_timeout(self, mock_run):
        """Test handling of git command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=['git', 'diff', '--name-only', 'HEAD'],
            timeout=30
        )

        result = get_changed_files()

        assert result == []

    @patch('subprocess.run')
    def test_get_changed_files_unexpected_error(self, mock_run):
        """Test handling of unexpected errors."""
        mock_run.side_effect = Exception("Unexpected error")

        result = get_changed_files()

        assert result == []


class TestIncrementalIndex:
    """Test suite for incremental_index function."""

    @pytest.mark.asyncio
    @patch('app.indexing.incremental_indexer.get_changed_files')
    @patch('logging.getLogger')
    async def test_incremental_index_no_changes(self, mock_logger, mock_get_changed):
        """Test incremental index with no changed files."""
        logger_instance = Mock()
        mock_logger.return_value = logger_instance
        mock_get_changed.return_value = []

        await incremental_index()

        logger_instance.info.assert_any_call("No files to reindex")

    @pytest.mark.asyncio
    @patch('app.indexing.incremental_indexer.get_changed_files')
    @patch('app.indexing.incremental_indexer.index_file')
    @patch('os.path.exists')
    @patch('logging.getLogger')
    async def test_incremental_index_non_existent_file(
        self, mock_logger, mock_exists, mock_index_file, mock_get_changed
    ):
        """Test handling of non-existent files during indexing."""
        logger_instance = Mock()
        mock_logger.return_value = logger_instance
        mock_get_changed.return_value = ['deleted_file.py', 'existing_file.py']
        mock_exists.side_effect = [False, True]  # First file doesn't exist, second does
        mock_index_file.return_value = None

        await incremental_index()

        # Should only index the existing file
        mock_index_file.assert_called_once_with('existing_file.py')
        logger_instance.warning.assert_any_call("File no longer exists: deleted_file.py")

    @pytest.mark.asyncio
    @patch('app.indexing.incremental_indexer.get_changed_files')
    @patch('app.indexing.incremental_indexer.index_file')
    @patch('os.path.exists')
    @patch('logging.getLogger')
    async def test_incremental_index_successful(
        self, mock_logger, mock_exists, mock_index_file, mock_get_changed
    ):
        """Test successful incremental indexing."""
        logger_instance = Mock()
        mock_logger.return_value = logger_instance
        mock_get_changed.return_value = ['file1.py', 'file2.py', 'file3.py']
        mock_exists.return_value = True
        mock_index_file.return_value = None

        await incremental_index()

        assert mock_index_file.call_count == 3
        logger_instance.info.assert_any_call("Incremental indexing complete. Indexed: 3, Failed: 0")

    @pytest.mark.asyncio
    @patch('app.indexing.incremental_indexer.get_changed_files')
    @patch('app.indexing.incremental_indexer.index_file')
    @patch('os.path.exists')
    @patch('logging.getLogger')
    async def test_incremental_index_with_failures(
        self, mock_logger, mock_exists, mock_index_file, mock_get_changed
    ):
        """Test incremental indexing with some failures."""
        logger_instance = Mock()
        mock_logger.return_value = logger_instance
        mock_get_changed.return_value = ['file1.py', 'file2.py', 'file3.py']
        mock_exists.return_value = True

        # Make the second file fail to index
        mock_index_file.side_effect = [None, Exception("Index error"), None]

        await incremental_index()

        assert mock_index_file.call_count == 3
        logger_instance.error.assert_any_call("Failed to reindex file2.py: Index error")
        logger_instance.info.assert_any_call("Incremental indexing complete. Indexed: 2, Failed: 1")

    @pytest.mark.asyncio
    @patch('app.indexing.incremental_indexer.get_changed_files')
    @patch('app.indexing.incremental_indexer.index_file')
    @patch('os.path.exists')
    @patch('logging.getLogger')
    async def test_incremental_index_batching(
        self, mock_logger, mock_exists, mock_index_file, mock_get_changed
    ):
        """Test batching functionality for large changesets."""
        logger_instance = Mock()
        mock_logger.return_value = logger_instance

        # Create 250 changed files
        files = [f'file{i}.py' for i in range(250)]
        mock_get_changed.return_value = files
        mock_exists.return_value = True
        mock_index_file.return_value = None

        await incremental_index(batch_size=100)

        # Should process in 3 batches (100, 100, 50)
        assert mock_index_file.call_count == 250
        # Check batch logging
        logger_instance.info.assert_any_call("Processing batch 1 (100 files)")
        logger_instance.info.assert_any_call("Processing batch 2 (100 files)")
        logger_instance.info.assert_any_call("Processing batch 3 (50 files)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
