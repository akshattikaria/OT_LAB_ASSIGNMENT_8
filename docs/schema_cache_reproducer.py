"""Observed SQLite-build corner case; diagnostic only, not the benchmark protocol.

Prints the reused-connection result and the fresh-connection result. It makes no
claim about SQLite internals or other versions. The final experiment and fixture
tests create schema before querying and reopen connections for each portfolio.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from test_dbms import QueryTests
from dblab.core import INDEXES,QUERIES,reference
import sqlite3

print('SQLite',sqlite3.sqlite_version)
for mode in ('reuse_after_querying_old_schema','fresh_schema_before_queries'):
    fixture=QueryTests();c=fixture.database()
    if mode.startswith('reuse'):
        c.execute('ANALYZE')
        for case in fixture.fixture_cases():c.execute(QUERIES[case['kind']],case['params']).fetchall()
    c.execute(INDEXES['confirmed_station']);c.execute('ANALYZE')
    print(mode)
    for status in ('confirmed','pending'):
        case={'kind':'status','params':(status,0,8760)}
        actual=c.execute(QUERIES['status'],case['params']).fetchall();expected=reference(fixture.rows,case)
        print(status,'actual=',actual,'expected=',expected,'equal=',actual==expected)
    c.close()
