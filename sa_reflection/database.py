from __future__ import annotations

import pandas as pd
import polars as pl
from pprint import pprint

from sqlalchemy import (
    MetaData,
    Table,
    create_engine,
    inspect,
    select,
)
from sqlalchemy.engine import Engine, URL
from sqlalchemy.sql.selectable import FromClause, SelectBase

from .reflection import ReflectedTable


class Database: 
    def __init__(self, odbc_string: str) -> None:
        self.odbc_string = odbc_string
        self.metadata = MetaData()
        self._engine: Engine | None = None

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            url = URL.create(
                "mssql+pyodbc",
                query={"odbc_connect": self.odbc_string},
            )

            self._engine = create_engine(
                url,
                pool_pre_ping=True,
            )

        return self._engine
    

    def reflect(
        self, 
        source: str
    ) -> ReflectedTable:
        
        schema, tablename = source.rpartition(".", 1)

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


    def to_pd(
        self,
        table_or_stmt: SelectBase | FromClause,
    ) -> pd.DataFrame:
        if isinstance(table_or_stmt, FromClause):
            table_or_stmt = select(table_or_stmt)

        with self.engine.connect() as conn:
            return pd.read_sql_query(table_or_stmt, conn)


    def to_pl(
        self,
        table_or_stmt: SelectBase | FromClause,
    ) -> pl.DataFrame:
        if isinstance(table_or_stmt, FromClause):
            table_or_stmt = select(table_or_stmt)

        with self.engine.connect() as conn:
            return pl.read_database(table_or_stmt, conn)


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
