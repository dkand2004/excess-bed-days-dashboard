"""Run one SQL file against the local DuckDB database.
Usage: python src/run_sql.py sql/01_expected_los.sql
"""
import os
import sys

import duckdb
from dotenv import load_dotenv

load_dotenv()
con = duckdb.connect(os.getenv("DUCKDB_PATH", "data/ebd.duckdb"))
with open(sys.argv[1], encoding="utf-8") as f:
    con.execute(f.read())
print(f"ran {sys.argv[1]}")
