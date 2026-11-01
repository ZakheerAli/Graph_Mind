from __future__ import annotations

from collections.abc import Callable
from threading import Lock
from typing import Protocol
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from app.schemas.documents import DocumentRecord


class DocumentStore(Protocol):
    def add(self, document: DocumentRecord, chunks: list[str]) -> None: ...

    def list_for_user(self, user_id: str) -> list[DocumentRecord]: ...

    def get_for_user(self, document_id: str, user_id: str) -> DocumentRecord | None: ...

    def delete_for_user(self, document_id: str, user_id: str) -> bool: ...

    def count_for_user(self, user_id: str) -> int: ...


class InMemoryDocumentStore:
    def __init__(self) -> None:
        self._documents: dict[str, DocumentRecord] = {}
        self._chunks: dict[str, list[str]] = {}
        self._lock = Lock()

    def add(self, document: DocumentRecord, chunks: list[str]) -> None:
        with self._lock:
            self._documents[document.id] = document
            self._chunks[document.id] = chunks.copy()

    def list_for_user(self, user_id: str) -> list[DocumentRecord]:
        with self._lock:
            values = [
                document for document in self._documents.values() if document.user_id == user_id
            ]
            return sorted(values, key=lambda item: item.uploaded_at, reverse=True)

    def get_for_user(self, document_id: str, user_id: str) -> DocumentRecord | None:
        with self._lock:
            document = self._documents.get(document_id)
            if document is None or document.user_id != user_id:
                return None
            return document

    def delete_for_user(self, document_id: str, user_id: str) -> bool:
        with self._lock:
            document = self._documents.get(document_id)
            if document is None or document.user_id != user_id:
                return False
            del self._documents[document_id]
            self._chunks.pop(document_id, None)
            return True

    def count_for_user(self, user_id: str) -> int:
        with self._lock:
            return sum(1 for document in self._documents.values() if document.user_id == user_id)


class PostgresDocumentStore:
    def __init__(
        self,
        database_url: str,
        connect: Callable[..., psycopg.Connection] = psycopg.connect,
    ) -> None:
        self.database_url = database_url
        self._connect = connect

    def add(self, document: DocumentRecord, chunks: list[str]) -> None:
        with self._connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into public.documents
                        (id, user_id, title, filename, storage_path, status, page_count)
                    values (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        UUID(document.id),
                        UUID(document.user_id),
                        document.title,
                        document.filename,
                        f"documents/{document.user_id}/{document.id}/{document.filename}",
                        document.status.value,
                        document.page_count,
                    ),
                )
                cursor.executemany(
                    """
                    insert into public.chunks
                        (document_id, user_id, chunk_index, page, content, token_count)
                    values (%s, %s, %s, 1, %s, %s)
                    """,
                    [
                        (
                            UUID(document.id),
                            UUID(document.user_id),
                            index,
                            chunk,
                            len(chunk.split()),
                        )
                        for index, chunk in enumerate(chunks)
                        if chunk.strip()
                    ],
                )

    def list_for_user(self, user_id: str) -> list[DocumentRecord]:
        with self._connect(self.database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select d.id::text as id, d.user_id::text as user_id, d.title,
                           d.filename, d.status, d.page_count,
                           count(c.id)::int as chunk_count, d.created_at as uploaded_at
                    from public.documents d
                    left join public.chunks c on c.document_id = d.id and c.user_id = d.user_id
                    where d.user_id = %s
                    group by d.id
                    order by d.created_at desc
                    """,
                    (UUID(user_id),),
                )
                return [self._to_record(row) for row in cursor.fetchall()]

    def get_for_user(self, document_id: str, user_id: str) -> DocumentRecord | None:
        with self._connect(self.database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select d.id::text as id, d.user_id::text as user_id, d.title,
                           d.filename, d.status, d.page_count,
                           count(c.id)::int as chunk_count, d.created_at as uploaded_at
                    from public.documents d
                    left join public.chunks c on c.document_id = d.id and c.user_id = d.user_id
                    where d.id = %s and d.user_id = %s
                    group by d.id
                    """,
                    (UUID(document_id), UUID(user_id)),
                )
                row = cursor.fetchone()
                return self._to_record(row) if row else None

    def delete_for_user(self, document_id: str, user_id: str) -> bool:
        with self._connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "delete from public.documents where id = %s and user_id = %s returning id",
                    (UUID(document_id), UUID(user_id)),
                )
                return cursor.fetchone() is not None

    def count_for_user(self, user_id: str) -> int:
        with self._connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "select count(*) from public.documents where user_id = %s",
                    (UUID(user_id),),
                )
                return cursor.fetchone()[0]

    @staticmethod
    def _to_record(row: dict[str, object]) -> DocumentRecord:
        return DocumentRecord(
            id=str(row["id"]),
            user_id=str(row["user_id"]),
            title=str(row["title"]),
            filename=str(row["filename"]),
            status=str(row["status"]),
            page_count=int(row["page_count"]),
            chunk_count=int(row["chunk_count"]),
            uploaded_at=row["uploaded_at"],
        )
