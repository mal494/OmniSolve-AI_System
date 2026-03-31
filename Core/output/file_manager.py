"""
File manager with async write support and validation.
Handles writing generated code to the filesystem safely.
"""
import asyncio
import os
from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor

if TYPE_CHECKING:
    # Type-only import; keep aiofiles optional at runtime
    pass

from ..config.constants import PROJECTS_DIR
from ..exceptions.errors import FileOperationError
from ..logging import get_logger, audit_log
from ..utils.text_parsers import validate_python_syntax

logger = get_logger('file_manager')


class FileManager:
    """Manages file operations with validation and async writes."""

    def __init__(self, projects_dir: Optional[str] = None):
        """
        Initialize the file manager.

        Args:
            projects_dir: Base directory for projects (defaults to config value)
        """
        self.projects_dir = Path(projects_dir or PROJECTS_DIR)
        self.projects_dir.mkdir(exist_ok=True, parents=True)
        self.logger = logger

    def get_project_path(self, project_name: str) -> Path:
        """
        Get the full path for a project.

        Args:
            project_name: Name of the project

        Returns:
            Path object for the project directory
        """
        return self.projects_dir / project_name

    def ensure_project_exists(self, project_name: str) -> Path:
        """
        Ensure project directory exists.

        Args:
            project_name: Name of the project

        Returns:
            Path to the project directory
        """
        project_path = self.get_project_path(project_name)
        project_path.mkdir(exist_ok=True, parents=True)
        self.logger.debug(f"Ensured project directory exists: {project_path}")
        return project_path

    def _prepare_file_path(self, project_name: str, file_path: str) -> Path:
        """
        Prepare and validate file path for writing.

        Args:
            project_name: Name of the project
            file_path: Relative path within project

        Returns:
            Full path to the file
        """
        project_path = self.ensure_project_exists(project_name)

        # Remove project name prefix if present in file_path
        if file_path.startswith(f"{project_name}/"):
            file_path = file_path[len(project_name) + 1:]

        full_path = project_path / file_path

        # Block path traversal attempts (resolve symlinks and normalize)
        resolved = full_path.resolve()
        project_resolved = project_path.resolve()
        if not str(resolved).startswith(str(project_resolved) + os.sep) and resolved != project_resolved:
            raise FileOperationError(
                f"Path traversal detected: '{file_path}' escapes project directory",
                {'file': file_path, 'project': str(project_resolved)}
            )

        # Ensure parent directory exists
        full_path.parent.mkdir(exist_ok=True, parents=True)

        return full_path

    def _validate_content(self, file_path: str, content: str, validate: bool = True):
        """
        Validate file content based on file type.

        Args:
            file_path: Path to the file
            content: Content to validate
            validate: Whether to validate

        Raises:
            FileOperationError: If validation fails
        """
        if validate and file_path.endswith('.py'):
            is_valid, error_msg = validate_python_syntax(content)
            if not is_valid:
                raise FileOperationError(
                    f"Invalid Python syntax in {file_path}: {error_msg}",
                    {'file': file_path, 'error': error_msg}
                )

    def write_file(
        self,
        project_name: str,
        file_path: str,
        content: str,
        validate: bool = True,
        backup: bool = True
    ) -> Path:
        """
        Write a single file with validation.

        Args:
            project_name: Name of the project
            file_path: Relative path within project
            content: File content
            validate: Whether to validate Python syntax
            backup: Whether to backup existing file

        Returns:
            Path to the written file

        Raises:
            FileOperationError: If write fails
        """
        try:
            # Prepare path and validate content
            full_path = self._prepare_file_path(project_name, file_path)
            self._validate_content(file_path, content, validate)

            # Backup existing file if requested
            if backup and full_path.exists():
                backup_path = full_path.with_suffix(full_path.suffix + '.bak')
                full_path.rename(backup_path)
                self.logger.debug(f"Backed up existing file to {backup_path}")

            # Write the file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"Wrote file: {full_path}")
            audit_log(
                'file_written',
                project_name=project_name,
                file_path=file_path,
                size=len(content),
                validated=validate
            )

            return full_path

        except FileOperationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to write {file_path}: {e}")
            raise FileOperationError(
                f"Failed to write file {file_path}",
                {'file': file_path, 'error': str(e)}
            )

    async def write_file_async(
        self,
        project_name: str,
        file_path: str,
        content: str,
        validate: bool = True
    ) -> Path:
        """
        Write a single file asynchronously.

        Args:
            project_name: Name of the project
            file_path: Relative path within project
            content: File content
            validate: Whether to validate Python syntax

        Returns:
            Path to the written file
        """
        try:
            # Prepare path and validate content using shared helpers
            full_path = self._prepare_file_path(project_name, file_path)
            self._validate_content(file_path, content, validate)

            # Write async
            try:
                import aiofiles  # type: ignore  # Local import so aiofiles can be optional at runtime
            except ImportError as e:
                self.logger.error(f"aiofiles not available for async write: {e}")
                raise FileOperationError(
                    "aiofiles is required for async file writes. Install aiofiles with 'pip install aiofiles'.",
                    {'file': file_path, 'error': str(e)}
                )
            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                await f.write(content)

            self.logger.info(f"Wrote file async: {full_path}")
            audit_log(
                'file_written_async',
                project_name=project_name,
                file_path=file_path,
                size=len(content)
            )

            return full_path

        except Exception as e:
            self.logger.error(f"Failed to write {file_path} async: {e}")
            raise FileOperationError(
                f"Failed to write file {file_path}",
                {'file': file_path, 'error': str(e)}
            )

    def write_files_batch(
        self,
        project_name: str,
        files: List[Dict[str, str]],
        validate: bool = True
    ) -> List[Path]:
        """
        Write multiple files using thread pool for parallel I/O.

        Args:
            project_name: Name of the project
            files: List of dicts with 'path' and 'content' keys
            validate: Whether to validate Python syntax

        Returns:
            List of paths to written files
        """
        self.logger.info(f"Writing {len(files)} files in batch")

        written_paths = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for file_info in files:
                future = executor.submit(
                    self.write_file,
                    project_name,
                    file_info['path'],
                    file_info['content'],
                    validate,
                    False  # Don't backup in batch operations
                )
                futures.append(future)

            for future in futures:
                try:
                    path = future.result()
                    written_paths.append(path)
                except Exception as e:
                    self.logger.error(f"Failed to write file in batch: {e}")
                    # Continue with other files

        self.logger.info(f"Batch write complete: {len(written_paths)}/{len(files)} successful")
        return written_paths

    async def write_files_async(
        self,
        project_name: str,
        files: List[Dict[str, str]],
        validate: bool = True
    ) -> List[Path]:
        """
        Write multiple files asynchronously.

        Args:
            project_name: Name of the project
            files: List of dicts with 'path' and 'content' keys
            validate: Whether to validate Python syntax

        Returns:
            List of paths to written files
        """
        self.logger.info(f"Writing {len(files)} files async")

        tasks = []
        for file_info in files:
            task = self.write_file_async(
                project_name,
                file_info['path'],
                file_info['content'],
                validate
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Narrow result type so mypy can infer a list[Path] return type
        from typing import cast
        written_paths: List[Path] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to write {files[i]['path']}: {result}")
            else:
                written_paths.append(cast(Path, result))

        self.logger.info(f"Async write complete: {len(written_paths)}/{len(files)} successful")
        return written_paths

    def get_file_content(self, project_name: str, file_path: str) -> str:
        """
        Read file content.

        Args:
            project_name: Name of the project
            file_path: Relative path within project

        Returns:
            File content as string
        """
        project_path = self.get_project_path(project_name)
        full_path = project_path / file_path

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise FileOperationError(
                f"Failed to read file {file_path}",
                {'file': file_path, 'error': str(e)}
            )


# Global file manager instance
file_manager = FileManager()
