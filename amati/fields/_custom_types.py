"""Types for use across all fields"""

from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class _Str(str):
    """
    A custom string subclass that can be used with Pydantic.

    _Str extends the built-in string type and implements the necessary methods for
    Pydantic validation and schema generation. It allows for custom string validation
    while maintaining compatibility with Pydantic's type system.

    The primary goal behind _Str is to allow logic in models to access metadata about
    the string, created during class instantiation, but to still treat the string as a
    string for the purposes of JSON/YAML parsing and serialisation.

    Inherits:
        str: Python's built-in string class
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
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
    def validate(cls, value: str) -> "_Str":
        """
        Perform custom validation on the string value.

        This method is called after the basic string validation has passed. It allows
        implementing custom validation rules or transformations before returning an
        instance of the _Str class or a subclass. It is expected that subclasses will
        override validate() if necessary.

        Args:
            value (str): The string value to validate.

        Returns:
            _Str: An instance of the _Str class containing the validated value.
        """

        return cls(value)


class _Any(Any):
    """
    A custom Any subclass that can be used with Pydantic.
    _Any extends the built-in Any type and implements the necessary methods for
    Pydantic validation and schema generation. It allows for custom validation
    according to the type of the object passed to the Any constructor,
    while maintaining compatibility with Pydantic's type system.
    The primary goal behind _Any is to allow logic in models to access metadata about
    the object, created during class instantiation, but to still treat the object
    correctly for the purposes of JSON/YAML parsing and serialisation.
    """

    def __new__(cls, *args, **kwargs):

        obj = super().__new__(cls, *args, **kwargs)

        if len(args) != 1:
            raise ValueError

        cls_type = type(args[0]).__name__

        obj._pydantic_core_schema_generator(cls_type)
        return obj

    @classmethod
    def _pydantic_core_schema_generator(cls, cls_type: str):
        """
        Adds the method __get_pydantic_core_schema__ to the class during
        instantiation, using the correct schema handler according to the
        type of the passed value.
        Args:
            cls_type (str): The type of the value given to the constructor.
        """

        schema_handler = getattr(core_schema, f"{cls_type}_schema")

        def _pydantic_core_schema(
            cls, _source_type: Any, _handler: GetCoreSchemaHandler
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
                    schema_handler(),
                    # Then convert to our Test type and run validation
                    core_schema.no_info_plain_validator_function(cls.validate),
                ]
            )

        setattr(cls, "__get_pydantic_core_schema__", classmethod(_pydantic_core_schema))

    @classmethod
    def validate(cls, value: Any) -> "_Any":
        """
        Perform custom validation on the value.
        This method is called after the basic validation has passed. It allows
        implementing custom validation rules or transformations before returning an
        instance of the _Any class or a subclass. It is expected that subclasses will
        override validate() if necessary.
        Args:
            value (Any): The value to validate.
        Returns:
            _Any: An instance of the _Any class containing the validated value.
        """

        return cls(value)
