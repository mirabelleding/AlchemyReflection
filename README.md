# Alchemy-Reflection

A lightweight Python package built on SQLAlchemy for database connection management, table reflection, schema inspection, and DataFrame retrieval.</br>
Designed with an emphasis on API ergonomics and method chaining, the object-oriented interface preserves native SQLAlchemy functionality and interoperability with pandas and Polars.

## Installation

```bash
pip install git+ssh://git@github.com/mirabelleding/AlchemyReflection.git
```
*Currently targets **SQL Server** through `mssql+pyodbc`. Requires an installed ODBC driver.*

## Connection
*`Database` accepts a **raw ODBC connection string**. Each instance owns its engine and reflected metadata.*

**Connection string format:**

```text
DRIVER={ODBC Driver 18 for SQL Server};
SERVER=server_name;
DATABASE=database_name;
UID=username;
PWD=password;
```

## Basic Usage
```python
import os

from sqlalchemy import select
from alchemy_reflection import Database

# Initialize database connection
db = Database(os.environ["DB_ODBC"])

# Search and display database objects
db.catalogue("some keywords", display=True)

# Instantiate a ReflectedTable
table = db.reflect("schemaname.tablename")

# Retrieve table as DataFrames
pd_df = table.to_pd()
pl_df = table.to_pl()

# Create a query using ReflectedTable.select()
stmt = table.select().where(...)

# Create a query using native SQLAlchemy expressions
stmt = select(table).where(...)

# Execute query and retrieve DataFrames
pd_df = db.query(stmt).to_pd(stmt)
pl_df = db.query(stmt).to_pl(stmt)

# Inspect table metadata
table.inspect()
```
## Advanced SQLAlchemy Queries

SQL construction remains entirely native to SQLAlchemy. Below are examples of advanced query expressions and direct DataFrame retrieval.
```python
import hashlib
from sqlalchemy import select, func, exists, or_

en_cours = (
    (e := db.reflect("mi77_lab.experiments").sa.alias("e"))
    .select()
    .where(
        e.c.status.in_(["unfinished", "in_exploration"]),
        ~exists().where(
            db.reflect("mi77_lab.archives").sa.c.experiment_id
            == e.c.experiment_id
        ),
    )
    .add_columns(
        func.row_number().over(
            partition_by=e.c.inspiration_id,
            order_by=e.c.updated_at.desc(),
        ).label("rn")
    )
    .cte("en_cours")
)

# Now the art of composition
next_inventions = (
    db.query(
        select(
            (i := db.reflect("mi77_lab.inspirations").sa.alias("i"))
            .c.name.label("inspiration"),
            i.c.category,
            en_cours.c.name.label("invention"),
            en_cours.c.updated_at,
        )
        .join(en_cours, en_cours.c.inspiration_id == i.c.inspiration_id)
        .where(
            en_cours.c.rn == 1,
            or_(
                i.c.source.in_(["some magic", "and more..."]),
                i.c.intrigue >= 7,
            ),
        )
    )
    .to_pd()
    .pipe(refactor_atelier)
    .groupby("category")
    .get_group("nouveau")
    .astype({"introspection": "string"})
    .sort_values(
        ["updated_at", "essence"],
        ascending=[False, False],
    )
    .assign(
        imprint=lambda df: (
            df.astype(str)
            .agg("-".join, axis=1)
            .map(
                lambda value: hashlib.blake2s(
                    value.encode(),
                    digest_size=7,
                ).hexdigest()
            )
        )
    )
    .loc[:, cols]
    .to_numpy()
)
```

## Multiple Database Connections

```python
dev = Database(os.environ["DEV_ODBC"])
test = Database(os.environ["TEST_ODBC"])

dev_df = dev.reflect("schemaname.tablename").to_pd()
test_df = test.reflect("schemaname.tablename").to_pl()

dev.dispose()
test.dispose()
```

## Interface

| Class | Attributes / Methods |
| --- | --- |
| `Database` | `engine`, `reflect()`, `catalogue()`, `query()`, `dispose()` |
| `ReflectedTable` | `sa`, `c`, `select()`, `inspect()`, `to_pd()`, `to_pl()` |
| `QueryExecutor` | `stmt_or_table`, `engine`, `to_pd()`, `to_pl()` |

`Database.reflect()` returns a `ReflectedTable`, while `Database.query()` returns a `QueryExecutor` that accepts SQLAlchemy selectable objects and provides DataFrame retrieval through `to_pd()` and `to_pl()`.

`ReflectedTable.sa` exposes the underlying SQLAlchemy `Table` when a native table object is required. Native SQLAlchemy expressions such as `select(table)` are supported through the clause-element protocol.

## Design Philosophy

Built on the belief that abstractions should eliminate repetitive operations without obscuring the underlying framework or introducing unnecessary complexity. The package simplifies common database operations while while retaining SQLAlchemy's native capabilities.

## License
MIT License © MI77-LAB
