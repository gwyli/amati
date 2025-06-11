"""Generic factories to add repetitive validators to Pydantic models."""

from typing import Any, Optional, Sequence
from pydantic import BaseModel, model_validator
from pydantic._internal._decorators import (
    PydanticDescriptorProxy,
    ModelValidatorDecoratorInfo,
)

ExceptionType = type[Exception]


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
        >>> class UserModel(BaseModel):
        ...     name: str = ""
        ...     email: str = ""
        ...     _at_least_one = at_least_one()
        ...
        >>> user = UserModel()  # Raises ValueError
        >>> user = UserModel(name="John")  # Works fine

        >>> class UserModel(BaseModel):
        ...     name: str = ""
        ...     email: str = ""
        ...     age: int = None
        ...     _at_least_one = at_least_one(fields=["name", "email"])
        ...
        >>> user = UserModel()  # Raises ValueError
        >>> user = UserModel(name="John")  # Works fine
        >>> user = UserModel(age=30) # Raises ValueError


    Note:
        Only public fields (not starting with '_') are checked. Private fields
        and computed fields are ignored in the validation. The validator runs
        after all other field validation and model construction.
    """

    # Create the validator function with proper binding
    @model_validator(mode="after")
    def validate_at_least_one(self: BaseModel) -> Any:
        """Validate that at least one public field is non-empty."""

        model_fields: dict[str, Any] = self.model_dump()

        if fields:
            # Filter fields to only those specified in the `fields` argument
            model_fields = {
                name: model_fields[name] for name in fields if name in model_fields
            }

        # Early return if no fields exist (edge case)
        if not model_fields:
            return self

        public_fields: str = ""

        # Check if at least one public field has a truthy value
        for name, value in model_fields.items():
            if not name.startswith("_"):
                if value:
                    return self

                public_fields += f"{name}, "

        public_fields = public_fields.strip(", ")

        # If no public fields then exit
        if not public_fields:
            return self

        msg = f"{public_fields} are empty, expected at least one to be non-empty."

        raise ValueError(msg)

    return validate_at_least_one
