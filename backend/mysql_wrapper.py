import os
import re
import pymysql
import pymysql.cursors

try:
    from pymysql.err import IntegrityError
except ImportError:
    class IntegrityError(Exception):
        pass

class MySQLRow:
    """Row object supporting column name and 0-based integer index access."""
    def __init__(self, data_dict):
        self._data = dict(data_dict) if data_dict is not None else {}
        self._keys = list(self._data.keys())
        self._values = list(self._data.values())

    def __getitem__(self, key):
        if isinstance(key, int):
            if 0 <= key < len(self._values):
                val = self._values[key]
                if val is None and len(self._values) == 1 and any(k in str(self._keys[0]).upper() for k in ('SUM', 'COUNT')):
                    return 0
                return val
            return 0
        return self._data.get(key)

    def __setitem__(self, key, value):
        self._data[key] = value

    def get(self, key, default=None):
        try:
            val = self._data.get(key, default)
            return val if val is not None else default
        except Exception:
            return default

    def __contains__(self, key):
        return key in self._data

    def keys(self):
        return self._keys

    def values(self):
        return self._values

    def items(self):
        return self._data.items()

    def __repr__(self):
        return f"<MySQLRow {self._data}>"

class MySQLCursor:
    def __init__(self, raw_cursor, rows=None, lastrowid=None):
        self._raw_cursor = raw_cursor
        self._rows = [MySQLRow(r) for r in rows] if rows is not None else []
        self._index = 0
        self._lastrowid = lastrowid if lastrowid is not None else getattr(raw_cursor, 'lastrowid', None)

    def fetchone(self):
        if self._index < len(self._rows):
            row = self._rows[self._index]
            self._index += 1
            return row
        return None

    def fetchall(self):
        remaining = self._rows[self._index:]
        self._index = len(self._rows)
        return remaining

    @property
    def lastrowid(self):
        return self._lastrowid

    def __iter__(self):
        return self

    def __next__(self):
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row

def _convert_query_placeholders(query):
    """
    Replaces ? placeholders with %s placeholders, ignoring ? inside string literals.
    """
    out = []
    in_single = False
    in_double = False
    i = 0
    while i < len(query):
        c = query[i]
        if c == "'" and not in_double:
            in_single = not in_single
            out.append(c)
        elif c == '"' and not in_single:
            in_double = not in_double
            out.append(c)
        elif c == '?' and not in_single and not in_double:
            out.append('%s')
        else:
            out.append(c)
        i += 1
    return "".join(out)

class MySQLConnectionWrapper:
    """Connection wrapper for MySQL using PyMySQL."""
    def __init__(self, conn=None):
        if conn is None:
            from config import Config
            self.conn = pymysql.connect(
                host=getattr(Config, 'MYSQL_HOST', 'localhost'),
                port=int(getattr(Config, 'MYSQL_PORT', 3306)),
                user=getattr(Config, 'MYSQL_USER', 'root'),
                password=getattr(Config, 'MYSQL_PASSWORD', ''),
                database=getattr(Config, 'MYSQL_DB', 'cloud_dedup'),
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
                charset='utf8mb4'
            )
        else:
            self.conn = conn
        self.IntegrityError = IntegrityError
        self._last_cursor = None

    def cursor(self):
        return self

    def commit(self):
        try:
            self.conn.commit()
        except Exception:
            pass

    def rollback(self):
        try:
            self.conn.rollback()
        except Exception:
            pass

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

    @property
    def lastrowid(self):
        return self._last_cursor.lastrowid if self._last_cursor else None

    def fetchone(self):
        return self._last_cursor.fetchone() if self._last_cursor else None

    def fetchall(self):
        return self._last_cursor.fetchall() if self._last_cursor else []

    def execute(self, query, params=None):
        converted_query = _convert_query_placeholders(query.strip())
        with self.conn.cursor() as cur:
            if params is not None:
                if isinstance(params, (list, tuple)):
                    cur.execute(converted_query, tuple(params))
                else:
                    cur.execute(converted_query, (params,))
            else:
                cur.execute(converted_query)
            
            rows = cur.fetchall() if cur.description else []
            lastrowid = cur.lastrowid
            
        self._last_cursor = MySQLCursor(None, rows=rows, lastrowid=lastrowid)
        return self._last_cursor

def get_mysql_connection():
    from config import Config
    if getattr(Config, 'DB_TYPE', 'mysql').lower() == 'mongodb':
        try:
            from mongo_wrapper import MongoConnectionWrapper
            return MongoConnectionWrapper()
        except Exception:
            pass
    return MySQLConnectionWrapper()

# Backward-compatibility aliases
SQLiteRow = MySQLRow
SQLiteMimicCursor = MySQLCursor
SQLiteConnectionMimic = MySQLConnectionWrapper
