"""
Where forward references are used in a Pydantic model the model can be built
without all its dependencies. This module rebuilds all models in a module.
"""

import inspect
import sys
from types import ModuleType

from pydantic import BaseModel


def resolve_forward_references(module: ModuleType):
    """
    Rebuilds all Pydantic models within a given module.

    Args:
        module: The module to be rebuilt
    """

    models: dict[str, type[BaseModel]] = {}

    for _, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, BaseModel):
            models.update({obj.__name__: obj})

    for _, model in models.items():
        # Temporarily modify the model's module globals
        model_module = sys.modules[model.__module__]
        original_dict = dict(model_module.__dict__)
        model_module.__dict__.update(models)

        try:
            model.model_rebuild()
        finally:
            # Restore original globals
            model_module.__dict__.clear()
            model_module.__dict__.update(original_dict)
