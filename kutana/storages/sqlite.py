import json
import sqlite3
import threading
from contextlib import contextmanager
from ..storage import Storage, OptimisticLockException


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class SqliteStorage(Storage):
    """
    Storage implementation of the storage that uses sqlite3.
    """

    def __init__(self, path):
        self._path = path
        self._lock = threading.Lock()
        self.connection = None

    async def init(self):
        self.connection = sqlite3.connect(self._path, check_same_thread=False)
        self.connection.row_factory = dict_factory

        with self.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS kvs (
                    key text NOT NULL,
                    val text NOT NULL,
                    ver integer NOT NULL default 0
                )
            """)
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS kvs__key ON kvs (key)")
            cur.execute("CREATE INDEX IF NOT EXISTS kvs__key__ver ON kvs (key, ver)")

    @contextmanager
    def cursor(self):
        with self._lock:
            with self.connection:
                yield self.connection.cursor()

    async def _put(self, key, values, version=None):
        old_version = version or 0
        new_version = old_version + 1
        dumped_values = json.dumps(values, ensure_ascii=False)

        try:
            with self.cursor() as cur:
                if version:
                    cur.execute(
                        "UPDATE kvs SET val = ?, ver = ? WHERE key = ? AND ver = ?",
                        (dumped_values, new_version, key, old_version)
                    )

                if not version or cur.rowcount < 1:
                    cur.execute(
                        "INSERT INTO kvs (key, val, ver) VALUES (?, ?, ?)",
                        (key, dumped_values, new_version)
                    )
        except sqlite3.IntegrityError:
            raise OptimisticLockException(f"Failed to set values for key {key} (mismatched version)")

        return new_version

    async def _get(self, key):
        with self.cursor() as cur:
            cur.execute("SELECT * FROM kvs WHERE key = ?", (key,))
            row = cur.fetchone()
            if row:
                return {**json.loads(row["val"]), "_version": row["ver"]}
            return row

    async def _delete(self, key):
        with self.cursor() as cur:
            cur.execute("DELETE FROM kvs WHERE key = ?", (key,))
