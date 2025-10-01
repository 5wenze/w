# src/embed.py
import numpy as np
from openai import OpenAI
from .config import OPENAI_API_KEY, EMBED_MODEL

_client = OpenAI(api_key=OPENAI_API_KEY)

def get_embeddings(texts):
    """
    texts: List[str] -> np.ndarray[float32]  (n, d)
    """
    resp = _client.embeddings.create(model=EMBED_MODEL, input=texts)
    vecs = [d.embedding for d in resp.data]
    return np.array(vecs, dtype="float32")

def l2_normalize(x: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / norm
