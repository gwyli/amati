"""Test suite for URIRegistry class.

Tests cover singleton behavior, URI registration, path processing,
and state management using both concrete examples and property-based testing.
"""

import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from amati._references import URIReference, URIRegistry
from amati.fields import URI
from tests.strategies import (
    file_strategy,
    json_pointers,
    network_path_uris,
    pydantic_models,
    relative_paths,
    relative_uris,
)

uri_reference_strategy = st.builds(
    URIReference,
    uri=st.one_of(json_pointers(), network_path_uris(), relative_uris()).map(URI),
    source_document=file_strategy(),
    source_model_name=st.text(min_size=1, max_size=20),
    source_field=st.text(min_size=1, max_size=20),
    target_model=pydantic_models(),
)


def clean_registry() -> URIRegistry:
    """Provide a clean registry instance."""
    registry = URIRegistry.get_instance()
    registry.reset()
    return registry


class TestSingletonBehavior:
    """Tests for singleton pattern implementation."""

    def test_get_instance_returns_same_object(self):
        """Multiple calls to get_instance() should return the same object."""
        instance1 = URIRegistry.get_instance()
        instance2 = URIRegistry.get_instance()

        assert instance1 is instance2

    @given(uri_ref=uri_reference_strategy)
    def test_singleton_persists_state_across_calls(self, uri_ref: URIReference):
        """State changes should persist across get_instance() calls."""
        registry1 = clean_registry()
        registry2 = clean_registry()
        registry1 = URIRegistry.get_instance()
        registry1.register(uri_ref)

        registry2 = URIRegistry.get_instance()

        assert len(registry2.get_all_references()) == 1
        assert registry2.get_all_references() == [uri_ref]

    def test_direct_instantiation_creates_separate_instance(self):
        """Direct __init__ call creates a new instance (anti-pattern check)."""
        singleton = URIRegistry.get_instance()
        direct = URIRegistry()

        assert singleton is not direct

    @given(uri_ref=uri_reference_strategy)
    def test_singleton_state_not_shared_with_direct_instances(
        self, uri_ref: URIReference
    ):
        """Singleton and directly created instances have separate state."""
        singleton = URIRegistry.get_instance()
        direct = URIRegistry()

        singleton.register(uri_ref)

        assert len(direct.get_all_references()) == 0


class TestURIRegistration:
    """Tests for URI reference registration."""

    @given(uri_ref=uri_reference_strategy)
    def test_register_single_uri(self, uri_ref: URIReference):
        """Should register a single URI reference."""
        registry = clean_registry()

        registry.register(uri_ref)

        assert len(registry.get_all_references()) == 1
        assert registry.get_all_references()[0] == uri_ref

    @given(uri_refs=st.lists(uri_reference_strategy))
    def test_register_multiple_uris(self, uri_refs: list[URIReference]):
        """Should register multiple URI references in order."""
        registry = clean_registry()

        ref: URIReference
        for ref in uri_refs:
            registry.register(ref)

        assert registry.get_all_references() == uri_refs

    @given(uri_ref=uri_reference_strategy)
    def test_register_duplicate_uris(self, uri_ref: URIReference):
        """Should allow duplicate URI references (no deduplication)."""
        registry = clean_registry()

        registry.register(uri_ref)
        registry.register(uri_ref)

        assert len(registry.get_all_references()) == 2  # noqa: PLR2004

    @given(uri_ref=uri_reference_strategy)
    def test_get_all_references_returns_copy(self, uri_ref: URIReference):
        """get_all_references() should return a copy, not the internal list."""
        registry = clean_registry()
        registry.register(uri_ref)

        refs1 = registry.get_all_references()
        refs2 = registry.get_all_references()

        assert refs1 is not refs2
        assert refs1 == refs2

    @given(uri_ref=uri_reference_strategy)
    def test_external_modification_does_not_affect_registry(
        self, uri_ref: URIReference
    ):
        """Modifying returned list should not affect internal registry."""
        registry = clean_registry()
        registry.register(uri_ref)

        refs = registry.get_all_references()
        refs.append(uri_ref)

        assert len(registry.get_all_references()) == 1

    @given(uri_ref=uri_reference_strategy)
    def test_register_with_empty_registry(self, uri_ref: URIReference):
        """Should handle registration when registry is empty."""
        registry = clean_registry()

        assert len(registry.get_all_references()) == 0

        registry.register(uri_ref)

        assert len(registry.get_all_references()) == 1


