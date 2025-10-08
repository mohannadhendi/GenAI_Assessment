from fastapi import APIRouter, Body
from server.agent.runner import run_agent_query

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(payload: dict = Body(...)):
    query = payload.get("query")
    session_id = payload.get("session_id")  # optional
    result = run_agent_query(query, session_id)
    return result