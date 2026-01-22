from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import traceback

from app.services.rag_agent import rag_agent

router = APIRouter(tags=["AI"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    context: Optional[str] = "FINANCIAL_AI_PAGE"  # HOME_PAGE, TRANSACTIONS_PAGE, FINANCIAL_AI_PAGE

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        history = [(m.role, m.content) for m in request.history] if request.history else []
        response = await rag_agent.chat(request.message, history, context=request.context or "FINANCIAL_AI_PAGE")
        return ChatResponse(response=response)
    except Exception as e:
        print("[ERROR] Exception in /api/v1/chat endpoint:", repr(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

