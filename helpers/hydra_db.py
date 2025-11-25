import os
from typing import Any, Iterable, Sequence

import psycopg
from psycopg import sql
from psycopg.rows import dict_row


def _dsn() -> str:
    """
    Build the DSN for connecting to the Hydra/Postgres CSV database.

    Defaults target the local stack described in the README (Hydra on localhost:5434).
    Environment variables allow overriding each component when needed.
    """
    host = os.getenv("HYDRA_DB_HOST", "127.0.0.1")
    port = int(os.getenv("HYDRA_DB_PORT", "5434"))
    user = os.getenv("HYDRA_DB_USER", "postgres")
    password = os.getenv("HYDRA_DB_PASSWORD", "postgres")
    database = os.getenv("HYDRA_DB_NAME", "postgres")
    return f"host={host} port={port} user={user} password={password} dbname={database}"


async def _ensure_connection(
    connection: psycopg.AsyncConnection | None,
) -> tuple[psycopg.AsyncConnection, bool]:
    """
    Return an open async connection plus a flag indicating whether we created it.
    """
    if connection is not None:
        return connection, False
    conn = await psycopg.AsyncConnection.connect(_dsn(), row_factory=dict_row)
    return conn, True


async def fetch(
    query: str,
    *args: Any,
    connection: psycopg.AsyncConnection | None = None,
) -> list[dict[str, Any]]:
    """
    Run a SELECT-like query and return rows as list of dicts.
    """
    conn, owned = await _ensure_connection(connection)
    try:
        async with conn.cursor() as cur:
            await cur.execute(query, args or None)
            rows = await cur.fetchall()
            return list(rows)
    finally:
        if owned:
            await conn.close()


async def fetchrow(
    query: str,
    *args: Any,
    connection: psycopg.AsyncConnection | None = None,
) -> dict[str, Any] | None:
    """
    Run a query expecting a single row.
    """
    conn, owned = await _ensure_connection(connection)
    try:
        async with conn.cursor() as cur:
            await cur.execute(query, args or None)
            row = await cur.fetchone()
            return dict(row) if row else None
    finally:
        if owned:
            await conn.close()


async def execute(
    query: str,
    *args: Any,
    connection: psycopg.AsyncConnection | None = None,
) -> str:
    """
    Execute a statement (INSERT/UPDATE/DELETE). Returns psycopg status string.
    """
    conn, owned = await _ensure_connection(connection)
    try:
        async with conn.cursor() as cur:
            await cur.execute(query, args or None)
            await conn.commit()
            return cur.statusmessage or ""
    finally:
        if owned:
            await conn.close()


async def executemany(
    query: str,
    args_iterable: Iterable[Sequence[Any]],
    connection: psycopg.AsyncConnection | None = None,
) -> None:
    """
    Execute the same statement with multiple argument sets (bulk insert/update).
    """
    conn, owned = await _ensure_connection(connection)
    try:
        async with conn.cursor() as cur:
            await cur.executemany(query, args_iterable)
            await conn.commit()
    finally:
        if owned:
            await conn.close()


async def get_table_name_for_resource(
    resource_id: str,
    connection: psycopg.AsyncConnection | None = None,
) -> str | None:
    """
    Find the table name for a given resource_id by querying tables_index.

    Args:
        resource_id: The resource ID to look up
        connection: Optional existing connection (creates one if not provided)

    Returns:
        The table name if found, None otherwise
    """
    row = await fetchrow(
        "SELECT parsing_table FROM tables_index WHERE resource_id = %s",
        resource_id,
        connection=connection,
    )
    return row["parsing_table"] if row else None


async def explore_table(
    table_name: str,
    limit: int = 100,
    offset: int = 0,
    connection: psycopg.AsyncConnection | None = None,
) -> dict[str, Any]:
    """
    Explore a table by fetching rows with pagination.

    Args:
        table_name: Name of the table to explore (can include schema, e.g., "schema.table")
        limit: Maximum number of rows to return (default: 100)
        offset: Number of rows to skip (default: 0)
        connection: Optional existing connection (creates one if not provided)

    Returns:
        Dict with 'rows' (list of dicts), 'count' (total row count), 'limit', 'offset'

    Raises:
        psycopg.errors.UndefinedTable: If the table doesn't exist
    """
    conn, owned = await _ensure_connection(connection)
    try:
        # Split table name into parts (schema.table or just table)
        parts = table_name.split(".")
        identifiers = [sql.Identifier(part) for part in parts]

        # Build queries using sql.Identifier for safe identifier quoting
        count_query = sql.SQL("SELECT COUNT(*) as count FROM {}").format(
            sql.SQL(".").join(identifiers)
        )
        select_query = sql.SQL("SELECT * FROM {} LIMIT %s OFFSET %s").format(
            sql.SQL(".").join(identifiers)
        )

        # Get total count
        async with conn.cursor() as cur:
            await cur.execute(count_query)
            count_row = await cur.fetchone()
            total_count = count_row["count"] if count_row else 0

            # Get paginated rows
            await cur.execute(select_query, (limit, offset))
            rows = await cur.fetchall()

        return {
            "rows": list(rows),
            "count": total_count,
            "limit": limit,
            "offset": offset,
        }
    finally:
        if owned:
            await conn.close()


async def explore_resource(
    resource_id: str,
    limit: int = 100,
    offset: int = 0,
    connection: psycopg.AsyncConnection | None = None,
) -> dict[str, Any]:
    """
    Explore a resource by finding its table name and fetching rows.

    Args:
        resource_id: The resource ID to explore
        limit: Maximum number of rows to return (default: 100)
        offset: Number of rows to skip (default: 0)
        connection: Optional existing connection (creates one if not provided)

    Returns:
        Dict with 'resource_id', 'table_name', 'rows', 'count', 'limit', 'offset'
        Returns None for 'table_name' and empty 'rows' if resource not found

    Raises:
        ValueError: If resource_id is invalid
    """
    conn, owned = await _ensure_connection(connection)
    try:
        table_name = await get_table_name_for_resource(resource_id, connection=conn)

        if not table_name:
            return {
                "resource_id": resource_id,
                "table_name": None,
                "rows": [],
                "count": 0,
                "limit": limit,
                "offset": offset,
            }

        result = await explore_table(
            table_name, limit=limit, offset=offset, connection=conn
        )
        result["resource_id"] = resource_id
        result["table_name"] = table_name

        return result
    finally:
        if owned:
            await conn.close()
