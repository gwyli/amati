"""Generic factories to add repetitive validators to Pydantic models."""

from collections.abc import Iterable, Sequence
from numbers import Number
from typing import Any

from pydantic import model_validator
from pydantic._internal._decorators import (
    ModelValidatorDecoratorInfo,
    PydanticDescriptorProxy,
)

from amati._logging import Logger
from amati.validators.generic import GenericObject


class UnknownValue:
    """
    Sentinel singleton to represent the existence of a value.
    """

    _instance = None

    def __new__(cls) -> UnknownValue:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:  # pragma: no cover
        return "UNKNOWN"

    def __str__(self) -> str:  # pragma: no cover
        return "UNKNOWN"


UNKNOWN = UnknownValue()


def is_truthy_with_numeric_zero(value: Any) -> bool:
    """Checks if a variable is truthy, treating numeric zero as truthy.

    This function follows standard Python truthiness rules with one exception:
    any numeric value that equals 0 (e.g., `0`, `0.0`, `0j`) is considered
    truthy, rather than falsy.

    Args:
      value: The variable to test for truthiness. Can be of any type.

    Returns:
      True if the variable is truthy according to the custom rules, False otherwise.

    Example:
        >>> is_truthy_with_numeric_zero(0)
        True
        >>> is_truthy_with_numeric_zero(1)
        True
        >>> is_truthy_with_numeric_zero(0.0)
        True
        >>> is_truthy_with_numeric_zero([])
        False
        >>> is_truthy_with_numeric_zero("Hello")
        True
        >>> is_truthy_with_numeric_zero(None)
        False
    """
    # Check if the value is a number and if it's equal to zero.
    # numbers.Number is used to cover integers, floats, complex numbers, etc.
    if isinstance(value, Number):
        return True
    # For all other cases, revert to standard Python's bool() conversion.
    return bool(value)


def _get_candidates(
    self: GenericObject, fields: Sequence[str] | None
) -> dict[str, Any]:
    """
    Helper function to filter down the list of fields of a model to examine.
    """

    model_fields: dict[str, Any] = self.model_dump()

    options: Sequence[str] = fields or list(model_fields.keys())

    return {
        name: value
        for name, value in model_fields.items()
        if not name.startswith("_") and name in options
    }


