# my_private_rag_service/main.py
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from rag_backend import RAGSystem # 导入RAG核心逻辑

# 初始化RAG系统 (这里假设config2.yaml在/root/.metagpt/)
# 实际部署时，你可能需要一个更安全的配置加载方式，例如通过环境变量
rag_system = RAGSystem(config_path="/root/.metagpt/config2.yaml")

app = FastAPI(
    title="Private RAG Service API",
    description="Custom RAG service for internal knowledge base queries."
)

class QueryRequest(BaseModel):
    query: str
    agentType: str # 对应 Context7Adapter 的 agent_type
    params: Optional[Dict[str, Any]] = None

class AuditRequest(BaseModel):
    query: str
    agentType: str

@app.post("/api/v1/query")
async def handle_query(request: QueryRequest):
    """处理RAG查询请求。"""
    print(f"Received query from {request.agentType}: {request.query}")
    try:
        results = await rag_system.query(request.query)
        return {"status": "success", "data": results}
    except Exception as e:
        print(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Internal RAG error: {e}")

@app.post("/api/v1/audit")
async def handle_audit(request: AuditRequest):
    """处理审计日志请求（通常是异步和非关键的）。"""
    print(f"Received audit log for {request.agentType}: {request.query}")
    # 这里可以添加实际的审计日志记录逻辑（例如写入文件、发送到日志系统）
    return {"status": "success", "message": "Audit log received."}

if __name__ == "__main__":
    import uvicorn
    # 【重要】: 请将 host 设置为 0.0.0.0 以便从外部访问，port 选择一个可用端口
    # 这个端口和IP就是 config2.yaml 中 private_rag_service.base_url 指向的地址
    uvicorn.run(app, host="0.0.0.0", port=9000)