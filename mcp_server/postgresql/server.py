"""PostgreSQL MCP server — schema introspection and safe read queries."""

from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from mcp.server.fastmcp import FastMCP

from eai_platform.config import get_settings
from eai_platform.mcp_base import error_result, text_result

mcp = FastMCP(
    "postgresql",
    instructions=(
        "PostgreSQL integration for schema exploration and read-only SQL queries. "
        "Write operations are blocked for safety."
    ),
)

_engine: Engine | None = None

BLOCKED_KEYWORDS = frozenset(
    {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"}
)


def _get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database_sync_url, pool_pre_ping=True)
    return _engine


def _validate_read_only(sql: str) -> None:
    first_token = sql.strip().split()[0].upper() if sql.strip() else ""
    if first_token in BLOCKED_KEYWORDS:
        raise ValueError(f"Write operations are not allowed. Blocked keyword: {first_token}")
    if ";" in sql.strip().rstrip(";"):
        raise ValueError("Multiple statements are not allowed")


@mcp.tool()
def list_tables(schema: str = "public") -> str:
    """List all tables in the database schema."""
    try:
        inspector = inspect(_get_engine())
        tables = inspector.get_table_names(schema=schema)
        return text_result({"schema": schema, "tables": tables})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def describe_table(table_name: str, schema: str = "public") -> str:
    """Describe columns, types, and constraints for a table."""
    try:
        inspector = inspect(_get_engine())
        columns = inspector.get_columns(table_name, schema=schema)
        pk = inspector.get_pk_constraint(table_name, schema=schema)
        fks = inspector.get_foreign_keys(table_name, schema=schema)
        return text_result(
            {
                "table": table_name,
                "schema": schema,
                "columns": columns,
                "primary_key": pk,
                "foreign_keys": fks,
            }
        )
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def execute_query(sql: str, limit: int = 100) -> str:
    """Execute a read-only SQL query (SELECT only). Results are limited."""
    try:
        _validate_read_only(sql)
        wrapped = (
            f"SELECT * FROM ({sql.rstrip(';')}) AS _q LIMIT {limit}"
            if "LIMIT" not in sql.upper()
            else sql
        )
        with _get_engine().connect() as conn:
            result = conn.execute(text(wrapped))
            rows = [dict(row._mapping) for row in result]
            columns = list(result.keys()) if result.returns_rows else []
        return text_result({"columns": columns, "rows": rows, "count": len(rows)})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def get_table_stats(table_name: str, schema: str = "public") -> str:
    """Get row count and basic statistics for a table."""
    try:
        with _get_engine().connect() as conn:
            count_result = conn.execute(
                text(f'SELECT COUNT(*) AS row_count FROM "{schema}"."{table_name}"')
            )
            row_count = count_result.scalar()
        return text_result({"table": table_name, "schema": schema, "row_count": row_count})
    except Exception as exc:
        return error_result(str(exc))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
