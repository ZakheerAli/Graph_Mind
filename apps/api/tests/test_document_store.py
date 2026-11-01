from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from psycopg.rows import dict_row

from apps.api.app.adapters.document_store import PostgresDocumentStore
from apps.api.app.schemas.documents import DocumentRecord


class RecordingCursor:
    def __init__(self, result: Any = None) -> None:
        self.calls: list[tuple[str, Any]] = []
        self.batch_calls: list[tuple[str, list[Any]]] = []
        self.result = result

    def __enter__(self) -> RecordingCursor:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, query: str, params: Any = None) -> None:
        self.calls.append((query, params))

    def executemany(self, query: str, params: list[Any]) -> None:
        self.batch_calls.append((query, params))

    def fetchone(self) -> Any:
        return self.result

    def fetchall(self) -> list[Any]:
        return []


class RecordingConnection:
    def __init__(self, cursor: RecordingCursor) -> None:
        self.recording_cursor = cursor

    def __enter__(self) -> RecordingConnection:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def cursor(self, **_: Any) -> RecordingCursor:
        return self.recording_cursor


def test_postgres_store_persists_document_and_nonempty_chunks() -> None:
    cursor = RecordingCursor()
    connection = RecordingConnection(cursor)
    connect_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def connect(*args: Any, **kwargs: Any) -> RecordingConnection:
        connect_calls.append((args, kwargs))
        return connection

    document = DocumentRecord(
        id=str(uuid4()),
        user_id=str(uuid4()),
        title="Notes",
        filename="notes.txt",
        page_count=1,
        chunk_count=2,
    )
    store = PostgresDocumentStore("postgresql://test", connect=connect)

    store.add(document, ["first chunk", "  "])

    assert len(cursor.calls) == 1
    insert_query, document_params = cursor.calls[0]
    assert "insert into public.documents" in insert_query
    assert document_params[:2] == (UUID(document.id), UUID(document.user_id))
    chunks_query, chunks_params = cursor.batch_calls[0]
    assert "insert into public.chunks" in chunks_query
    assert chunks_params == [(UUID(document.id), UUID(document.user_id), 0, "first chunk", 2)]
    assert connect_calls[0][0] == ("postgresql://test",)


def test_postgres_store_scopes_deletion_to_document_owner() -> None:
    document_id = uuid4()
    user_id = uuid4()
    cursor = RecordingCursor(result=(document_id,))
    store = PostgresDocumentStore(
        "postgresql://test",
        connect=lambda *_args, **_kwargs: RecordingConnection(cursor),
    )

    assert store.delete_for_user(str(document_id), str(user_id))

    query, params = cursor.calls[0]
    assert "where id = %s and user_id = %s" in query
    assert params == (document_id, user_id)


def test_postgres_store_scopes_reads_to_user() -> None:
    document_id = uuid4()
    user_id = uuid4()
    cursor = RecordingCursor()
    connect_calls: list[dict[str, Any]] = []

    def connect(*_args: Any, **kwargs: Any) -> RecordingConnection:
        connect_calls.append(kwargs)
        return RecordingConnection(cursor)

    store = PostgresDocumentStore(
        "postgresql://test",
        connect=connect,
    )

    assert store.get_for_user(str(document_id), str(user_id)) is None

    query, params = cursor.calls[0]
    assert "where d.id = %s and d.user_id = %s" in query
    assert params == (document_id, user_id)
    assert connect_calls[0]["row_factory"] is dict_row
