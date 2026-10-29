from __future__ import annotations

import re
from pprint import pprint

from sqlalchemy import (
    URL,
    MetaData,
    Selectable,
    Table,
    create_engine,
    inspect,
)

from .execution import QueryExecutor
from .reflection import ReflectedTable


class Database:
    """
    The main interface of AlchemyReflection for database reflection and query execution.
    Accepts SQLAlchemy connection URLs for supported database dialects,
    as well as raw ODBC connection strings for SQL Server.
    """
    def __init__(self, conn: str | URL):
        if (
            isinstance(conn, str)
            and not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", conn)
        ):
            conn = URL.create(
                "mssql+pyodbc",
                query={"odbc_connect": conn},
            )

        self.engine = create_engine(
            conn,
            pool_pre_ping=True,
        )
        self.metadata = MetaData()

    def reflect(self,source: str) -> ReflectedTable:
        """
        Reflect a database table or view into a ReflectedTable instance.
        Requires a schema-qualified table or view name.
        --------
        e.g.
        >>> db.reflect("someschema.sometable")
        """
        schema, separator, tablename = source.rpartition(".")

        if not separator or not schema or not tablename:
            raise ValueError("A schema-qualified table or view name is required")

        return (
            ReflectedTable(
                Table(
                    tablename,
                    self.metadata,
                    schema=schema,
                    autoload_with=self.engine,
                ),
                self,
            )
        )

    def query(
        self,
        statement: Selectable | ReflectedTable | str,
    ) -> QueryExecutor:
        """
        Create a QueryExecutor for query execution, row retrieval, and
        result conversion to pandas, Polars, NumPy, PyArrow, etc...
        Accepts raw SQL statements, SQLAlchemy selectables, and ReflectedTable instances.
        """
        return QueryExecutor(statement, self.engine)

    def catalogue(
        self,
        keyword: str | None = None,
        display: bool = False,
    ) -> dict[str, dict[str, list[str]]]:
        """
        Return a dictionary of all schemas, tables, and views in the database.
        Supports keyword filtering and optional pretty-printing of the results.
        """
        inspector = inspect(self.engine)
        catalogue = {
            schema: {
                "tables": inspector.get_table_names(schema=schema),
                "views": inspector.get_view_names(schema=schema),
            }
            for schema in inspector.get_schema_names()
        }

        if keyword is not None:
            keyword = keyword.lower()
            catalogue = {
                schema: {
                    obj_type: [
                        obj
                        for obj in objects
                        if keyword in obj.lower()
                    ]
                    for obj_type, objects in content.items()
                }
                for schema, content in catalogue.items()
                if any(
                    keyword in obj.lower()
                    for objects in content.values()
                    for obj in objects
                )
            }
        if display:
            pprint(catalogue)
        return catalogue

    def dispose(self) -> None:
        if self.engine is not None:
            self.engine.dispose()
            self.engine = None
