from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
import polars as pl
from sqlalchemy import Engine, FromClause, Selectable, select, text

from .reflection import ReflectedTable

if TYPE_CHECKING:
    import pyarrow as pa


class QueryExecutor:
    def __init__(
        self,
        statement: Selectable | ReflectedTable | str,
        engine: Engine,
    ) -> None:
        if isinstance(statement, str):
            statement = text(statement)
        elif isinstance(statement, (FromClause, ReflectedTable)):
            statement = select(statement)

        self.statement = statement
        self.engine = engine

    def to_pd(self) -> pd.DataFrame | pd.Series:
        """
        Returns query result as a pandas DataFrame or Series.
        A single-column query returns a Series; otherwise, a DataFrame.
        --------
        e.g.
        >>> type(db.query(select(table.c.amount)).to_pd()).__name__
        'Series'
        >>> type(db.query(select(table)).to_pd()).__name__
        'DataFrame'
        """
        with self.engine.connect() as conn:
            df = pd.read_sql_query(self.statement, conn)

        return df.iloc[:, 0] if df.shape[1] == 1 else df

    def to_pl(self) -> pl.DataFrame | pl.Series:
        """
        Returns query result as a Polars DataFrame or Series.
        Similar to to_pd(), a single-column query returns a Series.
        """
        with self.engine.connect() as conn:
            df = pl.read_database(self.statement, conn)

        return df.to_series(0) if df.width == 1 else df

    def to_numpy(self, dtype: Any = None) -> np.ndarray:
        """
        Returns query results as a NumPy array.
        Single-column results are returned as 1D arrays, while multi-column
        results retain their 2D structure.
        The dtype is inferred by default and can be explicitly specified
        to control type conversion or preserve mixed types.
        """
        with self.engine.connect() as conn:
            result = conn.execute(self.statement)

            array = np.asarray(
                [tuple(row) for row in result],
                dtype=dtype,
            ).reshape(-1, len(result.keys()))

            return array[:, 0] if array.shape[1] == 1 else array

    def to_arrow(self) -> pa.Table | pa.Array:
        """
        Returns query results as a PyArrow Table or Array.
        Similar to to_pd(), single-column results are returned as an Array.
        Requires the optional PyArrow dependency.
        """
        return self.to_pl().to_arrow()

    def to_records(self) -> list[dict[str, Any]]:
        """
        Returns query results as a list of dictionaries, with each dictionary
        representing a row and column names as keys.
        """
        return [row._asdict() for row in self.fetch()]

    def to_scalar(self) -> Any:
        """
        Returns the scalar value from a query yielding exactly one row and column.
        Unlike SQLAlchemy's Result.scalar(), this method enforces both
        row and column cardinality.
        --------
        e.g.
        >>> db.query(select(func.count()).select_from(sometable)).scalar()
        77
        """
        with self.engine.connect() as conn:
            result = conn.execute(self.statement)

            if len(result.keys()) != 1:
                raise ValueError("Multiple columns were found when exactly one was required")

            return result.scalar_one()

    def fetch(self, n_rows: int | None = None) -> list:
        """
        Retrieves query results as a list of SQLAlchemy Row objects.
        All rows are retrieved by default. Specify n_rows to limit the
        number of rows returned.
        """
        if n_rows is not None and (type(n_rows) is not int or n_rows < 0):
            raise ValueError("n_rows must be a non-negative integer")

        with self.engine.connect() as conn:
            result = conn.execute(self.statement)
            return result.all() if n_rows is None else result.fetchmany(n_rows)
