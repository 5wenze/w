import os, ujson, faiss
import numpy as np
from .embed import get_embeddings, l2_normalize

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(ROOT, "data", "notion_dump.jsonl")
STORE = os.path.join(ROOT, "store")
INDEX = os.path.join(STORE, "index.faiss")
META  = os.path.join(STORE, "meta.jsonl")

os.makedirs(STORE, exist_ok=True)

def read_jsonl(path):
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8") as f:
        return [ujson.loads(line) for line in f if line.strip()]

def build():
    docs = read_jsonl(DATA)
    if not docs:
        print("⚠️ 没有可用数据，请先准备 notion_dump.jsonl")
        return

    payloads = [d["title"] + "\n" + d.get("content","")[:500] for d in docs]
    metas = [{"id": d.get("id",""), "title": d.get("title","")} for d in docs]

    embs = l2_normalize(get_embeddings(payloads)).astype("float32")

    index = faiss.IndexFlatIP(embs.shape[1])
    index.add(embs)

    faiss.write_index(index, INDEX)
    with open(META, "w", encoding="utf-8") as f:
        for m in metas: f.write(ujson.dumps(m, ensure_ascii=False)+"\n")

    print(f"✅ 构建完成，{len(metas)} 条 -> {INDEX}")

if __name__ == "__main__":
    build()
