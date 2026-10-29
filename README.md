# AlchemyReflection
A lightweight Python package built on SQLAlchemy for database connection management, table reflection, schema inspection, and query result retrieval.</br>
Designed with an emphasis on API ergonomics and method chaining, the object-oriented interface preserves native SQLAlchemy functionality and interoperability with pandas, Polars, NumPy, and PyArrow.

## Installation

```bash
pip install git+ssh://git@github.com/mirabelleding/AlchemyReflection.git
```
**PyArrow is optional and is required only for `to_arrow()`.*

## Connection

`Database` accepts SQLAlchemy connection URLs for supported database dialects. Raw ODBC connection strings are also accepted for SQL Server.

**SQLAlchemy URL:**

```python
from alchemy_reflection import Database

db = Database("postgresql+psycopg://user:password@localhost:5432/database_name")
```

**Raw SQL Server ODBC connection string:**

```text
DRIVER={ODBC Driver 18 for SQL Server};
SERVER=server_name;
DATABASE=database_name;
UID=username;
PWD=password;
```
```python
import os
from alchemy_reflection import Database

db = Database(os.environ["DB_ODBC"])
```
Each `Databse` instance maintains its own SQLAlchemy engine and reflected metadata. </br>
**The required database driver must be installed. SQL Server connections using pyodbc also require an ODBC driver.*

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

# Inspect table metadata
table.inspect()
```

## Native SQLAlchemy Interoperability

`ReflectedTable` provides access to native SQLAlchemy `Table` attributes and methods, alongside `QueryExecutor` methods for query execution and result retrieval.
Native SQLAlchemy expressions such as `select(reflected_table)` are also supported.

```python
reflected_table.name
reflected_table.schema
reflected_table.columns.keys()
reflected_table.primary_key
reflected_table.alias("t")
reflected_table.select()
```

## Query Execution and Result Retrieval

`QueryExecutor` supports query execution and result retrieval for raw SQL statements, SQLAlchemy `Selectable`, and `ReflectedTable` instances. Its methods are accessible through `Database.query()` or directly through `ReflectedTable` interface.

| Method | Return Type |
| --- | --- |
| `to_pd()` | pandas `DataFrame`, or `Series` for single-column queries |
| `to_pl()` | Polars `DataFrame`, or `Series` for single-column queries |
| `to_numpy(dtype=None)` | 2D NumPy array, or 1D for single-column queries; dtype inferred unless specified |
| `to_arrow()` | PyArrow `Table`, or `Array` for single-column queries; requires PyArrow |
| `to_records()` | List of dictionaries with column names as keys |
| `fetch(n_rows=None)` | List of SQLAlchemy `Row` objects; all rows are retrieved by default |
| `to_scalar()` | Scalar value from a single-row, single-column query |

```python
from sqlalchemy import func, select

stmt = select(table.c.some_column)

series = db.query(stmt).to_pd()
array = db.query(stmt).to_numpy()
rows = db.query(stmt).fetch(7)

count_stmt = select(func.count()).select_from(table)
count = db.query(count_stmt).to_scalar()
```

## Advanced SQLAlchemy Queries

SQL construction remains entirely native to SQLAlchemy. Below are examples of advanced query expressions and with DataFrame operations.
```python
import hashlib
from sqlalchemy import select, func, exists, or_

en_cours = (
    (e := db.reflect("mi77_lab.experiments").alias("e"))
    .select()
    .where(
        e.c.status.in_(["unfinished", "in_exploration"]),
        ~exists().where(
            db.reflect("mi77_lab.archives").c.experiment_id
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
            (i := db.reflect("mi77_lab.inspirations").alias("i"))
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
| `Database` | `engine`, `metadata`, `reflect()`, `catalogue()`, `query()` |
| `ReflectedTable` | `sa`, `database`, native SQLAlchemy `Table` attributes and methods, `inspect()`, delegated `QueryExecutor` methods |
| `QueryExecutor` | `statement`, `engine`, `to_pd()`, `to_pl()`, `to_numpy()`, `to_arrow()`, `to_records()`, `fetch()`, `to_scalar()` |

`Database.reflect()` returns a `ReflectedTable`, while `Database.query()` returns a `QueryExecutor`.

`ReflectedTable.__getattr__()` forwards unresolved attributes are delegated to the underlying SQLAlchemy `Table` first, then to `QueryExecutor` through `__getattr__()`.

`ReflectedTable.__clause_element__()` enables SQLAlchemy expression coercion. The explicit `.sa` attribute exposes the underlying SQLAlchemy `Table` when a native table object is required.


## Design Philosophy

Built on the belief that abstractions should eliminate repetitive operations without obscuring the underlying framework or introducing unnecessary complexity. The package simplifies common database operations while while retaining SQLAlchemy's native capabilities.

## License
MIT License © MI77-LAB
