import math
from typing import Dict, List, Optional

import chromadb

from config import CHROMA_DIR


class VectorStore:
    def __init__(self) -> None:
        self._fallback_memory: List[Dict] = []
        self._fallback = False
        self.collection_name = "omnimodal_docs"

        try:
            self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            self.collection = self.client.get_or_create_collection(self.collection_name)
        except Exception:
            self._fallback = True
            self.client = None
            self.collection = None

    def _cosine(self, a: List[float], b: List[float]) -> float:
        if not a or not b:
            return 0.0
        length = min(len(a), len(b))
        dot = sum(a[i] * b[i] for i in range(length))
        norm_a = math.sqrt(sum(x * x for x in a[:length]))
        norm_b = math.sqrt(sum(x * x for x in b[:length]))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def add_document_chunks(
        self,
        file_id: int,
        filename: str,
        filetype: str,
        chunks: List[str],
        embeddings: List[List[float]],
    ) -> None:
        if not chunks:
            return

        if self._fallback:
            for idx, chunk in enumerate(chunks):
                self._fallback_memory.append(
                    {
                        "id": f"file-{file_id}-chunk-{idx}",
                        "file_id": file_id,
                        "filename": filename,
                        "filetype": filetype,
                        "document": chunk,
                        "embedding": embeddings[idx],
                    }
                )
            return

        ids = [f"file-{file_id}-chunk-{idx}" for idx in range(len(chunks))]
        metadatas = [
            {
                "file_id": file_id,
                "filename": filename,
                "filetype": filetype,
                "chunk_index": idx,
            }
            for idx in range(len(chunks))
        ]

        self.collection.upsert(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)

    def query(self, query_embedding: List[float], file_ids: Optional[List[int]] = None, top_k: int = 5) -> List[str]:
        if self._fallback:
            candidates = self._fallback_memory
            if file_ids:
                filter_set = set(file_ids)
                candidates = [item for item in candidates if item["file_id"] in filter_set]

            ranked = sorted(
                candidates,
                key=lambda item: self._cosine(query_embedding, item["embedding"]),
                reverse=True,
            )
            return [item["document"] for item in ranked[:top_k]]

        where = None
        if file_ids:
            where = {"file_id": {"$in": file_ids}}

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents"],
            where=where,
        )

        docs = result.get("documents", [])
        if not docs:
            return []
        return docs[0]

    def delete_file_chunks(self, file_id: int) -> None:
        if self._fallback:
            self._fallback_memory = [item for item in self._fallback_memory if item["file_id"] != file_id]
            return

        try:
            self.collection.delete(where={"file_id": file_id})
        except Exception:
            return
