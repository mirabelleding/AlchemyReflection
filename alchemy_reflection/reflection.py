from __future__ import annotations

from pprint import pprint
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Table,
)

if TYPE_CHECKING:
    from .database import Database


class ReflectedTable:
    """
    Extends the SQLAlchemy Table interface with query execution and result
    retrieval methods from QueryExecutor.

    Unresolved attributes are delegated to the underlying SQLAlchemy Table
    first, then to QueryExecutor.
    """
    def __init__(
        self,
        table: Table,
        database: Database,
    ) -> None:
        self.sa = table
        self.database = database

    is_clause_element = False

    def __clause_element__(self) -> Table:
        return self.sa

    def __getattr__(self, name: str):
        try:
            return getattr(self.sa, name)
        except AttributeError:
            return getattr(self.database.query(self.sa), name)

    def __dir__(self):
        return sorted(
            set(super().__dir__())
            | set(dir(self.sa))
            | set(dir(self.database.query(self.sa)))
        )

    def inspect(self) -> None:
        """
        Pretty-print the reflected table's metadata and structural information,
        including its columns, constraints, and other table properties.
        """
        meta = {
            "schema": self.sa.schema,
            "table": self.sa.name,
            "columns": [
                {
                    "name": c.name,
                    "type": str(c.type),
                    "nullable": c.nullable,
                    "primary_key": c.primary_key,
                }
                for c in self.sa.columns
            ],
            "foreign_keys": [
                {
                    "column": fk.parent.name,
                    "references": fk.target_fullname,
                }
                for fk in self.sa.foreign_keys
            ],
            "indexes": [
                {
                    "name": index.name,
                    "columns": [c.name for c in index.columns],
                    "unique": index.unique,
                }
                for index in self.sa.indexes
            ],
            "constraints": [
                {
                    "type": type(constraint).__name__,
                    "name": constraint.name,
                    "details": (
                        str(constraint.sqltext)
                        if isinstance(constraint, CheckConstraint)
                        else [c.name for c in constraint.columns]
                    ),
                }
                for constraint in self.sa.constraints
                if not isinstance(constraint, ForeignKeyConstraint)
            ],
        }
        pprint(meta, sort_dicts=False)