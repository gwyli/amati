"""Types for use across all fields"""

from typing import Any, Self

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class Str(str):
    """
    A custom string subclass that can be used with Pydantic.

    Str extends the built-in string type and implements the necessary methods for
    Pydantic validation and schema generation. It allows for custom string validation
    while maintaining compatibility with Pydantic's type system.

    The primary goal behind Str is to allow logic in models to access metadata about
    the string, created during class instantiation, but to still treat the string as a
    string for the purposes of JSON/YAML parsing and serialisation.

    Inherits:
        str: Python's built-in string class
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls: type[Self], _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """
        Define how Pydantic should handle this custom type.

        This method is called by Pydantic during model creation to determine
        how to validate and process fields of this type. It creates a chain
        schema that first validates the input as a string, then applies
        custom validation logic.

        Args:
            _source_type (Any): The source type annotation.
            _handler (GetCoreSchemaHandler): Pydantic's schema handler.

        Returns:
            core_schema.CoreSchema: A schema defining how Pydantic should
                process this type.
        """
        return core_schema.chain_schema(
            [
                # First validate as a string
                core_schema.str_schema(),
                # Then convert to our Test type and run validation
                core_schema.no_info_plain_validator_function(cls.validate),
            ]
        )

    @classmethod
    def validate(cls: type[Self], value: str) -> Self:
        """
        Perform custom validation on the string value.

        This method is called after the basic string validation has passed. It allows
        implementing custom validation rules or transformations before returning an
        instance of the _Str class or a subclass. It is expected that subclasses will
        override validate() if necessary.

        Args:
            value (str): The string value to validate.

        Returns:
            Str: An instance of the _Str class containing the validated value.
        """

        return cls(value)
