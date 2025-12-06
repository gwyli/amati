from pathlib import Path

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st
from pydantic import BaseModel

from amati._references import URIReference
from amati.fields import URI, URIType
from tests.strategies import (
    absolute_paths,
    json_pointers,
    network_path_uris,
    pydantic_models,
    relative_paths,
    relative_uris,
)


class TestURIReferenceResolveExamples:
    """Example-based tests for URIReference.resolve() with concrete scenarios"""

    def test_relative_uri_simple_sibling(self) -> None:
        """Relative URI to sibling file resolves correctly"""
        uri_ref: URIReference = URIReference(
            uri=URI("sibling.json"),
            source_document=Path("/project/schemas/main.json"),
            source_model_name="MainModel",
            source_field="ref_field",
            target_model=BaseModel,
        )

        assert uri_ref.resolve() == Path("/project/schemas/sibling.json")

    def test_relative_uri_parent_directory(self) -> None:
        """Relative URI with parent traversal resolves correctly"""
        uri_ref: URIReference = URIReference(
            uri=URI("../sibling.json"),
            source_document=Path("/project/schemas/main.json"),
            source_model_name="MainModel",
            source_field="ref_field",
            target_model=BaseModel,
        )

        assert uri_ref.resolve() == Path("/project/sibling.json")

    def test_relative_uri_subdirectory(self) -> None:
        """Relative URI to subdirectory resolves correctly"""
        uri_ref: URIReference = URIReference(
            uri=URI("components/types.json"),
            source_document=Path("/project/schemas/main.json"),
            source_model_name="MainModel",
            source_field="ref_field",
            target_model=BaseModel,
        )

        assert uri_ref.resolve() == Path("/project/schemas/components/types.json")

    def test_relative_uri_multiple_parent_traversal(self) -> None:
        """Relative URI with multiple parent traversals resolves correctly"""
        uri_ref: URIReference = URIReference(
            uri=URI("../../other/file.json"),
            source_document=Path("/a/b/c/doc.json"),
            source_model_name="MainModel",
            source_field="ref_field",
            target_model=BaseModel,
        )

        assert uri_ref.resolve() == Path("/a/other/file.json")

    def test_relative_uri_with_dot_current_dir(self) -> None:
        """Relative URI with ./current directory notation resolves correctly"""
        uri_ref: URIReference = URIReference(
            uri=URI("./sibling.json"),
            source_document=Path("/project/schemas/main.json"),
            source_model_name="MainModel",
            source_field="ref_field",
            target_model=BaseModel,
        )

        assert uri_ref.resolve() == Path("/project/schemas/sibling.json")

    def test_absolute_file_path_returns_itself(self) -> None:
        """Absolute file path URIs resolve to themselves"""
        uri_ref: URIReference = URIReference(
            uri=URI("/absolute/path/file.json"),
            source_document=Path("/project/schemas/main.json"),
            source_model_name="MainModel",
            source_field="ref_field",
            target_model=BaseModel,
        )

        assert uri_ref.resolve() == Path("/project/schemas/absolute/path/file.json")

    def test_uri_with_http_scheme_raises_not_implemented(self) -> None:
        """HTTP URI with scheme should not be resolved relative to source"""
        uri_ref: URIReference = URIReference(
            uri=URI("http://example.com/schema.json"),
            source_document=Path("/project/schemas/main.json"),
            source_model_name="MainModel",
            source_field="ref_field",
            target_model=BaseModel,
        )

        with pytest.raises(NotImplementedError):
            uri_ref.resolve()

    def test_uri_with_file_scheme_not_resolved_relatively(self) -> None:
        """File URI with scheme should not be resolved relative to source"""
        uri_ref: URIReference = URIReference(
            uri=URI("file:///absolute/path/schema.json"),
            source_document=Path("/project/schemas/main.json"),
            source_model_name="MainModel",
            source_field="ref_field",
            target_model=BaseModel,
        )

        resolved: Path = uri_ref.resolve()

        assert resolved == Path("/absolute/path/schema.json"), (
            "Absolute URI resolved as whole path"
        )
        assert resolved != Path("/project/schemas/file:///absolute/path/schema.json")

    def test_network_path_uri_resolves_to_itself(self) -> None:
        """Network path URIs (//host/path) resolve to themselves"""
        uri_ref: URIReference = URIReference(
            uri=URI("//example.com/path/schema.json"),
            source_document=Path("/project/schemas/main.json"),
            source_model_name="MainModel",
            source_field="ref_field",
            target_model=BaseModel,
        )

        resolved: Path = uri_ref.resolve()

        # Network paths are absolute per RFC 3987
        assert resolved == Path("/example.com/path/schema.json")

    def test_pathless_uri_raises_value_error(self) -> None:
        """File URI without a path component should raise ValueError"""
        uri_ref: URIReference = URIReference(
            uri=URI("file://a.com"),
            source_document=Path("/project/schemas/main.json"),
            source_model_name="MainModel",
            source_field="ref_field",
            target_model=BaseModel,
        )

        with pytest.raises(ValueError):
            uri_ref.resolve()


