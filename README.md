# SA-Reflection

A lightweight Python package built on **SQLAlchemy** for database connection management, table reflection, schema inspection, and data retrieval using **pandas** and **Polars**.

The package provides an object-oriented interface for managing multiple database connections, inspecting database schemas, reflecting tables, while retaining full support for native SQLAlchemy query expressions.

## Installation

```bash
pip install git+https://github.com/mirabelleding/sa_reflection.git
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
from sa_reflect import Database

# Initialize database connection
db = Database(os.environ["DB_ODBC"])

# Search/View database objects
db.catalogue("some keywords", display=True)

# Instantiate a reflected table
table = db.reflect("schemaname.tablename")

# Load table into pandas/polars DataFrame
pd_df = table.to_pd()
pl_df = table.to_pl()

# Query using native SQLAlchemy expressions
stmt = select(table).where(table.c.status == "pending")

# Load query results into pandas/polars DataFrame
pd_df = db.to_pd(stmt)
pl_df = db.to_pl(stmt)

# Inspect table metadata
accounts.inspect()
```
## Advanced SQLAlchemy Queries

SQL construction remains entirely native to SQLAlchemy. Below are examples of advanced query expressions and direct DataFrame retrieval.
```python
from sqlalchemy import func, select

experiments = db.reflect("mi77_lab.experiments")
inspirations = db.reflect("mi77_lab.inspirations")
archives = db.reflect("mi77_lab.archives")

en_cours = (
    select(
        experiments.c.experiment_id,
        experiments.c.inspiration_id,
        experiments.c.name,
        func.row_number().over(
            partition_by=experiments.c.inspiration_id,
            order_by=experiments.c.updated_at.desc(),
        ).label("rn"),
    )
    .where(experiments.c.status == "unfinished")
    .cte("en_cours")
)

next_inventions = db.to_pd(
    select(
        inspirations.c.name.label("inspiration"),
        unfinished.c.name.label("experiment"),
    )
    .join(
        unfinished,
        unfinished.c.inspiration_id == inspirations.c.inspiration_id,
    )
    .where(
        unfinished.c.rn == 1,
        inspirations.c.source == "some magic",
        ~exists(
            select(1)
            .select_from(archives.sa)
            .where(
                archives.c.experiment_id == unfinished.c.experiment_id
            )
        ),
    )
)
```

`to_pd()` and `to_pl()` also accept SQLAlchemy `FromClause` objects, including tables and subqueries; these are automatically wrapped in `select()`.

## Multiple Database Connections

```python
dev = Database(os.environ["DEV_ODBC"])
test = Database(os.environ["TEST_ODBC"])

dev_table = dev.reflect("schemaname.tablename")
test_table = test.reflect("schemaname.tablename")

dev_df = dev_table.to_pd()
test_df = test_table.to_pl()

dev.dispose()
test.dispose()
```

## Interface

| Class | Methods / Attributes |
| --- | --- |
| `Database` | `engine`, `reflect()`, `catalogue()`, `to_pd()`, `to_pl()`, `dispose()` |
| `ReflectedTable` | `sa`, `c`, `select()`, `inspect()`, `to_pd()`, `to_pl()` |

`table.sa` exposes the underlying SQLAlchemy `Table` when a native table object is required. Native SQLAlchemy expressions such as `select(table)` are supported through the clause-element protocol.

Connection credentials should be managed through environment variables or a secrets manager.

## Design Philosophy

Built on the belief that abstractions should eliminate repetitive operations without obscuring the underlying framework or introducing unnecessary complexity. The package simplifies common database operations while while retaining SQLAlchemy's native capabilities.

## License
MIT License © MI77-LAB
