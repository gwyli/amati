"""
Where forward references are used in a Pydantic model the model can be built
without all its dependencies. This module rebuilds all models in a module.
"""

import inspect
import sys
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

    def register_models(self, models: list[type[BaseModel]]) -> None:
        """Register multiple Pydantic models."""
        for model in models:
            self.register_model(model)

    def _analyze_model_dependencies(self, model: type[BaseModel]) -> set[str]:
        """Analyze a single model's dependencies from its annotations."""
        dependencies: set[str] = set()

        for field_info in model.model_fields.values():

            # Use a magic value that's an invalid class name for getattr so if
            # there is no __name__ attribute it won't appear in self.models
            if (name := getattr(field_info.annotation, "__name__", "!")) in self.models:
                dependencies.update(name)

        return dependencies

    def build_dependency_graph(self) -> None:
        """Build the dependency graph for all registered models."""
        self.dependencies.clear()
        self.graph.clear()

        # First pass: collect all dependencies
        for model_name, model in self.models.items():
            deps = self._analyze_model_dependencies(model)
            self.dependencies[model_name] = deps

        # Second pass: build directed graph
        for model_name, deps in self.dependencies.items():
            for dep in deps:
                if dep in self.models:
                    # Build forward graph (dependency -> dependent)
                    self.graph[dep].append(model_name)

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

            for successor in self.graph[node]:
                if successor not in index:
                    strongconnect(successor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[successor])
                elif on_stack[successor]:
                    lowlinks[node] = min(lowlinks[node], index[successor])

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

    def _topological_sort_sccs(self, sccs: list[list[str]]) -> list[list[str]]:
        """Topologically sort the strongly connected components."""
        # Map each node to its SCC index
        node_to_scc = {node: i for i, scc in enumerate(sccs) for node in scc}

        # Find dependencies between SCCs
        dependencies: set[tuple[int, ...]] = set()
        for node in self.models:
            for neighbor in self.graph[node]:
                src_scc, dst_scc = node_to_scc[node], node_to_scc[neighbor]
                if src_scc != dst_scc:
                    dependencies.add((src_scc, dst_scc))

        # Count incoming edges for each SCC
        in_degree = [0] * len(sccs)
        for _, dst in dependencies:
            in_degree[dst] += 1

        # Process SCCs with no dependencies first
        ready = [i for i, deg in enumerate(in_degree) if deg == 0]
        result: list[list[str]] = []

        while ready:
            current = ready.pop()
            result.append(sccs[current])

            # Remove this SCC and update in-degrees
            for src, dst in dependencies:
                if src == current:
                    in_degree[dst] -= 1
                    if in_degree[dst] == 0:
                        ready.append(dst)

        return result

    def get_rebuild_order(self) -> list[list[str]]:
        """
        Get the order in which models should be rebuilt.
        Returns a list of lists, where each inner list contains models that can be
        rebuilt together.
        """
        self.build_dependency_graph()
        sccs = self._tarjan_scc()
        return self._topological_sort_sccs(sccs)

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
