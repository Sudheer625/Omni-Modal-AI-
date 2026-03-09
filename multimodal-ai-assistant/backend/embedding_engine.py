import hashlib
import math
from typing import Any, List, Optional

from config import EMBEDDING_MODEL_NAME


class EmbeddingEngine:
    def __init__(self) -> None:
        self._model: Optional[Any] = None
        self._fallback_mode = False
        self._warned = False

    def _get_model(self) -> Optional[Any]:
        if self._fallback_mode:
            return None
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            return self._model
        except Exception:
            self._fallback_mode = True
            return None

    def _fallback_embed(self, text: str, dim: int = 384) -> List[float]:
        vector = [0.0] * dim
        tokens = text.lower().split()
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for i in range(0, len(digest), 2):
                index = ((digest[i] << 8) | digest[i + 1]) % dim
                vector[index] += 1.0

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        if model is not None:
            embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            return embeddings.tolist()

        if not self._warned:
            print("Warning: sentence-transformers unavailable, using fallback embeddings.")
            self._warned = True
        return [self._fallback_embed(text) for text in texts]

    def embed_query(self, query: str) -> List[float]:
        model = self._get_model()
        if model is not None:
            embedding = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
            return embedding[0].tolist()

        if not self._warned:
            print("Warning: sentence-transformers unavailable, using fallback embeddings.")
            self._warned = True
        return self._fallback_embed(query)
