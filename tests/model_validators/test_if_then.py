"""Tests for amati.model_validators.if_then"""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel

from amati import Reference
from amati.logging import LogMixin
from amati.model_validators import UNKNOWN, if_then


class ModelNoConditions(BaseModel):
    field: str = ""
    x = if_then()
    _reference: Reference = Reference(title="test")


class ModelWithConditions(BaseModel):
    role: str = ""
    permission: bool = False
    _if_then = if_then(conditions={"role": "admin"}, consequences={"permission": True})
    _reference: Reference = Reference(title="test")


class ModelWithMultipleConditions(BaseModel):
    role: str = ""
    department: str = ""
    can_approve: bool = False
    _if_then = if_then(
        conditions={"role": "manager", "department": "finance"},
        consequences={"can_approve": True},
    )
    _reference: Reference = Reference(title="test")


# Add new test class after existing classes
class ModelWithUnknownConditions(BaseModel):
    role: str = ""
    permission: bool = False
    notify: bool = False
    _if_then = if_then(
        conditions={"role": "admin"},
        consequences={"permission": True, "notify": UNKNOWN},
    )
    _reference: Reference = Reference(title="test")


class ModelWithMultipleUnknownConditions(BaseModel):
    role: str = ""
    department: str = ""
    can_approve: bool = False
    can_edit: bool = False
    _if_then = if_then(
        conditions={"role": "manager", "department": "finance"},
        consequences={"can_approve": True, "can_edit": UNKNOWN},
    )
    _reference: Reference = Reference(title="test")


class ModelWithIterableConditions(BaseModel):
    role: str = ""
    status: str = ""
    _if_then = if_then(
        conditions={"role": "admin"}, consequences={"status": ["active", "pending"]}
    )
    _reference: Reference = Reference(title="test")


class ModelWithMultipleIterableConditions(BaseModel):
    role: str = ""
    department: str = ""
    status: str = ""
    level: int = 0
    _if_then = if_then(
        conditions={"role": "manager", "department": "finance"},
        consequences={"status": ["active", "pending"], "level": [1, 2, 3]},
    )
    _reference: Reference = Reference(title="test")


def test_missing_conditions_consequences():
    """Test that validator raises error when conditions/consequences missing."""
    with pytest.raises(ValueError) as exc:
        ModelNoConditions()
    assert "A condition and a consequence must be present" in str(exc.value)


def test_conditions_not_met():
    """Test that validation passes when conditions are not met."""
    with LogMixin.context():
        model = ModelWithConditions(role="user", permission=False)
        assert not LogMixin.logs
        assert model.role == "user"
        assert model.permission is False


def test_conditions_met_valid():
    """Test that validation passes when conditions are met and consequences valid."""
    with LogMixin.context():
        model = ModelWithConditions(role="admin", permission=True)
        assert not LogMixin.logs
        assert model.role == "admin"
        assert model.permission is True


def test_conditions_met_invalid():
    """Test that validation fails when conditions met but consequences invalid."""
    with LogMixin.context():
        ModelWithConditions(role="admin", permission=False)
        assert len(LogMixin.logs) == 1
        assert "Expected permission to be True found False" in LogMixin.logs[0].message


@given(role=st.sampled_from(["admin", "user", ""]), permission=st.booleans())
def test_property_based(role: str, permission: bool):

    with LogMixin.context():
        ModelWithConditions(role=role, permission=permission)

        if role == "admin" and not permission:
            assert len(LogMixin.logs) == 1
            assert "Expected permission to be True" in LogMixin.logs[0].message
        else:
            assert len(LogMixin.logs) == 0


def test_multiple_conditions_all_met_valid():
    """Test validation passes when all conditions are met and consequences valid."""
    with LogMixin.context():
        model = ModelWithMultipleConditions(
            role="manager", department="finance", can_approve=True
        )
        assert not LogMixin.logs
        assert model.role == "manager"
        assert model.department == "finance"
        assert model.can_approve is True


def test_multiple_conditions_all_met_invalid():
    """Test validation fails when all conditions met but consequences invalid."""
    with LogMixin.context():
        ModelWithMultipleConditions(
            role="manager", department="finance", can_approve=False
        )
        assert len(LogMixin.logs) == 1
        assert "Expected can_approve to be True found False" in LogMixin.logs[0].message


def test_multiple_conditions_partial_met():
    """Test validation passes when only some conditions are met."""
    with LogMixin.context():
        cases: list[dict[str, str | bool]] = [
            {"role": "manager", "department": "hr", "can_approve": False},
            {"role": "employee", "department": "finance", "can_approve": False},
            {"role": "employee", "department": "hr", "can_approve": False},
        ]

        for case in cases:
            model = ModelWithMultipleConditions(**case)  # type: ignore
            assert not LogMixin.logs
            assert model.role == case["role"]
            assert model.department == case["department"]
            assert model.can_approve is False


@given(
    role=st.sampled_from(["manager", "employee", "admin"]),
    department=st.sampled_from(["finance", "hr", "it"]),
    can_approve=st.booleans(),
)
def test_multiple_conditions_property_based(
    role: str, department: str, can_approve: bool
):
    """Property-based test for multiple conditions."""
    with LogMixin.context():
        ModelWithMultipleConditions(
            role=role, department=department, can_approve=can_approve
        )

        if role == "manager" and department == "finance" and not can_approve:
            assert len(LogMixin.logs) == 1
            assert "Expected can_approve to be True" in LogMixin.logs[0].message
        else:
            assert len(LogMixin.logs) == 0


