import json
import sqlite3
import threading
from contextlib import contextmanager

from ..storage import OptimisticLockException, Document, Storage


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
        self.connection: sqlite3.Connection

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
        with self.connection:
            yield self.connection.cursor()

    async def put(self, key, data):
        with self._lock:
            old_version = data.get("_version") or 0
            new_version = old_version + 1
            new_data = {k: v for k, v in data.items() if v is not None}
            serialized_data = json.dumps(new_data, ensure_ascii=False)

            try:
                with self.cursor() as cur:
                    if old_version:
                        cur.execute(
                            "UPDATE kvs SET val = ?, ver = ? WHERE key = ? AND ver = ?",
                            (serialized_data, new_version, key, old_version)
                        )

                    if not old_version or cur.rowcount < 1:
                        cur.execute(
                            "INSERT INTO kvs (key, val, ver) VALUES (?, ?, ?)",
                            (key, serialized_data, new_version)
                        )
            except sqlite3.IntegrityError:
                raise OptimisticLockException(f"Failed to update data for key {key} (mismatched version)")

            return Document({**new_data, "_version": new_version}, _storage=self, _storage_key=key)

    async def get(self, key):
        with self._lock:
            with self.cursor() as cur:
                cur.execute("SELECT * FROM kvs WHERE key = ?", (key,))
                row = cur.fetchone()

                if not row:
                    return None

                return Document(
                    {**json.loads(row["val"]), "_version": row["ver"]},
                    _storage=self,
                    _storage_key=key,
                )

    async def delete(self, key):
        with self._lock:
            with self.cursor() as cur:
                cur.execute("DELETE FROM kvs WHERE key = ?", (key,))
