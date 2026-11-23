"""Tiny dependency-free placeholder resolver for generated prose.

Templates use ``{{dotted.path|format_spec}}``.  Paths address nested mappings
and sequences; the optional format spec is passed to :func:`format`, with a few
convenience modes (``join``, ``pct``, ``raw``).  Rendering fails loudly on an
unknown path or an unresolved placeholder so a stale number cannot slip into
the paper.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

PLACEHOLDER = re.compile(r"\{\{\s*([^{}|]+?)\s*(?:\|\s*([^{}]+?)\s*)?\}\}")


class TemplateError(ValueError):
    """Raised when a placeholder cannot be resolved or formatted."""


def resolve(context: Mapping[str, Any], path: str) -> Any:
    current: Any = context
    for part in path.split("."):
        if isinstance(current, Mapping):
            if part not in current:
                raise TemplateError(f"unknown template path {path!r} at {part!r}")
            current = current[part]
        elif isinstance(current, Sequence) and not isinstance(current, (str, bytes)):
            try:
                current = current[int(part)]
            except (ValueError, IndexError) as exc:
                raise TemplateError(f"bad sequence index {part!r} in {path!r}") from exc
        else:
            raise TemplateError(f"cannot descend into {type(current).__name__} at {part!r} in {path!r}")
    return current


def stringify(value: Any, spec: str | None) -> str:
    if spec in {None, ""}:
        if isinstance(value, (list, tuple)):
            return ", ".join(str(v) for v in value)
        if isinstance(value, bool):
            return "yes" if value else "no"
        if value is None:
            return "n/a"
        return str(value)
    spec = spec.strip()
    if spec in {"join", "csv"}:
        return ", ".join(str(v) for v in value)
    if spec == "pct":
        return f"{100.0 * float(value):.2f}%"
    if spec == "raw":
        return str(value)
    try:
        return format(value, spec)
    except (TypeError, ValueError) as exc:
        raise TemplateError(f"cannot format {value!r} with spec {spec!r}") from exc


def render(text: str, context: Mapping[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        path, spec = match.group(1), match.group(2)
        return stringify(resolve(context, path), spec)

    out = PLACEHOLDER.sub(replace, text)
    if "{{" in out or "}}" in out:
        start = out.find("{{")
        if start < 0:
            start = out.find("}}")
        raise TemplateError(f"unresolved placeholder near: {out[max(0, start - 40):start + 80]!r}")
    return out


def has_placeholder(text: str) -> bool:
    return bool(PLACEHOLDER.search(text))
