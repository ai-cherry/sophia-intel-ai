#!/usr/bin/env python3
"""
Real File Operations Service for Sophia AI
Phase 4: MCP Tools Integration - File System Operations
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FileOperationResult:
    """Result of a file operation"""

    success: bool
    operation: str
    file_path: str
    content: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = None
    processing_time_ms: float = 0.0

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RealFileOperationsService:
    """
    Real file operations service - no mocks, actual file system access
    Provides safe file operations for AI assistant integration
    """

    def __init__(self, base_directory: str = None):
        self.base_directory = Path(base_directory) if base_directory else Path.cwd()
        self.allowed_extensions = {
            ".txt",
            ".md",
            ".py",
            ".js",
            ".ts",
            ".json",
            ".yaml",
            ".yml",
            ".html",
            ".css",
            ".sql",
            ".sh",
            ".xml",
            ".csv",
            ".log",
            ".ini",
            ".cfg",
        }
        self.max_file_size = 10 * 1024 * 1024  # 10MB limit
        self.operation_count = 0
        self.total_processing_time = 0.0

        # Security: Only allow operations within base directory
        self.base_directory = self.base_directory.resolve()

        logger.info(
            f"🗂️ File Operations Service initialized - Base: {self.base_directory}"
        )

    def _is_safe_path(self, file_path: str) -> bool:
        """Check if the file path is safe (within base directory)"""
        try:
            full_path = (self.base_directory / file_path).resolve()
            return str(full_path).startswith(str(self.base_directory))
        except Exception:
            return False

    def _is_allowed_extension(self, file_path: str) -> bool:
        """Check if file extension is allowed"""
        return Path(file_path).suffix.lower() in self.allowed_extensions

    async def read_file(
        self, file_path: str, max_lines: int | None = None
    ) -> FileOperationResult:
        """Read file contents safely"""
        start_time = time.time()

        try:
            if not self._is_safe_path(file_path):
                return FileOperationResult(
                    success=False,
                    operation="read_file",
                    file_path=file_path,
                    error="File path is outside allowed directory",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            if not self._is_allowed_extension(file_path):
                return FileOperationResult(
                    success=False,
                    operation="read_file",
                    file_path=file_path,
                    error=f"File extension not allowed. Allowed: {', '.join(self.allowed_extensions)}",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            full_path = self.base_directory / file_path

            if not full_path.exists():
                return FileOperationResult(
                    success=False,
                    operation="read_file",
                    file_path=file_path,
                    error="File does not exist",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            # Check file size
            file_size = full_path.stat().st_size
            if file_size > self.max_file_size:
                return FileOperationResult(
                    success=False,
                    operation="read_file",
                    file_path=file_path,
                    error=f"File too large ({file_size} bytes > {self.max_file_size} bytes)",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            # Read file content
            content = full_path.read_text(encoding="utf-8")

            # Limit lines if specified
            if max_lines:
                lines = content.split("\n")
                if len(lines) > max_lines:
                    content = "\n".join(lines[:max_lines])
                    content += f"\n\n... (truncated at {max_lines} lines, total: {len(lines)} lines)"

            processing_time = (time.time() - start_time) * 1000
            self.operation_count += 1
            self.total_processing_time += processing_time

            return FileOperationResult(
                success=True,
                operation="read_file",
                file_path=file_path,
                content=content,
                metadata={
                    "file_size": file_size,
                    "line_count": len(content.split("\n")),
                    "encoding": "utf-8",
                },
                processing_time_ms=processing_time,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Error reading file {file_path}: {e}")
            return FileOperationResult(
                success=False,
                operation="read_file",
                file_path=file_path,
                error=str(e),
                processing_time_ms=processing_time,
            )

    async def write_file(
        self, file_path: str, content: str, create_dirs: bool = True
    ) -> FileOperationResult:
        """Write content to file safely"""
        start_time = time.time()

        try:
            if not self._is_safe_path(file_path):
                return FileOperationResult(
                    success=False,
                    operation="write_file",
                    file_path=file_path,
                    error="File path is outside allowed directory",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            if not self._is_allowed_extension(file_path):
                return FileOperationResult(
                    success=False,
                    operation="write_file",
                    file_path=file_path,
                    error=f"File extension not allowed. Allowed: {', '.join(self.allowed_extensions)}",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            full_path = self.base_directory / file_path

            # Create directories if needed
            if create_dirs:
                full_path.parent.mkdir(parents=True, exist_ok=True)

            # Check content size
            content_size = len(content.encode("utf-8"))
            if content_size > self.max_file_size:
                return FileOperationResult(
                    success=False,
                    operation="write_file",
                    file_path=file_path,
                    error=f"Content too large ({content_size} bytes > {self.max_file_size} bytes)",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            # Write file
            full_path.write_text(content, encoding="utf-8")

            processing_time = (time.time() - start_time) * 1000
            self.operation_count += 1
            self.total_processing_time += processing_time

            return FileOperationResult(
                success=True,
                operation="write_file",
                file_path=file_path,
                content=None,  # Don't return content for write operations
                metadata={
                    "content_size": content_size,
                    "line_count": len(content.split("\n")),
                    "created_dirs": create_dirs,
                },
                processing_time_ms=processing_time,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Error writing file {file_path}: {e}")
            return FileOperationResult(
                success=False,
                operation="write_file",
                file_path=file_path,
                error=str(e),
                processing_time_ms=processing_time,
            )

    async def list_directory(
        self, directory_path: str = "", pattern: str = "*"
    ) -> FileOperationResult:
        """List directory contents safely"""
        start_time = time.time()

        try:
            if not self._is_safe_path(directory_path):
                return FileOperationResult(
                    success=False,
                    operation="list_directory",
                    file_path=directory_path,
                    error="Directory path is outside allowed directory",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            full_path = self.base_directory / directory_path

            if not full_path.exists():
                return FileOperationResult(
                    success=False,
                    operation="list_directory",
                    file_path=directory_path,
                    error="Directory does not exist",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            if not full_path.is_dir():
                return FileOperationResult(
                    success=False,
                    operation="list_directory",
                    file_path=directory_path,
                    error="Path is not a directory",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            # List directory contents
            entries = []
            for item in full_path.glob(pattern):
                relative_path = item.relative_to(self.base_directory)
                entry = {
                    "name": item.name,
                    "path": str(relative_path),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": item.stat().st_mtime,
                }
                if item.is_file():
                    entry["extension"] = item.suffix
                entries.append(entry)

            # Sort by type (directories first) then by name
            entries.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))

            content = json.dumps(entries, indent=2)

            processing_time = (time.time() - start_time) * 1000
            self.operation_count += 1
            self.total_processing_time += processing_time

            return FileOperationResult(
                success=True,
                operation="list_directory",
                file_path=directory_path,
                content=content,
                metadata={
                    "entry_count": len(entries),
                    "directories": len(
                        [e for e in entries if e["type"] == "directory"]
                    ),
                    "files": len([e for e in entries if e["type"] == "file"]),
                    "pattern": pattern,
                },
                processing_time_ms=processing_time,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Error listing directory {directory_path}: {e}")
            return FileOperationResult(
                success=False,
                operation="list_directory",
                file_path=directory_path,
                error=str(e),
                processing_time_ms=processing_time,
            )

    async def file_exists(self, file_path: str) -> FileOperationResult:
        """Check if file exists"""
        start_time = time.time()

        try:
            if not self._is_safe_path(file_path):
                return FileOperationResult(
                    success=False,
                    operation="file_exists",
                    file_path=file_path,
                    error="File path is outside allowed directory",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            full_path = self.base_directory / file_path
            exists = full_path.exists()

            processing_time = (time.time() - start_time) * 1000
            self.operation_count += 1
            self.total_processing_time += processing_time

            return FileOperationResult(
                success=True,
                operation="file_exists",
                file_path=file_path,
                content=str(exists),
                metadata={
                    "exists": exists,
                    "is_file": full_path.is_file() if exists else False,
                    "is_directory": full_path.is_dir() if exists else False,
                },
                processing_time_ms=processing_time,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Error checking file existence {file_path}: {e}")
            return FileOperationResult(
                success=False,
                operation="file_exists",
                file_path=file_path,
                error=str(e),
                processing_time_ms=processing_time,
            )

    async def get_file_info(self, file_path: str) -> FileOperationResult:
        """Get detailed file information"""
        start_time = time.time()

        try:
            if not self._is_safe_path(file_path):
                return FileOperationResult(
                    success=False,
                    operation="get_file_info",
                    file_path=file_path,
                    error="File path is outside allowed directory",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            full_path = self.base_directory / file_path

            if not full_path.exists():
                return FileOperationResult(
                    success=False,
                    operation="get_file_info",
                    file_path=file_path,
                    error="File does not exist",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            stat = full_path.stat()
            info = {
                "name": full_path.name,
                "path": str(full_path.relative_to(self.base_directory)),
                "type": "directory" if full_path.is_dir() else "file",
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "permissions": oct(stat.st_mode)[-3:],
                "extension": full_path.suffix if full_path.is_file() else None,
                "is_allowed_extension": (
                    self._is_allowed_extension(str(full_path))
                    if full_path.is_file()
                    else None
                ),
            }

            content = json.dumps(info, indent=2)

            processing_time = (time.time() - start_time) * 1000
            self.operation_count += 1
            self.total_processing_time += processing_time

            return FileOperationResult(
                success=True,
                operation="get_file_info",
                file_path=file_path,
                content=content,
                metadata=info,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Error getting file info {file_path}: {e}")
            return FileOperationResult(
                success=False,
                operation="get_file_info",
                file_path=file_path,
                error=str(e),
                processing_time_ms=processing_time,
            )

    async def get_service_stats(self) -> dict[str, Any]:
        """Get file operations service statistics"""
        avg_processing_time = self.total_processing_time / max(1, self.operation_count)

        return {
            "service_status": "operational",
            "base_directory": str(self.base_directory),
            "total_operations": self.operation_count,
            "average_processing_time_ms": avg_processing_time,
            "allowed_extensions": list(self.allowed_extensions),
            "max_file_size_mb": self.max_file_size // (1024 * 1024),
            "security_enabled": True,
            "supported_operations": [
                "read_file",
                "write_file",
                "list_directory",
                "file_exists",
                "get_file_info",
            ],
        }


# Global file operations service instance
_file_operations_service: RealFileOperationsService | None = None


async def get_file_operations_service() -> RealFileOperationsService:
    """Get global file operations service instance"""
    global _file_operations_service

    if _file_operations_service is None:
        # Initialize with current working directory as base
        _file_operations_service = RealFileOperationsService()

    return _file_operations_service


# Test the file operations service
if __name__ == "__main__":

    async def sophia_file_operations():
        service = await get_file_operations_service()

        # Test listing current directory
        result = await service.list_directory()
        print(f"Directory listing: {result.success}")
        if result.success:
            print(f"Found {result.metadata['entry_count']} entries")

        # Test reading a file
        result = await service.read_file("README.md", max_lines=10)
        print(f"Read README.md: {result.success}")
        if result.success:
            print(f"Content length: {len(result.content)} chars")

        # Test getting service stats
        stats = await service.get_service_stats()
        print(f"Service stats: {stats}")

    asyncio.run(sophia_file_operations())
