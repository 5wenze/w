from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/ask")
def ask(q: str = Query(...)):
    # 现在先返回假数据，后面再接 FAISS 和 GPT
    return {
        "query": q,
        "answer": f"你问的是：{q} —— 暂时是假的回答（后面会接索引和GPT）",
        "sources": []
    }
