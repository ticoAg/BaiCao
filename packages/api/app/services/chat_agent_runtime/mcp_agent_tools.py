from __future__ import annotations

import inspect
from json import loads
from typing import Any

from mcp.client import Client
from pydantic_ai import Tool


def _annotation(prop: dict[str, Any]) -> Any:
    if "anyOf" in prop:
        variants = [item for item in prop["anyOf"] if item.get("type") != "null"]
        if variants:
            return _annotation(variants[0]) | None
        return Any
    kind = prop.get("type")
    if kind == "string":
        return str
    if kind == "integer":
        return int
    if kind == "number":
        return float
    if kind == "boolean":
        return bool
    if kind == "array":
        return list[Any]
    if kind == "object":
        return dict[str, Any]
    return Any


def _payload_from_call(result: Any) -> Any:
    structured = getattr(result, "structured_content", None)
    if structured is not None:
        return structured
    content = getattr(result, "content", None) or []
    if not content:
        return {}
    text = getattr(content[0], "text", None)
    if not text:
        return {}
    try:
        return loads(text)
    except ValueError:
        return {"text": text}


async def schema_json_from_client(client: Client) -> str:
    result = await client.read_resource("graph://schema")
    for item in result.contents:
        text = getattr(item, "text", None)
        if text:
            return str(text)
    return "{}"


async def tools_from_mcp_client(client: Client) -> list[Tool]:
    listed = await client.list_tools()
    tools: list[Tool] = []
    for spec in listed.tools:
        schema = spec.input_schema or {}
        properties = schema.get("properties") or {}
        required = set(schema.get("required") or [])
        parameters: list[inspect.Parameter] = []
        for name, prop in properties.items():
            fields = prop if isinstance(prop, dict) else {}
            default = inspect.Parameter.empty if name in required else fields.get("default", None)
            parameters.append(
                inspect.Parameter(
                    name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    default=default,
                    annotation=_annotation(fields),
                )
            )

        def _bind(bound_name: str):
            async def _call(**kwargs: Any) -> Any:
                return _payload_from_call(await client.call_tool(bound_name, kwargs))

            return _call

        _call = _bind(spec.name)
        _call.__name__ = spec.name
        _call.__doc__ = spec.description or spec.name
        _call.__signature__ = inspect.Signature(parameters, return_annotation=dict)
        _call.__annotations__ = {item.name: item.annotation for item in parameters} | {"return": dict}
        tools.append(
            Tool(
                _call,
                takes_ctx=False,
                name=spec.name,
                description=spec.description,
            )
        )
    return tools
