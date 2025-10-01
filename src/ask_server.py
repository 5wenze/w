from fastapi import FastAPI, Query
from openai import OpenAI
import os, ujson, faiss
from .embed import get_embeddings, l2_normalize
from .config import OPENAI_API_KEY

app = FastAPI()
client = OpenAI(api_key=OPENAI_API_KEY)

ROOT = os.path.dirname(os.path.dirname(__file__))
IDX = os.path.join(ROOT, "store", "index.faiss")
META = os.path.join(ROOT, "store", "meta.jsonl")

def load_meta():
    metas = []
    if os.path.exists(META):
        with open(META, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    metas.append(ujson.loads(line))
    return metas

def search(q: str, k: int = 5):
    if not os.path.exists(IDX):
        return []
    index = faiss.read_index(IDX)
    qv = l2_normalize(get_embeddings([q])).astype("float32")
    D, I = index.search(qv, k)
    metas = load_meta()
    out = []
    for s, idx in zip(D[0], I[0]):
        if 0 <= idx < len(metas):
            m = metas[idx].copy()
            m["score"] = float(s)
            out.append(m)
    return out

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/ask")
def ask(q: str = Query(...), k: int = Query(3, ge=1, le=10)):
    hits = search(q, k)
    if not hits:
        return {
            "query": q,
            "answer": "资料不足：索引为空或未命中，请先补充语料并重建索引。",
            "sources": []
        }

    # 组装上下文供 GPT 总结（用标题+标签，避免粘贴超长正文）
    ctx = "\n".join([f"- {h.get('title')} | {','.join(h.get('tags', []))}" for h in hits])

    sys = ("你是严谨的交易助手，只能基于给定的 CONTEXT 回答；"
           "若信息不足请直说，不要编造；回答要先给结论，再给依据。")
    usr = f"问题：{q}\n\nCONTEXT:\n{ctx}"

    comp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[{"role": "system", "content": sys},
                  {"role": "user", "content": usr}],
        timeout=60
    )
    answer = comp.choices[0].message.content.strip()
    return {"query": q, "answer": answer, "sources": hits}
