from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel

from amati._references import URICollectorMixin, URIReference, URIRegistry
from amati.fields import URI
from tests.strategies import uri_strategy


@pytest.fixture
def clean_registry():
    """Provide a clean registry instance."""
    registry = URIRegistry.get_instance()
    registry.reset()
    return registry


@given(uri_strategy())
def test_uri_field_registration_with_valid_context(uri: URI):
    """Verifies register() called with correct URIReference
    containing uri, source_document, field name, and model class."""

    register = URIRegistry.get_instance()
    register.reset()

    class TestModel(URICollectorMixin, BaseModel):
        ref: URI

    TestModel.model_validate(
        {"ref": uri},
        context={"current_document": "/path/to/doc.json"},
    )

    references = register.get_all_references()

    assert len(references) == 1
    assert isinstance(references[0], URIReference)
    assert references[0].source_document == Path("/path/to/doc.json")
    assert references[0].source_field == "ref"
    assert references[0].source_model_name == "TestModel"
    assert references[0].target_model == TestModel


@given(uri_strategy())
def test_no_registration_when_context_is_none(uri: URI):
    """Verifies register() is never called when __context is None."""

    register = URIRegistry.get_instance()
    register.reset()

    class TestModel(URICollectorMixin, BaseModel):
        ref: URI

    TestModel.model_validate({"ref": uri}, context=None)

    assert len(register.get_all_references()) == 0, (
        "No references should be registered when context is None"
    )


@given(uri_strategy())
def test_no_registration_when_current_document_missing(uri: URI):
    """Verifies register() is never called when context
    lacks 'current_document' key."""

    register = URIRegistry.get_instance()
    register.reset()

    class TestModel(URICollectorMixin, BaseModel):
        ref: URI

    TestModel.model_validate({"ref": uri}, context={"some_other_key": "value"})

    assert len(register.get_all_references()) == 0, (
        "No references should be registered without current_document"
    )


@given(uri_strategy())
def test_multiple_uri_fields_all_registered(uri: URI):
    """Verifies register() called once per URI field
    with correct field names."""

    register = URIRegistry.get_instance()
    register.reset()

    class TestModel(URICollectorMixin, BaseModel):
        ref1: URI
        ref2: URI
        ref3: URI

    TestModel.model_validate(
        {
            "ref1": uri,
            "ref2": uri,
            "ref3": uri,
        },
        context={"current_document": "/path/to/doc.json"},
    )

    references = register.get_all_references()

    assert len(references) == 3, "All three URI fields should be registered"  # noqa: PLR2004
    field_names = {ref.source_field for ref in references}
    assert field_names == {"ref1", "ref2", "ref3"}, (
        "All field names should be registered"
    )


@given(uri_strategy())
def test_none_field_values_are_skipped(uri: URI):
    """Concrete example verifying fields set to None don't trigger
    registration attempts."""

    register = URIRegistry.get_instance()
    register.reset()

    class TestModel(URICollectorMixin, BaseModel):
        ref1: URI | None = None
        ref2: URI
        ref3: URI | None = None

    TestModel.model_validate(
        {"ref1": None, "ref2": uri, "ref3": None},
        context={"current_document": "/path/to/doc.json"},
    )

    references = register.get_all_references()

    assert len(references) == 1, "Only non-None URI fields should be registered"
    assert references[0].source_field == "ref2"


@given(uri_strategy())
def test_non_uri_fields_are_ignored(uri: URI):
    """Concrete example verifying string/int fields that aren't URI instances
    don't get registered."""

    register = URIRegistry.get_instance()
    register.reset()

    class TestModel(URICollectorMixin, BaseModel):
        ref: URI
        name: str
        age: int
        description: str | None = None

    model = TestModel.model_validate(
        {
            "ref": uri,
            "name": "Test Name",
            "age": 42,
            "description": "A description",
        },
        context={"current_document": "/path/to/doc.json"},
    )

    references = register.get_all_references()

    assert len(references) == 1, "Only URI fields should be registered"
    assert references[0].source_field == "ref"

    assert model.name == "Test Name"
    assert model.age == 42  # noqa: PLR2004
    assert model.description == "A description"


