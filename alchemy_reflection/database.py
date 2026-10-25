from __future__ import annotations

from pprint import pprint

from sqlalchemy import (
    MetaData,
    Table,
    create_engine,
    inspect,
)
from sqlalchemy.engine import URL, Engine
from sqlalchemy.sql.selectable import FromClause, SelectBase

from .execution import QueryExecutor
from .reflection import ReflectedTable


class Database:
    def __init__(self,_odbc: str) -> None:
        self._odbc = _odbc
        self.metadata = MetaData()
        self._engine: Engine | None = None

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            url = URL.create(
                "mssql+pyodbc",
                query={"odbc_connect": self._odbc},
            )
            self._engine = create_engine(
                url,
                pool_pre_ping=True,
            )
        return self._engine

    def reflect(self,source: str) -> ReflectedTable:
        schema, _, tablename = source.rpartition(".")
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
        statement: SelectBase | FromClause,
    ) -> QueryExecutor:
        return QueryExecutor(statement, self.engine)

    def catalogue(
        self,
        keyword: str | None = None,
        display: bool = False,
    ) -> dict[str, dict[str, list[str]]]:
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
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
