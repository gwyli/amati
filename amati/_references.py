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

            netloc: Path | None = None
            if self.uri.authority:
                netloc = Path(self.uri.authority)

            if self.uri.host and not netloc:
                netloc = Path(self.uri.host)

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

        raise ValueError(f"Unknown URI type: {self.uri.type}")


class URIRegistry:
    """Thread-safe registry for discovered URIs"""

    _instance = None

    def __init__(self):
        self._uris: list[URIReference] = []
        self._processed: set[Path] = set()

    @classmethod
    def get_instance(cls) -> URIRegistry:
        if cls._instance is None:
            cls._instance = cls()

        return cls._instance

    def register(self, ref: URIReference):
        """Register a discovered URI"""
        self._uris.append(ref)

    def mark_processed(self, path: Path):
        """Mark a document as having been validated"""
        self._processed.add(path.resolve())

    def is_processed(self, path: Path) -> bool:
        """Check if a document has already been validated"""
        return path.resolve() in self._processed

    def get_all_references(self) -> list[URIReference]:
        """Get all discovered URI references"""
        return self._uris.copy()

    def reset(self):
        """Reset for a new validation run"""
        self._uris.clear()
        self._processed.clear()


class URICollectorMixin(BaseModel):
    """Mixin for GenericModel to collect URIs during validation"""

    def model_post_init(self, __context: dict[str, Any]) -> None:
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
                    source_model_name=self.__class__.__qualname__,
                    source_field=field_name,
                    # The linked document should be validated with the same model type
                    target_model=self.__class__,
                )
                URIRegistry.get_instance().register(ref)
