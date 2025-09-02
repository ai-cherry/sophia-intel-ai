"""
Unit tests for the Airbyte ETL module.

Tests cover:
- ETL pipeline execution
- Database configuration validation
- File processing and chunking
- Metadata creation and validation
- Error handling
"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, mock_open, call
from datetime import datetime
from app.indexing.airbyte_etl import run_airbyte_etl, process_file
from app.models.metadata import MemoryMetadata


class TestRunAirbyteETL:
    """Test suite for run_airbyte_etl function."""
    
    @patch.dict(os.environ, {
        'NEON_DB_HOST': 'test-host',
        'NEON_DB_PORT': '5432',
        'NEON_DB_USER': 'test-user',
        'NEON_DB_PASSWORD': 'test-password',
        'NEON_DB_NAME': 'test-db'
    })
    @patch('app.indexing.airbyte_etl.AirbyteSource')
    @patch('tempfile.mkdtemp')
    @patch('os.listdir')
    @patch('os.path.isfile')
    @patch('app.indexing.airbyte_etl.process_file')
    @patch('shutil.rmtree')
    def test_run_airbyte_etl_successful(
        self, mock_rmtree, mock_process, mock_isfile, 
        mock_listdir, mock_mkdtemp, mock_source_class
    ):
        """Test successful ETL pipeline execution."""
        # Setup mocks
        mock_mkdtemp.return_value = '/tmp/test_dir'
        mock_listdir.return_value = ['file1.json', 'file2.json', 'dir1']
        mock_isfile.side_effect = [True, True, False]  # First two are files, third is directory
        mock_source = Mock()
        mock_source_class.return_value = mock_source
        
        # Run ETL
        run_airbyte_etl()
        
        # Verify source was configured correctly
        mock_source_class.assert_called_once_with("airbyte-source-postgres")
        mock_source.sync.assert_called_once()
        
        # Verify config passed to sync
        config = mock_source.sync.call_args[0][0]
        assert config['host'] == 'test-host'
        assert config['port'] == '5432'
        assert config['username'] == 'test-user'
        assert config['password'] == 'test-password'
        assert config['database'] == 'test-db'
        assert config['schema'] == 'public'
        assert config['output_directory'] == '/tmp/test_dir'
        
        # Verify files were processed
        assert mock_process.call_count == 2
        mock_process.assert_any_call('/tmp/test_dir/file1.json')
        mock_process.assert_any_call('/tmp/test_dir/file2.json')
        
        # Verify cleanup
        mock_rmtree.assert_called_once_with('/tmp/test_dir', ignore_errors=True)
    
    @patch.dict(os.environ, {})  # Empty environment
    def test_run_airbyte_etl_missing_config(self):
        """Test ETL fails with missing database configuration."""
        with pytest.raises(RuntimeError) as exc_info:
            run_airbyte_etl()
        
        assert "Missing DB configuration" in str(exc_info.value)
        assert "NEON_DB_HOST" in str(exc_info.value)
    
    @patch.dict(os.environ, {
        'NEON_DB_HOST': 'test-host',
        'NEON_DB_PORT': '5432',
        'NEON_DB_USER': 'test-user',
        # Missing NEON_DB_PASSWORD
        'NEON_DB_NAME': 'test-db'
    })
    def test_run_airbyte_etl_partial_config(self):
        """Test ETL fails with partial database configuration."""
        with pytest.raises(RuntimeError) as exc_info:
            run_airbyte_etl()
        
        assert "Missing DB configuration" in str(exc_info.value)
        assert "NEON_DB_PASSWORD" in str(exc_info.value)
    
    @patch.dict(os.environ, {
        'NEON_DB_HOST': 'test-host',
        'NEON_DB_PORT': '5432',
        'NEON_DB_USER': 'test-user',
        'NEON_DB_PASSWORD': 'test-password',
        'NEON_DB_NAME': 'test-db'
    })
    @patch('app.indexing.airbyte_etl.AirbyteSource')
    @patch('tempfile.mkdtemp')
    @patch('shutil.rmtree')
    @patch('logging.error')
    def test_run_airbyte_etl_sync_failure(
        self, mock_log_error, mock_rmtree, mock_mkdtemp, mock_source_class
    ):
        """Test ETL handles sync failures properly."""
        mock_mkdtemp.return_value = '/tmp/test_dir'
        mock_source = Mock()
        mock_source.sync.side_effect = Exception("Sync failed")
        mock_source_class.return_value = mock_source
        
        with pytest.raises(Exception) as exc_info:
            run_airbyte_etl()
        
        assert "Sync failed" in str(exc_info.value)
        mock_log_error.assert_called_once()
        # Ensure cleanup still happens
        mock_rmtree.assert_called_once_with('/tmp/test_dir', ignore_errors=True)


class TestProcessFile:
    """Test suite for process_file function."""
    
    @patch('builtins.open', new_callable=mock_open, read_data='Test content for chunking')
    @patch('app.indexing.airbyte_etl.chunk_text')
    @patch('app.indexing.airbyte_etl.index_file')
    @patch('os.remove')
    @patch('app.indexing.airbyte_etl.datetime')
    def test_process_file_successful(
        self, mock_datetime, mock_remove, mock_index, mock_chunk, mock_file
    ):
        """Test successful file processing."""
        # Setup mocks
        mock_now = Mock()
        mock_datetime.utcnow.return_value = mock_now
        mock_chunk.return_value = ['chunk1', 'chunk2', 'chunk3']
        
        # Process file
        process_file('/path/to/file.txt')
        
        # Verify file was read
        mock_file.assert_called()
        
        # Verify chunking
        mock_chunk.assert_called_once_with('Test content for chunking')
        
        # Verify each chunk was processed
        assert mock_index.call_count == 3
        
        # Verify metadata creation for each chunk
        for i, chunk in enumerate(['chunk1', 'chunk2', 'chunk3']):
            temp_file = f'/path/to/file.txt.chunk_{i}'
            
            # Check that index_file was called with correct metadata
            call_args = mock_index.call_args_list[i]
            assert call_args[0][0] == temp_file
            metadata = call_args[1]['metadata']
            assert isinstance(metadata, MemoryMetadata)
            assert metadata.type == 'doc'
            assert metadata.source == '/path/to/file.txt'
            assert metadata.timestamp == mock_now
            assert metadata.tags == ['etl', 'processed']
            
            # Verify temp file cleanup
            mock_remove.assert_any_call(temp_file)
    
    @patch('builtins.open', new_callable=mock_open, read_data='')
    def test_process_file_empty_content(self, mock_file):
        """Test processing empty file."""
        process_file('/path/to/empty.txt')
        
        # File should be opened but no further processing
        mock_file.assert_called_once_with('/path/to/empty.txt', 'r')
    
    @patch('builtins.open', side_effect=IOError("File not found"))
    @patch('logging.error')
    def test_process_file_read_error(self, mock_log_error, mock_file):
        """Test handling of file read errors."""
        with pytest.raises(IOError):
            process_file('/path/to/nonexistent.txt')
        
        mock_log_error.assert_called_once()
        assert "Failed to process file" in mock_log_error.call_args[0][0]
    
    @patch('builtins.open', new_callable=mock_open, read_data='Test content')
    @patch('app.indexing.airbyte_etl.chunk_text')
    @patch('app.indexing.airbyte_etl.index_file')
    @patch('logging.error')
    def test_process_file_index_error(
        self, mock_log_error, mock_index, mock_chunk, mock_file
    ):
        """Test handling of indexing errors."""
        mock_chunk.return_value = ['chunk1']
        mock_index.side_effect = Exception("Index failed")
        
        with pytest.raises(Exception):
            process_file('/path/to/file.txt')
        
        mock_log_error.assert_called_once()
        assert "Failed to process file" in mock_log_error.call_args[0][0]
    
    @patch('builtins.open', new_callable=mock_open, read_data='Large content')
    @patch('app.indexing.airbyte_etl.chunk_text')
    @patch('app.indexing.airbyte_etl.index_file')
    @patch('os.remove')
    @patch('app.indexing.airbyte_etl.datetime')
    def test_process_file_metadata_type_validation(
        self, mock_datetime, mock_remove, mock_index, mock_chunk, mock_file
    ):
        """Test that metadata uses correct type value."""
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        mock_chunk.return_value = ['chunk1']
        
        process_file('/path/to/file.txt')
        
        # Get the metadata passed to index_file
        call_args = mock_index.call_args_list[0]
        metadata = call_args[1]['metadata']
        
        # Verify metadata type is 'doc' (one of the allowed Literal values)
        assert metadata.type == 'doc'
        # Verify it's not 'text' which was the original bug
        assert metadata.type != 'text'
        # Verify type is one of the allowed values from MemoryMetadata model
        allowed_types = ["code", "sql", "doc", "summary", "entity", "relation"]
        assert metadata.type in allowed_types


class TestETLIntegration:
    """Integration tests for ETL components."""
    
    @patch('builtins.open', new_callable=mock_open, read_data='A' * 3000)  # Large content
    @patch('app.indexing.airbyte_etl.index_file')
    @patch('os.remove')
    def test_large_file_chunking(self, mock_remove, mock_index, mock_file):
        """Test that large files are properly chunked."""
        from app.indexing.chunker import chunk_text
        
        # Process a file with content that should be chunked
        process_file('/path/to/large.txt')
        
        # Verify multiple chunks were created and indexed
        # Default chunk size is 1000, so 3000 chars should create at least 3 chunks
        assert mock_index.call_count >= 3
        
        # Verify temp files were cleaned up
        assert mock_remove.call_count == mock_index.call_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])