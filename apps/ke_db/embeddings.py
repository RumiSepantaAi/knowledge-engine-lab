"""Embedding providers for generating vector embeddings.

Providers:
- DummyProvider: Deterministic embeddings for testing
- RemoteProvider: OpenAI API (requires OPENAI_API_KEY)
"""

import hashlib
import logging
import math
import os
import time
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)

# Configurable embedding dimension
EMBEDDING_DIMENSION = 1536


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of embeddings produced."""
        pass


class DummyProvider(EmbeddingProvider):
    """Deterministic embedding provider for testing.

    Generates reproducible embeddings based on text hash.
    Does not require any external API.
    """

    def __init__(self, dimension: int = EMBEDDING_DIMENSION):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate deterministic embeddings from text hash.

        Args:
            texts: List of text strings.

        Returns:
            List of embedding vectors.
        """
        logger.info(f"DummyProvider: Embedding {len(texts)} text(s)")
        return [self._hash_to_embedding(text) for text in texts]

    def _hash_to_embedding(self, text: str) -> list[float]:
        """Convert text hash to embedding vector."""
        # Use SHA256 to get deterministic seed
        hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(hash_bytes[:8], "big")

        # Generate embedding using sine/cosine waves
        embedding = []
        for i in range(self._dimension):
            value = (
                0.5 * math.sin(seed * 0.1 + i * 0.01)
                + 0.3 * math.cos(seed * 0.2 + i * 0.02)
                + 0.2 * math.sin(seed * 0.3 + i * 0.03)
            )
            embedding.append(value)

        # Normalize to unit length
        norm = math.sqrt(sum(x * x for x in embedding))
        return [x / norm for x in embedding]


class RemoteProvider(EmbeddingProvider):
    """OpenAI API embedding provider.

    Requires OPENAI_API_KEY environment variable.
    Includes batching, retry, and rate limiting.
    """

    def __init__(
        self,
        model: str = "text-embedding-ada-002",
        batch_size: int = 100,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._dimension = EMBEDDING_DIMENSION

        # Get API key from environment
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set - RemoteProvider will fail on use")

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI API.

        Args:
            texts: List of text strings.

        Returns:
            List of embedding vectors.

        Raises:
            RuntimeError: If API key not set or API fails after retries.
        """
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set")

        logger.info(f"RemoteProvider: Embedding {len(texts)} text(s) in batches of {self.batch_size}")

        all_embeddings: list[list[float]] = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            logger.debug(f"Processing batch {i // self.batch_size + 1}")

            embeddings = self._embed_batch_with_retry(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def _embed_batch_with_retry(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch with retry logic."""
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                return self._call_openai_api(texts)
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")

                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)

        raise RuntimeError(f"Failed after {self.max_retries} retries: {last_error}")

    def _call_openai_api(self, texts: list[str]) -> list[list[float]]:
        """Call OpenAI embeddings API.

        This is a stub that shows the expected interface.
        Actual implementation requires the openai package.
        """
        # NOTE: This is a stub implementation
        # To enable, install openai package and uncomment below:
        #
        # import openai
        # openai.api_key = self.api_key
        # response = openai.Embedding.create(
        #     model=self.model,
        #     input=texts,
        # )
        # return [item["embedding"] for item in response["data"]]

        raise NotImplementedError(
            "RemoteProvider requires openai package. "
            "Install with: pip install openai>=1.0.0"
        )


def get_provider(provider_name: str = "auto") -> EmbeddingProvider:
    """Get embedding provider by name.

    Args:
        provider_name: Provider name ("dummy", "openai", "auto").
            "auto" selects OpenAI if OPENAI_API_KEY is set, else Dummy.

    Returns:
        EmbeddingProvider instance.
    """
    if provider_name == "dummy":
        logger.info("Using DummyProvider")
        return DummyProvider()

    if provider_name == "openai":
        logger.info("Using RemoteProvider (OpenAI)")
        return RemoteProvider()

    if provider_name == "auto":
        if os.getenv("OPENAI_API_KEY"):
            logger.info("Auto-selected RemoteProvider (OPENAI_API_KEY found)")
            return RemoteProvider()
        else:
            logger.info("Auto-selected DummyProvider (no OPENAI_API_KEY)")
            return DummyProvider()

    raise ValueError(f"Unknown provider: {provider_name}")