def at_least_one_of(
    fields: Sequence[str] | None = None,
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

    Example:
        >>> Logger.logs = []
        >>>
        >>> class User(GenericObject):
        ...     name: str = ""
        ...     email: str = None
        ...     _at_least_one_of = at_least_one_of()
        ...     _reference_uri = "https://example.com"
        ...
        >>> user = User()
        >>> assert len(Logger.logs) == 1
        >>> Logger.logs = []

        >>> class User(GenericObject):
        ...     name: str = ""
        ...     email: str = None
        ...     age: int = None
        ...     _at_least_one_of = at_least_one_of(fields=["name", "email"])
        ...     _reference_uri = "https://example.com"
        ...
        >>>
        >>> user = User(name="John")  # Works fine
        >>> assert not Logger.logs
        >>> user = User()
        >>> assert len(Logger.logs) == 1
        >>> user = User(age=30)
        >>> assert len(Logger.logs) == 2


    Note:
        Only public fields (not starting with '_') are checked. Private fields
        and computed fields are ignored in the validation.
    """

    # Create the validator function with proper binding
    @model_validator(mode="after")
    def validate_at_least_one(self: GenericObject) -> Any:
        """Validate that at least one public field is non-empty."""

        # Early return if no fields exist
        if not (candidates := _get_candidates(self, fields)):
            return self

        # Check if at least one public field has a truthy value
        for value in candidates.values():
            if is_truthy_with_numeric_zero(value):
                return self

        public_fields = ", ".join(f"{name}" for name in candidates)

        msg = f"{public_fields} do not have values, expected at least one."
        Logger.log(
            {
                "msg": msg,
                "type": "value_error",
                "loc": (self.__class__.__name__,),
                "input": candidates,
                "url": self._reference_uri,  # type: ignore
            }
        )

        return self

    return validate_at_least_one


def only_one_of(
    fields: Sequence[str] | None = None,
    type_: str | None = "value_error",
) -> PydanticDescriptorProxy[ModelValidatorDecoratorInfo]:
    """Factory that adds validation to ensure one public field is non-empty.

    This factory adds a Pydantic model validator that checks all public fields
    (fields not starting with underscore) or a specified subset, and raises
    a ValueError if more than one, or none, of them contain truthy values.

    Args:
        fields: Optional sequence of field names to check. If provided, only these
            fields will be validated. If not provided, all public fields will be
            checked.
        type_: Optional string specifying the type of error to log.
            Defaults to "value_error".

    Returns:
        The validator that ensures at one public field is non-empty.

    Example:
        >>> Logger.logs = []
        >>>
        >>> class User(GenericObject):
        ...     email: str = ""
        ...     name: str = ""
        ...     _only_one_of = only_one_of()
        ...     _reference_uri = "https://example.com"
        ...
        >>> user = User(email="test@example.com")  # Works fine
        >>> user = User(name="123-456-7890")  # Works fine
        >>> assert not Logger.logs
        >>> user = User(email="a@b.com", name="123")
        >>> assert Logger.logs
        >>> Logger.logs = []

        >>> class User(GenericObject):
        ...     name: str = ""
        ...     email: str = ""
        ...     age: int = None
        ...     _only_one_of = only_one_of(["name", "email"])
        ...     _reference_uri = "https://example.com"
        ...
        >>> user = User(name="Bob")  # Works fine
        >>> user = User(email="test@example.com")  # Works fine
        >>> user = User(name="Bob", age=30)  # Works fine
        >>> assert not Logger.logs
        >>> user = User(name="Bob", email="a@b.com")
        >>> assert len(Logger.logs) == 1
        >>> user = User(age=30)
        >>> assert len(Logger.logs) == 2

    Note:
        Only public fields (not starting with '_') are checked. Private fields
        and computed fields are ignored in the validation.
    """

    @model_validator(mode="after")
    def validate_only_one(self: GenericObject) -> Any:
        """Validate that at most one public field is non-empty."""

        # Early return if no fields exist
        if not (candidates := _get_candidates(self, fields)):
            return self

        truthy: list[str] = []

        # Store fields with a truthy value
        for name, value in candidates.items():
            if is_truthy_with_numeric_zero(value):
                truthy.append(name)

        if len(truthy) != 1:
            field_string = ", ".join(truthy) if truthy else "none"

            msg = f"Expected at most one field to have a value, {field_string} did"

            Logger.log(
                {
                    "msg": msg,
                    "type": type_ or "value_error",
                    "loc": (self.__class__.__name__,),
                    "input": candidates,
                    "url": self._reference_uri,  # type: ignore
                }
            )

        return self

    return validate_only_one


def all_of(
    fields: Sequence[str] | None = None,
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

    Example:
        >>> Logger.logs = []
        >>>
        >>> class User(GenericObject):
        ...     email: str = ""
        ...     name: str = ""
        ...     _all_of = all_of()
        ...     _reference_uri = "https://example.com"
        ...
        >>> user = User(email="a@b.com", name="123") # Works fine
        >>> assert not Logger.logs
        >>> user = User(email="test@example.com")
        >>> assert len(Logger.logs) == 1
        >>> user = User(name="123-456-7890")
        >>> assert len(Logger.logs) == 2

        >>> class User(GenericObject):
        ...     name: str = ""
        ...     email: str = ""
        ...     age: int = None
        ...     _all_of = all_of(["name", "email"])
        ...     _reference_uri = "https://example.com"
        ...
        >>> Logger.logs = []
        >>> user = User(name="Bob", email="a@b.com") # Works fine
        >>> assert not Logger.logs
        >>> user = User(name="Bob")
        >>> assert len(Logger.logs) == 1
        >>> user = User(email="test@example.com")
        >>> assert len(Logger.logs) == 2
        >>> user = User(age=30)
        >>> assert len(Logger.logs) == 3
        >>> user = User(name="Bob", age=30)
        >>> assert len(Logger.logs) == 4

    Note:
        Only public fields (not starting with '_') are checked. Private fields
        and computed fields are ignored in the validation.
    """

    @model_validator(mode="after")
    def validate_only_one(self: GenericObject) -> Any:
        """Validate that at most one public field is non-empty."""

        # Early return if no fields exist
        if not (candidates := _get_candidates(self, fields)):
            return self

        falsy: list[str] = []

        # Store fields with a falsy value
        for name, value in candidates.items():
            if not is_truthy_with_numeric_zero(value):
                falsy.append(name)

        if falsy:
            msg = f"Expected at all fields to have a value, {', '.join(falsy)} did not"

            Logger.log(
                {
                    "msg": msg,
                    "type": "value_error",
                    "loc": (self.__class__.__name__,),
                    "input": candidates,
                    "url": self._reference_uri,  # type: ignore
                }
            )

        return self

    return validate_only_one


def if_then(
    conditions: dict[str, Any] | None = None,
    consequences: dict[str, Any | UnknownValue] | None = None,
) -> PydanticDescriptorProxy[ModelValidatorDecoratorInfo]:
    """Factory that adds validation to ensure if-then relationships between fields.

    This factory adds a Pydantic model validator that checks if certain field conditions
    are met, and if so, validates that other fields have specific values. This creates
    an if-then relationship between model fields.

    Args:
        conditions: Dictionary mapping field names to their required values that trigger
            the validation. All conditions must be met for the consequences to be
            checked.
        consequences: Dictionary mapping field names to their required values that must
            be true when the conditions are met.

    Returns:
        A validator that ensures the if-then relationship between fields is maintained.

    Raises:
        ValueError: If a condition and consequence are not present

    Example:
        >>> Logger.logs = []
        >>>
        >>> class User(GenericObject):
        ...     role: str = ""
        ...     can_edit: bool = False
        ...     _if_admin = if_then(
        ...         conditions={"role": "admin"},
        ...         consequences={"can_edit": True}
        ...     )
        ...     _reference_uri = "https://example.com"
        ...
        >>> user = User(role="admin", can_edit=True)  # Works fine
        >>> assert not Logger.logs
        >>> user = User(role="admin", can_edit=False)  # Fails validation
        >>> assert len(Logger.logs) == 1
        >>> user = User(role="user", can_edit=False)  # Works fine
        >>> assert len(Logger.logs) == 1
    """

    @model_validator(mode="after")
    def validate_if_then(self: GenericObject) -> GenericObject:
        if not conditions or not consequences:
            raise ValueError(
                "A condition and a consequence must be "
                f"present to validate {self.__class__.__name__}"
            )

        model_fields: dict[str, Any] = self.model_dump()

        candidates = {k: v for k, v in model_fields.items() if k in conditions}

        for k, v in candidates.items():
            # Unfulfilled condition
            if conditions[k] not in (v, UNKNOWN):
                return self

            # None and UNKNOWN are opposites
            if v is None and conditions[k] == UNKNOWN:
                return self

        for field, value in consequences.items():
            actual = model_fields.get(field)

            if (iterable := isinstance(value, Iterable)) and actual in value:
                continue

            if value == UNKNOWN and is_truthy_with_numeric_zero(actual):
                continue

            if value == actual:
                continue

            Logger.log(
                {
                    "msg": f"Expected {field} to be {'in ' if iterable else ''}"
                    f"{value} found {actual}",
                    "type": "value_error",
                    "loc": (self.__class__.__name__,),
                    "input": candidates,
                    "url": self._reference_uri,  # type: ignore
                }
            )

        return self

    return validate_if_then