class TestURIReferenceResolveProperties:
    """Property-based tests for URIReference.resolve() invariants"""

    @given(
        uri=st.one_of(relative_uris(), network_path_uris()),
        source_document=absolute_paths(),
        source_model_name=st.text(min_size=1),
        source_field=st.text(min_size=1),
        target_model=pydantic_models(),
    )
    def test_resolve_is_idempotent(
        self,
        uri: URI,
        source_document: Path,
        source_model_name: str,
        source_field: str,
        target_model: type[BaseModel],
    ) -> None:
        """Calling resolve() multiple times should return the same result"""
        uri_ref: URIReference = URIReference(
            uri=uri,
            source_document=source_document,
            source_model_name=source_model_name,
            source_field=source_field,
            target_model=target_model,
        )

        first_resolve: Path = uri_ref.resolve()
        second_resolve: Path = uri_ref.resolve()
        third_resolve: Path = uri_ref.resolve()

        assert first_resolve == second_resolve == third_resolve

    @given(
        uri=st.one_of(relative_uris(), network_path_uris(), json_pointers()),
        source_document=st.one_of(absolute_paths(), relative_paths()),
        source_model_name=st.text(min_size=1),
        source_field=st.text(min_size=1),
        target_model=pydantic_models(),
    )
    def test_resolve_always_returns_path(
        self,
        uri: URI,
        source_document: Path,
        source_model_name: str,
        source_field: str,
        target_model: type[BaseModel],
    ) -> None:
        """resolve() should always return a Path object"""

        assume(not (uri.type == URIType.NETWORK_PATH and source_document.is_absolute()))
        uri_ref: URIReference = URIReference(
            uri=uri,
            source_document=source_document,
            source_model_name=source_model_name,
            source_field=source_field,
            target_model=target_model,
        )

        resolved: Path = uri_ref.resolve()

        assert isinstance(resolved, Path)

    @given(
        relative_uri=relative_uris(),
        source_document=st.one_of(absolute_paths(), relative_paths()),
        source_model_name=st.text(min_size=1),
        source_field=st.text(min_size=1),
        target_model=pydantic_models(),
    )
    def test_relative_uri_path_is_normalized(
        self,
        relative_uri: URI,
        source_document: Path,
        source_model_name: str,
        source_field: str,
        target_model: type[BaseModel],
    ) -> None:
        """Relative URI paths should be normalized (.. and . resolved)"""
        assume(relative_uri.type == URIType.RELATIVE)
        assume(relative_uri.scheme is None)

        uri_ref: URIReference = URIReference(
            uri=relative_uri,
            source_document=source_document,
            source_model_name=source_model_name,
            source_field=source_field,
            target_model=target_model,
        )

        resolved: Path = uri_ref.resolve()

        assert resolved.is_absolute(), "Resolved path should be absolute (normalized)"

        assert ".." not in resolved.parts
        assert "." not in resolved.parts

    @given(
        relative_uri=relative_uris(),
        source_document=absolute_paths(),
        source_model_name=st.text(min_size=1),
        source_field=st.text(min_size=1),
        target_model=pydantic_models(),
    )
    def test_relative_uri_not_resolved_from_cwd(
        self,
        relative_uri: URI,
        source_document: Path,
        source_model_name: str,
        source_field: str,
        target_model: type[BaseModel],
    ) -> None:
        """Relative URIs should NOT resolve from current working directory"""
        assume(relative_uri.type == URIType.RELATIVE)
        assume(relative_uri.scheme is None)
        assume(source_document.parent != Path.cwd())
        assume(relative_uri.path != "/")

        uri_ref: URIReference = URIReference(
            uri=relative_uri,
            source_document=source_document,
            source_model_name=source_model_name,
            source_field=source_field,
            target_model=target_model,
        )

        resolved: Path = uri_ref.resolve()
        cwd_resolved: Path = (Path.cwd() / relative_uri.lstrip("/")).resolve()

        if source_document.parent != Path.cwd():
            assert resolved != cwd_resolved, "Should be different if source not in cwd"

    @given(
        relative_uri=relative_uris(),
        source_document=absolute_paths(),
        source_model_name=st.text(min_size=1),
        source_field=st.text(min_size=1),
        target_model=pydantic_models(),
    )
    def test_relative_uri_not_resolved_from_source_document_itself(
        self,
        relative_uri: URI,
        source_document: Path,
        source_model_name: str,
        source_field: str,
        target_model: type[BaseModel],
    ) -> None:
        """Relative URIs should resolve from parent directory,
        not the document itself"""
        assume(relative_uri.type == URIType.RELATIVE)
        assume(relative_uri.scheme is None)
        assume(relative_uri.path != "/")

        uri_ref: URIReference = URIReference(
            uri=relative_uri,
            source_document=source_document,
            source_model_name=source_model_name,
            source_field=source_field,
            target_model=target_model,
        )

        resolved: Path = uri_ref.resolve()
        wrong_from_document: Path = (
            source_document / relative_uri.lstrip("/")
        ).resolve()

        if source_document.parent != source_document:
            assert resolved != wrong_from_document, (
                "Should NOT resolve from the document itself"
            )
