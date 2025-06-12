"""Generic factories to add repetitive validators to Pydantic models."""

from typing import Any, Optional, Sequence

from pydantic import model_validator
from pydantic._internal._decorators import (
    ModelValidatorDecoratorInfo,
    PydanticDescriptorProxy,
)

from amati import AmatiValueError
from amati.validators.generic import GenericObject


def at_least_one(
    fields: Optional[Sequence[str]] = None,
) -> PydanticDescriptorProxy[ModelValidatorDecoratorInfo]:
    """Factory that adds validation to ensure at least one public field is non-empty.

    This factory adds a Pydantic model validator that checks all public fields
    (fields not starting with underscore) and raises the specified exception if
    none of them contain truthy values.

    Args:
        fields: Optional sequence of field names to check. If provided, only these
            fields will be validated. If not provided, all public fields will be
            checked.

    Returns:
        The validator that ensures at least one public field is non-empty.

    Raises:
        ValueError: If all public fields are empty after initialization.

    Example:
        >>> class User(GenericObject):
        ...     name: str = ""
        ...     email: str = ""
        ...     _at_least_one = at_least_one()
        ...
        >>> user = User()
        Traceback (most recent call last):
        pydantic_core._pydantic_core.ValidationError: message
        >>> user = User(name="John")  # Works fine

        >>> class User(GenericObject):
        ...     name: str = ""
        ...     email: str = ""
        ...     age: int = None
        ...     _at_least_one = at_least_one(fields=["name", "email"])
        ...
        >>> user = User()
        Traceback (most recent call last):
        pydantic_core._pydantic_core.ValidationError: message
        >>> user = User(name="John")  # Works fine
        >>> user = User(age=30)
        Traceback (most recent call last):
        pydantic_core._pydantic_core.ValidationError: message


    Note:
        Only public fields (not starting with '_') are checked. Private fields
        and computed fields are ignored in the validation.
    """

    # Create the validator function with proper binding
    @model_validator(mode="after")
    def validate_at_least_one(self: GenericObject) -> Any:
        """Validate that at least one public field is non-empty."""

        model_fields: dict[str, Any] = self.model_dump()

        options: Sequence[str] = fields or list(model_fields.keys())

        candidates = {
            name: value
            for name, value in model_fields.items()
            if not name.startswith("_") and name in options
        }

        # Early return if no fields exist (edge case)
        if not candidates:
            return self

        # Check if at least one public field has a truthy value
        for value in candidates.values():
            if value:
                return self

        public_fields = "".join(f"{name}, " for name in candidates.keys())

        # If no public fields then exit
        if not public_fields:
            return self

        raise AmatiValueError(
            f"{public_fields} do not have values, expected at least one.",
            self._reference,  # pylint: disable=protected-access # type: ignore
        )

    return validate_at_least_one


def only_one(
    fields: Optional[Sequence[str]] = None,
) -> PydanticDescriptorProxy[ModelValidatorDecoratorInfo]:
    """Factory that adds validation to ensure at most one public field is non-empty.

    This factory adds a Pydantic model validator that checks all public fields
    (fields not starting with underscore) or a specified subset, and raises
    a ValueError if more than one of them contain truthy values.

    Args:
        fields: Optional sequence of field names to check. If provided, only these
            fields will be validated. If not provided, all public fields will be
            checked.

    Returns:
        The validator that ensures at most one public field is non-empty.

    Raises:
        ValueError: If more than one public field (or specified field) is non-empty
            after initialization.

    Example:
        >>> class User(GenericObject):
        ...     email: str = ""
        ...     name: str = ""
        ...     _only_one = only_one()
        ...
        >>> user = User(email="test@example.com")  # Works fine
        >>> user = User(name="123-456-7890")  # Works fine
        >>> user = User(email="a@b.com", name="123")
        Traceback (most recent call last):
        pydantic_core._pydantic_core.ValidationError: message

        >>> class User(GenericObject):
        ...     name: str = ""
        ...     email: str = ""
        ...     age: int = None
        ...     _only_one = only_one(["name", "email"])
        ...
        >>> user = User(name="Bob")  # Works fine
        >>> user = User(email="test@example.com")  # Works fine
        >>> user = User(name="Bob", email="a@b.com")
        Traceback (most recent call last):
        pydantic_core._pydantic_core.ValidationError: message
        >>> user = User(age=30)
        Traceback (most recent call last):
        pydantic_core._pydantic_core.ValidationError: message
        >>> user = User(name="Bob", age=30)  # Works fine

    Note:
        Only public fields (not starting with '_') are checked. Private fields
        and computed fields are ignored in the validation.
    """

    @model_validator(mode="after")
    def validate_only_one(self: GenericObject) -> Any:
        """Validate that at most one public field is non-empty."""

        model_fields: dict[str, Any] = self.model_dump()

        options: Sequence[str] = fields or list(model_fields.keys())

        candidates = {
            name: value
            for name, value in model_fields.items()
            if not name.startswith("_") and name in options
        }

        # Early return if no fields exist (edge case)
        if not candidates:
            return self

        truthy: list[str] = []

        # Store fields with a truthy value
        for name, value in candidates.items():
            if value:
                truthy.append(name)

        if len(truthy) != 1:
            msg = f"Expected at most one field to have a value, {", ".join(truthy)} did"
            raise AmatiValueError(
                msg,
                self._reference,  # pylint: disable=protected-access # type: ignore
            )

        return self

    return validate_only_one
