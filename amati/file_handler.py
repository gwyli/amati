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

import gzip
import json
from abc import ABC, abstractmethod
from pathlib import Path

import yaml

type JSONPrimitive = str | int | float | bool | None
type JSONArray = list["JSONValue"]
type JSONObject = dict[str, "JSONValue"]
type JSONValue = JSONPrimitive | JSONArray | JSONObject


class FileLoader(ABC):
    """Abstract base class for file loaders."""

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Check if this loader can handle the given file."""
        pass

    @abstractmethod
    def load(self, content: str) -> JSONObject:
        """Load and parse the file content."""
        pass


class JSONLoader(FileLoader):
    """Loader for JSON files."""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in {".json", ".js"}

    def load(self, content: str) -> JSONObject:
        return json.loads(content)


class YAMLLoader(FileLoader):
    """Loader for YAML files."""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in {".yaml", ".yml"}

    def load(self, content: str) -> JSONObject:
        return yaml.safe_load(content)


class FileProcessor:
    """Main processor for handling gzipped and regular files."""

    def __init__(self) -> None:
        self.loaders: list[FileLoader] = [JSONLoader(), YAMLLoader()]

    def _is_gzip_file(self, file_path: Path) -> bool:
        """Check if file is gzipped by reading magic bytes."""
        try:
            with open(file_path, "rb") as f:
                magic = f.read(2)
                return magic == b"\x1f\x8b"
        except (IOError, OSError):
            return False

    def _get_decompressed_path(self, file_path: Path) -> Path:
        """Get the path without .gz extension for determining file type."""
        if file_path.suffix.lower() == ".gz":
            return file_path.with_suffix("")
        return file_path

    def _read_file_content(self, file_path: Path) -> str:
        """Read file content, decompressing if necessary."""
        if self._is_gzip_file(file_path):
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                return f.read()
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

    def _get_appropriate_loader(self, file_path: Path) -> FileLoader:
        """Get the appropriate loader for the file type."""
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
        except (IOError, OSError) as e:
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