# Add new test functions before property-based tests
def test_unknown_consequence_any_value():
    """Test that UNKNOWN consequence allows any value when conditions are met."""
    with LogMixin.context():
        # Should pass with notify=True
        model = ModelWithUnknownConditions(role="admin", permission=True, notify=True)
        assert not LogMixin.logs
        assert model.notify is True

        # Should also pass with notify=False
        model = ModelWithUnknownConditions(role="admin", permission=True, notify=False)
        assert not LogMixin.logs
        assert model.notify is False


def test_unknown_consequence_conditions_not_met():
    """Test that UNKNOWN consequence is ignored when conditions are not met."""
    with LogMixin.context():
        model = ModelWithUnknownConditions(role="user", permission=False, notify=False)
        assert not LogMixin.logs
        assert model.notify is False


def test_multiple_conditions_unknown_consequence():
    """Test multiple conditions with UNKNOWN consequence."""
    with LogMixin.context():
        # Should pass with can_edit=True
        model = ModelWithMultipleUnknownConditions(
            role="manager", department="finance", can_approve=True, can_edit=True
        )
        assert not LogMixin.logs
        assert model.can_edit is True

        # Should also pass with can_edit=False
        model = ModelWithMultipleUnknownConditions(
            role="manager", department="finance", can_approve=True, can_edit=False
        )
        assert not LogMixin.logs
        assert model.can_edit is False


# Add to existing property-based test or create new one
@given(
    role=st.sampled_from(["admin", "user"]),
    permission=st.booleans(),
    notify=st.booleans(),
)
def test_unknown_property_based(role: str, permission: bool, notify: bool):
    """Property-based test for UNKNOWN consequences."""
    with LogMixin.context():
        model = ModelWithUnknownConditions(
            role=role, permission=permission, notify=notify
        )

        if role == "admin" and not permission:
            assert len(LogMixin.logs) == 1
            assert "Expected permission to be True" in LogMixin.logs[0].message
        else:
            assert len(LogMixin.logs) == 0
            if role == "admin":
                # When conditions are met, notify can be any value
                assert model.notify == notify


# Add after existing test functions
def test_iterable_consequence_valid():
    """Test that validation passes when value is in iterable consequence."""
    with LogMixin.context():
        # Should pass with status in allowed values
        model = ModelWithIterableConditions(role="admin", status="active")
        assert not LogMixin.logs
        assert model.status == "active"

        model = ModelWithIterableConditions(role="admin", status="pending")
        assert not LogMixin.logs
        assert model.status == "pending"


def test_iterable_consequence_invalid():
    """Test that validation fails when value not in iterable consequence."""
    with LogMixin.context():
        ModelWithIterableConditions(role="admin", status="inactive")
        assert len(LogMixin.logs) == 1
        assert (
            "Expected status to be in ['active', 'pending'] found inactive"
            in LogMixin.logs[0].message
        )


def test_iterable_consequence_conditions_not_met():
    """Test that validation passes when conditions not met, regardless of value."""
    with LogMixin.context():
        model = ModelWithIterableConditions(role="user", status="whatever")
        assert not LogMixin.logs
        assert model.status == "whatever"


def test_multiple_iterable_consequences_valid():
    """Test that validation passes when all values are in their respective iterables."""
    with LogMixin.context():
        model = ModelWithMultipleIterableConditions(
            role="manager", department="finance", status="active", level=2
        )
        assert not LogMixin.logs
        assert model.status == "active"
        assert model.level == 2


def test_multiple_iterable_consequences_partial_invalid():
    """Test that validation fails when any value is not in its iterable."""
    with LogMixin.context():
        # Invalid status
        ModelWithMultipleIterableConditions(
            role="manager", department="finance", status="inactive", level=2
        )
        assert len(LogMixin.logs) == 1
        LogMixin.logs.clear()

        # Invalid level
        ModelWithMultipleIterableConditions(
            role="manager", department="finance", status="active", level=4
        )
        assert len(LogMixin.logs) == 1


@given(
    role=st.sampled_from(["admin", "user"]),
    status=st.sampled_from(["active", "pending", "inactive", "suspended"]),
)
def test_iterable_property_based(role: str, status: str):
    """Property-based test for iterable consequences."""
    with LogMixin.context():
        model = ModelWithIterableConditions(role=role, status=status)

        if role == "admin" and status not in ["active", "pending"]:
            assert len(LogMixin.logs) == 1
            assert (
                f"Expected status to be in ['active', 'pending'] found {status}"
                in LogMixin.logs[0].message
            )
        else:
            assert len(LogMixin.logs) == 0
            if role == "admin":
                assert model.status in ["active", "pending"]


def test_if_then_none_unknown_condition():
    """Test if_then when a field is None but condition expects UNKNOWN."""

    class ConditionalModel(BaseModel):
        status: str | None = None
        result: bool = False
        _if_then = if_then(
            conditions={"status": UNKNOWN}, consequences={"result": True}
        )
        _reference: Reference = Reference(title="test")

    with LogMixin.context():
        ConditionalModel()
        assert not LogMixin.logs  # Should early return due to None vs UNKNOWN check


def test_if_then_unfulfilled_condition():
    """Test if_then when a field is None but condition expects UNKNOWN."""

    class ConditionalModel(BaseModel):
        status: str = "Present"
        result: bool = False
        _if_then = if_then(
            conditions={"status": "Not Present"}, consequences={"result": True}
        )
        _reference: Reference = Reference(title="test")

    with LogMixin.context():
        ConditionalModel()
        assert not LogMixin.logs
