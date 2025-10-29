"""
Where forward references are used in a Pydantic model the model can be built
without all its dependencies. This module rebuilds all models in a module.
"""

import inspect
import sys
import typing
from collections import defaultdict
from types import ModuleType

from pydantic import BaseModel


class ModelDependencyResolver:
    """
    Resolves cyclic dependencies in Pydantic models using topological sort with
    SCC detection.
    """

    def __init__(self):
        self.models: dict[str, type[BaseModel]] = {}
        self.dependencies: dict[str, set[str]] = defaultdict(set)
        self.graph: dict[str, list[str]] = defaultdict(list)

    def register_model(self, model: type[BaseModel]) -> None:
        """Register a Pydantic model for dependency analysis."""
        self.models[model.__name__] = model

    @staticmethod
    def extract_all_references(annotation: typing.Any, refs: set[str] | None = None):
        """
        Recursively extract all ForwardRef and type references from an annotation.

        Args:
            annotation: A type annotation (potentially deeply nested)
            refs: Set to accumulate references (used internally for recursion)

        Returns:
            Set of either ForwardRef objects or actual type/class objects
        """
        if refs is None:
            refs = set()

        # Direct ForwardRef
        if isinstance(annotation, typing.ForwardRef):
            refs.add(annotation.__forward_arg__)
            return refs

        # Direct class reference
        if isinstance(annotation, type):
            refs.add(annotation.__name__)
            return refs

        for origin in typing.get_args(annotation):
            ModelDependencyResolver.extract_all_references(origin, refs)

        return refs

    def _analyze_model_dependencies(self, model: type[BaseModel]) -> set[str]:
        """Analyze a single model's dependencies from its annotations."""
        dependencies: set[str] = set()

        for field_info in model.model_fields.values():
            references = ModelDependencyResolver.extract_all_references(
                field_info.annotation
            )

            dependencies.update(ref for ref in references if ref in self.models)

        return dependencies

    def build_dependency_graph(self) -> None:
        """Build the dependency graph for all registered models."""
        self.dependencies.clear()
        self.graph.clear()

        for model_name, model in self.models.items():
            deps = self._analyze_model_dependencies(model)
            self.dependencies[model_name] = deps

    def _tarjan_scc(self) -> list[list[str]]:
        """Find strongly connected components using Tarjan's algorithm."""
        index_counter = [0]
        stack: list[str] = []
        lowlinks: dict[str, int] = {}
        index: dict[str, int] = {}
        on_stack = {}
        sccs: list[list[str]] = []

        def strongconnect(node: str) -> None:
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True

            if lowlinks[node] == index[node]:
                component: list[str] = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    component.append(w)
                    if w == node:
                        break
                sccs.append(component)

        for node in self.models:
            if node not in index:
                strongconnect(node)

        return sccs

    def get_rebuild_order(self) -> list[list[str]]:
        """
        Get the order in which models should be rebuilt.
        Returns a list of lists, where each inner list contains models that can be
        rebuilt together.
        """
        self.build_dependency_graph()
        return self._tarjan_scc()

    def rebuild_models(self) -> None:
        """Rebuild all registered models in the correct dependency order."""
        rebuild_order = self.get_rebuild_order()

        for _, phase_models in enumerate(rebuild_order):
            for model_name in phase_models:
                model = self.models[model_name]

                # Temporarily modify the model's module globals
                model_module = sys.modules[model.__module__]
                original_dict = dict(model_module.__dict__)
                model_module.__dict__.update(self.models)

                try:
                    model.model_rebuild()
                finally:
                    # Restore original globals
                    model_module.__dict__.clear()
                    model_module.__dict__.update(original_dict)
                    model_module.__dict__.update(self.models)


def resolve_forward_references(module: ModuleType):
    """
    Rebuilds all Pydantic models within a given module.

    Args:
        module: The module to be rebuilt
    """

    resolver = ModelDependencyResolver()

    for _, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, BaseModel):
            resolver.register_model(obj)

    resolver.rebuild_models()
