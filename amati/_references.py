from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from amati.fields import URI, URIType


@dataclass(frozen=True)
class URIReference:
    """Immutable record of a URI found during validation"""

    uri: URI
    source_document: Path
    source_model_name: str  # Just the string name for error reporting
    source_field: str
    target_model: type[BaseModel]  # The model type to validate with

    def resolve(self) -> Path:
        """Resolve URI relative to source document, see
        https://spec.openapis.org/oas/v3.1.1.html#relative-references-in-api-description-uris
        """

        if self.uri.scheme == "file":
            if not self.uri.path:
                raise ValueError("File URI must have a path component")

            netloc: Path | None = (
                Path(self.uri.authority)
                if self.uri.authority
                else Path(self.uri.host)
                if self.uri.host
                else None
            )

            return (
                (netloc / self.uri.path).resolve()
                if netloc
                else Path(self.uri.path).resolve()
            )

        if self.uri.type == URIType.ABSOLUTE:
            raise NotImplementedError("Absolute URI resolution not implemented")

        if self.uri.type == URIType.NETWORK_PATH:
            return Path(self.uri).resolve()

        if self.uri.type == URIType.RELATIVE:
            path: Path = self.source_document.parent / self.uri.lstrip("/")
            return path.resolve()

        if self.uri.type == URIType.JSON_POINTER:
            path: Path = self.source_document.parent / self.uri.lstrip("#/")
            return path.resolve()

        # Guard against future changes
        raise ValueError(f"Unknown URI type: {self.uri.type}")  # pragma: no cover


class URIRegistry:
    """Registry for discovered URIs using the Singleton pattern.

    This class maintains a central registry of all URI references discovered
    during document validation. It tracks both the URIs themselves and which
    documents have already been processed to avoid duplicate validation.

    Attributes:
        _instance: Class-level singleton instance.
        _uris: List of all registered URI references.
        _processed: Set of file paths that have been validated.
    """

    _instance = None

    def __init__(self):
        """Initialize a new URIRegistry instance.

        Note:
            This should not be called directly. Use get_instance() instead
            to obtain the singleton instance.
        """
        self._uris: list[URIReference] = []
        self._processed: set[Path] = set()

    @classmethod
    def get_instance(cls) -> URIRegistry:
        """Get or create the singleton instance of URIRegistry.

        Returns:
            URIRegistry: The singleton instance of the registry.
        """
        if cls._instance is None:
            cls._instance = cls()

        return cls._instance

    def register(self, ref: URIReference):
        """Register a discovered URI reference.

        Args:
            ref (URIReference): The URI reference to register, including
                source document, and target model.
        """

        if not isinstance(ref, URIReference):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("ref must be an instance of URIReference")

        self._uris.append(ref)

    def mark_processed(self, path: Path):
        """Mark a document as having been validated.

        The path is resolved to an absolute path before storage to ensure
        consistent tracking regardless of how the path was specified.

        Args:
            path (Path): The file path of the document that has been processed.
        """
        self._processed.add(path.resolve())

    def is_processed(self, path: Path) -> bool:
        """Check if a document has already been validated.

        Args:
            path (Path): The file path to check.

        Returns:
            bool: True if the document has been processed, False otherwise.
        """
        return path.resolve() in self._processed

    def get_all_references(self) -> list[URIReference]:
        """Get all discovered URI references.

        Returns:
            list[URIReference]: A copy of the list of all registered URI
                references. Returns a copy to prevent external modification
                of the internal registry.
        """
        return self._uris.copy()

    def resolvable(self, path: Path) -> bool:
        """Check if the file referenced by a URI exists.

        Args:
            path (Path): The file path to verify.

        Returns:
            bool: True if the path points to an existing file, False otherwise.
        """
        return path.is_file()

    def reset(self):
        """Reset the registry for a new validation run.

        Clears all registered URIs and processed document records. This is
        typically called at the beginning of a new validation session.
        """
        self._uris.clear()
        self._processed.clear()


class URICollectorMixin(BaseModel):
    """Mixin for Pydantic models to automatically collect URIs during validation.

    This mixin hooks into the Pydantic model lifecycle to automatically
    discover and register URI fields during model instantiation. It inspects
    all fields after validation and registers any URI-type fields with the
    URIRegistry for subsequent processing.

    The mixin expects a 'current_document' key in the validation context
    to track the source document for each URI reference.
    """

    def model_post_init(self, __context: dict[str, Any]) -> None:
        """Post-initialization hook to collect URI references from model fields.

        This method is automatically called by Pydantic after model validation
        is complete. It inspects all fields for URI types and registers them
        with the singleton URIRegistry.

        Args:
            __context (dict[str, Any]): Validation context dictionary. Expected
                to contain a 'current_document' key with the path to the source
                document being validated.

        Note:
            This method calls super().model_post_init() to ensure compatibility
            with other mixins and the base model's initialization process.

        Example:
            Context should be passed during model instantiation:
            >>> class MyModel(URICollectorMixin, BaseModel):
            ...     ref: URI
            >>> model = MyModel.model_validate(
            ...     {"ref": "http://example.com/resource"},
            ...     context={"current_document": "/path/to/doc.json"}
            ... )
        """
        super().model_post_init(__context)

        if not __context:
            return

        current_doc = __context.get("current_document")
        if not current_doc:
            return

        # Inspect all fields for URI types
        for field_name, field_value in self.model_dump().items():
            if field_value is None:
                continue

            # Check if this field contains a URI
            # Adjust this check based on your URI type implementation
            if isinstance(field_value, URI):
                ref = URIReference(
                    uri=field_value,
                    source_document=Path(current_doc),
                    source_model_name=self.__class__.__name__,
                    source_field=field_name,
                    # The linked document should be validated with the same model type
                    target_model=self.__class__,
                )
                URIRegistry.get_instance().register(ref)
