"""Offline batch ingestion pipeline for Deal Room AI.

This is the OFFLINE counterpart to Boston's synchronous upload-time pipeline
in api/document_processing.py. Use it for:
  - Bulk-loading historical documents that didn't come through the API
  - Re-embedding everything when the embedding model changes
  - Backfilling doc_type metadata from the trained classifier

It deliberately does NOT reimplement chunking, embedding, or Chroma I/O —
those live in Boston's modules (api.document_processing, api.vector_store)
and are the single source of truth for the chunking/storage contract.

DEPENDENCIES (call out before running):
  - Requires Boston's branch (feat/person-c) to be merged into main, OR run
    this script from a checkout that includes those modules.
  - Requires classifier_model.joblib in CWD (or set CLASSIFIER_MODEL_PATH).
  - Requires OPENAI_API_KEY for embeddings.

ALIGNMENT TODO (Boston):
  Boston's `Chunk` dataclass and `vector_store.upsert_chunks` do not yet carry
  a `doc_type` metadata field. Until that lands, this orchestrator writes
  doc_type by post-upserting metadata via the underlying Chroma collection.
  Once Boston extends `Chunk` to include `doc_type` and threads it through
  `ChromaVectorStore.upsert_chunks`, replace the _attach_doc_type call below
  with a single in-place upsert.

Usage:
  python -m ingestion.pipeline \\
      --source ./data/raw \\
      --deal-room-id 1 --user-id 1 --document-id 100 \\
      [--doc-type financials]   # omit to use the trained classifier
"""

from __future__ import annotations

import argparse
import logging
import mimetypes
import os
import time
from pathlib import Path

import mlflow
from dotenv import load_dotenv

from api.document_processing import (
    EmbeddingClient,
    build_chunks,
)
from api.vector_store import ChromaVectorStore, get_vector_store
from classifier.predict import predict_doc_type

load_dotenv()
log = logging.getLogger("ingestion.batch")


_EXT_MIME = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/plain",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _resolve_mime(path: Path) -> str:
    ext_mime = _EXT_MIME.get(path.suffix.lower())
    if ext_mime:
        return ext_mime
    guessed, _ = mimetypes.guess_type(str(path))
    if not guessed:
        raise ValueError(f"Cannot determine MIME type for {path}")
    return guessed


def _attach_doc_type(
    *, document_id: int, doc_type: str, store
) -> None:
    """Workaround until Boston extends Chunk with doc_type.

    Reads back the chunks just upserted for this document, then re-upserts
    them with doc_type added to metadata. Safe because Chroma upsert is
    idempotent on (id, embedding) and we don't change the embedding.
    """
    if not isinstance(store, ChromaVectorStore):
        log.warning("Vector store is not ChromaVectorStore — skipping doc_type backfill")
        return

    collection = store._collection  # noqa: SLF001 — intentional, see TODO above
    existing = collection.get(
        where={"document_id": document_id},
        include=["metadatas", "documents", "embeddings"],
    )
    ids = existing.get("ids") or []
    if not ids:
        return
    new_metas = []
    for meta in existing.get("metadatas") or []:
        meta = dict(meta or {})
        meta["doc_type"] = doc_type
        new_metas.append(meta)
    collection.upsert(
        ids=ids,
        embeddings=existing.get("embeddings"),
        documents=existing.get("documents"),
        metadatas=new_metas,
    )


def _configure_mlflow() -> bool:
    uri = os.getenv("MLFLOW_TRACKING_URI", "")
    if not uri:
        return False
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(
        os.getenv("MLFLOW_EXPERIMENT_NAME", "team-project")
    )
    return True


def ingest_file(
    path: Path,
    *,
    deal_room_id: int,
    user_id: int,
    document_id: int,
    doc_type: str | None = None,
) -> int:
    """Chunk + embed + upsert one file. Returns chunk count."""
    mime_type = _resolve_mime(path)
    data = path.read_bytes()

    embedder = EmbeddingClient()
    chunks = build_chunks(
        user_id=user_id,
        deal_room_id=deal_room_id,
        document_id=document_id,
        mime_type=mime_type,
        data=data,
        embedder=embedder,
    )
    if not chunks:
        log.warning("No extractable text in %s — skipping", path)
        return 0

    store = get_vector_store()
    store.delete_document(document_id)  # re-ingestion safety
    store.upsert_chunks(chunks)

    resolved_type = doc_type or predict_doc_type(
        "\n".join(c.text for c in chunks[:3])[:4000]
    )
    _attach_doc_type(document_id=document_id, doc_type=resolved_type, store=store)

    log.info(
        "Ingested %d chunks from %s (deal_room_id=%s, doc_type=%s)",
        len(chunks),
        path,
        deal_room_id,
        resolved_type,
    )
    return len(chunks)


def ingest_path(
    source: str,
    *,
    deal_room_id: int,
    user_id: int,
    document_id: int,
    doc_type: str | None = None,
) -> int:
    p = Path(source)
    paths = [p] if p.is_file() else [
        f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in _EXT_MIME
    ]

    tracking_enabled = _configure_mlflow()
    run_ctx = (
        mlflow.start_run(run_name="offline_ingest_batch")
        if tracking_enabled
        else _NullCtx()
    )

    started = time.perf_counter()
    total_chunks = 0
    total_files = 0
    with run_ctx:
        for i, file_path in enumerate(paths):
            total_chunks += ingest_file(
                file_path,
                deal_room_id=deal_room_id,
                user_id=user_id,
                document_id=document_id + i,
                doc_type=doc_type,
            )
            total_files += 1

        elapsed = time.perf_counter() - started
        if tracking_enabled:
            mlflow.log_param("source", source)
            mlflow.log_param("deal_room_id", deal_room_id)
            mlflow.log_param("doc_type_override", doc_type or "classifier")
            mlflow.log_metric("files_ingested", total_files)
            mlflow.log_metric("chunks_ingested", total_chunks)
            mlflow.log_metric("elapsed_seconds", elapsed)

    log.info("Done. %d files, %d chunks in %.1fs", total_files, total_chunks, elapsed)
    return total_chunks


class _NullCtx:
    def __enter__(self):
        return None

    def __exit__(self, *args):
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Deal Room AI offline ingestion")
    parser.add_argument("--source", required=True, help="File or directory to ingest")
    parser.add_argument("--deal-room-id", type=int, required=True)
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument(
        "--document-id",
        type=int,
        required=True,
        help="Starting document_id; incremented per file when --source is a directory.",
    )
    parser.add_argument(
        "--doc-type",
        default=None,
        help="Override classifier; one of classifier.labels.DOC_TYPES.",
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level, format="%(levelname)s %(name)s: %(message)s"
    )
    ingest_path(
        args.source,
        deal_room_id=args.deal_room_id,
        user_id=args.user_id,
        document_id=args.document_id,
        doc_type=args.doc_type,
    )


if __name__ == "__main__":
    main()
