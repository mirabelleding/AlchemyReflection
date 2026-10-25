import pandas as pd
import polars as pl
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.sql.selectable import FromClause, Selectable


class QueryExecutor:
    def __init__(
        self,
        stmt_or_table: Selectable,
        engine: Engine,
    ) -> None:
        if isinstance(stmt_or_table, FromClause):
            stmt_or_table = select(stmt_or_table)

        self.stmt_or_table = stmt_or_table
        self.engine = engine

    def to_pd(self) -> pd.DataFrame:
        with self.engine.connect() as conn:
            return pd.read_sql_query(self.stmt_or_table, conn)

    def to_pl(self) -> pl.DataFrame:
        with self.engine.connect() as conn:
            return pl.read_database(self.stmt_or_table, conn)