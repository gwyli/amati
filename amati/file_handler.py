"""
File Loader Module with Gzip Support

A file loading system that provides automatic format detection and gzip decompression
for JSON and YAML files. The module uses the Strategy pattern to allow easy extension
for additional file formats while maintaining type safety and comprehensive error
handling.

Features:
    - Automatic gzip detection using magic byte inspection
    - Safe loading of JSON and YAML files using json.loads() and yaml.safe_load()
    - Extensible architecture for adding new file format support
    - Comprehensive type hints for Python 3.13+
    - Detailed error handling with descriptive messages
    - Support for both regular and compressed files

Supported File Types:
    - JSON: .json, .js (optionally gzip compressed)
    - YAML: .yaml, .yml (optionally gzip compressed)
"""

import json
from abc import ABC, abstractmethod
from compression import gzip
from pathlib import Path

import yaml

type JSONPrimitive = str | int | float | bool | None
type JSONArray = list["JSONValue"]
type JSONObject = dict[str, "JSONValue"]
type JSONValue = JSONPrimitive | JSONArray | JSONObject


class FileLoader(ABC):
    """Abstract base class for file loaders.

    Defines the interface for loading and parsing files of different formats.
    Implementations should provide format-specific handling logic.
    """

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Check if this loader can handle the given file.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if this loader can handle the file, False otherwise.
        """
        pass

    @abstractmethod
    def load(self, content: str) -> JSONObject:
        """Load and parse the file content.

        Args:
            content: The raw file content as a string.

        Returns:
            The parsed content as a JSONObject.

        Raises:
            May raise implementation-specific exceptions for parsing errors.
        """
        pass


class JSONLoader(FileLoader):
    """Loader for JSON files."""

    def can_handle(self, file_path: Path) -> bool:
        """Check if this loader can handle the given file.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if this loader can handle the file, False otherwise.
        """
        return file_path.suffix.lower() in {".json", ".js"}

    def load(self, content: str) -> JSONObject:
        """Load and parse the file content.

        Args:
            content: The raw file content as a string.

        Returns:
            The parsed content as a JSONObject.

        Raises:
            May raise implementation-specific exceptions for parsing errors.
        """
        return json.loads(content)


class YAMLLoader(FileLoader):
    """Loader for YAML files."""

    def can_handle(self, file_path: Path) -> bool:
        """Check if this loader can handle the given file.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if this loader can handle the file, False otherwise.
        """
        return file_path.suffix.lower() in {".yaml", ".yml"}

    def load(self, content: str) -> JSONObject:
        """Load and parse the file content.

        Args:
            content: The raw file content as a string.

        Returns:
            The parsed content as a JSONObject.

        Raises:
            May raise implementation-specific exceptions for parsing errors.
        """
        return yaml.safe_load(content)


class FileProcessor:
    """Main processor for handling gzipped and regular files.

    Processes files in various formats (JSON, YAML) with optional gzip compression.
    Automatically detects compression and selects the appropriate loader based on
    file extension.

    Attributes:
        loaders: List of available file loaders for different formats.
    """

    def __init__(self) -> None:
        """Initialize the FileProcessor with default loaders."""
        self.loaders: list[FileLoader] = [JSONLoader(), YAMLLoader()]

    @staticmethod
    def _is_gzip_file(file_path: Path) -> bool:
        """Check if file is gzipped by reading magic bytes.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if the file is gzip-compressed, False otherwise.
        """
        try:
            with file_path.open("rb") as f:
                magic = f.read(2)
                return magic == b"\x1f\x8b"
        except OSError:
            return False

    @staticmethod
    def _get_decompressed_path(file_path: Path) -> Path:
        """Get the path without .gz extension for determining file type.

        Args:
            file_path: Path to the potentially compressed file.

        Returns:
            The file path with .gz extension removed if present, otherwise
            the original path unchanged.
        """
        if file_path.suffix.lower() == ".gz":
            return file_path.with_suffix("")
        return file_path

    def _read_file_content(self, file_path: Path) -> str:
        """Read file content, decompressing if necessary.

        Args:
            file_path: Path to the file to read.

        Returns:
            The file content as a UTF-8 encoded string.

        Raises:
            OSError: If the file cannot be read.
            gzip.BadGzipFile: If the file appears to be gzipped but is corrupted.
        """
        if self._is_gzip_file(file_path):
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                return f.read()
        else:
            with file_path.open(encoding="utf-8") as f:
                return f.read()

    def _get_appropriate_loader(self, file_path: Path) -> FileLoader:
        """Get the appropriate loader for the file type.

        Determines the correct loader based on the file extension, ignoring
        any .gz compression extension.

        Args:
            file_path: Path to the file needing a loader.

        Returns:
            The appropriate FileLoader instance for the file type.

        Raises:
            ValueError: If no suitable loader is found for the file type.
        """
        # Use the decompressed path to determine file type
        target_path = self._get_decompressed_path(file_path)

        for loader in self.loaders:
            if loader.can_handle(target_path):
                return loader

        raise ValueError(f"No suitable loader found for file: {file_path}")

    def load_file(self, file_path: str | Path) -> JSONObject:
        """
        Load a file, handling gzip decompression and format detection.

        Args:
            file_path: Path to the file to load

        Returns:
            Parsed content as dict, list, or other appropriate type

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If no suitable loader is found
            json.JSONDecodeError: If JSON parsing fails
            yaml.YAMLError: If YAML parsing fails
            OSError: If file reading fails
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            content = self._read_file_content(path)
            loader = self._get_appropriate_loader(path)
            return loader.load(content)
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise TypeError(f"Failed to parse {path}: {e}") from e
        except OSError as e:
            raise OSError(f"Failed to read file {path}: {e}") from e


def load_file(file_path: str | Path) -> JSONObject:
    """
    Convenience function to load a file with automatic format detection and gzip
    support.

    Args:
        file_path: Path to the file to load (.json, .yaml, .yml, optionally .gz
        compressed)

    Returns:
        Parsed content as dict, list, or other appropriate type
    """
    processor = FileProcessor()
    return processor.load_file(file_path)
