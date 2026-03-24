from urllib.parse import urlsplit, urlunsplit

from neomodel import adb

from ..core.config import get_settings


def build_neomodel_url(uri: str, user: str, password: str) -> str:
    parsed = urlsplit(uri)
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    netloc = f"{user}:{password}@{host}{port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


async def init_kg_db() -> None:
    settings = get_settings()
    await adb.set_connection(
        build_neomodel_url(
            settings.neo4j_uri,
            settings.neo4j_user,
            settings.neo4j_password,
        )
    )


async def cypher_query(query: str, params: dict | None = None):
    return await adb.cypher_query(query, params or {})


async def cypher_rows(query: str, params: dict | None = None) -> list[dict]:
    rows, meta = await cypher_query(query, params)
    columns = [item[0] if isinstance(item, tuple) else item for item in meta or []]
    if not columns:
        return []
    return [dict(zip(columns, row, strict=False)) for row in rows]


async def cypher_single(query: str, params: dict | None = None) -> dict | None:
    rows = await cypher_rows(query, params)
    return rows[0] if rows else None