def test_model_dump_serialization_doesnt_impede_uri_detection():
    """Concrete test demonstrating that model_dump() returns serialized
    data with actual types, not breaking isinstance checks."""

    register = URIRegistry.get_instance()
    register.reset()

    class TestModel(URICollectorMixin, BaseModel):
        ref: URI

    uri_value = URI("http://example.com/resource")

    model = TestModel.model_validate(
        {"ref": uri_value}, context={"current_document": "/path/to/doc.json"}
    )

    dumped = model.model_dump()
    assert isinstance(dumped["ref"], URI)

    references = register.get_all_references()
    assert len(references) == 1


def test_super_model_post_init_called():
    """Concrete test to verify mixin properly chains to parent initialization."""

    class ParentModel(BaseModel):
        def model_post_init(self, __context: dict[str, Any]) -> None:
            super().model_post_init(__context)
            self._parent_init_called = True

    class TestModel(URICollectorMixin, ParentModel):
        ref: URI

    model = TestModel.model_validate(
        {"ref": "http://example.com/resource"},
        context={"current_document": "/path/to/doc.json"},
    )

    assert hasattr(model, "_parent_init_called"), (
        "Parent model_post_init should have been called"
    )
    assert model._parent_init_called is True  # pyright: ignore[reportPrivateUsage]


def test_compatibility_with_multiple_mixins():
    """Integration test without mocks verifying correct behavior when URICollectorMixin
    is combined with other mixins in inheritance chain."""

    class OtherMixin(BaseModel):
        def model_post_init(self, __context: dict[str, Any]) -> None:
            super().model_post_init(__context)
            self._other_mixin_executed = True

    class TestModel(URICollectorMixin, OtherMixin):
        ref: URI
        name: str

    model = TestModel.model_validate(
        {"ref": "http://example.com/resource", "name": "test"},
        context={"current_document": "/path/to/doc.json"},
    )

    assert hasattr(model, "_other_mixin_executed"), "Other mixin should have executed"
    assert model._other_mixin_executed is True  # pyright: ignore[reportPrivateUsage]

    assert model.name == "test"
    assert model.ref is not None


@given(
    context_dict=st.one_of(
        st.none(),
        st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.one_of(
                st.none(),
                st.text(),
                st.integers(),
                st.lists(st.text()),
                st.dictionaries(st.text(), st.text()),
            ),
            max_size=10,
        ),
    )
)
def test_arbitrary_context_dictionaries_dont_crash(context_dict: dict[str, Any] | None):
    """Property-based test generating arbitrary dictionaries to verify graceful
    handling without crashes regardless of context structure."""

    registry = URIRegistry.get_instance()
    registry.reset()

    class TestModel(URICollectorMixin, BaseModel):
        ref: URI | None = None
        name: str = "default"

    model = TestModel.model_validate({"name": "test"}, context=context_dict)
    assert model is not None
    assert model.name == "test"


def test_path_vs_string_for_current_document():
    """Concrete examples without mocks verifying both Path objects and string paths
    work correctly in context."""

    class TestModel(URICollectorMixin, BaseModel):
        ref: URI

    register = URIRegistry.get_instance()
    register.reset()

    TestModel.model_validate(
        {"ref": "http://example.com/resource"},
        context={"current_document": "/path/to/doc.json"},
    )

    references_after_first = register.get_all_references()
    first_count = len(references_after_first)

    TestModel.model_validate(
        {"ref": "http://example.com/resource2"},
        context={"current_document": Path("/path/to/other.json")},
    )

    all_references = register.get_all_references()

    assert len(all_references) == first_count + 1, (
        "Both string and Path should behave consistently"
    )

    for uri_ref in all_references:
        assert isinstance(uri_ref.source_document, Path), (
            "source_document should be converted to Path"
        )
