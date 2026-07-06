import sqlite3
from pathlib import Path

sql = Path('config/database_schema.sql').read_text(encoding='utf-8')
statements = []
for raw in sql.split(';'):
    s = raw.strip()
    if not s or s.startswith('--'):
        continue
    statements.append(s)

conn = sqlite3.connect(':memory:')
for idx, stmt in enumerate(statements, start=1):
    print(f'Executing statement {idx}: {stmt[:120]}...')
    try:
        conn.execute(stmt)
        print('OK')
    except Exception as exc:
        print('FAILED', idx, type(exc).__name__, exc)
        break
else:
    print('All statements executed successfully')
