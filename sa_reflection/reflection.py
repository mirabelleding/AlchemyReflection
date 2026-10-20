from __future__ import annotations

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
        return self.database.to_pd(self.sa)


    def to_pl(self) -> pl.DataFrame:
        return self.database.to_pl(self.sa)


    def inspect(self) -> None:

        print(f"Schema: {self.sa.schema}")
        print(f"Table: {self.sa.name}\n")

        name_w = max(len(c.name) for c in self.sa.columns)
        type_w = max(len(str(c.type)) for c in self.sa.columns)

        print(f"     {'Column':<{name_w}}  {'Type':<{type_w}}  Nullable")
        for c in self.sa.columns:
            print(
                f"{'PK' if c.primary_key else '':<4} "
                f"{c.name:<{name_w}}  "
                f"{str(c.type):<{type_w}}  "
                f"{c.nullable}"
            )

        if self.sa.foreign_keys:
            print("\nForeign Keys")
            for fk in self.sa.foreign_keys:
                print(f"{fk.parent.name} -> {fk.target_fullname}")

        if self.sa.indexes:
            print("\nIndexes")
            for index in self.sa.indexes:
                print(
                    f"{index.name}: "
                    f"{', '.join(c.name for c in index.columns)} "
                    f"(Unique: {index.unique})"
                )

        constraints = [
            constraint
            for constraint in self.sa.constraints
            if not isinstance(constraint, ForeignKeyConstraint)
        ]

        if constraints:
            print("\nTable Constraints")
            for constraint in constraints:
                if isinstance(constraint, CheckConstraint):
                    details = str(constraint.sqltext)
                else:
                    details = ", ".join(c.name for c in constraint.columns)

                print(
                    f"{type(constraint).__name__}: "
                    f"{constraint.name or 'unnamed'} "
                    f"({details})"
                )