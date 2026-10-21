from __future__ import annotations

from pprint import pprint
from typing import TYPE_CHECKING

import pandas as pd
import polars as pl
from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Select,
    Table,
    select,
)

if TYPE_CHECKING:
    from .database import Database


class ReflectedTable:
    def __init__(
        self,
        table: Table,
        database: Database,
    ) -> None:
        
        self.sa = table
        self.database = database


    def __clause_element__(self) -> Table:

        return self.sa

    @property
    def c(self):

        return self.sa.c
    

    def select(self) -> Select:

        return select(self.sa)


    def to_pd(self) -> pd.DataFrame:

        return self.database.query(self.sa).to_pd()

    def to_pl(self) -> pl.DataFrame:

        return self.database.query(self.sa).to_pl()


    def inspect(self) -> None:
        
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