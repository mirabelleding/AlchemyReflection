import pandas as pd
import polars as pl
from sqlalchemy import Engine, FromClause, Selectable, select

from .reflection import ReflectedTable


class QueryExecutor:
    def __init__(
        self,
        statement: Selectable,
        engine: Engine,
    ) -> None:
        if isinstance(statement, (FromClause, ReflectedTable)):
            statement = select(statement)

        self.statement = statement
        self.engine = engine

    def to_pd(self) -> pd.DataFrame:
        with self.engine.connect() as conn:
            return pd.read_sql_query(self.statement, conn)

    def to_pl(self) -> pl.DataFrame:
        with self.engine.connect() as conn:
            return pl.read_database(self.statement, conn)