class TestPathProcessing:
    """Tests for document path processing and tracking."""

    @given(tmp_path=file_strategy())
    def test_mark_processed_absolute_path(self, tmp_path: Path):
        """Should mark an absolute or relative path as processed."""
        registry = clean_registry()

        registry.mark_processed(tmp_path)

        assert registry.is_processed(tmp_path)

    @given(tmp_path=relative_paths())
    def test_mark_processed_relative_path(self, tmp_path: Path):
        """Should resolve relative paths to absolute before marking."""
        registry = clean_registry()

        abs_path = tmp_path.resolve()

        registry.mark_processed(tmp_path)

        assert registry.is_processed(abs_path)
        assert registry.is_processed(tmp_path)

    @given(tmp_path=file_strategy())
    def test_is_processed_processed_file(self, tmp_path: Path):
        """Should return False for files that haven't been processed."""
        registry = clean_registry()

        assert not registry.is_processed(tmp_path)

    def test_mark_processed_multiple_files(self):
        """Should track multiple processed files."""
        registry = clean_registry()

        with tempfile.TemporaryDirectory(delete=True) as tmp_dir:
            paths = [Path(tmp_dir) / f"file{i}.txt" for i in range(3)]

            for path in paths:
                registry.mark_processed(path)

        for path in paths:
            assert registry.is_processed(path)

    def test_mark_processed_nonexistent_file(self):
        """Should allow marking nonexistent files as processed."""
        registry = clean_registry()

        with tempfile.TemporaryFile() as tmp_file:
            path: Path = Path(str(tmp_file.name))

            registry.mark_processed(path)

        assert registry.is_processed(path)


class TestResolvable:
    """Tests for file existence checking."""

    def test_resolvable_existing_file(self):
        """Should return True for existing files."""
        registry = clean_registry()

        with tempfile.NamedTemporaryFile(delete_on_close=True) as tmp_file:
            assert registry.resolvable(Path(str(tmp_file.name)))

    def test_resolvable_nonexistent_file(self):
        """Should return False for nonexistent files."""
        registry = clean_registry()

        with tempfile.TemporaryFile() as tmp_file:
            path: Path = Path(str(tmp_file.name))

        assert not registry.resolvable(path)

    def test_resolvable_directory(self):
        """Should return False for directories."""
        registry = clean_registry()

        with tempfile.TemporaryDirectory(delete=True) as tmp_dir:
            assert not registry.resolvable(Path(tmp_dir))


class TestReset:
    """Tests for registry reset functionality."""

    @given(uri_refs=st.lists(uri_reference_strategy))
    def test_reset_clears_all_instances(self, uri_refs: list[URIReference]):
        """Should clear all registered URIs."""
        registry1 = clean_registry()
        registry2 = clean_registry()

        for ref in uri_refs:
            registry1.register(ref)
            registry2.register(ref)

        registry1.reset()

        assert len(registry1.get_all_references()) == 0
        assert len(registry2.get_all_references()) == 0

        for ref in uri_refs:
            assert not registry1.is_processed(ref.resolve())
            assert not registry2.is_processed(ref.resolve())

    @given(uri_ref=uri_reference_strategy)
    def test_reset_clears_both_uris_and_paths(self, uri_ref: URIReference):
        """Should clear both URIs and processed paths."""
        registry = clean_registry()

        registry.register(uri_ref)

        registry.mark_processed(uri_ref.resolve())

        registry.reset()

        assert len(registry.get_all_references()) == 0
        assert not registry.is_processed(uri_ref.resolve())

    @given(uri_ref1=uri_reference_strategy, uri_ref2=uri_reference_strategy)
    def test_reset_allows_reuse(
        self,
        uri_ref1: URIReference,
        uri_ref2: URIReference,
    ):
        """Should allow registry reuse after reset."""
        registry = clean_registry()

        registry.register(uri_ref1)
        registry.reset()

        registry.register(uri_ref2)

        refs = registry.get_all_references()
        assert len(refs) == 1
        assert refs[0] == uri_ref2

    def test_empty_registry_reset(self):
        """Should handle reset on empty registry without errors."""
        registry = clean_registry()

        registry.reset()

        assert len(registry.get_all_references()) == 0


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_registry_state(self):
        """New registry should start empty."""
        registry = clean_registry()

        assert len(registry.get_all_references()) == 0
        assert not registry.is_processed(Path("any/path"))

    def test_register_none_raises_error(self):
        """Should handle None registration appropriately."""
        registry = clean_registry()

        with pytest.raises(TypeError):
            registry.register(None)  # type: ignore
