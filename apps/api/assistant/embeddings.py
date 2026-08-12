from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import os
from typing import Any

import requests
from django.core.cache import cache


@dataclass(frozen=True)
class EmbeddingConfig:
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    endpoint_path: str = "/embeddings"
    timeout_seconds: int = 30
    cache_seconds: int = 86400
    max_text_length: int = 4000

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)


class EmbeddingError(RuntimeError):
    pass


def load_embedding_config() -> EmbeddingConfig:
    return EmbeddingConfig(
        api_key=os.getenv("AGENT_EMBEDDING_API_KEY", os.getenv("AGENT_API_KEY", "")).strip(),
        base_url=os.getenv("AGENT_EMBEDDING_BASE_URL", os.getenv("AGENT_BASE_URL", "")).strip().rstrip("/"),
        model=os.getenv("AGENT_EMBEDDING_MODEL", "").strip(),
        endpoint_path=os.getenv("AGENT_EMBEDDING_ENDPOINT_PATH", "/embeddings").strip() or "/embeddings",
        timeout_seconds=int(os.getenv("AGENT_EMBEDDING_TIMEOUT_SECONDS", "30")),
        cache_seconds=int(os.getenv("AGENT_EMBEDDING_CACHE_SECONDS", "86400")),
        max_text_length=int(os.getenv("AGENT_EMBEDDING_MAX_TEXT_LENGTH", "4000")),
    )


def _embedding_url(config: EmbeddingConfig) -> str:
    endpoint = config.endpoint_path if config.endpoint_path.startswith("/") else f"/{config.endpoint_path}"
    base_url = config.base_url.rstrip("/")
    if base_url.endswith(endpoint.rstrip("/")):
        return base_url
    if base_url.endswith("/chat/completions"):
        base_url = base_url[: -len("/chat/completions")]
    return f"{base_url}{endpoint}"


def _cache_key(config: EmbeddingConfig, text: str) -> str:
    digest = hashlib.sha256(f"{config.base_url}\0{config.model}\0{text}".encode("utf-8")).hexdigest()
    return f"assistant-embedding:{digest}"


def _parse_embeddings(data: Any, expected_count: int) -> list[list[float]]:
    if not isinstance(data, dict) or not isinstance(data.get("data"), list):
        raise EmbeddingError("Embedding response format is invalid.")

    rows = data["data"]
    try:
        rows = sorted(rows, key=lambda row: int(row.get("index", 0)))
    except (AttributeError, TypeError, ValueError) as exc:
        raise EmbeddingError("Embedding response indexes are invalid.") from exc
    if len(rows) != expected_count:
        raise EmbeddingError("Embedding response count does not match the request.")

    vectors: list[list[float]] = []
    for row in rows:
        raw_vector = row.get("embedding") if isinstance(row, dict) else None
        if not isinstance(raw_vector, list) or not raw_vector:
            raise EmbeddingError("Embedding response contains an invalid vector.")
        try:
            vector = [float(value) for value in raw_vector]
        except (TypeError, ValueError) as exc:
            raise EmbeddingError("Embedding vector contains a non-numeric value.") from exc
        if not all(math.isfinite(value) for value in vector):
            raise EmbeddingError("Embedding vector contains a non-finite value.")
        vectors.append(vector)
    return vectors


def _request_embeddings(config: EmbeddingConfig, texts: list[str]) -> list[list[float]]:
    try:
        response = requests.post(
            _embedding_url(config),
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": config.model, "input": texts},
            timeout=config.timeout_seconds,
        )
        response.raise_for_status()
        return _parse_embeddings(response.json(), len(texts))
    except requests.RequestException as exc:
        raise EmbeddingError(f"Embedding request failed: {exc}") from exc
    except ValueError as exc:
        raise EmbeddingError("Embedding response is not valid JSON.") from exc


def embed_texts(texts: list[str]) -> list[list[float]]:
    config = load_embedding_config()
    if not config.enabled:
        raise EmbeddingError("Embedding config is incomplete.")
    if not texts:
        return []

    clean_texts = [" ".join(str(text or "").split())[: config.max_text_length] or "空内容" for text in texts]
    keys = [_cache_key(config, text) for text in clean_texts]
    cached = cache.get_many(keys)

    missing_keys: list[str] = []
    missing_texts: list[str] = []
    seen_missing: set[str] = set()
    for key, text in zip(keys, clean_texts):
        if key not in cached and key not in seen_missing:
            seen_missing.add(key)
            missing_keys.append(key)
            missing_texts.append(text)

    if missing_texts:
        vectors = _request_embeddings(config, missing_texts)
        fresh = dict(zip(missing_keys, vectors))
        cache.set_many(fresh, timeout=config.cache_seconds)
        cached.update(fresh)

    return [cached[key] for key in keys]


def cosine_similarity(first: list[float], second: list[float]) -> float:
    if not first or len(first) != len(second):
        raise EmbeddingError("Embedding vectors must have the same non-zero dimensions.")
    first_norm = math.sqrt(sum(value * value for value in first))
    second_norm = math.sqrt(sum(value * value for value in second))
    if first_norm == 0 or second_norm == 0:
        return 0.0
    return sum(left * right for left, right in zip(first, second)) / (first_norm * second_norm)


def vector_similarity_scores(query: str, documents: list[str]) -> list[float]:
    if not documents:
        return []
    vectors = embed_texts([query, *documents])
    query_vector = vectors[0]
    return [cosine_similarity(query_vector, vector) for vector in vectors[1:]]
