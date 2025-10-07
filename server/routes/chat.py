from fastapi import APIRouter
from server.agent.agent import process_user_message

router = APIRouter()

@router.post("/chat")
def chat(message: dict):
    user_message = message["query"]
    response = process_user_message(user_message)
    return {"response": response}
