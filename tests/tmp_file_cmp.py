"""Easily compare two files. Currently temporary."""

import json
import pathlib
import sys

import yaml

from amati import _resolve_forward_references
from amati.validators import oas311

if __name__ == "__main__":

    new = pathlib.Path("tests/data/out.json")
    old_sorted = pathlib.Path("tests/data/in.json")
    old = pathlib.Path(sys.argv[1])

    with open(old, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    _resolve_forward_references.resolve_forward_references(oas311)

    model = oas311.OpenAPIObject(**data)

    output = json.dumps(
        json.loads(model.model_dump_json(exclude_unset=True, by_alias=True)),
        sort_keys=True,
    )

    with new.open("w", encoding="utf-8") as f:
        f.write(output)

    with old_sorted.open("w", encoding="utf-8") as f:
        f.write(json.dumps(data, sort_keys=True))
